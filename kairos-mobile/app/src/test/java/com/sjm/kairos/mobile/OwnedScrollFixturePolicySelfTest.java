package com.sjm.kairos.mobile;
public final class OwnedScrollFixturePolicySelfTest{
    public static void main(String[] args){
        if(!SjmNavigationPolicy.isAllowedUrl(OwnedScrollFixturePolicy.URL)||
           SjmNavigationPolicy.isAllowedUrl(OwnedScrollFixturePolicy.URL+"?x=1")||
           SjmNavigationPolicy.isAllowedUrl(OwnedScrollFixturePolicy.URL+"/")||
           !OwnedUrlProofPolicy.matches(OwnedScrollFixturePolicy.URL,OwnedScrollFixturePolicy.URL.substring(8))||
           OwnedScrollFixturePolicy.marker("SJM SCROLL INICIO")!=1||
           OwnedScrollFixturePolicy.marker("SJM SCROLL ABAJO VERIFICADO")!=2||
           OwnedScrollFixturePolicy.marker("x SJM SCROLL ABAJO VERIFICADO")!=0||
           !OwnedScrollFixturePolicy.proven(1,false,2)||
           !OwnedScrollFixturePolicy.proven(0,true,2)||
           OwnedScrollFixturePolicy.proven(0,false,2)||
           OwnedScrollFixturePolicy.proven(-1,true,2)||
           OwnedScrollFixturePolicy.proven(1,true,3)||
           OwnedScrollFixturePolicy.proven(1,true,1)||
           !AppWorkflowPolicy.isAllowedStep("run_sjm_scroll_fixture","","")||
           AppWorkflowPolicy.isAllowedStep("run_sjm_scroll_fixture","","arbitrary"))throw new AssertionError("fixture policy");
        System.out.println("OWNED_SCROLL_FIXTURE_POLICY 15/15 PASS");
    }
}
