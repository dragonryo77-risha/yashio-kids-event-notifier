"""処理の起点。PC上の run.ps1 から2段階で呼ばれる。

  python src/main.py collect  … 地域サイトを巡回し、未評価の新着を data/candidates.json に書き出す
  (この間に run.ps1 が Claude Code を実行し、候補の採点＋Web検索での大型イベント探しを行い
   data/picks.json を書き出す)
  python src/main.py notify   … data/picks.json の厳選イベントをLINEに縦1枚のランキングで通知する
  python src/main.py notify --dry-run … LINEに送らず、送信内容(JSON)を表示するだけ
"""
import json
import os
import sys
from datetime import date, timedelta

from date_utils import extract_event_date, parse_published_date
from filters import filter_events
from notifier import notify_picks
from scraper import collect_events
from sources import SOURCES
from store import load_events, load_seen_urls, prune, save_events, save_seen_urls

CALENDAR_URL = "https://dragonryo77-risha.github.io/yashio-kids-event-notifier/"

_ROOT = os.path.join(os.path.dirname(__file__), "..")
CANDIDATES_PATH = os.path.join(_ROOT, "data", "candidates.json")
PICKS_PATH = os.path.join(_ROOT, "data", "picks.json")

RECENT_PICK_DAYS = 60  # この期間内に通知済みのイベントは再通知しないようClaudeに伝える
STALE_ARTICLE_DAYS = 45  # タイトルに日付がなく、掲載からこれ以上経った記事は終了済みとみなす


def collect() -> None:
    today = date.today()
    existing = load_events()
    seen = set(load_seen_urls()) | set(existing)
    stale_before = (today - timedelta(days=STALE_ARTICLE_DAYS)).isoformat()
    today_iso = today.isoformat()

    scraped = collect_events(SOURCES)
    print(f"取得件数: {len(scraped)}")
    reportable = filter_events(scraped)
    print(f"除外キーワードフィルタ後: {len(reportable)}")

    candidates = []
    seen_urls = set()
    for e in reportable:
        if e["url"] in seen or e["url"] in seen_urls:
            continue
        seen_urls.add(e["url"])
        title_date = extract_event_date(e["title"], today)
        published = parse_published_date(e["published_at"], today)
        if (title_date and title_date < today_iso) or (not title_date and published and published < stale_before):
            continue  # 明らかに終わったイベント
        e["event_date_hint"] = title_date or published
        candidates.append(e)
    print(f"未評価の新着: {len(candidates)}")

    since = (today - timedelta(days=RECENT_PICK_DAYS)).isoformat()
    recent_picks = sorted(
        {e["title"] for e in existing.values() if e.get("pick") and e.get("first_seen", "") >= since}
    )

    with open(CANDIDATES_PATH, "w", encoding="utf-8") as f:
        json.dump(
            {"today": today_iso, "candidates": candidates, "recent_picks": recent_picks,
             "scraped_urls": sorted(seen_urls)},
            f, ensure_ascii=False, indent=2,
        )
    # 前回の結果が残っていると、Claudeの実行に失敗した場合に古い内容を再通知してしまうため消しておく
    if os.path.exists(PICKS_PATH):
        os.remove(PICKS_PATH)


def notify(dry_run: bool = False) -> None:
    today = date.today()
    today_iso = today.isoformat()
    existing = load_events()

    with open(CANDIDATES_PATH, "r", encoding="utf-8") as f:
        collected = json.load(f)
    candidates = collected["candidates"]
    if not os.path.exists(PICKS_PATH):
        raise RuntimeError("data/picks.json がありません(Claudeによる選定が失敗した可能性があります)")
    with open(PICKS_PATH, "r", encoding="utf-8") as f:
        picks = json.load(f)["picks"]

    # 評価済みの候補はすべて蓄積(次回以降に再評価・再通知しないため)。カレンダーにも載る
    for c in candidates:
        c["event_date"] = c.pop("event_date_hint", None)
        c["first_seen"] = today_iso
        c.setdefault("recommendation", "")
        existing.setdefault(c["url"], c)

    notify_list = []
    for p in picks:
        if p.get("end_date") and p["end_date"] < today_iso:
            continue  # 既に終わったイベント(終了日不明の開催中イベントは残す)
        e = existing.get(p["url"], {})
        e.update({
            "title": p["title"],
            "url": p["url"],
            "source": e.get("source") or p.get("source") or "Web検索",
            "published_at": e.get("published_at", ""),
            "image_url": e.get("image_url", ""),
            "event_date": p.get("event_date"),
            "end_date": p.get("end_date"),
            "place": p.get("place", ""),
            "recommendation": p.get("reason", ""),
            "stars": p.get("stars", 0),
            "pick": True,
            "first_seen": e.get("first_seen", today_iso),
        })
        existing[p["url"]] = e
        notify_list.append(e)
    print(f"通知対象(厳選): {len(notify_list)}件")

    if not dry_run:
        save_events(prune(existing, today))
        save_seen_urls(load_seen_urls() + collected["scraped_urls"] + [p["url"] for p in picks])
    notify_picks(notify_list, CALENDAR_URL, dry_run=dry_run)


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    if command == "collect":
        collect()
    elif command == "notify":
        notify(dry_run="--dry-run" in sys.argv)
    else:
        print(__doc__)
        sys.exit(1)
