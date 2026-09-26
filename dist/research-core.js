export const markets={FI:'Finland',DE:'Germany',FR:'France',NL:'Netherlands',SE:'Sweden',GB:'United Kingdom'};
export const languages={fi:'Finnish',de:'German',fr:'French',nl:'Dutch',sv:'Swedish',en:'English'};
export const defaults={FI:'fi',DE:'de',FR:'fr',NL:'nl',SE:'sv',GB:'en'};
export const niches=['Budget gaming','PC building','Refurbished tech','PC performance','Gaming','Upgrading & reselling'];
// Five alternatives per niche, in niche order. Multi-word alternatives are quoted because YouTube's | binds single words.
// English loan phrases are included because many Nordic and Dutch creators title videos in English.
const terms={
 fi:['pelikone | budjettipelikone | "halpa pelikone" | "budjetti pelikone" | "budget gaming pc"',
  '"pelikoneen kasaus" | "tietokoneen kasaus" | "kasataan pelikone" | "pc build" | pelikone',
  '"käytetty pelikone" | "käytetty tietokone" | "kunnostettu tietokone" | "pelikone torista" | "refurbished pc"',
  'näytönohjain | "näytönohjain testi" | "pelikone testi" | "fps testi" | benchmark',
  'pelikone | pelitietokone | "pc pelit" | "pc gaming" | pelaaminen',
  '"vanha tietokone" | "tietokoneen päivitys" | "pelikoneen päivitys" | "näytönohjaimen vaihto" | "myy tietokone"'],
 sv:['"billig speldator" | "budget speldator" | "billig gamingdator" | speldator | "budget gaming pc"',
  '"bygga speldator" | "bygga dator" | datorbygge | "pc build" | speldator',
  '"begagnad speldator" | "begagnad dator" | "renoverad dator" | "blocket dator" | "refurbished pc"',
  'grafikkort | "grafikkort test" | "speldator test" | "fps test" | benchmark',
  'speldator | gamingdator | "pc-spel" | "pc gaming" | gaming',
  '"sälja dator" | "uppgradera dator" | "uppgradera speldator" | "byta grafikkort" | "gammal dator"'],
 de:['"günstiger gaming pc" | "budget gaming pc" | "billiger gaming pc" | "gaming pc unter" | "preis-leistungs gaming pc"',
  '"gaming pc zusammenbauen" | "pc zusammenbauen" | "pc selber bauen" | "pc build" | eigenbau',
  '"gebrauchter gaming pc" | "gebrauchter pc" | "generalüberholter pc" | "kleinanzeigen pc" | "refurbished pc"',
  '"grafikkarte test" | "gaming pc test" | "grafikkarten vergleich" | "fps test" | benchmark',
  '"gaming pc" | "pc gaming" | "pc spiele" | zocken | gaming',
  '"alten pc verkaufen" | "pc aufrüsten" | "gaming pc aufrüsten" | "grafikkarte tauschen" | "pc upgrade"'],
 fr:['"pc gamer pas cher" | "pc gamer petit budget" | "pc gaming budget" | "config pc gamer" | "budget gaming pc"',
  '"monter son pc" | "montage pc" | "monter un pc gamer" | "config pc" | "pc build"',
  '"pc gamer reconditionné" | "pc reconditionné" | "pc gamer occasion" | "pc occasion" | "leboncoin pc"',
  '"test carte graphique" | "test pc gamer" | "comparatif carte graphique" | "test fps" | benchmark',
  '"pc gamer" | "jeux pc" | "pc gaming" | gamer | gaming',
  '"vendre son pc" | "améliorer son pc" | "changer carte graphique" | "vieux pc" | "upgrade pc"'],
 nl:['"goedkope game pc" | "budget game pc" | "goedkope gaming pc" | "budget gaming pc" | "game pc kopen"',
  '"game pc bouwen" | "pc bouwen" | "zelf pc bouwen" | "computer samenstellen" | "pc build"',
  '"tweedehands game pc" | "tweedehands pc" | "marktplaats pc" | "refurbished gaming pc" | "refurbished pc"',
  '"videokaart test" | "gaming pc test" | "videokaart vergelijking" | "fps test" | benchmark',
  '"game pc" | "gaming pc" | "pc gaming" | gamen | gaming',
  '"oude pc verkopen" | "pc upgraden" | "game pc upgraden" | "videokaart vervangen" | "pc upgrade"'],
 en:['"budget gaming pc" | "cheap gaming pc" | "gaming pc under" | "budget pc build" | "best value gaming pc"',
  '"pc build" | "gaming pc build" | "building a pc" | "how to build a pc" | "pc build guide"',
  '"refurbished gaming pc" | "used gaming pc" | "second hand gaming pc" | "refurbished pc" | "used pc"',
  '"gaming pc benchmark" | "gpu benchmark" | "gpu comparison" | "fps test" | "graphics card review"',
  '"gaming pc" | "pc gaming" | "gaming setup" | "pc games" | gaming',
  '"sell old pc" | "gaming pc upgrade" | "upgrade old pc" | "gpu upgrade" | "pc upgrade"']};
