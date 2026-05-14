def classify_question(question):
    q = str(question or "").strip().lower()
    if not q:
        return "unsupported"
    rules = [
        ("evidence", ["证据", "为什么", "哪个文件", "行号", "依据", "evidence", "line", "file"]),
        ("risk", ["风险", "安全", "问题", "危险", "修", "risk", "priority", "fix"]),
        ("flow", ["流程", "怎么走", "调用", "路径", "顺序", "flow", "chain"]),
        ("summary", ["是什么", "做什么", "概览", "总结", "技术栈", "结构", "summary", "overview", "stack"]),
    ]
    hits = []
    for t, keys in rules:
        if any(k in q for k in keys):
            hits.append(t)
    if not hits:
        return "unsupported"
    pri = {"evidence": 0, "risk": 1, "flow": 2, "summary": 3}
    hits.sort(key=lambda x: pri.get(x, 9))
    return hits[0]
