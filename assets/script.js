
document.addEventListener('click', async (event) => {
  const button = event.target.closest('[data-copy]');
  if (!button) return;
  const text = button.getAttribute('data-copy');
  try {
    await navigator.clipboard.writeText(text);
    sendEvent('copy_code', { code_target: button.dataset.copyTarget || 'unknown', page_path: location.pathname });
    const old = button.textContent; button.textContent = 'コピー済み'; setTimeout(() => button.textContent = old, 1500);
  } catch(e) { alert('コピーできませんでした。手動で選択してください。'); }
});
function sendEvent(name, payload) {
  if (typeof window.gtag === 'function') window.gtag('event', name, payload || {});
  if (typeof window.clarity === 'function') window.clarity('event', name);
}
document.addEventListener('click', (event) => {
  const affiliateLink = event.target.closest('a[data-affiliate]');
  if (!affiliateLink) return;
  const affiliate = affiliateLink.dataset.affiliate || 'unknown';
  const payload = { affiliate, affiliate_name: affiliateLink.dataset.affiliateName || affiliate, link_url: affiliateLink.href, link_text: (affiliateLink.textContent || '').trim().slice(0,80), page_location: location.href, page_path: location.pathname };
  sendEvent('affiliate_click', payload);
  sendEvent('affiliate_click_' + affiliate, payload);
});
document.addEventListener('click', (event) => {
  const outbound = event.target.closest('a[href^="http"]');
  if (!outbound || outbound.dataset.affiliate) return;
  try { if (new URL(outbound.href).hostname === location.hostname) return; } catch(e) {}
  sendEvent('outbound_click', { link_url: outbound.href, link_text: (outbound.textContent||'').trim().slice(0,80), page_path: location.pathname });
});
document.addEventListener('click', (event) => {
  const cta = event.target.closest('a.button, a.card-link, .quick-choice a');
  if (!cta || cta.dataset.affiliate) return;
  const href = cta.getAttribute('href') || '';
  if (!href || href.startsWith('#')) return;
  sendEvent('internal_cta_click', { link_url: cta.href, link_text: (cta.textContent||'').trim().slice(0,80), page_path: location.pathname });
});
const firedScroll = new Set();
function checkScrollDepth() {
  const doc = document.documentElement;
  const height = doc.scrollHeight - window.innerHeight;
  if (height <= 0) return;
  const pct = Math.round((window.scrollY / height) * 100);
  [25, 50, 90].forEach(mark => { if (pct >= mark && !firedScroll.has(mark)) { firedScroll.add(mark); sendEvent('scroll_depth_' + mark, { percent: mark, page_path: location.pathname }); } });
}
addEventListener('scroll', checkScrollDepth, { passive: true });
addEventListener('load', () => { document.body.classList.toggle('has-sticky', !!document.querySelector('.sticky-cta')); });


// PWA install and lightweight member experience
let deferredInstallPrompt = null;
window.addEventListener('beforeinstallprompt', (event) => {
  event.preventDefault();
  deferredInstallPrompt = event;
  document.querySelectorAll('[data-install-app]').forEach(btn => btn.removeAttribute('hidden'));
  sendEvent('pwa_install_prompt_available', { page_path: location.pathname });
});
document.addEventListener('click', async (event) => {
  const install = event.target.closest('[data-install-app]');
  if (!install) return;
  if (!deferredInstallPrompt) {
    sendEvent('pwa_install_manual_guide', { page_path: location.pathname });
    location.href = '/install/';
    return;
  }
  deferredInstallPrompt.prompt();
  const result = await deferredInstallPrompt.userChoice;
  sendEvent('pwa_install_choice', { outcome: result.outcome, page_path: location.pathname });
  deferredInstallPrompt = null;
});
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => navigator.serviceWorker.register('/sw.js').then(() => sendEvent('service_worker_registered', { page_path: location.pathname })).catch(() => {}));
}
function readMember(){ try { return JSON.parse(localStorage.getItem('kozeni_member') || 'null'); } catch(e){ return null; } }
function writeMember(data){ localStorage.setItem('kozeni_member', JSON.stringify(data)); }
function updateMemberUI(){ const member=readMember(); document.querySelectorAll('[data-member-name]').forEach(el => { el.textContent = member && member.nickname ? member.nickname : 'ゲスト研究員'; }); document.body.classList.toggle('is-member', !!member); }
document.addEventListener('submit', (event) => {
  const form = event.target.closest('[data-member-form]');
  if (!form) return;
  event.preventDefault();
  const data = Object.fromEntries(new FormData(form).entries());
  data.createdAt = new Date().toISOString();
  data.localOnly = true;
  writeMember(data);
  updateMemberUI();
  sendEvent('member_register_local', { interest: data.interest || 'unknown', page_path: location.pathname });
  const result = document.querySelector('[data-member-result]');
  if (result) result.textContent = '登録しました。この端末に研究員カードを保存しました。メール配信は本登録機能の実装後に有効化します。';
});
document.addEventListener('click', (event) => { const el = event.target.closest('[data-track]'); if (!el) return; sendEvent(el.dataset.track, { page_path: location.pathname, label: (el.textContent||'').trim().slice(0,80) }); });
document.addEventListener('DOMContentLoaded', updateMemberUI);
