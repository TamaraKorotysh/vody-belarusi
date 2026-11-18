# One-off patch: language switch (ru/be), collapsible river list, book data on small-river cards.
import os
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(root, "lp_template.html"); s = open(p, encoding="utf8").read()
def R(a, b):
    global s
    assert a in s, a[:80]; s = s.replace(a, b, 1)
def cut(start, end, new):
    global s
    i = s.index(start); j = s.index(end, i) + len(end); s = s[:i] + new + s[j:]

# ---------- HTML
R('<div class="brand paper"><h1>Воды <b>Беларуси</b></h1><p>Вращайте макет. Нажмите на булавку, затем на название.</p></div>',
  '<div class="brand paper"><div class="lang" role="group" aria-label="Язык / Мова"><button data-l="ru" aria-pressed="true">Рус</button><button data-l="be" aria-pressed="false">Бел</button></div><h1 id="title">Воды <b>Беларуси</b></h1><p id="hint">Вращайте макет. Нажмите на булавку, затем на название.</p></div>')
R('<nav class="list paper" id="list" aria-label="Реки и озёра"></nav>',
  '<nav class="list paper collapsed" id="list" aria-label="Реки и озёра"><button class="ltog" id="listToggle" aria-expanded="false" aria-controls="listBody"><i class="ic"></i><span id="listLabel">Реки и озёра</span><i class="chev"></i></button><div id="listBody"></div></nav>')

# ---------- CSS
R('.list{position:fixed;left:calc(env(safe-area-inset-left,0px) + 14px);bottom:calc(env(safe-area-inset-bottom,0px) + 14px);border-radius:14px;padding:8px;z-index:3;display:flex;flex-direction:column;gap:1px;max-height:calc(100% - 150px);overflow:auto}',
  '''.list{position:fixed;left:calc(env(safe-area-inset-left,0px) + 14px);bottom:calc(env(safe-area-inset-bottom,0px) + 14px);border-radius:14px;padding:6px;z-index:3;display:flex;flex-direction:column-reverse;gap:4px;width:250px}
.list.collapsed{width:auto}
.list.collapsed #listBody{display:none}
#listBody{display:flex;flex-direction:column;gap:1px;max-height:calc(100vh - 230px);overflow:auto;overscroll-behavior:contain}
.ltog{border:0;background:none;display:flex;align-items:center;gap:9px;padding:7px 10px;border-radius:9px;font-family:var(--f-display);font-weight:500;font-size:14px;letter-spacing:.08em;text-transform:uppercase;color:var(--ink);white-space:nowrap}
.ltog:hover{background:var(--line)}
.ltog .ic{width:16px;height:12px;background:linear-gradient(var(--river) 0 2px,transparent 2px 5px,var(--river) 5px 7px,transparent 7px 10px,var(--river) 10px 12px)}
.ltog .chev{margin-left:auto;width:8px;height:8px;border-right:2px solid var(--ink2);border-bottom:2px solid var(--ink2);transform:rotate(-135deg) translate(-2px,-2px);transition:transform .2s}
.list.collapsed .ltog .chev{transform:rotate(45deg) translate(-2px,-2px)}
.grp{border:0;background:none;display:flex;align-items:center;gap:6px;margin:6px 0 1px;padding:4px 8px;border-radius:7px;font-family:var(--f-display);font-weight:500;font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--ink2);text-align:left}
.grp:hover{background:var(--line)}
.grp small{font-size:10px;letter-spacing:.04em;opacity:.7}
.grp i{margin-left:auto;width:6px;height:6px;border-right:1.5px solid var(--ink2);border-bottom:1.5px solid var(--ink2);transform:rotate(45deg);transition:transform .2s}
.grp[aria-expanded="true"] i{transform:rotate(-135deg)}
.grp[hidden]{display:none!important}
.lang{float:right;display:flex;margin:2px 0 0 12px;border:1px solid var(--line);border-radius:999px;overflow:hidden}
.lang button{border:0;background:none;padding:3px 9px;font-family:var(--f-display);font-size:11.5px;letter-spacing:.08em;text-transform:uppercase;color:var(--ink2)}
.lang button[aria-pressed="true"]{background:var(--ink);color:var(--paper)}''')
R('@media (max-width:760px){#search{margin:0 4px 0 0;width:140px;flex:none}}\n', '')
R('''  .list{flex-direction:row;left:10px;right:10px;bottom:calc(env(safe-area-inset-bottom,0px) + 10px);max-height:none;overflow-x:auto;padding:6px}
  .list h4{display:none}
  .tools{bottom:calc(env(safe-area-inset-bottom,0px) + 66px);right:10px}''',
  '''  .list{left:10px;bottom:calc(env(safe-area-inset-bottom,0px) + 10px);width:auto;max-width:calc(100% - 20px);z-index:6}
  .list:not(.collapsed){right:10px}
  #listBody{max-height:52vh}
  .tools{bottom:calc(env(safe-area-inset-bottom,0px) + 10px);right:10px}
  .list:not(.collapsed)~.tools{display:none}''')

