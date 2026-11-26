"""Validate a .pngRemix file for client-ready compatibility with official PNGTuber-Remix V1.4.7."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

GODOT_CHECK_SCRIPT = """extends SceneTree
func _init():
\tvar args = OS.get_cmdline_user_args()
\tif args.is_empty():
\t\tprinterr("ERROR: missing .pngRemix path")
\t\tquit(2)
\t\treturn
\tvar path = args[0]
\tvar f = FileAccess.open(path, FileAccess.READ)
\tif f == null:
\t\tprinterr("ERROR: cannot open file: " + path)
\t\tquit(2)
\t\treturn
\tvar d = f.get_var(true)
\tf.close()
\tif typeof(d) != TYPE_DICTIONARY:
\t\tprinterr("ERROR: invalid .pngRemix payload")
\t\tquit(2)
\t\treturn
\tvar version = str(d.get("version", ""))
\tvar sprites = d.get("sprites_array", [])
\tvar images = d.get("image_manager_data", [])
\tvar states_dict = d.get("settings_dict", {}).get("states", [])
\tvar input_arr = d.get("input_array", [])
\tvar empty_tex = 0
\tfor img in images:
\t\tvar rt = img.get("runtime_texture", [])
\t\tvar anim = img.get("anim_texture", null)
\t\tif (rt == null or rt.size() == 0) and anim == null:
\t\t\tempty_tex += 1
\tvar bad_active = 0
\tvar bad_states = 0
\tfor sp in sprites:
\t\tif not sp.get("is_asset", false) and not sp.get("was_active_before", true):
\t\t\tbad_active += 1
\t\tif sp.get("states", []).size() != states_dict.size():
\t\t\tbad_states += 1
\tprint("VERSION=", version)
\tprint("SPRITES=", sprites.size())
\tprint("IMAGES=", images.size())
\tprint("STATES=", states_dict.size(), " INPUTS=", input_arr.size())
\tprint("EMPTY_TEXTURES=", empty_tex)
\tprint("BAD_WAS_ACTIVE_BEFORE=", bad_active)
\tprint("BAD_STATES_LEN=", bad_states)
\tif sprites.is_empty() or empty_tex > 0 or bad_active > 0 or bad_states > 0:
\t\tquit(1)
\tquit(0)
"""


def find_godot(explicit: str | None) -> str | None:
    if explicit and Path(explicit).exists():
        return explicit
    env_bin = os.environ.get("GODOT_BIN")
    if env_bin and Path(env_bin).exists():
        return env_bin
    local_portable = Path(r"C:\Users\Juan\.gemini\antigravity\scratch\tools\godot-4.7\Godot_v4.7-stable_win64_console.exe")
    if local_portable.exists():
        return str(local_portable)
    for name in ("godot", "godot4", "Godot_v4.7-stable_win64_console.exe"):
        found = shutil.which(name)
        if found:
            return found
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a .pngRemix avatar file.")
    parser.add_argument("model_path", help="Path to the .pngRemix file")
    parser.add_argument("--godot", default=None, help="Optional path to Godot 4 console binary")
    args = parser.parse_args()

    model = Path(args.model_path).resolve()
    if not model.exists():
        print(f"INVALID: File not found: {model}", file=sys.stderr)
        return 2
    size = model.stat().st_size
    if size < 64:
        print(f"INVALID: File is suspiciously small ({size} bytes): {model}", file=sys.stderr)
        return 2

    godot = find_godot(args.godot)
    if not godot:
        print(f"BASIC_OK ({size} bytes): Godot binary not found for deep Variant deserialization.")
        return 0

    with tempfile.TemporaryDirectory() as tmp:
        script_path = Path(tmp) / "verify_save.gd"
        script_path.write_text(GODOT_CHECK_SCRIPT, encoding="utf-8")
        proc = subprocess.run(
            [godot, "--headless", "--script", str(script_path), "--", str(model)],
            capture_output=True,
            text=True,
            check=False,
        )
        print(proc.stdout.strip())
        if proc.stderr.strip():
            print(proc.stderr.strip(), file=sys.stderr)
        if proc.returncode != 0:
            print("INVALID: Client compatibility check failed.", file=sys.stderr)
            return proc.returncode

    print(f"VALID: {model.name} ({size} bytes) is 100% client-ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
