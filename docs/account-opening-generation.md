# 口座開設ページ生成

口座開設領域は、内容・広告・HTML構造を分離して管理します。
生成後の`account-opening/**/*.html`は成果物であり、直接編集しません。

## SSOT

```text
data/account-opening/products/*.json
data/account-opening/guides/*.json
data/account-opening-hub.json
data/monetization/programs.json
```

- 商品ページは申込前チェック、公式情報、CTAを持つ
- 解説ページは制度や口座の違いを説明し、収益CTAを持たない
- ハブは目的別の候補と解説ページへの入口を持つ
- 承認済み広告は`program_id`で参照する

## テンプレートとCSS

```text
templates/account-opening-product.html
templates/account-opening-guide.html
templates/account-opening-hub.html
assets/kozeni-account-opening.v1.css
```

ページ内`<style>`と実行JavaScriptは使用しません。
ハブの絞り込みUIは廃止し、すべての候補を静的HTMLで表示します。

## 生成

全ページを生成します。

```bash
python3 tools/build_account_opening.py
```

1ページだけ生成する場合はslugを指定します。

```bash
python3 tools/build_account_opening.py matsui-sec
```

生成結果がSSOTと一致するか確認します。

```bash
python3 tools/build_account_opening.py --check
```

## 監査

```bash
python3 tools/kozeni_site_audit.py
python3 tools/kozeni_design_audit.py
git diff --check
```

統合監査は次を確認します。

- データと生成HTMLの完全一致
- title、description、canonical、sitemap
- H1が1個
- 共通CSSの使用
- インラインCSSと実行JavaScriptの禁止
- CTAのURL、PR注記、rel属性、計測画像
- 広告URLのレジストリ外重複禁止
- 内部リンク切れ
- 旧手書きUIトークンの残存禁止
