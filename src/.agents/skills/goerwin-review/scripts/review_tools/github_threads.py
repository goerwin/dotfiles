"""Open GitHub review feedback as an archive report, and replies back to GitHub."""

from goerwin_tools.runtime import CommandError, github, new_id, now, pr_url

from .store import finalize_report, report_path

THREADS = """
query($owner: String!, $repo: String!, $number: Int!, $cursor: String) {
  viewer { login }
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $number) {
      reviewThreads(first: 50, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id isResolved isOutdated path line originalLine
          comments(first: 100) { nodes { author { login } body url createdAt } }
        }
      }
    }
  }
}
"""
REPLY = """
mutation($thread: ID!, $body: String!) {
  addPullRequestReviewThreadReply(input: {pullRequestReviewThreadId: $thread, body: $body}) {
    comment { url author { login } }
  }
}
"""


def graphql(cwd, user, host, query, **variables):
    args = ["api", "graphql", "-f", f"query={query}"]
    for key, value in variables.items():
        if value is not None:
            args += ["-F" if isinstance(value, int) else "-f", f"{key}={value}"]
    data = github(args, cwd, user, host)
    if data.get("errors"):
        raise CommandError("GitHub: " + "; ".join(error.get("message", "") for error in data["errors"]))
    return data["data"]


def open_threads(cwd, url, user=None):
    """Unresolved threads whose last comment isn't the viewer's, plus the viewer's login."""
    parsed = pr_url(url)
    _, owner, repo = parsed["repo"].split("/")
    threads, cursor, viewer = [], None, None
    while True:
        data = graphql(cwd, user, parsed["host"], THREADS, owner=owner, repo=repo,
                       number=parsed["number"], cursor=cursor)
        viewer = data["viewer"]["login"]
        page = data["repository"]["pullRequest"]["reviewThreads"]
        threads += page["nodes"]
        if not page["pageInfo"]["hasNextPage"]:
            break
        cursor = page["pageInfo"]["endCursor"]
    active = [
        thread for thread in threads
        if not thread["isResolved"] and thread["comments"]["nodes"]
        and (thread["comments"]["nodes"][-1]["author"] or {}).get("login") != viewer
    ]
    return active, viewer


def comments(cwd, url, user=None):
    """Top-level PR conversation comments; the agent keeps only those asking for a change."""
    parsed = pr_url(url)
    return github(["pr", "view", parsed["url"], "--json", "comments"], cwd, user, parsed["host"])["comments"]


def section(index, thread):
    first = thread["comments"]["nodes"][0]
    line = thread["line"] or thread["originalLine"]
    location = f"`{thread['path']}:{line}`" + (" (outdated)" if thread["isOutdated"] else "")
    conversation = "\n\n".join(
        f"**@{(item['author'] or {}).get('login', 'ghost')}** ({item['createdAt']}):\n\n{item['body'].strip()}"
        for item in thread["comments"]["nodes"]
    )
    title = first["body"].strip().splitlines()[0][:80] if first["body"].strip() else "Review thread"
    return (f"### F{index}: {title}\n\n{location} · thread `{thread['id']}` · {first['url']}\n\n"
            f"{conversation}")


def import_threads(target, archive, user=None):
    """Save the PR's open threads as an archive report that receiving handles like any other."""
    threads, viewer = open_threads(target["source_root"], target["pr_url"], user)
    body = "\n\n".join(section(index, thread) for index, thread in enumerate(threads, 1))
    path = report_path(archive, {**target, "title": f"{target['title']} github threads"})
    path.write_text(f"# GitHub review threads\n\nOpen threads on {target['pr_url']}, "
                    f"excluding resolved ones and those last answered by @{viewer}.\n\n"
                    + (body or "No actionable findings."))
    finalize_report({
        "report": str(path), "run_id": new_id(), "created_at": now(), "finished_at": now(),
        "target": target,
        "preset": {"skill": "github", "harness": "github", "model": "reviewers", "effort": "n/a"},
    })
    return {"report": str(path), "threads": len(threads), "viewer": viewer}


def reply(cwd, url, replies, user=None):
    """Post approved replies: {"thread": id, "body": text} or {"body": text} for a PR comment.

    Stops at the first failure and reports what was already posted, so a retry never double-posts.
    """
    parsed = pr_url(url)
    posted = []
    for item in replies:
        try:
            if item.get("thread"):
                data = graphql(cwd, user, parsed["host"], REPLY, thread=item["thread"], body=item["body"])
                comment = data["addPullRequestReviewThreadReply"]["comment"]
            else:
                comment = github(["api", f"repos/{parsed['repo'].split('/', 1)[1]}/issues/{parsed['number']}/comments",
                                  "-f", f"body={item['body']}"], cwd, user, parsed["host"])
                comment = {"url": comment["html_url"], "author": comment["user"]}
        except CommandError as error:
            raise CommandError(f"{error}; already posted: {[entry['url'] for entry in posted] or 'none'}") from error
        posted.append({"thread": item.get("thread"), "url": comment["url"], "author": comment["author"]["login"]})
    return posted
