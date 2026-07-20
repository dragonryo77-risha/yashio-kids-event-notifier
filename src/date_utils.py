"""タイトル文字列から開催日をベストエフォートで推定する。

記事の掲載日と実際の開催日は別物であることが多いため、
タイトルに含まれる日付表記(例: "7/26", "7月26日(土)")を優先的に使う。
見つからない場合は None を返し、呼び出し側で「日付不明」として扱う。
"""
from __future__ import annotations

import re
from datetime import date, timedelta

_PATTERNS = [
    re.compile(r"(\d{1,2})月(\d{1,2})日"),
    re.compile(r"(\d{1,2})/(\d{1,2})(?!\d)"),
]

# 掲載日が近すぎる過去になった場合は年をまたいだとみなす閾値(日数)
_ROLLOVER_THRESHOLD_DAYS = 200


def extract_event_date(title: str, today: date | None = None) -> str | None:
    today = today or date.today()
    for pattern in _PATTERNS:
        m = pattern.search(title)
        if not m:
            continue
        month, day = int(m.group(1)), int(m.group(2))
        if not (1 <= month <= 12):
            continue
        year = today.year
        try:
            candidate = date(year, month, day)
        except ValueError:
            continue
        if (today - candidate).days > _ROLLOVER_THRESHOLD_DAYS:
            try:
                candidate = date(year + 1, month, day)
            except ValueError:
                continue
        return candidate.isoformat()
    return None


def parse_published_date(published_at: str, today: date | None = None) -> str | None:
    """'2026/07/20 07:08' や '2026年7月20日(月)' のような掲載日文字列をISO日付に変換する。"""
    m = re.search(r"(\d{4})[/年](\d{1,2})[/月](\d{1,2})", published_at)
    if not m:
        return None
    try:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3))).isoformat()
    except ValueError:
        return None
