# スマホ小銭研究所 ページ作成ルール v46.0

このドキュメントは、今後ページを増やしてもサイト構成を崩さないための運用ルールです。

## 基本方針

- 新規ページは「案件を増やす」より先に、読者が申し込み前に確認すべき条件を整理する。
- PR/アフィリエイト/紹介リンクは、設置ページ内で明記する。
- 「準備中」「一部公開」「工事中」など、未完成に見える表現を表側に出さない。
- 掲載できない案件は無理に出さず、「掲載方針」や「条件確認メモ」として成立させる。
- 旧URLの実体ページは残さず、必要な場合は `_redirects` に集約する。

## 検証SSOT

公開前確認は必ず次の1コマンドで行う。

```bash
python3 tools/verify_site.py
```

個別generatorや監査コマンドをリリース手順へ追加しない。新しい`tools/build_*.py`は自動的に検証対象となる。詳細は`docs/site-verification.md`を参照する。

## URLとカテゴリ

主要カテゴリは以下を基本とする。

- `/mobile-sim/` スマホ・回線
- `/point-site/` ポイ活
- `/credit-card/` クレカ
- `/account-opening/` 口座開設
- `/tiktok-lite/` TikTok Lite

新規ページを作る場合は、カテゴリ配下に小文字英数字とハイフンでURLを作る。

例：

- `/credit-card/epos-card/`
- `/account-opening/sbi-securities/`
- `/mobile-sim/rakuten-mobile/`

## 新規ページの最低要件

新規HTMLページは、最低限以下を満たす。

- `<title>` がある
- `<meta name="description">` がある
- `<link rel="canonical">` がある
- PR/広告/紹介リンクの有無が分かる
- 公式条件の確認を促す文言がある
- `sitemap.xml` に追加されている
- 一覧ページまたは関連ページから内部リンクされている
- 404ではなく実ページとして表示確認できる

## 新規ページで避けること

- 新規ページで v36 系CSS/JSを増やさない
- インラインCSSを増やさない
- 「準備中」「一部公開」「強化中」「公開中」などの状態バッジを表側に出さない
- 比較できないのに「おすすめ」と断言しすぎない
- 条件未確認のまま高額特典だけを押し出さない
- 旧URLの実体ページを作り直さない

## CSS/JSの扱い

旧v36系CSS/JSは撤去済みであり、互換資産として再追加しない。

- すべてのページで`kozeni-tokens.v1.css`を最初に読み込み、その後にブランド・ナビ・カテゴリCSSを読み込む
- 共通色、フォント、角丸、影は`assets/kozeni-tokens.v1.css`だけで管理する
- カテゴリCSSはページ固有の構造と、共通トークンを参照する意味別の別名変数を持つ
- CSS統合はカテゴリ単位で進め、固有レイアウトを機械的に共通化しない
- 1ページだけの見た目調整をHTML内に増やさない
- インラインCSSとインライン実行JavaScriptは追加しない
- 詳細は`docs/design-tokens.md`を参照する

## 収益導線の考え方

- ポイ活：友達紹介報酬を中心にする
- クレカ：ASP/公式アフィリエイトを中心にする
- 口座開設：アクセストレード等のASP審査後に差し替える
- スマホ・回線：ASP/楽天アフィリエイト/公式提携を案件ごとに選ぶ

ただし、収益導線より先に「対象外条件」「達成条件」「付与時期」「失敗しやすい点」を見せる。

## ページ構成の基本型

個別案件ページは、以下の順番を基本にする。

1. ファーストビュー：何のページか、誰向けか
2. PR/紹介リンク表記
3. 向いている人 / 向いていない人
4. 申し込み前チェック
5. 条件確認：年会費・利用条件・対象外・付与時期
6. 公式/申込CTA
7. 関連ページへの内部リンク


## スマホ回線詳細ページのSSOT

共通基盤へ移行済みの`/mobile-sim/<slug>/index.html`は直接編集しない。

- 内容は`data/mobile-sim/<slug>.json`で管理する
- 構造は`templates/mobile-sim-detail.html`で管理する
- `python3 tools/build_mobile_sim.py`でHTMLを生成する
- `python3 tools/verify_site.py`で生成差分、CTA、PR、構造、内部リンクをまとめて監査する
- CSS更新時は`/assets/*`のimmutableキャッシュを考慮し、ファイル名の版を上げる

詳細は`docs/mobile-sim-generation.md`を参照する。


## スマホ回線比較ハブのSSOT

`/mobile-sim/index.html`は直接編集しない。

- ページ構成は`data/mobile-sim-hub.json`で管理する
- 主要3候補の比較情報は各詳細JSONの`hub`で管理する
- `python3 tools/build_mobile_sim_hub.py`で生成する
- 比較ハブにはASPリンクを直接置かず、詳細ページへ内部リンクする
- JavaScriptによる候補の出し分けを行わず、重要導線は常にHTMLへ表示する

## スマホ回線の確認・トラブルページ

- 料金のSSOTは`data/mobile-sim/*.json`
- 確認手順は`data/mobile-sim-guides/*.json`
- 親CTAは`parent_slug`から参照し、URLを複製しない
- 実行JavaScriptや診断UIを追加しない
- 金額より申込経路・期限・達成条件・進呈時期を優先する


## ホーム回線ページ

