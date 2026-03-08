#!/usr/bin/env python3
"""
Simple AI client for Lunar Lander
Demonstrates how to connect and play via WebSocket API
"""

import asyncio
import websockets
import json
import math

class SimpleLanderAI:
    def __init__(self, uri="ws://localhost:8000/ws"):
        self.uri = uri
        self.running = False
        self.last_thrust = False
        self.last_rotate = None
        
    async def play(self):
        async with websockets.connect(self.uri) as websocket:
            print("✓ Connected to server")
            
            # Start game
            await websocket.send(json.dumps({
                "type": "start",
                "difficulty": "simple"
            }))
            
            # Receive initial state
            init_msg = await websocket.recv()
            init_data = json.loads(init_msg)
            print(f"✓ Game started - {len(init_data['terrain']['landing_zones'])} landing zones")
            
            self.running = True
            
            # Game loop
            while self.running:
                msg = await websocket.recv()
                data = json.loads(msg)
                
                if data['type'] == 'telemetry':
                    await self.process_telemetry(data, websocket)
                elif data['type'] == 'game_over':
                    self.running = False
                    if data['landed']:
                        print(f"✓ LANDED! Time: {data['time']:.1f}s, Fuel: {data['fuel_remaining']:.0f}")
                    else:
                        print(f"✗ CRASHED after {data['time']:.1f}s")
                        
    async def process_telemetry(self, data, websocket):
        lander = data['lander']
        zone = data.get('nearest_landing_zone')
        
        if not zone:
            return
        
        # Use server-calculated values
        altitude = data['altitude']  # Actual altitude above terrain
        speed = data['speed']  # Total speed
        x_error = zone['center_x'] - lander['x']  # Horizontal distance to target
        
        # Rotation control - manage horizontal velocity and navigation
        target_angle = 0
        
        # Priority 1: If not over landing zone and low altitude, navigate there!
        if abs(x_error) > 20 and altitude < 100:
            # Emergency navigation - tilt toward landing zone
            target_angle = max(-0.4, min(0.4, x_error * 0.005))
        # Priority 2: If moving too fast horizontally, brake
        elif abs(lander['vx']) > 2.0 and altitude < 200:
            # Tilt opposite to horizontal velocity to brake
            target_angle = -lander['vx'] * 0.15
            target_angle = max(-0.5, min(0.5, target_angle))
        # Priority 3: Navigate toward landing zone when high up
        elif abs(x_error) > 50 and altitude > 200:
            target_angle = max(-0.3, min(0.3, x_error * 0.001))
        
        angle_error = target_angle - lander['rotation']
        
        desired_rotate = None
        if angle_error > 0.1:
            desired_rotate = "right"
        elif angle_error < -0.1:
            desired_rotate = "left"
        
        if desired_rotate != self.last_rotate:
            if desired_rotate:
                await websocket.send(json.dumps({"type": "input", "action": f"rotate_{desired_rotate}"}))
            else:
                await websocket.send(json.dumps({"type": "input", "action": "rotate_stop"}))
            self.last_rotate = desired_rotate
        
        # Thrust control - altitude-based strategy
        desired_thrust = False
        
        # Priority 1: Emergency hover if low and off-target (but don't build escape velocity!)
        if abs(x_error) > 20 and altitude < 50:
            # Hover to stay up while navigating - but stop if going up too fast
            if lander['vy'] < -2.0:  # Already going up fast enough
                desired_thrust = False
            else:
                desired_thrust = lander['vy'] > 0.5  # Only thrust if descending
        # Priority 2: Always thrust if moving too fast horizontally at low altitude
        elif altitude < 200 and abs(lander['vx']) > 3.0:
            desired_thrust = True
        elif altitude < 150:
            # Close to ground - very aggressive
            if self.last_thrust:
                desired_thrust = speed > 3.5 or lander['vy'] > 2.0
            else:
                desired_thrust = speed > 4.5 or lander['vy'] > 3.0
        elif altitude < 300:
            # Medium altitude
            if self.last_thrust:
                desired_thrust = lander['vy'] > 4.0
            else:
                desired_thrust = lander['vy'] > 5.0
        else:
            # High altitude
            if self.last_thrust:
                desired_thrust = lander['vy'] > 6.0
            else:
                desired_thrust = lander['vy'] > 8.0
        
        if desired_thrust != self.last_thrust:
            action = "thrust" if desired_thrust else "thrust_off"
            await websocket.send(json.dumps({"type": "input", "action": action}))
            self.last_thrust = desired_thrust
        
        # Debug output
        if int(data['timestamp'] * 2) % 2 == 0:
            print(f"Alt: {altitude:.0f}, Speed: {speed:.1f}, Vx: {lander['vx']:.1f}, Vy: {lander['vy']:.1f}, "
                  f"X-err: {x_error:.0f}, Angle: {lander['rotation']*57.3:.1f}°, "
                  f"Fuel: {lander['fuel']:.0f}, Thrust: {'ON' if desired_thrust else 'OFF'}")

async def main():
    ai = SimpleLanderAI()
    try:
        await ai.play()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Simple Lunar Lander AI")
    print("=" * 40)
    asyncio.run(main())
