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


## 保守・運用ドキュメント
- `docs/design-system.md` ブランド/配色/フォント/デザイン基調
- `docs/revenue-page-template.md` 収益ページ雛形/導線設計
- `docs/page-authoring-rules.md` 新規ページ作成ルール
- `docs/release-checklist.md` リリース前チェックリスト
- `docs/mobile-sim-generation.md` スマホ回線詳細ページのSSOT/生成/監査ルール
- `docs/monetization.md` 承認済みASP案件と収益導線のSSOTルール
- `docs/account-opening-generation.md` 口座開設ページのSSOT/生成/監査ルール
- `tools/kozeni_site_audit.py` サイト衛生チェック用スクリプト

監査コマンド：

```bash
python3 tools/kozeni_site_audit.py
```

スマホ回線詳細ページの生成確認：

```bash
python3 tools/build_mobile_sim.py --check
```

スマホ回線比較ハブの生成確認：

```bash
python3 tools/build_mobile_sim_hub.py --check
```

スマホ回線の確認・トラブルページ生成確認：

```bash
python3 tools/build_mobile_sim_guides.py --check
```

ホーム回線ページの生成確認：

```bash
python3 tools/build_home_network.py --check
```

クレジットカードページの生成確認：

```bash
python3 tools/build_credit_cards.py --check
```

口座開設ページの生成確認：

```bash
python3 tools/build_account_opening.py --check
```

デザイン監査コマンド：

```bash
python3 tools/kozeni_design_audit.py
```
