
function sendEvent(name, payload) {
  try { if (typeof window.gtag === 'function') window.gtag('event', name, payload || {}); } catch(e) {}
  try { if (typeof window.clarity === 'function') window.clarity('event', name); } catch(e) {}
}
document.addEventListener('click', async (event) => {
  const button = event.target.closest('[data-copy]');
  if (!button) return;
  const text = button.getAttribute('data-copy');
  try { await navigator.clipboard.writeText(text); sendEvent('copy_code', { code_target: button.dataset.copyTarget || 'unknown', page_path: location.pathname }); const old=button.textContent; button.textContent='コピー済み'; setTimeout(()=>button.textContent=old,1500); } catch(e){ alert('コピーできませんでした。手動で選択してください。'); }
});
document.addEventListener('click', (event) => {
  const offerLink = event.target.closest('a[data-offer]');
  if (!offerLink) return;
  const offer = (offerLink.dataset.offer || 'unknown').replace(/-/g,'_');
  const payload = { offer, offer_name: offerLink.dataset.offerName || offer, link_url: offerLink.href, link_text: (offerLink.textContent || '').trim().slice(0,80), page_location: location.href, page_path: location.pathname };
  sendEvent('offer_link_tap', payload); sendEvent('offer_link_tap_' + offer, payload);
});
document.addEventListener('click', (event) => {
  const outbound = event.target.closest('a[href^="http"]'); if (!outbound || outbound.dataset.offer) return;
  try { if (new URL(outbound.href).hostname === location.hostname) return; } catch(e) {}
  sendEvent('outbound_click', { link_url: outbound.href, link_text: (outbound.textContent||'').trim().slice(0,80), page_path: location.pathname });
});
document.addEventListener('click', (event) => {
  const cta = event.target.closest('a.button, a.card-link, .quick-item, .mini-deal, .bottom-tabs a'); if (!cta || cta.dataset.offer) return;
  const href = cta.getAttribute('href') || ''; if (!href || href.startsWith('#')) return;
  sendEvent('internal_cta_click', { link_url: cta.href, link_text: (cta.textContent||'').trim().slice(0,80), page_path: location.pathname });
});
const firedScroll = new Set();
function checkScrollDepth(){ const doc=document.documentElement; const h=doc.scrollHeight-window.innerHeight; if(h<=0)return; const pct=Math.round((window.scrollY/h)*100); [25,50,75,90].forEach(mark=>{ if(pct>=mark&&!firedScroll.has(mark)){ firedScroll.add(mark); sendEvent('scroll_depth_'+mark,{percent:mark,page_path:location.pathname}); }}); }
addEventListener('scroll', checkScrollDepth, {passive:true});
let deferredInstallPrompt=null;
window.addEventListener('beforeinstallprompt',(event)=>{ event.preventDefault(); deferredInstallPrompt=event; document.querySelectorAll('[data-install-app]').forEach(btn=>btn.removeAttribute('hidden')); sendEvent('pwa_install_prompt_available',{page_path:location.pathname}); });
document.addEventListener('click',async(event)=>{ const install=event.target.closest('[data-install-app]'); if(!install)return; if(!deferredInstallPrompt){ sendEvent('pwa_install_manual_guide',{page_path:location.pathname}); if(!location.pathname.startsWith('/install')) location.href='/install/'; return; } deferredInstallPrompt.prompt(); const result=await deferredInstallPrompt.userChoice; sendEvent('pwa_install_choice',{outcome:result.outcome,page_path:location.pathname}); deferredInstallPrompt=null; });
if('serviceWorker' in navigator){ window.addEventListener('load',()=>navigator.serviceWorker.register('/sw.js').then(()=>sendEvent('service_worker_registered',{page_path:location.pathname})).catch(()=>{})); }
function readMember(){ try{return JSON.parse(localStorage.getItem('kozeni_member')||'null');}catch(e){return null;} }
function writeMember(data){ localStorage.setItem('kozeni_member',JSON.stringify(data)); }
function updateMemberUI(){ const m=readMember(); document.querySelectorAll('[data-member-name]').forEach(el=>{ el.textContent=m&&m.nickname?m.nickname:'ゲスト研究員'; }); document.body.classList.toggle('is-member',!!m); }
document.addEventListener('submit',(event)=>{ const form=event.target.closest('[data-member-form]'); if(!form)return; event.preventDefault(); const data=Object.fromEntries(new FormData(form).entries()); data.createdAt=new Date().toISOString(); data.localOnly=true; writeMember(data); updateMemberUI(); sendEvent('member_register_local',{interest:data.interest||'unknown',page_path:location.pathname}); const result=document.querySelector('[data-member-result]'); if(result) result.textContent='登録しました。この端末に研究員カードを保存しました。'; });
document.addEventListener('click',(event)=>{ const el=event.target.closest('[data-track]'); if(!el)return; sendEvent(el.dataset.track,{page_path:location.pathname,label:(el.textContent||'').trim().slice(0,80)}); });
document.addEventListener('DOMContentLoaded',()=>{ document.body.classList.toggle('has-sticky',!!document.querySelector('.sticky-cta')); updateMemberUI(); });


// v15 conversion UI: lightweight client-side filtering only. No Cloudflare setting required.
document.addEventListener('click', (event) => {
  const filterButton = event.target.closest('[data-v15-filter]');
  if (!filterButton) return;
  const raw = (filterButton.dataset.v15Filter || 'all').trim();
  const tokens = raw.split(/\s+/).filter(Boolean);
  document.querySelectorAll('[data-v15-filter]').forEach(btn => btn.classList.toggle('is-active', btn === filterButton));
  document.querySelectorAll('[data-v15-card]').forEach(card => {
    const values = (card.dataset.v15Card || '').split(/\s+/);
    const show = tokens.includes('all') || tokens.some(t => values.includes(t));
    card.classList.toggle('v15-card-hidden', !show);
  });
  sendEvent('v15_filter_click', { filter: raw, page_path: location.pathname });
});


// v17 quick-pick: one-tap recommendation. Static JS, no Cloudflare config needed.
document.addEventListener('click', (event) => {
  const pick = event.target.closest('[data-v17-pick]');
  if (!pick) return;
  const root = pick.closest('[data-v17-picker]');
  if (!root) return;
  const key = pick.dataset.v17Pick || '';
  root.querySelectorAll('[data-v17-pick]').forEach(btn => btn.classList.toggle('is-active', btn === pick));
  const idle = root.querySelector('[data-v17-idle]');
  if (idle) idle.hidden = true;
  root.querySelectorAll('[data-v17-result]').forEach(card => {
    card.hidden = card.dataset.v17Result !== key;
  });
  sendEvent('v17_quick_pick', { pick: key, page_path: location.pathname });
});
