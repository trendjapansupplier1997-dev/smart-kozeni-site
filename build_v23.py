from pathlib import Path
import json, html, re, zipfile, os, shutil
from datetime import date
ROOT=Path('/mnt/data/kozeni_v23_work')
TODAY='2026-05-07'
VERSION='v23-tiktok-lite-seo-cluster'
CSS='style.v23.css'
JS='script.v23.js'
SITE='スマホ小銭研究所'
BASE='https://smart-kozeni.com'
CODES=['765692063','913299034']

def head(title, desc, canonical, faq=None, breadcrumb=None):
    faq_json=''
    if faq:
        faq_json='<script type="application/ld+json">'+json.dumps({
            "@context":"https://schema.org","@type":"FAQPage","mainEntity":[
                {"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in faq
            ]
        },ensure_ascii=False,separators=(',',':'))+'</script>'
    breadcrumb_json=''
    if breadcrumb:
        breadcrumb_json='<script type="application/ld+json">'+json.dumps({
            "@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[
                {"@type":"ListItem","position":i+1,"name":name,"item":BASE+url} for i,(name,url) in enumerate(breadcrumb)
            ]
        },ensure_ascii=False,separators=(',',':'))+'</script>'
    return f'''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{html.escape(title)}</title><meta name="description" content="{html.escape(desc)}"><meta name="robots" content="index,follow,max-image-preview:large"><link rel="canonical" href="{BASE}{canonical}"><meta property="og:site_name" content="{SITE}"><meta property="og:title" content="{html.escape(title)}"><meta property="og:description" content="{html.escape(desc)}"><meta property="og:type" content="website"><meta property="og:url" content="{BASE}{canonical}"><meta property="og:locale" content="ja_JP"><meta name="twitter:card" content="summary_large_image"><link rel="icon" href="/assets/favicon.svg" type="image/svg+xml"><meta name="theme-color" content="#082f2b"><link rel="apple-touch-icon" href="/assets/images/icon-192.png"><meta property="og:image" content="{BASE}/assets/images/ogp.png"><meta name="twitter:image" content="{BASE}/assets/images/ogp.png"><link rel="stylesheet" href="/assets/{CSS}"><script defer src="/assets/{JS}"></script><script type="application/ld+json">{{"@context":"https://schema.org","@type":"WebSite","name":"{SITE}","url":"{BASE}/","description":"登録前に条件を確認して、スマホで拾える小銭と紹介特典を整理するサイト。"}}</script><script type="application/ld+json">{{"@context":"https://schema.org","@type":"Organization","name":"{SITE}","url":"{BASE}/","sameAs":["https://x.com/smart_kozeni","https://www.instagram.com/smart_kozeni"]}}</script>{breadcrumb_json}{faq_json}<script async src="https://www.googletagmanager.com/gtag/js?id=G-V140MZBPKB"></script><script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-V140MZBPKB',{{anonymize_ip:true}});</script><script type="text/javascript">(function(c,l,a,r,i,t,y){{c[a]=c[a]||function(){{(c[a].q=c[a].q||[]).push(arguments)}};t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);}})(window,document,"clarity","script","wmurko5bi1");</script><meta name="x-kozeni-version" content="{VERSION}"></head>'''

def header(active='tiktok'):
    links=[('/', 'ホーム','home'),('/start-here/','はじめて','start'),('/tiktok-lite/','TikTok Lite','tiktok'),('/point-site/','ポイントサイト','point'),('/search/','検索','search')]
    nav=''.join([f'<a href="{u}" class="{ "is-active" if key==active else "" }">{label}</a>' for u,label,key in links])
    return f'''<body class="v23-page has-sticky"><header class="site-header v15-header"><nav class="nav" aria-label="主要ナビゲーション"><a class="brand" href="/"><span class="brand-mark" aria-hidden="true">¥</span><span>{SITE}</span></a><div class="nav-links">{nav}</div></nav></header>'''

def footer(sticky_main='/tiktok-lite/invite-code/', sticky_label='招待コードを見る', sticky_sub='/tiktok-lite/checklist/', sticky_sub_label='条件チェック'):
    return f'''<footer class="site-footer v15-footer"><div class="footer-inner"><div class="footer-grid"><div><strong>{SITE}</strong><p>登録前に条件を確認して、対象なら拾う。対象外ならやらない。</p><p class="note">※PR / 紹介リンクを含みます。報酬額・条件は変更される場合があります。開始前に必ず公式情報・アプリ内表示を確認してください。</p></div><div class="footer-links"><strong>まず見る</strong><a href="/quick-pick/">30秒診断</a><a href="/start-here/">初めての確認順</a><a href="/tiktok-lite/">TikTok Lite</a><a href="/tiktok-lite/invite-code/">TikTok Lite招待コード</a><a href="/point-site/referral-code/">紹介コード一覧</a></div><div class="footer-links"><strong>サイト情報</strong><a href="/policy/">PR表記・掲載方針</a><a href="/about/">このサイトについて</a><a href="/privacy/">プライバシーポリシー</a><a href="/sitemap.xml">sitemap.xml</a></div></div></div></footer><div class="v15-sticky v23-sticky"><a class="v15-sticky-main" href="{sticky_main}">{sticky_label}</a><a href="{sticky_sub}">{sticky_sub_label}</a></div><nav class="bottom-tabs v15-tabs" aria-label="スマホ下部ナビ"><a href="/"><b>⌂</b>ホーム</a><a href="/start-here/"><b>1</b>順番</a><a href="/tiktok-lite/"><b>♪</b>TikTok</a><a href="/point-site/referral-code/"><b>¥</b>コード</a></nav></body></html>'''

