"""各サイトのHTML構造に合わせたパーサー。

Event = {"title": str, "url": str, "published_at": str, "source": str}
"""
from __future__ import annotations

import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; YashioKidsEventNotifier/1.0; personal use)"}
TIMEOUT = 20


def fetch(url: str) -> str:
    res = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    res.raise_for_status()
    res.encoding = res.apparent_encoding
    return res.text


def parse_goguynet(html: str, source_label: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    events = []
    for box in soup.select("div.centerListBox01"):
        a = box.select_one("a.itemTitle01")
        if not a or not a.get("href"):
            continue
        title_el = a.select_one("h1.itemTitle01In, h2.itemTitle01In")
        title = title_el.get_text(strip=True) if title_el else a.get_text(strip=True)
        date_el = a.select_one(".listDate01")
        published_at = date_el.get_text(strip=True) if date_el else ""
        if not title:
            continue
        events.append({
            "title": title,
            "url": a["href"].strip(),
            "published_at": published_at,
            "source": source_label,
        })
    return events


def parse_yashion(html: str, source_label: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    events = []
    for article in soup.select("article.entry"):
        a = article.select_one("h2.ttl a")
        if not a or not a.get("href"):
            continue
        time_el = article.select_one("time")
        published_at = time_el.get_text(strip=True) if time_el else ""
        events.append({
            "title": a.get_text(strip=True),
            "url": a["href"].strip(),
            "published_at": published_at,
            "source": source_label,
        })
    return events


PARSERS = {
    "goguynet": parse_goguynet,
    "yashion": parse_yashion,
}


def collect_events(sources: list[dict]) -> list[dict]:
    all_events = []
    for src in sources:
        parser = PARSERS.get(src["type"])
        if parser is None:
            continue
        try:
            html = fetch(src["url"])
            all_events.extend(parser(html, src["label"]))
        except Exception as e:
            print(f"[WARN] {src['label']} の取得に失敗しました: {e}")
    return all_events
