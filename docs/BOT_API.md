# Bot API Guide

Build AI bots that play Lunar Lander via the WebSocket API.

## Quick Start

### 1. Register a player account

```bash
curl -X POST http://localhost:8080/api/register \
  -H "Content-Type: application/json" \
  -d '{"username": "botmaker", "password": "mypass123"}'
```

Save the `token` and `api_key` from the response.

### 2. Create a bot

```bash
curl -X POST http://localhost:8080/api/bots \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"bot_name": "LunarBot", "version": "1.0"}'
```

Save the bot's `api_key` — this is what your bot uses to authenticate.

### 3. Connect and play

```python
import asyncio, json, websockets

API_KEY = "your-bot-api-key"

async def play():
    async with websockets.connect(
        "ws://localhost:8080/ws",
        additional_headers={"X-API-Key": API_KEY}
    ) as ws:
        # Start a game
        await ws.send(json.dumps({
            "type": "start",
            "difficulty": "simple",
            "bot_name": "LunarBot",
            "bot_version": "1.0"
        }))

        # Receive init (terrain + starting position)
        init = json.loads(await ws.recv())
        print(f"Terrain points: {len(init['terrain'])}")

        # Game loop — receive telemetry, send inputs
        while True:
            msg = json.loads(await ws.recv())

            if msg["type"] == "telemetry":
                lander = msg["lander"]
                # Your AI logic here
                if lander["vy"] > 3.0:
                    await ws.send(json.dumps({"type": "input", "action": "thrust"}))
                if lander["rotation"] > 5:
                    await ws.send(json.dumps({"type": "input", "action": "rotate_left"}))
                elif lander["rotation"] < -5:
                    await ws.send(json.dumps({"type": "input", "action": "rotate_right"}))

            elif msg["type"] == "game_over":
                result = "LANDED" if msg["landed"] else "CRASHED"
                print(f"{result} — Score: {msg.get('score', 0)}")
                break

asyncio.run(play())
```

## Authentication

Bots authenticate via the `X-API-Key` header on the WebSocket connection. The server resolves the bot's identity and links game results to the bot and its owner.

## WebSocket Protocol

### Messages you send

| Type | Fields | Description |
|------|--------|-------------|
| `start` | `difficulty`, `bot_name`, `bot_version` | Start a game |
| `input` | `action` | Send a control input |
| `ping` | — | Keep-alive |

Actions: `thrust`, `rotate_left`, `rotate_right`, `thrust_off`, `rotate_left_off`, `rotate_right_off`

### Messages you receive

**`init`** — Sent once after `start`:
```json
{
  "type": "init",
  "terrain": [[0, 500], [50, 480], ...],
  "lander": {"x": 600, "y": 100, "vx": 0, "vy": 0, "rotation": 0, "fuel": 1000},
  "landing_zones": [{"x1": 400, "x2": 500, "y": 450}]
}
```

**`telemetry`** — Sent at 60Hz during gameplay:
```json
{
  "type": "telemetry",
  "lander": {"x": 601, "y": 102, "vx": 0.1, "vy": 1.2, "rotation": -2, "fuel": 998},
  "altitude": 348,
  "speed": 1.2,
  "thrusting": false,
  "nearest_landing_zone": {"x1": 400, "x2": 500, "distance": 201}
}
```

**`game_over`** — Game ended:
```json
{
  "type": "game_over",
  "landed": true,
  "crashed": false,
  "score": 1850,
  "time": 12.4,
  "fuel_remaining": 820,
  "inputs": 47,
  "replay_id": "abc123"
}
```

## Landing Criteria

- Speed < 5.0 m/s
- Angle < 17° from vertical
- On a landing zone

## Bot Management API

All endpoints require `Authorization: Bearer TOKEN` header.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/bots` | Create bot (max 10 per player) |
| `GET` | `/api/bots` | List your bots |
| `DELETE` | `/api/bots/{id}` | Delete a bot |
| `POST` | `/api/bots/{id}/regenerate-key` | Get a new API key |

## Viewing Results

- **Leaderboard**: `GET /api/leaderboard`
- **Player stats**: `GET /api/players/{id}/stats`
- **Replays**: `GET /replays` then `GET /replay/{id}`

## Tips

- Telemetry arrives at 60Hz — you don't need to respond to every frame
- `vy` is positive downward — higher values mean falling faster
- Fuel is finite — use short thrust bursts
- `rotation` is in degrees — 0 is upright
- Start with `simple` difficulty, then try `medium` and `hard`