def code_buttons(extra=''):
    return '<div class="v23-code-stack">' + ''.join([f'<button class="v15-copy v23-copy" type="button" data-copy="{c}" data-copy-target="TikTok Lite {i+1}"><span>{c}</span><small>コピー</small></button>' for i,c in enumerate(CODES)]) + extra + '</div>'

def related(current=None):
    items=[('/tiktok-lite/invite-code/','招待コード','コードを控える'),('/tiktok-lite/checklist/','登録前チェック','始める前に見る'),('/tiktok-lite/not-eligible/','対象外確認','過去利用・端末'),('/tiktok-lite/reward-timing/','報酬反映','いつ反映？'),('/tiktok-lite/link-not-open/','リンク不具合','開かない時'),('/tiktok-lite/trouble/','反映されない','問い合わせ前'),('/tiktok-lite/terms-check/','条件画面の読み方','最大表示に注意'),('/tiktok-lite/first-3-days/','初回3日メモ','スクショと進捗')]
    cards=[]
    for url,title,desc in items:
        cls='is-current' if url==current else ''
        cards.append(f'<a class="v23-mini-card {cls}" href="{url}"><b>{title}</b><span>{desc}</span></a>')
    return '<section class="v23-section"><div class="v23-section-head"><p class="v23-kicker">関連記事</p><h2>悩み別に確認する</h2></div><div class="v23-related-grid">'+''.join(cards)+'</div></section>'

def pr_note():
    return '<div class="pr-box v15-pr v23-pr">※PR / 紹介コードを含みます。報酬額・条件・対象者・期限は時期やアカウントによって変わります。最終判断は必ずTikTok Liteアプリ内・公式表示で確認してください。</div>'

def breadcrumb_html(label):
    return f'<div class="breadcrumb"><a href="/">ホーム</a> / <a href="/tiktok-lite/">TikTok Lite</a> / {label}</div>'

def page(canonical,title,desc,label,hero_kicker,h1,lead,body,faq=None,sticky_label='コードを見る',sticky_sub_label='条件チェック'):
    bc=[('ホーム','/'),('TikTok Lite','/tiktok-lite/'),(label,canonical)]
    return head(title,desc,canonical,faq,bc)+header('tiktok')+f'<main id="main" class="container v15-container v23-container">{breadcrumb_html(label)}<section class="v23-hero"><div><p class="v23-kicker">{hero_kicker}</p><h1>{h1}</h1><p>{lead}</p><div class="v23-hero-actions"><a class="v19-btn primary" href="/tiktok-lite/invite-code/">招待コードを見る</a><a class="v19-btn" href="/tiktok-lite/checklist/">開始前チェック</a></div></div><aside class="v23-code-panel"><p>控えておくコード</p>{code_buttons()}<small>コードは複数控え。使う前にアプリ内条件を確認。</small></aside></section>{body}{pr_note()}</main>'+footer(sticky_label=sticky_label, sticky_sub_label=sticky_sub_label)

# Top page
faq_top=[('TikTok Liteの招待コードは？','スマホ小銭研究所で控えているコードは765692063と913299034です。利用前にアプリ内の最新条件を確認してください。'),('報酬額は固定ですか？','固定ではありません。キャンペーン、アカウント、時期によって変わるため、最大表示だけで判断せず、対象者・達成条件・期限・反映タイミングを確認してください。'),('リンクが開かない時はどうする？','別ブラウザ、通信、アプリの有無、コード控えを確認します。何度も登録し直す前に条件画面を確認してください。')]
body_top='''<section class="v23-section v23-path"><div><p class="v23-kicker">最短ルート</p><h2>登録前に、ここだけ順番に見る。</h2><p>「とりあえず入れる」より、先に対象外と期限を確認した方が安全です。</p></div><ol class="v23-steps"><li><b>コードを控える</b><span>765692063 / 913299034</span></li><li><b>対象外を確認</b><span>過去利用・端末・期限・キャンペーン名</span></li><li><b>アプリ内条件を見る</b><span>最大表示ではなく達成条件まで確認</span></li><li><b>進捗を保存</b><span>条件画面とミッション画面をスクショ</span></li></ol></section><section class="v23-section"><div class="v23-section-head"><p class="v23-kicker">入口</p><h2>今の悩みから選ぶ</h2></div><div class="v23-choice-grid"><a class="v23-choice hot" href="/tiktok-lite/invite-code/"><small>まず使う</small><b>招待コードをコピー</b><span>コード控え・使う前の注意</span></a><a class="v23-choice" href="/tiktok-lite/not-eligible/"><small>不安</small><b>対象外か確認</b><span>過去利用・端末・複数登録</span></a><a class="v23-choice" href="/tiktok-lite/reward-timing/"><small>待っている</small><b>報酬がいつ反映？</b><span>反映待ち・達成表示の見方</span></a><a class="v23-choice" href="/tiktok-lite/link-not-open/"><small>詰まった</small><b>リンクが開かない</b><span>ブラウザ・通信・アプリ確認</span></a></div></section><section class="v23-section v23-warning"><h2>このページの方針</h2><p>報酬額を大きく見せるより、対象外・期限・反映待ちの確認を優先します。キャンペーンは変わるので、ここでは「始める前に見る順番」を固定化しています。</p><div class="v23-badges"><span>PR表記あり</span><span>条件確認優先</span><span>誇大表現なし</span><span>アプリ内表示優先</span></div></section>'''+related('/tiktok-lite/')
(Path(ROOT/'tiktok-lite/index.html')).write_text(page('/tiktok-lite/','TikTok Lite招待コードと条件確認｜スマホ小銭研究所','TikTok Liteの招待コード、対象外条件、報酬反映、リンクが開かない時の確認順を整理。登録前にアプリ内の最新条件を確認してください。','TikTok Lite','TikTok Lite / PR','招待コードと条件を<br><span>先に確認。</span>','コードは控える。対象外を確認する。最後にアプリ内表示で判断する。この順番でミスを減らします。',body_top,faq_top,'コードを見る','条件チェック'),encoding='utf-8')