- スマホ料金JSONへ固定回線の料金を混ぜない
- 内容は`data/home-network/*.json`で管理する
- キャンペーン価格と通常料金、端末代、工事費を分離する
- 工事不要と光回線の向き不向きを明示する
- 重複URLはHTMLを残さず`_redirects`へ集約する


## 収益導線のSSOT

- 承認済みASP案件は`data/monetization/programs.json`へ登録する
- ページJSONは`cta.program_id`だけを参照する
- ASP URL・PR注記・計測ピクセルをページごとに複製しない
- 生の広告HTMLを直接貼らない
- 一覧ページからASPへ直接遷移させず、個別条件ページを経由する
- 収益リンクをリンク切れ確認ツールやブラウザ自動化から開かない
- 公式リンクの死活確認は`python3 tools/check_external_links.py --live`で行う
- 詳細は`docs/monetization.md`と`docs/external-link-verification.md`を参照する

## クレジットカードページ

`/credit-card/`と`/credit-card/<slug>/`は直接編集しない。

- 内容は`data/credit-card/*.json`と`data/credit-card-hub.json`で管理する
- 構造は`templates/credit-card-*.html`で管理する
- CSSは`assets/kozeni-credit-card.v1.css`へ共通化する
- `python3 tools/build_credit_cards.py`で生成する
- `python3 tools/verify_site.py`で生成差分を確認する
- 診断JavaScriptを追加せず、重要な条件は常にHTMLへ表示する

## 公開前チェック

公開前は `python3 tools/verify_site.py` を実行し、最低限の欠落を確認する。

## 口座開設ページ

`/account-opening/`と`/account-opening/<slug>/`は直接編集しない。

- 商品ページは`data/account-opening/products/*.json`で管理する
- 解説ページは`data/account-opening/guides/*.json`で管理する
- ハブは`data/account-opening-hub.json`で管理する
- 構造は`templates/account-opening-*.html`で管理する
- CSSは`assets/kozeni-account-opening.v1.css`へ共通化する
- `python3 tools/build_account_opening.py`で生成する
- `python3 tools/verify_site.py`で生成差分を確認する
- 広告リンクは`program_id`だけを記述し、生URLをページデータへ複製しない
- 解説ページへ収益CTAを自動挿入しない

詳細は`docs/account-opening-generation.md`を参照する。


## ポイ活ページ

`/point-site/`配下のハブ、8サービスの登録前・登録後ページ、初心者・比較ガイドは直接編集しない。

- サービス内容は`data/point-site/sites/*.json`で管理する
- ガイドは`data/point-site/guides/*.json`で管理する
- ハブは`data/point-site-hub.json`で管理する
- 構造は`templates/point-site-*.html`で管理する
- CSSは`assets/kozeni-point-site.v1.css`へ共通化する
- `python3 tools/build_point_sites.py`で生成する
- 紹介URLは`data/monetization/programs.json`だけで管理する
- 登録前条件は常時表示し、診断JavaScriptを追加しない
- 金額・案件例には取得時点を明示し、現在条件の確認を促す

詳細は`docs/point-site-generation.md`を参照する。

## TikTok Liteページ

`/tiktok-lite/`配下の8ページは直接編集しない。

- ハブは`data/tiktok-lite-hub.json`で管理する
- 確認ページは`data/tiktok-lite/pages/*.json`で管理する
- 構造は`templates/tiktok-lite-*.html`で管理する
- CSSは`assets/kozeni-tiktok-lite.v1.css`へ共通化する
- `python3 tools/build_tiktok_lite.py`で生成する
- `python3 tools/verify_site.py`で生成差分を確認する
- 紹介URLと招待コードは`data/monetization/programs.json`だけで管理する
- 診断JavaScriptを追加せず、確認事項は常にHTMLへ表示する
- 報酬額・期限・必要タスクは固定値として断定せず、公式画面の確認を促す

詳細は`docs/tiktok-lite-generation.md`を参照する。

## 買い物・旅行ページ

`/shopping/`と`/travel/`配下のハブ・確認ページは直接編集しない。

- ハブは`data/lifestyle/hubs/*.json`で管理する
- 確認ページは`data/lifestyle/guides/*.json`で管理する
- 構造は`templates/lifestyle-*.html`で管理する
- CSSは`assets/kozeni-lifestyle.v1.css`へ共通化する
- `python3 tools/build_lifestyle.py`で生成する
- `python3 tools/verify_site.py`で生成差分を確認する
- ASP URLは`data/monetization/programs.json`だけで管理し、ページJSONには`program_id`だけを書く
- クーポン、ポイント、予約、キャンセル条件は固定保証せず、公式画面の確認を促す

詳細は`docs/lifestyle-generation.md`を参照する。

## サイト基盤ページ

ホーム、404、運営者情報、問い合わせ、PR表記、プライバシーは直接編集しない。

- 内容は`data/site-foundation/`で管理する
- 構造は`templates/site-home.html`と`templates/site-info.html`で管理する
- CSS/JSは`assets/kozeni-site-foundation.v1.*`へ集約する
- `python3 tools/build_site_foundation.py`で生成する
- インラインCSS、インライン実行JavaScript、旧`v36`資産を追加しない
- ホームメニュー以外の重要情報をJavaScriptへ依存させない

詳細は`docs/site-foundation-generation.md`を参照する。
