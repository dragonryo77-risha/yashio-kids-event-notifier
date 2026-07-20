# 監視対象サイト一覧。
# type="goguynet" は号外NET系(地域ニュースサイト)の「イベント」カテゴリページ。
# type="yashion"  は八潮市公式ポータル「やしおん」のイベントページ。
# いずれも公開されている地域ニュース/イベント告知ページで、個人の情報収集目的での定期巡回を想定。
# 対象を増やしたい場合はこのリストに追記するだけでよい(goguynet系は同一テンプレートのため
# サブドメインを変えるだけで動く)。

SOURCES = [
    # --- 地元(八潮・草加・三郷・越谷・松戸) ---
    {"type": "yashion", "label": "やしおん(八潮市公式)", "url": "https://yashion.jp/event/"},
    {"type": "goguynet", "label": "号外NET 三郷市・八潮市・吉川市",
     "url": "https://misato-yashio.goguynet.jp/category/cat_event/"},
    {"type": "goguynet", "label": "号外NET 草加市", "url": "https://soka.goguynet.jp/category/cat_event/"},
    {"type": "goguynet", "label": "号外NET 越谷市", "url": "https://koshigaya.goguynet.jp/category/cat_event/"},
    {"type": "goguynet", "label": "号外NET 松戸市", "url": "https://matsudo.goguynet.jp/category/cat_event/"},

    # --- 東京23区(八潮駅から電車1.5時間圏の主要エリア) ---
    {"type": "goguynet", "label": "号外NET 足立区", "url": "https://adachi.goguynet.jp/category/cat_event/"},
    {"type": "goguynet", "label": "号外NET 台東区", "url": "https://taito.goguynet.jp/category/cat_event/"},
    {"type": "goguynet", "label": "号外NET 江東区", "url": "https://koto.goguynet.jp/category/cat_event/"},
    {"type": "goguynet", "label": "号外NET 葛飾区", "url": "https://katsushika.goguynet.jp/category/cat_event/"},
    {"type": "goguynet", "label": "号外NET 荒川区", "url": "https://arakawa.goguynet.jp/category/cat_event/"},
    {"type": "goguynet", "label": "号外NET 墨田区", "url": "https://sumida.goguynet.jp/category/cat_event/"},
    {"type": "goguynet", "label": "号外NET 江戸川区", "url": "https://edogawa.goguynet.jp/category/cat_event/"},
]
