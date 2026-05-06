
document.addEventListener('click', async (event) => {
  const button = event.target.closest('[data-copy]');
  if (!button) return;
  const text = button.getAttribute('data-copy');
  try { await navigator.clipboard.writeText(text); const old = button.textContent; button.textContent = 'コピー済み'; setTimeout(()=>button.textContent=old, 1500); }
  catch(e){ alert('コピーできませんでした。手動で選択してください。'); }
});
