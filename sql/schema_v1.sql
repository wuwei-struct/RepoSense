PRAGMA user_version=1;
CREATE TABLE IF NOT EXISTS files(path TEXT PRIMARY KEY, lang TEXT, size INTEGER, sha256 TEXT, mtime INTEGER);
CREATE TABLE IF NOT EXISTS symbols(name TEXT, path TEXT, start_line INTEGER, end_line INTEGER);
CREATE TABLE IF NOT EXISTS calls(caller TEXT, callee TEXT, path TEXT, line INTEGER);
CREATE TABLE IF NOT EXISTS text_hits(path TEXT, rule_id TEXT, start_line INTEGER, end_line INTEGER);
CREATE TABLE IF NOT EXISTS evidence(eid INTEGER PRIMARY KEY, path TEXT, start_line INTEGER, end_line INTEGER, snippet TEXT, sha256 TEXT, parse_level TEXT, node_type TEXT);
CREATE TABLE IF NOT EXISTS findings(fid INTEGER PRIMARY KEY, concept TEXT, rule_id TEXT, confidence REAL, primary_eid INTEGER, meta_json TEXT);
CREATE TABLE IF NOT EXISTS finding_evidence(fid INTEGER, eid INTEGER);
CREATE TABLE IF NOT EXISTS events(event_id INTEGER PRIMARY KEY, type TEXT, key TEXT, confidence REAL, meta_json TEXT);
CREATE TABLE IF NOT EXISTS event_links(src_event INTEGER, dst_event INTEGER, kind TEXT);