# invite page
faq_inv=[('TikTok Liteの招待コードは？','スマホ小銭研究所で控えているコードは765692063と913299034です。'),('コードだけ入力すれば必ず報酬がもらえますか？','必ずではありません。対象者、期限、達成条件、反映タイミングをアプリ内表示で確認してください。'),('リンクが開かない時もコードは使えますか？','キャンペーン仕様によって異なります。まずコードを控えたうえで、リンク不具合ページの確認順で切り分けてください。')]
body_inv=f'''<section class="v23-section v23-code-main"><div><p class="v23-kicker">コピー用</p><h2>招待コードを控える</h2><p>登録作業中にページを閉じても慌てないよう、先にコードをコピーしておきます。</p></div>{code_buttons()}</section><section class="v23-section"><div class="v23-section-head"><p class="v23-kicker">使う前</p><h2>コード入力前の3チェック</h2></div><div class="v23-check-grid"><div><b>1. 新規対象か</b><p>過去にTikTok / TikTok Liteを使ったことがある場合は、対象外になる可能性があります。</p></div><div><b>2. 期限はいつまでか</b><p>キャンペーンには期限や達成日数がある場合があります。開始前に画面を保存。</p></div><div><b>3. 達成条件は何か</b><p>登録だけでなく、チェックイン・視聴・タスク達成などが必要な場合があります。</p></div></div></section><section class="v23-section v23-flowline"><h2>おすすめの進め方</h2><ol><li><b>このページでコードをコピー</b><span>765692063 または 913299034</span></li><li><b>対象外ページを確認</b><span>過去利用・端末・アカウント条件を見る</span></li><li><b>アプリ内のキャンペーン画面を確認</b><span>最大額ではなく条件・期限・反映時期を見る</span></li><li><b>条件画面をスクショ</b><span>あとで反映待ちになった時の確認材料にする</span></li></ol></section>'''+related('/tiktok-lite/invite-code/')
(Path(ROOT/'tiktok-lite/invite-code/index.html')).write_text(page('/tiktok-lite/invite-code/','TikTok Lite招待コード｜765692063・913299034をコピー','TikTok Lite招待コード765692063・913299034を控えるページ。入力前に対象外条件、期限、達成条件、反映タイミングを確認してください。','招待コード','TikTok Lite / 招待コード','招待コードは<br><span>先に控える。</span>','リンクが開かない時や画面を閉じた時に備えて、コードと確認順を先に押さえます。',body_inv,faq_inv,'コードをコピー','対象外確認'),encoding='utf-8')

# checklist
faq_check=[('登録前に何を確認すべきですか？','招待コード、対象キャンペーン名、対象者、期限、達成条件、反映タイミング、交換先を確認します。'),('スクショは必要ですか？','必須とは限りませんが、条件画面・ミッション画面・進捗画面を保存しておくと反映待ちの確認がしやすくなります。')]
body_check='''<section class="v23-section"><div class="v23-section-head"><p class="v23-kicker">保存版</p><h2>開始前チェックリスト</h2></div><div class="v23-checklist-big"><label><input type="checkbox"> 招待コードを控えた</label><label><input type="checkbox"> 対象キャンペーン名を確認した</label><label><input type="checkbox"> 対象者・対象外条件を読んだ</label><label><input type="checkbox"> 達成期限を見た</label><label><input type="checkbox"> 何をすると報酬対象か確認した</label><label><input type="checkbox"> 反映タイミングの記載を見た</label><label><input type="checkbox"> 条件画面をスクショした</label><label><input type="checkbox"> ログインするアカウントを決めた</label></div></section><section class="v23-section v23-two"><div class="v23-panel"><h2>リンクを押す前</h2><ul class="checklist"><li>コードをコピー</li><li>過去利用がないか確認</li><li>期限・達成条件を読む</li><li>Wi-Fi/通信/ブラウザの状態を整える</li></ul></div><div class="v23-panel"><h2>登録直後</h2><ul class="checklist"><li>ミッション画面が出ているか</li><li>進捗が見えるか</li><li>反映待ち表示があるか</li><li>同じアカウントで進めているか</li></ul></div></section><section class="v23-section v23-warning"><h2>一番避けたいミス</h2><p>条件を読まずにインストール・登録だけ済ませてしまい、あとから「対象外」「期限切れ」「ミッション未達」に気づくパターンです。始める前に30秒だけ確認する方が安全です。</p></section>'''+related('/tiktok-lite/checklist/')
(Path(ROOT/'tiktok-lite/checklist/index.html')).write_text(page('/tiktok-lite/checklist/','TikTok Lite登録前チェックリスト｜対象外を避ける確認順','TikTok Liteの登録前に確認する招待コード、対象外条件、期限、達成条件、反映タイミング、スクショ保存のチェックリスト。','登録前チェック','TikTok Lite / チェックリスト','登録前に<br><span>30秒チェック。</span>','対象外や反映漏れを減らすため、始める前・登録直後・達成後に見る項目をまとめます。',body_check,faq_check,'チェックする','コードを見る'),encoding='utf-8')

