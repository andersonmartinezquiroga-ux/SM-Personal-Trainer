package com.sjm.kairos.mobile;
/** Fixed report vocabulary only. No raw screen text exits the device. */
final class OwnedDiagnosticProof {
    static final String URL="https://sjm-kairos-conversacion-sjm-pruebas.vercel.app/";
    static final String HEADER="KAIRÓS 360 · PRUEBA LOCAL DEL NAVEGADOR";
    static final String[] LABELS={"Página segura HTTPS","WebAssembly para ejecución CPU",
        "WebGPU para ejecución GPU (opcional)","Reconocimiento de voz","Lectura de voz",
        "Modo CPU disponible en la interfaz","Laboratorio IA local disponible"};
    private int seen=0, available=0;
    private boolean header=false, model=false, generation=false, privacy=false, conflict=false;
    void observe(String text){
        if(text==null || text.length()>1800)return;
        for(String line:text.split("\\r?\\n")){
            String s=line.trim();
            if(s.equals(HEADER))header=true;
            if(s.equals("Modelo CPU descargado: SIN COMPROBAR."))model=true;
            if(s.equals("Generación independiente real: SIN COMPROBAR."))generation=true;
            if(s.equals("No se ha activado el micrófono ni enviado información del dispositivo."))privacy=true;
            for(int i=0;i<LABELS.length;i++){
                boolean yes=s.equals(LABELS[i]+": DISPONIBLE"),no=s.equals(LABELS[i]+": NO DISPONIBLE");
                if(!yes&&!no)continue;
                int bit=1<<i;
                if((seen&bit)!=0 && (((available&bit)!=0)!=yes))conflict=true;
                seen|=bit;if(yes)available|=bit;
            }
        }
    }
    String receipt(){
        if(conflict || !header || !model || !generation || !privacy || seen!=127)return null;
        return "SJM_BROWSER_DIAGNOSTIC_OBSERVED_MASK_"+available+"_MODEL_UNVERIFIED";
    }
}
