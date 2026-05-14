import os
import sqlite3
def _apply_schema(conn, schema_path):
    with open(schema_path, "r", encoding="utf-8") as f:
        sql = f.read()
    conn.executescript(sql)
    conn.commit()
def init_indices_db(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    conn = sqlite3.connect(path)
    _apply_schema(conn, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sql", "schema_v1.sql")))
    return conn
def init_detections_db(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    conn = sqlite3.connect(path)
    _apply_schema(conn, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sql", "schema_v1.sql")))
    return conn
def ensure_schema(conn):
    req = ["files","symbols","calls","text_hits","evidence","findings","finding_evidence","events","event_links"]
    c = conn.cursor()
    got = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    for t in req:
        if t not in got:
            raise RuntimeError(f"missing table: {t}")
    v = c.execute("PRAGMA user_version").fetchone()[0]
    if v != 1:
        raise RuntimeError("invalid schema version")
    return True
def insert_file(conn, info):
    c = conn.cursor()
    c.execute("insert or replace into files(path, lang, size, sha256, mtime) values(?,?,?,?,?)", (info["path"], info["lang"], info["size"], info["sha256"], info["mtime"]))
    conn.commit()
def insert_text_hit(conn, path, rule_id, start_line, end_line):
    c = conn.cursor()
    c.execute("insert into text_hits(path, rule_id, start_line, end_line) values(?,?,?,?)", (path, rule_id, start_line, end_line))
    conn.commit()
def insert_evidence(conn, e):
    c = conn.cursor()
    c.execute("insert into evidence(path, start_line, end_line, snippet, sha256, parse_level, node_type) values(?,?,?,?,?,?,?)", (e["path"], e["start_line"], e["end_line"], e["snippet"], e["sha256"], e["parse_level"], e.get("node_type")))
    eid = c.lastrowid
    conn.commit()
    return eid
def insert_finding(conn, f, primary_eid, meta_json):
    c = conn.cursor()
    c.execute("insert into findings(concept, rule_id, confidence, primary_eid, meta_json) values(?,?,?,?,?)", (f["concept"], f["rule_id"], float(f["confidence"]), primary_eid, meta_json))
    fid = c.lastrowid
    conn.commit()
    return fid
def link_finding_evidence(conn, fid, eid):
    c = conn.cursor()
    c.execute("insert into finding_evidence(fid, eid) values(?,?)", (fid, eid))
    conn.commit()
def insert_event(conn, type_, key, confidence, meta_json):
    c = conn.cursor()
    c.execute("insert into events(type, key, confidence, meta_json) values(?,?,?,?)", (type_, key, confidence, meta_json))
    eid = c.lastrowid
    conn.commit()
    return eid

