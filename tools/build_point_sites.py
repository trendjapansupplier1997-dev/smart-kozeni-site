#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path
from string import Template
from typing import Any
sys.dont_write_bytecode = True
import monetization, site_common
ROOT=Path(__file__).resolve().parents[1]
SITE_DIR=ROOT/'data'/'point-site'/'sites'
GUIDE_DIR=ROOT/'data'/'point-site'/'guides'
HUB_PATH=ROOT/'data'/'point-site-hub.json'
DETAIL_TEMPLATE_PATH=ROOT/'templates'/'point-site-detail.html'
EARN_TEMPLATE_PATH=ROOT/'templates'/'point-site-earn.html'
GUIDE_TEMPLATE_PATH=ROOT/'templates'/'point-site-guide.html'
HUB_TEMPLATE_PATH=ROOT/'templates'/'point-site-hub.html'
STYLE_HREF='/assets/kozeni-point-site.v1.css?v=45.0'
SLUG_RE=re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')

def load_json(path:Path)->dict[str,Any]:
    data=json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data,dict): raise ValueError(f'{path}: root must be an object')
    return data

def require_strings(path:Path,data:dict[str,Any],keys:set[str])->None:
    for key in sorted(keys):
        if not str(data.get(key,'')).strip(): raise ValueError(f'{path}: {key} is required')

def require_list(path:Path,data:dict[str,Any],key:str,allow_empty:bool=False)->list[Any]:
    value=data.get(key)
    if not isinstance(value,list) or (not allow_empty and not value): raise ValueError(f'{path}: {key} must be a list')
    return value

def validate_link(path:Path,item:dict[str,Any],fields=('href','title','description'))->None:
    for field in fields:
        if not str(item.get(field,'')).strip(): raise ValueError(f'{path}: {field} is required')
    if not str(item['href']).startswith('/'): raise ValueError(f'{path}: href must be site-relative')

def load_site(path:Path)->dict[str,Any]:
    data=load_json(path); slug=data.get('slug')
    if not isinstance(slug,str) or not SLUG_RE.fullmatch(slug) or path.stem!=slug: raise ValueError(f'{path}: invalid slug')
    require_strings(path,data,{'name','title','description','eyebrow','h1','lead','checked_at'})
    site_common.parse_date(data['checked_at'],path)
    checks=require_list(path,data,'register_checks')
    if len(checks)!=3 or not all(str(x).strip() for x in checks): raise ValueError(f'{path}: register_checks must contain 3 strings')
    faq=require_list(path,data,'faq',allow_empty=True)
    for item in faq:
        if not isinstance(item,dict) or not str(item.get('question','')).strip() or not str(item.get('answer','')).strip(): raise ValueError(f'{path}: invalid faq')
    data['cta']=monetization.resolve_cta(data.get('cta'),path)
    earn=data.get('earn')
    if not isinstance(earn,dict): raise ValueError(f'{path}: earn must be an object')
    require_strings(path,earn,{'title','description','eyebrow','h1','lead','checked_at','ranking_title','ranking_intro'})
    site_common.parse_date(earn['checked_at'],path,'earn.checked_at')
    rankings=require_list(path,earn,'rankings')
    if len(rankings)!=5: raise ValueError(f'{path}: rankings must contain 5 rows')
    for i,item in enumerate(rankings,1):
        if not isinstance(item,dict) or item.get('rank')!=i: raise ValueError(f'{path}: ranking order is invalid')
        require_strings(path,item,{'name','summary','amount','amount_note','condition','memo'})
    require_list(path,earn,'rules'); require_list(path,earn,'avoid'); related=require_list(path,earn,'related')
    for item in related: validate_link(path,item,('href','label'))
    return data

def load_all_sites()->dict[str,dict[str,Any]]:
    sites={}
    for path in sorted(SITE_DIR.glob('*.json')):
        data=load_site(path); sites[data['slug']]=data
    if len(sites)!=8: raise ValueError(f'{SITE_DIR}: exactly 8 service files are required')
    return sites

