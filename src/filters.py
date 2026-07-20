"""子供(未就学児)向け・ファミリー向けらしいイベントかどうかをタイトルから判定する。

完璧な精度は出せないので「見逃しを減らす」方向に倒し、
明らかに対象外なものだけ除外する設計にしている。
"""

# タイトルにこれらの語が含まれていれば子供・ファミリー向けの可能性が高い
KID_KEYWORDS = [
    "子ども", "子供", "こども", "キッズ", "親子", "ファミリー", "赤ちゃん", "ベビー",
    "幼児", "児童", "保育園", "幼稚園", "おやこ", "0歳", "1歳", "2歳", "3歳",
    "未就学", "プラネタリウム", "動物園", "水族館", "工作教室", "縁日",
]

# 地域の一般的なお祭り・季節イベントも未就学児連れで行きやすいので含める
FAMILY_FRIENDLY_EVENT_KEYWORDS = [
    "夏祭り", "夏まつり", "盆踊り", "花火大会", "フリーマーケット", "マルシェ",
    "まつり", "祭り", "縁日", "運動会", "収穫祭", "産業まつり",
]

# タイトルにこれらが含まれる場合は対象外(大人向け・業者向けなど)とみなす
NG_KEYWORDS = [
    "婚活", "出会い", "セミナー(法人", "求人説明会", "就職説明会", "投資セミナー",
]


def is_kid_friendly(title: str) -> bool:
    if any(ng in title for ng in NG_KEYWORDS):
        return False
    if any(k in title for k in KID_KEYWORDS):
        return True
    if any(k in title for k in FAMILY_FRIENDLY_EVENT_KEYWORDS):
        return True
    return False


def filter_events(events: list[dict]) -> list[dict]:
    return [e for e in events if is_kid_friendly(e["title"])]
