# Examples

## minimal_bot.py
The absolute simplest bot — just thrusts when falling too fast. A good starting point to verify your connection works.

## simple_ai.py
A more complete bot with:
- Horizontal navigation toward landing zones
- Altitude-based thrust strategy
- Rotation control
- Hysteresis to avoid thruster chatter

Both require the `websockets` library:
```bash
pip install websockets
```
