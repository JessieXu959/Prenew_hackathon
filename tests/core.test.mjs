import assert from 'node:assert/strict';
import {localizedQuery,matchesKeywords,evidence,defaultWeights,shortlistCSV} from '../dist/research-core.js';
const fi={country:'FI',language:'fi',niche:'Budget gaming',goal:'buyers'};
assert.match(localizedQuery(fi),/halpa pelikone/);
assert.match(localizedQuery({...fi,language:'de'}),/günstiger/);
assert.match(localizedQuery({...fi,goal:'sellers'}),/myynti/);
assert.equal(localizedQuery(fi),'"halpa pelikone" | "budjetti pelitietokone"');
const topic=(title,niche,goal='buyers')=>evidence({followers:1,videos:[{title,description:''}]},{...fi,niche,goal}).factors.topic;
assert.equal(topic('My latest contest, the fastest speedrun','PC performance'),0);
assert.equal(topic('I focused on what caused the bug','Refurbished tech'),0);
assert.equal(topic('Kasaan elämäni parhaan kakun','PC building'),0);
assert.equal(topic('Sellaista elämää','Gaming','sellers'),0);
assert.equal(topic('RTX 4060 benchmark test','PC performance'),100);
assert.equal(topic('Used gaming PC for 300€','Refurbished tech'),100);
assert.equal(topic('Kasasin budjettipelikoneen','PC building'),100);
assert.equal(topic('Uusi budjettipelikone','Gaming'),100);
assert.ok(matchesKeywords('Günstiger Gaming-PC',['günstig']));
const c={name:'=SYNTHETIC TEST',sourceType:'imported',platform:'Twitch',followers:1000,videos:[{title:'halpa pelikone testi',description:'budget test',views:500,likes:null,comments:4,publishedAt:'2026-09-01T00:00:00Z',language:null,url:'https://twitch.tv/synthetic_test_only'}]};
const e=evidence(c,fi,defaultWeights,Date.parse('2026-09-26'));
assert.equal(e.factors.topic,100);assert.equal(e.factors.language,null);assert.equal(e.factors.engagement,null);assert.equal(e.factors.views,null);assert.equal(e.known,2);
assert.equal(evidence(c,fi,Object.fromEntries(Object.keys(defaultWeights).map(k=>[k,0]))).score,null);
assert.equal(evidence({...c,followers:null},fi).factors.views,null);
const csv=shortlistCSV([{creator:c,pipeline:{status:'Shortlisted',notes:'first line\nsecond, line',review:'Reviewing'}}],fi,defaultWeights);
assert.match(csv,/'=SYNTHETIC TEST/);assert.match(csv,/Audience geography unverified/);assert.match(csv,/first line\nsecond, line/);
assert.ok(csv.split('\r\n')[0].includes('"view_subscriber_ratio"'));assert.match(csv,/"N\/A"/);
console.log('Core checks passed: localized queries, missing evidence, scoring, zero weights, CSV escaping.');

const {comparisonMetrics}=await import('../dist/research-core.js');
const comparison=comparisonMetrics({videos:[{title:'Refurbished budget gaming PC',views:1000,likes:50,comments:10},{title:'Pasta recipe',views:3000,likes:null,comments:0},{title:'GPU upgrade',views:null,likes:10,comments:null}]});
assert.deepEqual(comparison.views,{value:null,count:0});
assert.deepEqual(comparison.comments,{value:5,count:2});
assert.deepEqual(comparison.likes,{value:30,count:2});
assert.equal(comparison.engagement,6);
assert.equal(comparison.engagementSamples,1);
assert.ok(comparison.keywords.includes('refurbished'));
assert.ok(comparison.keywords.includes('upgrade'));
assert.ok(!comparison.keywords.includes('pasta'));
assert.equal(comparisonMetrics({}).views.value,null);
assert.equal(comparisonMetrics({}).engagement,null);
console.log('Comparison metrics checks passed.');

const {viewSummary,medianViews,viewSubscriberRatio,nicheEvidence,languageStatus}=await import('../dist/research-core.js');
const live={...c,sourceType:'live',country:'FI',countrySource:'YouTube channel-declared country',market:'FI',contentLanguage:'fi',fetchedAt:'2026-09-27T12:00:00Z',videos:Array.from({length:3},(_,i)=>({id:String(i),title:'Fortnite RTX 5090 budget gaming PC',publishedAt:'2026-09-25T12:00:00Z',views:(i+1)*100,url:'https://youtube.com/watch?v='+i,recentUpload:true,audioLanguage:'fi',metadataLanguage:'fi'})),recentViewStats:{average:200,windowDays:30,sampleSize:3,videoIds:['0','1','2'],checkedAt:'2026-09-27T12:00:00Z',status:'sufficient',method:'Mean lifetime public views of sampled uploads'}};
assert.equal(viewSummary(live).average,200);
assert.equal(medianViews(live),200);
const outlier={...live,videos:[...live.videos,{...live.videos[0],id:'3',views:10000}],recentViewStats:{...live.recentViewStats,average:2650,sampleSize:4,videoIds:['0','1','2','3']}};
assert.equal(medianViews(outlier),250,'Median must resist one high-view outlier');
assert.equal(medianViews({...live,videos:live.videos.slice(0,2)}),null,'An incomplete measured sample must not produce a median');
assert.deepEqual(viewSubscriberRatio(live),{value:20,label:'High Activity',tone:'high',text:'20.0% view ratio'});
assert.equal(viewSubscriberRatio({...live,recentViewStats:{...live.recentViewStats,average:199}}).label,'Healthy / Normal');
assert.equal(viewSubscriberRatio({...live,recentViewStats:{...live.recentViewStats,average:80}}).label,'Healthy / Normal');
assert.equal(viewSubscriberRatio({...live,recentViewStats:{...live.recentViewStats,average:79}}).label,'Low Activity');
for(const invalid of [{followers:0},{followers:null},{recentViewStats:{...live.recentViewStats,average:0}},{recentViewStats:{...live.recentViewStats,average:null}}])assert.equal(viewSubscriberRatio({...live,...invalid}).text,'Ratio: N/A');
assert.equal(evidence(live,fi).avg,200);
assert.equal(comparisonMetrics(live).views.value,200);
assert.equal(viewSummary({...live,recentViewStats:undefined}).average,null,'Old snapshots require refresh');
assert.equal(viewSummary({...live,sourceType:'imported'}).average,null,'Imported claims never become measured averages');
assert.ok(nicheEvidence(live).some(x=>x.label==='Fortnite'&&x.videos.length===3));
assert.equal(languageStatus({...live,videos:live.videos.map(v=>({...v,metadataLanguage:'pt-BR'}))},'fi').accepted,false);
const fullCSV=shortlistCSV([{creator:live,pipeline:{notes:'Review linked videos',status:'Shortlisted'}}],fi,defaultWeights);
for(const column of ['country','country_source','content_language','language_evidence','verified_audience_country','subscribers_followers','recent_average_views','recent_median_views','view_subscriber_ratio','views_window_days','views_sample_size','views_last_checked','niche_game_hardware','public_contact','views_video_urls','missing_data_flags'])assert.ok(fullCSV.split('\r\n')[0].includes('"'+column+'"'),column);
assert.match(fullCSV,/"200","200","20","30","3"/);assert.match(fullCSV,/"100 \| 200 \| 300"/);
assert.match(fullCSV,/No public contact found/);assert.match(fullCSV,/YouTube channel-declared country/);
console.log('Sponsor export checks passed: measured-view consistency, source separation, language conflicts, niche/video provenance, and complete CSV fields.');

const overviewHeader=['Creator key','Market','Country','Creator / channel','Agency','Year-week','Platform','Niche / content','YT subscribers','YT views / video','TikTok followers','TikTok views / video'];
assert.ok(fullCSV.startsWith('\ufeff'+overviewHeader.map(x=>'"'+x+'"').join(',')+','));
const imported={name:'Estonian gamer',platform:'YouTube + TikTok',sourceType:'imported',source:'PRENEW spreadsheet',contentLanguage:'et',followers:12000,videos:[],prenewImport:{'YT subscribers':'12,000','YT views / video':'10K-50K','TikTok followers':'30,000','TikTok views / video':'<10K','Niche / content':'Gaming'},prenewHistory:[{'YT subscribers':'12,000','YT views / video':'10K-50K','TikTok followers':'30,000','TikTok views / video':'<10K','Niche / content':'Gaming'}]};
const importedCSV=shortlistCSV([{creator:imported,pipeline:{notes:'Agency: North Star\nCheck audience',status:'Shortlisted'}}],fi,defaultWeights);
assert.match(importedCSV,/"Estonian gamer","EE","Estonia","Estonian gamer","North Star","\d{4}-\d{2}","YouTube \+ TikTok","Gaming","12,000","10K-50K","30,000","<10K"/);
assert.match(importedCSV,/"prenew_original_record"/);
assert.match(importedCSV,/Agency: North Star\nCheck audience/);
const unknownCSV=shortlistCSV([{creator:{name:'Unknown origin',platform:'TikTok',sourceType:'imported',videos:[]},pipeline:{}}],fi,defaultWeights);
assert.match(unknownCSV,/"Unknown origin","Unknown","Unknown","Unknown origin","","\d{4}-\d{2}","TikTok","Unknown","","","Unknown","Unknown"/);
console.log('PRENEW two-zone export checks passed.');

const {languages,markets,dimensions}=await import('../dist/research-core.js');
assert.equal(languages.et,'Estonian');assert.equal(languages.hu,'Hungarian');
assert.equal(markets.EE,'Estonia');assert.equal(markets.HU,'Hungary');
for(const language of ['et','hu']){const query=localizedQuery({...fi,language});assert.ok(query.length>5);assert.ok(!query.includes('?'));}
assert.equal(dimensions(c,fi).community,null);
assert.equal(dimensions({...c,community:{discussionShare:75,sampleSize:24,videoCount:2}},fi).community,75);
console.log('New-language queries and assessment dimensions passed.');

assert.equal(localizedQuery({language:'et',niche:'Gaming',mode:'channel'}),localizedQuery({language:'et',niche:'Gaming',mode:'video'}));

const {niches}=await import('../dist/research-core.js');
for(const language of Object.keys(languages))for(const niche of niches)for(const mode of ['channel','video']){
 const query=localizedQuery({language,niche,mode,goal:'buyers'});
 assert.equal(query.split('|').length,2,language+' '+niche+' '+mode);
 assert.ok(query.length<=600);
}
console.log('Two localized alternatives verified for every language, niche and mode.');
