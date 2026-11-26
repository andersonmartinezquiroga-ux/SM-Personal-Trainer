package com.sjm.kairos.mobile;

import android.accessibilityservice.AccessibilityService;
import android.accessibilityservice.GestureDescription;
import android.graphics.Path;
import android.graphics.Rect;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.media.AudioManager;
import android.os.Handler;
import android.view.accessibility.AccessibilityNodeInfo;

import org.json.JSONArray;
import org.json.JSONObject;

import java.util.ArrayDeque;

/**
 * Executes a bounded, owner-approved workflow on an explicitly named app.
 * No screen dumps, screenshots, remotely supplied coordinates, passwords, purchases,
 * message sending, or permission-setting actions. All matching stays on-device.
 */
final class AppWorkflowEngine {
    interface Completion { void onDone(boolean ok, String receipt); }
    private final AccessibilityService service;
    private final Handler handler;
    private final String target;
    private final JSONArray steps;
    private final Completion completion;
    private boolean finished;
    private int foregroundRetries;
    private int actionRetryStep=-1;
    private int actionRetries;

    private AppWorkflowEngine(AccessibilityService svc, Handler h,
                              String pkg, JSONArray instructions, Completion callback) {
        service=svc; handler=h; target=pkg; steps=instructions; completion=callback;
    }

    private boolean isCommunicationActive() {
        AudioManager mgr=service.getSystemService(AudioManager.class);
        if(mgr==null)return true; // fail closed when Android cannot report audio mode
        int mode=mgr.getMode();
        return mode==AudioManager.MODE_IN_CALL ||
               mode==AudioManager.MODE_IN_COMMUNICATION;
    }

    static boolean validate(JSONObject payload) {
        if(payload==null || payload.length()!=2 ||
           !payload.has("package") || !payload.has("steps"))return false;
        String target=payload.optString("package","");
        JSONArray sequence=payload.optJSONArray("steps");
        if(!AppWorkflowPolicy.isValidPackage(target) ||
           sequence==null || sequence.length()<1 ||
           sequence.length()>AppWorkflowPolicy.MAX_STEPS)return false;
        for(int i=0;i<sequence.length();i++){
            JSONObject step=sequence.optJSONObject(i);
            if(step==null || step.length()<1 || step.length()>3)return false;
            for(java.util.Iterator<String> it=step.keys();it.hasNext();) {
                String key=it.next();
                if(!"action".equals(key)&&!"selector".equals(key)&&!"value".equals(key))return false;
            }
            if(!step.has("action") || !(step.opt("action") instanceof String))return false;
            if(step.has("selector") && !(step.opt("selector") instanceof String))return false;
            if(step.has("value") && !(step.opt("value") instanceof String))return false;
            String action=step.optString("action","");
            String selector=step.optString("selector","");
            String value=step.optString("value","");
            if(!AppWorkflowPolicy.isAllowedStep(action,selector,value))return false;
            if(("youtube_play_video".equals(action) ||
                 "youtube_search_play".equals(action)) &&
               (!"com.google.android.youtube".equals(target) || sequence.length()!=1))
                return false;
        }
        return true;
    }

    static void start(AccessibilityService svc,Handler h,
                      JSONObject payload,Completion cb) {
        if(!validate(payload)) {cb.onDone(false,"WORKFLOW_POLICY_DENIED");return;}
        String pkg=payload.optString("package","");
        // Package must also be query-visible and launchable on this device.
        Intent launch=svc.getPackageManager().getLaunchIntentForPackage(pkg);
        if(launch==null) {cb.onDone(false,"WORKFLOW_APP_UNAVAILABLE");return;}
        AppWorkflowEngine worker=new AppWorkflowEngine(svc,h,pkg,payload.optJSONArray("steps"),cb);
        if(worker.isCommunicationActive()){
            cb.onDone(false,"WORKFLOW_VOICE_BUSY_NOT_EXECUTED");
            return;
        }
        JSONObject onlyStep=payload.optJSONArray("steps").optJSONObject(0);
        if(onlyStep!=null && "youtube_play_video".equals(onlyStep.optString("action",""))){
            worker.openYoutubeVideo(onlyStep.optString("value",""));
            return;
        }
        if(onlyStep!=null && "youtube_search_play".equals(onlyStep.optString("action",""))){
            worker.searchAndPlayYoutube(onlyStep.optString("value",""));
            return;
        }
        try{
            // Do not reset a visible app or disturb an existing screen.
            if(worker.foreground()!=null){
                h.postDelayed(()->worker.executeStep(0),400L);
            }else{
                launch.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                svc.startActivity(launch);
                h.postDelayed(()->worker.executeStep(0),1100L);
            }
        }catch(RuntimeException e){cb.onDone(false,"WORKFLOW_LAUNCH_DENIED");}
    }

