(() => {
  'use strict';

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
  button.addEventListener('click', () => {
    setOpen(!document.body.classList.contains('foundation-menu-open'));
  });
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && document.body.classList.contains('foundation-menu-open')) {
      setOpen(false, true);
    }
  });
  document.addEventListener('click', (event) => {
    if (!document.body.classList.contains('foundation-menu-open')) return;
    if (menu.contains(event.target) || button.contains(event.target)) return;
    setOpen(false);
  });
  menu.querySelectorAll('a').forEach((link) => {
    link.addEventListener('click', () => setOpen(false));
  });
})();
