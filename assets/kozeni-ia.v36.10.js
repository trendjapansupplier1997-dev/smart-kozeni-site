(function(){
  var button=document.querySelector('[data-menu-toggle]');
  if(!button)return;
  button.addEventListener('click',function(){document.body.classList.toggle('menu-open')});
  document.addEventListener('keydown',function(event){if(event.key==='Escape')document.body.classList.remove('menu-open')});
  document.querySelectorAll('.side-menu a').forEach(function(link){link.addEventListener('click',function(){document.body.classList.remove('menu-open')})});
})();
