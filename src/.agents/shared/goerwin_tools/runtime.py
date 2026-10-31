import contextlib
import datetime as dt
import fcntl
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlsplit

DEFAULT_CONFIG = Path.home() / ".config/goerwin-wts/config.json"
LEGACY_CONFIGS = (
    Path.home() / ".config/review-pr/config.json",
    Path.home() / ".config/goerwin-code-review/config.json",
)


class CommandError(RuntimeError):
    pass



def run(args, cwd=None, env=None, check=True, timeout=120):
    try:
        result = subprocess.run(
            [str(arg) for arg in args],
            cwd=cwd,
            env=env,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise CommandError(str(error)) from error
    if check and result.returncode:
        raise CommandError(
            result.stderr.strip() or f"{args[0]} exited {result.returncode}"
        )
    return result



def git(repo, *args, check=True):
    return run(["git", "-C", str(repo), *args], check=check)



def json_read(path):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError) as error:
        raise CommandError(f"Cannot read JSON from {path}: {error}") from error



def json_write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".review-", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as stream:
            json.dump(data, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)



def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()



def repository_url(value):
    value = value.strip()
    if re.fullmatch(r"[^/@\s]+@[^/:\s]+:.+", value):
        value = "ssh://" + value.replace(":", "/", 1)
    parsed = urlsplit(value)
    parts = parsed.path.strip("/").removesuffix(".git").split("/")
    if not parsed.hostname or len(parts) != 2 or not all(parts):
        return None
    return "/".join([parsed.hostname.lower(), *[p.lower() for p in parts]])



def pr_url(value):
    parsed = urlsplit(value)
    match = re.fullmatch(r"/([^/]+)/([^/]+)/pull/([1-9][0-9]*)(?:/.*)?", parsed.path)
    if parsed.scheme not in ("https", "http") or not parsed.hostname or not match:
        return None
    owner, repo, number = match.groups()
    if not all(re.fullmatch(r"[A-Za-z0-9_.-]+", p) for p in (owner, repo)):
        return None
    host = parsed.hostname.lower()
    return {
        "repo": f"{host}/{owner.lower()}/{repo.lower()}",
        "url": f"https://{host}/{owner}/{repo}/pull/{number}",
        "number": int(number),
        "host": host,
    }



def worktrees(repo):
    output = git(repo, "worktree", "list", "--porcelain", "-z").stdout
    entries, current = [], {}
    for field in output.split("\0"):
        if not field:
            if current:
                entries.append(current)
                current = {}
            continue
        key, _, value = field.partition(" ")
        current[key] = value if value else True
    if current:
        entries.append(current)
    return entries



def source_root(cwd):
    items = worktrees(cwd)
    if not items or "bare" in items[0]:
        raise CommandError("A non-bare primary source checkout is required")
    return str(Path(items[0]["worktree"]).resolve())



def common_dir(repo):
    return str(
        Path(
            git(repo, "rev-parse", "--path-format=absolute", "--git-common-dir")
            .stdout.strip()
        ).resolve()
    )



def remote_repositories(repo):
    result = {}
    for name in git(repo, "remote").stdout.splitlines():
        url = git(repo, "remote", "get-url", name).stdout.strip()
        parsed = repository_url(url)
        if parsed:
            result[name] = parsed
    return result



def github_environment(user=None, host=None):
    env = os.environ.copy()
    if host:
        env["GH_HOST"] = host
    if user:
        token_env = {
            key: value
            for key, value in env.items()
            if key not in ("GH_TOKEN", "GITHUB_TOKEN", "GH_ENTERPRISE_TOKEN", "GITHUB_ENTERPRISE_TOKEN")
        }
        token = run(
            ["gh", "auth", "token", "--hostname", host or "github.com", "--user", user],
            env=token_env,
        ).stdout.strip()
        if not token:
            raise CommandError(f"No existing gh login for {user}")
        env = token_env.copy()
        env["GH_TOKEN" if (host or "github.com") == "github.com" else "GH_ENTERPRISE_TOKEN"] = token
    return env


def github(args, cwd, user=None, host=None):
    result = run(["gh", *args], cwd=cwd, env=github_environment(user, host))
    try:
        return json.loads(result.stdout)
    except ValueError as error:
        raise CommandError("gh returned invalid JSON") from error



def commit(repo, ref):
    return git(repo, "rev-parse", "--verify", "--end-of-options", f"{ref}^{{commit}}").stdout.strip()



def default_base(repo):
    for remote in ("origin", "upstream"):
        value = git(repo, "symbolic-ref", "--quiet", f"refs/remotes/{remote}/HEAD", check=False)
        if value.returncode == 0:
            return value.stdout.strip().removeprefix("refs/remotes/")
    for branch in ("main", "master"):
        if git(repo, "show-ref", "--verify", f"refs/heads/{branch}", check=False).returncode == 0:
            return branch
    return None



@contextlib.contextmanager
def allocation_lock(directory, key=".allocation"):
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / (key + ".lock")).open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        yield
        fcntl.flock(lock, fcntl.LOCK_UN)


def config(path=DEFAULT_CONFIG):
    paths = (*LEGACY_CONFIGS, Path(path)) if Path(path) == DEFAULT_CONFIG else (Path(path),)
    settings = {}
    for candidate in paths:
        if candidate.exists():
            data = json_read(candidate)
            if not isinstance(data, dict) or not isinstance(data.get("repositories", {}), dict):
                raise CommandError(f"Invalid repository configuration: {candidate}")
            repositories = {**settings.get("repositories", {}), **data.get("repositories", {})}
            settings.update(data)
            settings["repositories"] = repositories
    return settings


def find_source(cwd, repo_name, settings):
    candidates = [str(Path(cwd).resolve())]
    registered = settings.get("repositories", {}).get(repo_name)
    if registered:
        candidates.append(str(Path(registered).expanduser().resolve()))
    for candidate in candidates:
        try:
            if repo_name in remote_repositories(candidate).values():
                return source_root(candidate)
        except CommandError:
            continue
    raise CommandError(
        f"No registered local checkout for {repo_name}. "
        "Run 'goerwin-wts register /path/to/checkout' first."
    )


def register_checkout(path, config_path=DEFAULT_CONFIG, repository=None):
    root = source_root(path)
    identities = set(remote_repositories(root).values())
    if repository:
        identity = repository_url(repository)
        if not identity or identity not in identities:
            raise CommandError("The checkout has no remote matching that repository")
        identities = {identity}
    if not identities:
        raise CommandError("The checkout has no recognizable GitHub remotes")
    with allocation_lock(Path(config_path).parent, ".repositories"):
        settings = config(config_path)
        settings.setdefault("repositories", {}).update({identity: root for identity in identities})
        json_write(config_path, settings)
    return {"repositories": sorted(identities), "source_root": root, "config": str(config_path)}
