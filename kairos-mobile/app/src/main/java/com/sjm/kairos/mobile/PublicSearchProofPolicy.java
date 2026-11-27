package com.sjm.kairos.mobile;
import java.net.URI;
import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;
/** Verifies only the exact public test query and known search-results heading. */
final class PublicSearchProofPolicy {
    static final String BAR="id:com.android.chrome:id/url_bar";
    static final String QUERY="PRUEBA KAIROS 360";
    static boolean matchesAddress(CharSequence text){
        if(text==null||text.length()>2048)return false;
        try{
            String value=text.toString();
            URI u=new URI(value.startsWith("https://")?value:"https://"+value);
            String host=u.getHost();
            if(!"https".equals(u.getScheme())||u.getUserInfo()!=null||u.getPort()!=-1||
               !("www.google.com".equals(host)||"google.com".equals(host)||"www.google.com.co".equals(host)||"google.com.co".equals(host))||
               !"/search".equals(u.getRawPath())||u.getRawQuery()==null)return false;
            int matches=0;
            for(String part:u.getRawQuery().split("&")){
                int i=part.indexOf('=');
                if(i>0&&"q".equals(URLDecoder.decode(part.substring(0,i),StandardCharsets.UTF_8.name()))){
                    if(!QUERY.equals(URLDecoder.decode(part.substring(i+1),StandardCharsets.UTF_8.name())))return false;
                    matches++;
                }
            }
            return matches==1;
        }catch(Exception e){return false;}
    }
    static boolean isResultHeading(CharSequence text){
        return text!=null&&("Resultados de búsqueda".contentEquals(text)||"Search results".contentEquals(text));
    }
    static boolean isCompactQuery(CharSequence text){return text!=null&&QUERY.contentEquals(text);}
    static int resultTabMask(CharSequence text){
        if(text==null)return 0;
        String label=text.toString();
        switch(label){
            case "Todos":case "All":return 1;
            case "Imágenes":case "Images":return 2;
            case "Videos":case "Vídeos":return 4;
            case "Noticias":case "News":return 8;
            case "Herramientas":case "Tools":return 16;
            default:return 0;
        }
    }
    static boolean isVerified(boolean address,boolean heading,int tabs){
        return address&&(heading||Integer.bitCount(tabs&31)>=3);
    }
    static String failure(boolean address,boolean compact,boolean heading,int tabs){
        if(!address&&compact)return "PUBLIC_SEARCH_COMPACT_QUERY_ADDRESS_UNVERIFIED";
        if(!address)return "PUBLIC_SEARCH_EXACT_ADDRESS_UNVERIFIED";
        return "PUBLIC_SEARCH_ADDRESS_OBSERVED_RESULT_CONTENT_UNVERIFIED";
    }
}
