// COMTROL 360 · pruebas repetibles de herramientas independientes v3.4
// Node 18+: node kairos-web/tests/independent_tools_smoke.mjs
// No llama servicios externos y no descarga modelos.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname,resolve } from "node:path";
const root=resolve(dirname(fileURLToPath(import.meta.url)),"..");
const html=readFileSync(resolve(root,"index.html"),"utf8");
const between=(a,b)=>{
 const i=html.indexOf(a),j=html.indexOf(b,i);
 assert(i>=0&&j>i,"missing code "+a);
 return html.slice(i,j);
};
const calc=new Function(between("function localCalculate(expression){","function initIndependentTools(){")+"\nreturn localCalculate;")();
for(const [expr,expected] of [["25000+5000",30000],["25000*3",75000],["(12+8)*3",60],["1,5*2",3],["25000*19%",4750],["-4+10",6],["(10+(2*3))/4",4],["100/4",25]]){
 assert.equal(calc(expr),expected,"calculation "+expr);
}
for(const invalid of ["5/0","console.log(1)","","999999999999999*999","(2+3","3+"]){
 assert.throws(()=>calc(invalid),"invalid "+invalid);
}
assert(html.includes('SmolLM2-360M-Instruct-q4f32_1-MLC'),"small independent model not configured");
assert(html.includes('await import("https://esm.run/@mlc-ai/web-llm")'),"lazy WebLLM import missing");
assert(html.includes("window.confirm(\"¿Descargar un modelo abierto"),"download without opt-in");
assert(html.includes('action:"research_public"'),"public research route absent");
assert(html.includes('allow_public_search:true'),"public search consent missing");
assert(html.includes('COMTROL · Respaldo privado voluntario de conversaciones v3.0'),"private memory regression");
let passed=20;
let request;
const engine={chat:{completions:{create:async options=>{
 request=options;
 return {choices:[{message:{content:"Respuesta local ficticia"}}]};
}}}};
const local=new Function("localModelEngine",between("async function askLocalBrowserModel(q,chat){","function updateStandaloneControls(){")+"\nreturn askLocalBrowserModel;")(engine);
const conversation={messages:[
 {role:"user",text:"Estado privado"},
 {role:"assistant",text:"Código secreto de CONTROL",mode:"kairos_pairing_code_10min"},
 {role:"user",text:"Quiero abrir tienda de zapatos"},
 {role:"assistant",text:"Prepara un presupuesto",mode:"local_browser_llm"},
 {role:"user",text:"¿Qué hago?"}
]};
const answer=await local("¿Qué hago?",conversation);
assert.equal(answer.mode,"local_browser_llm");
assert.equal(answer.externalProcessing,false);
assert.equal(answer.executedActions,0);
assert.equal(answer.contextMessagesUsed,2);
assert(!JSON.stringify(request).includes("Código secreto de CONTROL"),"private Mentor data leaked to local model context");
assert.equal(request.messages.at(-1).content,"¿Qué hago?");
assert(request.max_tokens<=320);
passed+=7;
console.log("COMTROL local tooling smoke PASS: "+passed+" checks; GPU inference/download not exercised.");
