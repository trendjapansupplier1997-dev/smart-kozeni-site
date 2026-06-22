# サイト基盤ページのSSOT生成

ホーム、404、運営者情報、問い合わせ、PR表記、プライバシーは、サイト全体の入口と信頼情報を担う基盤ページです。手書きHTMLや旧テーマ資産へ戻さず、データ・テンプレート・共通CSS/JSから生成します。

## 対象ページ

- `/`
- `/404.html`
- `/about/`
- `/contact/`
- `/policy/`
- `/privacy/`

## SSOT

- ホーム内容: `data/site-foundation/home.json`
- 基盤ページ内容: `data/site-foundation/pages/*.json`
- ホーム構造: `templates/site-home.html`
- 基盤ページ構造: `templates/site-info.html`
- 共通表示: `assets/kozeni-site-foundation.v1.css`
- ホームメニュー: `assets/kozeni-foundation-menu.v1.js`
- 全ページ共通解析: `assets/kozeni-analytics.v1.js`
- 公開実行設定: `data/site-runtime.json`
- 生成器: `tools/build_site_foundation.py`

HTMLは生成物です。内容はJSON、共通構造はテンプレート、表示は共通CSSで変更します。

## 生成と確認

```bash
python3 tools/build_site_foundation.py
python3 tools/verify_site.py
```

## JavaScriptの境界

- ホームの開閉メニューは`kozeni-foundation-menu.v1.js`だけが担当する
- Google Analytics 4とMicrosoft Clarityは`kozeni-analytics.v1.js`だけが担当し、全生成ページで同じファイルを1回だけ読む
- HTMLへフォールバックJavaScriptや解析IDを複製しない
- 重要な本文、導線、条件はJavaScriptなしでも読める静的HTMLにする

## 廃止済み資産

次の資産は再追加しません。

- `assets/style.v36.css`
- `assets/kozeni-nav.v36.3.css`
- `assets/script.v36.js`
- `assets/kozeni-nav.v36.3.js`
- `assets/kozeni-home.v1.css`
- `assets/kozeni-menu.v1.css`
- `assets/kozeni-menu.v1.js`

統合監査は、これらのファイル・参照・旧クラスが復活した場合に失敗します。公開資産と解析の詳細は`docs/public-assets-runtime.md`を参照します。
