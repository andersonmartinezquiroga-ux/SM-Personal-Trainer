import test from "node:test";
import assert from "node:assert/strict";
import {normalizeCommand} from "./policy.mjs";
test("admite acciones simples sin capacidad de ejecutarlas",()=>{
 assert.deepEqual(normalizeCommand({type:"notify",message:"KAIRÓS conectado"}),{type:"notify",payload:{message:"KAIRÓS conectado"}});
 assert.equal(normalizeCommand({type:"open_app",package:"com.arlosoft.macrodroid"}).type,"open_app");
 assert.equal(normalizeCommand({type:"open_url",url:"https://sjm-control-360.floot.app/mentor"}).type,"open_url");
});
test("deniega dominios extraños, scripts y permisos amplios",()=>{
 for(const c of [
  {type:"open_url",url:"javascript:alert(1)"},
  {type:"open_url",url:"https://sjm-control-360.floot.app.evil.net/mentor"},
  {type:"open_url",url:"https://sjm-control-360.floot.app/mentor?redirect=x"},
  {type:"open_url",url:"https://sjm-control-360.floot.app/_api/kairos/phone_poll"},
  {type:"open_app",package:"com.android.settings"},
  {type:"open_app",package:"com.whatsapp"},
  {type:"tap",x:1,y:3},
  {type:"notify",message:"Hola",send:true},
  {type:"notify",message:"Hola\nworld"}
 ])assert.equal(normalizeCommand(c),null);
});
