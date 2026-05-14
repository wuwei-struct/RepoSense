import os
import zipfile
from .utils import safe_join, is_ignored
def import_input(input_path, work_dir, budget):
    if os.path.isdir(input_path):
        return input_path
    if zipfile.is_zipfile(input_path):
        return unpack_zip(input_path, work_dir, budget)
    raise ValueError("unsupported input")
def unpack_zip(zip_path, work_dir, budget):
    z = zipfile.ZipFile(zip_path, "r")
    names = z.namelist()
    if len(names) > budget.get("zip_max_files", 20000):
        raise ValueError("zip file count over budget")
    total = 0
    for n in names:
        if ".." in n or n.startswith("/") or n.startswith("\\"):
            raise ValueError("zip path traversal")
        info = z.getinfo(n)
        total += info.file_size
        if info.compress_size > budget.get("zip_max_compress_size_single", 64 * 1024 * 1024):
            raise ValueError("zip entry too large compressed")
    if total > budget.get("zip_max_total_size", 512 * 1024 * 1024):
        raise ValueError("zip total size over budget")
    out_dir = safe_join(work_dir, "unpacked")
    os.makedirs(out_dir, exist_ok=True)
    for n in names:
        if n.endswith("/"):
            continue
        dst = safe_join(out_dir, n)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with z.open(n) as src, open(dst, "wb") as f:
            f.write(src.read())
    return out_dir