export function localizedQuery(config){return terms[config.language]?.[Math.max(0,niches.indexOf(config.niche))]||terms.en[0]}
// Stems match at the start of a word; stems of 7+ letters also match inside compounds (budjettipelikone);
// a trailing $ requires the whole word.
const hardware=['gpu$','rtx','radeon','geforce','näytönohjain','grafikkort','grafikkarte','carte graphique','videokaart','graphics card','prebuilt'];
const keywordGroups={
 'Budget gaming':['budget','cheap','halpa','halv','budjet','günstig','pas cher','petit budget','goedkop','goedkoop','billig','value'],
 'PC building':['build','kasau','kasat','kasas','kasaan pelikone','rakenta','zusammenbau','selber bauen','eigenbau','assembl','monter','montage','bouwen','samenstel','bygga','bygge','datorbygg'],
 'Refurbished tech':['refurb','used$','second hand','secondhand','käytet','kunnoste','torista','gebraucht','generalüberholt','kleinanzeigen','recondition','reconditionné','occasion$','leboncoin','tweedehands','marktplaats','begagnad','renover','rekondition','blocket'],
 'PC performance':['benchmark','fps','performance','test','vertailu','vergleich','compar','jämför','prestanda','leistung','vergelijk',...hardware],
 'Gaming':['gaming','gamer','pelikone','pelitieto','pelaa','peli','speldator','gamingdator','spel$','pc-spel','game pc','pc spiel','zock','jeux','gamen','pc game',...hardware],
 'Upgrading & reselling':['sell$','sells$','selling','seller','myynt','myyd','myy$','verkauf','verkaufen','vendre','verkop','sälja','säljer','upgrad','uppgrad','päivit','aufrüst','améliorer','byta grafikkort','näytönohjaimen vaihto','grafikkarte tauschen','videokaart vervangen']};
const matchers=new Map();
function matcher(word){if(!matchers.has(word)){const whole=word.endsWith('$'),stem=whole?word.slice(0,-1):word,esc=stem.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
 matchers.set(word,new RegExp((whole||stem.length<7?'(?<![\\p{L}\\p{N}])':'')+esc+(whole?'(?![\\p{L}\\p{N}])':''),'u'))}return matchers.get(word)}
