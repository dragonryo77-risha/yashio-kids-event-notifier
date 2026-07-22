from datetime import date

from date_utils import extract_event_date, parse_published_date
from filters import filter_events
from notifier import notify_new_events
from recommend import generate_recommendations
from scraper import collect_events
from sources import SOURCES
from store import load_events, prune, save_events

CALENDAR_URL = "https://dragonryo77-risha.github.io/yashio-kids-event-notifier/"


def main() -> None:
    today = date.today()
    existing = load_events()

    scraped = collect_events(SOURCES)
    print(f"取得件数: {len(scraped)}")

    reportable_events = filter_events(scraped)
    print(f"報告対象フィルタ後: {len(reportable_events)}")

    new_events = []
    for e in reportable_events:
        if e["url"] in existing:
            continue
        event_date = extract_event_date(e["title"], today) or parse_published_date(e["published_at"], today)
        e["event_date"] = event_date
        e["first_seen"] = today.isoformat()
        new_events.append(e)
        existing[e["url"]] = e
    print(f"未通知の新着: {len(new_events)}")

    today_iso = today.isoformat()
    notify_events = [e for e in new_events if not e["event_date"] or e["event_date"] >= today_iso]
    skipped = len(new_events) - len(notify_events)
    if skipped:
        print(f"開催日が本日より前のため通知から除外: {skipped}件")

    recommendations = generate_recommendations(notify_events)
    for e in notify_events:
        e["recommendation"] = recommendations.get(e["url"], "")

    existing = prune(existing, today)
    save_events(existing)

    notify_new_events(notify_events, CALENDAR_URL)


if __name__ == "__main__":
    main()
