package com.sjm.kairos.mobile;

/** Only an exact owner-allowed HTTPS address, not a prefix or typed lookalike. */
final class OwnedUrlProofPolicy {
    private OwnedUrlProofPolicy(){}
    static boolean matches(String expected,String observed){
        if(!SjmNavigationPolicy.isAllowedUrl(expected) || observed==null)return false;
        String actual=observed.trim();
        if(actual.isEmpty() || actual.length()>300)return false;
        if(!actual.contains("://"))actual="https://"+actual;
        if(actual.equals(expected))return true;
        return expected.endsWith("/") && actual.equals(expected.substring(0,expected.length()-1))
            && java.net.URI.create(expected).getRawPath().equals("/");
    }
}
