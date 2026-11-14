package com.sjm.kairos.mobile;

import android.accessibilityservice.AccessibilityService;
import android.content.Intent;
import android.os.Bundle;
import android.os.Handler;
import android.view.accessibility.AccessibilityNodeInfo;

import org.json.JSONArray;
import org.json.JSONObject;

import java.util.ArrayDeque;

/**
 * Executes a bounded, owner-approved workflow on an explicitly named app.
 * No screen dumps, screenshots, arbitrary coordinates, passwords, purchases,
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
        try{
            launch.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK|Intent.FLAG_ACTIVITY_CLEAR_TOP);
            svc.startActivity(launch);
            h.postDelayed(()->worker.executeStep(0),1100L);
        }catch(RuntimeException e){cb.onDone(false,"WORKFLOW_LAUNCH_DENIED");}
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
    private void executeStep(int index){
        if(finished)return;
        if(CommandReceiptStore.isPaused(service)){
            finish(false,"WORKFLOW_OWNER_PAUSED");return;
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
                AccessibilityNodeInfo targetNode=findOne(root,selector,true);
                if(targetNode!=null){
                    accepted=targetNode.performAction("scroll_down".equals(action)
                        ?AccessibilityNodeInfo.ACTION_SCROLL_FORWARD
                        :AccessibilityNodeInfo.ACTION_SCROLL_BACKWARD);
                }
            }else if("tap".equals(action)||"type".equals(action)){
                AccessibilityNodeInfo node=findOne(root,selector,false);
                if(node!=null && node.isVisibleToUser() && node.isEnabled() &&
                   !node.isPassword() && target.equals(String.valueOf(node.getPackageName()))){
                    if("tap".equals(action)){
                        // In YouTube a labeled element can be a non-clickable child
                        // of the real button. Ascend only within the same approved app.
                        AccessibilityNodeInfo button=safeClickableAncestor(node);
                        if(button!=null)
                            accepted=button.performAction(AccessibilityNodeInfo.ACTION_CLICK);
                    }else if(node.isEditable()){
                        Bundle arguments=new Bundle();
                        arguments.putCharSequence(
                          AccessibilityNodeInfo.ACTION_ARGUMENT_SET_TEXT_CHARSEQUENCE,value);
                        accepted=node.performAction(AccessibilityNodeInfo.ACTION_SET_TEXT,arguments);
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
            finish(false,"WORKFLOW_ACTION_REJECTED_STEP_"+index);
            return;
        }
        actionRetryStep=-1;
        actionRetries=0;
        // Do not claim the business task succeeded; each action is acknowledged separately.
        if(index+1>=steps.length()){
            handler.postDelayed(()->{
                if(foreground()!=null)
                    finish(true,"WORKFLOW_ACTIONS_ACCEPTED_FOREGROUND_CONFIRMED_"+steps.length());
                else finish(false,"WORKFLOW_FINAL_FOREGROUND_UNVERIFIED");
            },delay);
        }else{
            handler.postDelayed(()->executeStep(index+1),delay);
        }
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
