(function() {
  function normalize(path) {
    if (!path) return '/';
    path = path.split('?')[0].split('#')[0];
    if (path !== '/' && !path.endsWith('/')) path += '/';
    return path;
  }

  function openMenu(open) {
    document.body.classList.toggle('sk-menu-open', open);
    var btn = document.querySelector('.sk-menu-toggle');
    var overlay = document.querySelector('.sk-menu-overlay');
    if (btn) btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    if (overlay) overlay.hidden = !open;
  }

  function addHistoryButtons() {
    var frag = document.createDocumentFragment();

    var back = document.createElement('button');
    back.type = 'button';
    back.className = 'sk-page-turn prev sk-history-turn';
    back.setAttribute('aria-label', '前に見ていた画面へ戻る');
    back.textContent = '戻る';
    back.addEventListener('click', function() {
      try { sessionStorage.setItem('sk-history-back-used', '1'); } catch (e) {}
      if (window.history.length > 1) {
        window.history.back();
      } else {
        window.location.href = '/';
      }
    });
    frag.appendChild(back);

    var forward = document.createElement('button');
    forward.type = 'button';
    forward.className = 'sk-page-turn next sk-history-turn';
    forward.setAttribute('aria-label', '戻る前に見ていた画面へ進む');
    forward.textContent = '進む';
    forward.addEventListener('click', function() {
      window.history.forward();
    });
    frag.appendChild(forward);

    document.body.appendChild(frag);
  }

  document.addEventListener('DOMContentLoaded', function() {
    var current = normalize(document.body.getAttribute('data-page-path') || location.pathname);

    document.querySelectorAll('.sk-left-menu a').forEach(function(a) {
      if (normalize(a.getAttribute('href')) === current) a.classList.add('is-active');
    });

    var btn = document.querySelector('.sk-menu-toggle');
    var overlay = document.querySelector('.sk-menu-overlay');
    if (btn) btn.addEventListener('click', function() { openMenu(!document.body.classList.contains('sk-menu-open')); });
    if (overlay) overlay.addEventListener('click', function() { openMenu(false); });
    document.addEventListener('keydown', function(e) { if (e.key === 'Escape') openMenu(false); });

    addHistoryButtons();
  });
})();
