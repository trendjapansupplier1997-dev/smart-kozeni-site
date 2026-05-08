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


  function initQuickChecks() {
    document.querySelectorAll('[data-quick-check]').forEach(function(box) {
      var questions = Array.prototype.slice.call(box.querySelectorAll('[data-quiz-question]'));
      var result = box.querySelector('[data-quiz-result]');
      var label = box.querySelector('[data-result-label]');
      var title = box.querySelector('[data-result-title]');
      var copy = box.querySelector('[data-result-copy]');
      var link = box.querySelector('[data-result-link]');
      if (!questions.length || !result) return;

      function update() {
        var answers = questions.map(function(q) { return q.getAttribute('data-answer-value') || ''; });
        if (answers.some(function(v) { return !v; })) {
          result.hidden = true;
          return;
        }
        var hasNo = answers.indexOf('no') !== -1;
        var hasUnknown = answers.indexOf('unknown') !== -1;
        result.hidden = false;
        result.classList.remove('is-ok', 'is-caution', 'is-stop');

        if (hasNo) {
          result.classList.add('is-stop');
          if (label) label.textContent = 'RESULT';
          if (title) title.textContent = '今回は見送りでOK';
          if (copy) copy.textContent = '対象外の可能性があります。無理に進まず、別のアプリを選んで大丈夫です。';
          return;
        }
        if (hasUnknown) {
          result.classList.add('is-caution');
          if (label) label.textContent = 'RESULT';
          if (title) title.textContent = '条件を再確認';
          if (copy) copy.textContent = 'わからない項目があります。公式画面で条件・期限を確認してから判断しましょう。';
          if (link) link.textContent = '公式条件を確認';
          return;
        }
        result.classList.add('is-ok');
        if (label) label.textContent = 'RESULT';
        if (title) title.textContent = '狙う価値あり';
        if (copy) copy.textContent = '3つOK。対象の可能性があります。最後に公式画面で条件を確認してから進みましょう。';
        if (link) link.textContent = '公式へ進む';
      }

      questions.forEach(function(q) {
        q.querySelectorAll('[data-answer]').forEach(function(btn) {
          btn.addEventListener('click', function() {
            q.setAttribute('data-answer-value', btn.getAttribute('data-answer'));
            q.querySelectorAll('[data-answer]').forEach(function(other) { other.classList.remove('is-selected'); });
            btn.classList.add('is-selected');
            update();
          });
        });
      });
    });
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
    initQuickChecks();
  });
})();
