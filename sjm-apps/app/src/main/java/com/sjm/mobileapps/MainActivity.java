package com.sjm.mobileapps;

import android.Manifest;
import android.app.Activity;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Bundle;
import android.speech.RecognitionListener;
import android.speech.RecognizerIntent;
import android.speech.SpeechRecognizer;
import android.speech.tts.TextToSpeech;
import android.webkit.JavascriptInterface;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.webkit.WebResourceRequest;
import android.graphics.Color;
import android.widget.Toast;
import org.json.JSONObject;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Locale;

public final class MainActivity extends Activity {
    private WebView page;
    private SpeechRecognizer listener;
    private TextToSpeech speaker;
    private volatile boolean speakerReady = false;
    private String requestedLanguage = "es-CO";
    private static final int MICROPHONE_PERMISSION = 1092;
    private static final String BOOT_JS =
        "(function(){" +
        "window.SpeechSynthesisUtterance=window.SpeechSynthesisUtterance||function(t){this.text=t;this.lang='es-CO';this.rate=1};" +
        "if(!window.speechSynthesis)window.speechSynthesis={cancel:function(){SJMAndroid.stopAudio()},getVoices:function(){return []},speak:function(u){SJMAndroid.speak(u.text,u.lang,u.rate)}};" +
        "function NativeRecognizer(){this.lang='es-CO';this.onresult=null;this.onerror=null;this.onend=null;}" +
        "NativeRecognizer.prototype.start=function(){window.__sjmCurrentRecognition=this;SJMAndroid.startSpeech(this.lang)};" +
        "NativeRecognizer.prototype.stop=function(){SJMAndroid.stopSpeech()};" +
        "window.SpeechRecognition=NativeRecognizer;window.webkitSpeechRecognition=NativeRecognizer;" +
        "window.sjmTranslateRemote=function(text,from,to){return new Promise(function(resolve,reject){" +
        "window.__sjmTranslationCallback=function(ok,val){if(ok){try{resolve(JSON.parse(val))}catch(e){reject(e)}}else reject(Error(val))};" +
        "SJMAndroid.translateRemote(text,from,to);" +
        "})};" +
        "})()";