def detail_canonical(data): return f'{site_common.BASE_URL}/point-site/{data["slug"]}/'
def earn_canonical(data): return f'{site_common.BASE_URL}/point-site/{data["slug"]}/earn/'
def detail_output(data): return ROOT/'point-site'/data['slug']/'index.html'
def earn_output(data): return ROOT/'point-site'/data['slug']/'earn'/'index.html'

def render_related(items):
    out=[]
    for item in items:
        href=item['href']; title=item.get('title') or item.get('label'); desc=item.get('description','関連ページを確認します。')
        if not href.startswith('/'): raise ValueError('related href must be site-relative')
        out.append(f'<a href="{site_common.esc(href)}"><strong>{site_common.esc(title)}</strong><span>{site_common.esc(desc)}</span></a>')
    return ''.join(out)

def render_detail(data,template):
    canonical=detail_canonical(data); faq=data['faq']
    faq_section=''
    if faq:
        faq_section='<section class="point-panel" aria-labelledby="faq-title"><h2 id="faq-title">よくある確認</h2><div class="point-faq">'+site_common.render_faq(faq)+'</div></section>'
    related=[
        {'href':f'/point-site/{data["slug"]}/earn/','title':f'{data["name"]}登録済みの人向け','description':'掲載例と条件確認の順番を見ます。'},
        {'href':'/point-site/','title':'ポイ活一覧','description':'ほかの候補を目的別に比較します。'},
        {'href':'/point-site/beginner/','title':'初めてのポイ活','description':'最初の1つを選ぶ順番を確認します。'},
        {'href':'/point-site/moppy-hapitas/','title':'モッピーとハピタス比較','description':'定番2サービスの使い分けを確認します。'},
    ]
    cta=monetization.render_cta(data['cta'],container_class='point-cta',link_class='point-cta__link',note_class='point-cta__note',tracking_class='point-cta__tracking',creative_class='point-cta__creative')
    return site_common.clean_rendered(template.substitute(
        title=site_common.esc(data['title']),description=site_common.esc(data['description']),canonical=canonical,name=site_common.esc(data['name']),
        seo_jsonld=site_common.render_page_jsonld(canonical=canonical,title=data['title'],description=data['description'],checked_at=data['checked_at'],breadcrumbs=[('ホーム',site_common.BASE_URL+'/'),('ポイ活',site_common.BASE_URL+'/point-site/'),(data['name'],canonical)]),
        eyebrow=site_common.esc(data['eyebrow']),h1=site_common.esc(data['h1']),lead=site_common.esc(data['lead']),checked_at=data['checked_at'],checked_at_display=site_common.format_date(site_common.parse_date(data['checked_at'],Path(data['slug']))),
        earn_path=f'/point-site/{data["slug"]}/earn/',register_checks=''.join(f'<li>{site_common.esc(x)}</li>' for x in data['register_checks']),cta=cta,faq_section=faq_section,related=render_related(related)))

def render_earn(data,template):
    earn=data['earn']; canonical=earn_canonical(data)
    rankings=''.join(
        f'<article class="point-rank"><div class="point-rank__no">{item["rank"]}</div><div><strong>{site_common.esc(item["name"])}</strong><small>{site_common.esc(item["summary"])}</small></div><div><span class="point-rank__label">目安</span><b class="point-rank__amount">{site_common.esc(item["amount"])}</b><small>{site_common.esc(item["amount_note"])}</small></div><div><span class="point-rank__label">条件</span><small>{site_common.esc(item["condition"])}</small></div><div><span class="point-rank__label">判断</span><small>{site_common.esc(item["memo"])}</small></div></article>' for item in earn['rankings'])
    related=[{'href':x['href'],'title':x['label'],'description':'関連する登録前・登録後ページを確認します。'} for x in earn['related']]
    return site_common.clean_rendered(template.substitute(
        title=site_common.esc(earn['title']),description=site_common.esc(earn['description']),canonical=canonical,name=site_common.esc(data['name']),detail_path=f'/point-site/{data["slug"]}/',
        seo_jsonld=site_common.render_page_jsonld(canonical=canonical,title=earn['title'],description=earn['description'],checked_at=earn['checked_at'],breadcrumbs=[('ホーム',site_common.BASE_URL+'/'),('ポイ活',site_common.BASE_URL+'/point-site/'),(data['name'],detail_canonical(data)),('登録後',canonical)]),
        eyebrow=site_common.esc(earn['eyebrow']),h1=site_common.esc(earn['h1']),lead=site_common.esc(earn['lead']),checked_at=earn['checked_at'],checked_at_display=site_common.format_date(site_common.parse_date(earn['checked_at'],Path(data['slug']))),ranking_title=site_common.esc(earn['ranking_title']),ranking_intro=site_common.esc(earn['ranking_intro']),rankings=rankings,rules=''.join(f'<li>{site_common.esc(x)}</li>' for x in earn['rules']),avoid=site_common.render_list(earn['avoid']),related=render_related(related)))

