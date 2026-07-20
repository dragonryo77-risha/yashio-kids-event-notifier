"""通知済みイベント(URL)を記録し、重複通知を防ぐための状態ファイル管理。"""
import json
import os

STATE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "state.json")
MAX_KEEP = 1000  # 肥大化を防ぐため直近N件のみ保持


def load_seen_urls() -> set[str]:
    if not os.path.exists(STATE_PATH):
        return set()
    with open(STATE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return set(data.get("seen_urls", []))


def save_seen_urls(urls: list[str]) -> None:
    trimmed = urls[-MAX_KEEP:]
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump({"seen_urls": trimmed}, f, ensure_ascii=False, indent=2)
