export const markets={FI:'Finland',DE:'Germany',FR:'France',NL:'Netherlands',SE:'Sweden',GB:'United Kingdom'};
export const languages={fi:'Finnish',de:'German',fr:'French',nl:'Dutch',sv:'Swedish',en:'English'};
export const defaults={FI:'fi',DE:'de',FR:'fr',NL:'nl',SE:'sv',GB:'en'};
export const niches=['Budget gaming','PC building','Refurbished tech','PC performance','Gaming'];
const terms={
 fi:['halpa pelikone | budjetti pelitietokone','pelikoneen kasaus | tietokoneen rakentaminen','käytetty pelikone | kunnostettu tietokone','pelikone testi | näytönohjain vertailu','pelikone | PC pelaaminen','vanhan tietokoneen myynti | pelikone päivitys'],
 de:['günstiger Gaming PC | Budget Gaming PC','Gaming PC zusammenbauen | PC Eigenbau','gebrauchter Gaming PC | generalüberholter PC','Gaming PC Test | Grafikkarten Vergleich','Gaming PC | PC Spiele','alten PC verkaufen | Gaming PC aufrüsten'],
 fr:['PC gamer pas cher | PC gaming petit budget','monter un PC gamer | assemblage PC','PC gamer reconditionné | PC occasion','test PC gamer | comparatif carte graphique','PC gamer | jeux PC','vendre son PC | améliorer PC'],
 nl:['goedkope game pc | budget gaming pc','game pc bouwen | computer samenstellen','refurbished gaming pc | tweedehands computer','gaming pc test | videokaart vergelijking','game pc | pc gaming','oude pc verkopen | pc upgraden'],
 sv:['billig speldator | budget gaming dator','bygga speldator | datorbygge','begagnad speldator | rekonditionerad dator','speldator test | grafikkort jämförelse','speldator | PC spel','sälja gammal dator | uppgradera dator'],
 en:['budget gaming PC | cheap gaming computer','PC building | gaming PC build','refurbished gaming PC | used gaming computer','gaming PC benchmark | GPU comparison','gaming PC | PC gaming','sell old PC | gaming PC upgrade']};
// YouTube's | operator binds single words, so multi-word alternatives are quoted as phrases.
const quote=t=>t.split('|').map(x=>x.trim()).map(x=>x.includes(' ')?'"'+x+'"':x).join(' | ');
const channelTerms={fi:'pelikone | tietokone | tietotekniikka | PC pelaaminen',de:'Gaming PC | PC Hardware | Computer Technik',fr:'PC gamer | informatique | materiel PC',nl:'game pc | computer hardware | computer bouwen',sv:'speldator | datorbygge | datorteknik',en:'gaming PC | PC hardware | computer reviews'};
export function localizedQuery(config){if(config.mode==='channel')return quote(channelTerms[config.language]||channelTerms.en);return quote(terms[config.language]?.[config.goal==='sellers'?5:Math.max(0,niches.indexOf(config.niche))]||terms.en[0])}
// Stems match at the start of a word; stems of 7+ letters also match inside compounds (budjettipelikone);
// a trailing $ requires the whole word.
const keywordGroups={
 'Budget gaming':['budget','cheap','halpa','halv','budjet','günstig','pas cher','goedkop','goedkoop','billig','value'],
 'PC building':['build','kasau','kasat','kasas','rakenta','zusammenbau','eigenbau','assembl','monter','bouwen','samenstel','bygga','bygge'],
 'Refurbished tech':['refurb','used$','second hand','secondhand','käytet','kunnoste','gebraucht','generalüberholt','recondition','occasion$','tweedehands','begagnad','rekondition'],
 'PC performance':['benchmark','fps','performance','test','vertailu','vergleich','compar','jämför','prestanda','leistung'],
 'Gaming':['gaming','gamer','pelikone','pelitieto','pelaami','speldator','game pc','pc spiel']};
const sellerWords=['sell$','sells$','selling','seller','myynt','myyd','verkauf','verkaufen','vendre','verkop','sälja','upgrad','päivit','aufrüst'];
const matchers=new Map();
function matcher(word){if(!matchers.has(word)){const whole=word.endsWith('$'),stem=whole?word.slice(0,-1):word,esc=stem.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
 matchers.set(word,new RegExp((whole||stem.length<7?'(?<![\\p{L}\\p{N}])':'')+esc+(whole?'(?![\\p{L}\\p{N}])':''),'u'))}return matchers.get(word)}
