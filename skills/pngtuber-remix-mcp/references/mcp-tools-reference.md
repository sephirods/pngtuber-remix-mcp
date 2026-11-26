# PNGTuber-Remix MCP Tools Reference

## Table of Contents
- [1. Lifecycle & Connection](#1-lifecycle--connection)
- [2. Project Save / Load / Reset](#2-project-save--load--reset)
- [3. Layer & Hierarchy Authoring](#3-layer--hierarchy-authoring)
- [4. States & Hotkeys](#4-states--hotkeys)
- [5. Model Settings, Simulation & Screenshots](#5-model-settings-simulation--screenshots)
- [6. Live Stream Control & Tween Animations](#6-live-stream-control--tween-animations)
- [7. Complete `build_rig_from_spec` Example](#7-complete-build_rig_from_spec-example)

---

## 1. Lifecycle & Connection

| Tool | Arguments | Description |
|---|---|---|
| `ping` | *(none)* | Tests WebSocket connection (`ws://localhost:9321`); returns `{"event": "pong"}`. |
| `launch_studio` | `exe_path?`, `ws_port=9321`, `wait_seconds=20.0` | Launches `PNGTube Remix.exe` detached and waits until `ping` succeeds. |
| `stop_studio` | *(none)* | Terminates a Studio instance started by `launch_studio`. |

## 2. Project Save / Load / Reset

| Tool | Arguments | Description |
|---|---|---|
| `new_project` | *(none)* | Clears all sprites/images and resets to 1 clean state. |
| `load_model` | `file_path` | Loads an existing `.pngRemix` or `.save` file. |
| `save_model` | `file_path` | Saves a self-contained V1.4.7 `.pngRemix` file with embedded textures. |

## 3. Layer & Hierarchy Authoring

| Tool | Arguments | Description |
|---|---|---|
| `import_sprite` | `file_path`, `sprite_name?`, `sprite_type="Sprite2D"`, `trim=False`, `offset_on_trim=True`, `parent?`, `position?`, `offset?`, `scale?`, `rotation?`, `z_index?`, `visible=True` | Imports a PNG/APNG/GIF/SVG as `Sprite2D` or `WiggleApp` with embedded image bytes. |
| `create_folder` | `sprite_name="Folder"`, `parent?`, `position?`, `z_index?`, `visible=True` | Creates a Folder `SpriteObject` for grouping layers. |
| `replace_sprite_image` | `file_path`, `sprite_name?`, `sprite_id?`, `trim=False`, `offset_on_trim=True` | Hot-swaps a sprite's texture while preserving parenting, properties, and states. |
| `reparent_sprite` | `parent=""`, `sprite_name?`, `sprite_id?`, `keep_global_position=False` | Moves a sprite under `parent` (or `""` / `"0"` for root). |
| `rename_sprite` | `new_name`, `sprite_name?`, `sprite_id?` | Renames a sprite or folder. |
| `delete_sprite` | `sprite_name?`, `sprite_id?`, `delete_children=True` | Removes a sprite (and optionally its children). |
| `get_sprite_info` | `sprite_name?`, `sprite_id?` | Returns full JSON metadata, children, `state_count`, and `sprite_data`. |
| `set_sprite_properties` | `properties`, `sprite_name?`, `sprite_id?`, `state_id?`, `all_states=False` | Updates reactions, transforms, mouse tracking, wiggle, physics, or asset hotkeys. |
| `build_rig_from_spec` | `spec` | Declaratively resets, builds layers, applies properties, configures states, and saves `.pngRemix`. |

## 4. States & Hotkeys

| Tool | Arguments | Description |
|---|---|---|
| `list_states` | *(none)* | Lists all states (`id` 1-based, `name`, `is_current`). |
| `set_state` | `state_name?`, `state_id?` | Switches active state and syncs UI button + sprite state. |
| `add_state` | `state_name=""`, `hotkey=""`, `duplicate_current=True`, `select=True` | Adds a new state, optionally duplicating the active state, and binds a hotkey. |
| `rename_state` | `new_name`, `state_name?`, `state_id?` | Renames an existing state. |
| `delete_state` | `state_name?`, `state_id?` | Deletes a state (cannot delete the last remaining state). |
| `set_state_hotkey` | `hotkey`, `state_name?`, `state_id?` | Binds a keyboard key (e.g. `"1"`, `"2"`, `"F1"`) to switch to a state. |

## 5. Model Settings, Simulation & Screenshots

| Tool | Arguments | Description |
|---|---|---|
| `get_model_settings` | *(none)* | Reads `Global.settings_dict` and current `model_animation` bounce/idle settings. |
| `set_model_settings` | `settings?`, `model_animation?` | Updates global blink/mic/bg/camera settings and/or container bounce animations. |
| `set_ui_mode` | `mode=0` | `0` = Editor, `1` = Stream clean preview, `2` = Mesh editor. |
| `simulate_input` | `mouth_state?`, `blink?` | Overrides mic (`"auto"`, `"closed"`, `"open"`, `"screaming"`) and blink (`"auto"`, `"open"`, `"closed"`, or bool). |
| `capture_screenshot` | `file_path`, `source="subviewport"` | Captures `"subviewport"` (avatar canvas) or `"window"` (full UI) as PNG. |

## 6. Live Stream Control & Tween Animations

| Tool | Arguments | Description |
|---|---|---|
| `press_key` | `key` | Triggers asset toggle/hide hotkeys bound to `saved_event` / `hide_keys`. |
| `list_sprites` | *(none)* | Lists all sprites with `id`, `name`, `visible`, `is_group`, `children`, `parent_id`. |
| `list_groups` | *(none)* | Lists only sprites that have children. |
| `show_sprite` / `hide_sprite` / `toggle_sprite` | `sprite_name?`, `sprite_id?` | Changes visibility for a sprite (and children if group) in the active state. |
| `show_group` / `hide_group` / `toggle_group` | `group_name?`, `group_id?` | Explicit group visibility toggles. |
| `move_sprite` | `x`, `y`, `sprite_name?`, `sprite_id?`, `duration=1.0`, `reset=False`, `reset_delay=0.0` | Smooth position tween. |
| `animate_sprite` | `sprite_name?`, `sprite_id?`, `scale?`, `scale_x?`, `scale_y?`, `rotation=0.0`, `duration=1.0`, `reset=False`, `reset_delay=0.0` | Smooth scale + degree rotation tween. |
| `shake_sprite` | `sprite_name?`, `sprite_id?`, `intensity=10.0`, `duration=1.0` | Random shake impulse. |
| `bounce_sprite` | `sprite_name?`, `sprite_id?`, `height=20.0`, `duration=0.5` | Vertical bounce tween. |

## 7. Complete `build_rig_from_spec` Example

```json
{
  "reset": true,
  "settings": {
    "blink_speed": 1.0,
    "blink_chance": 8,
    "bg_color": "#4b596b",
    "is_transparent": false
  },
  "model_animation": {
    "mouth_closed": 0,
    "mouth_open": 3,
    "current_mc_anim": "Idle",
    "current_mo_anim": "One Bounce",
    "should_squish": true,
    "squish_amount": 1.06,
    "bounce_state": true
  },
  "layers": [
    {
      "kind": "sprite",
      "name": "Body",
      "file_path": "C:/path/01_body.png",
      "z_index": 0,
      "properties": { "yAmp": 4.0, "yFrq": 2.0, "dragSpeed": 2.0 }
    },
    {
      "kind": "sprite",
      "name": "Head",
      "file_path": "C:/path/04_head.png",
      "parent": "Body",
      "z_index": 2,
      "properties": { "dragSpeed": 4.5, "rdragStr": 3.5, "stretchAmount": 0.04 }
    },
    {
      "kind": "sprite",
      "name": "Antenna",
      "file_path": "C:/path/05_antenna.png",
      "parent": "Head",
      "z_index": -1,
      "properties": {
        "wiggle": true,
        "wiggle_amp": 0.14,
        "wiggle_freq": 3.5,
        "wiggle_physics": true,
        "wiggle_rot_offset": [0.5, 0.28]
      }
    },
    {
      "kind": "sprite",
      "name": "Eyes_Open",
      "file_path": "C:/path/06_eyes_open.png",
      "parent": "Head",
      "z_index": 3,
      "properties": {
        "should_blink": true,
        "open_eyes": true,
        "follow_type": 0,
        "pos_x_min": -8.0,
        "pos_x_max": 8.0,
        "pos_y_min": -6.0,
        "pos_y_max": 6.0,
        "mouse_delay": 0.15
      }
    },
    {
      "kind": "sprite",
      "name": "Eyes_Closed",
      "file_path": "C:/path/07_eyes_closed.png",
      "parent": "Head",
      "z_index": 3,
      "properties": {
        "should_blink": true,
        "open_eyes": false,
        "follow_type": 0,
        "pos_x_min": -8.0,
        "pos_x_max": 8.0,
        "pos_y_min": -6.0,
        "pos_y_max": 6.0,
        "mouse_delay": 0.15
      }
    },
    {
      "kind": "sprite",
      "name": "Mouth_Closed",
      "file_path": "C:/path/08_mouth_closed.png",
      "parent": "Head",
      "z_index": 3,
      "properties": { "should_talk": true, "open_mouth": false }
    },
    {
      "kind": "sprite",
      "name": "Mouth_Open",
      "file_path": "C:/path/09_mouth_open.png",
      "parent": "Head",
      "z_index": 3,
      "properties": { "should_talk": true, "open_mouth": true }
    },
    {
      "kind": "sprite",
      "name": "Blush",
      "file_path": "C:/path/10_blush.png",
      "parent": "Head",
      "z_index": 4,
      "visible": false
    }
  ],
  "states": [
    { "name": "Normal", "hotkey": "1", "overrides": { "Blush": { "visible": false } } },
    { "name": "Blush", "hotkey": "2", "overrides": { "Blush": { "visible": true } } }
  ],
  "save_path": "C:/path/Avatar_ClientReady.pngRemix"
}
```
