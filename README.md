# 八潮駅から電車1.5時間圏 子供向けイベント通知

八潮市周辺〜東京23区の地域ニュースサイト・自治体サイトを毎日自動巡回し、
子供(未就学児)・ファミリー向けと思われる新着イベントをLINEに通知する個人用ツール。

## 仕組み

- `src/sources.py` に登録したサイトを毎日1回スクレイピング
- `src/filters.py` のキーワードで子供・ファミリー向けらしいものを抽出
- タイトルから開催日をベストエフォートで推定(`src/date_utils.py`)
- これまでに見つけたイベントは `data/events.json`(内部用)/ `docs/events.json`(カレンダーページ用)に蓄積し、重複通知を防止
- 新着があれば LINE Messaging API の「ブロードキャスト配信」でカード形式(Flex Message)で通知
- GitHub Pages(`docs/`フォルダ)でカレンダー形式の一覧ページを公開
- GitHub Actions が毎日 7:30(JST) に自動実行(PCを起動しておく必要なし)

対象サイトは「いこーよ」「Walkerplus」のような大手ポータルではなく、
公開されている地域ニュースサイト(号外NET各エリア版)や八潮市公式ポータルに限定しています。
大手ポータルは利用規約でスクレイピングや転載を明確に禁止しているため対象外にしています。

## セットアップ手順

### 1. LINE Messaging APIチャネルを作成する(通知の受け取り口)

LINE Notifyは2025年3月末で終了しているため、LINE公式アカウント(Messaging API)を使います。

1. [LINE Developers Console](https://developers.line.biz/console/) にLINEアカウントでログイン
2. 「プロバイダー」を新規作成(名前は任意、例: `個人用`)
3. 「新規チャネル作成」→「Messaging API」を選択し、チャネルを作成
   - チャネル名: 例「子供イベント通知Bot」
   - 業種などは個人利用で適当なものを選択
4. 作成したチャネルの「Messaging API設定」タブを開く
   - 一番下の「チャネルアクセストークン(長期)」を発行し、値をコピーして控えておく
   - 「応答メッセージ」は「オフ」に、「Webhookの利用」もオフのままでOK(送るだけなので不要)
5. 同じ画面のQRコードを自分のLINEアプリで読み取り、このBotを友だち追加する
   - ブロードキャスト配信は「友だち全員」に届く仕組みなので、自分だけが友だち追加していれば実質専用通知になります

### 2. GitHubリポジトリを作成してこのフォルダをpushする

```bash
cd "yashio-kids-event-notifier"
git init
git add .
git commit -m "init: 子供向けイベント通知アプリ"
```

GitHub上で新規リポジトリを作成し、表示される手順に従って `git remote add origin ...` → `git push -u origin main` を実行してください。
カレンダーページをGitHub Pages(無料)で公開するには、リポジトリを **Public** にする必要があります(中身はスクレイピングした公開イベント情報のみで個人情報は含みません)。

### 3. GitHub Secretsにトークンを登録する

リポジトリの `Settings → Secrets and variables → Actions → New repository secret` から

- Name: `LINE_CHANNEL_ACCESS_TOKEN`
- Value: 手順1で控えたチャネルアクセストークン

を登録します。

### 4. GitHub Pagesを有効にする(カレンダーページ)

`Settings → Pages` を開き、

- Source: `Deploy from a branch`
- Branch: `main` / フォルダ `/docs`

を選んで保存します。数分後に `https://<ユーザー名>.github.io/<リポジトリ名>/` でカレンダーページが見られるようになります。
(このリポジトリの場合は `https://dragonryo77-risha.github.io/yashio-kids-event-notifier/`)

### 5. 動作確認

`Actions` タブ → `Notify kids events` → `Run workflow` で手動実行できます。
成功すればログに取得件数などが出て、新着があればLINEに通知が届きます。
その後は毎日7:30(JST)に自動実行されます(時刻を変えたい場合は `.github/workflows/notify.yml` の `cron` を編集してください。UTC表記なので JST-9時間 で指定します)。

## カスタマイズ

- **対象エリアを増やす**: `src/sources.py` に追記(号外NET系は `https://<エリア>.goguynet.jp/category/cat_event/` の形式が多くのエリアで使えます)
- **キーワードを調整する**: `src/filters.py` の `KID_KEYWORDS` / `FAMILY_FRIENDLY_EVENT_KEYWORDS` / `NG_KEYWORDS` を編集
- **通知時刻**: `.github/workflows/notify.yml` の `cron`

## 注意点

- 対象サイトのHTML構造が変わるとスクレイピングが失敗することがあります(その場合はActionsのログにWARNとして出力され、他のサイトの処理は継続されます)。動かなくなったら `src/scraper.py` の該当パーサーを更新してください。
- あくまで個人・私的利用を想定しています。取得したデータの再配布や商用利用はしないでください。
- イベントの正確な開催日時は各記事の本文に書かれていることが多いため、通知に含まれるリンク先で必ず確認してください(通知に出る日付は記事の掲載日であり、開催日そのものではない場合があります)。