    /**
     * Direct verified YouTube video link. The backend searches for the
     * song's real video ID; the phone opens it in YouTube itself.
     * This avoids brittle keyboard selectors and never opens another app.
     * An accepted launch does NOT certify that audio has started.
     */
    /** Search any requested song by a YouTube deep link; no fixed video IDs or coordinates. */
    private void searchAndPlayYoutube(String request){
        if(!"com.google.android.youtube".equals(target) ||
           !AppWorkflowPolicy.isValidSongRequest(request)){
            finish(false,"YOUTUBE_SEARCH_POLICY_DENIED");
            return;
        }
        if(CommandReceiptStore.isPaused(service)){
            finish(false,"WORKFLOW_OWNER_PAUSED");
            return;
        }
        int separator=request.indexOf('|');
        String title=request.substring(0,separator).trim();
        String artist=request.substring(separator+1).trim();
        Uri search=Uri.parse("https://www.youtube.com/results").buildUpon()
            .appendQueryParameter("search_query",title+" "+artist).build();
        try {
            Intent intent=new Intent(Intent.ACTION_VIEW,search);
            intent.setPackage("com.google.android.youtube");
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TOP);
            service.startActivity(intent);
            handler.postDelayed(()->tapYouTubeResult(request,0),1900L);
        }catch(RuntimeException e){
            finish(false,"YOUTUBE_SEARCH_LAUNCH_DENIED");
        }
    }

    private void tapYouTubeResult(String request,int attempt){
        if(finished)return;
        if(CommandReceiptStore.isPaused(service)){
            finish(false,"WORKFLOW_OWNER_PAUSED");
            return;
        }
        if(isCommunicationActive()){
            finish(false,"WORKFLOW_VOICE_BUSY_INTERRUPTED_SAFELY");
            return;
        }
        AccessibilityNodeInfo root=foreground();
        if(root!=null){
            AccessibilityNodeInfo video=findMatchingVideo(root,request);
            if(video!=null){
                AccessibilityNodeInfo click=safeClickableAncestor(video);
                try {
                    if(click!=null && click.performAction(AccessibilityNodeInfo.ACTION_CLICK)){
                        // Matching a search result is not proof that YouTube started
                        // video playback. Observe its player and attempt Play safely.
                        handler.postDelayed(()->verifyYoutubePlayback(request,0,0,false),1400L);
                        return;
                    }
                }catch(RuntimeException ignored){}
            }
        }
        if(attempt>=18){
            finish(false,"YOUTUBE_SEARCH_MATCHING_RESULT_NOT_VERIFIED");
            return;
        }
        handler.postDelayed(()->tapYouTubeResult(request,attempt+1),650L);
    }

    /**
     * YouTube can first show a suggestion, rather than open a watch page.
     * Continue through at most ONE additional matching result, never blindly
     * click coordinates and never claim success without a visible player.
     */
    private void verifyYoutubePlayback(String request,int attempt,int furtherResultClicks,
                                       boolean playAttempted){
        if(finished)return;
        if(CommandReceiptStore.isPaused(service)){
            finish(false,"WORKFLOW_OWNER_PAUSED");
            return;
        }
        if(isCommunicationActive()){
            finish(false,"WORKFLOW_VOICE_BUSY_INTERRUPTED_SAFELY");
            return;
        }
        AccessibilityNodeInfo root=foreground();
        if(root!=null){
            PlayerObservation observation=inspectYoutubePlayer(root);
            AudioManager audio=service.getSystemService(AudioManager.class);
            boolean musicActive=audio!=null && audio.isMusicActive() &&
                audio.getStreamVolume(AudioManager.STREAM_MUSIC)>0;
            if(observation.pauseControlVisible && musicActive){
                finish(true,"YOUTUBE_PAUSE_CONTROL_AND_AUDIO_ACTIVE_TRACK_OWNER_UNVERIFIED");
                return;
            }
            if(observation.playButton!=null && !playAttempted && attempt>=2){
                AccessibilityNodeInfo click=safeClickableAncestor(observation.playButton);
                try {
                    if(click!=null && click.performAction(AccessibilityNodeInfo.ACTION_CLICK)){
                        handler.postDelayed(()->verifyYoutubePlayback(request,attempt+1,
                            furtherResultClicks,true),800L);
                        return;
                    }
                }catch(RuntimeException ignored){}
            }
            if(!observation.hasPlayerControl && furtherResultClicks<1 && attempt>=4){
                AccessibilityNodeInfo result=findMatchingVideo(root,request);
                AccessibilityNodeInfo click=result==null?null:safeClickableAncestor(result);
                try {
                    if(click!=null && click.performAction(AccessibilityNodeInfo.ACTION_CLICK)){
                        handler.postDelayed(()->verifyYoutubePlayback(request,attempt+1,
                            furtherResultClicks+1,playAttempted),1200L);
                        return;
                    }
                }catch(RuntimeException ignored){}
            }
        }
        if(attempt>=20){
            finish(false,root==null?"YOUTUBE_FOREGROUND_LOST_AFTER_RESULT":
                "YOUTUBE_PLAYBACK_NOT_VERIFIED");
            return;
        }
        handler.postDelayed(()->verifyYoutubePlayback(request,attempt+1,
            furtherResultClicks,playAttempted),600L);
    }

    private static final class PlayerObservation {
        AccessibilityNodeInfo playButton;
        boolean pauseControlVisible;
        boolean hasPlayerControl;
    }

    /** Only examine visible, enabled YouTube player buttons on this device. */
    private PlayerObservation inspectYoutubePlayer(AccessibilityNodeInfo root){
        PlayerObservation result=new PlayerObservation();
        ArrayDeque<AccessibilityNodeInfo> pending=new ArrayDeque<>();
        pending.add(root);
        int examined=0;
        while(!pending.isEmpty() && examined++<350){
            AccessibilityNodeInfo node=pending.removeFirst();
            if(node==null || !target.equals(String.valueOf(node.getPackageName())) ||
               !node.isVisibleToUser())continue;
            String id=String.valueOf(node.getViewIdResourceName()).toLowerCase(java.util.Locale.ROOT);
            String description=String.valueOf(node.getContentDescription())
                .toLowerCase(java.util.Locale.ROOT).trim();
            String cls=String.valueOf(node.getClassName()).toLowerCase(java.util.Locale.ROOT);
            boolean playerId=id.contains("player_control") || id.contains("play_pause") ||
                id.contains("player_overlay");
            boolean button=cls.contains("button") || cls.contains("imageview") || playerId;
            if(button && node.isEnabled() && !node.isPassword()){
                boolean paused=description.equals("reproducir") ||
                    description.startsWith("reproducir vídeo") ||
                    description.startsWith("reproducir video") ||
                    description.startsWith("play video") ||
                    description.equals("play") || description.startsWith("play video");
                boolean playing=description.equals("pausar") ||
                    description.startsWith("pausar vídeo") ||
                    description.startsWith("pausar video") ||
                    description.startsWith("pause video") ||
                    description.equals("pause");
                if(paused || playing){
                    result.hasPlayerControl=true;
                    if(playing)result.pauseControlVisible=true;
                    if(paused && result.playButton==null)result.playButton=node;
                }
                // A generic player container does not prove playback;
                // it only prevents another video-result click.
                if(playerId)result.hasPlayerControl=true;
            }
            for(int i=0;i<node.getChildCount();i++){
                AccessibilityNodeInfo child=node.getChild(i);
                if(child!=null)pending.addLast(child);
            }
        }
        return result;
    }

    private void openYoutubeVideo(String videoId){
        if(!"com.google.android.youtube".equals(target) ||
           videoId==null || !videoId.matches("[A-Za-z0-9_-]{11}")){
            finish(false,"YOUTUBE_VIDEO_POLICY_DENIED");
            return;
        }
        if(CommandReceiptStore.isPaused(service)){
            finish(false,"WORKFLOW_OWNER_PAUSED");
            return;
        }
        try{
            Intent intent=new Intent(Intent.ACTION_VIEW,
                 Uri.parse("https://www.youtube.com/watch?v="+videoId));
            intent.setPackage("com.google.android.youtube");
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TOP);
            service.startActivity(intent);
            handler.postDelayed(()->verifyYoutubeOpened(0),1600L);
        }catch(RuntimeException e){
            finish(false,"YOUTUBE_VIDEO_OPEN_DENIED");
        }
    }

    private void verifyYoutubeOpened(int attempt){
        if(finished)return;
        if(CommandReceiptStore.isPaused(service)){
            finish(false,"WORKFLOW_OWNER_PAUSED");
            return;
        }
        if(isCommunicationActive()){
            finish(false,"WORKFLOW_VOICE_BUSY_INTERRUPTED_SAFELY");
            return;
        }
        if(foreground()!=null){
            finish(true,"YOUTUBE_VIDEO_LINK_OPENED_FOREGROUND_CONFIRMED_PLAYBACK_UNVERIFIED");
            return;
        }
        if(attempt>=18){
            finish(false,"YOUTUBE_VIDEO_FOREGROUND_NOT_VERIFIED");
            return;
        }
        handler.postDelayed(()->verifyYoutubeOpened(attempt+1),650L);
    }

    private void finish(boolean ok,String detail) {
        if(finished)return;
        finished=true;
        completion.onDone(ok,detail);
    }
    private AccessibilityNodeInfo foreground(){
        AccessibilityNodeInfo root=service.getRootInActiveWindow();
        return root!=null && root.getPackageName()!=null &&
               target.equals(String.valueOf(root.getPackageName())) ? root:null;
    }
    /**
     * Chrome's new-tab page and its focused omnibox have different Android
     * resource ids. Only resolve the known Chrome search_box_text control when
     * the owner-approved selector is Chrome's exact url_bar id. Never match
     * another package or a generic editable field.
     */
    private AccessibilityNodeInfo findChromeOmniboxAlternative(
        AccessibilityNodeInfo root,String requestedSelector,boolean requireEditable){
        if(!"com.android.chrome".equals(target) ||
           !"id:com.android.chrome:id/url_bar".equals(requestedSelector))
            return null;
        AccessibilityNodeInfo candidate=findOne(
            root,"id:com.android.chrome:id/search_box_text",false);
        if(candidate==null || !candidate.isVisibleToUser() ||
           !candidate.isEnabled() || candidate.isPassword() ||
           !target.equals(String.valueOf(candidate.getPackageName())))
            return null;
        if(requireEditable)return candidate.isEditable()?candidate:null;
        return safeClickableAncestor(candidate)==null?null:candidate;
    }

    private void executeStep(int index){
        if(finished)return;
        if(CommandReceiptStore.isPaused(service)){
            finish(false,"WORKFLOW_OWNER_PAUSED");return;
        }
        // A voice call may start after the command was received. Recheck
        // before EVERY UI step rather than blindly continuing a prior plan.
        if(isCommunicationActive()){
            finish(false,"WORKFLOW_VOICE_BUSY_INTERRUPTED_SAFELY");return;
        }
        AccessibilityNodeInfo root=foreground();
        if(root==null){
            // Window handoff is asynchronous. Never interact with another foreground app.
            if(foregroundRetries++ < (index==0 ? 10 : 5)){
                handler.postDelayed(()->executeStep(index),650L);
                return;
            }
            finish(false,"WORKFLOW_FOREGROUND_NOT_VERIFIED_STEP_"+index);
            return;
        }
        foregroundRetries=0;
        if(index>=steps.length()){
            // Proven that the target package is still visible; not an app-specific outcome.
            finish(true,"WORKFLOW_ACTIONS_ACCEPTED_FOREGROUND_CONFIRMED_"+steps.length());
            return;
        }
        JSONObject step=steps.optJSONObject(index);
        if(step==null){finish(false,"WORKFLOW_STEP_INVALID");return;}
        String action=step.optString("action","");
        String selector=step.optString("selector","");
        String value=step.optString("value","");
        boolean accepted=false;
        long delay=550L;
        try{
            if("wait".equals(action)){
                accepted=true;delay=Long.parseLong(value);
            }else if("back".equals(action)){
                accepted=service.performGlobalAction(AccessibilityService.GLOBAL_ACTION_BACK);
            }else if("scroll_up".equals(action)||"scroll_down".equals(action)){
                final int direction="scroll_down".equals(action)
                    ?AccessibilityNodeInfo.ACTION_SCROLL_FORWARD
                    :AccessibilityNodeInfo.ACTION_SCROLL_BACKWARD;
                AccessibilityNodeInfo targetNode=findOne(root,selector,true);
                if("com.android.chrome".equals(target) && selector.isEmpty()){
                    // Chrome may expose both browser chrome and nested web content.
                    // Prefer only a unique visible WebView supporting this direction.
                    // No cross-package traversal or ambiguous clicks; bounded fallback below.
                    targetNode=findUniqueChromeScrollableWebView(root,direction);
                }
                if(targetNode!=null && targetNode.isVisibleToUser() &&
                   targetNode.isEnabled() && !targetNode.isPassword() &&
                   target.equals(String.valueOf(targetNode.getPackageName()))){
                    accepted=targetNode.performAction(direction);
                    if(!accepted && "com.android.chrome".equals(target) && selector.isEmpty()){
                        int verticalAction=direction==AccessibilityNodeInfo.ACTION_SCROLL_FORWARD
                            ?AccessibilityNodeInfo.AccessibilityAction.ACTION_SCROLL_DOWN.getId()
                            :AccessibilityNodeInfo.AccessibilityAction.ACTION_SCROLL_UP.getId();
                        if(hasScrollAction(targetNode,verticalAction))
                            accepted=targetNode.performAction(verticalAction);
                    }
                }
            }else if("tap_video".equals(action) && "com.google.android.youtube".equals(target)){
                AccessibilityNodeInfo video=findMatchingVideo(root,value);
                if(video!=null){
                    AccessibilityNodeInfo button=safeClickableAncestor(video);
                    if(button!=null)accepted=button.performAction(AccessibilityNodeInfo.ACTION_CLICK);
                }
            }else if("tap".equals(action)||"type".equals(action)||"ime_search".equals(action)){
                AccessibilityNodeInfo node=findOne(root,selector,false);
                if("type".equals(action) && (node==null || !node.isEditable()))
                    node=findChromeOmniboxAlternative(root,selector,true);
                if("tap".equals(action) && node==null)
                    node=findChromeOmniboxAlternative(root,selector,false);
                if(node!=null && node.isVisibleToUser() && node.isEnabled() &&
                   !node.isPassword() && target.equals(String.valueOf(node.getPackageName()))){
                    if("tap".equals(action)){
                        // In YouTube a labeled element can be a non-clickable child
                        // of the real button. Ascend only within the same approved app.
                        AccessibilityNodeInfo button=safeClickableAncestor(node);
                        if(button!=null)
                            accepted=button.performAction(AccessibilityNodeInfo.ACTION_CLICK);
                        if(!accepted){
                            // Retry only the alternate named Chrome new-tab search box.
                            // Never use arbitrary coordinates or other fields.
                            AccessibilityNodeInfo alternative=
                                findChromeOmniboxAlternative(root,selector,false);
                            AccessibilityNodeInfo altButton=alternative==null?null:
                                safeClickableAncestor(alternative);
                            if(altButton!=null)
                                accepted=altButton.performAction(AccessibilityNodeInfo.ACTION_CLICK);
                        }
                    }else if(node.isEditable()){
                        if("type".equals(action)){
                            Bundle arguments=new Bundle();
                            arguments.putCharSequence(
                              AccessibilityNodeInfo.ACTION_ARGUMENT_SET_TEXT_CHARSEQUENCE,value);
                            accepted=node.performAction(AccessibilityNodeInfo.ACTION_SET_TEXT,arguments);
                            if(accepted){
                                // Acknowledgement alone is not proof that the field contains the text.
                                // Observe locally, never repeat an already accepted write.
                                handler.postDelayed(()->verifyWrittenText(index,selector,value,0),400L);
                                return;
                            }
                        }else if("ime_search".equals(action) &&
                                 android.os.Build.VERSION.SDK_INT>=30){
                            // Search through the focused editable field, not a brittle
                            // screen coordinate or YouTube search button ID.
                            if(!node.isFocused()) node.performAction(AccessibilityNodeInfo.ACTION_FOCUS);
                            accepted=node.performAction(
                                AccessibilityNodeInfo.AccessibilityAction.ACTION_IME_ENTER.getId());
                        }
                    }
                }
            }
        }catch(RuntimeException e){
            accepted=false;
        }
        if(!accepted){
            // Controls can appear after the screen begins to render.
            // Never repeat an action that was already accepted by Android.
            if(actionRetryStep!=index){actionRetryStep=index;actionRetries=0;}
            if(actionRetries++ < 5){
                handler.postDelayed(()->executeStep(index),650L);
                return;
            }
            // The owner explicitly authorized only vertical scrolling inside Chrome.
            // The fallback is local, bounded, and cannot accept remote coordinates.
            if("com.android.chrome".equals(target) && selector.isEmpty() &&
               ("scroll_down".equals(action)||"scroll_up".equals(action))){
                if(dispatchChromeScroll(index,"scroll_down".equals(action)))return;
            }
            String boundedReason="ACTION_REFUSED";
            try {
            if("tap".equals(action) || "type".equals(action)){
                AccessibilityNodeInfo exact=findOne(root,selector,false);
                AccessibilityNodeInfo alternate=findChromeOmniboxAlternative(
                    root,selector,"type".equals(action));
                if(exact==null && alternate==null)
                    boundedReason="SELECTOR_NOT_FOUND";
                else if("type".equals(action) && exact!=null && !exact.isEditable()
                        && alternate==null)
                    boundedReason="TARGET_NOT_EDITABLE";
                else if("tap".equals(action) && exact!=null &&
                        safeClickableAncestor(exact)==null && alternate==null)
                    boundedReason="TARGET_NOT_CLICKABLE";
            }else if("scroll_down".equals(action)||"scroll_up".equals(action)){
                if(("com.android.chrome".equals(target) && selector.isEmpty()
                    ?findUniqueChromeScrollableWebView(root,"scroll_down".equals(action)
                        ?AccessibilityNodeInfo.ACTION_SCROLL_FORWARD:AccessibilityNodeInfo.ACTION_SCROLL_BACKWARD)
                    :findOne(root,selector,true))==null)
                    boundedReason="NO_VISIBLE_SCROLLABLE_CONTAINER";
            }
            } catch(RuntimeException diagnosticFailure){
                // A stale accessibility node must not prevent the terminal receipt.
                boundedReason="DIAGNOSTIC_UNAVAILABLE";
            }
            // Reason codes only. No screen text, URLs or private data leave Android.
            finish(false,"WORKFLOW_ACTION_REJECTED_STEP_"+index+"_"+boundedReason);
            return;
        }
        actionRetryStep=-1;
        actionRetries=0;
        // Do not claim the business task succeeded; each action is acknowledged separately.
        // Reuse the guarded foreground/voice/pause checks even at the final step.
        handler.postDelayed(()->executeStep(index+1),delay);
    }

    private boolean dispatchChromeScroll(int index,boolean down){
        if(finished || !"com.android.chrome".equals(target) ||
           CommandReceiptStore.isPaused(service) || isCommunicationActive())return false;
        AccessibilityNodeInfo current=foreground();
        if(current==null || !current.isVisibleToUser())return false;
        AccessibilityNodeInfo input=current.findFocus(AccessibilityNodeInfo.FOCUS_INPUT);
        if(input!=null && (input.isPassword() || input.isEditable()))return false;
        Rect bounds=new Rect();
        current.getBoundsInScreen(bounds);
        android.util.DisplayMetrics dm=service.getResources().getDisplayMetrics();
        if(!bounds.intersect(0,0,dm.widthPixels,dm.heightPixels) ||
           bounds.width()<120 || bounds.height()<240)return false;
        float x=bounds.exactCenterX();
        float upper=bounds.top+bounds.height()*0.35f;
        float lower=bounds.top+bounds.height()*0.72f;
        Path path=new Path();
        path.moveTo(x,down?lower:upper);
        path.lineTo(x,down?upper:lower);
        GestureDescription gesture=new GestureDescription.Builder()
            .addStroke(new GestureDescription.StrokeDescription(path,0,420)).build();
        // Recheck immediately before dispatch. A successful callback verifies
        // Android completed the gesture, not the actual page displacement.
        if(foreground()==null || CommandReceiptStore.isPaused(service) ||
           isCommunicationActive())return false;
        boolean submitted=service.dispatchGesture(gesture,new AccessibilityService.GestureResultCallback(){
            @Override public void onCompleted(GestureDescription g){
                if(finished)return;
                actionRetryStep=-1;actionRetries=0;
                if(CommandReceiptStore.isPaused(service) || isCommunicationActive() ||
                   foreground()==null){
                    finish(false,"CHROME_SCROLL_GESTURE_COMPLETED_CONTEXT_CHANGED");return;
                }
                if(index+1>=steps.length()){
                    finish(true,"CHROME_SCROLL_GESTURE_COMPLETED_FOREGROUND_CONFIRMED_MOVEMENT_UNVERIFIED");
                }else{
                    handler.postDelayed(()->executeStep(index+1),550L);
                }
            }
            @Override public void onCancelled(GestureDescription g){
                finish(false,"CHROME_SCROLL_GESTURE_CANCELLED");
            }
        },handler);
        if(submitted)handler.postDelayed(()->{
            if(!finished && actionRetryStep==index)
                finish(false,"CHROME_SCROLL_GESTURE_CALLBACK_TIMEOUT");
        },4000L);
        return submitted;
    }

    private void verifyWrittenText(int index,String selector,String expected,int attempt){
        if(finished)return;
        if(CommandReceiptStore.isPaused(service)){
            finish(false,"WORKFLOW_OWNER_PAUSED");return;
        }
        if(isCommunicationActive()){
            finish(false,"WORKFLOW_VOICE_BUSY_INTERRUPTED_SAFELY");return;
        }
        AccessibilityNodeInfo root=foreground();
        AccessibilityNodeInfo node=root==null?null:findOne(root,selector,false);
        if(root!=null && (node==null || !node.isEditable()))
            node=findChromeOmniboxAlternative(root,selector,true);
        // text: selectors can cease matching after the write. Fail closed instead
        // of choosing another editable field or disclosing text to the backend.
        if(node!=null && node.isVisibleToUser() && node.isEnabled() &&
           node.isEditable() && !node.isPassword() &&
           target.equals(String.valueOf(node.getPackageName())) &&
           expected.contentEquals(node.getText()==null?"":node.getText())){
            actionRetryStep=-1; actionRetries=0; foregroundRetries=0;
            handler.postDelayed(()->executeStep(index+1),350L);
            return;
        }
        if(attempt<5){
            handler.postDelayed(()->verifyWrittenText(index,selector,expected,attempt+1),400L);
        }else{
            finish(false,"WORKFLOW_WRITE_ACCEPTED_READBACK_UNVERIFIED_STEP_"+index);
        }
    }

    /**
     * Video title and artist must both occur in the SAME accessible result.
     * Never pick the search text field or a generic result with only the song name.
     * Does not export any screen content.
     */
    private AccessibilityNodeInfo findMatchingVideo(AccessibilityNodeInfo root,String query){
        if(query==null)return null;
        String[] words=query.toLowerCase(java.util.Locale.ROOT).split("\\|",-1);
        if(words.length!=2||words[0].trim().length()<3||words[1].trim().length()<3)return null;
        String song=words[0].trim(),artist=words[1].trim();
        ArrayDeque<AccessibilityNodeInfo> queue=new ArrayDeque<>();
        queue.add(root);
        int count=0;
        while(!queue.isEmpty()&&count++<350){
            AccessibilityNodeInfo n=queue.removeFirst();
            if(n==null||!target.equals(String.valueOf(n.getPackageName()))||
               !n.isVisibleToUser())continue;
            String label=(String.valueOf(n.getText())+" "+String.valueOf(n.getContentDescription()))
                .toLowerCase(java.util.Locale.ROOT);
            if(!n.isEditable()&&!n.isPassword()&&
               !AppWorkflowPolicy.isSensitiveClick(label)){
                AccessibilityNodeInfo clickable=safeClickableAncestor(n);
                if(clickable!=null && !clickable.isScrollable()){
                    if(label.contains(song)&&label.contains(artist))return n;
                    // A result row can split the video title and channel labels.
                    if(label.contains(song) && matchingRowText(clickable,song,artist))
                        return clickable;
                }
            }
            for(int i=0;i<n.getChildCount();i++){
                AccessibilityNodeInfo child=n.getChild(i);
                if(child!=null)queue.addLast(child);
            }
        }
        return null;
    }

    private boolean matchingRowText(AccessibilityNodeInfo row,String song,String artist){
        ArrayDeque<AccessibilityNodeInfo> sub=new ArrayDeque<>();
        sub.add(row);
        int checked=0;
        StringBuilder labels=new StringBuilder();
        while(!sub.isEmpty()&&checked++<30){
            AccessibilityNodeInfo child=sub.removeFirst();
            if(!target.equals(String.valueOf(child.getPackageName())) ||
               !child.isVisibleToUser() || child.isPassword() ||
               child.isEditable())return false;
            String label=(String.valueOf(child.getText())+" "+
                    String.valueOf(child.getContentDescription())).toLowerCase(java.util.Locale.ROOT);
            if(AppWorkflowPolicy.isSensitiveClick(label))return false;
            labels.append(' ').append(label);
            for(int i=0;i<child.getChildCount();i++){
                AccessibilityNodeInfo nested=child.getChild(i);
                if(nested!=null)sub.addLast(nested);
            }
        }
        return sub.isEmpty() && labels.toString().contains(song) && labels.toString().contains(artist);
    }

    private AccessibilityNodeInfo safeClickableAncestor(AccessibilityNodeInfo node){
        AccessibilityNodeInfo current=node;
        for(int depth=0;current!=null && depth<4;depth++){
            if(!target.equals(String.valueOf(current.getPackageName())) ||
               !current.isVisibleToUser() || !current.isEnabled() || current.isPassword())
                return null;
            if(AppWorkflowPolicy.isSensitiveClick(String.valueOf(current.getText())) ||
               AppWorkflowPolicy.isSensitiveClick(String.valueOf(current.getContentDescription())))
                return null;
            if(current.isClickable())return current;
            current=current.getParent();
        }
        return null;
    }

    /**
     * Bounded, local Chrome scroll disambiguation. If two eligible WebViews
     * are present, fail closed instead of guessing which page to move.
     */
    private static boolean hasScrollAction(AccessibilityNodeInfo node,int action){
        for(AccessibilityNodeInfo.AccessibilityAction item:node.getActionList()){
            if(item.getId()==action)return true;
        }
        return false;
    }

    private AccessibilityNodeInfo findUniqueChromeScrollableWebView(
        AccessibilityNodeInfo root,int direction){
        if(root==null || !"com.android.chrome".equals(target))return null;
        final int verticalAction=direction==AccessibilityNodeInfo.ACTION_SCROLL_FORWARD
            ?AccessibilityNodeInfo.AccessibilityAction.ACTION_SCROLL_DOWN.getId()
            :AccessibilityNodeInfo.AccessibilityAction.ACTION_SCROLL_UP.getId();
        ArrayDeque<AccessibilityNodeInfo> pending=new ArrayDeque<>();
        pending.add(root);
        AccessibilityNodeInfo web=null,other=null;
        int webCount=0,otherCount=0,inspected=0;
        while(!pending.isEmpty() && inspected++<350){
            AccessibilityNodeInfo node=pending.removeFirst();
            if(!target.equals(String.valueOf(node.getPackageName())))continue;
            // Chrome virtual content may advertise an action without the scrollable flag.
            if(node.isVisibleToUser() && node.isEnabled() && !node.isPassword() &&
               (hasScrollAction(node,direction) || hasScrollAction(node,verticalAction))){
                if("android.webkit.WebView".equals(String.valueOf(node.getClassName()))){
                    web=node;webCount++;
                }else{
                    other=node;otherCount++;
                }
            }
            for(int i=0;i<node.getChildCount();i++){
                AccessibilityNodeInfo child=node.getChild(i);
                if(child!=null)pending.addLast(child);
            }
        }
        // Never infer a target from a partially inspected tree or ambiguous nodes.
        if(!pending.isEmpty() || webCount>1)return null;
        if(webCount==1)return web;
        return otherCount==1?other:null;
    }

    private static boolean equalsTarget(String prefix,String selector, AccessibilityNodeInfo node){
        if("id:".equals(prefix))return selector.equals(String.valueOf(node.getViewIdResourceName()));
        if("text:".equals(prefix))return selector.equals(String.valueOf(node.getText()));
        if("desc:".equals(prefix))return selector.equals(String.valueOf(node.getContentDescription()));
        if("hint:".equals(prefix))return selector.equals(String.valueOf(node.getHintText()));
        return false;
    }

    /**
     * Finds exactly one visible match within the target app, up to 350 nodes.
     * Blank selector for scrolling chooses the first visible scrollable container.
     * Matching text is never returned to the backend or stored.
     */
    private AccessibilityNodeInfo findOne(AccessibilityNodeInfo root,String selector,boolean scroll){
        String prefix="",term="";
        if(selector!=null && !selector.isEmpty()){
            int colon=selector.indexOf(':');
            if(colon<0)return null;
            prefix=selector.substring(0,colon+1);
            term=selector.substring(colon+1);
        }
        ArrayDeque<AccessibilityNodeInfo> queue=new ArrayDeque<>();
        queue.add(root);
        AccessibilityNodeInfo found=null;
        int inspected=0;
        while(!queue.isEmpty() && inspected<350){
            AccessibilityNodeInfo n=queue.removeFirst();
            inspected++;
            if(n==null)continue;
            if(target.equals(String.valueOf(n.getPackageName())) && n.isVisibleToUser()){
                boolean candidate=scroll ? n.isScrollable() &&
                    (selector==null || selector.isEmpty() || equalsTarget(prefix,term,n))
                    :equalsTarget(prefix,term,n);
                if(candidate){
                    if(found!=null)return null; // ambiguous elements: fail closed
                    found=n;
                }
                for(int i=0;i<n.getChildCount();i++){
                    AccessibilityNodeInfo child=n.getChild(i);
                    if(child!=null)queue.addLast(child);
                }
            }
        }
        return found;
    }
}
