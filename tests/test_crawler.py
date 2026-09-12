from site_markdown.crawler import (
    CrawlResult,
    Page,
    _in_scope,
    extract_page,
    normalize_url,
    render_document,
)


def test_normalize_url_keeps_query_but_removes_fragment_and_trailing_slash():
    assert normalize_url("HTTPS://Example.COM/docs/?q=1#top") == "https://example.com/docs?q=1"


def test_resource_id_links_remain_distinct():
    html = """
    <main><a href="/?resourceId=One">One</a>
    <a href="/?resourceId=Two">Two</a>
    <a href="http://external.example/guide">External</a></main>
    """
    _, links = extract_page(html, "https://help.example/start")
    assert links == [
        "https://help.example/?resourceId=One",
        "https://help.example/?resourceId=Two",
        "http://external.example/guide",
    ]
    assert _in_scope(links[-1], "https://help.example/start", "linked")


def test_extract_page_prefers_main_and_discovers_links():
    html = """
    <html><head><title>Fallback</title></head><body>
      <nav>Menu</nav>
      <main><h1>API Guide</h1><p>Use <code>GET</code>.</p>
        <a href="child/">Next</a><script>bad()</script>
      </main>
    </body></html>
    """
    page, links = extract_page(html, "https://example.com/docs")
    assert page.title == "API Guide"
    assert "API Guide" not in page.markdown
    assert "`GET`" in page.markdown
    assert "bad()" not in page.markdown
    assert "https://example.com/child/" in page.markdown
    assert links == ["https://example.com/child"]


def test_render_document_includes_provenance_and_page_count():
    result = CrawlResult(
        pages=[Page("https://example.com/docs", "Docs", "# Docs\n\nHello")],
        errors=[],
    )
    output = render_document(result, "https://example.com/docs")
    assert output.startswith("# Docs")
    assert "Pages captured: 1" in output
    assert "Source: <https://example.com/docs>" in output
