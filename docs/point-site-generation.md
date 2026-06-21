# ポイ活ページ生成

`/point-site/`配下の19ページは、HTMLを直接編集せずデータ・テンプレート・共通CSSから生成します。

## SSOT

```text
data/point-site/sites/*.json
data/point-site/guides/*.json
data/point-site-hub.json
```

8サービスは1つのJSONから登録前ページと登録後ページを生成します。紹介URLはJSONへ直接書かず、`cta.program_id`で`data/monetization/programs.json`を参照します。

## 表示構造

```text
templates/point-site-detail.html
templates/point-site-earn.html
templates/point-site-guide.html
templates/point-site-hub.html
assets/kozeni-point-site.v1.css
```

登録前ページはJavaScript診断を使いません。3項目を常時表示し、条件確認後に紹介リンクへ進む静的構造です。

登録後ページの金額・案件は固定的なおすすめではなく、取得時点を明示した掲載例として扱います。現在の条件は各サービス内で確認します。

## 生成

```bash
python3 tools/build_point_sites.py
python3 tools/build_point_sites.py --check
python3 tools/kozeni_site_audit.py
```

## 禁止事項

- 生成HTMLの直接編集
- サービスJSONへの紹介URL直書き
- インラインCSS
- 実行JavaScriptによる診断・条件分岐
- 取得時点を示さない金額ランキング
- 一覧ページから紹介URLへの直接遷移
