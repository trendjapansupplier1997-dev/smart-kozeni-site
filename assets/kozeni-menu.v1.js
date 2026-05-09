(() => {
  const button = document.querySelector('[data-menu-toggle]');
  const menu = document.querySelector('.side-menu');

  if (!button || !menu) return;

  if (!menu.id) menu.id = 'kozeni-home-menu';

  button.setAttribute('aria-controls', menu.id);
  button.setAttribute('aria-expanded', 'false');

  const setOpen = (open) => {
    document.body.classList.toggle('menu-open', open);
    button.setAttribute('aria-expanded', open ? 'true' : 'false');
    button.textContent = open ? '閉じる' : 'メニュー';
  };

  setOpen(false);

  button.addEventListener('click', () => {
    setOpen(!document.body.classList.contains('menu-open'));
  });

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') setOpen(false);
  });

  document.addEventListener('click', (event) => {
    if (!document.body.classList.contains('menu-open')) return;
    if (menu.contains(event.target) || button.contains(event.target)) return;
    setOpen(false);
  });

  menu.querySelectorAll('a').forEach((link) => {
    link.addEventListener('click', () => setOpen(false));
  });
})();
