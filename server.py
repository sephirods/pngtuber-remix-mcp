"""MCP server for authoring, rigging, animating, and exporting PNGTuber-Remix models."""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
from pathlib import Path
from typing import Any

import websockets
from mcp.server.mcpserver import MCPServer

WS_URL = os.environ.get("PNGTUBER_WS_URL", "ws://localhost:9321")
REQUEST_TIMEOUT_SECONDS = 15.0
BASE_DIR = Path(__file__).resolve().parent


def _resolve_studio_exe() -> Path:
    env_exe = os.environ.get("PNGTUBER_STUDIO_EXE")
    if env_exe:
        return Path(env_exe)
    for candidate in (
        BASE_DIR / "PNGTubeRemix-Studio-MCP" / "PNGTube Remix.exe",
        BASE_DIR / "dist" / "PNGTubeRemix-Studio-MCP" / "PNGTube Remix.exe",
    ):
        if candidate.exists():
            return candidate
    return BASE_DIR / "dist" / "PNGTubeRemix-Studio-MCP" / "PNGTube Remix.exe"


DEFAULT_STUDIO_EXE = _resolve_studio_exe()

mcp = MCPServer("pngtuber-remix")
_studio_process: subprocess.Popen[Any] | None = None


async def _send_command(payload: dict[str, Any], timeout: float = REQUEST_TIMEOUT_SECONDS) -> dict[str, Any]:
    """Send a single JSON command to PNGTuber-Remix Studio and return the parsed reply."""
    try:
        async with websockets.connect(WS_URL, open_timeout=timeout) as ws:
            await ws.send(json.dumps(payload))
            raw = await asyncio.wait_for(ws.recv(), timeout=timeout)
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8", errors="replace")
            return json.loads(raw)
    except OSError as exc:
        return {
            "result": "failed",
            "error": (
                f"Could not connect to PNGTuber-Remix WebSocket at {WS_URL}. "
                "Call launch_studio() or ensure PNGTubeRemix-Studio-MCP is running."
            ),
            "details": str(exc),
        }
    except Exception as exc:  # noqa: BLE001
        return {"result": "failed", "error": str(exc)}


def _target_fields(
    name: str | None,
    item_id: str | None,
    name_key: str = "sprite_name",
    id_key: str = "sprite_id",
) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    if name is not None and str(name) != "":
        fields[name_key] = name
    elif item_id is not None and str(item_id) != "":
        fields[id_key] = item_id
    return fields


# ---------------------------------------------------------------------------
# Studio Lifecycle & Connection
# ---------------------------------------------------------------------------


@mcp.tool()
async def launch_studio(
    exe_path: str | None = None,
    ws_port: int = 9321,
    wait_seconds: float = 20.0,
) -> dict[str, Any]:
    """Launch PNGTubeRemix-Studio-MCP and wait until its WebSocket server responds to ping."""
    global _studio_process

    ping_res = await _send_command({"event": "ping"}, timeout=1.5)
    if ping_res.get("event") == "pong":
        return {"result": "success", "status": "already_running", "ws_url": WS_URL}

    target_exe = Path(exe_path) if exe_path else DEFAULT_STUDIO_EXE
    if not target_exe.exists():
        return {"result": "failed", "error": f"Studio executable not found: {target_exe}"}

    env = os.environ.copy()
    env["PNGTUBER_WS_PORT"] = str(ws_port)
    popen_kwargs: dict[str, Any] = {
        "cwd": str(target_exe.parent),
        "env": env,
    }
    if os.name == "nt":
        detached = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        breakaway = getattr(subprocess, "CREATE_BREAKAWAY_FROM_JOB", 0)
        try:
            _studio_process = subprocess.Popen(
                [str(target_exe), f"--ws-port={ws_port}"],
                creationflags=detached | breakaway,
                **popen_kwargs,
            )
        except OSError:
            _studio_process = subprocess.Popen(
                [str(target_exe), f"--ws-port={ws_port}"],
                creationflags=detached,
                **popen_kwargs,
            )
    else:
        _studio_process = subprocess.Popen(
            [str(target_exe), f"--ws-port={ws_port}"],
            start_new_session=True,
            **popen_kwargs,
        )

    deadline = asyncio.get_running_loop().time() + wait_seconds
    while asyncio.get_running_loop().time() < deadline:
        res = await _send_command({"event": "ping"}, timeout=1.5)
        if res.get("event") == "pong":
            return {
                "result": "success",
                "status": "launched",
                "pid": _studio_process.pid,
                "exe_path": str(target_exe),
                "ws_url": WS_URL,
            }
        if _studio_process.poll() is not None:
            return {
                "result": "failed",
                "error": f"Studio process exited early with code {_studio_process.returncode}",
            }
        await asyncio.sleep(0.5)

    return {"result": "failed", "error": f"Timed out waiting {wait_seconds}s for WebSocket at {WS_URL}"}


