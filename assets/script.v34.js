/* v34-trima-css-fix */
(() => {
  const links = document.querySelectorAll('[data-referral-link]');
  links.forEach((link) => {
    link.addEventListener('click', () => {
      const name = link.getAttribute('data-referral-link') || 'referral';
      if (typeof gtag === 'function') {
        gtag('event', 'referral_click', { item_name: name, link_url: link.href });
      }
      if (typeof clarity === 'function') {
        clarity('event', 'referral_click_' + name);
      }
    });
  });
})();
