# Bot API Guide

Build AI bots that play Lunar Lander via the WebSocket API.

## Quick Start

### 1. Register and create a bot

Visit the game server in your browser and create an account. Once logged in, go to your profile to create a bot and get your API key.

### 2. Connect and play

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

        # Receive init (terrain, starting position, physics constants)
        init = json.loads(await ws.recv())
        terrain = init["terrain"]
        constants = init["constants"]
        print(f"Difficulty: {init['difficulty']}, Landing zones: {len(terrain['landing_zones'])}")

        # Game loop — receive telemetry, send inputs
        while True:
            msg = json.loads(await ws.recv())

            if msg["type"] == "telemetry":
                lander = msg["lander"]
                # Your AI logic here
                if lander["vy"] > 3.0:
                    await ws.send(json.dumps({"type": "input", "action": "thrust"}))
                if lander["rotation"] > 0.1:
                    await ws.send(json.dumps({"type": "input", "action": "rotate_left"}))
                elif lander["rotation"] < -0.1:
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

Actions: `thrust`, `thrust_off`, `rotate_left`, `rotate_right`, `rotate_stop`

### Messages you receive

**`init`** — Sent once after `start`:
```json
{
  "type": "init",
  "difficulty": "simple",
  "terrain": {
    "points": [[0, 700], [50, 680], ...],
    "landing_zones": [{"x1": 400, "x2": 500, "y": 700, "multiplier": 1.0}],
    "width": 1200,
    "height": 800
  },
  "lander": {"x": 600, "y": 100, "vx": 0, "vy": 0, "rotation": 0, "fuel": 1000},
  "constants": {
    "gravity": 1.62,
    "thrust_power": 8.0,
    "rotation_speed": 3.0,
    "fuel_consumption_rate": 10.0,
    "max_fuel": 1000.0,
    "max_landing_speed": 5.0,
    "max_landing_angle": 0.3,
    "terrain_width": 1200,
    "terrain_height": 800,
    "max_possible_score": 1800
  }
}
```

> **Important:** Terrain and constants are only sent in `init`. Store them — they don't change during the game.

**`telemetry`** — Sent at 30Hz during gameplay:
```json
{
  "type": "telemetry",
  "lander": {"x": 601, "y": 102, "vx": 0.1, "vy": 1.2, "rotation": -0.05, "fuel": 998},
  "altitude": 348,
  "terrain_height": 450,
  "speed": 1.2,
  "thrusting": false,
  "nearest_landing_zone": {
    "x1": 400, "x2": 500, "center_x": 450, "y": 700,
    "width": 100, "distance": 151, "direction": "left"
  },
  "spectator_count": 3
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
- Angle < 0.3 radians (~17°) from vertical
- On a landing zone

## Useful Calculations

The telemetry gives you everything you need. Here are common calculations for your bot logic:

```python
import math

# From init (store these once)
terrain = init["terrain"]
zones = terrain["landing_zones"]
constants = init["constants"]
max_fuel = constants["max_fuel"]

# From each telemetry frame
lander = msg["lander"]
zone = msg["nearest_landing_zone"]

# --- Navigation ---
# Am I over the landing zone?
over_zone = zone["x1"] <= lander["x"] <= zone["x2"]

# Landing zone center
zone_center = (zone["x1"] + zone["x2"]) / 2

# Horizontal error to target
x_error = zone_center - lander["x"]

# --- Safety checks ---
# Speed from components (also available as msg["speed"])
speed = math.sqrt(lander["vx"]**2 + lander["vy"]**2)

# Safe to land?
safe_speed = speed < 5.0                    # matches server threshold
safe_angle = abs(lander["rotation"]) < 0.3  # radians, ~17 degrees

# Angle in degrees (if you prefer)
angle_deg = abs(lander["rotation"]) * 180 / math.pi

# --- Fuel ---
fuel_pct = lander["fuel"] / max_fuel

# Seconds of thrust remaining
thrust_time_left = lander["fuel"] / constants["fuel_consumption_rate"]

# --- Physics predictions ---
# How fast will I be falling in T seconds (no thrust)?
def predict_vy(vy, t):
    return vy + constants["gravity"] * t

# How much altitude will I lose in T seconds (no thrust)?
def predict_altitude_loss(vy, t):
    return vy * t + 0.5 * constants["gravity"] * t**2

# Thrust deceleration (when pointing up, rotation ≈ 0)
# Net upward acceleration = thrust_power - gravity
net_decel = constants["thrust_power"] - constants["gravity"]  # 6.38 m/s²

# Seconds of thrust needed to stop from current vy
if lander["vy"] > 0:
    burn_time = lander["vy"] / net_decel
    fuel_to_stop = burn_time * constants["fuel_consumption_rate"]
```

## Physics Constants Reference

All constants are sent in the `init` message under `constants`:

| Constant | Value | Unit | Description |
|----------|-------|------|-------------|
| `gravity` | 1.62 | m/s² | Lunar gravity (downward) |
| `thrust_power` | 8.0 | m/s² | Thrust acceleration |
| `rotation_speed` | 3.0 | rad/s | Rotation rate |
| `fuel_consumption_rate` | 10.0 | units/s | Fuel burn while thrusting |
| `max_fuel` | varies | units | Starting fuel for this game |
| `max_landing_speed` | 5.0 | m/s | Max speed for safe landing |
| `max_landing_angle` | 0.3 | rad | Max tilt for safe landing (~17°) |
| `max_possible_score` | varies | points | Max score for this difficulty |

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

- Telemetry arrives at 30Hz — you don't need to respond to every frame
- `vy` is positive downward — higher values mean falling faster
- `rotation` is in radians — 0 is upright, positive is clockwise
- Fuel is finite — use short thrust bursts
- Start with `simple` difficulty, then try `medium` and `hard`
- Store terrain from `init` — it's not resent in telemetry
- The key insight: `thrust_power` (8.0) is ~5x `gravity` (1.62), so you have plenty of stopping power if you have fuel
