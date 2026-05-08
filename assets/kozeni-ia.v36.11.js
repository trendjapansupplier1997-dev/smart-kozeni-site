(function(){
  function onReady(fn){
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', fn);
    else fn();
  }

  function normalizePath(pathname) {
    if (!pathname) return '/';
    var path = pathname.replace(/\/index\.html$/, '/');
    if (path.length > 1 && path.endsWith('/')) return path;
    return path + (path === '/' ? '' : '/');
  }

  function isHome(path) { return path === '/' || path === '/index.html/'; }

  function fallbackHref(path) {
    if (path.indexOf('/tiktok-lite/earn/') === 0) return '/tiktok-lite/';
    if (path.indexOf('/tiktok-lite/') === 0) return '/point-site/';
    if (path.indexOf('/point-site/') === 0 && path.indexOf('/earn/') > -1) {
      return path.replace(/earn\/$/, '');
    }
    if (path.indexOf('/point-site/') === 0 && path !== '/point-site/') return '/point-site/';
    if (path.indexOf('/mobile-sim/') === 0 && path !== '/mobile-sim/') return '/mobile-sim/';
    if (path === '/point-site/' || path === '/mobile-sim/' || path === '/account-opening/' || path === '/credit-card/') return '/';
    return '/';
  }

  function injectSharedStyles() {
    if (document.querySelector('[data-kozeni-js-style]')) return;

    var style = document.createElement('style');
    style.setAttribute('data-kozeni-js-style', 'true');
    style.textContent = [
      '.kozeni-backbar{width:min(1120px,calc(100% - 40px));margin:22px auto -28px;display:flex;align-items:center;gap:10px}',
      '.kozeni-backbtn{display:inline-flex;align-items:center;gap:8px;border:1px solid #dcece4;background:rgba(255,255,255,.92);color:#228C62;border-radius:999px;padding:9px 14px;font-size:13px;font-weight:950;box-shadow:0 12px 30px rgba(34,140,98,.10);transition:transform .16s ease,border-color .16s ease}',
      '.kozeni-backbtn:hover{transform:translateY(-1px);border-color:rgba(77,189,140,.58)}',
      '.kozeni-backbtn:focus-visible,.kozeni-point-return a:focus-visible,.quiz-register-link:focus-visible{outline:3px solid rgba(77,189,140,.35);outline-offset:3px}',
      '.kozeni-backicon{font-size:17px;line-height:1}',
      '.kozeni-point-return{position:fixed;left:50%;bottom:18px;transform:translateX(-50%);z-index:140;width:min(420px,calc(100% - 28px));pointer-events:none}',
      '.kozeni-point-return a{pointer-events:auto;display:flex;align-items:center;justify-content:center;min-height:48px;border-radius:999px;background:linear-gradient(135deg,#228C62,#4DBD8C);color:#fff;font-size:15px;font-weight:950;box-shadow:0 18px 44px rgba(34,140,98,.28);border:1px solid rgba(255,255,255,.38)}',
      '.kozeni-point-return a:hover{transform:translateY(-1px)}',
      '.quiz-register-link{display:inline-flex!important;align-items:center;justify-content:center;margin-top:12px;border-radius:999px;background:linear-gradient(135deg,#228C62,#4DBD8C)!important;color:#fff!important;padding:11px 16px!important;font-weight:950!important;box-shadow:0 14px 34px rgba(34,140,98,.18)}',
      'body.has-kozeni-point-return .site-footer{padding-bottom:96px}',
      '@media (max-width:720px){.kozeni-backbar{width:calc(100% - 24px);margin:18px auto -18px}.kozeni-backbtn{padding:9px 13px}.kozeni-point-return{bottom:14px}}'
    ].join('\n');
    document.head.appendChild(style);
  }

  function setupMenu() {
    var button = document.querySelector('[data-menu-toggle]');
    if (!button) return;

    button.addEventListener('click', function(){ document.body.classList.toggle('menu-open'); });
    document.addEventListener('keydown', function(event){
      if (event.key === 'Escape') document.body.classList.remove('menu-open');
    });
    document.querySelectorAll('.side-menu a').forEach(function(link){
      link.addEventListener('click', function(){ document.body.classList.remove('menu-open'); });
    });
  }

  function injectBackButton() {
    var path = normalizePath(window.location.pathname);
    if (isHome(path)) return;
    if (document.querySelector('[data-kozeni-back]')) return;

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
      try { sameOrigin = !!referrer && new URL(referrer).origin === window.location.origin; }
      catch (error) { sameOrigin = false; }
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

  function injectPointSiteReturn() {
    var path = normalizePath(window.location.pathname);
    var isPointDetail = path.indexOf('/point-site/') === 0 && path !== '/point-site/';
    var isTikTok = path.indexOf('/tiktok-lite/') === 0;
    if (!isPointDetail && !isTikTok) return;
    if (document.querySelector('[data-kozeni-point-return]')) return;

    var nav = document.createElement('nav');
    nav.className = 'kozeni-point-return';
    nav.setAttribute('aria-label', 'ポイ活一覧へ戻る');
    nav.setAttribute('data-kozeni-point-return', 'true');

    var link = document.createElement('a');
    link.href = '/point-site/';
    link.textContent = 'ポイ活一覧へ戻る';

    nav.appendChild(link);
    document.body.appendChild(nav);
    document.body.classList.add('has-kozeni-point-return');
  }

  function setupQuizzes() {
    function findQuiz(element) {
      return element && element.closest ? element.closest('[data-kozeni-quiz]') : null;
    }

    function getQuestions(quiz) {
      return Array.from(quiz.querySelectorAll('[data-quiz-question]'));
    }

    function getResult(quiz) {
      return quiz.querySelector('[data-quiz-result]');
    }

    function getAnswers(quiz) {
      return getQuestions(quiz).map(function(q) {
        var selected = q.querySelector('[data-quiz-answer].is-selected');
        return selected ? selected.getAttribute('data-quiz-answer') : null;
      });
    }

    function resetResult(quiz) {
      var result = getResult(quiz);
      if (!result) return;
      result.className = 'quiz-result';
      result.textContent = '3つ答えてから、結果を確認してください。';
    }

    function showResult(quiz) {
      var result = getResult(quiz);
      if (!result) return;

      var answers = getAnswers(quiz);
      var registerUrl = quiz.getAttribute('data-register-url') || '#';
      var registerName = quiz.getAttribute('data-register-name') || '登録先';

      if (answers.some(function(a){ return a === null; })) {
        result.className = 'quiz-result is-ng';
        result.textContent = '未回答があります。3つすべて答えてから確認してください。';
        return;
      }

      if (answers.every(function(a){ return a === 'yes'; })) {
        result.className = 'quiz-result is-ok';
        result.innerHTML =
          '<strong>登録前チェックはOKです。</strong><br>' +
          '最後に公式画面の条件を確認して進んでください。<br>' +
          '<a class="quiz-register-link" href="' + registerUrl + '" target="_blank" rel="sponsored noopener noreferrer">' +
          registerName + 'に新規登録する</a>';
      } else {
        result.className = 'quiz-result is-ng';
        result.textContent = '今は無理に進めなくてOKです。条件を満たせるか、公式画面で確認してから判断してください。';
      }
    }

    document.querySelectorAll('[data-kozeni-quiz]').forEach(function(quiz){
      resetResult(quiz);
    });

    document.addEventListener('click', function(event) {
      var answer = event.target.closest ? event.target.closest('[data-quiz-answer]') : null;
      if (answer) {
        var question = answer.closest('[data-quiz-question]');
        var quiz = findQuiz(answer);
        if (!question || !quiz) return;

        question.querySelectorAll('[data-quiz-answer]').forEach(function(other) {
          other.classList.remove('is-selected');
          other.setAttribute('aria-pressed', 'false');
        });

        answer.classList.add('is-selected');
        answer.setAttribute('aria-pressed', 'true');
        resetResult(quiz);
        return;
      }

      var submit = event.target.closest ? event.target.closest('[data-quiz-submit]') : null;
      if (submit) {
        var targetQuiz = findQuiz(submit);
        if (!targetQuiz) return;
        showResult(targetQuiz);
      }
    });
  }

  onReady(function(){
    injectSharedStyles();
    setupMenu();
    injectBackButton();
    injectPointSiteReturn();
    setupQuizzes();
  });
})();