# ---------- data: Belarusian cards, small rivers with book data, language helpers
cut('const AUTO=/*AUTO*/;', 'from:["",""],to:[a.mouth||"",""],name:"",facts:[]};', '''/*CARDSBE*/
const AUTO=/*AUTO*/;
for(const a of AUTO)if(!CARDS[a.id]){const b=a.book||null;
  CARDS[a.id]={type:"river",minor:true,auto:true,be:a.be||a.ru,ru:a.ru,mouth:a.mouth,mouthBe:a.mouth_be||a.mouth,book:!!b,
    km:b?b.km:a.km,kin:a.kin,basin:b&&b.basin,q:b&&b.q,side:b&&b.side,stats:[],from:["",""],to:["",""],name:"",facts:[]}}
let LANG="ru";try{if(localStorage.getItem("lang")==="be")LANG="be"}catch(e){}
const TX={
 ru:{doc:"Воды Беларуси",title:"Воды <b>Беларуси</b>",hint:"Вращайте макет. Нажмите на булавку, затем на название.",refill:"Наполнить",home:"Весь макет",
  search:"Найти реку или озеро",searchAria:"Поиск по названию",list:"Реки и озёра",canvas:"Гранёный макет Беларуси с реками и озёрами",
  river:"Река",lake:"Озеро",riverL:"река",lakeL:"озеро",more:"подробнее ›",route:"Откуда и куда",link:"Связь с реками",hist:"История названия",facts:"Интересные факты",
  close:"Закрыть",other:"по-белорусски: ",g_main:"Главные реки",g_minor:"Притоки",g_lake:"Озёра",g_auto:"Малые реки",
  len:"Длина",inBY:"По Беларуси",basin:"Бассейн",q:"Расход в устье",into:"Впадает в",left:"левый приток",right:"правый приток",
  noteCur:"Цифры сверены с «Блакітнай кнігай Беларусі» (1994). Версии происхождения названий взяты из других источников: в этой книге их нет.",
  noteBook:"Длина, бассейн и расход — по «Блакітнай кнізе Беларусі» (1994). Устье определено по OpenStreetMap.",
  noteOsm:"Длина и устье посчитаны автоматически по данным OpenStreetMap; в «Блакітнай кнізе Беларусі» эту реку найти не удалось."},
 be:{doc:"Воды Беларусі",title:"Воды <b>Беларусі</b>",hint:"Круціце макет. Націсніце на шпільку, потым на назву.",refill:"Напоўніць",home:"Увесь макет",
  search:"Знайсці раку або возера",searchAria:"Пошук па назве",list:"Рэкі і азёры",canvas:"Гранёны макет Беларусі з рэкамі і азёрамі",
  river:"Рака",lake:"Возера",riverL:"рака",lakeL:"возера",more:"падрабязней ›",route:"Адкуль і куды",link:"Сувязь з рэкамі",hist:"Гісторыя назвы",facts:"Цікавыя факты",
  close:"Закрыць",other:"па-руску: ",g_main:"Галоўныя рэкі",g_minor:"Прытокі",g_lake:"Азёры",g_auto:"Малыя рэкі",
  len:"Даўжыня",inBY:"Па Беларусі",basin:"Басейн",q:"Расход у вусці",into:"Упадае ў",left:"левы прыток",right:"правы прыток",
  noteCur:"Лічбы звераны з «Блакітнай кнігай Беларусі» (1994). Версіі паходжання назваў узятыя з іншых крыніц: у гэтай кнізе іх няма.",
  noteBook:"Даўжыня, басейн і расход — па «Блакітнай кнізе Беларусі» (1994). Вусце вызначана па OpenStreetMap.",
  noteOsm:"Даўжыня і вусце падлічаны аўтаматычна па даных OpenStreetMap; у «Блакітнай кнізе Беларусі» гэтую раку знайсці не ўдалося."}};
const tx=k=>TX[LANG][k];
const CITY_BE={"Минск":"Мінск","Гомель":"Гомель","Витебск":"Віцебск","Гродно":"Гродна","Могилёв":"Магілёў","Брест":"Брэст","Бобруйск":"Бабруйск","Барановичи":"Баранавічы","Борисов":"Барысаў","Пинск":"Пінск","Солигорск":"Салігорск","Орша":"Орша","Мозырь":"Мазыр","Лида":"Ліда","Новополоцк":"Наваполацк","Молодечно":"Маладзечна","Полоцк":"Полацк","Жлобин":"Жлобін","Жодино":"Жодзіна","Речица":"Рэчыца","Слуцк":"Слуцк","Светлогорск":"Светлагорск","Кобрин":"Кобрын","Слоним":"Слонім","Волковыск":"Ваўкавыск","Сморгонь":"Смаргонь","Калинковичи":"Калінкавічы","Горки":"Горкі","Рогачёв":"Рагачоў","Новогрудок":"Навагрудак","Осиповичи":"Асіповічы","Берёза":"Бяроза","Дзержинск":"Дзяржынск","Вилейка":"Вілейка","Кричев":"Крычаў","Лунинец":"Лунінец","Ивацевичи":"Івацэвічы","Марьина Горка":"Мар'іна Горка"};
const plain=n=>n.replace(" (река)","").replace(/ \\(.*\\)$/,"");
function dname(n){const c=CARDS[n];return LANG==="be"&&c&&c.be&&c.be!=="—"?c.be:plain(n)}
function listName(n){if(LANG!=="be")return n.replace(" (река)","");const c=CARDS[n],m=n.match(/ \\(приток: (.*)\\)$/);return dname(n)+(m?" (прыток: "+((c&&c.mouthBe)||m[1])+")":"")}''')

