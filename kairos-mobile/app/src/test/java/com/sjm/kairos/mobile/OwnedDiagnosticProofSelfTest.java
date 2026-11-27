package com.sjm.kairos.mobile;
public final class OwnedDiagnosticProofSelfTest {
    public static void main(String[] args){
        OwnedDiagnosticProof p=new OwnedDiagnosticProof();
        p.observe("Pulse Comprobar mi dispositivo. No se han realizado pruebas.");
        if(p.receipt()!=null)throw new AssertionError("initial state");
        p.observe(OwnedDiagnosticProof.HEADER);
        for(int i=0;i<7;i++)p.observe(OwnedDiagnosticProof.LABELS[i]+(i==2?": NO DISPONIBLE":": DISPONIBLE"));
        if(p.receipt()!=null)throw new AssertionError("partial proof");
        p.observe("Modelo CPU descargado: SIN COMPROBAR.\nGeneración independiente real: SIN COMPROBAR.\nNo se ha activado el micrófono ni enviado información del dispositivo.");
        if(!"SJM_BROWSER_DIAGNOSTIC_OBSERVED_MASK_123_MODEL_UNVERIFIED".equals(p.receipt()))throw new AssertionError("exact report");
        p.observe(OwnedDiagnosticProof.LABELS[2]+": DISPONIBLE");
        if(p.receipt()!=null)throw new AssertionError("contradictory evidence");
        if(!AppWorkflowPolicy.isAllowedStep("verify_sjm_diagnostic","","") ||
            AppWorkflowPolicy.isAllowedStep("verify_sjm_diagnostic","text:secret","") ||
            AppWorkflowPolicy.isAllowedStep("verify_sjm_diagnostic","","arbitrary"))
            throw new AssertionError("read-only action scope");
        if(!AppWorkflowPolicy.isAllowedStep("run_sjm_diagnostic","","") || AppWorkflowPolicy.isAllowedStep("run_sjm_diagnostic","text:secret","") || AppWorkflowPolicy.isAllowedStep("run_sjm_diagnostic","","arbitrary"))throw new AssertionError("atomic diagnostic scope");
        System.out.println("SJM_DIAGNOSTIC_PROOF PASS");
    }
}
