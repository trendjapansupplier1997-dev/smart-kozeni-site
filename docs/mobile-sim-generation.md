# スマホ回線詳細ページの生成ルール

`/mobile-sim/<slug>/index.html` のうち、共通基盤へ移行済みのページは
直接編集しません。

## SSOT

編集対象は次のJSONです。

```text
data/mobile-sim/<slug>.json
```

HTML構造は次のテンプレートで管理します。

```text
templates/mobile-sim-detail.html
```

共通スタイルは次のCSSで管理します。

```text
assets/kozeni-sim-detail.v2.css
```

## 生成

全ページを生成します。

```bash
python3 tools/build_mobile_sim.py
```

特定ページだけ生成します。

```bash
python3 tools/build_mobile_sim.py ahamo
```

生成済みHTMLがJSONとテンプレートに一致するか確認します。

```bash
python3 tools/build_mobile_sim.py --check
```

サイト全体の監査では生成差分も検査されます。

```bash
python3 tools/kozeni_site_audit.py
```

## 更新手順

1. 公式サイトで料金・通話・対象外条件を確認する
2. `checked_at`を更新する
3. JSONだけを編集する
4. HTMLを生成する
5. `--check`とサイト監査を実行する
6. `git diff`でJSONと生成HTMLを確認する
7. ローカルHTTPサーバーでPC・スマホ幅を確認する
8. commit・pushする

## CTA

CTAは1ページ1種類・1か所を原則とします。

アフィリエイトリンクでは以下を必須とします。

```text
rel="nofollow sponsored noopener noreferrer"
```

文言は次に統一します。

```text
公式条件を見る
```

PR文言は次に統一します。

```text
PR：このリンクは広告リンクです。条件・特典は公式画面で確認してください。
```

ASPが指定する計測ピクセルは`cta.tracking_pixel_url`で管理します。

## CSSキャッシュ

Cloudflare Pagesでは`/assets/*`が1年間`immutable`です。

CSSを変更するときは既存ファイルを上書きせず、ファイル名の版を上げます。

```text
kozeni-sim-detail.v2.css
kozeni-sim-detail.v3.css
```

テンプレート側の参照も同時に更新します。
