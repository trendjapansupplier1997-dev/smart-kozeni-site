# 公開資産・サイト実行基盤のSSOT

## 目的

favicon、Web App Manifest、解析スクリプト、基盤メニュー、Service Worker廃止処理を、用途不明の公開ファイルとして放置しない。公開中の資産、互換維持だけのエンドポイント、削除済み資産を明確に分ける。

## SSOT

共通実行設定は`data/site-runtime.json`で管理する。

- サイト名、短縮名、説明
- Web App Manifestの色・表示方式・アイコン
- HTML headで使うfaviconとApple Touch Icon
- Google Analytics 4 Measurement ID
- Microsoft Clarity Project ID

`tools/build_site_runtime.py`が次を生成する。

- `site.webmanifest`
- `assets/kozeni-analytics.v1.js`

HTMLへ共通挿入するhead断片は`tools/public_assets.py`が同じ設定から生成する。各テンプレートは`$site_runtime_head`を1回だけ持ち、各generatorは`public_assets.load_template(...)`を通して展開する。

## JavaScriptの責任分離

- `assets/kozeni-analytics.v1.js`: 全生成ページのGA4・Clarity読込だけを担当
- `assets/kozeni-foundation-menu.v1.js`: ホームの開閉メニューだけを担当

解析とUI操作を同じファイルへ混在させない。重要な本文、条件、CTAはJavaScriptなしでも利用できる静的HTMLとして生成する。

プライバシーポリシーには、全ページでGA4とClarityを利用することを明記する。

## Web App Manifest

`site.webmanifest`は全生成ページから参照する。Service Workerやオフラインキャッシュの稼働を意味するものではなく、ホーム画面追加時の名前・色・アイコンを提供する公開メタデータとして扱う。

重複していた`manifest.webmanifest`は使用しない。

## Service Workerの廃止エンドポイント

現在はオフラインキャッシュを運用しない。ただし、過去に`/sw.js`を登録したブラウザを安全に解除するため、`sw.js`は互換用の廃止エンドポイントとして残す。

このファイルは次だけを行う。

1. 即時activate
2. 旧Cache Storageを削除
3. 自身の登録を解除
4. 開いている同一オリジン画面を再読み込み

`fetch`イベントを持たず、通常通信を横取りしない。`_headers`ではキャッシュ禁止とし、古い廃止処理を保持させない。

## 公開資産の分類

### HTML・Manifestから参照される資産

`assets/`配下のCSS、JavaScript、画像、SVGは、生成HTML、CSS、またはManifestから参照されるものだけを置く。未参照資産があると統合監査は失敗する。

### URLから直接利用される互換・標準エンドポイント

次はHTMLから参照されなくても、標準URLまたはクローラー向け公開物として維持する。

- `favicon.ico`
- `robots.txt`
- `sitemap.xml`
- `humans.txt`
- `llms.txt`
- `site.webmanifest`
- `sw.js`

### 削除済み資産

次は再追加しない。

- `manifest.webmanifest`
- `version.json`
- `assets/kozeni-site-foundation.v1.js`
- 未参照の旧ブランドSVG
- 未参照の旧SNS SVG
- 制作元画像`assets/images/x-icon-source.png`
- 文字化けしていた未使用OGP画像

手動の`version.json`はGit commitとデプロイ履歴に役割が重複し、更新漏れを起こすため使用しない。

## 生成と検証

個別生成：

```bash
python3 tools/build_site_runtime.py
```

確認のみ：

```bash
python3 tools/build_site_runtime.py --check
```

サイト全体：

```bash
python3 tools/verify_site.py
```

統合監査は次を検査する。

- 全生成ページが共通headを1回だけ持つ
- 全生成ページが解析スクリプトを1回だけ読む
- メニュースクリプトがホームだけに存在する
- Manifestと解析JSがSSOTからの生成結果と一致する
- iconの実寸と`sizes`が一致する
- `assets/`に未参照ファイルがない
- 廃止資産が復活していない
- `sw.js`が通信を横取りせず、自身を解除する
- ManifestとService Worker廃止エンドポイントのキャッシュ方針が正しい
