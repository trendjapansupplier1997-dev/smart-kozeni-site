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
- 新規ページ追加時は、`sitemap.xml` と内部リンクの両方を更新します。
- 旧ページ実体を残さず、必要な旧URLは `_redirects` に集約します。
- バックアップファイルや作業ログは公開用ZIPに含めません。