# not eligible
faq_ne=[('TikTok Liteで対象外になる理由は？','代表的には過去利用、同一端末・同一アカウント、期限切れ、条件未達、キャンペーン対象外などが考えられます。実際の判定はアプリ内表示を確認してください。'),('対象外表示が出たらやり直せますか？','仕様や条件によって異なります。むやみに再登録するより、対象外表示・条件画面・ログイン状態を確認してください。')]
rows=[('過去に利用した','新規登録条件に関わる可能性','アプリ内の「新規」「過去利用」表記を確認'),('同じ端末・電話番号・アカウント','重複参加扱いになる可能性','別条件での参加可否は公式表示を見る'),('期限を過ぎた','チェックインやミッション期限切れ','開始日と達成期限をスクショ'),('リンク経由が切れた','紹介判定が付かない可能性','コード控えとキャンペーン画面を確認'),('年齢・地域・OS条件','キャンペーン対象者の条件外','対象者欄を確認'),('複数アカウント運用','規約・条件上のリスク','無理に回避しようとしない')]
body_ne='<section class="v23-section"><div class="v23-section-head"><p class="v23-kicker">対象外確認</p><h2>よくある確認ポイント</h2></div><div class="table-wrap"><table><thead><tr><th>確認ポイント</th><th>なぜ見る？</th><th>対応</th></tr></thead><tbody>'+''.join(f'<tr><td><b>{a}</b></td><td>{b}</td><td>{c}</td></tr>' for a,b,c in rows)+'</tbody></table></div></section><section class="v23-section v23-two"><div class="v23-panel warning"><h2>やらない方がいいこと</h2><ul class="checklist"><li>対象外表示のまま何度も登録し直す</li><li>条件を読まずに別アカウントを増やす</li><li>最大額だけ見て達成期限を見落とす</li></ul></div><div class="v23-panel info"><h2>先にやること</h2><ul class="checklist"><li>条件画面を開く</li><li>対象外表示の文言を確認</li><li>ログイン中のアカウントを見る</li><li>進捗・反映待ち画面を保存</li></ul></div></section>'+related('/tiktok-lite/not-eligible/')
(Path(ROOT/'tiktok-lite/not-eligible/index.html')).write_text(page('/tiktok-lite/not-eligible/','TikTok Lite対象外になりやすい人｜過去利用・端末・期限の確認','TikTok Liteで対象外になりやすい条件を整理。過去利用、同一端末、期限切れ、リンク経由、対象者条件を登録前に確認。','対象外確認','TikTok Lite / 対象外','対象外になりやすい所を<br><span>先に潰す。</span>','過去利用・端末・期限・リンク経由など、登録後に戻しにくいポイントを先に確認します。',body_ne,faq_ne,'対象外を確認','コードを見る'),encoding='utf-8')

# reward timing
faq_rt=[('TikTok Liteの報酬はいつ反映されますか？','キャンペーンごとに異なります。登録完了、タスク達成、チェックイン完了、審査後など条件により変わるため、アプリ内の反映時期を確認してください。'),('反映されない時は何を見る？','達成条件、進捗画面、対象外表示、ログインアカウント、反映予定時間、スクショを順番に確認します。')]
body_rt='''<section class="v23-section v23-flowline"><h2>反映待ちの確認順</h2><ol><li><b>達成条件</b><span>登録・視聴・チェックイン・タスクなど、何が条件かを見る</span></li><li><b>進捗画面</b><span>達成済み / 反映待ち / 未達 / 対象外 の表示を確認</span></li><li><b>ログイン状態</b><span>登録時と同じアカウントで見ているか確認</span></li><li><b>反映予定</b><span>即時か、一定時間後か、日数が必要かを見る</span></li><li><b>記録保存</b><span>条件画面・進捗画面・日時をスクショ</span></li></ol></section><section class="v23-section"><div class="v23-section-head"><p class="v23-kicker">見分け方</p><h2>慌てる前に表示を分ける</h2></div><div class="v23-check-grid"><div><b>未達</b><p>まだ条件を満たしていない状態。何が残っているか確認。</p></div><div><b>反映待ち</b><p>条件達成後、反映予定の時間や日数を待つ状態。</p></div><div><b>対象外</b><p>条件外の可能性。対象外ページで過去利用・期限などを確認。</p></div></div></section>'''+related('/tiktok-lite/reward-timing/')
(Path(ROOT/'tiktok-lite/reward-timing/index.html')).write_text(page('/tiktok-lite/reward-timing/','TikTok Lite報酬はいつ反映？反映待ちの確認順','TikTok Liteの報酬反映タイミング、反映待ち、未達、対象外の見分け方。問い合わせ前に見る画面と保存する情報を整理。','報酬反映','TikTok Lite / 反映待ち','報酬がいつ反映されるか<br><span>順番に確認。</span>','反映タイミングはキャンペーン次第です。焦って操作を増やす前に、表示と条件を分けて見ます。',body_rt,faq_rt,'反映確認','対象外確認'),encoding='utf-8')

