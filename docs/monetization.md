# 収益導線SSOT

承認済みASP案件のURL・PR注記・計測ピクセル・バナー素材は、
`data/monetization/programs.json`だけで管理します。

## 原則

- 各ページJSONへASP URLを複製しない
- 承認済み案件だけ`status: approved`で登録する
- 表示ページ側は`cta.program_id`だけを持つ
- `nofollow sponsored noopener noreferrer`を必須とする
- PR注記を必ず表示する
- ASP指定の計測ピクセルはレジストリで管理する
- 提供された広告コードの識別子・画像URL・サイズを改変しない
- 一覧ページからASPへ直接送らず、個別の条件確認ページを経由する

## 構造

```text
data/monetization/programs.json
        ↓
tools/monetization.py
        ↓
各カテゴリの生成器
```

ページJSONの例：

```json
{
  "cta": {
    "program_id": "tokyu-card-afb"
  }
}
```

公式リンクで収益化しない場合だけ、ページJSONへ通常CTAを記述します。

```json
{
  "cta": {
    "url": "https://example.com/",
    "label": "公式条件を見る",
    "affiliate": false,
    "note": "このリンクは公式ページへの案内です。"
  }
}
```

## 東急カード

承認済みCSVに含まれる以下の識別子をSSOTへ保存します。

```text
ASP: afb
campaign_id: C980560u
media_id: H13605n
creative_id: 450756
size: 320x100
```

生の広告HTMLを各ページへ貼りません。
`tools/monetization.py`が安全な属性・PR注記・計測画像を共通生成します。

## 監査

```bash
python3 tools/kozeni_site_audit.py
```

統合監査では以下を確認します。

- 未承認案件がない
- ASP URLがページJSONへ重複していない
- `program_id`が存在する
- CTAの`rel`属性
- PR注記
- 計測ピクセル
- バナー画像URL・サイズ・識別子
