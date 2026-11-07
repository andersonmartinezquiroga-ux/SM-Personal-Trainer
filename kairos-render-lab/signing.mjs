import {createPublicKey, verify as verifyRsa} from "node:crypto";
const JWKS_URL = "https://token.actions.githubusercontent.com/.well-known/jwks";
const ISSUER = "https://token.actions.githubusercontent.com";
const REPOSITORY = "andersonmartinezquiroga-ux/SM-Personal-Trainer";
const WORKFLOW = ".github/workflows/kairos-android-build.yml";
const AUDIENCE = "sjm-kairos-signing-v1";
const DEFAULT_REF = "refs/heads/feature/kairos-mobile-v03";

let cache = {at:0,keys:[]};
async function publicKeys() {
 if (Date.now()-cache.at<300_000 && cache.keys.length) return cache.keys;
 const response = await fetch(JWKS_URL,{signal:AbortSignal.timeout(8000)});
 if(!response.ok) throw new Error("No fue posible verificar GitHub");
 const json = await response.json();
 if(!Array.isArray(json.keys)||json.keys.length>60)throw new Error("JWKS inválido");
 cache = {at:Date.now(),keys:json.keys};
 return cache.keys;
}
/**
 * Validación criptográfica OIDC de GitHub Actions, no simplemente decodificar JWT.
 * Solo el workflow y rama permitidos pueden solicitar el certificado privado.
 */
export async function isAuthorizedGithubBuild(rawToken){
 try {
  if(typeof rawToken!=="string"||rawToken.length>8500)return false;
  const parts=rawToken.split(".");
  if(parts.length!==3)return false;
  const [h,p,s]=parts;
  const header=JSON.parse(Buffer.from(h,"base64url").toString("utf8"));
  const payload=JSON.parse(Buffer.from(p,"base64url").toString("utf8"));
  if(header.alg!=="RS256"||typeof header.kid!=="string")return false;
  if(payload.iss!==ISSUER||payload.aud!==AUDIENCE||payload.repository!==REPOSITORY)return false;
  const allowedRef=process.env.KAIROS_SIGNING_ALLOWED_REF||DEFAULT_REF;
  const expectedSubjects = new Set([
    `repo:${REPOSITORY}:ref:${allowedRef}`,
    `repo:andersonmartinezquiroga-ux@317761897/SM-Personal-Trainer@1340977588:ref:${allowedRef}`
  ]);
  if(payload.ref!==allowedRef || !expectedSubjects.has(payload.sub))return false;
  if(payload.repository_id!=="1340977588" || payload.repository_owner_id!=="317761897")return false;
  if(payload.workflow_ref!==`${REPOSITORY}/${WORKFLOW}@${allowedRef}`)return false;
  const now=Math.floor(Date.now()/1000);
  if(typeof payload.iat!=="number"||typeof payload.exp!=="number" ||
     payload.exp<now||payload.iat>now+30||now-payload.iat>600 ||
     payload.exp-payload.iat>900)return false;
  const keys=await publicKeys();
  const jwk=keys.find(k=>k.kid===header.kid&&k.kty==="RSA"&&(!k.alg||k.alg==="RS256"));
  if(!jwk)return false;
  const key=createPublicKey({key:jwk,format:"jwk"});
  return verifyRsa("RSA-SHA256",Buffer.from(h+"."+p),key,Buffer.from(s,"base64url"));
 }catch{return false;}
}
export function haveSigningMaterial() {
 const key=process.env.KAIROS_KEYSTORE_B64||"";
 const password=process.env.KAIROS_SIGNING_STORE_PASS||"";
 const alias=process.env.KAIROS_SIGNING_ALIAS||"";
 return key.length>1000 && password.length>=16 && /^[a-zA-Z0-9_-]{4,40}$/.test(alias);
}
export function signingMaterialForAuthorizedBuild(){
 if(!haveSigningMaterial())throw new Error("Firma estable aún no preparada");
 return {keystoreBase64:process.env.KAIROS_KEYSTORE_B64,
         storePassword:process.env.KAIROS_SIGNING_STORE_PASS,
         keyAlias:process.env.KAIROS_SIGNING_ALIAS,
         keyPassword:process.env.KAIROS_SIGNING_STORE_PASS};
}
