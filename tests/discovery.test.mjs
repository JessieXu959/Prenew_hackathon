import assert from 'node:assert/strict';
import {filtered} from '../dist/discovery.js';
import {defaultWeights} from '../dist/research-core.js';

const video={title:'budget gaming PC',language:'fi',publishedAt:new Date().toISOString(),views:500,likes:20,comments:5};
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
const finnish=['engagement','good','unknown','views'];
for(const source of ['imported','live']){
  const state={records:Object.fromEntries(Object.entries(records).map(([id,c])=>[id,{...c,sourceType:source}])),research:{source,ids:Object.keys(records),size:'all',language:'fi',niche:'Budget gaming',minViews:0},researchWeights:{...defaultWeights}};
  // A zero topic match or a known language mismatch hides a creator; other weak factors just lower the score.
  assert.deepEqual(filtered(state).map(c=>c.id).sort(),finnish);
  assert.equal(filtered(state)[0].id,'good');
  state.researchWeights=Object.fromEntries(Object.keys(defaultWeights).map(k=>[k,0]));
  assert.deepEqual(filtered(state).map(c=>c.id).sort(),finnish);
  state.research.language='de';
  assert.deepEqual(filtered(state).map(c=>c.id).sort(),['language','unknown']);
  state.research.language='fr';
  assert.deepEqual(filtered(state).map(c=>c.id).sort(),['unknown']);
  // The minimum-views filter applies to live YouTube results only.
  state.research.language='fi';
  state.research.minViews=1000;
  assert.deepEqual(filtered(state).map(c=>c.id).sort(),source==='live'?[]:finnish);
  state.research.minViews=0;
  state.research.size='mid';
  assert.deepEqual(filtered(state),[]);
}
console.log('Discovery checks passed: topic filter, language mismatches hidden, unknown language retained, weak factors, zero weights, min views, both sources.');
