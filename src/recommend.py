"""Claude APIを使い、新着イベントごとに「おすすめポイント」を生成する。

未就学児(2歳前後)を連れて行く親向けに、屋内/屋外・混雑しそうか・対象年齢の
適性など、判断に役立つ具体的な観点を1〜2文で返してもらう。
"""
import json
import os

from anthropic import Anthropic

MODEL = "claude-opus-4-8"
MAX_EVENTS_PER_CALL = 30  # 1回のAPI呼び出しで扱う件数の上限(念のため)

_SCHEMA = {
    "type": "object",
    "properties": {
        "recommendations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "index": {"type": "integer"},
                    "recommendation": {"type": "string"},
                },
                "required": ["index", "recommendation"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["recommendations"],
    "additionalProperties": False,
}


def _build_prompt(events: list[dict]) -> str:
    lines = [
        f"{i}. {e['title']} / 情報源: {e['source']} / 掲載日: {e['published_at']}"
        for i, e in enumerate(events)
    ]
    return (
        "以下は地域のイベント情報一覧です。子供向けとは限らず、地域の祭り・店舗イベント・"
        "季節の催しなど一般的なものも含まれます。\n"
        "2歳2ヶ月の子供がいる家族向けに、それぞれのイベントの「おすすめポイント」を"
        "日本語で1〜2文、簡潔に書いてください。以下を踏まえてください:\n"
        "- 子供(2歳前後)を連れて行くのに向いているか(屋内/屋外、混雑や待ち時間の予想、"
        "対象年齢や安全面)\n"
        "- 子供向けの内容でない場合は、大人だけ/家族全体で楽しめそうな点、話題性や珍しさなど、"
        "行く価値があるかどうかの判断材料\n"
        "タイトルだけでは開催内容が分からない場合は、一般的な傾向から推測して構いません。\n\n"
        "イベント一覧:\n" + "\n".join(lines)
    )


def generate_recommendations(events: list[dict]) -> dict[str, str]:
    """event["url"] -> おすすめポイント文 のdictを返す。失敗時は空dict。"""
    if not events:
        return {}
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("[WARN] ANTHROPIC_API_KEY が未設定のため、おすすめポイントの生成をスキップします。")
        return {}

    client = Anthropic()
    result: dict[str, str] = {}

    for i in range(0, len(events), MAX_EVENTS_PER_CALL):
        chunk = events[i:i + MAX_EVENTS_PER_CALL]
        try:
            response = client.messages.create(
                model=MODEL,
                max_tokens=4096,
                output_config={"format": {"type": "json_schema", "schema": _SCHEMA}},
                messages=[{"role": "user", "content": _build_prompt(chunk)}],
            )
            text = next(b.text for b in response.content if b.type == "text")
            data = json.loads(text)
            for item in data["recommendations"]:
                idx = item["index"]
                if 0 <= idx < len(chunk):
                    result[chunk[idx]["url"]] = item["recommendation"]
        except Exception as e:
            print(f"[WARN] おすすめポイントの生成に失敗しました: {e}")

    return result
