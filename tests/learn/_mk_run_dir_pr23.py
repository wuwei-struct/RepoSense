import os
import json
import sqlite3
import tempfile


def mk_run_dir_pr23():
    td = tempfile.mkdtemp(prefix="learn-pr23-run-")
    os.makedirs(os.path.join(td, "evidence"), exist_ok=True)
    conn = sqlite3.connect(os.path.join(td, "detections.sqlite"))
    c = conn.cursor()
    c.execute("create table evidence(eid integer primary key, path text, start_line integer, end_line integer, snippet text, sha256 text, parse_level text, node_type text)")
    c.execute("create table findings(fid integer primary key, concept text, rule_id text, confidence real, primary_eid integer, meta_json text)")
    c.execute("create table finding_evidence(fid integer, eid integer)")
    c.execute("create table events(event_id integer primary key, type text, key text, confidence real, meta_json text)")
    eid = 1
    fid = 1
    ev_id = 1
    for i in range(12):
        p = f"svc/tx_{i}.java"
        sn = "@Transactional public void run(){ repo.save(x); }"
        c.execute("insert into evidence(eid,path,start_line,end_line,snippet,sha256,parse_level,node_type) values(?,?,?,?,?,'h','L2','')", (eid, p, 10, 12, sn))
        meta = json.dumps({"language": "java", "tx.kind": "java_transactional", "framework": "spring"})
        c.execute("insert into findings(fid,concept,rule_id,confidence,primary_eid,meta_json) values(?,?,?,?,?,?)", (fid, "Transaction", "java_transactional_l2", 0.9, eid, meta))
        c.execute("insert into finding_evidence(fid,eid) values(?,?)", (fid, eid))
        c.execute("insert into events(event_id,type,key,confidence,meta_json) values(?,?,?,?,?)", (ev_id, "tx_boundary", f"k{ev_id}", 0.9, json.dumps({"path": p})))
        ev_id += 1
        c.execute("insert into events(event_id,type,key,confidence,meta_json) values(?,?,?,?,?)", (ev_id, "db_op", f"k{ev_id}", 0.8, json.dumps({"path": p, "db.kind": "db.write"})))
        ev_id += 1
        if i % 3 == 0:
            c.execute("insert into events(event_id,type,key,confidence,meta_json) values(?,?,?,?,?)", (ev_id, "queue_dispatch", f"k{ev_id}", 0.8, json.dumps({"path": p})))
            ev_id += 1
            c.execute("insert into events(event_id,type,key,confidence,meta_json) values(?,?,?,?,?)", (ev_id, "api", f"k{ev_id}", 0.8, json.dumps({"path": p})))
            ev_id += 1
        eid += 1
        fid += 1
    for i in range(6):
        p = f"svc/idem_{i}.py"
        sn = "if cache.get(idempotency_key): return\nif repo.existsById(key): return\nrepo.save(x)"
        c.execute("insert into evidence(eid,path,start_line,end_line,snippet,sha256,parse_level,node_type) values(?,?,?,?,?,'h','L2','')", (eid, p, 20, 25, sn))
        meta = json.dumps({"language": "python", "framework": "django"})
        c.execute("insert into findings(fid,concept,rule_id,confidence,primary_eid,meta_json) values(?,?,?,?,?,?)", (fid, "DB", "idempotency_guard_l2", 0.88, eid, meta))
        c.execute("insert into finding_evidence(fid,eid) values(?,?)", (fid, eid))
        c.execute("insert into events(event_id,type,key,confidence,meta_json) values(?,?,?,?,?)", (ev_id, "db_op", f"k{ev_id}", 0.8, json.dumps({"path": p, "db.kind": "db.read"})))
        ev_id += 1
        eid += 1
        fid += 1
    for i in range(6):
        p = f"svc/lock_{i}.java"
        sn = "synchronized(this){ lock.acquire(); critical(); }"
        c.execute("insert into evidence(eid,path,start_line,end_line,snippet,sha256,parse_level,node_type) values(?,?,?,?,?,'h','L2','')", (eid, p, 30, 32, sn))
        meta = json.dumps({"language": "java", "framework": "spring"})
        c.execute("insert into findings(fid,concept,rule_id,confidence,primary_eid,meta_json) values(?,?,?,?,?,?)", (fid, "DB", "lock_guard_l2", 0.87, eid, meta))
        c.execute("insert into finding_evidence(fid,eid) values(?,?)", (fid, eid))
        c.execute("insert into events(event_id,type,key,confidence,meta_json) values(?,?,?,?,?)", (ev_id, "db_op", f"k{ev_id}", 0.8, json.dumps({"path": p, "db.kind": "db.write"})))
        ev_id += 1
        if i % 2 == 0:
            c.execute("insert into events(event_id,type,key,confidence,meta_json) values(?,?,?,?,?)", (ev_id, "tx_boundary", f"k{ev_id}", 0.8, json.dumps({"path": p})))
            ev_id += 1
        eid += 1
        fid += 1
    conn.commit()
    conn.close()
    for i in range(1, eid):
        with open(os.path.join(td, "evidence", f"E{i}.json"), "w", encoding="utf-8") as f:
            json.dump({"eid": f"E{i}"}, f)
    with open(os.path.join(td, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump({"repo_root": td}, f)
    os.makedirs(os.path.join(td, "meta"), exist_ok=True)
    with open(os.path.join(td, "meta", "config.json"), "w", encoding="utf-8") as f:
        json.dump({"budget": {}}, f)
    return td
