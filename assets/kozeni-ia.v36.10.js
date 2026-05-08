(function(){
  var button = document.querySelector('[data-menu-toggle]');
  if (button) {
    button.addEventListener('click', function(){ document.body.classList.toggle('menu-open'); });
    document.addEventListener('keydown', function(event){ if (event.key === 'Escape') document.body.classList.remove('menu-open'); });
    document.querySelectorAll('.side-menu a').forEach(function(link){
      link.addEventListener('click', function(){ document.body.classList.remove('menu-open'); });
    });
  }

  function normalizePath(pathname) {
    if (!pathname) return '/';
    var path = pathname.replace(/\/index\.html$/, '/');
    if (path.length > 1 && path.endsWith('/')) return path;
    return path + (path === '/' ? '' : '/');
  }

  function isHome(path) { return path === '/' || path === '/index.html/'; }

  function fallbackHref(path) {
    if (path.indexOf('/tiktok-lite/') === 0) return '/point-site/';
    if (path.indexOf('/point-site/moppy/earn/') === 0) return '/point-site/moppy/';
    if (path.indexOf('/point-site/') === 0 && path !== '/point-site/') return '/point-site/';
    if (path.indexOf('/mobile-sim/') === 0 && path !== '/mobile-sim/') return '/mobile-sim/';
    if (path === '/point-site/' || path === '/mobile-sim/' || path === '/account-opening/' || path === '/credit-card/') return '/';
    return '/';
  }

  function injectBackButton() {
    var path = normalizePath(window.location.pathname);
    if (isHome(path)) return;
    if (document.querySelector('[data-kozeni-back]')) return;

    var style = document.createElement('style');
    style.textContent = [
      '.kozeni-backbar{width:min(1120px,calc(100% - 40px));margin:22px auto -28px;display:flex;align-items:center;gap:10px}',
      '.kozeni-backbtn{display:inline-flex;align-items:center;gap:8px;border:1px solid #dcece4;background:rgba(255,255,255,.92);color:#228C62;border-radius:999px;padding:9px 14px;font-size:13px;font-weight:950;box-shadow:0 12px 30px rgba(34,140,98,.10);transition:transform .16s ease,border-color .16s ease}',
      '.kozeni-backbtn:hover{transform:translateY(-1px);border-color:rgba(77,189,140,.58)}',
      '.kozeni-backbtn:focus-visible{outline:3px solid rgba(77,189,140,.35);outline-offset:3px}',
      '.kozeni-backicon{font-size:17px;line-height:1}',
      '@media (max-width:720px){.kozeni-backbar{width:calc(100% - 24px);margin:18px auto -18px}.kozeni-backbtn{padding:9px 13px}}'
    ].join('\n');
    document.head.appendChild(style);

    var bar = document.createElement('nav');
    bar.className = 'kozeni-backbar';
    bar.setAttribute('aria-label', '前のページへ');
    bar.setAttribute('data-kozeni-back', 'true');

    var link = document.createElement('a');
    link.className = 'kozeni-backbtn';
    link.href = fallbackHref(path);
    link.innerHTML = '<span class="kozeni-backicon" aria-hidden="true">←</span><span>前へ戻る</span>';

    link.addEventListener('click', function(event){
      var referrer = document.referrer;
      var sameOrigin = false;
      try { sameOrigin = !!referrer && new URL(referrer).origin === window.location.origin; } catch (error) { sameOrigin = false; }
      if (sameOrigin && window.history.length > 1) {
        event.preventDefault();
        window.history.back();
      }
    });

    bar.appendChild(link);

    var main = document.querySelector('.page-main') || document.querySelector('main') || document.body;
    var top = main.querySelector('.site-top');
    if (top && top.parentNode === main) top.insertAdjacentElement('afterend', bar);
    else main.insertBefore(bar, main.firstChild);
  }

  function setupQuizzes() {
    var quizzes = document.querySelectorAll('[data-kozeni-quiz]');
    if (!quizzes.length) return;

    quizzes.forEach(function(quiz) {
      var questions = Array.from(quiz.querySelectorAll('[data-quiz-question]'));
      var result = quiz.querySelector('[data-quiz-result]');
      var submit = quiz.querySelector('[data-quiz-submit]');
      var registerUrl = quiz.getAttribute('data-register-url') || '#';
      var registerName = quiz.getAttribute('data-register-name') || '登録先';

      function getAnswers() {
        return questions.map(function(q) {
          var selected = q.querySelector('[data-quiz-answer].is-selected');
          return selected ? selected.getAttribute('data-quiz-answer') : null;
        });
      }

      function render(force) {
        var answers = getAnswers();
        if (!force) {
          result.className = 'quiz-result';
          result.textContent = '3つ答えてから、結果を確認してください。';
          return;
        }

        if (answers.some(function(a){ return a === null; })) {
          result.className = 'quiz-result is-ng';
          result.textContent = '未回答があります。3つすべて答えてから確認してください。';
          return;
        }

        if (answers.every(function(a){ return a === 'yes'; })) {
          result.className = 'quiz-result is-ok';
          result.innerHTML = '登録前チェックはOKです。最後に公式画面の条件を確認して進んでください。<br><a href="' + registerUrl + '" target="_blank" rel="sponsored noopener noreferrer">' + registerName + 'に新規登録する</a>';
        } else {
          result.className = 'quiz-result is-ng';
          result.textContent = '今は無理に進めなくてOKです。条件を満たせるか、公式画面で確認してから判断してください。';
        }
      }

      quiz.querySelectorAll('[data-quiz-answer]').forEach(function(btn) {
        btn.addEventListener('click', function() {
          var wrap = btn.closest('[data-quiz-question]');
          wrap.querySelectorAll('[data-quiz-answer]').forEach(function(other) {
            other.classList.remove('is-selected');
            other.setAttribute('aria-pressed', 'false');
          });
          btn.classList.add('is-selected');
          btn.setAttribute('aria-pressed', 'true');
          render(false);
        });
      });

      if (submit) submit.addEventListener('click', function(){ render(true); });
      render(false);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function(){
      injectBackButton();
      setupQuizzes();
    });
  } else {
    injectBackButton();
    setupQuizzes();
  }
})();
