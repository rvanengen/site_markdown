from pathlib import Path

from site_markdown import cli
from site_markdown.crawler import CrawlResult, Page


def test_cli_writes_output(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(
        cli,
        "crawl",
        lambda *args, **kwargs: CrawlResult(
            [Page("https://example.com/docs", "Docs", "Content")], []
        ),
    )
    output = tmp_path / "out.md"
    assert cli.main(["https://example.com/docs", "-o", str(output)]) == 0
    assert "Content" in output.read_text(encoding="utf-8")
