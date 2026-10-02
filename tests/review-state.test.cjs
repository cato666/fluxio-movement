const {test} = require('node:test');
const assert = require('node:assert/strict');
const {createDraft,saveAndComplete,requirements,momentsForReview} = require('../app/static/review-state.js');
const valid = {main_focus:'Profundidad',next_session:'3 series',strengths:'Estabilidad',summary:''};
function draftWithChanges() {const draft=createDraft();draft.hydrate({});for(const [key,value] of Object.entries(valid))draft.edit(key,value);return draft;}
test('classification, IA, annotation and status refreshes preserve dirty fields',()=>{
  const draft=draftWithChanges();
  for(const action of ['classification','IA','annotation','start']){
    draft.hydrate({main_focus:`Servidor ${action}`,next_session:'Viejo',strengths:'Viejo'});
    assert.equal(draft.snapshot().main_focus,valid.main_focus);assert.equal(draft.snapshot().next_session,valid.next_session);assert.equal(draft.dirty,true);
  }
});
test('untouched fields accept fresh server values',()=>{const d=createDraft();d.hydrate(valid);d.edit('main_focus','Local');d.hydrate({...valid,strengths:'Nueva'});assert.equal(d.snapshot().strengths,'Nueva');assert.equal(d.snapshot().main_focus,'Local');});
test('acknowledged save clears dirty state and uses server normalization',()=>{const d=draftWithChanges(),sent=d.snapshot();d.acknowledge(sent,{...sent,main_focus:'Normalizado'});assert.equal(d.dirty,false);assert.equal(d.snapshot().main_focus,'Normalizado');});
test('typing while save is in flight retains newer draft',()=>{const d=draftWithChanges(),sent=d.snapshot();d.edit('main_focus','Nuevo texto');d.acknowledge(sent);assert.equal(d.snapshot().main_focus,'Nuevo texto');assert.equal(d.dirty,true);});
test('safe close saves before completing',async()=>{const calls=[],draft=draftWithChanges();await saveAndComplete({draft,status:()=> 'IN_REVIEW',annotations:()=>[{}],save:async s=>{calls.push('save');return s;},complete:async()=>calls.push('complete')});assert.deepEqual(calls,['save','complete']);assert.equal(draft.dirty,false);});
test('failed save never completes and preserves dirty content',async()=>{const draft=draftWithChanges();let completed=false;await assert.rejects(saveAndComplete({draft,status:()=> 'IN_REVIEW',annotations:()=>[{}],save:async()=>{throw Error('503');},complete:async()=>{completed=true;}}),/503/);assert.equal(completed,false);assert.deepEqual(draft.snapshot(),valid);assert.equal(draft.dirty,true);});
test('failed completion retains saved summary and supports retry',async()=>{const draft=draftWithChanges();let saves=0;const options={draft,status:()=> 'IN_REVIEW',annotations:()=>[{}],save:async s=>{saves++;return s;},complete:async()=>{throw Error('409');}};await assert.rejects(saveAndComplete(options),/409/);assert.deepEqual(draft.snapshot(),valid);await saveAndComplete({...options,complete:async()=>({status:'COMPLETED'})});assert.equal(saves,1);});
test('missing requirements are reported together after pending save',async()=>{const draft=createDraft();draft.hydrate({});draft.edit('strengths','Buena técnica');let completed=false;await assert.rejects(saveAndComplete({draft,status:()=> 'PENDING',annotations:()=>[],save:async s=>s,complete:async()=>{completed=true;}}),/revisión iniciada.*anotación.*punto principal.*próxima sesión/);assert.equal(completed,false);assert.equal(draft.snapshot().strengths,'Buena técnica');});
test('edits during safe close block completion',async()=>{const draft=draftWithChanges();let completed=false;await assert.rejects(saveAndComplete({draft,status:()=> 'IN_REVIEW',annotations:()=>[{}],save:async s=>{draft.edit('summary','Nuevo');return s;},complete:async()=>{completed=true;}}),/cambió/);assert.equal(completed,false);assert.equal(draft.snapshot().summary,'Nuevo');});
test('requirements use trimmed text and actual annotations',()=>{assert.deepEqual(requirements('PENDING',[],{main_focus:' ',next_session:''}).map(x=>x.met),[false,false,false,false]);assert.deepEqual(requirements('IN_REVIEW',[{}],valid).map(x=>x.met),[true,true,true,true]);});
test('unified moments deduplicate IDs, retain priority order and omit invalid timestamps',()=>{assert.deepEqual(momentsForReview({review_moments:[{id:1,timestamp:0}],ai_observations:[{id:1,timestamp:0},{id:2,timestamp:3},{id:3,timestamp:null}]}).map(x=>x.id),[1,2]);});
