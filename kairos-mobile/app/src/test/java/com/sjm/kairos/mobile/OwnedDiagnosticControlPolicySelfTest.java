package com.sjm.kairos.mobile;
public final class OwnedDiagnosticControlPolicySelfTest {
    public static void main(String[] args){
        String run=OwnedDiagnosticControlPolicy.RUN,expand=OwnedDiagnosticControlPolicy.EXPAND;
        if(!OwnedDiagnosticControlPolicy.matches(run,run,null))throw new AssertionError("text");
        if(!OwnedDiagnosticControlPolicy.matches(run,null,run))throw new AssertionError("description");
        if(!OwnedDiagnosticControlPolicy.matches(expand,null,"Comprobar compatibilidad de este dispositivo\u00a0(sin descargas)"))throw new AssertionError("normalized description");
        if(OwnedDiagnosticControlPolicy.matches(run,"Pulsar "+run,null))throw new AssertionError("prefix denied");
        if(OwnedDiagnosticControlPolicy.matches(run,null,run+" y enviar datos"))throw new AssertionError("suffix denied");
        if(OwnedDiagnosticControlPolicy.matches("Guardar contraseña","Guardar contraseña",null))throw new AssertionError("unapproved label");
        if(OwnedDiagnosticControlPolicy.matches(run,expand,null))throw new AssertionError("different action");
        if(OwnedDiagnosticControlPolicy.matches(run,null,null))throw new AssertionError("empty");
        System.out.println("OWNED_DIAGNOSTIC_CONTROL_POLICY PASS 8 cases");
    }
}
