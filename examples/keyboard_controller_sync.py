"""Sync live Windows keyboard typing to controller & hand animations in PNGTubeRemix-Studio-MCP."""

from __future__ import annotations

import asyncio
import ctypes
import json
import random
import time
import websockets

WS_URL = "ws://localhost:9321"
USER32 = ctypes.windll.user32

# Sprite IDs (or names) for controller & hands
JOYSTICK_1_ID = "3034511850350"
JOYSTICK_2_ID = "3035216493447"
HAND_LEFT_ID = "3041558281320"
HAND_RIGHT_ID = "3042262924417"
CONTROLLER_ID = "6054914047591"

# Virtual-Key codes to watch (A-Z, 0-9, Space, Enter, Backspace, punctuation)
WATCH_VKS = (
    list(range(0x30, 0x3A))  # 0-9
    + list(range(0x41, 0x5B))  # A-Z
    + [0x08, 0x09, 0x0D, 0x20, 0xBA, 0xBB, 0xBC, 0xBD, 0xBE, 0xBF]
)


def any_key_newly_pressed(prev_state: dict[int, bool]) -> bool:
    pressed = False
    for vk in WATCH_VKS:
        down = bool(USER32.GetAsyncKeyState(vk) & 0x8000)
        if down and not prev_state.get(vk, False):
            pressed = True
        prev_state[vk] = down
    return pressed


async def main() -> None:
    print(f"Connecting to {WS_URL}... Start typing anywhere to animate the controller!")
    prev_state: dict[int, bool] = {}
    last_trigger = 0.0

    async with websockets.connect(WS_URL, open_timeout=5) as ws:
        while True:
            if any_key_newly_pressed(prev_state):
                now = time.monotonic()
                if now - last_trigger >= 0.07:  # throttle to ~14 updates/sec max
                    last_trigger = now
                    side = random.choice((-1, 1))
                    jx = random.uniform(-6.0, 6.0)
                    jy = random.uniform(-5.0, 5.0)
                    cmds = [
                        {
                            "event": "animate_sprite",
                            "sprite_id": CONTROLLER_ID,
                            "scale_x": 1.02,
                            "scale_y": 0.98,
                            "rotation": side * 2.2,
                            "duration": 0.08,
                            "reset": True,
                            "reset_delay": 0.05,
                        },
                        {
                            "event": "move_sprite",
                            "sprite_id": JOYSTICK_1_ID,
                            "x": 160.0 + jx,
                            "y": 381.9 + jy,
                            "duration": 0.06,
                            "reset": True,
                            "reset_delay": 0.06,
                        },
                        {
                            "event": "move_sprite",
                            "sprite_id": JOYSTICK_2_ID,
                            "x": 163.3 - jx,
                            "y": 399.8 - jy,
                            "duration": 0.06,
                            "reset": True,
                            "reset_delay": 0.06,
                        },
                        {
                            "event": "bounce_sprite",
                            "sprite_id": HAND_LEFT_ID if side < 0 else HAND_RIGHT_ID,
                            "height": 6.0,
                            "duration": 0.09,
                        },
                    ]
                    for cmd in cmds:
                        await ws.send(json.dumps(cmd))
                        await asyncio.wait_for(ws.recv(), timeout=2.0)
            await asyncio.sleep(0.02)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Stopped.")
