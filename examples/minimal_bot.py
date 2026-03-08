#!/usr/bin/env python3
"""Minimal Lunar Lander bot — just enough to land."""
import asyncio, json, websockets

SERVER = "ws://localhost:8080/ws"
API_KEY = "YOUR_BOT_API_KEY"

async def play():
    async with websockets.connect(SERVER, additional_headers={"X-API-Key": API_KEY}) as ws:
        await ws.send(json.dumps({"type": "start", "difficulty": "simple"}))
        await ws.recv()  # init

        while True:
            msg = json.loads(await ws.recv())
            if msg["type"] == "telemetry":
                vy = msg["lander"]["vy"]
                # Thrust when falling too fast — that's it
                if vy > 3.0:
                    await ws.send(json.dumps({"type": "input", "action": "thrust"}))
                else:
                    await ws.send(json.dumps({"type": "input", "action": "thrust_off"}))
            elif msg["type"] == "game_over":
                r = "LANDED" if msg["landed"] else "CRASHED"
                print(f"{r} — Score: {msg.get('score', 0)}")
                break

asyncio.run(play())
