import http from "node:http";
import {authorizePulse,coordinatePulse} from "./pulse.mjs";
import {normalizeCommand} from "./policy.mjs";
import {isAuthorizedGithubBuild,haveSigningMaterial,signingMaterialForAuthorizedBuild} from "./signing.mjs";
const PORT=Number(process.env.PORT||10000);
const VERSION="0.1.0";
const reply=(res,status,payload)=>{
 res.writeHead(status,{"Content-Type":"application/json; charset=utf-8",
 "Cache-Control":"no-store","X-Content-Type-Options":"nosniff",
 "Access-Control-Allow-Origin":"https://sjm-control-360.floot.app"});
 res.end(JSON.stringify(payload));
};
function safeBasePath(url){
 try{return new URL(url,"http://localhost").pathname;}catch{return "/invalid";}
}
const server=http.createServer(async(req,res)=>{
 const path=safeBasePath(req.url||"/");
 if(req.method==="POST"&&path==="/coordinate"){
   const auth=req.headers.authorization||"";
   if(!auth.startsWith("Bearer ")||!await authorizePulse(auth.slice(7)))return reply(res,403,{ok:false,error:"Pulso no autorizado"});
   const result=await coordinatePulse();
   return reply(res,result.status,result.body);
 }
 if(req.method==="POST"&&path==="/signing-material"){
   if(!haveSigningMaterial())return reply(res,503,{ok:false,error:"Certificado persistente no configurado"});
   const auth=req.headers.authorization||"";
   if(!auth.startsWith("Bearer ")||!await isAuthorizedGithubBuild(auth.slice(7))){
      return reply(res,403,{ok:false,error:"Acceso restringido a GitHub Actions SJM"});
   }
   return reply(res,200,{ok:true,signing:signingMaterialForAuthorizedBuild()});
 }
 if(req.method==="GET"&&path==="/signing-status"){
   return reply(res,200,{ok:true,stableSigningConfigured:haveSigningMaterial(),
      signingMaterialNeverPublic:true,migrationNeededFromV01:true});
 }
 if(req.method==="GET"&&path==="/health"){
  return reply(res,200,{ok:true,server:"KAIRÓS Laboratorio Alterno",version:VERSION,
     state:"standby",phoneCommandsActive:false,deviceKeysStored:false,stableSigningConfigured:haveSigningMaterial(),
     meaning:"Servidor de pruebas activo. NO está conectado al Motorola ni sustituye a CONTROL 360."});
 }
 if(req.method==="GET"&&(path==="/"||path==="/capabilities")){
  return reply(res,200,{ok:true,title:"SJM KAIRÓS · Nodo alterno",version:VERSION,
   purpose:"Validación segura y pruebas independientes de Floot",
   mode:"standby",phoneCommandsActive:false,phoneLinked:false,
   acceptedCommands:["notify","open_app","open_url"],unsafeActionsBlocked:true,
   instructions:"CONTROL 360/Motorola siguen usando Floot hasta una migración verificada"});
 }
 if(req.method==="POST"&&path==="/validate"){
   let raw="";
   try{
    for await(const piece of req){
      raw+=piece.toString();
      if(raw.length>4096)return reply(res,413,{ok:false,error:"Solicitud demasiado grande"});
    }
    const input=JSON.parse(raw);
    const command=normalizeCommand(input);
    return reply(res,200,{ok:true,allowed:!!command,normalized:command,
      executed:false,queued:false,note:"Validación solamente; no se envió nada al teléfono."});
   }catch{return reply(res,400,{ok:false,error:"JSON inválido"});}
 }
 reply(res,404,{ok:false,error:"No encontrado"});
});
server.listen(PORT,"0.0.0.0",()=>console.log("KAIRÓS Render lab listening "+PORT));
