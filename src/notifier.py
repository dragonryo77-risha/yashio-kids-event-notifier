"""LINE Messaging API のブロードキャスト配信で自分(Botを友だち追加した自分)に通知する。

LINE Notifyは2025年3月末で終了したため、LINE公式アカウント(Messaging API)の
ブロードキャスト機能を使う。ブロードキャストは「友だち全員」への配信だが、
このBotを友だち追加するのは基本的に自分だけなので、実質的に自分専用の通知になる。
"""
import os

import requests

LINE_BROADCAST_URL = "https://api.line.me/v2/bot/message/broadcast"
MAX_MESSAGES_PER_CALL = 5
MAX_CHARS_PER_MESSAGE = 4500  # LINEの上限5000に対して余裕を持たせる
EVENTS_PER_CHUNK = 15


def _format_event(e: dict) -> str:
    date_part = f"[{e['published_at']}] " if e["published_at"] else ""
    return f"{date_part}{e['title']}\n({e['source']})\n{e['url']}"


def build_messages(new_events: list[dict]) -> list[str]:
    header = f"【子供向けイベント通知】新着 {len(new_events)} 件\n\n"
    chunks: list[str] = []
    buf = header
    count_in_buf = 0
    for e in new_events:
        block = _format_event(e) + "\n\n"
        if count_in_buf >= EVENTS_PER_CHUNK or len(buf) + len(block) > MAX_CHARS_PER_MESSAGE:
            chunks.append(buf.rstrip())
            buf = ""
            count_in_buf = 0
        buf += block
        count_in_buf += 1
    if buf.strip():
        chunks.append(buf.rstrip())
    return chunks[:MAX_MESSAGES_PER_CALL]


def send_line_broadcast(messages: list[str]) -> None:
    token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
    if not token:
        raise RuntimeError("環境変数 LINE_CHANNEL_ACCESS_TOKEN が設定されていません")

    payload = {"messages": [{"type": "text", "text": m} for m in messages]}
    res = requests.post(
        LINE_BROADCAST_URL,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=20,
    )
    if res.status_code != 200:
        raise RuntimeError(f"LINE通知の送信に失敗しました: {res.status_code} {res.text}")


def notify_new_events(new_events: list[dict]) -> None:
    if not new_events:
        print("新着イベントなし。通知はスキップします。")
        return
    messages = build_messages(new_events)
    send_line_broadcast(messages)
    print(f"LINEに{len(new_events)}件の新着イベントを通知しました。")
