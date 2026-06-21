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

承認済みASP案件は`data/monetization/programs.json`で管理し、
ページJSONは`cta.program_id`だけを参照します。
ASP URL・PR注記・計測ピクセルをページJSONへ複製しません。

## CSSキャッシュ

Cloudflare Pagesでは`/assets/*`が1年間`immutable`です。

CSSを変更するときは既存ファイルを上書きせず、ファイル名の版を上げます。

```text
kozeni-sim-detail.v2.css
kozeni-sim-detail.v3.css
```

テンプレート側の参照も同時に更新します。

## 比較ハブ

`/mobile-sim/index.html`も直接編集しません。

- ページ内容は`data/mobile-sim-hub.json`で管理する
- 3候補の料金・データ量・通話は各`data/mobile-sim/<slug>.json`の`hub`から取得する
- HTML構造は`templates/mobile-sim-hub.html`で管理する
- CSSは`assets/kozeni-mobile-sim-hub.v1.css`で管理する

生成：

```bash
python3 tools/build_mobile_sim_hub.py
```

生成差分の確認：

```bash
python3 tools/build_mobile_sim_hub.py --check
```

比較ハブにアフィリエイトURLを直接置かない。
詳細ページへの内部リンクだけを置き、公式条件・PR表記・計測は詳細ページで管理する。

## 確認・トラブルページ

料金詳細とは別に、申込前チェックや反映待ちの確認ページを生成します。

```text
data/mobile-sim-guides/*.json
templates/mobile-sim-guide.html
assets/kozeni-mobile-guide.v1.css
tools/build_mobile_sim_guides.py
```

親サービスがあるガイドは`parent_slug`で詳細JSONを参照します。
CTA・PR注記・ASP URL・計測ピクセルをガイドJSONへ複製しません。

```bash
python3 tools/build_mobile_sim_guides.py
python3 tools/build_mobile_sim_guides.py --check
```

## ホーム回線ページ

スマホ料金や確認ガイドとは分けて、家のネットを生成します。

```text
data/home-network/*.json
templates/home-network-detail.html
assets/kozeni-home-network.v1.css
tools/build_home_network.py
```

生成：

```bash
python3 tools/build_home_network.py
python3 tools/build_home_network.py --check
```

`/mobile-sim/no-construction-wifi/`は重複ページを置かず、
`_redirects`から`/mobile-sim/home-wifi/`へ恒久転送します。
