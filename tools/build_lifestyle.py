#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re
from pathlib import Path
from string import Template
from typing import Any
import monetization, site_common

ROOT=Path(__file__).resolve().parents[1]
HUB_DIR=ROOT/'data'/'lifestyle'/'hubs'
GUIDE_DIR=ROOT/'data'/'lifestyle'/'guides'
HUB_TEMPLATE_PATH=ROOT/'templates'/'lifestyle-hub.html'
GUIDE_TEMPLATE_PATH=ROOT/'templates'/'lifestyle-guide.html'
STYLE_HREF='/assets/kozeni-lifestyle.v1.css?v=45.0'
EXPECTED_OUTPUTS={'shopping/index.html','shopping/coupon-check/index.html','travel/index.html','travel/cancel-fee-check/index.html'}
CATEGORY_META={
 'shopping': {'label':'買い物・日用品','href':'/shopping/'},
 'travel': {'label':'旅行・移動','href':'/travel/'},
}

def load_json(path:Path)->dict[str,Any]:
    value=json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value,dict): raise ValueError(f'{path}: root must be an object')
    return value

def req_str(path,data,keys):
    for key in keys:
        if not isinstance(data.get(key),str) or not data[key].strip(): raise ValueError(f'{path}: {key} must be a non-empty string')

def req_list(path,data,key):
    value=data.get(key)
    if not isinstance(value,list) or not value: raise ValueError(f'{path}: {key} must be a non-empty list')
    return value

def validate_related(path,items):
    for item in items:
        if not isinstance(item,dict): raise ValueError(f'{path}: related entries must be objects')
        req_str(path,item,{'href','title','description'})
        if not item['href'].startswith('/'): raise ValueError(f'{path}: related href must be site-relative')

def resolve_offers(path,items):
    result=[]
    for item in items:
        if not isinstance(item,dict) or set(item)!={'program_id','description'}: raise ValueError(f'{path}: offer must contain program_id and description')
        req_str(path,item,{'program_id','description'})
        cta=monetization.resolve_cta({'program_id':item['program_id']},path)
        if not cta['affiliate'] or cta.get('format')!='text': raise ValueError(f'{path}: lifestyle offers must be approved text programs')
        result.append({**item,'cta':cta})
    return result

def common(path,data,page_type):
    req_str(path,data,{'page_type','category','output','breadcrumb_label','title','description','eyebrow','h1','lead','checked_at','offers_title','offers_intro','offers_note'})
    if data['page_type']!=page_type: raise ValueError(f'{path}: page_type must be {page_type}')
    if data['category'] not in CATEGORY_META: raise ValueError(f'{path}: unknown category')
    if not data['output'].endswith('/index.html'): raise ValueError(f'{path}: invalid output')
    site_common.parse_date(data['checked_at'],path)
    tags=req_list(path,data,'tags')
    if not all(isinstance(x,str) and x.strip() for x in tags): raise ValueError(f'{path}: tags must be strings')
    data['offers']=resolve_offers(path,req_list(path,data,'offers'))
    validate_related(path,req_list(path,data,'related'))
    return data

def load_hub(path):
    data=common(path,load_json(path),'hub')
    req_str(path,data,{'cards_title','cards_intro'})
    for card in req_list(path,data,'cards'):
        if not isinstance(card,dict): raise ValueError(f'{path}: cards entries must be objects')
        req_str(path,card,{'label','title','description'})
        items=req_list(path,card,'items')
        if not all(isinstance(x,str) and x.strip() for x in items): raise ValueError(f'{path}: card items must be strings')
        if ('href' in card) != ('link_label' in card): raise ValueError(f'{path}: href and link_label must be paired')
        if 'href' in card and not card['href'].startswith('/'): raise ValueError(f'{path}: card href must be site-relative')
    return data

def load_guide(path):
    data=common(path,load_json(path),'guide')
    req_str(path,data,{'slug','summary_label','summary_title','summary_body','steps_title','avoid_label','avoid_title','avoid_body'})
    for key in ('summary_items',):
        items=req_list(path,data,key)
        if not all(isinstance(x,str) and x.strip() for x in items): raise ValueError(f'{path}: {key} must contain strings')
    for step in req_list(path,data,'steps'):
        if not isinstance(step,dict): raise ValueError(f'{path}: steps entries must be objects')
        req_str(path,step,{'title','description'})
    return data

def nav(category):
    links=[('mobile-sim','/mobile-sim/','スマホ・回線'),('point-site','/point-site/','ポイ活'),('shopping','/shopping/','買い物'),('credit-card','/credit-card/','クレカ'),('account-opening','/account-opening/','口座'),('travel','/travel/','旅行・移動')]
    return ''.join(f'<a{(" class=\"is-active\" aria-current=\"page\"" if key==category else "")} href="{href}">{label}</a>' for key,href,label in links)

def breadcrumb(data):
    meta=CATEGORY_META[data['category']]
    parts=['<a href="/">ホーム</a>','<span aria-hidden="true">›</span>']
    if data['page_type']=='hub': parts.append(f'<span aria-current="page">{site_common.esc(meta["label"])}</span>')
    else:
        parts.extend([f'<a href="{meta["href"]}">{site_common.esc(meta["label"])}</a>','<span aria-hidden="true">›</span>',f'<span aria-current="page">{site_common.esc(data["breadcrumb_label"])}</span>'])
    return ''.join(parts)

