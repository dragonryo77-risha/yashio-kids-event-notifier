"""LINE Messaging API のブロードキャスト配信で自分(Botを友だち追加した自分)に通知する。

LINE Notifyは2025年3月末で終了したため、LINE公式アカウント(Messaging API)の
ブロードキャスト機能を使う。ブロードキャストは「友だち全員」への配信だが、
このBotを友だち追加するのは基本的に自分だけなので、実質的に自分専用の通知になる。

見た目重視のため、テキストではなくFlex Message(カード形式)で送る。
"""
import os

import requests

LINE_BROADCAST_URL = "https://api.line.me/v2/bot/message/broadcast"
BUBBLES_PER_CAROUSEL = 10
MAX_CAROUSELS = 4  # + サマリーのテキストメッセージ1件 = 合計5件(ブロードキャスト上限)
PLACEHOLDER_IMAGE = "https://placehold.co/1024x682?text=NO+IMAGE"


def _bubble(e: dict) -> dict:
    image_url = e.get("image_url") or PLACEHOLDER_IMAGE
    date_text = e.get("event_date") or e.get("published_at") or "日付不明"
    body_contents = [
        {"type": "text", "text": date_text, "size": "sm", "color": "#e91e63", "weight": "bold"},
        {"type": "text", "text": e["title"], "wrap": True, "weight": "bold", "size": "md"},
        {"type": "text", "text": e["source"], "size": "xs", "color": "#999999"},
    ]
    if e.get("recommendation"):
        body_contents.append({
            "type": "text",
            "text": f"💡 {e['recommendation']}",
            "wrap": True,
            "size": "xs",
            "color": "#555555",
            "margin": "md",
        })
    return {
        "type": "bubble",
        "hero": {
            "type": "image",
            "url": image_url,
            "size": "full",
            "aspectRatio": "20:13",
            "aspectMode": "cover",
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": body_contents,
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "button",
                    "style": "primary",
                    "color": "#e91e63",
                    "action": {"type": "uri", "label": "詳細を見る", "uri": e["url"]},
                }
            ],
        },
    }


def build_messages(new_events: list[dict], calendar_url: str | None) -> list[dict]:
    carousels: list[dict] = []
    for i in range(0, len(new_events), BUBBLES_PER_CAROUSEL):
        chunk = new_events[i:i + BUBBLES_PER_CAROUSEL]
        carousels.append({
            "type": "flex",
            "altText": f"子供向けイベント新着 {len(chunk)}件",
            "contents": {"type": "carousel", "contents": [_bubble(e) for e in chunk]},
        })
        if len(carousels) >= MAX_CAROUSELS:
            break

    shown = min(len(new_events), MAX_CAROUSELS * BUBBLES_PER_CAROUSEL)
    remaining = len(new_events) - shown
    summary = f"【子供向けイベント通知】新着 {len(new_events)} 件"
    if remaining > 0:
        summary += f"\n(カードは{shown}件のみ表示。残り{remaining}件はカレンダーで確認できます)"
    if calendar_url:
        summary += f"\n\nカレンダーで見る:\n{calendar_url}"

    messages: list[dict] = [{"type": "text", "text": summary}]
    messages.extend(carousels)
    return messages[:5]


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


def notify_new_events(new_events: list[dict], calendar_url: str | None = None) -> None:
    if not new_events:
        print("新着イベントなし。通知はスキップします。")
        return
    messages = build_messages(new_events, calendar_url)
    send_line_broadcast(messages)
    print(f"LINEに{len(new_events)}件の新着イベントを通知しました。")
