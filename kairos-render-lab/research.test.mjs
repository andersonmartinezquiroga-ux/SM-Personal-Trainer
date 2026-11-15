import test from "node:test";
import assert from "node:assert/strict";
import {normalizePublicTopic,parseWikiExtracts,publicKnowledge} from "./research.mjs";

test("tema público español se normaliza",()=>{
  assert.equal(normalizePublicTopic("¿Qué es la fotosíntesis?"),"fotosintesis");
  assert.equal(normalizePublicTopic("fotosíntesis"),"fotosintesis");
});
test("deniega datos sensibles, URL, líneas nuevas y consultas extensas",()=>{
  for(const s of ["mi contraseña es hola","token de acceso ABC","https://example.com","user@gmail.com","\nfoo","f".repeat(161),"¿?",""]) {
    assert.equal(normalizePublicTopic(s),null,JSON.stringify(s));
  }
});
test("títulos y URLs proceden del dominio oficial y sin HTML inyectado",()=>{
 const sources=parseWikiExtracts({query:{pages:[{pageid:22,title:"Fotosíntesis",extract:"Las plantas utilizan la luz solar."},{pageid:34,title:"<script>alert(1)</script>",extract:"texto"}]}});
 assert.equal(sources.length,2);
 assert.ok(sources[0].url.startsWith("https://es.wikipedia.org/wiki/"));
 assert.ok(!sources[1].url.includes("<script>"));
});
test("consulta de Wikipedia real sólo usa destino fijo y GET; no finge IA",async()=>{
 let requested="";
 const fake=async(url,opts)=>{
   requested=url;
   assert.equal(opts.method,"GET");
   assert.equal(opts.redirect,"error");
   return new Response(JSON.stringify({query:{pages:[{pageid:42,title:"Fotosíntesis",extract:"Proceso en que las plantas transforman luz en energía."}]}}),{status:200,headers:{"content-type":"application/json"}});
 };
 const out=await publicKnowledge("¿Qué es la fotosíntesis?",fake);
 assert.equal(out.status,200);
 assert.equal(out.body.sources.length,1);
 assert.equal(out.body.generatedByLLM,false);
 assert.equal(out.body.executedActions,0);
 assert.equal(new URL(requested).hostname,"es.wikipedia.org");
 assert.equal(new URL(requested).searchParams.get("gsrsearch"),"fotosintesis");
});
test("no hace solicitudes si tema inválido y no inventa fuentes",async()=>{
 let calls=0;
 const out=await publicKnowledge("mi password secreto",()=>{calls++;throw Error("debería impedirse")});
 assert.equal(out.status,400);
 assert.equal(calls,0);
 const noResults=await publicKnowledge("fotosíntesis",async()=>new Response(JSON.stringify({query:{pages:[]}}),{status:200}));
 assert.equal(noResults.status,200);
 assert.deepEqual(noResults.body.sources,[]);
});
test("rechaza errores y respuestas extensas",async()=>{
 const http=await publicKnowledge("fotosíntesis",async()=>new Response("failed",{status:429}));
 assert.equal(http.status,503);
 const large=await publicKnowledge("fotosíntesis",async()=>new Response("x".repeat(170100),{status:200}));
 assert.equal(large.status,503);
});
