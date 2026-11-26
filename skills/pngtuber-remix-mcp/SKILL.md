---
name: pngtuber-remix-mcp
description: >-
  Design, rig, animate, live-edit, and export client-ready .pngRemix avatars in
  PNGTubeRemix-Studio-MCP over WebSocket/MCP. Use when creating or modifying
  PNGTuber-Remix characters, layers, hierarchy, blink/talk reactions, mouse
  tracking, wiggle physics, expression states, keybinds, or exporting .pngRemix
  files for unmodified PNGTuber-Remix clients. Not for: SVG-based SVGTuber
  rigs or Live2D (.moc3) models.
---

# pngtuber-remix-mcp

Author, rig, animate, visually verify, and export complete `.pngRemix` avatars through the `pngtuber-remix` MCP server connected to **PNGTubeRemix-Studio-MCP** (`ws://localhost:9321`). Exported `.pngRemix` files use the native V1.4.7 format with embedded PNG textures and run unmodified in official **PNGTuber-Remix**.

## Desktop Visibility Rule

In sandboxed agent environments (such as Antigravity `exebox`), GUI processes launched from a terminal run inside an isolated virtual desktop and are invisible on the user's monitor.

1. Always call `ping()` first.
2. If `ping()` fails, ask the user to launch `PNGTube Remix.exe` directly on their desktop (it auto-starts the WebSocket server on `ws://localhost:9321` with zero menu clicks) so every import, rig update, and state change appears live on their screen.
3. Only call `launch_studio()` for headless/automated testing or when the user explicitly asks you to launch it.

## Artwork Authoring Rules

- Render all layers on an **identical transparent square canvas** (e.g., `600x600` or `1000x1000`, drawn at `4x` supersampling and downsampled with `Image.Resampling.LANCZOS`), and import with `trim=False` so every part aligns at `[0, 0]` automatically.
- **Clip internal details**: mask tongues, teeth, or iris highlights inside the mouth/eye cavity mask before drawing the outer border so nothing protrudes past the outline.
- **Connect stems & appendages**: anchor leaf/hair/ear Bezier paths directly onto the parent stem/joint coordinates and place behind-parent parts (stems, back hair, arms) at negative relative `z_index` (e.g., `-1`).

## 5-Step Rigging Pipeline

1. **Connect & Reset**: Call `ping()`, then `new_project()` (or build everything in one shot with `build_rig_from_spec(spec)`).
2. **Build Hierarchy**: Import root `Body` (`parent=""`), attach limbs/neck (`parent="Body"`), attach `Head` (`parent="Body"`), and attach facial features, hair/antenna, and expression overlays (`parent="Head"`).
3. **Configure Reactions & Physics**:
   - **Blink**: `Eyes_Open` (`should_blink=True, open_eyes=True`) and `Eyes_Closed` (`should_blink=True, open_eyes=False`).
   - **Lipsync**: `Mouth_Closed` (`should_talk=True, open_mouth=False`) and `Mouth_Open` (`should_talk=True, open_mouth=True`).
   - **Mouse Tracking**: Set `follow_type=0`, `mouse_delay=0.15`, and subtle bounds (e.g., eyes `pos_x_min=-8, pos_x_max=8, pos_y_min=-6, pos_y_max=6`).
   - **Wiggle & Drag**: Use shader `wiggle=True` with `wiggle_rot_offset=[0.5, 0.28]` on hair/antennas or `sprite_type="WiggleApp"` for multi-segment tails/ribbons, plus `dragSpeed`/`rdragStr` for inertia.
4. **Configure States & Hotkeys**:
   - Create expression states (`Normal`, `Blush`, `Cool`, `Angry`, etc.) with `add_state(..., duplicate_current=True)` and bind hotkeys `1`–`9` via `set_state_hotkey`.
   - Keep `is_asset=False` on state-switched layers (`sprite_data.visible` controls visibility per state). Reserve `is_asset=True` + `hotkey` for independent toggle props.
5. **Visual Verification & Client Export Gate**:
   - Switch to `set_ui_mode(1)` (Stream mode hides the Editor's 20%-alpha ghost preview of inactive blink/talk layers).
   - Test deterministically with `simulate_input(mouth_state=..., blink=...)` + `set_state(...)` + `capture_screenshot(...)`, and visually inspect every state screenshot.
   - Restore `simulate_input(mouth_state="auto", blink="auto")`, `set_state(state_id=1)`, and `set_ui_mode(0)`.
   - Save via `save_model(output_path)` and run [verify_pngremix.py](./scripts/verify_pngremix.py) before delivering `.pngRemix` to a client.

## Live Revision Loop

When the user requests visual or motion tweaks:
- **Artwork fix**: Regenerate only the changed PNG layer(s) and call `replace_sprite_image(file_path=..., sprite_name=...)` to hot-swap textures in-place while keeping hierarchy, rigging, and states intact.
- **Motion/visibility fix**: Call `set_sprite_properties(..., all_states=True)` (or target `state_id`), then re-save with `save_model(output_path)`.

## References

- All 39 MCP tools and `build_rig_from_spec` schema: [mcp-tools-reference.md](./references/mcp-tools-reference.md)
- `SpriteObject`, `WiggleApp`, `model_animation`, and `settings_dict` keys: [sprite-properties-guide.md](./references/sprite-properties-guide.md)
- Standalone `.pngRemix` client-compatibility validator: [verify_pngremix.py](./scripts/verify_pngremix.py)
