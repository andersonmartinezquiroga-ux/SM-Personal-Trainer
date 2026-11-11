#!/usr/bin/env python3
"""Batería rápida, adversarial y aislada de la banda SJM.

NO integra producción. No puede enviar a terceros ni generar acuses reales.
Objetivo: cientos de escenarios en <=120 s y reporte con verdades verificables.
"""
import json
import time
from sjm_factory_canary import Factory

REGIONS=("LATAM_CARIBE","USA_CANADA","EUROPA","MENA","ASIA_OCEANIA","AFRICA")
CATEGORIES=("empleo","donacion_pc","financiacion","patrocinio","alianza","clientes")
RESPONSES=("interested","rejected","no_response")
FAILS=tuple(range(1,15))

def fixture(caseid,region="LATAM_CARIBE",category="alianza",answer="interested",variant=0,**kw):
    data=dict(id=caseid,project="SJM-"+category,region=region,
              goal="Caso ficticio: "+category,source="mock://"+region+"/"+category+"/"+str(variant),
              days=19,response=answer,approval=True,no_fee=True,eligible=True)
    data.update(kw)
    return data

def suite():
    start=time.monotonic()
    counts={"complete":0,"fault_injection":0,"blocked_policy":0,"duplicate":0,"retry":0}
    anomalies=[]
    group_counts={}
    for region in REGIONS:
        for category in CATEGORIES:
            for v in range(9):
                c=fixture("SIM-"+region+"-"+category+"-"+str(v),region,category,RESPONSES[v%3],v)
                r=Factory().run(c)
                if r["status"]!="SIMULATION_PASS" or len(r["steps"])!=14:
                    anomalies.append([c["id"],r["status"],r["blocking_station"]])
                else: counts["complete"]+=1
                group_counts[category]=group_counts.get(category,0)+1
    for n in FAILS:
        r=Factory().run(fixture("INJECT-"+str(n)),fault=n)
        if r["status"]!="SIMULATION_BLOCKED" or r["blocking_station"]!=n:
            anomalies.append(["fault",n,r["status"],r["blocking_station"]])
        else: counts["fault_injection"]+=1
    policy_cases=[
      (fixture("NO-OBJECTIVE",goal=""),1),
      (fixture("WRONG-PROTOCOL",source="https://company.test/"),2),
      (fixture("NO-FEE",no_fee=False),6),
      (fixture("NO-ELIGIBLE",eligible=False),6),
      (fixture("NO-CONSENT",approval=False),9),
      (fixture("BAD-TIME",days=-1),13),
      (fixture("BAD-ANSWER",response="approved"),14),
    ]
    for case,expected in policy_cases:
        r=Factory().run(case)
        if r["status"]!="SIMULATION_BLOCKED" or r["blocking_station"]!=expected:
            anomalies.append(["policy",case["id"],r["blocking_station"]])
        else: counts["blocked_policy"]+=1
    fac=Factory()
    a=fixture("DUP-A",variant=100)
    first=fac.run(a)
    twice=fac.run(dict(a,id="DUP-B"))
    if first["status"]=="SIMULATION_PASS" and twice["blocking_station"]==5:
        counts["duplicate"]+=1
    else: anomalies.append(["duplicate",first["status"],twice["blocking_station"]])
    # Evidencia de limitación: si falla en estación 10 el mismo expediente
    # no puede reintentarse en el simulador actual (se bloquea en deduplicación).
    fac_retry=Factory()
    a=fixture("RETRY-1",variant=101)
    failed=fac_retry.run(a,fault=10)
    retry=fac_retry.run(a)
    retry_issue=(failed["blocking_station"]==10 and retry["blocking_station"]==5)
    if retry_issue:
        counts["retry"]+=1 # problema correctamente detectado, NO reparación
    else: anomalies.append(["retry",failed["blocking_station"],retry["blocking_station"]])
    elapsed=round((time.monotonic()-start)*1000,2)
    assert elapsed < 120_000
    assert not anomalies,anomalies
    return {"scope":"SIMULACION_AISLADA","real_end_to_end_verified":False,
            "production_changes":0,"emails_sent":0,"real_phone_ack":0,
            "budget_ms":120000,"elapsed_ms":elapsed,
            "total_scenarios":sum(counts.values()),
            "counters":counts,"categories":group_counts,"regions":list(REGIONS),
            "known_limitation":"RETRY_SAME_CASE_BLOCKED_AT_STATION_5_AFTER_FAILURE_AT_10",
            "outcome":"SIMULATOR_PASS_WITH_IDENTIFIED_RETRY_DEFECT"}

if __name__=="__main__":
    print(json.dumps(suite(),ensure_ascii=False,indent=2))
