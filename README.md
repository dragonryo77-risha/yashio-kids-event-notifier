# 八潮駅から電車1.5時間圏 こどもイベント厳選通知

八潮市周辺〜東京23区の地域ニュースサイト・自治体サイトを毎週巡回し、さらにWeb検索で大型イベントも探したうえで、
**「2〜3歳の子どもが本当に楽しめる」「規模が大きい」イベントだけを5〜7件に厳選**してLINEに通知する個人用ツール。

## 仕組み(2026-09-26 改修)

PC上のWindowsタスクスケジューラ「KidsEventNotifier」が毎週水曜7:30に `run_hidden.vbs` → `run.ps1` を実行する(PCが起動/スリープ中である必要あり)。

1. `python src/main.py collect` … `src/sources.py` のサイトを巡回し、`src/filters.py` で明らかな対象外を除外。
   一度見た記事は `data/seen_urls.json` に記録して再評価しない。終了済みと明らかな記事も除外し、`data/candidates.json` に書き出す
2. `claude -p`(Claude Code、追加費用なし) … `prompt.md` の基準で候補を採点し、Web検索で候補外の大型イベント
   (車両基地公開・動物園/水族館の特別企画・幕張メッセ等のこどもフェスなど)も探して、上位を `data/picks.json` に書き出す
3. `python src/main.py notify` … 厳選イベントをLINEに**縦1枚のランキングカード**で通知(横スワイプなし、各行タップで詳細)。
   `data/events.json` / `docs/events.json` を更新し、GitHubへpush → カレンダーページ(GitHub Pages)にも⭐付きで反映

実行ログは `logs/last_run.log`。以前のGitHub Actions + Claude API方式(API費用がかかり、実際にはAPIキー未設定で厳選が機能していなかった)は廃止した。

## セットアップ(PC側)

1. **LINEトークンを置く**: [LINE Developers Console](https://developers.line.biz/console/) → 該当チャネル →「Messaging API設定」→「チャネルアクセストークン(長期)」を発行(再発行)し、
   値だけをこのフォルダの `line_token.txt` に保存する(Gitには載らない設定済み)
2. **Pythonライブラリ**: `python -m pip install -r requirements.txt`
3. **動作確認**: `run.ps1` を右クリック →「PowerShellで実行」。LINEに届けばOK
4. 厳選基準を変えたいとき → `prompt.md` を編集(対象年齢・選ばないもの・件数など)
5. LINEに送らず中身だけ確認したいとき → `python src/main.py notify --dry-run`

## ファイル一覧・役割

```
yashio-kids-event-notifier/
├── README.md             このファイル
├── run.ps1               毎週の処理全体(収集→Claude厳選→LINE通知→GitHub反映)
├── run_hidden.vbs        タスクスケジューラ用(PowerShellの窓を出さずにrun.ps1を実行)
├── prompt.md             Claude Codeへの厳選基準の指示書(ここを直すと選ばれ方が変わる)
├── line_token.txt        LINEトークン(各自作成・Git管理外)
├── requirements.txt      Pythonの依存ライブラリ一覧
├── src/
│   ├── main.py             collect / notify の起点
│   ├── sources.py          巡回対象サイトの一覧
│   ├── scraper.py          各サイトのHTMLからイベント情報を抜き出す
│   ├── filters.py          明らかな対象外(求人・事件・相談会など)を除外するキーワード
│   ├── date_utils.py       タイトルから開催日の参考値を推定
│   ├── notifier.py         LINEに縦1枚ランキングで通知
│   └── store.py            イベント蓄積・既読URL管理
├── data/events.json      蓄積データ / data/seen_urls.json 既読URL(自動更新)
└── docs/                 GitHub Pagesのカレンダーページ
```

## 注意点

- 対象サイトのHTML構造が変わるとスクレイピングが失敗することがあります(その場合は`logs/last_run.log`にWARNとして出力され、他のサイトの処理は継続されます)。動かなくなったら `src/scraper.py` の該当パーサーを更新してください。
- あくまで個人・私的利用を想定しています。取得したデータの再配布や商用利用はしないでください。
- イベントの正確な開催日時は各記事の本文に書かれていることが多いため、通知に含まれるリンク先で必ず確認してください(通知に出る日付は記事の掲載日であり、開催日そのものではない場合があります)。
