import os
for f in ['patch_main.py', 'patch_routes.py', 'diag_ad.py', 'check_meta.py', 'check_ig.py', 'check_graph.py']:
    if os.path.exists(f):
        os.remove(f)
        print(f"Removed {f}")
