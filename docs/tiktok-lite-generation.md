# TikTok Liteページ生成

`/tiktok-lite/`配下のページは、JSON・テンプレート・共通CSSから生成します。

## SSOT

```text
data/tiktok-lite-hub.json
data/tiktok-lite/pages/*.json
data/monetization/programs.json
```

紹介URLと招待コードは`data/monetization/programs.json`の
`tiktok-lite-direct-referral`だけで管理します。

## 表示構造

```text
templates/tiktok-lite-hub.html
templates/tiktok-lite-guide.html
assets/kozeni-tiktok-lite.v1.css
```

ハブと確認ページは実行JavaScriptを持ちません。
登録前条件、対象外、リンク不具合、報酬反映は常にHTMLへ表示します。

## 生成

```bash
python3 tools/build_tiktok_lite.py
```

生成差分の確認：

```bash
python3 tools/build_tiktok_lite.py --check
```

## 監査

```bash
python3 tools/kozeni_site_audit.py
python3 tools/kozeni_design_audit.py
git diff --check
```

統合監査では以下を確認します。

- 8ページが生成結果と一致する
- title、description、canonical、JSON-LDがある
- 共通CSSを参照する
- インラインCSSと実行JavaScriptがない
- 紹介URLがCTAのあるページに1回だけ出る
- `nofollow sponsored noopener noreferrer`とPR注記がある
- 招待コードが`invite-code`ページにだけ出る
- 関連リンクとsitemapが有効である

## 更新方針

報酬額、キャンペーン期限、必要タスクは変動します。
固定値をページへ書き足すのではなく、登録時の公式画面を確認する案内を維持します。
