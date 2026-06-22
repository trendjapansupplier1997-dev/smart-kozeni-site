# 外部リンクと収益導線の検証

## 目的

外部URLには、性質が異なる2種類があります。

1. 公式情報、公式申込ページ、SNSなど、通常の外部リンク
2. ASP、紹介リンク、計測ピクセル、広告クリエイティブなどの収益リンク

通常の外部リンクは定期的にHTTP確認できますが、収益リンクを自動巡回すると、人工的な広告クリックやインプレッションを発生させる危険があります。そのため検証を次の2層に分けます。

## 構造検証

通常の公開前検証に含まれます。

```bash
python3 tools/verify_site.py
```

`tools/external_links.py`が、`data/monetization/programs.json`、全ページJSON、生成HTMLを横断して確認します。

- `program_id`が小文字英数字とハイフンだけである
- 参照先のプログラムが存在する
- `status: approved`のプログラムが少なくとも1ページから使われる
- `paused`または`retired`のプログラムがページから参照されない
- 同じ`click_url`を複数プログラムへ登録しない
- ASP URL、計測ピクセル、広告画像をレジストリ外へ複製しない
- 生の`affiliate: true`をページJSONへ書かない
- 生成HTMLに承認済みプログラムのリンクが存在する
- 収益リンクに`nofollow sponsored noopener noreferrer`がある
- 収益リンクに共通の`referrerpolicy`がある
- 計測ピクセルとバナー画像の出現数がCTA数と一致する
- 収益リンクではない外部リンクに`target="_blank"`と`noopener noreferrer`がある
- 未登録の外部画像や`rel="sponsored"`を許可しない

この検証はネットワークへ接続しません。

## ネットワーク確認

公式リンクとSNSの現在の応答だけを確認します。

```bash
python3 tools/check_external_links.py --live
```

対象は生成HTMLに現れる非収益の外部リンクです。重複URLは1回だけ確認します。

収益リンク、計測ピクセル、広告画像は、偽クリックや偽インプレッションを避けるため、`--live`でも絶対にリクエストしません。これらの有効性はASPや紹介サービスの管理画面で確認します。

判定は次のとおりです。

- `PASS`: HTTP 2xxまたは3xx
- `WARN`: 認証、Bot制限、レート制限、一時的な5xx、タイムアウト
- `FAIL`: 404、410、DNSエラー、TLSエラー、その他の確定的な4xx

警告も失敗扱いにしたい手動調査時だけ、次を使います。

```bash
python3 tools/check_external_links.py --live --strict-warnings
```

JSONレポートを残す場合：

```bash
python3 tools/check_external_links.py --live \
  --report /tmp/smart-kozeni-external-links.json
```

レポートは運用ログであり、サイト内容のSSOTではないためコミットしません。

## GitHub Actions

`.github/workflows/external-link-verification.yml`が毎週月曜日と手動実行でネットワーク確認を行います。

通常のpushとPull Requestではネットワーク確認を行いません。外部サイトの一時障害で通常CIを不安定にしないためです。

- `Site verification`: push、Pull Request、手動。生成物と構造を検証
- `External link verification`: 週次、手動。非収益リンクの応答を検証

どちらのワークフローも検証処理をYAMLへ複製せず、Pythonの単一コマンドへ委譲します。

## プログラム停止時

案件を一時停止する場合は、レジストリの`status`を`paused`へ変更し、すべてのページJSONから`program_id`参照を外します。

終了案件は`retired`へ変更できます。履歴としてレジストリに残せますが、生成ページから参照してはいけません。

```text
approved  公開ページから参照可能
paused    一時停止。公開ページから参照不可
retired   終了。公開ページから参照不可
```

停止状態のまま参照が残っている場合や、承認済みなのにどこからも使われていない場合は、通常の`verify_site.py`が失敗します。