@mcp.tool()
async def stop_studio() -> dict[str, Any]:
    """Terminate the Studio process if launched by this MCP server."""
    global _studio_process
    if _studio_process is not None and _studio_process.poll() is None:
        _studio_process.terminate()
        try:
            _studio_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _studio_process.kill()
        pid = _studio_process.pid
        _studio_process = None
        return {"result": "success", "stopped_pid": pid}
    return {"result": "success", "status": "not_managed_or_already_stopped"}


@mcp.tool()
async def ping() -> dict[str, Any]:
    """Test the WebSocket connection to PNGTuber-Remix Studio."""
    return await _send_command({"event": "ping"})


# ---------------------------------------------------------------------------
# Project Save / Load / Reset
# ---------------------------------------------------------------------------


@mcp.tool()
async def new_project() -> dict[str, Any]:
    """Clear the current avatar and start a fresh project with 1 clean state."""
    return await _send_command({"event": "new_project"})


@mcp.tool()
async def load_model(file_path: str) -> dict[str, Any]:
    """Load an existing .pngRemix or .save model file."""
    return await _send_command({"event": "load_model", "file_path": file_path})


@mcp.tool()
async def save_model(file_path: str) -> dict[str, Any]:
    """Save the current rigged avatar to a self-contained client-compatible .pngRemix file."""
    return await _send_command({"event": "save_model", "file_path": file_path}, timeout=30.0)


# ---------------------------------------------------------------------------
# Sprite & Folder Authoring
# ---------------------------------------------------------------------------


@mcp.tool()
async def import_sprite(
    file_path: str,
    sprite_name: str | None = None,
    sprite_type: str = "Sprite2D",
    trim: bool = False,
    offset_on_trim: bool = True,
    parent: str | None = None,
    position: list[float] | None = None,
    offset: list[float] | None = None,
    scale: list[float] | None = None,
    rotation: float | None = None,
    z_index: int | None = None,
    visible: bool = True,
) -> dict[str, Any]:
    """Import a PNG/APNG/GIF/SVG image as a Sprite2D or WiggleApp layer with optional parent & transform."""
    payload: dict[str, Any] = {
        "event": "import_sprite",
        "file_path": file_path,
        "sprite_type": sprite_type,
        "trim": trim,
        "offset_on_trim": offset_on_trim,
        "visible": visible,
    }
    if sprite_name:
        payload["sprite_name"] = sprite_name
    if parent:
        payload["parent"] = parent
    if position is not None:
        payload["position"] = position
    if offset is not None:
        payload["offset"] = offset
    if scale is not None:
        payload["scale"] = scale
    if rotation is not None:
        payload["rotation"] = rotation
    if z_index is not None:
        payload["z_index"] = z_index
    return await _send_command(payload)


@mcp.tool()
async def create_folder(
    sprite_name: str = "Folder",
    parent: str | None = None,
    position: list[float] | None = None,
    z_index: int | None = None,
    visible: bool = True,
) -> dict[str, Any]:
    """Create a Folder layer for grouping child sprites."""
    payload: dict[str, Any] = {
        "event": "create_folder",
        "sprite_name": sprite_name,
        "visible": visible,
    }
    if parent:
        payload["parent"] = parent
    if position is not None:
        payload["position"] = position
    if z_index is not None:
        payload["z_index"] = z_index
    return await _send_command(payload)


@mcp.tool()
async def replace_sprite_image(
    file_path: str,
    sprite_name: str | None = None,
    sprite_id: str | None = None,
    trim: bool = False,
    offset_on_trim: bool = True,
) -> dict[str, Any]:
    """Replace a sprite's image file while keeping its hierarchy, rigging, and states intact."""
    fields = _target_fields(sprite_name, sprite_id)
    if not fields:
        return {"result": "failed", "error": "Provide either sprite_name or sprite_id."}
    return await _send_command(
        {
            "event": "replace_sprite_image",
            **fields,
            "file_path": file_path,
            "trim": trim,
            "offset_on_trim": offset_on_trim,
        }
    )