export function matchesKeywords(text,words){const t=String(text||'').toLowerCase();return words.some(w=>matcher(w).test(t))}
export const factorLabels={topic:'Recent topic relevance',language:'Language clues',recency:'Posting recency',views:'Views relative to size',engagement:'Public engagement'};
export const defaultWeights={topic:40,language:0,recency:15,views:15,engagement:10};
export function evidence(c,config,weights=defaultWeights,at=Date.now()){
 const videos=c.videos||[], words=[...keywordGroups[config.niche]||keywordGroups.Gaming,...(config.goal==='sellers'?sellerWords:[])];
 const relevant=videos.filter(v=>matchesKeywords(v.title+' '+(v.description||''),words));
 const hints=videos.map(v=>v.language).filter(Boolean);if(c.language)hints.push(c.language);
 const languageMatch=hints.some(x=>x.toLowerCase().split('-')[0]===config.language||x.toLowerCase()===languages[config.language]?.toLowerCase());
 const dates=videos.map(v=>Date.parse(v.publishedAt)).filter(Number.isFinite), newest=dates.length?Math.max(...dates):null;
 const age=newest===null?null:Math.max(0,Math.floor((at-newest)/86400000));
 const views=videos.map(v=>v.views).filter(v=>v!==null&&v!==undefined),avg=views.length?views.reduce((a,b)=>a+b,0)/views.length:null;
 const ratios=videos.filter(v=>v.views>0&&v.likes!=null&&v.comments!=null).map(v=>(v.likes+v.comments)/v.views*100);
 const rate=ratios.length?ratios.reduce((a,b)=>a+b,0)/ratios.length:null;
 const factors={topic:videos.length?Math.round(relevant.length/videos.length*100):null,language:hints.length?(languageMatch?100:0):null,
 recency:age===null?null:age<=30?100:age<=90?70:age<=180?40:10,
 views:avg!==null&&c.followers>0?Math.min(100,Math.round(avg/c.followers*100)):null,
 engagement:rate===null?null:Math.min(100,Math.round(rate*20))};
 let total=0,denominator=0;for(const k in factors){if(k!=='language'&&factors[k]!==null){total+=factors[k]*weights[k];denominator+=weights[k]}}
 return {factors,score:denominator?Math.round(total/denominator):null,known:Object.values(factors).filter(v=>v!==null).length,relevant,age,avg,rate,engagementSamples:ratios.length,languageHints:[...new Set(hints)]};
}
export function unknowns(c){return [c.audienceCountry&&c.audienceSource?'Audience geography: uploader evidence supplied; not independently verified':'Audience geography unverified','Audience age and demographics unknown','Fee, availability and collaboration interest unknown','Content honesty and sponsorship conflicts require manual review',...(c.followers==null?['Channel size unknown']:[]),...(!(c.videos||[]).length?['Recent video evidence missing']:[])];}
export function fitReason(c,config,e){return `${e.relevant.length}/${(c.videos||[]).length} supplied recent videos contain ${config.goal==='sellers'?'niche or upgrade/resale':'niche'} keywords. ${e.languageHints.length?'Language metadata: '+e.languageHints.join(', ')+'.':'Language unverified; search language is only a hint.'} ${e.age===null?'Posting recency unknown.':'Latest supplied upload: '+e.age+' days ago.'}`}
export function angle(c,config){return config.goal==='sellers'?'An old-rig audit: inspect condition and components, document testing, then compare keeping, upgrading and selling. Confirm Prenew’s actual acceptance criteria and selling process; do not promise a payout.':'An honest refurbished-PC test: inspect condition, explain testing and measured game performance, compare total value, and ask what the warranty actually covers. Confirm exact specifications, prices and warranty terms with Prenew before recording.';}
export function csvCell(value){let s=String(value??'');if(/^[\s]*[=+@-]/.test(s))s="'"+s;return '"'+s.replaceAll('"','""')+'"';}
export function shortlistCSV(entries,config,weights){const headers=['name','platform','source_type','source_url','provenance','fetched_or_imported_at','discovery_market','search_language','query','review','notes','scoring_niche','scoring_goal','scoring_language','scoring_weights','score','topic_score','language_score','recency_score','views_score','engagement_score','known_factors','evidence_urls','evidence_titles','evidence_dates','unknowns','collaboration_angle','outreach_status'];
const lines=entries.map(({creator:c,pipeline:p})=>{const e=evidence(c,config,weights);return [c.name,c.platform,c.sourceType||'demo',c.sourceUrl||'',c.source,c.fetchedAt,markets[c.market]||c.market||'',c.searchLanguage||c.language||'',c.query||'',p.review||'Unreviewed',p.notes||'',config.niche,config.goal,config.language,JSON.stringify(weights),e.score,...Object.values(e.factors),e.known,(c.videos||[]).map(v=>v.url).join(' | '),(c.videos||[]).map(v=>v.title).join(' | '),(c.videos||[]).map(v=>v.publishedAt||'Unknown').join(' | '),unknowns(c).join('; '),angle(c,config),p.status].map(csvCell).join(',')});return '\ufeff'+[headers.map(csvCell).join(','),...lines].join('\r\n');}

// Comparison uses observed metrics only; missing values never become zero.
export function comparisonMetrics(c){
 const videos=c.videos||[];
 const average=key=>{const values=videos.map(v=>v[key]).filter(v=>Number.isFinite(v)&&v>=0);return {value:values.length?values.reduce((a,b)=>a+b,0)/values.length:null,count:values.length}};
 const samples=videos.filter(v=>v.views>0&&Number.isFinite(v.likes)&&Number.isFinite(v.comments));
 const engagement=samples.length?samples.reduce((sum,v)=>sum+(v.likes+v.comments)/v.views*100,0)/samples.length:null;
 const groups={...keywordGroups,'Resale / upgrades':sellerWords};
 const keywords=new Set(),themes=[];
 for(const [theme,words] of Object.entries(groups)){
  let count=0;
  for(const v of videos){
   const text=(String(v.title||'')+' '+String(v.description||'')).toLowerCase();
   if(matchesKeywords(text,words))count++;
   for(const word of words){
    const match=text.match(matcher(word));if(!match)continue;
    let start=match.index,end=start+match[0].length;
    while(start>0&&/[\p{L}\p{N}]/u.test(text[start-1]))start--;
    while(end<text.length&&/[\p{L}\p{N}]/u.test(text[end]))end++;
    keywords.add(text.slice(start,end));
   }
  }
  if(count)themes.push(`${theme} (${count}/${videos.length} videos)`);
 }
 return {views:average('views'),likes:average('likes'),comments:average('comments'),engagement,engagementSamples:samples.length,keywords:[...keywords].sort(),themes,total:videos.length};
}
