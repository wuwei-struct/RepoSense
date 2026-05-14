import os
AST_AVAILABLE = True
_languages = {}
_parsers = {}
try:
    from tree_sitter import Parser
    from tree_sitter_languages import get_language
except Exception:
    AST_AVAILABLE = False
def lang_from_ext(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in [".py"]:
        return "python"
    if ext in [".js", ".jsx"]:
        return "javascript"
    if ext in [".ts", ".tsx"]:
        return "typescript"
    return None
def get_parser(lang):
    if not AST_AVAILABLE or not lang:
        return None
    if lang not in _parsers:
        language = get_language(lang)
        p = Parser()
        p.set_language(language)
        _languages[lang] = language
        _parsers[lang] = p
    return _parsers[lang]
def parse_ast(path, text, lang, budget):
    warnings = []
    if not AST_AVAILABLE:
        warnings.append({"type": "ast_disabled", "path": path, "reason": "missing_dependencies"})
        return None, warnings
    max_bytes = int(budget.get("ast_max_bytes", 1048576))
    if len(text.encode("utf-8")) > max_bytes:
        warnings.append({"type": "ast_skipped", "path": path, "reason": "file_exceeds_budget"})
        return None, warnings
    parser = get_parser(lang)
    if not parser:
        warnings.append({"type": "ast_skipped", "path": path, "reason": "unsupported_language"})
        return None, warnings
    tree = parser.parse(text.encode("utf-8"))
    return tree, warnings
def run_matcher(matcher, tree, source_bytes, lang):
    if not AST_AVAILABLE or not tree:
        return []
    from .ast_matchers import express_route, fastapi_route, py_lock, js_concurrency
    if matcher == "express_route":
        return express_route(tree, source_bytes, lang)
    if matcher == "fastapi_route":
        return fastapi_route(tree, source_bytes, lang)
    if matcher == "py_lock":
        return py_lock(tree, source_bytes, lang)
    if matcher == "js_concurrency":
        return js_concurrency(tree, source_bytes, lang)
    return []
