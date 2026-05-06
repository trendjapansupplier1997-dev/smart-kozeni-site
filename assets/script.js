
document.addEventListener('click', async (event) => {
  const button = event.target.closest('[data-copy]');
  if (!button) return;
  const text = button.getAttribute('data-copy');
  try {
    await navigator.clipboard.writeText(text);
    if (typeof window.gtag === 'function') window.gtag('event', 'copy_code', { code_target: button.dataset.copyTarget || 'unknown', page_path: window.location.pathname });
    if (typeof window.clarity === 'function') window.clarity('event', 'copy_code_' + (button.dataset.copyTarget || 'unknown'));
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
  const cta = event.target.closest('a.button, a.card-link');
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
  [50, 90].forEach(mark => { if (pct >= mark && !firedScroll.has(mark)) { firedScroll.add(mark); sendEvent('scroll_depth_' + mark, { percent: mark, page_path: location.pathname }); } });
}
addEventListener('scroll', checkScrollDepth, { passive: true });
addEventListener('load', () => { document.body.classList.toggle('has-sticky', !!document.querySelector('.sticky-cta')); });
