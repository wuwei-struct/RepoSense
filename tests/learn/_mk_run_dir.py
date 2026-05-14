import os, json, sqlite3, tempfile, shutil
def mk_run_dir():
    td = tempfile.mkdtemp(prefix="learn-run-")
    # minimal directories
    os.makedirs(os.path.join(td, "evidence"), exist_ok=True)
    # sqlite minimal schema
    conn = sqlite3.connect(os.path.join(td, "detections.sqlite"))
    c = conn.cursor()
    c.execute("create table evidence(eid integer primary key, path text, start_line integer, end_line integer, snippet text, sha256 text, parse_level text, node_type text)")
    c.execute("create table findings(fid integer primary key, concept text, rule_id text, confidence real, primary_eid integer, meta_json text)")
    c.execute("create table finding_evidence(fid integer, eid integer)")
    # insert evidence
    c.execute("insert into evidence(eid,path,start_line,end_line,snippet,sha256,parse_level,node_type) values(1,?,?,?,?,'hash','L2','')", ("docker-compose.yml",4,10,"services:\n  api:\n    image: redis"))
    # insert finding
    meta = json.dumps({"service_name":"api","infra_kind":"rabbitmq","infra_type":"queue"})
    c.execute("insert into findings(fid,concept,rule_id,confidence,primary_eid,meta_json) values(12,'Queue','L2_COMPOSE_QUEUE',0.72,1,?)", (meta,))
    c.execute("insert into finding_evidence(fid,eid) values(12,1)")
    conn.commit()
    conn.close()
    # evidence JSON
    with open(os.path.join(td, "evidence", "E1.json"), "w", encoding="utf-8") as f:
        json.dump({"path":"docker-compose.yml","start_line":4,"end_line":10,"snippet":"services:\n  api:\n    image: redis","sha256":"hash","parse_level":"L2","node_type":""}, f)
    # manifest/meta
    with open(os.path.join(td, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump({"repo_root": td}, f)
    os.makedirs(os.path.join(td, "meta"), exist_ok=True)
    with open(os.path.join(td, "meta", "config.json"), "w", encoding="utf-8") as f:
        json.dump({"budget":{}}, f)
    return td
