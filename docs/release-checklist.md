# スマホ小銭研究所 リリース前チェックリスト v45.0

## 1. 変更前

```bash
cd ~/smart-kozeni-site
git status --short --branch
```

作業前に、意図しない未コミット差分がないことを確認する。

## 2. 編集と生成

生成対象HTMLは直接編集せず、対応する`data/`・`templates/`・`tools/build_*.py`を変更する。

必要なgeneratorだけを実行するか、全生成ページを更新する。

```bash
python3 tools/verify_site.py --write
```

`--write`後は必ず差分を確認する。

```bash
git status --short
git diff --check
git diff --stat
```

## 3. 公開前の統合検証

検証入口は次の1コマンドだけとする。

```bash
python3 tools/verify_site.py
```

個別generator、サイト監査、デザイン監査をリリース手順へ重複記載しない。`verify_site.py`が自動発見して実行する。

## 4. 新規ページを追加したとき

- URLがカテゴリ配下として自然か
- title / description / canonical があるか
- `sitemap.xml`へ追加したか
- 一覧ページから内部リンクしたか
- PR/紹介/広告リンク表記があるか
- 公式条件の確認を促しているか
- 「準備中」「一部公開」など未完成表示を出していないか
- 生成対象ならHTMLを直接編集していないか

## 5. CSS・デザイントークンを変更したとき

- `kozeni-tokens.v1.css`をブランドCSSより前に1回だけ読み込んでいるか
- 共通色・RGB・フォント・角丸をカテゴリCSSへ生値で再追加していないか
- ページ固有値を無理に共通トークンへ昇格させていないか
- トークン値を変更した場合、代表ページをデスクトップ・スマホで確認したか
- immutableキャッシュ対象のファイル名を更新すべき変更ではないか

## 6. 旧URL・資産を整理したとき

- 旧ページ実体を残していないか
- `_redirects`に転送先を1回だけ定義したか
- `sitemap.xml`に旧URLを残していないか
- 旧`v36`、旧home/menu資産を復活させていないか
- インラインCSS・インライン実行JavaScriptを追加していないか

## 7. コミット前

```bash
git add -A
git diff --cached --check
git diff --cached --stat
git diff --cached --name-status
python3 tools/verify_site.py
```

問題がなければコミット・pushする。

```bash
git commit -m "<変更内容>"
git push origin main
```

## 8. push後

GitHub Actionsの`Site verification`が成功したことを確認する。
ローカルとCIは同じ`python3 tools/verify_site.py`を実行するため、別の検証手順を増やさない。
