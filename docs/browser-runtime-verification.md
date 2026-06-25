# ブラウザ実行時検証

## 目的

静的なHTML・CSS・JavaScript構文監査だけでは、実際のブラウザで発生する例外、資産404、レスポンシブ横はみ出し、メニュー操作の破損までは検出できない。

Phase 19ではPlaywright Chromiumを使い、公開される全67ページをデスクトップとモバイルの2環境で実行する。
ピクセル単位のスクリーンショット一致は壊れやすいため採用せず、利用者に影響する実行時契約だけを検証する。

## 検証入口

依存関係とChromiumを一度準備する。

```bash
npm ci
npx playwright install chromium
```

実行する。

```bash
npm run verify:browser
```

LinuxでOS依存パッケージも含めて準備する場合：

```bash
npx playwright install --with-deps chromium
```

## 対象ページ

`tests/browser/site-runtime.spec.mjs`は`sitemap.xml`から66件のindexable URLを読み、`/404.html`を加える。
ページ一覧をテストコードへ重複管理しない。

各ページを次の2プロジェクトで確認する。1プロジェクト内で67ページを順次検査し、失敗はURL付きで集約する。

- desktop-chromium: 1440×900
- mobile-chromium: Pixel 7相当

## ページ共通契約

各ページで次を検査する。

- 生成HTMLと参照ローカル資産が存在する
- `main#main`が1件で表示される
- `h1`が1件で表示される
- canonicalが公開URLと一致する
- 404だけが`noindex,follow`
- JavaScript例外がない
- console errorがない
- ローカルCSS・操作JS・ローカル画像を実際に展開でき、参照画像・Manifestが存在する
- 重複IDがない
- 空href・`javascript:`リンクがない
- HTMLとbodyに横スクロールがない

## 外部通信の隔離

ブラウザ検証は生成HTMLへローカルCSS・操作JavaScript・ローカル画像をメモリ上で展開し、公開ファイル以外を要求しない。参照されたローカル資産が存在することも展開前に検査する。
GA4とClarityは別テストで外部script追加をDOM上だけで捕捉し、ASP、紹介、計測画像、SNSを含む外部originへは一切要求しない。

これにより次を防ぐ。

- 人工的な広告クリック・インプレッション
- 解析データの汚染
- 外部サイト障害による通常CIの不安定化

収益リンクはクリックしない。URLと属性は既存の構造監査が担当する。

## 操作契約

ホームのサイドメニューについて次を実ブラウザで確認する。

- 初期状態は閉じている
- ボタン操作で開く
- `aria-expanded`、`aria-hidden`、`inert`、body classが同期する
- Escapeで閉じる
- 閉じた後にトグルボタンへフォーカスが戻る

## GitHub Actions

`.github/workflows/site-verification.yml`は先に`python3 tools/verify_site.py`を実行する。
静的検証が成功した場合だけbrowser jobが`npm ci`、Chromium準備、`npm run verify:browser`を実行する。

失敗時だけPlaywright report、trace、スクリーンショットをArtifactへ保存する。通常成功時には成果物を保存しない。

## 責任境界

- `python3 tools/verify_site.py`: generator、構文、SSOT、SEO、資産、リンク、デザイン、Git差分
- `npm run verify:browser`: 実ブラウザの読込、例外、レスポンシブ、操作
- `python3 tools/check_external_links.py --live`: 非収益の外部リンク死活確認

各検証の責任を混ぜず、失敗原因を追いやすくする。