@mcp.tool()
async def reparent_sprite(
    parent: str = "",
    sprite_name: str | None = None,
    sprite_id: str | None = None,
    keep_global_position: bool = False,
) -> dict[str, Any]:
    """Reparent a sprite under another sprite/folder (or '' / '0' for root)."""
    fields = _target_fields(sprite_name, sprite_id)
    if not fields:
        return {"result": "failed", "error": "Provide either sprite_name or sprite_id."}
    return await _send_command(
        {
            "event": "reparent_sprite",
            **fields,
            "parent": parent,
            "keep_global_position": keep_global_position,
        }
    )


@mcp.tool()
async def rename_sprite(
    new_name: str,
    sprite_name: str | None = None,
    sprite_id: str | None = None,
) -> dict[str, Any]:
    """Rename a sprite or folder."""
    fields = _target_fields(sprite_name, sprite_id)
    if not fields:
        return {"result": "failed", "error": "Provide either sprite_name or sprite_id."}
    return await _send_command({"event": "rename_sprite", **fields, "new_name": new_name})


@mcp.tool()
async def delete_sprite(
    sprite_name: str | None = None,
    sprite_id: str | None = None,
    delete_children: bool = True,
) -> dict[str, Any]:
    """Delete a sprite (and optionally its children)."""
    fields = _target_fields(sprite_name, sprite_id)
    if not fields:
        return {"result": "failed", "error": "Provide either sprite_name or sprite_id."}
    return await _send_command({"event": "delete_sprite", **fields, "delete_children": delete_children})


@mcp.tool()
async def get_sprite_info(
    sprite_name: str | None = None,
    sprite_id: str | None = None,
) -> dict[str, Any]:
    """Inspect a sprite's full rigging properties, hierarchy, and state count."""
    fields = _target_fields(sprite_name, sprite_id)
    if not fields:
        return {"result": "failed", "error": "Provide either sprite_name or sprite_id."}
    return await _send_command({"event": "get_sprite_info", **fields})


@mcp.tool()
async def set_sprite_properties(
    properties: dict[str, Any],
    sprite_name: str | None = None,
    sprite_id: str | None = None,
    state_id: int | None = None,
    all_states: bool = False,
) -> dict[str, Any]:
    """Update rigging, reactions (should_blink/should_talk), physics, wiggle, transform, or asset hotkeys."""
    fields = _target_fields(sprite_name, sprite_id)
    if not fields:
        return {"result": "failed", "error": "Provide either sprite_name or sprite_id."}
    payload: dict[str, Any] = {
        "event": "set_sprite_properties",
        **fields,
        "properties": properties,
        "all_states": all_states,
    }
    if state_id is not None:
        payload["state_id"] = state_id
    return await _send_command(payload)


# ---------------------------------------------------------------------------
# State Management
# ---------------------------------------------------------------------------


@mcp.tool()
async def list_states() -> dict[str, Any]:
    """List all character states with their names, 1-based IDs, and active status."""
    return await _send_command({"event": "list_states"})


@mcp.tool()
async def set_state(state_name: str | None = None, state_id: int | None = None) -> dict[str, Any]:
    """Switch to a character state by name or 1-based state_id."""
    payload: dict[str, Any] = {"event": "state"}
    if state_name is not None:
        payload["state_name"] = state_name
    elif state_id is not None:
        payload["state_id"] = state_id
    else:
        return {"result": "failed", "error": "Provide either state_name or state_id."}
    return await _send_command(payload)


@mcp.tool()
async def add_state(
    state_name: str = "",
    hotkey: str = "",
    duplicate_current: bool = True,
    select: bool = True,
) -> dict[str, Any]:
    """Create a new state (optionally duplicating the current state), name it, and bind a hotkey."""
    payload: dict[str, Any] = {
        "event": "add_state",
        "duplicate_current": duplicate_current,
        "select": select,
    }
    if state_name:
        payload["state_name"] = state_name
    if hotkey:
        payload["hotkey"] = hotkey
    return await _send_command(payload)


@mcp.tool()
async def rename_state(
    new_name: str,
    state_name: str | None = None,
    state_id: int | None = None,
) -> dict[str, Any]:
    """Rename an existing state."""
    payload: dict[str, Any] = {"event": "rename_state", "new_name": new_name}
    if state_name is not None:
        payload["state_name"] = state_name
    elif state_id is not None:
        payload["state_id"] = state_id
    else:
        return {"result": "failed", "error": "Provide either state_name or state_id."}
    return await _send_command(payload)