def load_hub():
    data=load_json(HUB_PATH); require_strings(HUB_PATH,data,{'title','description','h1','lead','checked_at','note'}); site_common.parse_date(data['checked_at'],HUB_PATH)
    sections=require_list(HUB_PATH,data,'sections'); require_list(HUB_PATH,data,'checklist')
    for section in sections:
        require_strings(HUB_PATH,section,{'title'}); cards=require_list(HUB_PATH,section,'cards')
        for card in cards: validate_link(HUB_PATH,card,('href','tag','title','amount','description'))
    return data

def render_hub(data,template):
    canonical=site_common.BASE_URL+'/point-site/'
    sections=''.join('<section class="point-panel"><h2>'+site_common.esc(section['title'])+'</h2><div class="point-card-grid">'+''.join(f'<a class="point-card" href="{site_common.esc(c["href"])}"><span class="point-card__tag">{site_common.esc(c["tag"])}</span><h3>{site_common.esc(c["title"])}</h3><span class="point-card__amount">{site_common.esc(c["amount"])}</span><p>{site_common.esc(c["description"])}</p><span class="point-card__action">条件を見る →</span></a>' for c in section['cards'])+'</div></section>' for section in data['sections'])
    checklist=''.join(f'<article class="point-card"><span class="point-card__tag">{site_common.esc(x["label"])}</span><h3>{site_common.esc(x["title"])}</h3><p>{site_common.esc(x["description"])}</p></article>' for x in data['checklist'])
    return site_common.clean_rendered(template.substitute(title=site_common.esc(data['title']),description=site_common.esc(data['description']),canonical=canonical,seo_jsonld=site_common.render_page_jsonld(canonical=canonical,title=data['title'],description=data['description'],checked_at=data['checked_at'],breadcrumbs=[('ホーム',site_common.BASE_URL+'/'),('ポイ活',canonical)]),h1=site_common.esc(data['h1']),lead=site_common.esc(data['lead']),checked_at=data['checked_at'],checked_at_display=site_common.format_date(site_common.parse_date(data['checked_at'],HUB_PATH)),sections=sections,checklist=checklist,note=site_common.esc(data['note'])))

def load_guides():
    out={}
    for path in sorted(GUIDE_DIR.glob('*.json')):
        data=load_json(path); require_strings(path,data,{'page_type','slug','title','description','eyebrow','h1','lead','checked_at'}); site_common.parse_date(data['checked_at'],path)
        if path.stem!=data['slug'] or not SLUG_RE.fullmatch(data['slug']): raise ValueError(f'{path}: invalid slug')
        if data['page_type'] not in {'beginner','comparison'}: raise ValueError(f'{path}: unsupported page_type')
        related=require_list(path,data,'related')
        for item in related: validate_link(path,item)
        out[data['slug']]=data
    if set(out)!={'beginner','moppy-hapitas'}: raise ValueError(f'{GUIDE_DIR}: expected beginner and moppy-hapitas')
    return out

