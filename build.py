#!/usr/bin/env python3
"""Build the clhodapp.github.io site into an output directory.

The index lists the public repositories that the GitHub API reports
for the user, minus forks, archived repositories and the names in
blocklist.txt. The script also
writes robots.txt and sitemap.xml so that search engines may crawl and
index the site.

Environment:
  GITHUB_TOKEN              optional; raises the API rate limit
  GOOGLE_SITE_VERIFICATION  optional; the content value of the
                            google-site-verification meta tag that
                            Google Search Console issues
"""

import datetime
import html
import json
import os
import sys
import urllib.request
from pathlib import Path

USER = "clhodapp"
SITE_URL = f"https://{USER}.github.io/"
HERE = Path(__file__).resolve().parent


def read_blocklist(path):
    names = set()
    for raw in path.read_text().splitlines():
        line = raw.split("#", 1)[0].strip()
        if line:
            names.add(line.lower())
    return names


def fetch_repos(token):
    repos = []
    page = 1
    while True:
        url = (
            f"https://api.github.com/users/{USER}/repos"
            f"?type=owner&per_page=100&page={page}"
        )
        request = urllib.request.Request(
            url, headers={"Accept": "application/vnd.github+json"}
        )
        if token:
            request.add_header("Authorization", f"Bearer {token}")
        with urllib.request.urlopen(request) as response:
            batch = json.load(response)
        repos.extend(batch)
        if len(batch) < 100:
            return repos
        page += 1


def select(repos, blocklist):
    kept = [
        r
        for r in repos
        if not r["fork"]
        and not r["archived"]
        and not r["private"]
        and r["name"].lower() not in blocklist
    ]
    kept.sort(key=lambda r: r["pushed_at"], reverse=True)
    return kept


def render_repo(repo):
    name = html.escape(repo["name"])
    url = html.escape(repo["html_url"])
    description = html.escape(repo["description"] or "")
    meta = []
    if repo["language"]:
        meta.append(html.escape(repo["language"]))
    if repo["stargazers_count"]:
        meta.append(f"★ {repo['stargazers_count']}")
    meta.append(f"updated {repo['pushed_at'][:10]}")
    homepage = repo.get("homepage") or ""
    if homepage:
        meta.append(f'<a href="{html.escape(homepage)}">homepage</a>')
    topics = "".join(
        f'<span class="topic">{html.escape(t)}</span>'
        for t in repo.get("topics") or []
    )
    lines = [
        "      <li>",
        f'        <h3><a href="{url}">{name}</a></h3>',
    ]
    if description:
        lines.append(f"        <p>{description}</p>")
    lines.append(f'        <p class="meta">{" · ".join(meta)}</p>')
    if topics:
        lines.append(f'        <p class="topics">{topics}</p>')
    lines.append("      </li>")
    return "\n".join(lines)


def render_index(repos, verification, built):
    items = "\n".join(render_repo(r) for r in repos)
    verification_tag = ""
    if verification:
        verification_tag = (
            '\n  <meta name="google-site-verification" '
            f'content="{html.escape(verification)}">'
        )
    description = f"Open-source projects by {USER} on GitHub."
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{USER}: projects</title>
  <meta name="description" content="{description}">
  <meta name="robots" content="index, follow">{verification_tag}
  <link rel="canonical" href="{SITE_URL}">
  <style>
    :root {{ --fg: #1d1d1f; --muted: #6e6e73; --bg: #fff; --line: #e5e5ea; --link: #0b57d0; }}
    @media (prefers-color-scheme: dark) {{
      :root {{ --fg: #f2f2f7; --muted: #a1a1a6; --bg: #121214; --line: #2c2c2e; --link: #8ab4f8; }}
    }}
    body {{ margin: 0 auto; max-width: 46rem; padding: 2rem 1rem 4rem;
           font: 16px/1.5 system-ui, sans-serif; color: var(--fg); background: var(--bg); }}
    a {{ color: var(--link); text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    header p, .meta, footer {{ color: var(--muted); }}
    .repos {{ list-style: none; padding: 0; }}
    .repos li {{ padding: .9rem 0; border-top: 1px solid var(--line); }}
    .repos h3 {{ margin: 0; font-size: 1.05rem; }}
    .repos p {{ margin: .25rem 0 0; }}
    .meta {{ font-size: .875rem; }}
    .topic {{ display: inline-block; margin: 0 .35rem .25rem 0; padding: 0 .5rem;
             border: 1px solid var(--line); border-radius: 1rem; font-size: .8rem; color: var(--muted); }}
    footer {{ margin-top: 3rem; font-size: .8rem; }}
  </style>
</head>
<body>
  <header>
    <h1>{USER}</h1>
    <p>{description} More on <a href="https://github.com/{USER}">github.com/{USER}</a>.</p>
  </header>
  <main>
    <ul class="repos">
{items}
    </ul>
  </main>
  <footer>Generated {built} from the GitHub API.</footer>
</body>
</html>
"""


def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "_site")
    out.mkdir(parents=True, exist_ok=True)
    blocklist = read_blocklist(HERE / "blocklist.txt")
    repos = select(fetch_repos(os.environ.get("GITHUB_TOKEN")), blocklist)
    today = datetime.date.today().isoformat()
    verification = os.environ.get("GOOGLE_SITE_VERIFICATION", "").strip()
    (out / "index.html").write_text(render_index(repos, verification, today))
    (out / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}sitemap.xml\n"
    )
    (out / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"  <url><loc>{SITE_URL}</loc><lastmod>{today}</lastmod></url>\n"
        "</urlset>\n"
    )
    (out / ".nojekyll").write_text("")
    print(f"wrote {len(repos)} repositories to {out}/index.html")


if __name__ == "__main__":
    main()
