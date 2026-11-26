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
4. **Live-session screenshots**: when editing a model live on the user's open desktop window, capture verification screenshots with `capture_screenshot(..., source="subviewport")` while keeping `ui_mode = 0` (avoid calling `set_ui_mode(1)` on older builds where unfocusing hides `%TopBar`).

## Artwork Authoring Rules

- Render all layers on an **identical transparent square canvas** (e.g., `600x600`, `1000x1000`, or `2048x2048`, drawn at `4x` supersampling and downsampled with `Image.Resampling.LANCZOS`), and import with `trim=False` so every part aligns at `[0, 0]` automatically.
- **Keep `scale` uniform (`[s, s]`)**: never squash animated overlays (orbiting hearts, sparkles) with mismatched X/Y scales.
- **Lock anchor edges across animated frames**: when building multi-frame spritesheets (`hframes > 1`, e.g., open-mouth talking frames or blink cycles), keep the upper lip / anchor pixels at the exact same `y` coordinate across every frame and inspect a side-by-side frame strip before uploading.
- **Set anatomical pivots (`position` + `offset = -position`)**: never rotate `HEAD`, `EAR_*`, `TAIL`, `ARM_*`, or hanging accessories around `[0, 0]` canvas center. Measure the joint/root coordinate `[px, py]`, set `position = [px, py]` and `offset = [-px, -py]`, synchronize `HEAD` and `BODY` vertical breathing, and disable full-model `model_animation` bounce unless requested.
- **Clip internal details**: mask tongues, teeth, or iris highlights inside the mouth/eye cavity mask before drawing the outer border so nothing protrudes past the outline.
- **Connect stems & appendages**: anchor leaf/hair/ear Bezier paths directly onto the parent stem/joint coordinates and place behind-parent parts (stems, back hair, arms) at negative relative `z_index` (e.g., `-1`).
- **Decompose composite raster layers before animating sub-parts**: whenever a sub-element (pupils/irises, tongues, gauges, accessories) must move independently inside a flat PNG, split it into (1) a stationary base (`clip: 2` / `AndDraw` if the moving child must stay bounded, with residual pixels cleanly inpainted out of the base), (2) the moving child layer with a complete silhouette cutout, and (3) any front occluders (eyelids, bangs, lapels, fingers) as higher-`z_index` layers.
- **Audit full cumulative `z_index` chains before any `reparent_sprite` or `z_index` edit**: in Godot 4 (`z_as_relative = true`), `effective_z = sum(ancestors.z_index) + node.z_index`, and when two nodes share the same `effective_z`, **children draw ON TOP of their parent**. Reparenting shifts the entire subtree's `effective_z` by the new parent's `effective_z`. Before reparenting or changing `z_index`, compute `effective_z` for every node in the moved subtree (including `+1` sub-layers like bones/highlights) and all overlapping branches (e.g. arms, wings, tails, hair, jacket flaps vs belts), ensuring `max(descendants.effective_z) < parent.effective_z` for behind-parent layers and `min(front_branch.effective_z) > max(back_branch.effective_z)` across overlapping branches. Also match sibling `z_index` across alternate expression groups (e.g., `MOUTH_SAD`/`MOUTH_MAD` must match `MOUTH_IDDLE`'s `z_index` so muzzle/cheek fluff doesn't cover them).
- **Clip alternate eye scleras & keep clipped children at `z_index: 0`**: in Godot 4, `clip: 2` (`CLIP_CHILDREN_AND_DRAW`) only clips descendants that keep `z_index: 0` — any non-zero `z_index` on a clipped pupil/highlight breaks out of the mask! Also trim sclera pixels that extend past squinted lower eyelashes (`EYES_MAD_WHITE`), tighten `pos_y_min`/`pos_y_max`, and place halo/orbiting overlays (`LOVE_HEARTS_ORBIT`) above the head bounding box rather than at eye/nose height.
- **Respect `int` vs `float` coercion on motion keys**: in `SpriteObject`, `xAmp`, `xFrq`, `yAmp`, `yFrq`, `rot_degree`, `dragSpeed`, `wiggle_amp`, and `wiggle_freq` default to `int` (`0`), so fractional values (e.g., `0.05` or `0.3`) truncate to `0` over WebSocket. Use `float` keys (`rot_frq`, `mo_rot_frq`, `should_rotate` + `should_rot_speed`) for slow continuous loops (e.g., galaxy wing layers).

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
   - Test deterministically with `simulate_input(mouth_state=..., blink=...)` + `set_state(...)` + `capture_screenshot(...)`, and visually inspect **every state (`1..N`)** — never only the single state you just edited — to catch `z_index` or visibility regressions across expressions.
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
