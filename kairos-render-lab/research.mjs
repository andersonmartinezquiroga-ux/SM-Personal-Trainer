// B4: consulta informativa pública, de solo lectura, sin IA generativa.
// No recibe credenciales, historiales ni URLs elegidas por el cliente.
const WIKI_API = "https://es.wikipedia.org/w/api.php";
const MAX_BODY_BYTES = 170000;
export function normalizePublicTopic(value) {
  if (typeof value !== "string" || value.length > 160) return null;
  // Validate raw input BEFORE trim() so leading/trailing controls cannot disappear.
  if (/[\u0000-\u001f\u007f<>]/u.test(value)) return null;
  const text = value.trim();
  if (text.length < 2 || text.length > 120 ||
      /@|https?:\/\//i.test(text) ||
      /(?:contraseñ|password|secret[oa]|api\s*key|private\s*key|\botp\b|c[oó]digo\s+de\s+verificaci[oó]n|pin\s+bancario|token\s+de\s+acceso|frase\s+semilla)/i.test(text)) return null;
  const topic = text.normalize("NFD").replace(/[\u0300-\u036f]/g, "")
    .replace(/^[¿?\s]*(?:que es|explicame que es|explica que es|cual es|hablame de|quiero saber sobre|dime sobre)\s+(?:el\s+|la\s+|los\s+|las\s+|un\s+|una\s+)?/i, "")
    .replace(/[¿?!.]+$/u, "").trim();
  return topic.length >= 2 && topic.length <= 120 ? topic : null;
}
export function parseWikiExtracts(data) {
  if (data?.error) throw new Error("Fuente enciclopédica rechazó consulta");
  const pages = Array.isArray(data?.query?.pages) ? data.query.pages : [];
  return pages.filter(x => x && Number.isInteger(x.pageid) && x.pageid > 0 && typeof x.title === "string")
    .slice(0,3)
    .map(x => {
      const title = x.title.trim().slice(0,130);
      return {
        title,
        excerpt: typeof x.extract === "string" ? x.extract.replace(/\s+/g," ").trim().slice(0,550) : "",
        url: "https://es.wikipedia.org/wiki/" + encodeURIComponent(title.replace(/ /g,"_"))
      };
    });
}
export async function publicKnowledge(input, requestFetch=fetch) {
  const topic = normalizePublicTopic(input);
  if (!topic) return {status:400,body:{ok:false,error:"Tema público inválido o sensible; no se envió"}};
  const url = new URL(WIKI_API);
  for(const [k,v] of Object.entries({
    action:"query",generator:"search",gsrsearch:topic,gsrlimit:"3",
    prop:"extracts",exintro:"1",explaintext:"1",exchars:"500",
    format:"json",formatversion:"2"
  })) url.searchParams.set(k,v);
  try {
    const response = await requestFetch(url.toString(),{
      method:"GET",redirect:"error",
      headers:{"accept":"application/json","user-agent":"SJM-Kairos-360/0.1 (public educational read-only research)"},
      signal:AbortSignal.timeout(10000)
    });
    if(!response.ok) throw new Error("upstream_http_"+response.status);
    const declared=Number(response.headers.get("content-length")||0);
    if(!Number.isFinite(declared)||declared>MAX_BODY_BYTES)throw new Error("Fuente demasiado extensa");
    const reader=response.body?.getReader();
    if(!reader) throw new Error("Fuente vacía");
    let total=0, parts=[];
    try {
      while(true) {
        const {done,value}=await reader.read();
        if(done)break;
        total+=value.byteLength;
        if(total>MAX_BODY_BYTES) {await reader.cancel().catch(()=>{});throw new Error("Fuente demasiado extensa");}
        parts.push(value);
      }
    }finally {reader.releaseLock();}
    const bytes=new Uint8Array(total);let offset=0;
    for(const part of parts){bytes.set(part,offset);offset+=part.length;}
    const data=JSON.parse(new TextDecoder("utf-8",{fatal:true}).decode(bytes));
    const entries=parseWikiExtracts(data);
    return {status:200,body:{
      ok:true,mode:"public_sources_not_generative",topic,source:"Wikipedia en español",
      sources:entries,readOnly:true,generatedByLLM:false,executedActions:0,
      disclaimer:"Los extractos son de la enciclopedia, no respuestas generadas ni hechos verificados independientemente."
    }};
  }catch (err) {
    // Safe diagnostics: no query, headers, URLs, user content or stack traces.
    const raw=String(err?.message||"");
    const upstream=/^upstream_http_(\d{3})$/.exec(raw);
    const failure_class=upstream?"upstream_http_"+upstream[1]:
      err?.name==="TimeoutError"||err?.name==="AbortError"?"timeout":
      raw==="Fuente demasiado extensa"?"content_too_large":
      err instanceof SyntaxError?"invalid_json":"source_unavailable";
    return {status:503,body:{ok:false,error:"No se pudo consultar la fuente pública. No se inventaron resultados.",failure_class,readOnly:true,generatedByLLM:false,executedActions:0}};
  }
}
