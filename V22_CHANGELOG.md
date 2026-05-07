# v22 Hard cache bust / Production verification

- CSS/JSをクエリ文字列ではなくファイル名でバージョン化: `/assets/style.v22.css`, `/assets/script.v22.js`。
- 全HTMLのCSS/JS参照をv22ファイルへ更新。
- `_headers`を一時的に全体 no-store にして、Cloudflare/ブラウザ/中間キャッシュの残留を避ける。
- `sw.js`をさらに強め、Cache Storage削除・Service Worker解除・一度だけ `kozeni_sw_reset=v22` 付きで再読込。
- `/__version.html` と `/version.json` を追加し、独自ドメインが本当に最新版を返しているか確認可能にした。

頻繁なデザイン更新が落ち着いたら、画像など一部assetsは長期キャッシュへ戻してOK。