@mcp.tool()
async def delete_state(
    state_name: str | None = None,
    state_id: int | None = None,
) -> dict[str, Any]:
    """Delete an existing state (cannot delete the last state)."""
    payload: dict[str, Any] = {"event": "delete_state"}
    if state_name is not None:
        payload["state_name"] = state_name
    elif state_id is not None:
        payload["state_id"] = state_id
    else:
        return {"result": "failed", "error": "Provide either state_name or state_id."}
    return await _send_command(payload)


@mcp.tool()
async def set_state_hotkey(
    hotkey: str,
    state_name: str | None = None,
    state_id: int | None = None,
) -> dict[str, Any]:
    """Bind a keyboard hotkey (e.g. '1', '2', 'F1') to a state."""
    payload: dict[str, Any] = {"event": "set_state_hotkey", "hotkey": hotkey}
    if state_name is not None:
        payload["state_name"] = state_name
    elif state_id is not None:
        payload["state_id"] = state_id
    else:
        return {"result": "failed", "error": "Provide either state_name or state_id."}
    return await _send_command(payload)


# ---------------------------------------------------------------------------
# Model Settings, Simulation & Screenshots
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_model_settings() -> dict[str, Any]:
    """Read Global.settings_dict and current state's model bounce/idle animation parameters."""
    return await _send_command({"event": "get_model_settings"})


