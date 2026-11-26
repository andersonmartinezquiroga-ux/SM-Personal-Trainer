import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2.76.1";

// KAIRÓS v0.3.6 fallback: narrow, private Motorola connector.
const headers = {
  "Content-Type": "application/json; charset=utf-8",
  "Cache-Control": "no-store, private",
  "X-Content-Type-Options": "nosniff",
  "Referrer-Policy": "no-referrer"
};
const out = (data: Record<string,unknown>, status=200) =>
  new Response(JSON.stringify(data), {status,headers});
const encoder = new TextEncoder();
async function sha256(s:string):Promise<string>{
  const bytes = new Uint8Array(await crypto.subtle.digest("SHA-256",encoder.encode(s)));
  return Array.from(bytes).map(x=>x.toString(16).padStart(2,"0")).join("");
}
function randomHex(n:number):string{
  const b=crypto.getRandomValues(new Uint8Array(n));
  return Array.from(b).map(x=>x.toString(16).padStart(2,"0")).join("");
}

// Must match VoiceActionPolicy and local Android audio-mode checks.
function safeConcurrentChrome(payload:any):boolean{
  if(!payload || payload.package!=="com.android.chrome" || !Array.isArray(payload.steps) ||
      payload.steps.length<1 || payload.steps.length>8)return false;
  return payload.steps.every((s:any)=>{
    if(!s || typeof s!=="object" || typeof s.action!=="string" ||
       Object.keys(s).some(k=>!["action","selector","value"].includes(k)))return false;
    const selector=s.selector??"", value=s.value??"";
    if(typeof selector!=="string" || typeof value!=="string")return false;
    if(s.action==="wait")return selector==="" && ["400","800","1200"].includes(value);
    if(["scroll_up","scroll_down"].includes(s.action))return selector==="" && value==="";
    if(!["id:com.android.chrome:id/url_bar","id:com.android.chrome:id/search_box_text"].includes(selector))return false;
    if(s.action==="type")return value.length>0 && value.length<=400 && !value.includes("\u0000");
    return ["tap","ime_search"].includes(s.action) && value==="";
  });
}

