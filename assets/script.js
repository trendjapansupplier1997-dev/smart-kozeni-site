
document.addEventListener('click', async (event) => {
  const button = event.target.closest('[data-copy]');
  if (!button) return;
  const text = button.getAttribute('data-copy');
  try { await navigator.clipboard.writeText(text); const old = button.textContent; button.textContent = 'コピー済み'; setTimeout(()=>button.textContent=old, 1500); }
  catch(e){ alert('コピーできませんでした。手動で選択してください。'); }
});


// v3: affiliate/outbound click measurement for GA4 and Microsoft Clarity.
document.addEventListener('click', (event) => {
  const affiliateLink = event.target.closest('a[data-affiliate]');
  if (!affiliateLink) return;
  const affiliate = affiliateLink.dataset.affiliate || 'unknown';
  const affiliateName = affiliateLink.dataset.affiliateName || affiliate;
  const payload = {
    affiliate: affiliate,
    affiliate_name: affiliateName,
    link_url: affiliateLink.href,
    link_text: (affiliateLink.textContent || '').trim().slice(0, 80),
    page_location: window.location.href,
    page_path: window.location.pathname
  };
  if (typeof window.gtag === 'function') {
    window.gtag('event', 'affiliate_click', payload);
    window.gtag('event', 'affiliate_click_' + affiliate, payload);
  }
  if (typeof window.clarity === 'function') {
    window.clarity('event', 'affiliate_click_' + affiliate);
  }
});

document.addEventListener('click', (event) => {
  const cta = event.target.closest('a.button, a.card-link');
  if (!cta || cta.dataset.affiliate) return;
  const href = cta.getAttribute('href') || '';
  if (!href || href.startsWith('#')) return;
  const payload = {
    link_url: cta.href,
    link_text: (cta.textContent || '').trim().slice(0, 80),
    page_location: window.location.href,
    page_path: window.location.pathname
  };
  if (typeof window.gtag === 'function') window.gtag('event', 'internal_cta_click', payload);
  if (typeof window.clarity === 'function') window.clarity('event', 'internal_cta_click');
});
