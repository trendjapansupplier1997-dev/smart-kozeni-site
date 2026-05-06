
async function initSearch(){
 const input=document.querySelector('#site-search'); const results=document.querySelector('#search-results');
 if(!input||!results) return;
 const res=await fetch('/assets/search-data.json'); const data=await res.json();
 function render(){
  const q=input.value.trim().toLowerCase();
  if(!q){results.innerHTML='<p class="note">キーワードを入力すると、関連ページを表示します。</p>';return;}
  const words=q.split(/\s+/).filter(Boolean);
  const hits=data.map(p=>{const hay=(p.title+' '+p.description+' '+p.keywords).toLowerCase(); let score=0; words.forEach(w=>{if(hay.includes(w)) score++}); return {...p,score};}).filter(p=>p.score>0).sort((a,b)=>b.score-a.score).slice(0,12);
  results.innerHTML=hits.length?hits.map(p=>`<div class="search-result"><a href="${p.url}">${p.title}</a><p class="note">${p.description}</p></div>`).join(''):'<p class="note">該当ページが見つかりません。TikTok Lite、ポイントサイト、KODO、PayPayなどで試してください。</p>';
  if(typeof sendEvent==='function') sendEvent('site_search',{search_term:q, result_count:hits.length});
 }
 input.addEventListener('input', render); render();
}
initSearch();
