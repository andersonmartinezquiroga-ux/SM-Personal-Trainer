export const SAFE_APPS = new Set(["com.arlosoft.macrodroid","com.android.chrome","com.google.android.gm"]);
export const SAFE_PAGES = new Set(["/","/mentor","/kairos","/estado","/secretario","/expedientes","/sjm-panel-8"]);
export const ALLOWED = new Set(["notify","open_app","open_url"]);
export function normalizeCommand(input){
 if(!input || typeof input!=="object" || Array.isArray(input))return null;
 const keys=Object.keys(input);
 if(typeof input.type!=="string"||!ALLOWED.has(input.type))return null;
 if(input.type==="notify"){
   if(keys.some(k=>!["type","message"].includes(k)))return null;
   const m=input.message;
   if(typeof m!=="string" || m.trim().length<3||m.length>280||/[\u0000-\u001f\u007f]/.test(m))return null;
   return {type:"notify",payload:{message:m.trim()}};
 }
 if(input.type==="open_app"){
   if(keys.some(k=>!["type","package"].includes(k)) || !SAFE_APPS.has(input.package))return null;
   return {type:"open_app",payload:{package:input.package}};
 }
 if(input.type==="open_url"){
   if(keys.some(k=>!["type","url"].includes(k)) || typeof input.url!=="string"||input.url.length>300)return null;
   try{
    const u=new URL(input.url);
    if(u.protocol!=="https:"||u.hostname!=="sjm-control-360.floot.app"||u.port||
       u.username||u.password||u.search||u.hash||!SAFE_PAGES.has(u.pathname))return null;
    return {type:"open_url",payload:{url:u.href}};
   }catch{return null;}
 }
 return null;
}
