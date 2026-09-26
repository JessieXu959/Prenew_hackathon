import assert from 'node:assert/strict';
import {filtered} from '../dist/discovery.js';
import {defaultWeights} from '../dist/research-core.js';

const video={title:'budget gaming PC',language:'fi',publishedAt:new Date().toISOString(),views:6000,likes:20,comments:5};
const creator={id:'good',sourceType:'imported',followers:1000,videos:[video]};
const records={
  good:creator,
  topic:{...creator,id:'topic',videos:[{...video,title:'cooking pasta'}]},
  language:{...creator,id:'language',videos:[{...video,language:'de'}]},
  brazilian:{...creator,id:'brazilian',videos:[{...video,language:'pt-BR'}]},
  views:{...creator,id:'views',videos:[{...video,views:0}]},
  engagement:{...creator,id:'engagement',videos:[{...video,likes:0,comments:0}]},
  unknown:{...creator,id:'unknown',videos:[{...video,language:null,likes:null}]},
};
for(const source of ['imported','live']){
  const state={records:Object.fromEntries(Object.entries(records).map(([id,c])=>[id,{...c,sourceType:source}])),research:{source,ids:Object.keys(records),size:'all',language:'fi',niche:'Budget gaming',goal:'buyers'},researchWeights:{...defaultWeights}};
  assert.deepEqual(filtered(state).map(c=>c.id).sort(),['engagement','good','topic']);
  state.researchWeights=Object.fromEntries(Object.keys(defaultWeights).map(k=>[k,0]));
  assert.deepEqual(filtered(state).map(c=>c.id).sort(),['engagement','good','topic']);
  state.research.language='de';
  assert.deepEqual(filtered(state).map(c=>c.id).sort(),['language']);
  state.research.language='fr';
  assert.deepEqual(filtered(state).map(c=>c.id).sort(),[]);
  state.research.size='mid';
  assert.deepEqual(filtered(state),[]);
}
console.log('Discovery checks passed: strict language matching and minimum metrics.');

const base={source:'imported',size:'all',language:'sv',niche:'Budget gaming',goal:'buyers'};
const state={research:base,records:{},researchWeights:defaultWeights};
for(const [id,followers,views,language] of [['pass',501,5001,'sv-SE'],['japanese',900,9000,'ja'],['unknown',900,9000,null],['subBoundary',500,9000,'sv'],['viewBoundary',900,5000,'sv']])state.records[id]={...creator,id,followers,videos:[{...video,views,language}]};
assert.deepEqual(filtered(state).map(c=>c.id),['pass']);
console.log('Strict metadata and minimum boundary checks passed.');
