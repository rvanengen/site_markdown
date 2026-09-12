from __future__ import annotations

import re
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable
from urllib.parse import urldefrag, urljoin, urlsplit, urlunsplit
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup
from markdownify import markdownify


USER_AGENT = "site-markdown/0.1 (+https://github.com/rvanengen/site_markdown)"
SKIP_SUFFIXES = {
    ".7z", ".avi", ".css", ".csv", ".doc", ".docx", ".gif", ".gz",
    ".ico", ".jpeg", ".jpg", ".js", ".json", ".mov", ".mp3", ".mp4",
    ".pdf", ".png", ".ppt", ".pptx", ".rss", ".svg", ".tar", ".txt",
    ".webp", ".xls", ".xlsx", ".xml", ".zip",
}


class CrawlError(RuntimeError):
    """Raised when the starting page cannot be crawled."""


@dataclass(frozen=True)
class Page:
    url: str
    title: str
    markdown: str


@dataclass(frozen=True)
class CrawlResult:
    pages: list[Page]
    errors: list[tuple[str, str]]


def normalize_url(url: str) -> str:
    """Return a canonical HTTP(S) crawl URL without query or fragment."""
    raw, _ = urldefrag(url.strip())
    parts = urlsplit(raw)
    if parts.scheme.lower() not in {"http", "https"} or not parts.netloc:
        raise ValueError(f"not an absolute HTTP(S) URL: {url}")
    path = re.sub(r"/{2,}", "/", parts.path or "/")
    if path != "/":
        path = path.rstrip("/")
    host = (parts.hostname or "").lower()
    port = parts.port
    netloc = host if port is None else f"{host}:{port}"
    return urlunsplit((parts.scheme.lower(), netloc, path, "", ""))


def _in_scope(candidate: str, start: str, scope: str) -> bool:
    target, root = urlsplit(candidate), urlsplit(start)
    if target.netloc != root.netloc:
        return False
    if scope == "host":
        return True
    base = root.path.rstrip("/")
    return target.path == base or target.path.startswith(base + "/")


def _looks_like_page(url: str) -> bool:
    path = urlsplit(url).path.lower()
    return not any(path.endswith(suffix) for suffix in SKIP_SUFFIXES)


def extract_page(html: str, url: str) -> tuple[Page, list[str]]:
    soup = BeautifulSoup(html, "html.parser")
    title_node = soup.find("h1") or soup.find("title")
    title = title_node.get_text(" ", strip=True) if title_node else url

    links = []
    for anchor in soup.find_all("a", href=True):
        try:
            links.append(normalize_url(urljoin(url, anchor["href"])))
        except (ValueError, TypeError):
            continue

    content = soup.find("main") or soup.find("article") or soup.body or soup
    for node in content.select(
        "script, style, noscript, nav, footer, form, button, svg, textarea, "
        "[aria-hidden='true'], .breadcrumb, .breadcrumbs"
    ):
        node.decompose()
    for node in content.select(".code-block-header"):
        node.decompose()
    first_heading = content.find("h1")
    if first_heading and first_heading.get_text(" ", strip=True) == title:
        first_heading.decompose()
    for node in content.find_all(href=True):
        node["href"] = urljoin(url, node["href"])
    for node in content.find_all(src=True):
        node["src"] = urljoin(url, node["src"])
    body = markdownify(str(content), heading_style="ATX", bullets="-")
    body = re.sub(r"\n[ \t]+\n", "\n\n", body)
    body = re.sub(r"\n{3,}", "\n\n", body).strip()
    return Page(url=url, title=title, markdown=body), links


def crawl(
    start_url: str,
    *,
    max_pages: int = 100,
    delay: float = 0.25,
    timeout: float = 20,
    scope: str = "path",
    respect_robots: bool = True,
    session: requests.Session | None = None,
    progress: Callable[[str], None] | None = None,
) -> CrawlResult:
    if max_pages < 1:
        raise ValueError("max_pages must be at least 1")
    start = normalize_url(start_url)
    client = session or requests.Session()
    client.headers.setdefault("User-Agent", USER_AGENT)

    robots: RobotFileParser | None = None
    if respect_robots:
        parts = urlsplit(start)
        robots = RobotFileParser(urlunsplit((parts.scheme, parts.netloc, "/robots.txt", "", "")))
        try:
            response = client.get(robots.url, timeout=timeout)
            robots.parse(response.text.splitlines() if response.ok else [])
        except requests.RequestException:
            robots = None

    queue = deque([start])
    queued = {start}
    pages: list[Page] = []
    errors: list[tuple[str, str]] = []
    while queue and len(pages) < max_pages:
        url = queue.popleft()
        if robots and not robots.can_fetch(USER_AGENT, url):
            errors.append((url, "blocked by robots.txt"))
            continue
        if progress:
            progress(url)
        if pages and delay:
            time.sleep(delay)
        try:
            response = client.get(url, timeout=timeout)
            response.raise_for_status()
            if "text/html" not in response.headers.get("Content-Type", ""):
                errors.append((url, "not an HTML page"))
                continue
            page, links = extract_page(response.text, response.url)
        except requests.RequestException as exc:
            errors.append((url, str(exc)))
            if url == start:
                raise CrawlError(f"could not fetch starting URL: {exc}") from exc
            continue
        pages.append(page)
        for link in links:
            if link not in queued and _looks_like_page(link) and _in_scope(link, start, scope):
                queued.add(link)
                queue.append(link)
    return CrawlResult(pages=pages, errors=errors)


def render_document(result: CrawlResult, start_url: str) -> str:
    if not result.pages:
        raise CrawlError("crawl produced no pages")
    title = result.pages[0].title
    chunks = [
        f"# {title}\n\nSource: <{normalize_url(start_url)}>\n\n"
        f"Pages captured: {len(result.pages)}"
    ]
    for page in result.pages:
        chunks.append(f"## {page.title}\n\nSource: <{page.url}>\n\n{page.markdown}")
    return "\n\n---\n\n".join(chunks).rstrip() + "\n"


def write_document(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(path)
