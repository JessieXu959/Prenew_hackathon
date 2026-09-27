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
export function localizedQuery(config){return quote(terms[config.language]?.[config.goal==='sellers'?5:Math.max(0,niches.indexOf(config.niche))]||terms.en[0])}
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
export function viewSummary(c){
 if(c.sourceType==='live'&&c.recentViewStats)return c.recentViewStats;
 return {average:null,windowDays:null,sampleSize:0,checkedAt:null,videoIds:[],status:'insufficient',sampleLimited:false,
  method:c.sourceType==='imported'?'A single imported example is not a measured 30/90-day average.':c.sourceType==='live'?'Refresh this older API snapshot to measure recent uploads.':'Fictional demo metrics are not measured averages.'};
}
const languageCode=value=>{const text=String(value||'').toLowerCase();return Object.entries(languages).find(([,name])=>name.toLowerCase()===text)?.[0]||text.split('-')[0]};
export function languageStatus(c,language){
 const videos=c.sourceType==='live'?(c.videos||[]).filter(v=>v.recentUpload&&(!v.broadcastStatus||v.broadcastStatus==='none')).sort((a,b)=>String(b.publishedAt).localeCompare(String(a.publishedAt))).slice(0,5):(c.videos||[]);
 const hints=videos.flatMap(v=>[v.audioLanguage,v.metadataLanguage,...(!v.audioLanguage&&!v.metadataLanguage?[v.language]:[])]).filter(Boolean);
 if(c.language)hints.push(c.language);
 const codes=hints.map(languageCode),conflict=codes.some(code=>code!==language);
 const positive=videos.filter(v=>[v.audioLanguage,v.metadataLanguage,v.language].filter(Boolean).some(tag=>languageCode(tag)===language)).length;
 const accepted=!conflict&&(c.sourceType==='live'?videos.length>=3&&positive>=2:positive>=1||languageCode(c.language)===language);
 return {accepted,conflict,positive,sampleSize:videos.length,hints:[...new Set(hints)],value:accepted?100:conflict?0:null};
}
const contentLabels={
 'Counter-Strike / CS2':['counter-strike','counter strike','cs2$','csgo$'],Fortnite:['fortnite'],Minecraft:['minecraft'],Valorant:['valorant'],
 'League of Legends':['league of legends','leagueoflegends'], 'PC hardware / GPUs':['gpu$','grafikk','näytönohj','rtx','radeon','geforce'],
 'PC hardware / CPUs':['cpu$','ryzen','intel'], 'PC hardware / memory':['ram$','ddr4','ddr5'],
 'PC gaming':['gaming pc','pc gaming','pelikone','pelitieto','speldator']
};
function topicVideos(c){
 const at=Date.parse(c.fetchedAt);return (c.videos||[]).filter(v=>c.sourceType!=='live'||v.recentUpload&&Number.isFinite(Date.parse(v.publishedAt))&&Date.parse(v.publishedAt)<=at&&Date.parse(v.publishedAt)>=at-90*86400000);
 }
