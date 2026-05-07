/* v36-add-powl-referral */
(() => {
  const copyButtons = document.querySelectorAll('[data-copy]');
  copyButtons.forEach((button) => {
    button.addEventListener('click', async () => {
      const value = button.getAttribute('data-copy') || '';
      try {
        await navigator.clipboard.writeText(value);
        button.classList.add('copied');
        const label = button.querySelector('small');
        const original = label ? label.textContent : '';
        if (label) label.textContent = 'コピー済み';
        window.setTimeout(() => {
          button.classList.remove('copied');
          if (label) label.textContent = original || 'コピー';
        }, 1400);
        if (typeof gtag === 'function') gtag('event', 'copy_code', { item_name: value, page_path: location.pathname });
        if (typeof clarity === 'function') clarity('event', 'copy_code');
      } catch (error) {
        window.prompt('コピーしてください', value);
      }
    });
  });

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
