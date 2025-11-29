# utils/env_loader.py
"""
Environment loader for local DLLs and runtimes.

Ensures that WeasyPrint and other native dependencies
load only from the local 'bin' directory — no system dependencies required.
"""

import os
import sys
import ctypes


def setup_local_dlls():
    """
    Force Windows to load DLLs from ./bin instead of system PATH.
    Call this before importing WeasyPrint or any C-extensions.
    """
    # Locate project root and bin folder
    app_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(app_dir, ".."))
    bin_path = os.path.join(project_root, "bin")

    if not os.path.exists(bin_path):
        print(f"⚠️  bin directory not found at: {bin_path}")
        return

    # --- Add DLL search path (Python 3.8+ supports this) ---
    try:
        os.add_dll_directory(bin_path)
        print(f"🧩 Added DLL search path: {bin_path}")
    except (AttributeError, OSError):
        # Fallback for older Python versions
        os.environ["PATH"] = bin_path + os.pathsep + os.environ["PATH"]
        print(f"🧩 PATH updated with: {bin_path}")

    # --- Preload MSVC runtime DLLs ---
    runtime_dlls = ["vcruntime140.dll", "vcruntime140_1.dll", "msvcp140.dll"]
    for dll_name in runtime_dlls:
        dll_path = os.path.join(bin_path, dll_name)
        if os.path.exists(dll_path):
            try:
                ctypes.WinDLL(dll_path)
                print(f"✅ Preloaded {dll_name}")
            except OSError as e:
                print(f"⚠️ Failed to preload {dll_name}: {e}")
        else:
            print(f"⚠️ Missing {dll_name} in {bin_path}")

    print("✅ Local DLL environment ready.")
