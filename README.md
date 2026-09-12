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

By default, only HTML pages on the same host whose paths sit under the input URL are crawled. Use `--scope host` to follow every same-host link, `--max-pages` to bound a crawl, and `--delay` to pause between requests.

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
