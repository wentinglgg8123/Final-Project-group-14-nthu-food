import './style.css';
import restaurants from './restaurants.json';
import {recommend, localTime, openingStatus} from './recommend.js';
const icons = {leaf:'✳',pin:'⌖',clock:'◷',heart:'♡',arrow:'↗',plus:'＋',close:'×'};
const esc = value => String(value).replace(/[&<>"']/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const read = (key,fallback) => {try {return JSON.parse(localStorage.getItem(key)) ?? fallback;} catch {return fallback;}};
let favorites = read('nthu-favorites',[]); if (!Array.isArray(favorites)) favorites=[];
let people = [{id:1,name:'用餐者 1',budget:2.5,type:'不限',walk:15}];
let nextId=2, tab='recommend', area='全部', search='', origin='清大校門', occasion='不限', openOnly=false, strict=true, time=localTime(), weights={price:35,distance:30,type:35};
let currentResults=[];
const types=[...new Set(restaurants.flatMap(r=>r.types))];
const option = (values, selected) => values.map(v=>`<option value="${esc(v)}" ${String(v)===String(selected)?'selected':''}>${esc(v)}</option>`).join('');
const priceLabel = p=>`級距 ${p} ${'＄'.repeat(Math.ceil(p))}`;
function art(r) {
  if (r.types.some(t=>['飲料','牛奶','超商'].includes(t))) return 'drink';
  if (r.types.some(t=>['豆花','甜點'].includes(t))) return 'dessert';
  if (r.types.some(t=>['麵食','義大利麵'].includes(t))) return 'noodles';
  if (r.types.some(t=>['早餐','早午餐'].includes(t))) return 'breakfast';
  return 'rice';
}
function foodSvg(kind) {
 const food={rice:'<ellipse cx="150" cy="88" rx="66" ry="24" fill="#f8f0d9"/><path d="M93 84q20-29 39-5q12-28 27-8q28-25 48 15" fill="#e6a044"/><path d="M106 76q10-20 23-11m37 8q12-22 28-6" stroke="#659352" stroke-width="14" stroke-linecap="round"/><circle cx="148" cy="84" r="17" fill="#fff5d5"/><circle cx="148" cy="84" r="9" fill="#edaf37"/>',noodles:'<ellipse cx="150" cy="88" rx="63" ry="23" fill="#8b4d2c"/><g stroke="#f0c67e" stroke-width="4" fill="none"><path d="M108 84q22-20 42 0t42 0M110 91q21-20 42 0t40 0M119 75q20-12 40 0t28 0"/></g><path d="M108 73l23-8m42 8l19-6" stroke="#7d9c52" stroke-width="10"/><path d="M180 17l-25 62m42-61l-32 62" stroke="#755036" stroke-width="4"/>',breakfast:'<path d="M102 97V59q-9-17 7-22q41-17 81 0q16 7 6 22v38z" fill="#c79055"/><path d="M110 91V60q-10-16 6-18q33-13 67 0q15 3 5 18v31z" fill="#f8e5b6"/><circle cx="149" cy="66" r="23" fill="#fff8e6"/><circle cx="150" cy="66" r="12" fill="#edac34"/><path d="M105 99l26-4m41 4l26-4" stroke="#6b934e" stroke-width="6"/>',drink:'<path d="M124 34h55l-6 87h-42z" fill="#f3e0b8"/><path d="M128 64h47l-4 54h-39z" fill="#b98450"/><path d="M149 49l14-38" stroke="#789775" stroke-width="6"/><ellipse cx="151" cy="34" rx="28" ry="6" fill="#fff7e6"/><g fill="#644936"><circle cx="143" cy="106" r="4"/><circle cx="155" cy="110" r="4"/><circle cx="163" cy="102" r="4"/></g>',dessert:'<ellipse cx="150" cy="90" rx="62" ry="24" fill="#d0ac84"/><path d="M105 85q20-25 38-6q20-25 47 5q-25 18-85 1" fill="#fbefcf"/><g fill="#ad7554"><circle cx="120" cy="89" r="6"/><circle cx="135" cy="94" r="5"/><circle cx="176" cy="88" r="6"/></g><path d="M185 73l24-30" stroke="#d9c5a4" stroke-width="5"/>'};
 return `<svg viewBox="0 0 300 160" aria-hidden="true"><ellipse cx="150" cy="134" rx="87" ry="9" fill="#000" opacity=".055"/><ellipse cx="150" cy="107" rx="86" ry="28" fill="#fcfaf2"/><ellipse cx="150" cy="105" rx="73" ry="22" fill="none" stroke="#e5dac5"/>${kind==='drink'?'':'<path d="M88 87q8 51 62 49q55 0 63-49z" fill="#f8f1df"/>'}${food[kind]}<path d="M54 53l7-9m-5 20l-10-1m194 34l9-5" stroke="#b3aa8b" stroke-width="2" stroke-linecap="round"/></svg>`;
}
document.querySelector('#app').innerHTML=`
<header class="header"><a class="brand" href="#"><span class="brand-mark">食</span><span>清食指南<small>NTHU FOOD GUIDE</small></span></a><nav aria-label="主選單"><button class="nav active" data-tab="recommend">探索美食</button><button class="nav" data-tab="favorites">我的收藏 <span id="fav-count">0</span></button><button class="nav" data-tab="database">餐廳資料庫</button></nav><span class="campus">⌖ 新竹・清華大學</span></header>
<main><section class="hero"><div class="hero-copy"><div class="eyebrow"><span></span> 好好吃飯，也是一件重要的事</div><h1>今天，吃點<span>什麼？<svg viewBox="0 0 220 12"><path d="M3 8 Q95 -3 217 7" fill="none" stroke="currentColor" stroke-width="5" stroke-linecap="round"/></svg></span></h1><p>從學餐到清夜，把選擇困難交給我們。<br>找到符合每個人口味的那一餐。</p><div class="hero-meta"><span><b>14</b> 間精選餐廳</span><i></i><span><b>2</b> 大美食區域</span><i></i><span>為你們一起挑選</span></div></div><div class="hero-art"><div class="orbit orbit-one"></div><div class="orbit orbit-two"></div><span class="art-note">GOOD FOOD, GOOD MOOD</span><div class="hero-dish">${foodSvg('rice')}</div><span class="float-note note-one">✦ 你的下一餐，這裡找</span><span class="float-note note-two">♥ 一起吃，更好吃</span><span class="hero-star">✳</span></div></section>
<div class="workspace"><aside class="preferences"><div class="section-heading"><span class="mini-icon">☷</span><h2>你們想吃什麼？</h2><button id="reset" class="text-button">重設</button></div><p class="muted aside-intro">告訴我們偏好，讓每個人都吃得開心。</p><div class="location-field"><label for="origin">⌖ 從哪裡出發</label><select id="origin">${option(['清大校門','小吃部','清夜'],origin)}</select></div><div class="diner-title"><h3>用餐夥伴 <span id="people-count">1</span></h3><span>最多 8 人</span></div><div id="people"></div><button id="add-person" class="add-person">＋ 新增用餐夥伴</button><div class="weights"><div class="weight-heading"><h3>推薦在意什麼？</h3><span>自由調整權重</span></div>${[['price','預算優先'],['distance','距離優先'],['type','口味優先']].map(([key,label])=>`<label class="weight-label" for="weight-${key}">${label}<output id="value-${key}">${weights[key]}</output></label><input type="range" id="weight-${key}" data-weight="${key}" min="0" max="100" value="${weights[key]}">`).join('')}</div><label class="check-label"><input type="checkbox" id="strict" checked>符合每個人的預算與距離</label><button id="recommend" class="primary">幫我們挑一餐 <span>↗</span></button><p class="fine-print">偏好即時套用，推薦分數以全員加權平均計算。</p></aside>
<section class="results-panel" aria-labelledby="result-title"><div class="results-heading"><div><div class="eyebrow small">YOUR NEXT FAVORITE</div><h2 id="result-title">為你們選好的美味 <span>✦</span></h2><p id="result-subtitle">不用再問「要吃什麼」，從這裡開始吧。</p></div><button id="surprise" class="secondary">⚄ 隨機幫我選</button></div><div class="toolbar"><div class="area-tabs" aria-label="餐廳區域">${['全部','小吃部','清夜'].map((a,i)=>`<button data-area="${a}" class="${i===0?'active':''}">${a==='全部'?'全部餐廳':a}</button>`).join('')}</div><label class="search-box"><span>⌕</span><input id="search" type="search" placeholder="找餐廳、想吃的料理…" aria-label="搜尋餐廳或料理"></label></div><div class="filter-row"><label class="check-label"><input id="open-only" type="checkbox">只看指定時間營業</label><input type="datetime-local" id="time" value="${time}" aria-label="用餐時間（台灣）"><label class="occasion-label">用餐情境 <select id="occasion">${option(['不限','一人食','約會','聚餐','快速吃','慢慢吃'],'不限')}</select></label></div><div class="result-info"><span id="result-count" aria-live="polite"></span><span id="sort-note">依推薦分數排序 ↓</span></div><div id="cards" class="cards"></div><div class="data-note"><span>ⓘ</span><p>資料來自你提供的餐廳清單。價格為原始級距（1–2.5），並非實際金額；步行時間為區域估算，非即時導航。營業資訊請以店家公告為準。</p></div></section></div>
<section class="bottom-banner"><div class="banner-icon">✳</div><div><h3>一個人吃，或是一群人吃，都值得好好選。</h3><p>把每個人的小偏好，變成一起吃飯的好理由。</p></div><span>LET’S EAT TOGETHER ↗</span></section></main><footer><span class="footer-brand">✳ 清食指南</span><span>清大學餐及周邊餐廳選擇器</span><span>Made for hungry NTHU souls.</span></footer><dialog id="detail"><div id="detail-content"></div></dialog><div id="toast" role="status"></div>`;
function renderPeople() {
 document.querySelector('#people-count').textContent=people.length;
 document.querySelector('#add-person').disabled=people.length>=8;
 document.querySelector('#people').innerHTML=people.map((p,i)=>`<div class="person"><div class="person-heading"><span class="avatar">${String(i+1).padStart(2,'0')}</span><input class="person-name" data-person="${p.id}" data-field="name" value="${esc(p.name)}" aria-label="用餐者 ${i+1} 姓名" maxlength="20">${people.length>1?`<button class="remove-person" data-remove="${p.id}" aria-label="移除 ${esc(p.name)}">×</button>`:''}</div><div class="person-grid"><label>預算級距<select data-person="${p.id}" data-field="budget">${[1,1.5,2,2.5].map(v=>`<option value="${v}" ${v===Number(p.budget)?'selected':''}>${v===2.5?'2.5（全部級距）':`${v} 以下`}</option>`).join('')}</select></label><label>願意走多久<select data-person="${p.id}" data-field="walk">${[5,10,15,20].map(v=>`<option value="${v}" ${v===Number(p.walk)?'selected':''}>${v} 分鐘內</option>`).join('')}</select></label><label class="full">想吃的料理<select data-person="${p.id}" data-field="type">${option(['不限',...types],p.type)}</select></label></div></div>`).join('');
}
function options() {return {origin, time, openOnly, strict, area, search, occasion};}
function renderResults() {
 currentResults = recommend(restaurants,people,weights,options());
 const results=tab==='favorites'?currentResults.filter(r=>favorites.includes(r.id)):currentResults;
 document.querySelector('#result-title').innerHTML=tab==='favorites'?'想再吃一次的口袋名單 <span>♡</span>':tab==='database'?'清大周邊美食地圖 <span>⌖</span>':'為你們選好的美味 <span>✦</span>';
 document.querySelector('#result-subtitle').textContent=tab==='database'?'完整資料庫保留原始資訊；目前條件也會套用於此。':tab==='favorites'?'收藏保存在這個瀏覽器，隨時回來找靈感。':'不用再問「要吃什麼」，從這裡開始吧。';
 document.querySelector('#fav-count').textContent=favorites.length;
 document.querySelector('#result-count').innerHTML=`找到 <b>${results.length}</b> 間${tab==='favorites'?'收藏':''}餐廳 <span>／資料庫共 ${restaurants.length} 間</span>`;
 document.querySelector('#sort-note').textContent=Object.values(weights).every(v=>v===0)?'權重皆為 0，使用等權平均 ↓':'依推薦分數排序 ↓';
 document.querySelector('#cards').innerHTML=results.length?results.map((r,i)=>`<article class="restaurant-card"><div class="card-art ${art(r)}">${foodSvg(art(r))}${i===0&&tab==='recommend'?'<span class="top-pick">✦ 本次首選</span>':''}<button class="favorite ${favorites.includes(r.id)?'saved':''}" data-favorite="${r.id}" aria-label="${favorites.includes(r.id)?'取消收藏':'收藏'} ${esc(r.name)}" aria-pressed="${favorites.includes(r.id)}">${favorites.includes(r.id)?'♥':'♡'}</button><span class="area-badge">⌖ ${r.location}</span></div><div class="card-body"><div class="card-title-row"><h3><button data-detail="${r.id}">${esc(r.name)}</button></h3><div class="score">${r.score}<small>推薦分數</small></div></div><p class="cuisine">${r.types.map(esc).join(' · ')}</p><div class="card-meta"><span>${priceLabel(r.price)}</span><span>♧ 約 ${r.walk} 分鐘</span></div><div class="hours ${r.status.state}"><span class="status-dot"></span>${r.status.label}<span class="hours-value">${esc(r.hours||'待確認')}</span></div><div class="reason"><span>✧</span><p>${esc(r.reasons[0])}<small>${esc(r.reasons[1])} · ${r.eligible===people.length?'全員距離可接受':`${r.eligible}/${people.length} 人符合預算及距離`}</small></p></div><button class="detail-link" data-detail="${r.id}">查看餐廳資訊 <span>↗</span></button></div></article>`).join(''):`<div class="empty"><span>⌕</span><h3>${tab==='favorites'?'還沒有符合條件的收藏':'暫時沒有符合條件的餐廳'}</h3><p>${tab==='favorites'?'點餐廳卡片上的愛心加入收藏，或放寬目前條件。':'試著增加預算、步行時間，或關閉營業時間篩選。'}</p><button class="secondary" id="clear-filters">重設篩選條件</button></div>`;
 document.querySelectorAll('[data-tab]').forEach(b=>b.classList.toggle('active',b.dataset.tab===tab));
 document.querySelectorAll('[data-area]').forEach(b=>b.classList.toggle('active',b.dataset.area===area));
}
let toastTimer;
function toast(text) {const el=document.querySelector('#toast');el.textContent=text;el.classList.add('show');clearTimeout(toastTimer);toastTimer=setTimeout(()=>el.classList.remove('show'),2600);}
function detail(id, random=false) {
 const r=restaurants.find(r=>r.id===Number(id)); if(!r)return;
 const result=currentResults.find(x=>x.id===r.id);const status=openingStatus(r,time);
 document.querySelector('#detail-content').innerHTML=`<button class="dialog-close" aria-label="關閉餐廳資訊">×</button><div class="dialog-art ${art(r)}">${foodSvg(art(r))}</div><div class="dialog-body"><div class="eyebrow small">${random?'YOUR LUCKY PICK · 今天就吃這間':'RESTAURANT DETAILS'}</div><h2>${esc(r.name)}</h2><p class="cuisine">${r.types.map(esc).join(' · ')}</p><dl><div><dt>所在區域</dt><dd>${esc(r.location)} · 從${origin}步行約 ${result?.walk??'?'} 分鐘（估算）</dd></div><div><dt>價格級距</dt><dd>${r.price} / 2.5（清單未提供實際金額）</dd></div><div><dt>一般營業時間</dt><dd>${esc(r.hours||'清單未提供，請向店家確認')}</dd></div><div><dt>特殊營業資訊</dt><dd>${esc(r.specialHours||'清單未提供特殊時段')}</dd></div><div><dt>指定時間狀態</dt><dd>${status.label}（台灣時間 ${esc(time.replace('T',' '))}）</dd></div><div><dt>適合情境</dt><dd>${r.occasions.join('、')||'未提供'}</dd></div></dl>${result?`<div class="dialog-reasons"><b>${result.score} 分 · 推薦給你們的理由</b><ul>${result.reasons.map(s=>`<li>${esc(s)}</li>`).join('')}</ul></div>`:''}<a class="primary map-link" href="https://www.google.com/maps/search/?api=1&query=${encodeURIComponent('新竹 清華大學 '+r.name)}" target="_blank" rel="noopener noreferrer">在 Google 地圖搜尋 ↗</a><p class="fine-print">資料僅供選餐參考；公休日、假日及實際營業狀態請向店家確認。</p></div>`;
 const dialog=document.querySelector('#detail');if(!dialog.open)dialog.showModal();
}
function reset() {
 people=[{id:nextId++,name:'用餐者 1',budget:2.5,type:'不限',walk:15}];area='全部';search='';origin='清大校門';occasion='不限';strict=true;openOnly=false;time=localTime();weights={price:35,distance:30,type:35};
 for(const [id,value] of Object.entries({origin,occasion,time,search}))document.getElementById(id).value=value;
 document.querySelector('#strict').checked=true;document.querySelector('#open-only').checked=false;
 for(const key of Object.keys(weights)){document.querySelector(`#weight-${key}`).value=weights[key];document.querySelector(`#value-${key}`).textContent=weights[key];}
 renderPeople();renderResults();
}
document.addEventListener('click',e=>{
 const b=e.target.closest('button');if(!b)return;
 if(b.dataset.tab){tab=b.dataset.tab;renderResults();}
 if(b.dataset.area){area=b.dataset.area;renderResults();}
 if(b.dataset.favorite){const id=Number(b.dataset.favorite);favorites=favorites.includes(id)?favorites.filter(x=>x!==id):[...favorites,id];try{localStorage.setItem('nthu-favorites',JSON.stringify(favorites));}catch{toast('無法儲存收藏，這次開啟期間仍可使用。');}renderResults();}
 if(b.dataset.detail)detail(b.dataset.detail);
 if(b.dataset.remove){people=people.filter(p=>p.id!==Number(b.dataset.remove));renderPeople();renderResults();}
 if(b.id==='add-person'&&people.length<8){people.push({id:nextId++,name:`用餐者 ${people.length+1}`,budget:2.5,type:'不限',walk:15});renderPeople();renderResults();}
 if(b.id==='reset'||b.id==='clear-filters')reset();
 if(b.id==='recommend'){tab='recommend';renderResults();toast('已依所有人的條件更新推薦');if(innerWidth<800)document.querySelector('.results-panel').scrollIntoView({behavior:'smooth'});}
 if(b.id==='surprise'){const pool=tab==='favorites'?currentResults.filter(r=>favorites.includes(r.id)):currentResults;if(pool.length)detail(pool[Math.floor(Math.random()*pool.length)].id,true);else toast('沒有符合條件的餐廳，請先放寬條件。');}
 if(b.classList.contains('dialog-close'))document.querySelector('#detail').close();
});
document.addEventListener('input',e=>{
 const el=e.target;
 if(el.dataset.person){const p=people.find(p=>p.id===Number(el.dataset.person));p[el.dataset.field]=el.value;renderResults();}
 if(el.dataset.weight){weights[el.dataset.weight]=Number(el.value);document.querySelector(`#value-${el.dataset.weight}`).textContent=el.value;renderResults();}
 if(el.id==='search'){search=el.value;renderResults();}
});
document.addEventListener('change',e=>{
 const el=e.target;
 if(!['origin','occasion','time','open-only','strict'].includes(el.id))return;
 if(el.id==='origin')origin=el.value;if(el.id==='occasion')occasion=el.value;
 if(el.id==='time'){time=el.value;if(!time)toast('請選擇用餐日期與時間。');}
 if(el.id==='open-only')openOnly=el.checked;if(el.id==='strict')strict=el.checked;
 renderResults();
});
document.querySelector('#detail').addEventListener('click',e=>{if(e.target.id==='detail')e.target.close();});
renderPeople();renderResults();
