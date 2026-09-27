import assert from 'node:assert/strict';
import {filtered,researchHTML,researchDetailHTML} from '../dist/discovery.js';
import {defaultWeights} from '../dist/research-core.js';

const at=new Date().toISOString();
const videos=Array.from({length:5},(_,i)=>({id:String(i),title:'halpa pelikone / budget gaming PC',language:'fi',audioLanguage:'fi',metadataLanguage:'fi',recentUpload:true,publishedAt:at,views:6000,likes:20,comments:5,url:`https://youtube.com/watch?v=fixture000${i}`}));
const creator={id:'good',name:'Fixture',platform:'YouTube',sourceType:'live',country:'FI',market:'FI',contentLanguage:'fi',sourceUrl:'https://youtube.com/channel/fixture',followers:1000,videos,fetchedAt:at,recentViewStats:{average:6000,windowDays:30,sampleSize:5,videoIds:videos.map(v=>v.id),checkedAt:at,status:'sufficient',method:'Measured upload sample'}};
const stateFor=(records,overrides={})=>({campaign:{goal:'buyers'},pipeline:{},records,research:{source:'live',market:'FI',ids:Object.keys(records),size:'all',language:'fi',niche:'Budget gaming',goal:'buyers',minSubscribers:500,minAverageViews:5000,...overrides},researchWeights:{...defaultWeights}});
const records={
 good:creator,
 unrelated:{...creator,id:'unrelated',videos:videos.map(v=>({...v,title:'Cooking pasta'}))},
 foreign:{...creator,id:'foreign',country:'BR',followers:100000000},
 unknownCountry:{...creator,id:'unknownCountry',country:null},
 mixed:{...creator,id:'mixed',videos:videos.map((v,i)=>i? v:{...v,audioLanguage:'ja',language:'ja'})},
 unknownLanguage:{...creator,id:'unknownLanguage',videos:videos.map(v=>({...v,audioLanguage:null,metadataLanguage:null,language:null}))},
 oneHit:{...creator,id:'oneHit',videos:videos.map((v,i)=>({...v,recentUpload:i===0}))},
 insufficientViews:{...creator,id:'insufficientViews',recentViewStats:{...creator.recentViewStats,average:null,sampleSize:1,status:'insufficient'}},
 subBoundary:{...creator,id:'subBoundary',followers:500},
 viewBoundary:{...creator,id:'viewBoundary',recentViewStats:{...creator.recentViewStats,average:5000}},
};
const state=stateFor(records);
assert.deepEqual(filtered(state).map(c=>c.id),['good']);
for(const [market,language] of [['FI','fi'],['SE','sv'],['EE','et'],['NL','nl']]){
 const local={...creator,id:'local',market,country:market,contentLanguage:'en',eligibility:'match',market_match_tier:2,language_detected:'en',language_confidence:.65,local_market_evidence:['channel country: '+market,'local link: https://example.'+market.toLowerCase()],videos:videos.map(v=>({...v,audioLanguage:'en',metadataLanguage:'en',language:'en'}))};
 assert.deepEqual(filtered(stateFor({local},{market,language})).map(c=>c.id),['local'],`${market} local English creator must reach matching candidates`);
 const foreign={...local,country:'US'};
 assert.equal(filtered(stateFor({local:foreign},{market,language})).length,0,`${market} foreign channel must stay excluded`);
}
state.researchWeights=Object.fromEntries(Object.keys(defaultWeights).map(k=>[k,0]));
assert.deepEqual(filtered(state).map(c=>c.id),['good'],'Scores cannot rescue language/country mismatches');
state.research.market='DE';assert.deepEqual(filtered(state),[],'Previous-market results cannot leak into a new market');
state.research.market='FI';state.research.language='de';assert.deepEqual(filtered(state),[]);
state.research.language='fi';state.research.size='mid';assert.deepEqual(filtered(state),[]);
state.research.size='all';state.research.minSubscribers=0;state.research.minAverageViews=0;
assert.deepEqual(filtered(state).map(c=>c.id).sort(),['good','insufficientViews','viewBoundary']);