# ---------- bubble and city labels
cut('function openBubble(n){', '<span class="bm">подробнее ›</span>`;bubble.hidden=false}',
    'function openBubble(n){bubbleFor=n;const it=items[n];bubble.innerHTML=`<span class="bk">${it.type==="lake"?tx("lakeL"):tx("riverL")}</span><span class="bn">${dname(n)}</span><span class="bm">${tx("more")}</span>`;bubble.hidden=false}')
R('for(const [n,x,z,r] of L.cities){const el=document.createElement("div");el.className="city"+(r===2?" small":r===3?" tiny":"");el.textContent=n;labelsEl.appendChild(el);labels.push({el,r,pos:',
  'for(const [n,x,z,r] of L.cities){const el=document.createElement("div");el.className="city"+(r===2?" small":r===3?" tiny":"");el.textContent=LANG==="be"?(CITY_BE[n]||n):n;labelsEl.appendChild(el);labels.push({el,r,n,pos:')

# ---------- list
cut('const list=document.getElementById("list"),card=document.getElementById("card"),chips={};', 'g.h.hidden=!any}});', '''const list=document.getElementById("list"),listBody=document.getElementById("listBody"),listToggle=document.getElementById("listToggle"),card=document.getElementById("card"),chips={};
const narrow=matchMedia("(max-width:760px)").matches;
const search=document.createElement("input");search.type="search";search.id="search";
const openGroups={main:true,minor:false,lake:true,auto:false};let groups=[];
function buildList(){listBody.textContent="";listBody.appendChild(search);groups=[];for(const k of Object.keys(chips))delete chips[k];
  search.placeholder=tx("search");search.setAttribute("aria-label",tx("searchAria"));
  for(const [key,type] of [["main","river"],["minor","river"],["lake","lake"],["auto","river"]]){
    const ents=Object.entries(CARDS).filter(([n,c])=>c.type===type&&items[n]&&(type==="lake"||(key==="main"?!c.minor:key==="minor"?(c.minor&&!c.auto):c.auto)));
    if(!ents.length)continue;
    if(key==="minor"||key==="auto")ents.sort((a,b)=>listName(a[0]).localeCompare(listName(b[0]),LANG));
    const h=document.createElement("button");h.className="grp";h.innerHTML=`<span>${tx("g_"+key)}</span><small>${ents.length}</small><i></i>`;
    h.onclick=()=>{openGroups[key]=!openGroups[key];filter()};listBody.appendChild(h);const g={key,h,chips:[]};groups.push(g);
    for(const [n,c] of ents){const b=document.createElement("button");b.className="chip "+type+(c.minor?" minor":"");b.setAttribute("aria-pressed",String(n===selected));
      b.innerHTML=`<i></i>${listName(n)}`;b.dataset.q=(n+" "+(c.be||"")).toLowerCase();
      b.onclick=()=>{select(n,true);if(narrow)setListOpen(false)};listBody.appendChild(b);chips[n]=b;g.chips.push([n,b])}}
  filter()}
function filter(){const q=search.value.trim().toLowerCase();
  for(const g of groups){let any=false;for(const [n,b] of g.chips){const hit=!q||b.dataset.q.includes(q);b.hidden=!(hit&&(q||openGroups[g.key]));any=any||hit}
    g.h.hidden=!any;g.h.setAttribute("aria-expanded",String(!!q||openGroups[g.key]))}}
search.addEventListener("input",filter);
function setListOpen(o){list.classList.toggle("collapsed",!o);listToggle.setAttribute("aria-expanded",String(o))}
listToggle.onclick=()=>setListOpen(list.classList.contains("collapsed"));''')

