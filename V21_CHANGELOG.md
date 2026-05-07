# v21 Cache reset / Service Worker retirement

- Service Worker registrationを一時停止。
- 既存Service WorkerとCache Storageをページ読み込み時に削除。
- sw.jsを自己登録解除・キャッシュ削除用に変更。
- CSS/JS読み込みに ?v=21 を付与して古いボタンCSSの残留を回避。
- _headersでHTML・sw.js・manifestのキャッシュを弱め、更新確認を優先。

頻繁にデザイン更新している間は、PWAより最新版表示を優先する。