const MAX_JSON=4096;
async function bodyOf(req:Request):Promise<any>{
  const t=await req.text();
  if(t.length>MAX_JSON)throw new Error("Petición demasiado extensa");
  const o=JSON.parse(t);
  if(!o||typeof o!=="object"||Array.isArray(o))throw new Error("Objeto inválido");
  return o;
}
Deno.serve(async (req:Request)=>{
  if(req.method!=="GET"&&req.method!=="POST")return out({ok:false,error:"Método no permitido"},405);
  const u=new URL(req.url);
  const path=u.searchParams.get("path")||"";
  const expectedPaths=[
    "/_api/kairos/executor_claim",
    "/_api/kairos/phone_executor",
    "/_api/kairos/phone_command_poll",
    "/_api/kairos/phone_command_ack"
  ];
  if(!expectedPaths.includes(path))return out({ok:false,error:"Ruta no permitida"},404);
  if((path.endsWith("poll") && req.method!=="GET") ||
     (!path.endsWith("poll")&&req.method!=="POST"))
    return out({ok:false,error:"Método no permitido"},405);
  const url=Deno.env.get("SUPABASE_URL")||"";
  const secret=Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")||"";
  if(!url||!secret)return out({ok:false,error:"Servicio no configurado"},503);
  const db=createClient(url,secret,{auth:{autoRefreshToken:false,persistSession:false}});
  try{
    if(path.endsWith("executor_claim")){
      const input=await bodyOf(req);
      const code=String(input.code||"").replace(/-/g,"").trim().toUpperCase();
      if(!/^[0-9A-F]{10}$/.test(code))return out({ok:false,error:"Código inválido"},400);
      const hash=await sha256(code);
      const {data:pair,error:pe}=await db.from("sjm_kairos_phone_codes_v1")
        .select("code_hash,owner_id,expires_at,used_at").eq("code_hash",hash).maybeSingle();
      if(pe)return out({ok:false,error:"Verificación no disponible"},503);
      if(!pair||pair.used_at||new Date(pair.expires_at).getTime()<=Date.now())
        return out({ok:false,error:"Código no válido, ya utilizado o vencido"},403);
      // Single use, conditionally consume; two competing requests cannot both win.
      const {data:claimed,error:ce}=await db.from("sjm_kairos_phone_codes_v1")
        .update({used_at:new Date().toISOString()})
        .eq("code_hash",hash).is("used_at",null)
        .gt("expires_at",new Date().toISOString())
        .select("owner_id").maybeSingle();
      if(ce||!claimed)return out({ok:false,error:"Código ya utilizado"},403);
      const executorKey=randomHex(32);
      const {data:device,error:de}=await db.from("sjm_kairos_phone_devices_v1")
        .insert({owner_id:claimed.owner_id,token_hash:await sha256(executorKey),
          version:1,capabilities:["notify","open_app","open_url"]})
        .select("device_id").single();
      if(de||!device)return out({ok:false,error:"No se pudo registrar el Motorola. Genere otro código."},503);
      await db.from("sjm_kairos_phone_codes_v1")
        .update({device_id:device.device_id}).eq("code_hash",hash);
      return out({ok:true,executorKey,deviceId:device.device_id,
        message:"Vinculación segura realizada; falta activar registro y prueba remota."});
    }
    const key=String(req.headers.get("x-kairos-executor-key")||"");
    if(!/^[a-f0-9]{64}$/.test(key))return out({ok:false,error:"Motorola no autorizado"},401);
    const {data:device,error:le}=await db.from("sjm_kairos_phone_devices_v1")
      .select("device_id,owner_id,enabled,app_version,capabilities").eq("token_hash",await sha256(key)).maybeSingle();
    if(le)return out({ok:false,error:"Autorización temporalmente no disponible"},503);
    if(!device||!device.enabled)return out({ok:false,error:"Motorola no autorizado"},401);
    if(path.endsWith("phone_executor")){
      const input=await bodyOf(req);
      if(input.action!=="register"||input.version!==1||!Array.isArray(input.capabilities))
        return out({ok:false,error:"Registro no compatible"},400);
      const permitted=["notify","open_app","open_url","app_workflow","concurrent_chrome"];
      const capabilities=input.capabilities.filter((x:unknown)=>typeof x==="string"&&permitted.includes(x));
      // Protocol v1 is separate from Android APK release version. No secrets are reported.
      const appVersion=typeof input.appVersion==="string" &&
         /^[0-9]+[.][0-9]+[.][0-9]+$/.test(input.appVersion) &&
         input.appVersion.length<=20 ? input.appVersion : null;
      const patch: Record<string,unknown>={
        last_seen_at:new Date().toISOString(),version:1,capabilities
      };
      if(appVersion) patch.app_version=appVersion;
      const {error:e}=await db.from("sjm_kairos_phone_devices_v1")
        .update(patch)
        .eq("device_id",device.device_id);
      if(e)return out({ok:false,error:"Registro no confirmado"},503);
      return out({ok:true,connected:true,message:"CONTROL 360 alternativo: Motorola registrado por Supabase"});
    }
    if(path.endsWith("phone_command_poll")){
      // VOICE_STATUS_REPORT_0326: authenticated APK-only, boolean state;
      // never transmit audio, recording, transcript or app content.
      // Old Android versions omit this parameter and remain compatible.
      const voiceState=u.searchParams.get("voice");
      const checkedAt=new Date().toISOString();
      const seenPatch: Record<string,unknown>={
        last_seen_at:checkedAt,last_poll_at:checkedAt
      };
      if(voiceState==="busy"||voiceState==="free"){
        seenPatch.last_voice_busy=voiceState==="busy";
        seenPatch.last_voice_status_at=checkedAt;
      }
      const {error:seenErr}=await db.from("sjm_kairos_phone_devices_v1")
        .update(seenPatch).eq("device_id",device.device_id);
      if(seenErr)return out({ok:false,error:"Latido no confirmado"},503);
      // Modo clase: mantener solo el latido; no entregar aperturas ni avisos.
      const {data:gate,error:gateError}=await db.from("sjm_kairos_phone_execution_gates_v1")
        .select("pause_open_app,pause_notifications").eq("device_id",device.device_id).maybeSingle();
      // Fallar cerrado: ante un error de política, no entregar aperturas.
      const pauseApps=!!gateError || !gate || gate.pause_open_app===true;
      const pauseNotices=!!gateError || !gate || gate.pause_notifications===true;
      let commandQuery=db.from("sjm_kairos_phone_jobs_v1")
        .select("id,type,payload").eq("device_id",device.device_id)
        .eq("status","queued")
        // No entregar órdenes viejas aunque el cron todavía no haya expirado.
        .gte("created_at",new Date(Date.now()-10*60_000).toISOString())
        // Reject stale per-job deadlines before offering a command to Android.
        // The SQL ACK function independently blocks expired receipts as well.
        .or("timeout_at.is.null,timeout_at.gt."+new Date().toISOString());
      if(pauseApps) commandQuery=commandQuery
        .neq("type","open_app").neq("type","open_url").neq("type","speak").neq("type","local_test").neq("type","app_workflow");
      if(!["0.3.11","0.3.12","0.3.13","0.3.14","0.3.15","0.3.16","0.3.17","0.3.18","0.3.19","0.3.20","0.3.21","0.3.22","0.3.23","0.3.24","0.3.25","0.3.26","0.3.27","0.3.28","0.3.29","0.3.30"].includes(device.app_version)) commandQuery=commandQuery.neq("type","local_test");
      // A pre-0.3.19 Motorola must never receive new multi-app steps.
      // Nunca mandar un flujo multi-paso si el ejecutor no declaró soporte real.
      // Evita que una APK antigua reciba tareas que rechaza y genere falsos fallos.
      if(!Array.isArray(device.capabilities)||!device.capabilities.includes("app_workflow"))
        commandQuery=commandQuery.neq("type","app_workflow");
      if(!["0.3.19","0.3.20","0.3.21","0.3.22","0.3.23","0.3.24","0.3.25","0.3.26","0.3.27","0.3.28","0.3.29","0.3.30"].includes(device.app_version)) commandQuery=commandQuery.neq("type","app_workflow");
      // A voice call must never receive screen-changing commands.
      // Leave existing queued jobs untouched to preserve ACK/idempotency semantics.
      const concurrentChrome=voiceState==="busy" && !pauseApps &&
        u.searchParams.get("concurrent")==="chrome" && device.app_version==="0.3.30" &&
        Array.isArray(device.capabilities) && device.capabilities.includes("concurrent_chrome") &&
        device.capabilities.includes("app_workflow");
      if(voiceState==="busy"){
        commandQuery=commandQuery.in("type",concurrentChrome?["notify","app_workflow"]:["notify"]);
      }
      if(pauseNotices) commandQuery=commandQuery.neq("type","notify");
      const {data:jobs,error:je}=await commandQuery
        .order("created_at",{ascending:true}).limit(concurrentChrome?50:1);
      if(je)return out({ok:false,error:"Cola no disponible"},503);
      const job=concurrentChrome?jobs?.find(j=>j.type==="notify" || safeConcurrentChrome(j.payload)):jobs?.[0];
      return out(job?{ok:true,shouldExecute:true,command:job}
        :{ok:true,shouldExecute:false});
    }
    if(path.endsWith("phone_command_ack")){
      const input=await bodyOf(req);
      const commandId=String(input.commandId||"");
      const result=String(input.result||"");
      if(!/^[0-9a-fA-F-]{36}$/.test(commandId) ||
          !["received","completed","failed"].includes(result))
        return out({ok:false,error:"Acuse inválido"},400);
      const {data:found,error:fe}=await db.from("sjm_kairos_phone_jobs_v1")
        .select("id,status,received_at,timeout_at,result_message").eq("id",commandId).eq("device_id",device.device_id).maybeSingle();
      if(fe)return out({ok:false,error:"No se pudo consultar la orden"},503);
      if(!found)return out({ok:false,error:"Orden ajena o inexistente"},404);
      // Terminal ACKs are only idempotent when they match the stored outcome.
      // A cancelled job must NEVER respond OK to a stale "received" ACK.
      if(["completed","failed"].includes(found.status)) {
        // A completed/failed receipt can arrive after the safe no-retry timeout.
        // Only the original authorized Android executor can reconcile it.
        if(found.status==="failed" && result!=="received" &&
           found.received_at && found.timeout_at &&
           String(found.result_message||"").startsWith("EXECUTION_OUTCOME_UNKNOWN:")) {
          const {data:late,error:lateError}=await db.rpc(
            "sjm_kairos_phone_reconcile_late_ack_v1",{
              p_device_id:device.device_id,p_job_id:commandId,
              p_result:result,p_message:String(input.message||"").slice(0,280)
            });
          if(lateError)return out({ok:false,error:"No se pudo conciliar recibo tardío"},503);
          if(late?.accepted===true)
            return out({ok:true,status:late.status,lateReceipt:true,
                        duplicate:late.reused===true});
          return out({ok:false,error:"El recibo tardío fue rechazado"},409);
        }
        if(result==="received" || found.status!==result || !found.received_at)
          return out({ok:false,error:"La orden ya está cerrada; no ejecutar"},409);
        return out({ok:true,status:found.status,duplicate:true});
      }
      if(result==="received"){
        // Atomic Postgres check: owner pause, 10-minute TTL, job lock,
        // then status update. Prevents racing cancellation vs Android execution.
        const {data:receipt,error:re}=await db.rpc(
          "sjm_kairos_phone_receive_authorized_v1",{
            p_device_id:device.device_id,p_job_id:commandId
        });
        if(re)return out({ok:false,error:"No se pudo autorizar recepción"},503);
        if(receipt?.accepted!==true)
          return out({ok:false,error:"Orden cerrada, pausada o vencida; no ejecutar",
                      reason:receipt?.reason||"denied"},409);
        return out({ok:true,status:"received"});
      }
      // Android may only claim completion AFTER the server accepted receipt.
      if(found.status!=="received")
        return out({ok:false,error:"Orden sin recepción autorizada; no ejecutar"},409);
      const {data:updated,error:ue}=await db.from("sjm_kairos_phone_jobs_v1")
        .update({status:result,completed_at:new Date().toISOString(),
                 result_message:String(input.message||"").slice(0,280)})
        .eq("id",commandId).eq("device_id",device.device_id)
        .eq("status","received")
        .select("id").maybeSingle();
      if(ue)return out({ok:false,error:"No se pudo confirmar resultado"},503);
      if(!updated)return out({ok:false,error:"La orden cambió de estado"},409);
      return out({ok:true,status:result});
    }
    return out({ok:false,error:"Ruta no permitida"},404);
  }catch(e){
    return out({ok:false,error:"No se pudo completar la operación"},500);
  }
});