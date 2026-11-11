import {createPublicKey,verify} from "node:crypto";
const REPO="andersonmartinezquiroga-ux/SM-Personal-Trainer";
const WORKFLOW=".github/workflows/kairos-pulso-general-15m.yml";
const AUD="sjm-kairos-pulse-v1";
const JWKS="https://token.actions.githubusercontent.com/.well-known/jwks";
const scope=["registro","memoria_operativa","respaldo_cron_15m"];
let keys=[],at=0;
export async function authorizePulse(raw){
 try{
  if(typeof raw!=="string"||raw.length>8500)return false;
  const p=raw.split(".");if(p.length!==3)return false;
  const h=JSON.parse(Buffer.from(p[0],"base64url")),v=JSON.parse(Buffer.from(p[1],"base64url"));
  const now=Math.floor(Date.now()/1000);
  if(h.alg!=="RS256"||!h.kid||v.iss!=="https://token.actions.githubusercontent.com"||v.aud!==AUD||v.repository!==REPO||v.ref!=="refs/heads/main"||v.repository_id!=="1340977588"||v.repository_owner_id!=="317761897"||v.workflow_ref!==REPO+"/"+WORKFLOW+"@refs/heads/main"||!["repo:"+REPO+":ref:refs/heads/main","repo:andersonmartinezquiroga-ux@317761897/SM-Personal-Trainer@1340977588:ref:refs/heads/main"].includes(v.sub)||!Number.isFinite(v.iat)||!Number.isFinite(v.exp)||v.exp<now||v.iat>now+30||now-v.iat>600||v.exp-v.iat>900)return false;
  if(Date.now()-at>300000||!keys.length){const r=await fetch(JWKS,{signal:AbortSignal.timeout(8000)});if(!r.ok)return false;keys=(await r.json()).keys;at=Date.now();}
  const k=keys.find(x=>x.kid===h.kid&&x.kty==="RSA");if(!k)return false;
  return verify("RSA-SHA256",Buffer.from(p[0]+"."+p[1]),createPublicKey({key:k,format:"jwk"}),Buffer.from(p[2],"base64url"));
 }catch{return false;}
}
export async function coordinatePulse(rawToken){
 // GitHub OIDC has already been verified by authorizePulse. Supabase validates
 // the signature, audience and exact repository identity a second time.
 if(typeof rawToken!=="string"||rawToken.length<100||rawToken.length>8500)
  return {status:403,body:{ok:false,reason:"Pulso sin identidad verificada"}};
 const url="https://dfqjwlsgqetyxdrsuviy.supabase.co/functions/v1/sjm_kairos_pulse_coordinator_v1";
 try{
  const response=await fetch(url,{method:"POST",headers:{
   "Authorization":"Bearer "+rawToken,
   "Content-Type":"application/json"
  },body:JSON.stringify({operation:"coordinate",interval_minutes:15}),
   signal:AbortSignal.timeout(45000)});
  let data={};
  try{data=await response.json();}catch{}
  if(!response.ok||data?.ok!==true)
   return {status:502,body:{ok:false,reason:"El coordinador seguro no aceptó la verificación",upstream_status:response.status,
    upstream_reason:String(data?.error||"no_reply").slice(0,80)}};
  return {status:202,body:{ok:true,accepted:true,
   scope:["registro","memoria_operativa","respaldo_cron_15m"],
   registryStatus:data.registryStatus||"unknown",
   cronRecent:data.cronRecent??null,
   failoverTriggered:data.failoverTriggered===true,
   registryMemoryChecked:data.registryMemoryChecked===true,
   externalActions:0,
   meaning:"Pulso autenticado y verificación de registro/memoria completada. No equivale a postulaciones enviadas."}};
 }catch{
  return {status:502,body:{ok:false,reason:"Coordinador seguro no disponible"}};
 }
}
