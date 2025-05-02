# CSE423-project-Tank-Wars
Ongoing project using the OpenGL library of python

## Current features:


### Core Gameplay
- Two tanks: Player (blue) and AI Enemy (red)
- Health-based damage system with visible floating health bars
- Projectiles and explosions with realistic collision handling
- Smart enemy AI: chases and avoids based on obstacles

### Controls

#### Keyboard
| Key | Action |
|-----|--------|
| W   | Move forward |
| S   | Move backward |
| A   | Rotate left |
| D   | Rotate right |
| R   | Reset game |
| C   | Increment player score (debug) |
| V   | Increment enemy score (debug) |

#### Special Keys
| Key | Action |
|-----|--------|
| F1  | Toggle camera (third-person ↔ top-down) |
| ↑ / ↓ | Zoom in/out in third-person view |

#### Mouse
| Action | Description |
|--------|-------------|
| Left Click | Fire a projectile |

---

## 📷 Camera Modes
- **Third-Person View**: Camera follows behind and above the player tank
- **Top-Down View**: Static orthographic overview of the full arena

---

## 💣 Combat and Collisions
- Bullets are fired by both tanks and cause 20 damage on hit
- Collisions detected with tanks, obstacles, and arena boundaries
- Explosions appear at impact points with fading effect

---

## 🧠 Enemy AI
- Rotates to face and pursue the player
- Avoids obstacles dynamically
- Fires projectiles when aligned and within range
- Alternates between `chasing` and `avoiding` modes

---

## 🧱 Arena Design
- Large grid-based battlefield
- 4 boundary walls prevent escaping
- Randomly placed cube obstacles
- Scaled to prevent clipping or overlap with tanks

---

## 🎁 Power-Ups
- Randomly spawn every 15–20 seconds
- Disappear if uncollected in 15 seconds
- Effects:
  - Full health restore
  - Speed boost for 10 seconds
- Floating, rotating yellow cube visual

---

## 🧾 HUD and UI
- Score display for both tanks
- Health values
- Speed boost countdown
- AI mode display
- Endgame message when a tank reaches 5 points

---

## 🛠️ Technologies Used
- Python 3
- PyOpenGL
- GLUT

---

## 🚀 How to Run

1. Install dependencies:
   ```bash
   pip install PyOpenGL PyOpenGL_accelerate