def render_offers(items):
    rows=[]
    for item in items:
        c=item['cta']
        rows.append(f'<a class="life-offer" href="{site_common.esc(c["url"])}" target="_blank" rel="nofollow sponsored noopener noreferrer" referrerpolicy="no-referrer-when-downgrade"><strong>{site_common.esc(c["advertiser"])}</strong><span>{site_common.esc(item["description"])}</span><small>{site_common.esc(c["label"])}</small></a>')
    return ''.join(rows)

def render_cards(cards):
    rows=[]
    for card in cards:
        link=f'<a class="life-card__link" href="{site_common.esc(card["href"])}">{site_common.esc(card["link_label"])}</a>' if 'href' in card else ''
        rows.append(f'<article class="life-card"><span class="life-tag">{site_common.esc(card["label"])}</span><h3>{site_common.esc(card["title"])}</h3><p>{site_common.esc(card["description"])}</p><ul class="life-list">{site_common.render_list(card["items"])}</ul>{link}</article>')
    return ''.join(rows)

def render_steps(steps):
    return ''.join(f'<div class="life-step"><span class="life-step__no">{i}</span><div><strong>{site_common.esc(x["title"])}</strong><span>{site_common.esc(x["description"])}</span></div></div>' for i,x in enumerate(steps,1))

def render_common(data,template,extra):
    canonical=f'{site_common.BASE_URL}/'+data['output'].removesuffix('index.html')
    meta=CATEGORY_META[data['category']]
    crumbs=[('ホーム',site_common.BASE_URL+'/')]
    if data['page_type']=='hub': crumbs.append((meta['label'],canonical))
    else: crumbs.extend([(meta['label'],site_common.BASE_URL+meta['href']),(data['breadcrumb_label'],canonical)])
    values={
      'title':site_common.esc(data['title']),'description':site_common.esc(data['description']),'canonical':canonical,'og_type':'website' if data['page_type']=='hub' else 'article',
      'seo_jsonld':site_common.render_page_jsonld(canonical=canonical,title=data['title'],description=data['description'],checked_at=data['checked_at'],breadcrumbs=crumbs),
      'main_nav':nav(data['category']),'breadcrumb':breadcrumb(data),'eyebrow':site_common.esc(data['eyebrow']),'h1':site_common.esc(data['h1']),'lead':site_common.esc(data['lead']),
      'tags':site_common.render_badges(data['tags']).replace('<span>','<span class="life-tag">'),'checked_at':data['checked_at'],'checked_at_display':site_common.format_date(site_common.parse_date(data['checked_at'],Path(data['output']))),
      'offers_title':site_common.esc(data['offers_title']),'offers_intro':site_common.esc(data['offers_intro']),'offers_note':site_common.esc(data['offers_note']),'offers':render_offers(data['offers']),
      'related':site_common.render_related(data['related']),'return_href':meta['href'],'return_label':site_common.esc(meta['label']),
    }
    values.update(extra)
    return site_common.clean_rendered(template.safe_substitute(values))

def render_hub(data,template):
    return render_common(data,template,{'cards_title':site_common.esc(data['cards_title']),'cards_intro':site_common.esc(data['cards_intro']),'cards':render_cards(data['cards'])})

def render_guide(data,template):
    return render_common(data,template,{
      'summary_label':site_common.esc(data['summary_label']),'summary_title':site_common.esc(data['summary_title']),'summary_body':site_common.esc(data['summary_body']),'summary_items':site_common.render_list(data['summary_items']),
      'steps_title':site_common.esc(data['steps_title']),'steps':render_steps(data['steps']),'avoid_label':site_common.esc(data['avoid_label']),'avoid_title':site_common.esc(data['avoid_title']),'avoid_body':site_common.esc(data['avoid_body'])})

def build_records():
    hub_template=Template(HUB_TEMPLATE_PATH.read_text(encoding='utf-8')); guide_template=Template(GUIDE_TEMPLATE_PATH.read_text(encoding='utf-8'))
    records=[]
    for path in sorted(HUB_DIR.glob('*.json')):
        data=load_hub(path); records.append((path,data,ROOT/data['output'],render_hub(data,hub_template)))
    for path in sorted(GUIDE_DIR.glob('*.json')):
        data=load_guide(path); records.append((path,data,ROOT/data['output'],render_guide(data,guide_template)))
    outputs={data['output'] for _,data,_,_ in records}
    if outputs!=EXPECTED_OUTPUTS: raise ValueError(f'expected {sorted(EXPECTED_OUTPUTS)}, got {sorted(outputs)}')
    return records

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--check',action='store_true'); args=parser.parse_args(); failed=False
    for _,_,output,rendered in build_records():
        rel=output.relative_to(ROOT)
        if args.check:
            if not output.exists() or output.read_text(encoding='utf-8')!=rendered: print(f'NG: {rel}'); failed=True
            else: print(f'OK: {rel}')
        else:
            output.parent.mkdir(parents=True,exist_ok=True); output.write_text(rendered,encoding='utf-8'); print(f'WROTE: {rel}')
    raise SystemExit(1 if failed else 0)
if __name__=='__main__': main()
