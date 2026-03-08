# Scoring System

## How Scoring Works

### Base Score: 1000 points
Awarded for any successful landing.

### Fuel Bonus: 0-500 points
- Based on remaining fuel percentage
- Formula: `(fuel_remaining / 1000) * 500`
- Full fuel (1000) = 500 bonus
- Half fuel (500) = 250 bonus
- Empty fuel (0) = 0 bonus

### Time Bonus: 0-300 points
- Faster landings earn more points
- Formula: `max(0, 300 - (time - 20) * 5)`
- 20 seconds = 300 bonus (maximum)
- 40 seconds = 200 bonus
- 60 seconds = 100 bonus
- 80+ seconds = 0 bonus

### Difficulty Multiplier
- **Easy (simple)**: 1.0x
- **Medium**: 1.5x
- **Hard**: 2.0x

### Crashed or Failed
- Score = 0 (no points awarded)

## Example Scores

### Perfect Landing (Easy)
- Base: 1000
- Fuel (900/1000): 450
- Time (25s): 275
- Multiplier: 1.0x
- **Total: 1,725 points**

### Perfect Landing (Hard)
- Base: 1000
- Fuel (900/1000): 450
- Time (25s): 275
- Multiplier: 2.0x
- **Total: 3,450 points**

### Slow Landing (Medium)
- Base: 1000
- Fuel (300/1000): 150
- Time (55s): 125
- Multiplier: 1.5x
- **Total: 1,913 points**

### Crash
- **Total: 0 points**

## Maximum Possible Scores

- **Easy**: 1,800 points (1000 + 500 + 300) × 1.0
- **Medium**: 2,700 points (1000 + 500 + 300) × 1.5
- **Hard**: 3,600 points (1000 + 500 + 300) × 2.0

## Strategy Tips

1. **Land quickly** - Every second after 20s costs 5 points
2. **Conserve fuel** - Each 1% fuel = 5 points
3. **Play on Hard** - 2x multiplier doubles your score
4. **Balance speed vs fuel** - Using thrust costs fuel but saves time

## Display

Score is shown on the game over screen:
- **Successful landing**: Score displayed prominently in green
- **Crash**: No score shown (0 points)
- Visible to both player and spectators
