"""Exercise the real Worktrunk backend and shutdown using only temporary fixtures.

Run explicitly outside a sandbox that blocks ps/lsof. No Herdr commands or
agents are started. The only processes eligible for shutdown are our helpers.
"""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / "src/.local/bin/goerwin-wt"


def main():
    real_wt = shutil.which("wt")
    if not real_wt:
        raise RuntimeError("Worktrunk is required")
    with tempfile.TemporaryDirectory(prefix="goerwin-real-smoke-") as temporary:
        root = Path(temporary).resolve()
        repo, binaries = root / "repo", root / "bin"
        repo.mkdir()
        binaries.mkdir()
        config = root / "wt.toml"
        config.write_text("")
        shim = binaries / "wt"
        shim.write_text(f"#!{sys.executable}\nimport os, sys\nos.execv({real_wt!r}, "
                        f"[{real_wt!r}, '--config', {str(config)!r}, *sys.argv[1:]])\n")
        shim.chmod(0o755)
        # Exclude installed hc/herdr-app so the test cannot touch live sessions.
        env = dict(os.environ, PATH=f"{binaries}:/usr/bin:/bin:/usr/sbin:/sbin",
                   GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")

        def command(args, check=True):
            return subprocess.run(args, cwd=repo, env=env, capture_output=True, text=True, check=check)

        def cli(*args, check=True):
            result = command([sys.executable, str(CLI), *args, "--json"], check=check)
            return result, json.loads(result.stdout)

        command(["git", "init", "-b", "main"])
        command(["git", "config", "user.name", "Smoke Tests"])
        command(["git", "config", "user.email", "tests@example.invalid"])
        (repo / "file").write_text("base\n")
        command(["git", "add", "."])
        command(["git", "commit", "-m", "base"])
        _, switched = cli("switch", "feature", "main")
        folder = Path(switched["path"])
        assert folder.is_relative_to(root), "Worktrunk checkout escaped the temporary fixture"
        (folder / "dirty").write_text("temporary fixture data")
        helper = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)"], cwd=folder, env=env)
        unrelated = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)"], cwd=repo, env=env)
        try:
            result, failed = cli("remove", "feature", "--force", check=False)
            assert result.returncode == 1 and "--stop" in failed["error"], failed
            assert helper.poll() is None and folder.exists()
            _, removed = cli("remove", "feature", "--force", "--stop")
            assert removed["status"] == "removed" and not folder.exists(), removed
            helper.wait(timeout=5)
            assert unrelated.poll() is None, "Unrelated helper was stopped"
            assert str(helper.pid) in str(removed["stopped_processes"]), removed
            command(["git", "show-ref", "--verify", "refs/heads/feature"])
            _, listed = cli("list")
            assert len(listed["items"]) == 1, listed
            print("Real Worktrunk smoke passed: switch/list/remove, dirty-file permission, "
                  "explicit shutdown, branch retention, unrelated-process preservation.")
        finally:
            for process in (helper, unrelated):
                if process.poll() is None:
                    process.terminate()
                process.wait(timeout=5)


if __name__ == "__main__":
    main()
