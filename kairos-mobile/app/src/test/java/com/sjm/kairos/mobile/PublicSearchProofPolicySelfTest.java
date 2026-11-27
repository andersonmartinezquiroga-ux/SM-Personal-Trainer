package com.sjm.kairos.mobile;
public final class PublicSearchProofPolicySelfTest{
 public static void main(String[] args){
  String q="PRUEBA+KAIROS+360";
  if(!PublicSearchProofPolicy.matchesAddress("https://www.google.com/search?q="+q))throw new AssertionError("valid");
  if(!PublicSearchProofPolicy.matchesAddress("www.google.com.co/search?q="+q+"&hl=es"))throw new AssertionError("compact");
  String[] invalid={"https://evil.example/search?q="+q,"https://www.google.com.evil.example/search?q="+q,"https://www.google.com/search?q=other","https://www.google.com/search?q="+q+"&q=other","https://www.google.com/search?q="+q+"&q="+q,"https://www.google.com/?q="+q,"https://www.google.com@evil.example/search?q="+q,"PRUEBA KAIROS 360","http://www.google.com/search?q="+q};
  for(String v:invalid)if(PublicSearchProofPolicy.matchesAddress(v))throw new AssertionError("invalid accepted");
  if(!PublicSearchProofPolicy.isResultHeading("Resultados de búsqueda")||!PublicSearchProofPolicy.isResultHeading("Search results")||PublicSearchProofPolicy.isResultHeading("PRUEBA KAIROS 360"))throw new AssertionError("heading");
  System.out.println("PUBLIC_SEARCH_PROOF PASS");
 }
}
