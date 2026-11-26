# PNGTuber-Remix Sprite & Model Properties Guide

## Table of Contents
- [1. Transform, Visibility & Layer Properties](#1-transform-visibility--layer-properties)
- [2. Blink & Lipsync Reactions](#2-blink--lipsync-reactions)
- [3. Idle Oscillation, Physics & Drag](#3-idle-oscillation-physics--drag)
- [4. Mouse & Input Tracking (`follow_type`)](#4-mouse--input-tracking-follow_type)
- [5. Wiggle Shader (`Sprite2D`) & Appendage (`WiggleApp`)](#5-wiggle-shader-sprite2d--appendage-wiggleapp)
- [6. Global Model Animation & Settings](#6-global-model-animation--settings)
- [7. Client Compatibility Rules](#7-client-compatibility-rules)

---

## 1. Transform, Visibility & Layer Properties

| Key | Type | Default / Example | Notes |
|---|---|---|---|
| `position` | `[x, y]` | `[0, 0]` | Position relative to parent (or canvas root). |
| `offset` | `[x, y]` | `[0, 0]` | Sprite pivot offset (`%Sprite2D.position`). |
| `scale` | `[sx, sy]` | `[1, 1]` | Uniform or non-uniform scale. |
| `rotation` | `float` | `0.0` | Rotation in radians. |
| `z_index` | `int` | `0` | Render order relative to parent (`-1` renders behind parent). |
| `visible` | `bool` | `true` | Per-state layer visibility. |
| `colored` | `#rrggbbaa` | `"#ffffffff"` | Node modulate color & alpha. |
| `tint` | `#rrggbbaa` | `"#ffffffff"` | Sprite self-modulate tint. |
| `blend_mode` | `string` | `"Normal"` | `"Normal"`, `"Add"`, `"Subtract"`, `"Multiply"`, `"Burn"`, `"HardMix"`, `"Cursed"`. |
| `clip` | `int` | `0` | Godot `CanvasItem.ClipChildrenMode` (`0`=Disabled, `1`=Only, `2`=AndDraw). |
| `flip_sprite_h` / `flip_sprite_v` | `bool` | `false` | Horizontal / vertical sprite flip (`Sprite2D`). |
| `fade` / `fade_speed` | `bool` / `float` | `false` / `1.0` | Smooth fade when state visibility toggles. |

## 2. Blink & Lipsync Reactions

| Key | Type | Use |
|---|---|---|
| `should_blink` | `bool` | Enable automatic blinking on this layer. |
| `open_eyes` | `bool` | `true` = shown when eyes are open; `false` = shown during blink. |
| `should_talk` | `bool` | Enable microphone-reactive visibility on this layer. |
| `open_mouth` | `bool` | `true` = shown while speaking; `false` = shown while silent. |
| `hframes` / `vframes` | `int` | Spritesheet grid dimensions (`1` for static single sprite). |
| `animation_speed` | `float` | Frames per second for multi-frame spritesheets. |

## 3. Idle Oscillation, Physics & Drag

When `shared_movement` is `true` (default), base keys apply to all mouth states. Set `shared_movement: false` to override separately with `mo_*` (mouth open) and `scream_*` prefixes.

| Key | Typical Range | Effect |
|---|---|---|
| `xAmp` / `xFrq` | `0..15` / `0..5` | Horizontal sine sway amplitude (px) and frequency. |
| `yAmp` / `yFrq` | `2..8` / `1.5..3.0` | Vertical sine breathing/bobbing amplitude and frequency. |
| `dragSpeed` | `1.5..6.0` | Follow-through position lag/spring when parent bounces or moves. |
| `rdragStr` | `-8..8` | Rotational follow-through tilt during movement. |
| `stretchAmount` | `0..0.08` | Subtle squash-and-stretch on movement. |
| `rot_degree` / `rot_frq` | `-15..15` / `0..4` | Idle rotational oscillation amplitude and speed. |
| `rLimitMin` / `rLimitMax` | `-180` / `180` | Rotation clamp in degrees. |
| `ignore_bounce` | `bool` | `true` prevents this layer from reacting to global talk bounce. |
| `physics` | `bool` | Enables physics on this layer (`true` by default). |

## 4. Mouse & Input Tracking (`follow_type`)

| Key | Recommended Value | Effect |
|---|---|---|
| `follow_type` | `0` (mouse), `15` (disabled) | `0` = follow mouse cursor; `15` = off; `1`/`2` = controller sticks; `17` = UDP tracker. |
| `pos_x_min` / `pos_x_max` | `-8.0` / `8.0` (eyes) | Horizontal displacement range in pixels (`-25..25` for subtle head parallax). |
| `pos_y_min` / `pos_y_max` | `-6.0` / `6.0` (eyes) | Vertical displacement range in pixels. |
| `mouse_delay` | `0.12..0.25` | Lerp smoothing factor per physics frame (lower = smoother/slower). |
| `mouse_rotation` / `mouse_rotation_max` | `0.0` | Optional rotation toward mouse. |
| `pos_invert_x` / `pos_invert_y` | `false` | Invert X or Y tracking direction. |

## 5. Wiggle Shader (`Sprite2D`) & Appendage (`WiggleApp`)

### `Sprite2D` Shader Wiggle
- `wiggle`: `true` / `false`
- `wiggle_amp`: `0.08..0.25` (radians-like bend amplitude)
- `wiggle_freq`: `2.0..5.0`
- `wiggle_physics`: `true` (adds parent drag inertia to sway)
- `wiggle_rot_offset`: `[0.5, 0.28]` (normalized `[0..1, 0..1]` pivot on texture; adjust Y toward the stem/root attachment point)

### `WiggleApp` Multi-Segment Appendage
- `wiggle_segm` (`5`), `wiggle_stiff` (`20`), `wiggle_max_angle` (`0.5`), `wiggle_gravity` (`[0, 0]`), `auto_wag` (`true`/`false`), `wag_speed` (`0.5`), `wag_freq` (`0.02`), `width` (`80`), `segm_length` (`30`).

## 6. Global Model Animation & Settings

Passed via `set_model_settings(settings=..., model_animation=...)`:
- **`settings`**: `blink_speed` (`1.0`), `blink_chance` (`8`), `volume_limit` (`0.1`), `volume_delay` (`0.5`), `sensitivity_limit` (`1.0`), `bg_color` (`"#4b596b"`), `is_transparent` (`false`), `darken` (`false`), `dim_color`, `zoom` (`[1, 1]`), `pan` (`[0, 0]`), `max_fps` (`60`).
- **`model_animation`**: `mouth_closed` (`0`=Idle, `1`=Bouncy, `3`=One Bounce, `4`=Wobble, `5`=Squish), `mouth_open` (`3`), `current_mc_anim` (`"Idle"`), `current_mo_anim` (`"One Bounce"`), `should_squish` (`true`), `squish_amount` (`1.06`), `bounce_state` (`true`).

## 7. Client Compatibility Rules

1. Keep `is_asset: false` on layers switched by States (`Blush`, `Glasses`, `Angry_Brows`, etc.). Set `is_asset: true` + `hotkey: "F1"` only when a client wants an independent toggleable prop across states.
2. Always save via `save_model(path)` — it embeds all `ImageData.runtime_texture` PNG buffers inside the `.pngRemix` archive so the client never needs external PNG folders.
3. Validate every client export with `scripts/verify_pngremix.py` before delivery.
