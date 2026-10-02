const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const ReviewState=require('../app/static/review-state.js');

// Execute the actual Studio handlers. Rendering is stubbed; browser E2E covers it.
async function studio(){
  const nodes=new Map(),listeners={},calls=[];
  const node=id=>{if(!nodes.has(id))nodes.set(id,{value:'',hidden:id==='#coach-annotation-editor',disabled:false,textContent:'',options:[],classList:{toggle(){},add(){}},addEventListener(type,fn){this[type]=fn;},replaceChildren(){},append(){},focus(){},scrollIntoView(){}});return nodes.get(id);};
  const document={querySelector:node,createElement:()=>node(`element-${nodes.size}`),querySelectorAll:selector=>selector.includes('button')?[...nodes].filter(([id])=>/save|complete|start-review|cancel|add-annotation/.test(id)).map(([,n])=>n):[node('#coach-annotation-text')]};
  const server={status:'IN_REVIEW',summary:{},athlete:{name:'QA'},analysis:{repetitions:[]}},annotations=[];
  let fault,hold;
  const context=vm.createContext({document,window:{addEventListener:(type,fn)=>listeners[type]=fn},ReviewState,Intl,console,fetch:async(url,options={})=>{
    const method=options.method||'GET',body=options.body&&JSON.parse(options.body);
    calls.push({url,method,body});
    if(hold&&method!=='GET'){const wait=hold;hold=null;await wait;}
    if(fault&&method!=='GET'){const current=fault;fault=null;if(current==='offline')throw new TypeError('Failed to fetch');return {ok:false,status:current,json:async()=>({detail:`Error ${current}`})};}
    let data;
    if(url==='/api/auth/me')data={id:'coach'};
    else if(url.includes('/annotations')){if(method==='POST')annotations.push({...body,id:'annotation'});data=method==='GET'?{items:annotations}:annotations.at(-1);}
    else if(url.includes('/summary')){server.summary=body;data=body;}
    else if(url.includes('/complete')){server.status='COMPLETED';data={status:server.status};}
    else if(url.includes('/start')){server.status='IN_REVIEW';data={status:server.status};}
    else data=server;
    return {ok:true,status:200,json:async()=>JSON.parse(JSON.stringify(data))};
  }});
  const source=fs.readFileSync(require.resolve('../app/static/app.js'),'utf8').split('const path = window.location.pathname;')[0];
  vm.runInContext(source,context);
  vm.runInContext(`showView=()=>{};renderCoachAnalysis=(item,classify,decide)=>{globalThis.actions={classify,decide};};renderCoachAnnotations=()=>{};fillAnnotationRepetitions=()=>{};`,context);
  await context.setupCoachReviewDetail('review');
  return {node,calls,server,annotations,context,listeners,fail:value=>fault=value,hold:promise=>hold=promise,edit:(id,value)=>{node(id).value=value;node(id).input();}};
}
const fill=s=>{s.edit('#coach-main-focus','Borrador principal');s.edit('#coach-next-session','Próxima sesión pendiente');};
const mutations=s=>s.calls.filter(c=>c.method!=='GET');
test('annotation DELETE 204 succeeds without trying to parse absent JSON',async()=>{
  const s=await studio();let parsed=false;
  s.context.fetch=async()=>({ok:true,status:204,json:async()=>{parsed=true;throw Error('No JSON body');}});
  assert.equal(await s.context.apiJson('/annotations/id',{method:'DELETE'}),null);
  assert.equal(parsed,false);
});
async function readyToClose(s){s.node('#coach-add-annotation').onclick();s.node('#coach-annotation-text').value='Anotación existente';await s.node('#coach-annotation-save').onclick();s.calls.length=0;}

test('Studio refresh after classification and both IA decisions preserves summary',async()=>{const s=await studio();fill(s);await s.context.actions.classify({id:'rep'},'BEST');for(const decision of ['CONFIRMED','DISMISSED'])await s.context.actions.decide({id:'ai'},{decision});assert.equal(s.node('#coach-main-focus').value,'Borrador principal');assert.equal(s.node('#coach-draft-status').textContent,'Cambios sin guardar');});
test('annotation save refresh preserves pending summary and editor closes only on success',async()=>{const s=await studio();fill(s);s.node('#coach-add-annotation').onclick();s.node('#coach-annotation-text').value='Comentario';await s.node('#coach-annotation-save').onclick();assert.equal(s.node('#coach-next-session').value,'Próxima sesión pendiente');assert.equal(s.node('#coach-annotation-editor').hidden,true);assert.equal(s.annotations.length,1);});
test('beforeunload warns for summary and annotation; acknowledged save clears summary warning',async()=>{const s=await studio();fill(s);let prevented=0;const event=()=>({preventDefault(){prevented++;}});s.listeners.beforeunload(event());assert.equal(prevented,1);await s.node('#coach-save-summary').onclick();s.listeners.beforeunload(event());assert.equal(prevented,1);s.node('#coach-add-annotation').onclick();s.node('#coach-annotation-text').value='Pendiente';s.listeners.beforeunload(event());assert.equal(prevented,2);});
test('actual close handler saves before complete and locks fields',async()=>{const s=await studio();fill(s);await readyToClose(s);await s.node('#coach-complete-review').onclick();assert.deepEqual(mutations(s).map(c=>c.url.split('/').at(-1).split('?')[0]),['summary','complete']);assert.equal(s.node('#coach-main-focus').disabled,true);assert.equal(s.node('#coach-draft-status').textContent,'Sin cambios pendientes');});
for(const status of [401,403,409,503,'offline'])test(`save failure ${status} blocks close, keeps draft and allows recovery`,async()=>{const s=await studio();fill(s);await readyToClose(s);s.fail(status);await s.node('#coach-complete-review').onclick();assert.equal(s.server.status,'IN_REVIEW');assert.equal(mutations(s).filter(c=>c.url.includes('/complete')).length,0);assert.equal(s.node('#coach-main-focus').value,'Borrador principal');assert.equal(s.node('#coach-draft-status').textContent,'Cambios sin guardar');assert.equal(s.node('#coach-complete-review').disabled,false);await s.node('#coach-complete-review').onclick();assert.equal(s.server.status,'COMPLETED');});
test('failed completion keeps saved data and retry does not repeat summary save',async()=>{const s=await studio();fill(s);await readyToClose(s);await s.node('#coach-save-summary').onclick();s.fail(409);await s.node('#coach-complete-review').onclick();assert.equal(s.node('#coach-main-focus').value,'Borrador principal');assert.equal(s.server.status,'IN_REVIEW');await s.node('#coach-complete-review').onclick();assert.equal(mutations(s).filter(c=>c.url.includes('/summary')).length,1);});
test('queued double click does not duplicate annotation, summary or completion',async()=>{for(const id of ['#coach-annotation-save','#coach-save-summary','#coach-complete-review']){const s=await studio();fill(s);await readyToClose(s);if(id.includes('annotation')){s.node('#coach-add-annotation').onclick();s.node('#coach-annotation-text').value='Comentario';}let resolve; s.hold(new Promise(r=>resolve=r));const first=s.node(id).onclick();const second=s.node(id).onclick();resolve();await Promise.all([first,second]);const endpoints=mutations(s).map(c=>c.url);assert.equal(new Set(endpoints).size,endpoints.length);}});
