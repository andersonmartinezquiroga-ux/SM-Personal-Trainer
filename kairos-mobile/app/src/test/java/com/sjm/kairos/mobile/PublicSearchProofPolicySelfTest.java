package com.sjm.kairos.mobile;
public final class PublicSearchProofPolicySelfTest{
 public static void main(String[] args){
  String q="PRUEBA+KAIROS+360";
  if(!PublicSearchProofPolicy.matchesAddress("https://www.google.com/search?q="+q))throw new AssertionError("valid");
  if(!PublicSearchProofPolicy.matchesAddress("www.google.com.co/search?q="+q+"&hl=es"))throw new AssertionError("compact");
  String[] invalid={"https://evil.example/search?q="+q,"https://www.google.com.evil.example/search?q="+q,"https://www.google.com/search?q=other","https://www.google.com/search?q="+q+"&q=other","https://www.google.com/search?q="+q+"&q="+q,"https://www.google.com/?q="+q,"https://www.google.com@evil.example/search?q="+q,"PRUEBA KAIROS 360","http://www.google.com/search?q="+q};
  for(String v:invalid)if(PublicSearchProofPolicy.matchesAddress(v))throw new AssertionError("invalid accepted");
  if(!PublicSearchProofPolicy.isResultHeading("Resultados de búsqueda")||!PublicSearchProofPolicy.isResultHeading("Search results")||PublicSearchProofPolicy.isResultHeading("PRUEBA KAIROS 360"))throw new AssertionError("heading");
  if(PublicSearchProofPolicy.isVerified(false,true,31))throw new AssertionError("host must be proved");
  if(PublicSearchProofPolicy.isVerified(true,false,3))throw new AssertionError("only two tabs");
  if(!PublicSearchProofPolicy.isVerified(true,false,7))throw new AssertionError("three distinct tabs");
  if(!PublicSearchProofPolicy.isVerified(true,true,0))throw new AssertionError("exact heading");
  if(!PublicSearchProofPolicy.isCompactQuery("PRUEBA KAIROS 360"))throw new AssertionError("compact");
  if(PublicSearchProofPolicy.resultTabMask("Imágenes")!=2||PublicSearchProofPolicy.resultTabMask("Ver Imágenes")!=0)throw new AssertionError("exact tab");
  if(!PublicSearchProofPolicy.failure(false,true,true,31).equals("PUBLIC_SEARCH_COMPACT_QUERY_ADDRESS_UNVERIFIED"))throw new AssertionError("partial not success");
  System.out.println("PUBLIC_SEARCH_PROOF PASS");
 }
}
