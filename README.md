# site-markdown

A small command-line crawler that turns a website section into one Markdown file.

## Development setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
site-markdown --help
```

## Quick start

```bash
site-markdown https://example.com/docs/ -o example-docs.md
```

By default, every HTTP(S) page linked from a captured page is eligible, including
links on other hosts. The crawl continues recursively and `--max-pages` keeps it
bounded. Use `--scope host` for same-host links only or `--scope path` for links
beneath the starting path. `--delay` pauses between page requests.
The crawler honors each host's `robots.txt`; use `--ignore-robots` only when you
have permission to bypass it.

## Sample

```bash
site-markdown \
  'https://help.splunk.com/en/splunk-enterprise/leverage-rest-apis/rest-api-user-manual/10.4/rest-api-user-manual/basic-concepts-about-the-splunk-platform-rest-api' \
  --output splunk-rest-api.md
```

Run `site-markdown --help` for all options.

## Tests

```bash
pytest
```