export function nicheEvidence(c){
 const videos=topicVideos(c);
 return Object.entries({...keywordGroups,...contentLabels}).map(([label,words])=>({label,videos:videos.filter(v=>matchesKeywords(v.title,words))})).filter(x=>x.videos.length);
}
export function nicheLabel(c){return nicheEvidence(c).map(x=>x.label).join(', ')||c.topic||'Unknown'}
export function countryName(c){return markets[c.country]||c.country||'Unknown'}
export function countrySource(c){return c.countrySource||(c.sourceType==='imported'&&c.country?'CSV uploader claim':'Unknown')}
export function contentLanguage(c){return languages[c.contentLanguage]||c.contentLanguage||languages[languageCode(c.language)]||c.language||'Unknown'}
export function viewWindowLabel(c){const v=viewSummary(c);return v.windowDays?`${v.windowDays}-day publication window${v.windowDays===90?' (fallback)':''} · ${v.sampleSize} videos${v.status==='insufficient'?' · Insufficient sample (minimum 3)':''}${v.sampleLimited?' · Latest 50 uploads only':''}${v.missingViewCount?' · '+v.missingViewCount+' missing view counts':''}`:v.method}
export function evidence(c,config,weights=defaultWeights,at=Date.now()){
 const videos=topicVideos(c), words=[...keywordGroups[config.niche]||keywordGroups.Gaming,...(config.goal==='sellers'?sellerWords:[])];
 const relevant=videos.filter(v=>matchesKeywords(v.title+' '+(v.description||''),words));
 const language=languageStatus(c,config.language),hints=language.hints;
 const dates=videos.map(v=>Date.parse(v.publishedAt)).filter(Number.isFinite), newest=dates.length?Math.max(...dates):null;
 const age=newest===null?null:Math.max(0,Math.floor((at-newest)/86400000));
 const avg=viewSummary(c).average;
 const ratios=videos.filter(v=>v.views>0&&v.likes!=null&&v.comments!=null).map(v=>(v.likes+v.comments)/v.views*100);
 const rate=ratios.length?ratios.reduce((a,b)=>a+b,0)/ratios.length:null;
 const factors={topic:videos.length?Math.round(relevant.length/videos.length*100):null,language:language.value,
 recency:age===null?null:age<=30?100:age<=90?70:age<=180?40:10,
 views:avg!==null&&c.followers>0?Math.min(100,Math.round(avg/c.followers*100)):null,
 engagement:rate===null?null:Math.min(100,Math.round(rate*20))};
 let total=0,denominator=0;for(const k in factors){if(k!=='language'&&factors[k]!==null){total+=factors[k]*weights[k];denominator+=weights[k]}}
 return {total:videos.length,factors,score:denominator?Math.round(total/denominator):null,known:Object.values(factors).filter(v=>v!==null).length,relevant,age,avg,rate,engagementSamples:ratios.length,languageHints:[...new Set(hints)]};
}
export function unknowns(c){return [...(contentLanguage(c)==='Unknown'?['Content language unknown']:[]),...(nicheLabel(c)==='Unknown'?['Niche / game evidence missing']:[]),...(!c.country?['Channel / creator country unknown']:[]),...(!c.contact?['No public contact found']:[]),...(viewSummary(c).average===null?['Recent average views unknown / insufficient sample']:[]),...(viewSummary(c).sampleLimited?['View sample capped at latest 50 uploads']:[]),c.audienceCountry&&c.audienceSource?'Audience geography: uploader evidence supplied; not independently verified':'Audience geography unverified','Audience age and demographics unknown','Fee, availability and collaboration interest unknown','Content honesty and sponsorship conflicts require manual review',...(c.followers==null?['Channel size unknown']:[]),...(!(c.videos||[]).length?['Recent video evidence missing']:[])];}
export function fitReason(c,config,e){return `${e.relevant.length}/${e.total} recent evidence videos contain ${config.goal==='sellers'?'niche or upgrade/resale':'niche'} keywords. ${e.languageHints.length?'Language metadata: '+e.languageHints.join(', ')+'.':'Language unverified; search language is only a hint.'} ${e.age===null?'Posting recency unknown.':'Latest supplied upload: '+e.age+' days ago.'}`}
export function angle(c,config){return config.goal==='sellers'?'An old-rig audit: inspect condition and components, document testing, then compare keeping, upgrading and selling. Confirm Prenew’s actual acceptance criteria and selling process; do not promise a payout.':'An honest refurbished-PC test: inspect condition, explain testing and measured game performance, compare total value, and ask what the warranty actually covers. Confirm exact specifications, prices and warranty terms with Prenew before recording.';}
export function csvCell(value){let s=String(value??'');if(/^[\s]*[=+@-]/.test(s))s="'"+s;return '"'+s.replaceAll('"','""')+'"';}
export function shortlistCSV(entries,config,weights){
 const headers=['name','platform','source_type','source_url','provenance','fetched_or_imported_at','discovery_market','search_language','query','country','country_source','content_language','language_evidence','language_evidence_urls','verified_audience_country','audience_claim','audience_claim_source','subscribers_followers','recent_average_views','views_window_days','views_sample_size','views_window_start','views_window_end','views_last_checked','views_status','views_sample_limited','views_missing_counts','views_method','views_video_urls','views_video_counts','niche_game_hardware','niche_evidence_urls','public_contact','contact_type','contact_source','review','notes','scoring_niche','scoring_goal','scoring_language','scoring_weights','score','topic_score','language_score','recency_score','views_score','engagement_score','known_factors','evidence_urls','evidence_titles','evidence_dates','missing_data_flags','collaboration_angle','outreach_status'];
 const lines=entries.map(({creator:c,pipeline:p})=>{
  const e=evidence(c,config,weights),v=viewSummary(c),sample=(c.videos||[]).filter(video=>v.videoIds.includes(video.id)),niches=nicheEvidence(c);
  const languageEvidence=c.languageEvidence?`${c.languageEvidence.positiveVideos}/${c.languageEvidence.sampleSize} recent videos match; ${c.languageEvidence.method} ${(c.languageEvidence.videos||[]).map(video=>`${video.videoId}: audio=${video.audioLanguage||'Unknown'}, metadata=${video.metadataLanguage||'Unknown'}`).join(' | ')}`:c.sourceType==='imported'?'Uploader-supplied language; unverified':'Unknown';
  return [c.name,c.platform,c.sourceType||'demo',c.sourceUrl||'Unknown',c.source,c.fetchedAt||'Unknown',markets[c.market]||c.market||'Unknown',c.searchLanguage||'Unknown',c.query||'',countryName(c),countrySource(c),contentLanguage(c),languageEvidence,(c.languageEvidence?.videos||[]).map(x=>x.url).join(' | ')||'Unknown','Unknown',c.audienceCountry||'Unknown',c.audienceSource||'Unknown',c.followers??'Unknown',v.average??'Unknown',v.windowDays??'Unknown',v.sampleSize,v.windowStart||'Unknown',v.windowEnd||'Unknown',v.checkedAt||'Unknown',v.status,v.sampleLimited,v.missingViewCount??'Unknown',v.method,sample.map(x=>x.url).join(' | '),sample.map(x=>x.views).join(' | '),nicheLabel(c),[...new Set(niches.flatMap(x=>x.videos.map(video=>video.url)))].join(' | '),c.contact?.value||'No public contact found',c.contact?.kind||'Unknown',c.contact?.sourceUrl||'Unknown',p.review||'Unreviewed',p.notes||'',config.niche,config.goal,config.language,JSON.stringify(weights),e.score,...Object.values(e.factors),e.known,(c.videos||[]).map(x=>x.url).join(' | '),(c.videos||[]).map(x=>x.title).join(' | '),(c.videos||[]).map(x=>x.publishedAt||'Unknown').join(' | '),unknowns(c).join('; '),angle(c,config),p.status].map(csvCell).join(',');
 });
 return '\ufeff'+[headers.map(csvCell).join(','),...lines].join('\r\n');
}

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
 const views=viewSummary(c);
 return {views:{value:views.average,count:views.sampleSize},likes:average('likes'),comments:average('comments'),engagement,engagementSamples:samples.length,keywords:[...keywords].sort(),themes,total:videos.length};
}
