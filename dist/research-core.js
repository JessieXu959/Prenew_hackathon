export const markets={FI:'Finland',DE:'Germany',FR:'France',SE:'Sweden',GB:'United Kingdom',EE:'Estonia',HU:'Hungary'};
export const languages={fi:'Finnish',de:'German',fr:'French',sv:'Swedish',en:'English',et:'Estonian',hu:'Hungarian'};
export const defaults={FI:'fi',DE:'de',FR:'fr',SE:'sv',GB:'en',EE:'et',HU:'hu'};
export const niches=['Budget gaming','PC building','Refurbished tech','PC performance','Gaming'];
const terms={
 fi:['halpa pelikone | budjetti pelitietokone','pelikoneen kasaus | tietokoneen rakentaminen','käytetty pelikone | kunnostettu tietokone','pelikone testi | näytönohjain vertailu','pelikone | PC pelaaminen','vanhan tietokoneen myynti | pelikone päivitys'],
 de:['günstiger Gaming PC | Budget Gaming PC','Gaming PC zusammenbauen | PC Eigenbau','gebrauchter Gaming PC | generalüberholter PC','Gaming PC Test | Grafikkarten Vergleich','Gaming PC | PC Spiele','alten PC verkaufen | Gaming PC aufrüsten'],
 fr:['PC gamer pas cher | PC gaming petit budget','monter un PC gamer | assemblage PC','PC gamer reconditionné | PC occasion','test PC gamer | comparatif carte graphique','PC gamer | jeux PC','vendre son PC | améliorer PC'],
 sv:['billig speldator | budget gaming dator','bygga speldator | datorbygge','begagnad speldator | rekonditionerad dator','speldator test | grafikkort jämförelse','speldator | PC spel','sälja gammal dator | uppgradera dator'],
 en:['budget gaming PC | cheap gaming computer','PC building | gaming PC build','refurbished gaming PC | used gaming computer','gaming PC benchmark | GPU comparison','gaming PC | PC gaming','sell old PC | gaming PC upgrade'],
 et:['odav mänguriarvuti | soodne mänguarvuti','arvuti kokkupanek | mänguriarvuti ehitamine','kasutatud mänguriarvuti | taastatud arvuti','mänguriarvuti test | videokaardi võrdlus','mänguriarvuti | arvutimängud','arvuti müük | arvuti uuendamine'],
 hu:['olcsó gamer PC | olcsó játékos számítógép','PC építés | számítógép összeszerelés','használt gamer PC | felújított számítógép','gamer PC teszt | videokártya összehasonlítás','gamer PC | számítógépes játék','számítógép eladás | PC fejlesztés']
};
export function localizedQuery(config){return terms[config.language]?.[config.goal==='sellers'?5:Math.max(0,niches.indexOf(config.niche))]||terms.en[0]}
// Stems match at the start of a word; stems of 7+ letters also match inside compounds (budjettipelikone);
// a trailing $ requires the whole word.
const keywordGroups={
 'Budget gaming':['budget','cheap','halpa','halv','budjet','günstig','pas cher','goedkop','goedkoop','billig','value','odav','soodne','olcsó'],
 'PC building':['build','kasau','kasat','kasas','rakenta','zusammenbau','eigenbau','assembl','monter','bouwen','samenstel','bygga','bygge','kokkupan','ehitami','építés','összeszerel'],
 'Refurbished tech':['refurb','used$','second hand','secondhand','käytet','kunnoste','gebraucht','generalüberholt','recondition','occasion$','tweedehands','begagnad','rekondition','kasutatud','taastatud','használt','felújított'],
 'PC performance':['benchmark','fps','performance','test','vertailu','vergleich','compar','jämför','prestanda','leistung','võrdlus','teszt','összehasonl'],
 'Gaming':['gaming','gamer','pelikone','pelitieto','pelaami','speldator','game pc','pc spiel','mänguriarvuti','mänguarvuti','arvutimäng','számítógép']};
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
export function medianViews(c){
 const summary=viewSummary(c),sampleIds=new Set(summary.videoIds||[]);
 const values=(c.videos||[]).filter(video=>sampleIds.has(video.id)&&Number.isFinite(video.views)&&video.views>=0).map(video=>video.views).sort((a,b)=>a-b);
 if(summary.average===null||!summary.sampleSize||values.length!==summary.sampleSize)return null;
 const middle=Math.floor(values.length/2);
 return values.length%2?values[middle]:(values[middle-1]+values[middle])/2;
}
export function viewSubscriberRatio(c){
 const views=viewSummary(c).average,subscribers=c.followers;
 if(!Number.isFinite(views)||views<=0||!Number.isFinite(subscribers)||subscribers<=0)return {value:null,label:null,tone:'na',text:'Ratio: N/A'};
 const value=Math.round(views/subscribers*1000)/10;
 if(value>=20)return {value,label:'High Activity',tone:'high',text:`${value.toFixed(1)}% view ratio`};
 if(value>=8)return {value,label:'Healthy / Normal',tone:'healthy',text:`${value.toFixed(1)}% view ratio`};
 return {value,label:'Low Activity',tone:'low',text:`${value.toFixed(1)}% view ratio`};
}
const languageCode=value=>{const text=String(value||'').toLowerCase();return Object.entries(languages).find(([,name])=>name.toLowerCase()===text)?.[0]||text.split('-')[0]};
export function languageStatus(c,language){
 if(c.sourceType==='live'&&language!=='en'&&c.market_match_tier){
  const accepted=c.eligibility==='match';
  return {accepted,conflict:false,positive:accepted?1:0,sampleSize:(c.videos||[]).length,hints:[c.language_detected||'Unknown'],value:accepted?100:null};
 }
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
const prenewColumns=['Creator key','Market','Country','Creator / channel','Agency','Year-week','Platform','Niche / content','YT subscribers','YT views / video','TikTok followers','TikTok views / video'];
function isoWeek(date=new Date()){
 const day=new Date(Date.UTC(date.getUTCFullYear(),date.getUTCMonth(),date.getUTCDate()));
 day.setUTCDate(day.getUTCDate()+4-(day.getUTCDay()||7));
 const year=day.getUTCFullYear(),first=new Date(Date.UTC(year,0,1));
 return `${year}-${String(Math.ceil((((day-first)/86400000)+1)/7)).padStart(2,'0')}`;
}
function prenewOverview(c,config,views,p){
 const history=c.prenewHistory||[],last=c.prenewImport||{};
 const supplied=key=>[...history].reverse().map(row=>row[key]).find(value=>String(value??'').trim())||last[key]||null;
 const countryCodes=Object.fromEntries(Object.entries(markets).map(([code,name])=>[name.toLowerCase(),code]));
 const rawCountry=String(c.country||supplied('Country')||'').trim();
 const directCountry=markets[rawCountry.toUpperCase()]?rawCountry.toUpperCase():countryCodes[rawCountry.toLowerCase()];
 const explicitMarket=String(c.market||supplied('Market')||'').trim().toUpperCase();
 // Estonian and Hungarian are explicit single-market language selections in this app.
 const locale=String(c.contentLanguage||c.language||c.searchLanguage||'').toLowerCase().split('-')[0];
 const languageMarket=locale==='et'?'EE':locale==='hu'?'HU':null;
 const market=directCountry||(markets[explicitMarket]?explicitMarket:null)||languageMarket||'Unknown';
 const country=rawCountry?(markets[rawCountry.toUpperCase()]||rawCountry):(languageMarket?markets[languageMarket]:(markets[explicitMarket]||'Unknown'));
 const platform=String(c.platform||supplied('Platform')||'Unknown').trim();
 const hasYouTube=/youtube/i.test(platform),hasTikTok=/tiktok/i.test(platform);
 const formatted=value=>{if(value===null||value===undefined||value==='')return 'Unknown';const n=Number(String(value).replaceAll(',',''));return Number.isFinite(n)&&n>=0?new Intl.NumberFormat('en-US',{maximumFractionDigits:1}).format(n):String(value)};
 const platformValue=(key,metric)=>{const claim=supplied(key);return formatted(claim??metric)};
 const agency=supplied('Agency')||(/\bagency\s*:\s*([^;\n]+)/i.exec(String(c.contact?.value||''))||/\bagency\s*:\s*([^;\n]+)/i.exec(String(p?.notes||'')))?.[1]?.trim()||'';
 return [c.name||'Unknown',market,country,c.name||'Unknown',agency,supplied('Year-week')||isoWeek(),platform,
   supplied('Niche / content')||nicheLabel(c)||config.niche||'Unknown',
   hasYouTube?platformValue('YT subscribers',c.platformMetrics?.YouTube?.followers??c.followers):'',
   hasYouTube?platformValue('YT views / video',c.platformMetrics?.YouTube?.viewsClaim??views.average):'',
   hasTikTok?platformValue('TikTok followers',c.platformMetrics?.TikTok?.followers??(hasYouTube?null:c.followers)):'',
   hasTikTok?platformValue('TikTok views / video',c.platformMetrics?.TikTok?.viewsClaim??(hasYouTube?null:views.average)):''];
}
export function shortlistCSV(entries,config,weights){
 const headers=['name','platform','source_type','source_url','provenance','fetched_or_imported_at','discovery_market','search_language','query','country','country_source','content_language','language_evidence','language_evidence_urls','verified_audience_country','audience_claim','audience_claim_source','subscribers_followers','recent_average_views','recent_median_views','view_subscriber_ratio','views_window_days','views_sample_size','views_window_start','views_window_end','views_last_checked','views_status','views_sample_limited','views_missing_counts','views_method','views_video_urls','views_video_counts','niche_game_hardware','niche_evidence_urls','public_contact','contact_type','contact_source','review','notes','scoring_niche','scoring_goal','scoring_language','scoring_weights','score','topic_score','language_score','recency_score','views_score','engagement_score','known_factors','evidence_urls','evidence_titles','evidence_dates','missing_data_flags','collaboration_angle','outreach_status','prenew_relevance','community_discussion_share','community_sample_size','community_checked_at','community_evidence','evidence_coverage','prenew_original_record','market_match_tier','language_detected','language_confidence','local_market_evidence','failure_reasons','market_reason_code','is_lingua_franca','language_signals'];
 const lines=entries.map(({creator:c,pipeline:p})=>{
  const e=evidence(c,config,weights),v=viewSummary(c),median=medianViews(c),ratio=viewSubscriberRatio(c),sample=(c.videos||[]).filter(video=>v.videoIds.includes(video.id)),niches=nicheEvidence(c);
  const languageEvidence=c.languageEvidence?`${c.languageEvidence.positiveVideos}/${c.languageEvidence.sampleSize} recent videos match; ${c.languageEvidence.method} ${(c.languageEvidence.videos||[]).map(video=>`${video.videoId}: audio=${video.audioLanguage||'Unknown'}, metadata=${video.metadataLanguage||'Unknown'}`).join(' | ')}`:c.sourceType==='imported'?'Uploader-supplied language; unverified':'Unknown';
  const metadata=[c.name,c.platform,c.sourceType||'demo',c.sourceUrl||'Unknown',c.source,c.fetchedAt||'Unknown',markets[c.market]||c.market||'Unknown',c.searchLanguage||'Unknown',c.query||'',countryName(c),countrySource(c),contentLanguage(c),languageEvidence,(c.languageEvidence?.videos||[]).map(x=>x.url).join(' | ')||'Unknown','Unknown',c.audienceCountry||'Unknown',c.audienceSource||'Unknown',c.followers??'Unknown',v.average??'Unknown',median??'Unknown',ratio.value??'N/A',v.windowDays??'Unknown',v.sampleSize,v.windowStart||'Unknown',v.windowEnd||'Unknown',v.checkedAt||'Unknown',v.status,v.sampleLimited,v.missingViewCount??'Unknown',v.method,sample.map(x=>x.url).join(' | '),sample.map(x=>x.views).join(' | '),nicheLabel(c),[...new Set(niches.flatMap(x=>x.videos.map(video=>video.url)))].join(' | '),c.contact?.value||'No public contact found',c.contact?.kind||'Unknown',c.contact?.sourceUrl||'Unknown',p.review||'Unreviewed',p.notes||'',config.niche,config.goal,config.language,JSON.stringify(weights),e.score,...Object.values(e.factors),e.known,(c.videos||[]).map(x=>x.url).join(' | '),(c.videos||[]).map(x=>x.title).join(' | '),(c.videos||[]).map(x=>x.publishedAt||'Unknown').join(' | '),unknowns(c).join('; '),angle(c,config),p.status,e.factors.topic,c.community?.discussionShare??'Not assessed',c.community?.sampleSize??0,c.community?.checkedAt||'',(c.community?.examples||[]).map(x=>x.url).join(' | '),dimensions(c,config).confidence+'/5',c.prenewImport?JSON.stringify(c.prenewHistory||[c.prenewImport]):''];
  return [...prenewOverview(c,config,v,p),...metadata,c.market_match_tier??'',c.language_detected??'',c.language_confidence??'',(c.local_market_evidence||[]).join(' | '),(c.failure_reasons||[]).join(' | '),c.market_reason_code??'',c.is_lingua_franca??'',JSON.stringify(c.language_signals||{})].map(csvCell).join(',');
 });
 return '\ufeff'+[[...prenewColumns,...headers].map(csvCell).join(','),...lines].join('\r\n');
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

export function dimensions(c,config){
 const e=evidence(c,config),v=viewSummary(c),community=c.community;
 const checks=[{label:'Recent view sample (3+)',known:v.sampleSize>=3&&v.average!=null},{label:'Matching language evidence',known:e.factors.language===100},{label:'Creator country supplied',known:!!c.country},{label:'Community sample (20+ comments / 2+ videos)',known:community?.sampleSize>=20&&community?.videoCount>=2},{label:'Public contact supplied',known:!!c.contact}];
 return {relevance:e.factors.topic,community:community?.discussionShare??null,confidence:checks.filter(x=>x.known).length,checks};
}

// Sorting keys only: ranges are never converted into measured averages.
export function importedMetricKey(raw){
 const text=String(raw??'').trim().replace(/[\s,]/g,'').replace(/[–—]/g,'-');
 const number=value=>{const match=/^(\d+(?:\.\d+)?)([kKmM]?)$/.exec(value);return match?Number(match[1])*({k:1000,m:1000000}[match[2].toLowerCase()]||1):null};
 if(/^[<≤]/.test(text))return number(text.slice(1))===null?null:0;
 if(/^[>≥]/.test(text))return number(text.slice(1));
 const range=/^(\d+(?:\.\d+)?[kKmM]?)-(\d+(?:\.\d+)?[kKmM]?)$/.exec(text);
 if(range){let lower=range[1];if(!/[kKmM]$/.test(lower)&&/[kKmM]$/.test(range[2]))lower+=range[2].slice(-1);const lo=number(lower),hi=number(range[2]);return lo!==null&&hi!==null&&lo<=hi?lo:null;}
 return number(text.replace(/\+$/,''));
}
export function importedPlatformNames(value){return String(value||'').split(/\s*(?:\+|,|\/|&|\band\b)\s*/i).map(x=>x.trim()).filter(Boolean)}
export function filterImportedCreators(records,filters={}){
 const fields={country:'Country',market:'Market',platform:'Platform',niche:'Niche / content'};
 const text=String(filters.search||'').trim().toLocaleLowerCase();
 const selected=records.filter(c=>{
  const row=c.prenewImport;
  if(!row)return false;
  if(text&&![row['Creator / channel'],row['Creator key'],row['Niche / content']].some(v=>String(v||'').toLocaleLowerCase().includes(text)))return false;
  return Object.entries(fields).every(([key,field])=>!filters[key]||(key==='platform'?importedPlatformNames(row[field]).some(v=>v.toLowerCase()===filters[key].toLowerCase()):(row[field]||'Unknown')===filters[key]));
 });
 const field=filters.sort||'Creator / channel',direction=filters.direction==='desc'?-1:1;
 const numeric=['YT subscribers','YT views / video','TikTok followers','TikTok views / video'].includes(field);
 return selected.sort((a,b)=>{
  const av=numeric?importedMetricKey(a.prenewImport[field]):a.prenewImport[field]?.trim()||null;
  const bv=numeric?importedMetricKey(b.prenewImport[field]):b.prenewImport[field]?.trim()||null;
  if(av===null&&bv!==null)return 1;if(bv===null&&av!==null)return -1;
  const order=av===null?0:numeric?av-bv:av.localeCompare(bv,undefined,{numeric:true,sensitivity:'base'});
  return order*direction||String(a.name).localeCompare(String(b.name));
 });
}
