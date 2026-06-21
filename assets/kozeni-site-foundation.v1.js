(() => {
  const loadAnalytics = () => {
    const gaId = 'G-V140MZBPKB';
    const clarityId = 'wmurko5bi1';

    window.dataLayer = window.dataLayer || [];
    window.gtag = window.gtag || function gtag() {
      window.dataLayer.push(arguments);
    };
    window.gtag('js', new Date());
    window.gtag('config', gaId);

    const ga = document.createElement('script');
    ga.async = true;
    ga.src = `https://www.googletagmanager.com/gtag/js?id=${encodeURIComponent(gaId)}`;
    document.head.appendChild(ga);

    window.clarity = window.clarity || function clarity() {
      (window.clarity.q = window.clarity.q || []).push(arguments);
    };
    const clarity = document.createElement('script');
    clarity.async = true;
    clarity.src = `https://www.clarity.ms/tag/${clarityId}`;
    const firstScript = document.getElementsByTagName('script')[0];
    if (firstScript && firstScript.parentNode) firstScript.parentNode.insertBefore(clarity, firstScript);
    else document.head.appendChild(clarity);
  };

  const initMenu = () => {
    const button = document.querySelector('[data-foundation-menu-toggle]');
    const menu = document.querySelector('[data-foundation-menu]');
    if (!button || !menu) return;

    button.setAttribute('aria-controls', menu.id);

    const setOpen = (open, returnFocus = false) => {
      document.body.classList.toggle('foundation-menu-open', open);
      button.setAttribute('aria-expanded', String(open));
      button.setAttribute('aria-label', open ? 'メニューを閉じる' : 'メニューを開く');
      button.textContent = open ? '閉じる' : 'メニュー';
      menu.setAttribute('aria-hidden', String(!open));
      if (open) menu.removeAttribute('inert');
      else menu.setAttribute('inert', '');
      if (returnFocus) button.focus();
    };

    setOpen(false);
    button.addEventListener('click', () => setOpen(!document.body.classList.contains('foundation-menu-open')));
    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape' && document.body.classList.contains('foundation-menu-open')) setOpen(false, true);
    });
    document.addEventListener('click', (event) => {
      if (!document.body.classList.contains('foundation-menu-open')) return;
      if (menu.contains(event.target) || button.contains(event.target)) return;
      setOpen(false);
    });
    menu.querySelectorAll('a').forEach((link) => link.addEventListener('click', () => setOpen(false)));
  };

  loadAnalytics();
  initMenu();
})();
