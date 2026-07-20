"""スクレイピングしたイベントを蓄積する永続ストア。

- data/events.json: 内部データ(重複通知防止・カレンダー表示の両方に使う)
- docs/events.json: GitHub Pagesで公開するカレンダーページ用の同一データ

古いイベント(開催日と思われる日付が過去のもの)は自動的に間引く。
"""
from __future__ import annotations

import json
import os
from datetime import date, timedelta

_ROOT = os.path.join(os.path.dirname(__file__), "..")
DATA_PATH = os.path.join(_ROOT, "data", "events.json")
DOCS_PATH = os.path.join(_ROOT, "docs", "events.json")

KEEP_PAST_DAYS = 14   # 過去のイベントもしばらくは一覧に残す
MAX_EVENTS = 500


def load_events() -> dict[str, dict]:
    if not os.path.exists(DATA_PATH):
        return {}
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {e["url"]: e for e in data.get("events", [])}


def _sort_key(e: dict):
    return e.get("event_date") or e.get("published_at") or ""


def prune(events: dict[str, dict], today: date | None = None) -> dict[str, dict]:
    today = today or date.today()
    cutoff = (today - timedelta(days=KEEP_PAST_DAYS)).isoformat()

    def keep(e: dict) -> bool:
        d = e.get("event_date")
        if d is None:
            return True  # 日付不明なものは念のため残す(件数上限で間引かれる)
        return d >= cutoff

    filtered = {url: e for url, e in events.items() if keep(e)}
    ordered = sorted(filtered.values(), key=_sort_key, reverse=True)[:MAX_EVENTS]
    return {e["url"]: e for e in ordered}


def save_events(events: dict[str, dict]) -> None:
    ordered = sorted(events.values(), key=_sort_key)
    payload = {"events": ordered, "generated_at": date.today().isoformat()}

    for path in (DATA_PATH, DOCS_PATH):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