    @Override public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().setStatusBarColor(Color.rgb(10,18,31));
        page=new WebView(this);
        WebSettings settings=page.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(true);
        settings.setAllowFileAccessFromFileURLs(false);
        settings.setAllowUniversalAccessFromFileURLs(false);
        settings.setMediaPlaybackRequiresUserGesture(false);
        page.setBackgroundColor(Color.rgb(10,18,31));
        page.addJavascriptInterface(new AndroidInterface(), "SJMAndroid");
        page.setWebViewClient(new WebViewClient() {
            @Override public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                Uri uri=request.getUrl();
                if(uri==null)return true;
                if("file".equals(uri.getScheme()) && "android_asset".equals(uri.getAuthority()))return false;
                if("https".equals(uri.getScheme()) || "http".equals(uri.getScheme())) {
                    try { startActivity(new Intent(Intent.ACTION_VIEW,uri)); }catch(Exception ignored){}
                }
                return true;
            }
            @Override public void onPageFinished(WebView view,String url) {
                if(url!=null && url.startsWith("file:///android_asset/"))
                    view.evaluateJavascript(BOOT_JS, null);
            }
        });
        setContentView(page);
        speaker=new TextToSpeech(getApplicationContext(), result->{
            speakerReady=(result==TextToSpeech.SUCCESS);
        });
        page.loadUrl("file:///android_asset/index.html");
    }

    private void javaScript(String body) {
        runOnUiThread(()->{
            if(page!=null)page.evaluateJavascript(body,null);
        });
    }
    private void microphoneStart(String language) {
        requestedLanguage=(language!=null && language.length()<18)?language:"es-CO";
        if(checkSelfPermission(Manifest.permission.RECORD_AUDIO)!=PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.RECORD_AUDIO}, MICROPHONE_PERMISSION);
            return;
        }
        if(!SpeechRecognizer.isRecognitionAvailable(this)) {
            speechError("El teléfono no tiene servicio de reconocimiento de voz disponible");
            return;
        }
        if(listener!=null){listener.cancel();listener.destroy();}
        listener=SpeechRecognizer.createSpeechRecognizer(this);
        listener.setRecognitionListener(new RecognitionListener(){
            @Override public void onReadyForSpeech(Bundle extras){}
            @Override public void onBeginningOfSpeech(){}
            @Override public void onRmsChanged(float rmsdB){}
            @Override public void onBufferReceived(byte[] buffer){}
            @Override public void onEndOfSpeech(){}
            @Override public void onPartialResults(Bundle partialResults){}
            @Override public void onEvent(int eventType, Bundle params){}
            @Override public void onError(int error) {
                speechError("Error de voz Android " + error + ". Compruebe conexión y micrófono.");
            }
            @Override public void onResults(Bundle results) {
                ArrayList<String> recognized=results.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION);
                if(recognized==null || recognized.isEmpty()) {
                    speechError("No se reconoció ninguna frase");
                    return;
                }
                String value=JSONObject.quote(recognized.get(0));
                javaScript("(function(){var r=window.__sjmCurrentRecognition;if(!r)return;" +
                    "try{if(r.onresult)r.onresult({results:[[{transcript:"+value+",confidence:0.8}]]})}finally{" +
                    "if(r.onend)r.onend();window.__sjmCurrentRecognition=null}})()");
            }
        });
        Intent request=new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH);
        request.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL,RecognizerIntent.LANGUAGE_MODEL_FREE_FORM);
        request.putExtra(RecognizerIntent.EXTRA_LANGUAGE,requestedLanguage);
        request.putExtra(RecognizerIntent.EXTRA_MAX_RESULTS,1);
        request.putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS,false);
        listener.startListening(request);
    }
    private void speechError(String explanation) {
        String msg=JSONObject.quote(explanation);
        javaScript("(function(){var r=window.__sjmCurrentRecognition;if(r){" +
            "if(r.onerror)r.onerror({error:"+msg+"});if(r.onend)r.onend();" +
            "window.__sjmCurrentRecognition=null}})()");
        runOnUiThread(()->Toast.makeText(this,explanation,Toast.LENGTH_SHORT).show());
    }
    @Override public void onRequestPermissionsResult(int code,String[] permissions,int[] grantResults) {
        super.onRequestPermissionsResult(code,permissions,grantResults);
        if(code==MICROPHONE_PERMISSION) {
            if(grantResults.length>0 && grantResults[0]==PackageManager.PERMISSION_GRANTED)
                microphoneStart(requestedLanguage);
            else speechError("Permiso del micrófono rechazado");
        }
    }
    private void readAloud(String sentence,String language,double speed) {
        if(!speakerReady || speaker==null) {
            Toast.makeText(this,"Preparando voz de Android",Toast.LENGTH_SHORT).show();return;
        }
        String text=sentence==null?"":sentence.trim();
        if(text.isEmpty())return;
        if(text.length()>3400)text=text.substring(0,3400);
        Locale locale=Locale.forLanguageTag((language==null||language.length()>16)?"es-CO":language);
        speaker.setLanguage(locale);
        float rate=(float)Math.max(.6,Math.min(1.35,speed));
        speaker.setSpeechRate(rate);
        speaker.speak(text,TextToSpeech.QUEUE_FLUSH,null,"SJM_"+System.nanoTime());
    }
    private void translateRemote(String sentence,String from,String to) {
        new Thread(()->{
            try {
                if(sentence==null || sentence.trim().isEmpty() || sentence.getBytes(StandardCharsets.UTF_8).length>480)
                    throw new IllegalArgumentException("Escriba una frase de máximo 480 bytes");
                if(!("en".equals(from)||"es".equals(from)) || !("en".equals(to)||"es".equals(to)) || from.equals(to))
                    throw new IllegalArgumentException("Dirección de idiomas no autorizada");
                String query="q="+URLEncoder.encode(sentence,"UTF-8")+
                    "&langpair="+URLEncoder.encode(from+"|"+to,"UTF-8");
                URL url=new URL("https://api.mymemory.translated.net/get?"+query);
                HttpURLConnection connection=(HttpURLConnection)url.openConnection();
                try {
                    connection.setInstanceFollowRedirects(false);
                    connection.setConnectTimeout(9000);connection.setReadTimeout(12000);
                    connection.setRequestProperty("Accept","application/json");
                    connection.setRequestProperty("Cache-Control","no-store");
                    int status=connection.getResponseCode();
                    if(status!=200)throw new IllegalStateException("Servicio HTTP "+status);
                    byte[] data;
                    try(InputStream in=connection.getInputStream();ByteArrayOutputStream b=new ByteArrayOutputStream()){
                        byte[] buf=new byte[2048];int n,total=0;
                        while((n=in.read(buf))!=-1){total+=n;if(total>60000)throw new IllegalStateException("Respuesta demasiado grande");b.write(buf,0,n);}
                        data=b.toByteArray();
                    }
                    String json=new String(data,StandardCharsets.UTF_8);
                    JSONObject parsed=new JSONObject(json);
                    if(parsed.optInt("responseStatus",-1)!=200 || parsed.optJSONObject("responseData")==null)
                        throw new IllegalStateException("El traductor no devolvió una traducción válida");
                    javaScript("if(window.__sjmTranslationCallback)window.__sjmTranslationCallback(true,"+
                        JSONObject.quote(json)+")");
                }finally{connection.disconnect();}
            } catch(Exception e){
                javaScript("if(window.__sjmTranslationCallback)window.__sjmTranslationCallback(false,"+
                    JSONObject.quote(e.getMessage()==null?"Sin conexión con el traductor":e.getMessage())+")");
            }
        },"sjm-translation").start();
    }
    private final class AndroidInterface {
        @JavascriptInterface public void startSpeech(String lang) {
            runOnUiThread(()->microphoneStart(lang));
        }
        @JavascriptInterface public void stopSpeech() {
            runOnUiThread(()->{if(listener!=null)listener.cancel();});
        }
        @JavascriptInterface public void speak(String text,String lang,double rate) {
            runOnUiThread(()->readAloud(text,lang,rate));
        }
        @JavascriptInterface public void stopAudio() {
            runOnUiThread(()->{if(speaker!=null)speaker.stop();});
        }
        @JavascriptInterface public void translateRemote(String text,String from,String to) {
            MainActivity.this.translateRemote(text,from,to);
        }
    }
    @Override public void onBackPressed() {
        if(page!=null && page.canGoBack())page.goBack();
        else super.onBackPressed();
    }
    @Override protected void onDestroy() {
        if(listener!=null){listener.cancel();listener.destroy();}
        if(speaker!=null){speaker.stop();speaker.shutdown();}
        if(page!=null){page.removeJavascriptInterface("SJMAndroid");page.destroy();page=null;}
        super.onDestroy();
    }
}