for(const country of ['BR','CN','JP']){
 const bad={...creator,id:country,market:'SE',country,videos:videos.map(v=>({...v,language:'sv',audioLanguage:'sv',metadataLanguage:'sv'}))};
 assert.equal(filtered(stateFor({[country]:bad},{market:'SE',language:'sv'})).length,0);
}
const imported={...creator,id:'imported',sourceType:'imported',country:null,videos:[{...videos[0],language:'fi'}],recentViewStats:undefined};
assert.equal(filtered(stateFor({imported},{source:'imported',minAverageViews:0,bucket:'review'})).length,1);
assert.equal(filtered(stateFor({imported},{source:'imported'})).length,0,'One imported video must not masquerade as an average');
assert.match(researchHTML(stateFor({imported},{source:'imported',minAverageViews:0,bucket:'review'})),/CSV IMPORT · UNVERIFIED/);
const small={...creator,id:'small',followers:1000,videos:videos.map((v,i)=>({...v,title:i?'Gaming PC':'budget gaming PC'}))};
const large={...creator,id:'large',followers:500000};
const ranking=stateFor({small,large});ranking.researchWeights={topic:100,language:100,recency:0,views:0,engagement:0};
assert.deepEqual(filtered(ranking).map(c=>c.id),['large','small']);assert.equal(ranking.researchWeights.language,0);
const html=researchHTML(stateFor({good:creator}));
for(const expected of ['Target country / market','Germany','Recent average views','Median: 6,000 views','600.0% view ratio','High Activity','30-day publication window','5 videos','Niche / games / hardware','No public contact found','Verified audience country'])assert.ok(html.includes(expected),expected);
const detailHTML=researchDetailHTML(creator,stateFor({good:creator}));
assert.match(detailHTML,/VIEW WINDOW SAMPLE/);
assert.match(detailHTML,/Median: 6,000 views/);
console.log('Discovery checks passed: strict country/recent-language gates, Sweden regressions, thresholds, imports, ranking, and required UI fields.');

const staleTopic={...creator,id:'stale',videos:[...videos.map(v=>({...v,title:'Cooking pasta'})),{...videos[0],id:'old-hit',title:'budget gaming PC',publishedAt:'2000-01-01',recentUpload:false,matchedSearch:true}]};
assert.equal(filtered(stateFor({stale:staleTopic})).length,0,'An old search hit cannot establish current niche relevance');
console.log('Current niche regression passed: historical search hits cannot rescue unrelated recent uploads.');

const capped=stateFor({low:{...creator,id:'low',followers:799},edge:{...creator,id:'edge',followers:800},cap:{...creator,id:'cap',followers:1000},over:{...creator,id:'over',followers:1001}},{maxSubscribers:1000});
assert.deepEqual(filtered(capped).map(c=>c.id).sort(),['cap','edge']);
const reach=stateFor({a:{...creator,id:'a',followers:2000},b:{...creator,id:'b',followers:800,recentViewStats:{...creator.recentViewStats,average:9000}}});
assert.deepEqual(filtered(reach).map(c=>c.id),['b','a']);
assert.match(researchHTML(reach),/How Community Engagement is Calculated/);

const reviewState=stateFor({unknownCountry:records.unknownCountry,unknownLanguage:records.unknownLanguage,mixed:records.mixed},{bucket:'review'});
assert.deepEqual(filtered(reviewState).map(c=>c.id).sort(),['unknownCountry','unknownLanguage']);
assert.ok(researchHTML(reviewState).includes('Needs review'));
assert.ok(researchDetailHTML(creator,stateFor({good:creator})).includes('Analyze community'));
assert.ok(researchHTML(stateFor({good:creator})).includes('Estonian'));
assert.ok(researchHTML(stateFor({good:creator})).includes('Hungarian'));
