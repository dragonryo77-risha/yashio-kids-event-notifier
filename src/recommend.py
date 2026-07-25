"""Claude APIを使い、新着イベントごとに「開催日の判定」と「おすすめポイント」を生成する。

タイトルの正規表現だけでの日付抽出は、チケット先行販売日・受付開始日・申込締切日
などを開催日と誤認識しやすい(例:「観覧チケットの先行販売は8月24日から」を8月24日開催と誤判定)。
そのため、タイトル全体の文脈をClaudeに読ませて「実際にイベントが開催される日」を
判定させ、正規表現の抽出結果は参考情報としてのみ渡す。

あわせて、未就学児(2歳前後)を連れて行く親向けに、屋内/屋外・混雑しそうか・対象年齢の
適性・体験や学びの要素など、行くかどうか判断しやすい「おすすめポイント」を生成する。
"""
import json
import os
from datetime import date

from anthropic import Anthropic

MODEL = "claude-opus-4-8"
MAX_EVENTS_PER_CALL = 30  # 1回のAPI呼び出しで扱う件数の上限(念のため)

_SCHEMA = {
    "type": "object",
    "properties": {
        "results": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "index": {"type": "integer"},
                    "event_date": {"type": ["string", "null"]},
                    "recommendation": {"type": "string"},
                },
                "required": ["index", "event_date", "recommendation"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["results"],
    "additionalProperties": False,
}


def _build_prompt(events: list[dict], today: date) -> str:
    lines = []
    for i, e in enumerate(events):
        hint = f" / 正規表現による参考日付(誤りの可能性あり): {e['event_date']}" if e.get("event_date") else ""
        lines.append(f"{i}. {e['title']} / 情報源: {e['source']} / 掲載日: {e['published_at']}{hint}")

    return (
        f"今日の日付は{today.isoformat()}です。\n"
        "以下は地域のイベント情報一覧です。子供向けとは限らず、地域の祭り・店舗イベント・"
        "季節の催しなど一般的なものも含まれます。\n\n"
        "各イベントについて、次の2つを判定してください。\n\n"
        "【1. event_date(実際の開催日)】\n"
        "タイトルから「イベントが実際に開催される日」をYYYY-MM-DD形式で判定してください。\n"
        "重要な注意点:\n"
        "- 「チケット先行販売は8月24日から」「受付開始は◯月◯日」「申込締切は◯月◯日」のような"
        "日付は開催日ではありません。誤って開催日として使わないでください。\n"
        "- 開催期間がある場合は開始日を使ってください。\n"
        "- 年が明記されていない場合は、今日の日付を基準に妥当な年(基本的には今年、"
        "既に大きく過ぎていそうな月日なら来年)を推定してください。\n"
        "- タイトルから開催日を特定できない場合は、無理に推測せずnullにしてください。\n"
        "- 「正規表現による参考日付」が付いている場合がありますが、あくまで参考(誤っている"
        "可能性あり)です。タイトルの文脈を優先してください。\n\n"
        "【2. recommendation(おすすめポイント)】\n"
        "2歳2ヶ月の子供がいる家族向けに、日本語で1〜2文、簡潔に書いてください。\n"
        "- 子供(2歳前後)を連れて行くのに向いているか(屋内/屋外、混雑や待ち時間の予想、"
        "対象年齢や安全面)\n"
        "- 子供が体験できること・学びがありそうな要素(工作、自然観察、職業体験、"
        "科学・生き物とのふれあいなど)があれば積極的に触れてください\n"
        "- 子供向けの内容でない場合は、大人だけ/家族全体で楽しめそうな点、話題性や珍しさなど、"
        "行く価値があるかどうかの判断材料\n"
        "タイトルだけでは開催内容が分からない場合は、一般的な傾向から推測して構いません。\n\n"
        "イベント一覧:\n" + "\n".join(lines)
    )


def analyze_events(events: list[dict], today: date | None = None) -> dict[str, dict]:
    """event["url"] -> {"event_date": str|None, "recommendation": str} のdictを返す。失敗時は空dict。"""
    if not events:
        return {}
    today = today or date.today()
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("[WARN] ANTHROPIC_API_KEY が未設定のため、開催日判定・おすすめポイント生成をスキップします。")
        return {}

    client = Anthropic()
    result: dict[str, dict] = {}

    for i in range(0, len(events), MAX_EVENTS_PER_CALL):
        chunk = events[i:i + MAX_EVENTS_PER_CALL]
        try:
            response = client.messages.create(
                model=MODEL,
                max_tokens=4096,
                output_config={"format": {"type": "json_schema", "schema": _SCHEMA}},
                messages=[{"role": "user", "content": _build_prompt(chunk, today)}],
            )
            text = next(b.text for b in response.content if b.type == "text")
            data = json.loads(text)
            for item in data["results"]:
                idx = item["index"]
                if 0 <= idx < len(chunk):
                    result[chunk[idx]["url"]] = {
                        "event_date": item.get("event_date") or None,
                        "recommendation": item.get("recommendation", ""),
                    }
        except Exception as e:
            print(f"[WARN] 開催日判定・おすすめポイント生成に失敗しました: {e}")

    return result
