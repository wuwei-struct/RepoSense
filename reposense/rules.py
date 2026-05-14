import os
import json
import re
import yaml
def load_ruleset(ruleset_dir):
    rules_path = os.path.join(ruleset_dir, "rules.yaml")
    with open(rules_path, "r", encoding="utf-8") as f:
        text = f.read()
    rules = parse_rules_yaml(text)
    ver_path = os.path.join(ruleset_dir, "ruleset_version.json")
    with open(ver_path, "r", encoding="utf-8") as f:
        version = json.load(f)
    return {"rules": rules, "version": version}
def parse_rules_yaml(text):
    data = yaml.safe_load(text) or []
    return data if isinstance(data, list) else []

