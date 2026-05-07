(() => {
  const buttons = document.querySelectorAll('[data-copy]');
  buttons.forEach((button) => {
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
      } catch (error) {
        window.prompt('コピーしてください', value);
      }
    });
  });
})();
