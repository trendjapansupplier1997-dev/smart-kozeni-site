# SEOメタデータ・構造化データ・sitemap

## 責任分離

ページ固有の`title`、`description`、`checked_at`は、各ページのcanonical JSONが所有する。
全ページを別の巨大なメタデータ一覧へ複製しない。

共通契約は`tools/seo.py`が所有する。

- canonical URLの導出
- 共通SEO head
- Open Graph / Twitter Card
- WebSite / Organization / WebPage / BreadcrumbListの基本JSON-LD
- 67生成ページのカタログ
- `sitemap.xml`生成
- title / description / canonicalの一意性
- noindexとsitemapの排他
- 内部リンク切れ・孤立ページ
- JSON-LDと表示メタデータの一致

## テンプレート

各テンプレートはSEOタグを個別に並べず、ページ種別に応じたマーカーを1つ置く。

```text
$seo_head_article
$seo_head_website
$seo_head_dynamic
```

`$seo_head_dynamic`はgeneratorが`og_type`を渡す場合だけ使用する。
`public_assets.load_template()`が共通headを展開する。

## sitemap

`sitemap.xml`は手編集しない。
canonical JSONからページカタログを構築し、次で生成する。

```bash
python3 tools/build_seo.py
```

一致確認：

```bash
python3 tools/build_seo.py --check
```

`noindex,follow`の404ページは自動的に除外する。
`changefreq`と`priority`は推測値を持たず、`loc`とcanonical JSON由来の`lastmod`だけを出力する。

## 日付

`checked_at`は、ページ内の確認日、JSON-LDの`dateModified`、sitemapの`lastmod`に使用する。
実際に内容を確認・更新した日だけ変更する。
公開日を確定できる一次情報がないため、`datePublished`は推測して追加しない。

## OGP画像

有効な共通OGP画像がない間は`twitter:card=summary`を使用し、存在しない画像URLを出力しない。
画像を導入する場合は、公開資産SSOTと全ページ監査へ同時に追加する。

## 統合検証

```bash
python3 tools/verify_site.py
```

新規ページ追加時はcanonical JSONとgenerator出力を追加する。
SEOページカタログに認識されない生成HTML、孤立ページ、sitemapの手編集は統合監査で失敗する。
