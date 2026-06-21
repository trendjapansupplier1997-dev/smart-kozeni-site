# デザイントークンSSOT

## 目的

色、フォント、角丸、影、基本余白をページ別CSSへ複製しない。
サイト共通の視覚プリミティブは次の1ファイルだけで管理する。

```text
assets/kozeni-tokens.v1.css
```

各カテゴリCSSは、ページ固有の意味を表す変数を残してよい。ただし値は共通トークンを参照する。

```css
:root {
  --point-deep: var(--kozeni-deep);
  --point-muted: var(--kozeni-muted);
  --point-line: var(--kozeni-line);
}
```

この二層構造により、カテゴリ内の読みやすい名前を維持しながら、実値のSSOTを一つにする。

## 読み込み順

すべてのHTMLは次の順序でCSSを読み込む。

1. `kozeni-tokens.v1.css`
2. `kozeni-brand.v1.css`
3. `kozeni-nav.v1.css`
4. 必要に応じて`kozeni-return.v1.css`
5. カテゴリ固有CSS

既存CSSは`/assets/*`のimmutableキャッシュ対象なので、トークン参照へ変更した版を確実に取得させるため`?v=<version>`を付ける。新規ファイルであるトークンCSSはファイル名の版で管理する。

生成対象HTMLへ直接`link`を追加しない。対応する`templates/*.html`を変更して再生成する。

## トークンの分類

### 色

- `--kozeni-green`：基本ブランドグリーン
- `--kozeni-deep`：主要CTAや濃いアクセント
- `--kozeni-deep-alt`：通信系ページの濃色
- `--kozeni-mint`：補助アクセント
- `--kozeni-pale`：薄いグリーン背景
- `--kozeni-ink`：基本文字色
- `--kozeni-muted`：補足文字色
- `--kozeni-white`：白い面
- `--kozeni-line`／`--kozeni-line-solid`：共通罫線
- `--kozeni-gold`：注意・特典の補助色

透過色はRGBチャネル変数を使う。

```css
background: rgba(var(--kozeni-rgb-green), .12);
```

同じRGB値を`rgba(34,140,98,.12)`のように再記述しない。

### フォント

本文フォントは共通トークンを使用する。

```css
font-family: var(--kozeni-font-sans);
```

既存表示を変えないため、クレカ系の日本語フォールバックは`--kozeni-font-sans-jp`、旧来のシステムスタックは`--kozeni-font-system`として中央管理する。新規ページでは原則`--kozeni-font-sans`を使う。コンポーネント内の`inherit`は許可するが、ページ別にフォントスタックを複製しない。

### 角丸

- `--kozeni-radius-pill`
- `--kozeni-radius-sm`
- `--kozeni-radius-md`
- `--kozeni-radius-lg`
- `--kozeni-radius-xl`

円形の`50%`や、明確に固有形状である値はカテゴリCSSに残してよい。

### 影

共通カード・パネルの影は`--kozeni-shadow-*`を使う。ページ固有の演出にだけ独自の影を残す。

### 余白

`--kozeni-space-1`から`--kozeni-space-8`は、新規コンポーネントや大きく修正する箇所で使用する。
既存レイアウトの余白を機械的に一括置換しない。見た目を変えずに意味が一致する箇所だけを移行する。

## 変更ルール

- 既存トークンの値変更はサイト全体へ影響するため、代表ページをデスクトップ・スマホ両方で確認する
- ページ固有色を安易に共通トークンへ昇格させない
- 同じ意味・同じ実値が複数カテゴリへ現れた場合にだけ共通化する
- `kozeni-tokens.v1.css`を変更して公開する場合、Cloudflareのimmutableキャッシュ方針を確認し、必要ならファイル名の版を上げる
- HTMLやJSONへ色・フォント・影を持ち込まない

## 自動検査

```bash
python3 tools/verify_site.py
```

デザイン監査は次を失敗として扱う。

- トークンCSSがない、複数回読み込まれる、またはブランドCSSより後に読み込まれる
- 共通色やRGBチャネルの生値がカテゴリCSSへ再導入される
- 共通フォントスタックが再複製される
- 共通角丸値が生値で再導入される
- インラインCSSまたはインライン実行JavaScriptが追加される
- 既存CSSのURLからキャッシュ更新用`?v=`が失われる
- どのHTMLからも参照されないCSS資産が残る
