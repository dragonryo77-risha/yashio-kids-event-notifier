from filters import filter_events
from notifier import notify_new_events
from scraper import collect_events
from sources import SOURCES
from state import load_seen_urls, save_seen_urls


def main() -> None:
    seen = load_seen_urls()

    all_events = collect_events(SOURCES)
    print(f"取得件数: {len(all_events)}")

    kid_events = filter_events(all_events)
    print(f"子供向けフィルタ後: {len(kid_events)}")

    new_events = [e for e in kid_events if e["url"] not in seen]
    print(f"未通知の新着: {len(new_events)}")

    notify_new_events(new_events)

    updated_seen = list(seen) + [e["url"] for e in new_events]
    save_seen_urls(updated_seen)


if __name__ == "__main__":
    main()