# link not open
faq_link=[('TikTok Liteの招待リンクが開かない時は？','通信、ブラウザ、アプリの有無、リンクコピー、端末再起動を確認します。コードも先に控えておくと安全です。'),('アプリを先に開いてしまったら？','キャンペーン条件によって扱いが異なります。対象外になる可能性もあるため、アプリ内表示で判定を確認してください。')]
body_link='''<section class="v23-section"><div class="v23-section-head"><p class="v23-kicker">切り分け</p><h2>リンクが開かない時の順番</h2></div><div class="v23-check-grid"><div><b>1. 通信を切り替える</b><p>Wi-Fi/モバイル通信を切り替えて再読み込み。</p></div><div><b>2. 別ブラウザで開く</b><p>SNS内ブラウザで詰まる時は、Safari/Chromeなどで開く。</p></div><div><b>3. アプリ状態を見る</b><p>TikTok Liteが入っているか、先に開いていないか確認。</p></div><div><b>4. コードを控える</b><p>リンクが不安定な時のために、招待コードをコピー。</p></div><div><b>5. 条件画面を見る</b><p>開けたらすぐ対象者・期限・達成条件を確認。</p></div><div><b>6. 無理に連打しない</b><p>何度も登録し直す前に対象外表示を確認。</p></div></div></section><section class="v23-section v23-code-main"><div><h2>リンク不具合時の控え</h2><p>リンクが開かない時も、コードだけ先に控えておくと確認がしやすくなります。</p></div>'''+code_buttons()+'''</section>'''+related('/tiktok-lite/link-not-open/')
(Path(ROOT/'tiktok-lite/link-not-open/index.html')).write_text(page('/tiktok-lite/link-not-open/','TikTok Lite招待リンクが開かない時｜ブラウザ・通信・コード確認','TikTok Liteの招待リンクが開かない、白い画面になる、アプリに飛ばない時の切り分け。通信、ブラウザ、アプリ状態、コード控えを確認。','リンク不具合','TikTok Lite / リンク不具合','招待リンクが開かない時は<br><span>切り分ける。</span>','URLを連打するより、通信・ブラウザ・アプリ状態・コード控えの順で確認します。',body_link,faq_link,'リンク確認','コードを見る'),encoding='utf-8')

# trouble
faq_tr=[('TikTok Liteで反映されない時の最初の確認は？','達成条件、進捗表示、対象外表示、ログインアカウント、反映予定時間を確認します。'),('問い合わせ前に保存するものは？','条件画面、達成画面、反映待ち表示、対象外表示、登録日時が分かる情報を保存しておくと確認しやすくなります。')]
body_tr='''<section class="v23-section"><div class="v23-section-head"><p class="v23-kicker">問い合わせ前</p><h2>反映されない時の確認メモ</h2></div><div class="v23-checklist-big"><label><input type="checkbox"> 条件画面を保存している</label><label><input type="checkbox"> 達成済み表示を確認した</label><label><input type="checkbox"> 対象外表示が出ていない</label><label><input type="checkbox"> 同じアカウントで見ている</label><label><input type="checkbox"> 反映予定時間を過ぎている</label><label><input type="checkbox"> リンク/コード経由の画面を確認した</label></div></section><section class="v23-section v23-two"><div class="v23-panel"><h2>原因候補</h2><ul class="checklist"><li>条件未達</li><li>対象外条件に該当</li><li>反映待ち時間内</li><li>別アカウントで確認している</li><li>リンク経由が切れている</li></ul></div><div class="v23-panel"><h2>残す記録</h2><ul class="checklist"><li>キャンペーン名</li><li>対象条件</li><li>達成日時</li><li>進捗画面</li><li>対象外・エラー表示</li></ul></div></section>'''+related('/tiktok-lite/trouble/')
(Path(ROOT/'tiktok-lite/trouble/index.html')).write_text(page('/tiktok-lite/trouble/','TikTok Lite反映されない時｜問い合わせ前の確認メモ','TikTok Liteで報酬が反映されない時の確認順。条件未達、対象外、反映待ち、ログインアカウント、保存すべき画面を整理。','反映されない時','TikTok Lite / 反映されない','反映されない時は<br><span>原因を分ける。</span>','条件未達・対象外・反映待ち・ログイン違いを分けると、次に見る場所がはっきりします。',body_tr,faq_tr,'反映確認','チェックリスト'),encoding='utf-8')

# terms
faq_terms=[('最大〇〇円分は全員がもらえる意味ですか？','全員が必ず受け取れる意味とは限りません。対象者、達成条件、期限、反映タイミングを合わせて確認してください。'),('条件画面で特に見る場所は？','対象者、対象外条件、達成条件、期限、反映時期、交換先、注意事項です。')]
body_terms='''<section class="v23-section"><div class="v23-section-head"><p class="v23-kicker">読み方</p><h2>最大表示だけで判断しない</h2></div><div class="table-wrap"><table><thead><tr><th>見る場所</th><th>意味</th><th>注意</th></tr></thead><tbody><tr><td><b>最大〇〇円分</b></td><td>条件達成時の上限表示</td><td>全員が必ず受け取れる意味とは限りません。</td></tr><tr><td><b>対象者</b></td><td>誰が参加できるか</td><td>新規・地域・年齢・端末などを見る。</td></tr><tr><td><b>達成条件</b></td><td>何をすれば対象か</td><td>登録だけでなく、視聴・チェックインなどが必要な場合あり。</td></tr><tr><td><b>期限</b></td><td>いつまでに達成するか</td><td>開始日・連続日数・終了日を確認。</td></tr><tr><td><b>反映時期</b></td><td>いつポイントが入るか</td><td>即時・後日・条件達成後などの差を見る。</td></tr><tr><td><b>注意事項</b></td><td>対象外や例外</td><td>ここを読まずに始めるのが一番危険。</td></tr></tbody></table></div></section><section class="v23-section v23-warning"><h2>スマホ小銭研究所の判断基準</h2><p>「大きい金額が見える」より、「自分が対象で、条件を無理なく達成できる」ことを優先します。条件が曖昧なら、いったん進まず確認します。</p></section>'''+related('/tiktok-lite/terms-check/')
(Path(ROOT/'tiktok-lite/terms-check/index.html')).write_text(page('/tiktok-lite/terms-check/','TikTok Lite条件画面の読み方｜最大表示・対象者・期限を確認','TikTok Lite条件画面の読み方。最大表示、対象者、達成条件、期限、反映時期、注意事項を登録前に確認するメモ。','条件画面の読み方','TikTok Lite / 条件確認','条件画面は<br><span>ここを見る。</span>','最大表示だけで判断せず、対象者・達成条件・期限・反映タイミングをセットで読みます。',body_terms,faq_terms,'条件を見る','コードを見る'),encoding='utf-8')

