# 買い物・旅行ページ生成ルール

## SSOT

```text
data/lifestyle/hubs/*.json
data/lifestyle/guides/*.json
        ↓
templates/lifestyle-hub.html
templates/lifestyle-guide.html
        ↓
tools/build_lifestyle.py
        ↓
shopping/**/index.html
travel/**/index.html
```

生成HTMLは直接編集しない。内容はJSON、構造はテンプレート、見た目は`assets/kozeni-lifestyle.v1.css`で管理する。

## 収益導線

ASP URLは`data/monetization/programs.json`だけで管理する。各ページJSONの`offers`は`program_id`と文脈別説明だけを持つ。

生の広告HTML、ASP URL、`rel`属性、PR注記を各ページへ手作業で複製しない。

## 内容方針

- クーポン・ポイント・送料・返品条件は変動する前提で書く
- 宿泊料金・キャンセル条件は施設・プラン・支払方法ごとに異なることを明示する
- 「必ず得」「必ず返金」などの断定をしない
- 最終条件は各公式画面で確認する
- 重要事項をJavaScriptで隠さず、静的HTMLへ常時表示する

## 生成と監査

```bash
python3 tools/build_lifestyle.py
python3 tools/verify_site.py
git diff --check
```
