package com.sjm.kairos.mobile;

import android.app.Activity;
import android.graphics.Color;
import android.os.Bundle;
import android.os.SystemClock;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Button;

/** Pantalla privada: BACK del servicio se limita a este ensayo voluntario. */
public final class SafeBackTestActivity extends Activity {
    private boolean requested=false;
    private long started=0L;
    @Override protected void onCreate(Bundle state){
        super.onCreate(state);
        LinearLayout layout=new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setPadding(24,48,24,24);
        layout.setBackgroundColor(Color.rgb(15,25,36));
        TextView marker=new TextView(this);
        marker.setId(R.id.kairos_back_test_marker);
        marker.setText("PRUEBA DE REGRESO EN KAIRÓS");
        marker.setTextColor(Color.WHITE);
        marker.setTextSize(21);
        layout.addView(marker);
        TextView status=new TextView(this);
        status.setText("Solo esta pantalla interna puede ser cerrada por el servicio.");
        status.setTextColor(Color.WHITE);status.setTextSize(16);
        layout.addView(status);
        Button action=new Button(this);
        action.setAllCaps(false);action.setText("SOLICITAR REGRESO SEGURO");
        action.setOnClickListener(v->{
            action.setEnabled(false);
            started=SystemClock.uptimeMillis();
            requested=true;
            if(!KairosAccessibility.backFromOwnTestScreen()){
                requested=false;
                status.setText("SIN CONFIRMACIÓN: no se ejecutó regreso.");
                action.setEnabled(true);
                return;
            }
            status.setText("Android aceptó la solicitud; verificando cierre...");
            action.postDelayed(()->{
                if(!isFinishing()&&!isDestroyed()){
                    requested=false;action.setEnabled(true);
                    status.setText("REGRESO NO CONFIRMADO: puede probar de nuevo.");
                }
            },2500L);
        });
        layout.addView(action);
        setContentView(layout);
    }
    @Override protected void onDestroy(){
        if(requested&&isFinishing()&&SystemClock.uptimeMillis()-started<=3000L)
            CommandReceiptStore.mark(this,
                "REGRESO LOCAL CONFIRMADO: pantalla de ensayo cerrada tras Accesibilidad");
        super.onDestroy();
    }
}