# first 3 days
faq_3=[('初回3日で何を見る？','開始当日は条件画面、翌日は進捗・チェックイン、3日目以降は未達項目と期限を確認します。'),('毎日スクショが必要？','必須ではありませんが、条件画面や進捗画面を保存しておくと、反映待ちや問い合わせ時に確認しやすくなります。')]
body_3='''<section class="v23-section v23-flowline"><h2>初回3日の見る場所</h2><ol><li><b>開始当日</b><span>コード、条件、対象外、期限、キャンペーン名を保存</span></li><li><b>翌日</b><span>ミッション・チェックイン・進捗表示を確認</span></li><li><b>3日目以降</b><span>未達項目、反映待ち、期限切れがないか確認</span></li><li><b>完了後</b><span>報酬画面・交換先・反映予定を確認</span></li></ol></section><section class="v23-section"><div class="v23-section-head"><p class="v23-kicker">記録</p><h2>残すと便利なスクショ</h2></div><div class="v23-check-grid"><div><b>条件画面</b><p>対象者・達成条件・期限が載っている画面。</p></div><div><b>ミッション画面</b><p>現在の進捗やチェックイン状況が分かる画面。</p></div><div><b>報酬画面</b><p>反映済み・反映待ち・交換可能額が分かる画面。</p></div></div></section>'''+related('/tiktok-lite/first-3-days/')
(Path(ROOT/'tiktok-lite/first-3-days/index.html')).write_text(page('/tiktok-lite/first-3-days/','TikTok Lite初回3日で確認すること｜反映漏れを防ぐメモ','TikTok Lite開始直後の3日間で見る条件画面、進捗、チェックイン、報酬反映、保存するスクショを整理。','初回3日メモ','TikTok Lite / 初回3日','最初の3日は<br><span>記録を残す。</span>','開始直後は条件画面・ミッション画面・進捗をこまめに確認します。後から困らないためのメモです。',body_3,faq_3,'3日メモ','反映確認'),encoding='utf-8')

# update CSS/JS refs globally
for p in ROOT.rglob('*.html'):
    s=p.read_text(encoding='utf-8')
    s=s.replace('/assets/style.v22.css',f'/assets/{CSS}').replace('/assets/script.v22.js',f'/assets/{JS}')
    s=s.replace('content="v22-hard-cache-bust"',f'content="{VERSION}"')
    p.write_text(s,encoding='utf-8')