export function matchesKeywords(text,words){const t=String(text||'').toLowerCase();return words.some(w=>matcher(w).test(t))}
export const factorLabels={topic:'Recent topic relevance',reach:'Typical reach (avg. views)',language:'Language clues',recency:'Posting recency',views:'Views relative to size',engagement:'Public engagement'};
export const defaultWeights={topic:40,reach:30,language:10,recency:10,views:5,engagement:5};
export const minViewOptions={0:'Any',500:'500+',1000:'1,000+',5000:'5,000+',10000:'10,000+'};
export function evidence(c,config,weights=defaultWeights,at=Date.now()){
 const videos=c.videos||[], words=keywordGroups[config.niche]||keywordGroups.Gaming;
 const relevant=videos.filter(v=>matchesKeywords(v.title+' '+(v.description||''),words));
 const hints=videos.map(v=>v.language).filter(Boolean);if(c.language)hints.push(c.language);
 const languageMatch=hints.some(x=>x.toLowerCase().split('-')[0]===config.language||x.toLowerCase()===languages[config.language]?.toLowerCase());
 const dates=videos.map(v=>Date.parse(v.publishedAt)).filter(Number.isFinite), newest=dates.length?Math.max(...dates):null;
 const age=newest===null?null:Math.max(0,Math.floor((at-newest)/86400000));
 const views=videos.map(v=>v.views).filter(v=>v!==null&&v!==undefined),avg=views.length?views.reduce((a,b)=>a+b,0)/views.length:null;
 const ratios=videos.filter(v=>v.views>0&&v.likes!=null&&v.comments!=null).map(v=>(v.likes+v.comments)/v.views*100);
 const rate=ratios.length?ratios.reduce((a,b)=>a+b,0)/ratios.length:null;
 // Reach is log-scaled on average views: 100 → 0, 1k → 33, 10k → 67, 100k+ → 100.
 const factors={topic:videos.length?Math.round(relevant.length/videos.length*100):null,reach:avg===null?null:Math.round(Math.min(1,Math.max(0,(Math.log10(Math.max(avg,1))-2)/3))*100),language:hints.length?(languageMatch?100:0):null,
 recency:age===null?null:age<=30?100:age<=90?70:age<=180?40:10,
 views:avg!==null&&c.followers>0?Math.min(100,Math.round(avg/c.followers*100)):null,
 engagement:rate===null?null:Math.min(100,Math.round(rate*20))};
 let total=0,denominator=0;for(const k in factors){if(factors[k]!==null){total+=factors[k]*(weights[k]??0);denominator+=weights[k]??0}}
 return {factors,score:denominator?Math.round(total/denominator):null,known:Object.values(factors).filter(v=>v!==null).length,total:Object.keys(factors).length,relevant,age,avg,rate,engagementSamples:ratios.length,languageHints:[...new Set(hints)]};
}
export function unknowns(c){return [c.audienceCountry&&c.audienceSource?'Audience geography: uploader evidence supplied; not independently verified':'Audience geography unverified','Audience age and demographics unknown','Fee, availability and collaboration interest unknown','Content honesty and sponsorship conflicts require manual review',...(c.followers==null?['Channel size unknown']:[]),...(!(c.videos||[]).length?['Recent video evidence missing']:[])];}
export function fitReason(c,config,e){return `${e.relevant.length}/${(c.videos||[]).length} supplied recent videos contain ${config.niche} keywords. ${e.languageHints.length?'Language metadata: '+e.languageHints.join(', ')+'.':'Language unverified; search language is only a hint.'} ${e.age===null?'Posting recency unknown.':'Latest supplied upload: '+e.age+' days ago.'}`}
export function angle(c,config){return config.niche==='Upgrading & reselling'?'An old-rig audit: inspect condition and components, document testing, then compare keeping, upgrading and selling. Confirm Prenew’s actual acceptance criteria and selling process; do not promise a payout.':'An honest refurbished-PC test: inspect condition, explain testing and measured game performance, compare total value, and ask what the warranty actually covers. Confirm exact specifications, prices and warranty terms with Prenew before recording.';}
export function csvCell(value){let s=String(value??'');if(/^[\s]*[=+@-]/.test(s))s="'"+s;return '"'+s.replaceAll('"','""')+'"';}
export function shortlistCSV(entries,config,weights){const headers=['name','platform','source_type','source_url','provenance','fetched_or_imported_at','discovery_market','search_language','query','review','notes','scoring_niche','scoring_language','scoring_weights','score','topic_score','reach_score','language_score','recency_score','views_score','engagement_score','known_factors','evidence_urls','evidence_titles','evidence_dates','unknowns','collaboration_angle','outreach_status'];
const lines=entries.map(({creator:c,pipeline:p})=>{const e=evidence(c,config,weights);return [c.name,c.platform,c.sourceType||'demo',c.sourceUrl||'',c.source,c.fetchedAt,markets[c.market]||c.market||'',c.searchLanguage||c.language||'',c.query||'',p.review||'Unreviewed',p.notes||'',config.niche,config.language,JSON.stringify(weights),e.score,...Object.values(e.factors),e.known,(c.videos||[]).map(v=>v.url).join(' | '),(c.videos||[]).map(v=>v.title).join(' | '),(c.videos||[]).map(v=>v.publishedAt||'Unknown').join(' | '),unknowns(c).join('; '),angle(c,config),p.status].map(csvCell).join(',')});return '\ufeff'+[headers.map(csvCell).join(','),...lines].join('\r\n');}
