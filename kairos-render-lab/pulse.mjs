import {createPublicKey,verify} from "node:crypto";
const REPO="andersonmartinezquiroga-ux/SM-Personal-Trainer";
const WORKFLOW=".github/workflows/kairos-pulso-general-15m.yml";
const AUD="sjm-kairos-pulse-v1";
const JWKS="https://token.actions.githubusercontent.com/.well-known/jwks";
const scope=["radar_1","radar_2","radar_3","radar_4","radar_5","radar_6","laboratorio_7","candidaturas","computadores","financiacion","alianzas","proyectos_sjm"];
let keys=[],at=0;
export async function authorizePulse(raw){
 try{
  if(typeof raw!=="string"||raw.length>8500)return false;
  const p=raw.split(".");if(p.length!==3)return false;
  const h=JSON.parse(Buffer.from(p[0],"base64url")),v=JSON.parse(Buffer.from(p[1],"base64url"));
  const now=Math.floor(Date.now()/1000);
  if(h.alg!=="RS256"||!h.kid||v.iss!=="https://token.actions.githubusercontent.com"||v.aud!==AUD||v.repository!==REPO||v.ref!=="refs/heads/main"||v.repository_id!=="1340977588"||v.repository_owner_id!=="317761897"||v.workflow_ref!==REPO+"/"+WORKFLOW+"@refs/heads/main"||v.sub!=="repo:"+REPO+":ref:refs/heads/main"||!Number.isFinite(v.iat)||!Number.isFinite(v.exp)||v.exp<now||v.iat>now+30||now-v.iat>600||v.exp-v.iat>900)return false;
  if(Date.now()-at>300000||!keys.length){const r=await fetch(JWKS,{signal:AbortSignal.timeout(8000)});if(!r.ok)return false;keys=(await r.json()).keys;at=Date.now();}
  const k=keys.find(x=>x.kid===h.kid&&x.kty==="RSA");if(!k)return false;
  return verify("RSA-SHA256",Buffer.from(p[0]+"."+p[1]),createPublicKey({key:k,format:"jwk"}),Buffer.from(p[2],"base64url"));
 }catch{return false;}
}
export async function coordinatePulse(){
 const url=process.env.KAIROS_COORDINATOR_URL||"";
 const token=process.env.KAIROS_COORDINATOR_TOKEN||"";
 if(!url||!token)return {status:503,body:{ok:false,connected:false,reason:"Coordinador de tareas no configurado",scope}};
 if(!url.startsWith("https://"))return {status:503,body:{ok:false,reason:"Se exige HTTPS"}};
 try{
  const response=await fetch(url,{method:"POST",headers:{"Authorization":"Bearer "+token,"Content-Type":"application/json"},body:JSON.stringify({source:"kairos-15m",scope,allow_unverified_submission:false}),signal:AbortSignal.timeout(45000)});
  if(!response.ok)return {status:502,body:{ok:false,reason:"Coordinador rechazó pulso",http_status:response.status}};
  return {status:202,body:{ok:true,accepted:true,scope,meaning:"Coordinador externo aceptó el pulso; no confirma envíos individuales"}};
 }catch{return {status:502,body:{ok:false,reason:"Coordinador no disponible"}};}
}
