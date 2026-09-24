#!/usr/bin/env python3
"""Builds the ShuttleIQ public pages (US English): src/en/<page>.html → <page>/index.html.

Usage: python3 build.py, then commit and push. GitHub Pages serves this repository's root at BASE_URL.
Each source file starts with `<!-- title: … -->` and `<!-- description: … -->`; `{root}` in a body is the
relative path to the site root. The app is English-only since 2026-09-24; the former Polish URLs under /pl/
redirect to the English pages.
"""
import html
import posixpath
import re
from pathlib import Path

ROOT = Path(__file__).parent
BASE_URL = "https://szymdzie.github.io/shuttleiq/"
EMAIL = "chochoapps@gmail.com"
PAGES = ["index", "privacy", "terms", "support"]
LANGS = {
    "en": {
        "dir": "",
        "nav": {"support": "Support", "privacy": "Privacy", "terms": "Terms"},
        "nav_label": "Main",
        "footer": {"privacy": "Privacy Policy", "terms": "Terms of Use", "support": "Support"},
    },
}

TEMPLATE = """<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title}</title>
<meta name="description" content="{description}">
<link rel="canonical" href="{canonical}">
<meta name="theme-color" content="#121214">
<meta property="og:type" content="website">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{base}assets/icon-256.png">
<link rel="icon" type="image/png" sizes="32x32" href="{root}assets/favicon-32.png">
<link rel="icon" type="image/png" sizes="64x64" href="{root}assets/favicon-64.png">
<link rel="apple-touch-icon" href="{root}assets/apple-touch-icon.png">
<link rel="stylesheet" href="{root}assets/site.css">
</head>
<body>
<header class="top"><div class="wrap">
  <a class="brand" href="{home}"><img src="{root}assets/icon-256.png" alt="" width="34" height="34"><span>ShuttleIQ</span></a>
  <nav aria-label="{nav_label}">
{nav}
  </nav>
</div></header>
<main class="wrap">
{body}
</main>
<footer><div class="wrap">
  <span>© 2026 Szymon Dziedzic</span>
  <a href="mailto:{email}">{email}</a>
{footer_links}
</div></footer>
</body>
</html>
"""


def page_dir(lang, page):
    """Directory of a page relative to the site root ("" is the root)."""
    parts = [p for p in (LANGS[lang]["dir"], "" if page == "index" else page) if p]
    return "/".join(parts)


def rel(from_dir, to_dir):
    """Relative link between two site directories, always ending in "/" (or "./" for the same one)."""
    path = posixpath.relpath(to_dir or ".", from_dir or ".")
    return "./" if path == "." else path + "/"


def render(lang, page, absolute=None):
    """One page. With `absolute` (the site's URL path), every link is absolute: used for the 404 page."""
    source = (ROOT / "src" / lang / f"{page}.html").read_text(encoding="utf-8")
    title = re.search(r"<!-- title: (.+?) -->", source).group(1)
    description = re.search(r"<!-- description: (.+?) -->", source).group(1)
    body = re.sub(r"<!-- (title|description): .+? -->\n", "", source).strip()

    here = page_dir(lang, page)

    def link(to_dir):
        if absolute is not None:
            return absolute + (to_dir + "/" if to_dir else "")
        return rel(here, to_dir)

    root = link("")
    home = link(LANGS[lang]["dir"])
    nav = []
    for key, label in LANGS[lang]["nav"].items():
        current = ' aria-current="page"' if key == page and absolute is None else ""
        nav.append(f'    <a href="{link(page_dir(lang, key))}"{current}>{label}</a>')
    footer_links = "\n".join(
        f'  <a href="{link(page_dir(lang, key))}">{label}</a>' for key, label in LANGS[lang]["footer"].items())
    full_title = title if page == "index" else f"{title} · ShuttleIQ"
    return TEMPLATE.format(
        lang=lang, title=html.escape(full_title), description=html.escape(description),
        canonical=BASE_URL + (here + "/" if here else ""),
        base=BASE_URL, root=root, home=home, nav_label=LANGS[lang]["nav_label"], nav="\n".join(nav),
        body=body.replace("{root}", root), email=EMAIL, footer_links=footer_links,
    )


def not_found():
    """404 page for any missing path. GitHub Pages serves it at the requested URL, so links are absolute."""
    base_path = "/" + BASE_URL.split("/", 3)[3]
    page = render("en", "index", absolute=base_path)
    body = ('<p class="eyebrow">404</p>\n<h1>Page not found</h1>\n'
            f'<p class="lead">This page doesn’t exist. Go to the <a href="{base_path}">ShuttleIQ home page</a>'
            '.</p>').replace(" .</p>", ".</p>")
    page = re.sub(r'<main class="wrap">.*</main>', lambda _: f'<main class="wrap">\n{body}\n</main>', page, flags=re.S)
    return page.replace("<title>ShuttleIQ: Beep Test</title>", "<title>Page not found · ShuttleIQ</title>")


REDIRECT = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>ShuttleIQ</title>
<meta name="robots" content="noindex">
<link rel="canonical" href="{url}">
<meta http-equiv="refresh" content="0; url={url}">
</head>
<body><p><a href="{url}">{url}</a></p></body>
</html>
"""


def main():
    for lang in LANGS:
        for page in PAGES:
            out = ROOT / page_dir(lang, page) / "index.html"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(render(lang, page), encoding="utf-8")
            print("wrote", out.relative_to(ROOT))
    # The app is English-only: the former Polish pages send visitors to the English ones.
    for page in PAGES:
        target = BASE_URL + page_dir("en", page) + ("/" if page != "index" else "")
        out = ROOT / "pl" / ("" if page == "index" else page) / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(REDIRECT.format(url=target), encoding="utf-8")
    (ROOT / "404.html").write_text(not_found(), encoding="utf-8")
    print("wrote 404.html")


if __name__ == "__main__":
    main()
