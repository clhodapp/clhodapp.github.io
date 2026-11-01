# clhodapp.github.io

The source of <https://clhodapp.github.io/>, an index of the public
repositories of the clhodapp GitHub account.

The `pages` workflow runs `build.py` on every push to `main`, once a day,
and on demand. The script reads the account's repositories from the GitHub
API and writes `index.html`, `robots.txt` and `sitemap.xml`. The index
leaves out forks, archived repositories, private repositories and the
names in `blocklist.txt`. GitHub Pages then serves the result.

To leave a repository out of the index, add its name to `blocklist.txt`.

To verify the site in Google Search Console with the HTML tag method, set
the repository variable `GOOGLE_SITE_VERIFICATION` to the `content` value
of the tag that Search Console issues, then run the workflow.

To build locally:

```sh
python3 build.py _site
```
