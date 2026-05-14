import warnings
from .verifier import run_verify
from .gate import run_gate_policy
from .sarif import run_export_sarif
def run_selfcheck(run_dir, policy=None, sarif=False, strict=False):
    if strict:
        warnings.simplefilter("error", ResourceWarning)
    run_verify(run_dir, False)
    ok = True
    if policy:
        ok = run_gate_policy(run_dir, policy, True)
    if sarif:
        from os import path
        outp = path.join(run_dir, "exports", "reposense.sarif.json")
        run_export_sarif(run_dir, outp)
    return ok