def render_guide(data,template):
    canonical=f'{site_common.BASE_URL}/point-site/{data["slug"]}/'
    if data['page_type']=='beginner':
        steps=''.join(f'<div class="point-step"><span class="point-step__no">{i}</span><div><strong>{site_common.esc(x["title"])}</strong><span>{site_common.esc(x["description"])}</span></div></div>' for i,x in enumerate(data['steps'],1))
        cards=''.join(f'<a class="point-card" href="{site_common.esc(x["href"])}"><span class="point-card__tag">{site_common.esc(x["tag"])}</span><h3>{site_common.esc(x["title"])}</h3><p>{site_common.esc(x["description"])}</p><span class="point-card__action">{site_common.esc(x["label"])} →</span></a>' for x in data['cards'])
        content=f'<section class="point-panel"><p class="point-label">最初の順番</p><h2>まず1つだけ選ぶ</h2><div class="point-step-grid">{steps}</div></section><section class="point-panel"><h2>初心者向けの9候補</h2><div class="point-card-grid">{cards}</div></section><p class="point-note">{site_common.esc(data["note"])}</p>'
    else:
        summary=''.join(f'<article class="point-card"><h3>{site_common.esc(x["title"])}</h3><p>{site_common.esc(x["description"])}</p></article>' for x in data['summary_cards'])
        rows=''.join(f'<tr><th>{site_common.esc(x["label"])}</th><td>{site_common.esc(x["description"])}</td></tr>' for x in data['comparison_rows'])
        content=f'<section class="point-panel"><p class="point-label">先に結論</p><h2>使う場面で分ける</h2><div class="point-summary-grid">{summary}</div></section><section class="point-panel"><h2>{site_common.esc(data["comparison_title"])}</h2><div class="point-table-wrap"><table class="point-comparison"><tbody>{rows}</tbody></table></div><p class="point-note">{site_common.esc(data["source_note"])}</p></section><section class="point-panel"><h2>登録前に見るポイント</h2><ul class="point-list">{site_common.render_list(data["checklist"])}</ul></section>'
    return site_common.clean_rendered(template.substitute(title=site_common.esc(data['title']),description=site_common.esc(data['description']),canonical=canonical,name=site_common.esc(data['h1']),seo_jsonld=site_common.render_page_jsonld(canonical=canonical,title=data['title'],description=data['description'],checked_at=data['checked_at'],breadcrumbs=[('ホーム',site_common.BASE_URL+'/'),('ポイ活',site_common.BASE_URL+'/point-site/'),(data['h1'],canonical)]),eyebrow=site_common.esc(data['eyebrow']),h1=site_common.esc(data['h1']),lead=site_common.esc(data['lead']),checked_at=data['checked_at'],checked_at_display=site_common.format_date(site_common.parse_date(data['checked_at'],Path(data['slug']))),guide_content=content,related=render_related(data['related'])))

def build_outputs():
    outputs={}; sites=load_all_sites(); dt=Template(DETAIL_TEMPLATE_PATH.read_text(encoding='utf-8')); et=Template(EARN_TEMPLATE_PATH.read_text(encoding='utf-8')); gt=Template(GUIDE_TEMPLATE_PATH.read_text(encoding='utf-8')); ht=Template(HUB_TEMPLATE_PATH.read_text(encoding='utf-8'))
    for data in sites.values(): outputs[detail_output(data)]=render_detail(data,dt); outputs[earn_output(data)]=render_earn(data,et)
    outputs[ROOT/'point-site'/'index.html']=render_hub(load_hub(),ht)
    for data in load_guides().values(): outputs[ROOT/'point-site'/data['slug']/'index.html']=render_guide(data,gt)
    if len(outputs)!=19: raise ValueError(f'expected 19 outputs, got {len(outputs)}')
    return outputs

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--check',action='store_true'); args=parser.parse_args(); failed=False
    for path,rendered in sorted(build_outputs().items()):
        rel=path.relative_to(ROOT)
        if args.check:
            if not path.exists() or path.read_text(encoding='utf-8')!=rendered: print(f'NG: {rel}'); failed=True
            else: print(f'OK: {rel}')
        else:
            path.parent.mkdir(parents=True,exist_ok=True); path.write_text(rendered,encoding='utf-8'); print(f'WROTE: {rel}')
    return 1 if failed else 0
if __name__=='__main__': raise SystemExit(main())
