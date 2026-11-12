#!/usr/bin/env python3
"""Regresión SJM de entregas entre 14 estaciones con SQLite real e I/O aislado.
NO usa credenciales ni endpoints de producción; ningún envío o aviso real.
"""
import json, sqlite3, time
STATIONS=14
REGIONS=("LATAM","US_CANADA","EUROPE","MENA","ASIA_OCEANIA","AFRICA")
CATEGORIES=("employment","donation","funding","alliance","client","sponsor")
class Belt:
    def __init__(self):
        self.db=sqlite3.connect(":memory:")
        self.db.execute("create table delivery(case_id text, stage int, ack int, primary key(case_id,stage))")
        self.db.execute("create table sources(source text primary key,case_id text)")
        self.db.execute("create table outbox(case_id text primary key)")
        self.db.execute("create table alerts(case_id text primary key)")
        self.broken_links=set()
        self.languages={"es"}
    def run(self,key,source,language="es",approved=True,eligible=True):
        for station in range(1,STATIONS+1):
            if station>1 and not self.db.execute(
                "select ack from delivery where case_id=? and stage=?",
                (key,station-1)).fetchone():
                return {"status":"STOPPED","station":station-1,"reason":"MISSING_TRANSFER_ACK"}
            if station==3:
                fingerprint=source
            if station==5:
                owner=self.db.execute("select case_id from sources where source=?",(source,)).fetchone()
                if owner and owner[0]!=key:
                    return {"status":"STOPPED","station":5,"reason":"DUPLICATE"}
                self.db.execute("insert or ignore into sources values (?,?)",(source,key))
            if station==6 and not eligible:
                return {"status":"STOPPED","station":6,"reason":"INELIGIBLE"}
            if station==8 and language not in self.languages:
                return {"status":"STOPPED","station":8,"reason":"MISSING_LANGUAGE_ADAPTER"}
            if station==9 and not approved:
                return {"status":"STOPPED","station":9,"reason":"OWNER_APPROVAL_REQUIRED"}
            if station<STATIONS and (station,station+1) in self.broken_links:
                return {"status":"STOPPED","station":station,"reason":"MISSING_TRANSFER_ACK"}
            if station==10:
                self.db.execute("insert or ignore into outbox values (?)",(key,))
            if station==14:
                self.db.execute("insert or ignore into alerts values (?)",(key,))
            self.db.execute("insert into delivery values (?,?,1) on conflict(case_id,stage) do update set ack=1",
                            (key,station))
        return {"status":"COMPLETE_SYNTHETIC","station":STATIONS}
    def count(self,table):
        return self.db.execute("select count(*) from "+table).fetchone()[0]

def suite():
    clock=time.monotonic()
    results=[]
    for index in range(1,STATIONS):
        belt=Belt()
        key="RELAY-%d"%index
        belt.broken_links.add((index,index+1))
        bad=belt.run(key,"mock://%d"%index)
        assert bad=={"status":"STOPPED","station":index,"reason":"MISSING_TRANSFER_ACK"},bad
        belt.broken_links.remove((index,index+1))
        good=belt.run(key,"mock://%d"%index)
        assert good["status"]=="COMPLETE_SYNTHETIC",good
        assert belt.run(key,"mock://%d"%index)["status"]=="COMPLETE_SYNTHETIC"
        assert belt.count("outbox")==1 and belt.count("alerts")==1
        results.append({"link":"%d->%d"%(index,index+1),"detected":True,"corrected":True,"replayed":True})
    belt=Belt()
    english=belt.run("ENGLISH","mock://en","en")
    assert english["station"]==8
    belt.languages.add("en")
    assert belt.run("ENGLISH","mock://en","en")["station"]==14
    assert belt.run("ENGLISH","mock://en","en")["station"]==14
    assert belt.count("outbox")==1 and belt.count("alerts")==1
    unauthorized=Belt()
    bad=unauthorized.run("NO-CONSENT","mock://permit",approved=False)
    assert bad["station"]==9 and unauthorized.count("outbox")==0,bad
    batch=Belt()
    for region in REGIONS:
        for category in CATEGORIES:
            for i in range(5):
                key="%s/%s/%d"%(region,category,i)
                result=batch.run(key,"mock://"+key)
                assert result["station"]==14,result
    assert batch.count("outbox")==180 and batch.count("alerts")==180
    duplicates=Belt()
    assert duplicates.run("DUP-ONE","mock://shared")["station"]==14
    duplicate=duplicates.run("DUP-TWO","mock://shared")
    assert duplicate["station"]==5 and duplicate["reason"]=="DUPLICATE",duplicate
    assert duplicates.count("outbox")==1
    return {"label":"SIMULATION_WITH_REAL_SQLITE_ACK_MECHANICS","stations":14,
            "transition_breaks_detected_and_recovered":13,"english_break_detected_and_recovered":True,
            "authorization_remains_blocked":True,"duplicate_source_blocked":True,"test_cases":196,
            "consecutive_completed":180,"replay_no_duplicate":True,
            "real_deployed_chain_verified":False,"submissions_sent":0,"android_ack":0,
            "elapsed_ms":round(1000*(time.monotonic()-clock),2),"link_results":results}
if __name__=="__main__":
    print(json.dumps(suite(),indent=2))
