# 変動訴求ライフサイクル

料金、値引き額、還元額、適用期間、終了日のように外部都合で変わる訴求は、
`data/claims.json` を唯一の定義元にします。一般的な解説文まで移すためのCMSではありません。

## 構造

各claimは次を持ちます。

- `status`: `active`、`paused`、`retired`
- `checked_at`: 公式情報を確認した日
- `review_after_days`: 再確認までの最大日数
- `expires_at`: 明示された終了日。期限なしは `null`
- `source_url`: 根拠となる公式HTTPS URL
- `texts`: 公開ページへ展開する文章断片
- `retired_texts`: 対象ページから排除すべき旧表現

生成元JSONでは次の形式で参照します。

```text
{{claim:biglobe-wimax-monthly-discount.statement}}
```

ビルダーは `tools/claims.py` の `resolve_data()` で参照を解決します。公開HTMLには
トークンではなく通常の文章だけが出力されます。

## 検証

通常の統合検証:

```bash
python3 tools/verify_site.py
```

期限切れだけでなく、再確認期限超過も失敗させる定期検証:

```bash
python3 tools/claims.py --strict-stale
```

検証は次を強制します。

- active claimの未使用、inactive claimの参照、未使用variantを禁止
- claim本文の生成元JSONへの直接複製を禁止
- 根拠URLが参照ページの`sources`に存在すること
- ページの`checked_at`がclaimの確認日以上であること
- 終了済みclaimと旧表現の残存を禁止
- 通常CIでは再確認期限超過を警告し、定期CIでは失敗

## 更新手順

1. 公式ページで条件を確認する
2. `data/claims.json` の文章、`checked_at`、必要なら `expires_at` を更新する
3. 参照ページの `checked_at` を同日以降へ更新する
4. ジェネレーターを実行する
5. 統合検証とブラウザ検証を実行する

claimを削除する前に参照をなくします。終了した訴求を別文言へ暗黙に
フォールバックさせず、`paused` または `retired` にして参照を明示的に外します。
