from pxr import Usd, Sdf
import os, shutil

TEXTURE_EXTENSIONS = {'.tx', '.rat'}
USD_EXTENSIONS = {'.usd', '.usda', '.usdc'}

FALLBACK_LOG = []
dry_run = True  # Default; gets overridden

def is_texture_file(path):
    return os.path.splitext(path)[1].lower() in TEXTURE_EXTENSIONS

def is_usd_file(path):
    return os.path.splitext(path)[1].lower() in USD_EXTENSIONS

def normalize_path(path):
    path = os.path.abspath(path)
    if os.name == 'nt':
        drive, rest = os.path.splitdrive(path)
        path = drive.upper() + rest
    return path

def resolve_path(base_layer_path, asset_path, search_dirs=None):
    if os.path.isabs(asset_path):
        abs_path = normalize_path(asset_path)
        return abs_path if os.path.exists(abs_path) else None

    base_dir = os.path.dirname(base_layer_path)
    abs_path = normalize_path(os.path.join(base_dir, asset_path))
    if os.path.exists(abs_path):
        return abs_path

    if search_dirs:
        asset_path_parts = os.path.normpath(asset_path).split(os.sep)
        filename = asset_path_parts[-1]
        partial_folder = os.path.join(*asset_path_parts[-2:]) if len(asset_path_parts) > 1 else filename

        for root in search_dirs:
            for dirpath, _, files in os.walk(root):
                candidate = os.path.join(dirpath, filename)
                norm_candidate = normalize_path(candidate)
                if filename in files and partial_folder in norm_candidate:
                    print(f"[Fallback Match] '{asset_path}' → '{norm_candidate}'")
                    FALLBACK_LOG.append((asset_path, norm_candidate))
                    return norm_candidate

        for root in search_dirs:
            for dirpath, _, files in os.walk(root):
                if filename in files:
                    full_path = normalize_path(os.path.join(dirpath, filename))
                    print(f"[Fuzzy Match] '{asset_path}' → '{full_path}'")
                    FALLBACK_LOG.append((asset_path, full_path))
                    return full_path

    return None

def copy_with_structure_from_root(source_path, asset_library_root, dest_root):
    source_path = normalize_path(source_path)
    asset_library_root = normalize_path(asset_library_root)
    rel_path = os.path.relpath(source_path, asset_library_root)
    dest_path = os.path.join(dest_root, rel_path)

    os.makedirs(os.path.dirname(dest_path), exist_ok=True)

    if not os.path.exists(dest_path):
        if not dry_run:
            shutil.copy2(source_path, dest_path)
        print(f"Copied: {source_path} → {dest_path}")
    else:
        print(f"Exists: {dest_path}")

def gather_dependencies(layer_path, dest_root, visited=None, search_dirs=None):
    if visited is None:
        visited = set()

    layer_path = normalize_path(layer_path)
    if layer_path in visited:
        return
    visited.add(layer_path)

    try:
        stage = Usd.Stage.Open(layer_path)
    except Exception as e:
        print(f"Failed to open: {layer_path} - {e}")
        return

    copy_with_structure_from_root(layer_path, search_dirs[0], dest_root)

    for layer in stage.GetUsedLayers():
        layer_file = normalize_path(layer.identifier)
        if os.path.exists(layer_file):
            copy_with_structure_from_root(layer_file, search_dirs[0], dest_root)

    for prim in stage.Traverse():
        for attr in prim.GetAttributes():
            if not attr.HasAuthoredValueOpinion():
                continue
            val = attr.Get()
            if isinstance(val, Sdf.AssetPath):
                asset_path = val.path
                if not asset_path:
                    continue

                resolved = resolve_path(layer_path, asset_path, search_dirs)
                if not resolved:
                    print(f"[Missing] {asset_path} (from {layer_path})")
                    continue

                if is_texture_file(resolved) or is_usd_file(resolved):
                    copy_with_structure_from_root(resolved, search_dirs[0], dest_root)

                if is_usd_file(resolved):
                    gather_dependencies(resolved, dest_root, visited, search_dirs)

def copy_usd_and_all_dependencies(usd_path, dest_folder, search_root, dry_run_stat=True):
    global dry_run
    dry_run = dry_run_stat

    usd_path = normalize_path(usd_path)
    dest_folder = normalize_path(dest_folder)
    search_root = normalize_path(search_root)

    os.makedirs(dest_folder, exist_ok=True)
    search_dirs = [search_root]

    gather_dependencies(usd_path, dest_folder, visited=set(), search_dirs=search_dirs)

    # Write fallback resolution log
    log_path = os.path.join(dest_folder, "_fallback_matches.txt")
    with open(log_path, 'w') as log_file:
        for original, found in FALLBACK_LOG:
            log_file.write(f"{original} → {found}\n")

    print(f"\n[Fallback Log written to] {log_path}")
    print(f"Dry run: {dry_run}")
