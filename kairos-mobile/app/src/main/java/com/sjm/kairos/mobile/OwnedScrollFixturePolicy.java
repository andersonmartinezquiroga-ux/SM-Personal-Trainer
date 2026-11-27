package com.sjm.kairos.mobile;
final class OwnedScrollFixturePolicy{
    static final String URL="https://sjm-kairos-cerebro-ojklw4z94-sjm-pruebas.vercel.app/src/scroll-proof.html";
    static int marker(CharSequence value){
        if(value==null||value.length()>80)return 0;
        String s=value.toString().trim();
        if("SJM SCROLL INICIO".equals(s))return 1;
        if("SJM SCROLL ABAJO VERIFICADO".equals(s))return 2;
        return 0;
    }
    static boolean proven(int address,boolean same,int markers){
        return (address==1||(address==0&&same))&&markers==2;
    }
}
