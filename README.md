# スマホ小銭研究所

Cloudflare Pages 用のクリーンな静的サイト一式です。

## 主要ページ
- `/` ホーム
- `/mobile-sim/` スマホ・回線
- `/point-site/` ポイ活アプリ一覧
- `/tiktok-lite/` TikTok Lite
- `/credit-card/` クレカ
- `/account-opening/` 口座開設メモ
- `/about/` 運営者情報
- `/policy/` PR表記
- `/privacy/` プライバシーポリシー
- `/contact/` お問い合わせ

## 主要な旧URLリダイレクト
- `/mobile/` 系は `/mobile-sim/` 系へリダイレクトします。
- `/point-site/trip-mile/` 系は `/point-site/trima/` 系へリダイレクトします。
- `/start-here/` と `/point-site/referral-code/` は現行ページへリダイレクトします。

## 運用メモ
- 新規ページ追加時はcanonical JSONと内部リンクを更新します。`sitemap.xml`は`tools/build_seo.py`が生成するため手編集しません。
- 旧ページ実体を残さず、必要な旧URLは `_redirects` に集約します。
- バックアップファイルや作業ログは公開用ZIPに含めません。


## 保守・運用ドキュメント
- `docs/design-system.md` ブランド/配色/タイポグラフィの視覚方針
- `docs/design-tokens.md` 色・フォント・角丸・影・余白のSSOT運用
- `docs/revenue-page-template.md` 収益ページ雛形/導線設計
- `docs/page-authoring-rules.md` 新規ページ作成ルール
- `docs/release-checklist.md` リリース前チェックリスト
- `docs/site-verification.md` ローカル/CI共通の検証SSOT
- `docs/external-link-verification.md` 外部リンク・収益リンクの構造監査と安全な定期確認
- `docs/public-assets-runtime.md` favicon・Manifest・解析・Service Worker廃止処理のSSOT
- `docs/seo-metadata.md` SEO head・構造化データ・sitemap・内部リンクのSSOT
- `docs/browser-runtime-verification.md` 全公開ページの実ブラウザ・レスポンシブ・操作検証
- `docs/mobile-sim-generation.md` スマホ回線詳細ページのSSOT/生成/監査ルール
- `docs/monetization.md` 承認済みASP案件と収益導線のSSOTルール
- `docs/account-opening-generation.md` 口座開設ページのSSOT/生成/監査ルール
- `docs/point-site-generation.md` ポイ活ページのSSOT/生成/監査ルール
- `docs/tiktok-lite-generation.md` TikTok LiteページのSSOT/生成/監査ルール
- `docs/lifestyle-generation.md` 買い物・旅行ページのSSOT/生成/収益導線ルール
- `docs/site-foundation-generation.md` ホーム・404・サイト情報ページのSSOT/旧v36撤去ルール

## 統合検証

ローカルとGitHub Actionsは同じ1コマンドを使用します。

```bash
python3 tools/verify_site.py
```

このコマンドは、すべてのgenerator、JSON/JavaScript構文、公開資産、解析スクリプト、収益導線、外部リンク属性、内部リンク、SEOメタデータ、構造化データ、canonical、生成sitemap、デザイン、Git差分をまとめて検証します。

すべての生成ページを書き直してから検証する場合：

```bash
python3 tools/verify_site.py --write
```

`--write`後は`git status --short`と`git diff --stat`で生成差分を確認してください。

## ブラウザ実行時検証

公開67ページをデスクトップとモバイルのChromiumで確認します。

```bash
npm ci
npx playwright install chromium
npm run verify:browser
```

外部通信はテスト内で隔離し、ASP・紹介・解析URLへアクセスしません。GitHub Actionsでは静的統合検証の成功後に同じ`npm run verify:browser`を実行します。

## 外部リンクの定期確認

公式リンクとSNSだけをネットワーク確認します。

```bash
python3 tools/check_external_links.py --live
```

ASPリンク、紹介リンク、計測ピクセル、広告画像は人工的なクリックやインプレッションを避けるため自動アクセスしません。詳細は`docs/external-link-verification.md`を参照してください。