# copy assets
style=(ROOT/'assets/style.v22.css').read_text(encoding='utf-8')
style += r'''

/* v23: TikTok Lite SEO/conversion cluster */
.v23-container{padding-bottom:120px}.v23-page .is-active{background:#fff;border-color:var(--line);box-shadow:0 6px 16px rgba(16,32,28,.06)}.v23-kicker{margin:0 0 8px;color:#0d6b58;font-weight:950;letter-spacing:.08em;text-transform:uppercase;font-size:12px}.v23-hero{display:grid;grid-template-columns:minmax(0,1fr) 340px;gap:18px;align-items:stretch;border-radius:34px;padding:clamp(22px,5vw,44px);background:radial-gradient(circle at 100% 0,rgba(246,201,88,.45),transparent 28rem),linear-gradient(135deg,#10251f 0%,#173f35 54%,#fff8d8 54%,#fff 100%);box-shadow:var(--shadow);overflow:hidden}.v23-hero h1{font-size:clamp(40px,7vw,72px);line-height:1.02;letter-spacing:-.06em;margin:0 0 12px;color:#fff}.v23-hero h1 span{color:#f6c958}.v23-hero p{max-width:42rem;color:rgba(255,255,255,.88);font-weight:780;font-size:17px}.v23-hero-actions{display:flex;flex-wrap:wrap;gap:10px;margin-top:22px}.v23-code-panel{background:rgba(255,255,255,.94);border:1px solid rgba(255,255,255,.55);border-radius:28px;padding:18px;box-shadow:0 24px 60px rgba(0,0,0,.18);align-self:center}.v23-code-panel p{color:#123a32;margin:0 0 10px;font-weight:950}.v23-code-panel small{display:block;color:#63756f;font-weight:800;margin-top:10px}.v23-code-stack{display:grid;gap:10px}.v23-copy{appearance:none;border:1px solid #dcefe6;border-radius:20px;background:linear-gradient(135deg,#fff8db,#fff);padding:14px 16px;color:#123a32;display:flex;align-items:center;justify-content:space-between;gap:14px;font-weight:950;box-shadow:0 10px 22px rgba(16,32,28,.07);cursor:pointer}.v23-copy span{font-size:22px;letter-spacing:.02em;color:#0d6b58}.v23-copy small{margin:0!important;border-radius:999px;background:#10251f;color:#fff;padding:5px 9px;font-size:12px}.v23-section{margin-top:24px;background:#fff;border:1px solid var(--line);border-radius:30px;padding:clamp(18px,3vw,26px);box-shadow:var(--soft)}.v23-section h2{font-size:clamp(25px,4vw,38px);line-height:1.2;letter-spacing:-.035em;margin:0 0 12px;color:#10251f}.v23-section p{color:#526861;font-weight:730}.v23-section-head{display:flex;justify-content:space-between;gap:16px;align-items:end;margin-bottom:14px}.v23-path{display:grid;grid-template-columns:.78fr 1fr;gap:20px;align-items:center}.v23-steps{counter-reset:step;display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;list-style:none;margin:0;padding:0}.v23-steps li{background:#f7fbf7;border:1px solid var(--line);border-radius:20px;padding:16px;position:relative}.v23-steps li:before{counter-increment:step;content:counter(step);display:grid;place-items:center;width:28px;height:28px;border-radius:999px;background:#10251f;color:#f6c958;font-weight:950;margin-bottom:8px}.v23-steps b,.v23-flowline b{display:block;color:#10251f}.v23-steps span,.v23-flowline span,.v23-mini-card span,.v23-choice span{display:block;color:#60736d;font-weight:760;font-size:14px}.v23-choice-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}.v23-choice,.v23-mini-card{display:block;text-decoration:none;color:#10251f;background:#f8fbf6;border:1px solid var(--line);border-radius:22px;padding:16px;box-shadow:0 8px 20px rgba(16,32,28,.04)}.v23-choice.hot{background:linear-gradient(135deg,#fff4c3,#fff)}.v23-choice small{color:#0d6b58;font-weight:950}.v23-choice b{display:block;font-size:22px;line-height:1.2;margin:5px 0}.v23-warning{background:linear-gradient(135deg,#fff7da,#fff)}.v23-badges{display:flex;gap:8px;flex-wrap:wrap}.v23-badges span{border-radius:999px;background:#fff;border:1px solid #ecd78d;padding:7px 10px;font-weight:900;color:#6b4b00;font-size:13px}.v23-related-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px}.v23-mini-card.is-current{background:#10251f;color:#fff}.v23-mini-card.is-current span{color:rgba(255,255,255,.72)}.v23-code-main{display:grid;grid-template-columns:1fr 380px;gap:18px;align-items:center;background:linear-gradient(135deg,#f1fff7,#fff)}.v23-check-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}.v23-check-grid>div,.v23-panel{background:#f8fbf7;border:1px solid var(--line);border-radius:22px;padding:17px}.v23-check-grid b,.v23-panel h2{color:#10251f}.v23-flowline ol{display:grid;gap:10px;list-style:none;margin:0;padding:0;counter-reset:flow}.v23-flowline li{position:relative;background:#f8fbf7;border:1px solid var(--line);border-radius:20px;padding:15px 16px 15px 56px}.v23-flowline li:before{counter-increment:flow;content:counter(flow);position:absolute;left:16px;top:16px;width:28px;height:28px;border-radius:999px;display:grid;place-items:center;background:#0d6b58;color:#fff;font-weight:950}.v23-two{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}.v23-checklist-big{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.v23-checklist-big label{display:flex;gap:10px;align-items:flex-start;background:#f8fbf7;border:1px solid var(--line);border-radius:18px;padding:13px 14px;font-weight:850;color:#183d35}.v23-checklist-big input{accent-color:#0d6b58;margin-top:6px}.v23-pr{font-weight:800}.v23-sticky .v15-sticky-main{background:linear-gradient(135deg,#1c9d7f,#0d6b58)}@media(max-width:960px){.v23-hero,.v23-path,.v23-code-main,.v23-two{grid-template-columns:1fr}.v23-hero{background:linear-gradient(180deg,#10251f 0%,#163c32 58%,#fff8d8 58%,#fff 100%);padding:22px 18px}.v23-code-panel{margin-top:12px}.v23-steps,.v23-choice-grid,.v23-related-grid,.v23-check-grid,.v23-checklist-big{grid-template-columns:1fr}.v23-section-head{display:block}.v23-copy span{font-size:20px}}
'''
(ROOT/'assets'/CSS).write_text(style,encoding='utf-8')
script=(ROOT/'assets/script.v22.js').read_text(encoding='utf-8')
script += "\n// v23: TikTok Lite cluster uses existing copy, analytics, and SW cleanup handlers.\n"
(ROOT/'assets'/JS).write_text(script,encoding='utf-8')
# headers
(ROOT/'_headers').write_text(f'''/*
  X-Content-Type-Options: nosniff
  X-Frame-Options: DENY
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=()
  Cache-Control: no-cache, max-age=0, must-revalidate

/sw.js
  Cache-Control: no-store, no-cache, max-age=0, must-revalidate
  Service-Worker-Allowed: /

/assets/{CSS}
  Cache-Control: public, max-age=31536000, immutable

/assets/{JS}
  Cache-Control: public, max-age=31536000, immutable

/assets/images/*
  Cache-Control: public, max-age=31536000, immutable

/version.json
  Cache-Control: no-store, no-cache, max-age=0, must-revalidate

/__version.html
  Cache-Control: no-store, no-cache, max-age=0, must-revalidate
''',encoding='utf-8')
# version files
(ROOT/'version.json').write_text(json.dumps({"version":VERSION,"builtAt":"2026-05-07T00:00:00+09:00","notes":"TikTok Lite SEO/conversion cluster strengthened; v23 asset filenames; stable cache rules."},ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'__version.html').write_text(f'''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{VERSION}</title><link rel="stylesheet" href="/assets/{CSS}"></head><body><main class="container"><section class="v23-section"><p class="v23-kicker">Version</p><h1>{VERSION}</h1><p>Built: 2026-05-07 / TikTok Lite cluster update.</p><p><a class="v19-btn primary" href="/tiktok-lite/">TikTok Liteページへ</a></p></section></main></body></html>''',encoding='utf-8')
(ROOT/'V23_CHANGELOG.md').write_text('''# V23 Changelog - TikTok Lite SEO Cluster

- TikTok Lite配下9ページを検索意図別に再構成。
- 招待コード、対象外、報酬反映、リンク不具合、条件画面、初回3日メモの内部回遊を強化。
- FAQ構造化データを主要TikTok Liteページへ追加。
- v23のCSS/JSファイル名へ更新し、assetsはimmutable、HTMLは再検証キャッシュへ調整。
- version.json / __version.html を v23 に更新。
''',encoding='utf-8')
# update search data
sd=json.loads((ROOT/'assets/search-data.json').read_text(encoding='utf-8'))
updates={
'/tiktok-lite/':('TikTok Lite招待コードと条件確認','TikTok Liteの招待コード、対象外条件、報酬反映、リンクが開かない時の確認順。','TikTok Lite 招待コード 対象外 反映されない リンク 開かない'),
'/tiktok-lite/invite-code/':('TikTok Lite招待コード 765692063・913299034','TikTok Lite招待コード765692063・913299034をコピー。入力前に対象外条件と期限を確認。','TikTok Lite 招待コード 765692063 913299034 紹介コード'),
'/tiktok-lite/checklist/':('TikTok Lite登録前チェックリスト','TikTok Lite登録前に対象者、期限、達成条件、反映タイミング、スクショを確認。','TikTok Lite チェックリスト 登録前 条件 対象外'),
'/tiktok-lite/not-eligible/':('TikTok Lite対象外になりやすい人','過去利用、同一端末、期限切れ、リンク経由、対象者条件を登録前に確認。','TikTok Lite 対象外 過去利用 端末 期限'),
'/tiktok-lite/reward-timing/':('TikTok Lite報酬はいつ反映？','報酬反映、反映待ち、未達、対象外の確認順。','TikTok Lite 報酬 いつ 反映 反映待ち'),
'/tiktok-lite/link-not-open/':('TikTok Lite招待リンクが開かない時','招待リンクが開かない時のブラウザ、通信、アプリ状態、コード控えの確認。','TikTok Lite リンク 開かない 招待リンク 白い画面'),
'/tiktok-lite/trouble/':('TikTok Lite反映されない時','条件未達、対象外、反映待ち、ログインアカウント、保存すべき画面を整理。','TikTok Lite 反映されない 報酬 対象外'),
'/tiktok-lite/terms-check/':('TikTok Lite条件画面の読み方','最大表示、対象者、達成条件、期限、反映時期、注意事項を確認。','TikTok Lite 条件 最大 対象者 期限'),
'/tiktok-lite/first-3-days/':('TikTok Lite初回3日で確認すること','開始直後の3日間で見る条件画面、進捗、チェックイン、報酬反映を整理。','TikTok Lite 初回 3日 チェックイン 進捗')
}
seen={item['url']:item for item in sd}
for url,(title,desc,kw) in updates.items():
    if url in seen:
        seen[url].update(title=title,description=desc,keywords=kw)
    else:
        sd.append({'url':url,'title':title,'description':desc,'keywords':kw})
(ROOT/'assets/search-data.json').write_text(json.dumps(sd,ensure_ascii=False,indent=2),encoding='utf-8')
# sitemap: ensure lastmod and priority for tiktok pages
smap=(ROOT/'sitemap.xml').read_text(encoding='utf-8')
for url in updates:
    loc=f'https://smart-kozeni.com{url}'
    pattern=re.compile(rf'<url><loc>{re.escape(loc)}</loc><lastmod>[^<]+</lastmod><changefreq>[^<]+</changefreq><priority>[^<]+</priority></url>')
    pri='0.95' if url=='/tiktok-lite/' else '0.88'
    repl=f'<url><loc>{loc}</loc><lastmod>{TODAY}</lastmod><changefreq>weekly</changefreq><priority>{pri}</priority></url>'
    smap=pattern.sub(repl,smap)
(ROOT/'sitemap.xml').write_text(smap,encoding='utf-8')
# robots stays
# build zip excluding old temp build script and __MACOSX
out=Path('/mnt/data/smart-kozeni-pro-site-v23-tiktok-lite-seo-cluster.zip')
if out.exists(): out.unlink()
with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED) as z:
    for p in ROOT.rglob('*'):
        if p.is_dir():
            continue
        if p.name=='build_v23.py':
            continue
        rel=p.relative_to(ROOT)
        z.write(p,rel.as_posix())
print(out, out.stat().st_size)