# ---------- card
cut('  const c=CARDS[n],lake=c.type==="lake";', '<div class="note">${c.auto?"Длина и устье посчитаны автоматически по данным OpenStreetMap.":"Прототип: цифры округлены, перед публикацией их нужно сверить со справочниками."}</div>`;',
    '  const c=CARDS[n],lake=c.type==="lake";renderCard(n);')
R('function select(n,doFly){', '''function renderCard(n){const c=CARDS[n],lake=c.type==="lake",be=LANG==="be",cb=be&&typeof CARDS_BE!=="undefined"&&CARDS_BE[n];
  let stats=cb?cb.stats:c.stats,from=cb?cb.from:c.from,to=cb?cb.to:c.to,hist=cb?cb.name:c.name,facts=cb?cb.facts:c.facts,note=tx("noteCur");
  if(c.auto){const num=v=>String(v).replace(".",",");stats=[[tx("len"),(c.book?"":"≈ ")+num(c.km)+" км"]];
    if(!c.book)stats.push([tx("inBY"),"≈ "+c.kin+" км"]);if(c.basin)stats.push([tx("basin"),c.basin+" км²"]);if(c.q)stats.push([tx("q"),c.q+" м³/с"]);
    const mo=be?c.mouthBe:c.mouth;if(mo)stats.push([tx("into"),mo+(c.side?` <small>(${tx(c.side==="левы"?"left":"right")})</small>`:"")]);
    from=["",""];to=["",""];hist="";facts=[];note=c.book?tx("noteBook"):tx("noteOsm")}
  const other=be?plain(n):(c.be&&c.be!=="—"?c.be:"");
  card.innerHTML=`<button class="close" id="close" aria-label="${tx("close")}">×</button><div class="kind">${lake?tx("lake"):tx("river")}</div><h2>${dname(n)}</h2>${other?`<div class="be">${tx("other")}${other}</div>`:""}
  <dl class="stats">${stats.map(([k,v])=>`<div><dt>${k}</dt><dd>${v}</dd></div>`).join("")}</dl>
  ${from[0]?`<h3>${lake?tx("link"):tx("route")}</h3><div class="route"><span class="dot"></span><span><b>${from[0]}</b><small>${from[1]}</small></span><span class="ln"></span><span></span><span class="dot end"></span><span><b>${to[0]}</b><small>${to[1]}</small></span></div>`:""}
  ${hist?`<h3>${tx("hist")}</h3><p>${hist}</p>`:""}${facts.length?`<h3>${tx("facts")}</h3><ul>${facts.map(f=>`<li>${f}</li>`).join("")}</ul>`:""}
  <div class="note">${note}</div>`;
  document.getElementById("close").onclick=()=>select(null)}
function applyLang(l){LANG=l;try{localStorage.setItem("lang",l)}catch(e){}
  document.documentElement.lang=l;document.title=tx("doc");document.getElementById("title").innerHTML=tx("title");document.getElementById("hint").textContent=tx("hint");
  document.getElementById("refill").textContent=tx("refill");document.getElementById("home").textContent=tx("home");document.getElementById("listLabel").textContent=tx("list");
  list.setAttribute("aria-label",tx("list"));document.getElementById("c").setAttribute("aria-label",tx("canvas"));
  for(const b of document.querySelectorAll(".lang button"))b.setAttribute("aria-pressed",String(b.dataset.l===l));
  for(const lb of labels)lb.el.textContent=l==="be"?(CITY_BE[lb.n]||lb.n):lb.n;
  buildList();if(bubbleFor)openBubble(bubbleFor);if(selected)renderCard(selected)}
for(const b of document.querySelectorAll(".lang button"))b.onclick=()=>applyLang(b.dataset.l);
function select(n,doFly){''')
R('  card.classList.remove("hide");document.getElementById("close").onclick=()=>select(null);', '  card.classList.remove("hide");')
R('document.getElementById("home").onclick=', 'applyLang(LANG);\ndocument.getElementById("home").onclick=')
open(p, "w", encoding="utf8").write(s); print("patched")