@mcp.tool()
async def set_model_settings(
    settings: dict[str, Any] | None = None,
    model_animation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Update global model settings (blink_speed, bg_color, zoom, pan, etc.) and/or model_animation."""
    payload: dict[str, Any] = {"event": "set_model_settings"}
    if settings is not None:
        payload["settings"] = settings
    if model_animation is not None:
        payload["model_animation"] = model_animation
    return await _send_command(payload)


@mcp.tool()
async def set_ui_mode(mode: int = 0) -> dict[str, Any]:
    """Switch PNGTuber-Remix mode: 0 = Editor, 1 = Stream preview, 2 = Mesh editor."""
    return await _send_command({"event": "set_ui_mode", "mode": mode})


@mcp.tool()
async def simulate_input(
    mouth_state: str | None = None,
    blink: str | bool | None = None,
) -> dict[str, Any]:
    """Deterministically simulate talking/screaming ('auto'|'closed'|'open'|'screaming') and/or blink."""
    payload: dict[str, Any] = {"event": "simulate_input"}
    if mouth_state is not None:
        payload["mouth_state"] = mouth_state
    if blink is not None:
        payload["blink"] = blink
    return await _send_command(payload)


@mcp.tool()
async def capture_screenshot(file_path: str, source: str = "subviewport") -> dict[str, Any]:
    """Capture a PNG screenshot of the live avatar canvas ('subviewport') or full window ('window')."""
    return await _send_command({"event": "capture_screenshot", "file_path": file_path, "source": source})


# ---------------------------------------------------------------------------
# Declarative Batch Rig Builder
# ---------------------------------------------------------------------------


@mcp.tool()
async def build_rig_from_spec(spec: dict[str, Any]) -> dict[str, Any]:
    """Build an entire rigged .pngRemix character from a declarative JSON spec in one call.

    Expected spec structure:
    {
      "reset": true,
      "settings": { ... },
      "model_animation": { ... },
      "layers": [
        {
          "kind": "folder" | "sprite",
          "name": "Body",
          "file_path": ".../01_body.png",
          "sprite_type": "Sprite2D" | "WiggleApp",
          "parent": "",
          "position": [0, 0],
          "offset": [0, 0],
          "scale": [1, 1],
          "z_index": 0,
          "visible": true,
          "properties": { ... }
        }
      ],
      "states": [
        {
          "name": "Normal",
          "hotkey": "1",
          "model_animation": { ... },
          "overrides": { "Blush": { "visible": false } }
        }
      ],
      "save_path": ".../output.pngRemix"
    }
    """
    log: list[dict[str, Any]] = []
    if spec.get("reset", True):
        res = await new_project()
        log.append({"step": "new_project", "res": res})
        if res.get("result") != "success":
            return {"result": "failed", "error": "new_project failed", "log": log}

    if spec.get("settings") or spec.get("model_animation"):
        res = await set_model_settings(
            settings=spec.get("settings"),
            model_animation=spec.get("model_animation"),
        )
        log.append({"step": "set_model_settings", "res": res})

    for layer in spec.get("layers", []):
        kind = layer.get("kind", "sprite")
        name = layer["name"]
        if kind == "folder":
            res = await create_folder(
                sprite_name=name,
                parent=layer.get("parent"),
                position=layer.get("position"),
                z_index=layer.get("z_index"),
                visible=layer.get("visible", True),
            )
        else:
            res = await import_sprite(
                file_path=layer["file_path"],
                sprite_name=name,
                sprite_type=layer.get("sprite_type", "Sprite2D"),
                trim=layer.get("trim", False),
                offset_on_trim=layer.get("offset_on_trim", True),
                parent=layer.get("parent"),
                position=layer.get("position"),
                offset=layer.get("offset"),
                scale=layer.get("scale"),
                rotation=layer.get("rotation"),
                z_index=layer.get("z_index"),
                visible=layer.get("visible", True),
            )
        log.append({"step": f"layer:{name}", "res": res})
        if res.get("result") != "success":
            return {"result": "failed", "error": f"Failed importing layer {name}", "log": log}

        props = layer.get("properties")
        if props:
            pres = await set_sprite_properties(
                properties=props,
                sprite_name=name,
                all_states=True,
            )
            log.append({"step": f"props:{name}", "res": pres})

    states = spec.get("states", [])
    for idx, st in enumerate(states):
        st_num = idx + 1
        st_name = st.get("name", f"State {st_num}")
        if idx == 0:
            await rename_state(new_name=st_name, state_id=1)
            if st.get("hotkey"):
                await set_state_hotkey(hotkey=st["hotkey"], state_id=1)
        else:
            await set_state(state_id=1)
            await add_state(
                state_name=st_name,
                hotkey=st.get("hotkey", ""),
                duplicate_current=st.get("duplicate_current", True),
                select=True,
            )

        await set_state(state_id=st_num)
        if st.get("model_animation"):
            await set_model_settings(model_animation=st["model_animation"])

        for sprite_name, ov_props in st.get("overrides", {}).items():
            ores = await set_sprite_properties(
                properties=ov_props,
                sprite_name=sprite_name,
                state_id=st_num,
                all_states=False,
            )
            log.append({"step": f"state{st_num}:{sprite_name}", "res": ores})

    if states:
        await set_state(state_id=1)

    save_path = spec.get("save_path")
    save_res = None
    if save_path:
        save_res = await save_model(save_path)
        log.append({"step": "save_model", "res": save_res})
        if save_res.get("result") != "success":
            return {"result": "failed", "error": "save_model failed", "log": log}

    return {
        "result": "success",
        "layers_count": len(spec.get("layers", [])),
        "states_count": len(states),
        "save_result": save_res,
    }


# ---------------------------------------------------------------------------
# Live Playback, Visibility & Tween Animations
# ---------------------------------------------------------------------------


@mcp.tool()
async def press_key(key: str) -> dict[str, Any]:
    """Trigger a hotkey event in PNGTuber-Remix (e.g. 'space', '1', 'f1')."""
    return await _send_command({"event": "general", "key": key})


@mcp.tool()
async def list_sprites() -> dict[str, Any]:
    """List all sprites with visibility, IDs, and parent/child group hierarchy."""
    return await _send_command({"event": "list_sprites"})


@mcp.tool()
async def list_groups() -> dict[str, Any]:
    """List all sprite groups (sprites that have children)."""
    return await _send_command({"event": "list_groups"})


@mcp.tool()
async def show_sprite(sprite_name: str | None = None, sprite_id: str | None = None) -> dict[str, Any]:
    """Show a sprite (and its children if it is a group) by name or ID."""
    fields = _target_fields(sprite_name, sprite_id)
    if not fields:
        return {"result": "failed", "error": "Provide either sprite_name or sprite_id."}
    return await _send_command({"event": "show_sprite", **fields})


@mcp.tool()
async def hide_sprite(sprite_name: str | None = None, sprite_id: str | None = None) -> dict[str, Any]:
    """Hide a sprite (and its children if it is a group) by name or ID."""
    fields = _target_fields(sprite_name, sprite_id)
    if not fields:
        return {"result": "failed", "error": "Provide either sprite_name or sprite_id."}
    return await _send_command({"event": "hide_sprite", **fields})


@mcp.tool()
async def toggle_sprite(sprite_name: str | None = None, sprite_id: str | None = None) -> dict[str, Any]:
    """Toggle visibility of a sprite (and its children if it is a group) by name or ID."""
    fields = _target_fields(sprite_name, sprite_id)
    if not fields:
        return {"result": "failed", "error": "Provide either sprite_name or sprite_id."}
    return await _send_command({"event": "toggle_sprite", **fields})


@mcp.tool()
async def show_group(group_name: str | None = None, group_id: str | None = None) -> dict[str, Any]:
    """Show a group and all its children by name or ID."""
    fields = _target_fields(group_name, group_id, "group_name", "group_id")
    if not fields:
        return {"result": "failed", "error": "Provide either group_name or group_id."}
    return await _send_command({"event": "show_group", **fields})


@mcp.tool()
async def hide_group(group_name: str | None = None, group_id: str | None = None) -> dict[str, Any]:
    """Hide a group and all its children by name or ID."""
    fields = _target_fields(group_name, group_id, "group_name", "group_id")
    if not fields:
        return {"result": "failed", "error": "Provide either group_name or group_id."}
    return await _send_command({"event": "hide_group", **fields})


@mcp.tool()
async def toggle_group(group_name: str | None = None, group_id: str | None = None) -> dict[str, Any]:
    """Toggle visibility of a group and all its children by name or ID."""
    fields = _target_fields(group_name, group_id, "group_name", "group_id")
    if not fields:
        return {"result": "failed", "error": "Provide either group_name or group_id."}
    return await _send_command({"event": "toggle_group", **fields})


@mcp.tool()
async def move_sprite(
    x: float,
    y: float,
    sprite_name: str | None = None,
    sprite_id: str | None = None,
    duration: float = 1.0,
    reset: bool = False,
    reset_delay: float = 0.0,
) -> dict[str, Any]:
    """Smoothly move a sprite to (x, y) over duration seconds, optionally auto-resetting."""
    fields = _target_fields(sprite_name, sprite_id)
    if not fields:
        return {"result": "failed", "error": "Provide either sprite_name or sprite_id."}
    return await _send_command(
        {
            "event": "move_sprite",
            **fields,
            "x": x,
            "y": y,
            "duration": duration,
            "reset": reset,
            "reset_delay": reset_delay,
        }
    )


@mcp.tool()
async def animate_sprite(
    sprite_name: str | None = None,
    sprite_id: str | None = None,
    scale: float | None = None,
    scale_x: float | None = None,
    scale_y: float | None = None,
    rotation: float = 0.0,
    duration: float = 1.0,
    reset: bool = False,
    reset_delay: float = 0.0,
) -> dict[str, Any]:
    """Animate sprite scale and rotation in degrees, optionally auto-resetting."""
    fields = _target_fields(sprite_name, sprite_id)
    if not fields:
        return {"result": "failed", "error": "Provide either sprite_name or sprite_id."}
    payload: dict[str, Any] = {
        "event": "animate_sprite",
        **fields,
        "rotation": rotation,
        "duration": duration,
        "reset": reset,
        "reset_delay": reset_delay,
    }
    if scale is not None:
        payload["scale"] = scale
    if scale_x is not None:
        payload["scale_x"] = scale_x
    if scale_y is not None:
        payload["scale_y"] = scale_y
    return await _send_command(payload)


@mcp.tool()
async def shake_sprite(
    sprite_name: str | None = None,
    sprite_id: str | None = None,
    intensity: float = 10.0,
    duration: float = 1.0,
) -> dict[str, Any]:
    """Add a shake/vibration effect to a sprite."""
    fields = _target_fields(sprite_name, sprite_id)
    if not fields:
        return {"result": "failed", "error": "Provide either sprite_name or sprite_id."}
    return await _send_command(
        {
            "event": "shake_sprite",
            **fields,
            "intensity": intensity,
            "duration": duration,
        }
    )


@mcp.tool()
async def bounce_sprite(
    sprite_name: str | None = None,
    sprite_id: str | None = None,
    height: float = 20.0,
    duration: float = 0.5,
) -> dict[str, Any]:
    """Create a bouncing animation effect on a sprite."""
    fields = _target_fields(sprite_name, sprite_id)
    if not fields:
        return {"result": "failed", "error": "Provide either sprite_name or sprite_id."}
    return await _send_command(
        {
            "event": "bounce_sprite",
            **fields,
            "height": height,
            "duration": duration,
        }
    )


if __name__ == "__main__":
    mcp.run()
