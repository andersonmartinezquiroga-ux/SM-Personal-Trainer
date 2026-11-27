package com.sjm.kairos.mobile;
/** Fixed report vocabulary only. No raw screen text exits the device. */
final class OwnedDiagnosticProof {
    static final String URL="https://sjm-kairos-conversacion-sjm-pruebas.vercel.app/";
    static final String HEADER="KAIRÓS 360 · PRUEBA LOCAL DEL NAVEGADOR";
    static final String[] LABELS={"Página segura HTTPS","WebAssembly para ejecución CPU",
        "WebGPU para ejecución GPU (opcional)","Reconocimiento de voz","Lectura de voz",
        "Modo CPU disponible en la interfaz","Laboratorio IA local disponible"};
    private static final String MODEL="Modelo CPU descargado: SIN COMPROBAR.";
    private static final String GENERATION="Generación independiente real: SIN COMPROBAR.";
    private static final String PRIVACY="No se ha activado el micrófono ni enviado información del dispositivo.";
    private static final java.util.regex.Pattern COMPLETE=completePattern();
    private static java.util.regex.Pattern completePattern(){
        StringBuilder p=new StringBuilder("^").append(java.util.regex.Pattern.quote(HEADER));
        for(String label:LABELS)p.append(" ").append(java.util.regex.Pattern.quote(label+": ")).append("(NO DISPONIBLE|DISPONIBLE)");
        p.append(" ").append(java.util.regex.Pattern.quote(MODEL+" "+GENERATION+" "+PRIVACY)).append("$");
        return java.util.regex.Pattern.compile(p.toString());
    }
    private int seen=0, available=0;
    private boolean header=false, model=false, generation=false, privacy=false, conflict=false;
    void observe(String text){
        if(text==null || text.length()>1800)return;
        // Chrome may flatten whitespace into a single accessibility text or description.
        // Accept a complete ordered report, never arbitrary substring matches.
        String flat=normalize(text);
        java.util.regex.Matcher full=COMPLETE.matcher(flat);
        if(full.matches()){
            header=model=generation=privacy=true;
            for(int i=0;i<LABELS.length;i++)record(i,"DISPONIBLE".equals(full.group(i+1)));
            return;
        }
        for(String line:text.split("\\r?\\n")){
            String s=normalize(line);
            if(s.equals(HEADER))header=true;
            if(s.equals("Modelo CPU descargado: SIN COMPROBAR."))model=true;
            if(s.equals("Generación independiente real: SIN COMPROBAR."))generation=true;
            if(s.equals("No se ha activado el micrófono ni enviado información del dispositivo."))privacy=true;
            for(int i=0;i<LABELS.length;i++){
                boolean yes=s.equals(LABELS[i]+": DISPONIBLE"),no=s.equals(LABELS[i]+": NO DISPONIBLE");
                if(!yes&&!no)continue;
                record(i,yes);
            }
        }
    }
    private static String normalize(String text){
        return text.replaceAll("[\\s\\p{Z}]+"," ").trim();
    }
    private void record(int i,boolean yes){
        int bit=1<<i;
        if((seen&bit)!=0 && (((available&bit)!=0)!=yes))conflict=true;
        seen|=bit;if(yes)available|=bit;
    }
    String failureCode(){
        if(conflict)return "SJM_DIAGNOSTIC_REPORT_CONFLICT";
        if(!header)return "SJM_DIAGNOSTIC_HEADER_NOT_OBSERVED";
        return "SJM_DIAGNOSTIC_REPORT_INCOMPLETE";
    }
    String receipt(){
        if(conflict || !header || !model || !generation || !privacy || seen!=127)return null;
        return "SJM_BROWSER_DIAGNOSTIC_OBSERVED_MASK_"+available+"_MODEL_UNVERIFIED";
    }
}
