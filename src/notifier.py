"""LINE Messaging API のブロードキャスト配信で自分(Botを友だち追加した自分)に通知する。

LINE Notifyは2025年3月末で終了したため、LINE公式アカウント(Messaging API)の
ブロードキャスト機能を使う。ブロードキャストは「友だち全員」への配信だが、
このBotを友だち追加するのは基本的に自分だけなので、実質的に自分専用の通知になる。

横スワイプのカルーセルはスマホで見づらいため、厳選イベントを「縦1枚のランキングカード」
(Flex Messageのbubble 1枚)にまとめて送る。各行をタップすると記事が開く。
"""
import json
import os
from datetime import date

import requests

LINE_BROADCAST_URL = "https://api.line.me/v2/bot/message/broadcast"
MAX_ROWS = 8
ACCENT = "#e91e63"
RANK_MARKS = ["①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧"]
WEEKDAYS = "月火水木金土日"


def _format_date(e: dict) -> str:
    start = e.get("event_date")
    if not start:
        return "日程は記事で確認"

    def fmt(iso: str) -> str:
        d = date.fromisoformat(iso)
        return f"{d.month}/{d.day}({WEEKDAYS[d.weekday()]})"

    end = e.get("end_date")
    if end and end != start:
        return f"{fmt(start)}〜{fmt(end)}"
    return fmt(start)


def _row(rank: int, e: dict) -> dict:
    stars = max(1, min(3, int(e.get("stars") or 1)))
    meta = _format_date(e)
    if e.get("place"):
        meta += f"  📍{e['place']}"
    contents = [
        {"type": "text", "text": meta, "size": "xs", "color": ACCENT, "weight": "bold", "wrap": True},
        {
            "type": "text",
            "text": f"{RANK_MARKS[rank]} {e['title']}",
            "size": "md", "weight": "bold", "wrap": True, "maxLines": 3,
        },
        {"type": "text", "text": "★" * stars + "☆" * (3 - stars), "size": "xs", "color": "#f5a623"},
    ]
    if e.get("recommendation"):
        contents.append({
            "type": "text", "text": e["recommendation"], "size": "sm", "color": "#555555", "wrap": True,
        })
    contents.append({"type": "text", "text": "タップで詳細 ›", "size": "xxs", "color": "#999999", "align": "end"})
    return {
        "type": "box",
        "layout": "vertical",
        "spacing": "xs",
        "paddingAll": "md",
        "contents": contents,
        "action": {"type": "uri", "label": "詳細", "uri": e["url"]},
    }


def build_messages(picks: list[dict], calendar_url: str | None) -> list[dict]:
    if not picks:
        text = "【こどもイベント】今週は特におすすめできる新着イベントはありませんでした。"
        if calendar_url:
            text += f"\n\n全件はカレンダーで見られます:\n{calendar_url}"
        return [{"type": "text", "text": text}]

    rows: list[dict] = []
    for i, e in enumerate(picks[:MAX_ROWS]):
        if i > 0:
            rows.append({"type": "separator"})
        rows.append(_row(i, e))

    bubble = {
        "type": "bubble",
        "size": "giga",
        "header": {
            "type": "box",
            "layout": "vertical",
            "backgroundColor": ACCENT,
            "paddingAll": "lg",
            "contents": [
                {"type": "text", "text": "🎈 今週のこどもイベント厳選", "color": "#ffffff",
                 "weight": "bold", "size": "lg"},
                {"type": "text", "text": f"子どもが楽しめる・規模の大きい催しを{min(len(picks), MAX_ROWS)}件",
                 "color": "#ffffff", "size": "xs"},
            ],
        },
        "body": {"type": "box", "layout": "vertical", "paddingAll": "none", "contents": rows},
    }
    if calendar_url:
        bubble["footer"] = {
            "type": "box",
            "layout": "vertical",
            "contents": [{
                "type": "button", "style": "link", "height": "sm",
                "action": {"type": "uri", "label": "カレンダーで全件を見る", "uri": calendar_url},
            }],
        }
    alt = "今週のこどもイベント厳選: " + " / ".join(e["title"][:20] for e in picks[:3])
    return [{"type": "flex", "altText": alt[:400], "contents": bubble}]


def send_line_broadcast(messages: list[dict]) -> None:
    token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
    if not token:
        raise RuntimeError("環境変数 LINE_CHANNEL_ACCESS_TOKEN が設定されていません")

    res = requests.post(
        LINE_BROADCAST_URL,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={"messages": messages},
        timeout=20,
    )
    if res.status_code != 200:
        raise RuntimeError(f"LINE通知の送信に失敗しました: {res.status_code} {res.text}")


def notify_picks(picks: list[dict], calendar_url: str | None = None, dry_run: bool = False) -> None:
    messages = build_messages(picks, calendar_url)
    if dry_run:
        print(json.dumps(messages, ensure_ascii=False, indent=2))
        return
    send_line_broadcast(messages)
    print(f"LINEに厳選{len(picks[:MAX_ROWS])}件を通知しました。")
