(function() {
  var sequence = [["/", "ホーム"], ["/start-here/", "はじめて"], ["/tiktok-lite/", "TikTok Lite"], ["/point-site/moppy/", "モッピー"], ["/point-site/hapitas/", "ハピタス"], ["/point-site/trima/", "トリマ"], ["/point-site/kurashiru-reward/", "クラシルリワード"], ["/point-site/powl/", "Powl"], ["/point-site/pointtown/", "ポイントタウン"], ["/point-site/chobirich/", "ちょびリッチ"], ["/point-site/referral-code/", "紹介リンク一覧"]];
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
    var idx = sequence.findIndex(function(item) { return normalize(item[0]) === current; });
    if (idx >= 0) {
      var frag = document.createDocumentFragment();
      if (idx > 0) {
        var prev = sequence[idx - 1];
        var a = document.createElement('a');
        a.className = 'sk-page-turn prev';
        a.href = prev[0];
        a.innerHTML = '<small>前へ</small><span>' + prev[1] + '</span>';
        frag.appendChild(a);
      }
      if (idx < sequence.length - 1) {
        var next = sequence[idx + 1];
        var b = document.createElement('a');
        b.className = 'sk-page-turn next';
        b.href = next[0];
        b.innerHTML = '<small>次へ</small><span>' + next[1] + '</span>';
        frag.appendChild(b);
      }
      document.body.appendChild(frag);
    }
  });
})();
