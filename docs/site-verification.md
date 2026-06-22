# サイト検証SSOT

## 目的

ローカル確認とGitHub Actionsで異なる検証手順を持たない。
検証入口は次の1コマンドだけとする。

```bash
python3 tools/verify_site.py
```

通常のGitHub Actionsも同じコマンドを実行する。ワークフローへ個別generatorや監査コマンドを追加しない。外部ネットワーク確認だけは週次の独立コマンドに分離する。

## 検証内容

`tools/verify_site.py`は次を順番に実行する。

1. `tools/build_*.py`を自動発見し、通常は`--check`、`--write`時は生成を最大4並列で実行
2. リポジトリ内のJSONとWeb Manifestを構文検査（公開実行設定も含む）
3. リポジトリ内のJavaScriptを`node --check`で構文検査
4. GitHub Actionsが統合検証コマンドだけを呼んでいることを検査
5. `tools/kozeni_site_audit.py`を実行し、67生成HTML、公開資産、解析、Manifest、Service Worker廃止処理、収益レジストリ、外部リンク契約、SEOメタデータ、構造化データ、生成sitemap、孤立ページを検査
6. `tools/kozeni_design_audit.py`を実行し、トークン読込順・共通値の生書き戻し・インラインコードを検査
7. staged／unstaged両方の`git diff --check`を実行
8. CIでは作業ツリーがクリーンなことを検査

新しい`tools/build_*.py`を追加した場合、一覧ファイルの更新は不要。命名規則により自動的に検証対象へ入る。`tools/build_seo.py`も同じ仕組みでcanonical JSONから`sitemap.xml`を検査する。

## 通常の確認

```bash
cd ~/smart-kozeni-site
python3 tools/verify_site.py
```

生成HTMLが古い場合は失敗する。該当するJSON・テンプレート・生成器を修正し、必要なgeneratorを実行してから再確認する。

## 全ページを再生成して確認

すべてのgeneratorを実行してから検証する場合：

```bash
python3 tools/verify_site.py --write
```

`--write`は生成HTMLを書き換えるため、実行後に必ず差分を確認する。

```bash
git status --short
git diff --check
git diff --stat
```

## GitHub Actions

`.github/workflows/site-verification.yml`はpush、Pull Request、手動実行で統合検証を起動する。
CIでは`CI=true`のため、検証後に未追跡・変更ファイルがあれば失敗する。

これにより、JSONやテンプレートを変更したのに生成HTMLをコミットし忘れた状態をmainへ入れない。

`.github/workflows/external-link-verification.yml`は週次と手動実行で`python3 tools/check_external_links.py --live`を呼ぶ。通常CIとは分離し、外部サイトの一時障害をpush検証へ持ち込まない。収益URLは偽クリック防止のためネットワーク確認対象外とする。

## 必要環境

- Python 3
- Node.js
- Git

外部Pythonパッケージやnpmパッケージには依存しない。
