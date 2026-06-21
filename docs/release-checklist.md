# スマホ小銭研究所 リリース前チェックリスト v42.2

## 1. 変更前

```bash
cd ~/smart-kozeni-site
git status --short
```

作業前に未コミット差分がないことを確認する。

## 2. 変更後の基本確認

```bash
git diff --stat
git diff --check
python3 tools/build_point_sites.py --check
python3 tools/kozeni_site_audit.py
```

## 3. 新規ページを追加したとき

- URLがカテゴリ配下として自然か
- title / description / canonical があるか
- sitemap.xml に追加したか
- 一覧ページから内部リンクしたか
- PR/紹介/広告リンク表記があるか
- 公式条件の確認を促しているか
- 「準備中」「一部公開」など未完成表示を出していないか

## 4. 旧URLを整理したとき

- 旧ページ実体を残していないか
- `_redirects` に転送先を1回だけ定義したか
- sitemap.xml に旧URLを残していないか

## 5. コミット前

```bash
git status --short
git diff --stat
git diff --check
python3 tools/build_point_sites.py --check
python3 tools/kozeni_site_audit.py
```

問題なければコミットする。

```bash
git add -A
git commit -m "<変更内容>"
git push
```
