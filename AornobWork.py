from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *  # Import all GLUT functions
from OpenGL.GLUT.fonts import GLUT_BITMAP_HELVETICA_18  # Explicitly import the font
import sys
import math
import random
import time

# Game state
tank_pos = [0.0, 0.0, 0.0]
tank_angle = 0.0
player_health = 200

player_projectiles = []
explosions = []

game_over = False
victory = False
paused = False
menu_state = "main"  # main, difficulty, mode
difficulty = "medium"  # easy, medium, hard
game_mode = "normal"  # normal, capture_flag

arena_size = 50.0  # Increased arena size
camera_mode = "third_person"  # Added camera mode variable

# Capture the flag mode variables
flag_pos = [0.0, 0.0, 0.0]
flag_captured = False
player_score = 0
enemy_score = 0

# --- Enemy and Obstacle Structures ---
class EnemyTank:
    def __init__(self, pos, angle):
        self.pos = pos[:]
        self.angle = angle
        self.health = 100
        self.projectiles = []
        self.alive = True

# List of enemy tanks
enemy_tanks = [
    EnemyTank([20.0, 0.0, 20.0], 180.0),
    EnemyTank([-20.0, 0.0, 20.0], 180.0),
    EnemyTank([20.0, 0.0, -20.0], 180.0),
]

# --- Obstacles ---
class Obstacle:
    def __init__(self, pos, kind, **kwargs):
        self.pos = pos[:]
        self.kind = kind  # 'blade', 'lava', 'cube', 'barrier'
        self.angle = kwargs.get('angle', 0)
        self.speed = kwargs.get('speed', 0.05)
        self.size = kwargs.get('size', 2.0)
        self.dir = kwargs.get('dir', 1)
        self.axis = kwargs.get('axis', 'y')
        self.t = 0

obstacles = [
    Obstacle([10, 0, 0], 'blade', speed=2, size=2),
    Obstacle([-10, 0, 10], 'lava', size=3),
    Obstacle([0, 0, -10], 'cube', speed=0.1, dir=1),
    Obstacle([0, 0, 15], 'barrier', speed=1, axis='x'),
]

class Explosion:
    def __init__(self, x, z):
        self.x = x
        self.z = z
        self.start_time = time.time()

def draw_health_bar(x, z, health, color):
    glPushMatrix()
    glTranslatef(x, 1.8, z)
    glScalef(1, 0.2, 0.2)
    glColor3f(0.3, 0.3, 0.3)
    glutSolidCube(1.0)
    glColor3f(*color)
    glScalef(health / 100.0, 1, 1)
    glutSolidCube(1.0)
    glPopMatrix()

def draw_explosions():
    global explosions
    current_time = time.time()
    for e in explosions[:]:
        elapsed = current_time - e.start_time
        if elapsed > 0.5:
            explosions.remove(e)
            continue
        glPushMatrix()
        glTranslatef(e.x, 0.3, e.z)
        glColor3f(1.0, 0.5, 0.0)
        glutSolidSphere(0.3 + elapsed * 2, 10, 10)
        glPopMatrix()

def draw_tank(pos, angle, color):
    glPushMatrix()
    glTranslatef(pos[0], pos[1], pos[2])
    glRotatef(angle, 0, 1, 0)

    # Tank body (main chassis)
    glPushMatrix()
    glColor3f(*color)
    glScalef(1.2, 0.6, 2.0)  # Make the body longer and flatter
    glutSolidCube(1.0)
    glPopMatrix()

    # Tank tracks
    glPushMatrix()
    glColor3f(0.2, 0.2, 0.2)  # Dark gray for tracks
    # Left track
    glPushMatrix()
    glTranslatef(-0.7, -0.3, 0)
    glScalef(0.2, 0.3, 2.0)
    glutSolidCube(1.0)
    glPopMatrix()
    # Right track
    glPushMatrix()
    glTranslatef(0.7, -0.3, 0)
    glScalef(0.2, 0.3, 2.0)
    glutSolidCube(1.0)
    glPopMatrix()
    glPopMatrix()

    # Turret base
    glPushMatrix()
    glTranslatef(0, 0.4, 0)
    glColor3f(0.8, 0.8, 0.8)
    glScalef(0.8, 0.4, 0.8)
    glutSolidCube(1.0)
    glPopMatrix()

    # Turret dome
    glPushMatrix()
    glTranslatef(0, 0.8, 0)
    glColor3f(0.8, 0.8, 0.8)
    glutSolidSphere(0.4, 16, 16)
    glPopMatrix()

    # Main gun barrel
    glPushMatrix()
    glTranslatef(0, 0.8, 0.5)
    glRotatef(-90, 1, 0, 0)
    glColor3f(0.3, 0.3, 0.3)
    gluCylinder(gluNewQuadric(), 0.15, 0.1, 1.2, 16, 16)
    glPopMatrix()

    # Machine gun on top
    glPushMatrix()
    glTranslatef(0.3, 1.0, 0)
    glRotatef(-90, 1, 0, 0)
    glColor3f(0.3, 0.3, 0.3)
    gluCylinder(gluNewQuadric(), 0.05, 0.05, 0.4, 8, 8)
    glPopMatrix()

    # Headlights
    glPushMatrix()
    glColor3f(1.0, 1.0, 0.8)
    # Left headlight
    glPushMatrix()
    glTranslatef(-0.4, 0.2, -1.0)
    glutSolidSphere(0.1, 8, 8)
    glPopMatrix()
    # Right headlight
    glPushMatrix()
    glTranslatef(0.4, 0.2, -1.0)
    glutSolidSphere(0.1, 8, 8)
    glPopMatrix()
    glPopMatrix()

    glPopMatrix()

def draw_arena():
    glColor3f(0.2, 0.2, 0.2)
    glBegin(GL_QUADS)
    glVertex3f(-arena_size, -0.5, -arena_size)
    glVertex3f(-arena_size, -0.5, arena_size)
    glVertex3f(arena_size, -0.5, arena_size)
    glVertex3f(arena_size, -0.5, -arena_size)
    glEnd()

def distance(a, b):
    return math.sqrt((a[0]-b[0])**2 + (a[2]-b[2])**2)

def draw_menu():
    glPushAttrib(GL_ALL_ATTRIB_BITS)
    glDisable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(-5, 5, -3, 3)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    # Draw semi-transparent background
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(0.1, 0.1, 0.1, 0.8)
    glBegin(GL_QUADS)
    glVertex2f(-5, -3)
    glVertex2f(5, -3)
    glVertex2f(5, 3)
    glVertex2f(-5, 3)
    glEnd()
    glDisable(GL_BLEND)

    # Draw menu title
    glColor3f(1, 1, 1)
    glRasterPos2f(-1.5, 2)
    for c in b"PAUSE MENU":
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, c)

    # Draw menu options based on current state
    if menu_state == "main":
        options = ["1. Resume Game", "2. Change Difficulty", "3. Change Mode", "4. Restart Game"]
        for i, option in enumerate(options):
            glRasterPos2f(-2, 1 - i * 0.5)
            for c in option.encode():
                glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, c)
    elif menu_state == "difficulty":
        options = [f"1. Easy (Current: {'X' if difficulty == 'easy' else ' '})",
                  f"2. Medium (Current: {'X' if difficulty == 'medium' else ' '})",
                  f"3. Hard (Current: {'X' if difficulty == 'hard' else ' '})",
                  "4. Back"]
        for i, option in enumerate(options):
            glRasterPos2f(-2, 1 - i * 0.5)
            for c in option.encode():
                glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, c)
    elif menu_state == "mode":
        options = [f"1. Normal Mode (Current: {'X' if game_mode == 'normal' else ' '})",
                  f"2. Capture the Flag (Current: {'X' if game_mode == 'capture_flag' else ' '})",
                  "3. Back"]
        for i, option in enumerate(options):
            glRasterPos2f(-2, 1 - i * 0.5)
            for c in option.encode():
                glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, c)

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopAttrib()

def reset_game():
    global tank_pos, tank_angle, player_health
    global player_projectiles, explosions, game_over, victory
    global flag_captured, player_score, enemy_score
    
    tank_pos = [0.0, 0.0, 0.0]
    tank_angle = 0.0
    player_health = 200
    player_projectiles = []
    explosions = []
    game_over = False
    victory = False
    flag_captured = False
    player_score = 0
    enemy_score = 0

# --- Smarter Enemy AI ---
def update_enemy_ai():
    for enemy in enemy_tanks:
        if not enemy.alive:
            continue
        dx = tank_pos[0] - enemy.pos[0]
        dz = tank_pos[2] - enemy.pos[2]
        dist = math.sqrt(dx*dx + dz*dz)
        desired_angle = math.degrees(math.atan2(dx, dz))
        angle_diff = (desired_angle - enemy.angle + 360) % 360
        if angle_diff > 180:
            angle_diff -= 360
        # Turn toward player
        enemy.angle += max(min(angle_diff, 1.5), -1.5)
        enemy.angle %= 360
        # Move toward player (slowly)
        if dist > 5:
            rad = math.radians(enemy.angle)
            move_x = math.sin(rad) * 0.15
            move_z = math.cos(rad) * 0.15
            # Avoid player projectiles
            dodge = 0
            for p in player_projectiles:
                if abs(p[2] - enemy.pos[2]) < 2 and abs(p[0] - enemy.pos[0]) < 5:
                    dodge = -1 if (p[0] > enemy.pos[0]) else 1
            enemy.pos[0] += move_x + dodge * 0.2
            enemy.pos[2] += move_z
            check_boundaries(enemy.pos)
        # Fire at player
        if abs(angle_diff) < 10 and random.random() < 0.02:
            ex, ez = math.sin(math.radians(enemy.angle)), math.cos(math.radians(enemy.angle))
            enemy.projectiles.append([enemy.pos[0], 0.2, enemy.pos[2], ex, ez])

# --- Draw all enemy tanks ---
def draw_all_enemies():
    for enemy in enemy_tanks:
        if enemy.alive:
            draw_tank(enemy.pos, enemy.angle, (1, 0, 0))
            draw_health_bar(enemy.pos[0], enemy.pos[2], enemy.health, (1, 0, 0))

# --- Move all enemy projectiles ---
def move_projectiles():
    for p in player_projectiles[:]:
        p[0] += p[3] * 0.5
        p[2] += p[4] * 0.5
        if abs(p[0]) > arena_size or abs(p[2]) > arena_size:
            player_projectiles.remove(p)
    for enemy in enemy_tanks:
        for p in enemy.projectiles[:]:
            p[0] += p[3] * 0.5
            p[2] += p[4] * 0.5
            if abs(p[0]) > arena_size or abs(p[2]) > arena_size:
                enemy.projectiles.remove(p)

# --- Generate More Obstacles (with buildings and better lava) ---
def generate_obstacles():
    global obstacles
    obstacles = []
    spacing = 8
    for x in range(-int(arena_size)+4, int(arena_size)-3, spacing):
        for z in range(-int(arena_size)+4, int(arena_size)-3, spacing):
            # Leave a clear path at the center
            if abs(x) < 6 and abs(z) < 6:
                continue
            # Alternate obstacle types
            if (x+z) % 24 == 0:
                obstacles.append(Obstacle([x, 0, z], 'lava', size=5))
            elif (x-z) % 24 == 0:
                obstacles.append(Obstacle([x, 0, z], 'blade', speed=2, size=2))
            elif (x*z) % 32 == 0:
                obstacles.append(Obstacle([x, 0, z], 'cube', speed=0.1, dir=1, size=2))
            elif (x*z) % 40 == 0:
                obstacles.append(Obstacle([x, 0, z], 'building', size=3))
            else:
                obstacles.append(Obstacle([x, 0, z], 'barrier', speed=1, axis='x', size=2))

generate_obstacles()

# --- Update draw_obstacles for buildings and better lava ---
def draw_obstacles():
    for obs in obstacles:
        glPushMatrix()
        glTranslatef(obs.pos[0], 0, obs.pos[2])
        if obs.kind == 'blade':
            obs.angle += obs.speed
            glRotatef(obs.angle, 0, 1, 0)
            glColor3f(1, 0, 0)
            glScalef(obs.size, 0.2, 0.5)
            glutSolidCube(1.0)
        elif obs.kind == 'lava':
            glColor3f(1, 0.3, 0)
            glTranslatef(0, -0.6, 0)
            glScalef(obs.size, 0.1, obs.size)
            glutSolidCube(1.0)
        elif obs.kind == 'cube':
            obs.t += obs.speed * obs.dir
            if abs(obs.t) > 5:
                obs.dir *= -1
            glTranslatef(0, 0, obs.t)
            glColor3f(0, 0, 1)
            glutSolidCube(obs.size)
        elif obs.kind == 'barrier':
            obs.angle += obs.speed
            if obs.axis == 'x':
                glRotatef(obs.angle, 1, 0, 0)
            else:
                glRotatef(obs.angle, 0, 0, 1)
            glColor3f(0, 1, 1)
            glScalef(4, 0.2, 0.5)
            glutSolidCube(1.0)
        elif obs.kind == 'building':
            glColor3f(0.5, 0.5, 0.5)
            glScalef(obs.size, 4.0, obs.size)
            glutSolidCube(1.0)
        glPopMatrix()

# --- Update can_move_to to block buildings ---
def can_move_to(pos):
    for obs in obstacles:
        if obs.kind in ['blade', 'cube', 'barrier', 'building']:
            if distance(pos, obs.pos) < obs.size:
                return False
        if obs.kind == 'lava':
            continue
    return True

# --- Update collision_check to block projectiles with buildings ---
def check_obstacle_collision(pos, ignore_lava=False):
    for obs in obstacles:
        if obs.kind == 'lava' and not ignore_lava:
            if abs(pos[0] - obs.pos[0]) < obs.size/2 and abs(pos[2] - obs.pos[2]) < obs.size/2:
                return 'lava'
        elif obs.kind in ['blade', 'cube', 'barrier', 'building']:
            if distance(pos, obs.pos) < obs.size:
                return obs.kind
    return None

def collision_check():
    global player_health, game_over, victory
    # Player hit by any enemy projectile
    for enemy in enemy_tanks:
        for p in enemy.projectiles[:]:
            if distance(p, tank_pos) < 1.2:
                player_health -= 20
                enemy.projectiles.remove(p)
                explosions.append(Explosion(tank_pos[0], tank_pos[2]))
                if player_health <= 0:
                    game_over = True
    # Player hit by obstacle
    obs_hit = check_obstacle_collision(tank_pos)
    if obs_hit == 'lava':
        player_health = 0
        game_over = True
    elif obs_hit:
        player_health -= 1
        if player_health <= 0:
            game_over = True
    # Player projectiles hit any enemy or obstacle
    for enemy in enemy_tanks:
        if not enemy.alive:
            continue
        for p in player_projectiles[:]:
            if distance(p, enemy.pos) < 1.2:
                enemy.health -= 20
                player_projectiles.remove(p)
                explosions.append(Explosion(enemy.pos[0], enemy.pos[2]))
                if enemy.health <= 0:
                    enemy.alive = False
            elif check_obstacle_collision(p, ignore_lava=False):
                player_projectiles.remove(p)
    # Enemy tanks hit by obstacles
    for enemy in enemy_tanks:
        if not enemy.alive:
            continue
        obs_hit = check_obstacle_collision(enemy.pos)
        if obs_hit == 'lava':
            enemy.health = 0
            enemy.alive = False
        elif obs_hit:
            enemy.health -= 1
            if enemy.health <= 0:
                enemy.alive = False
    # Enemy projectiles hit obstacles
    for enemy in enemy_tanks:
        for p in enemy.projectiles[:]:
            if check_obstacle_collision(p, ignore_lava=False):
                enemy.projectiles.remove(p)
    # Victory if all enemies are dead
    if all(not e.alive for e in enemy_tanks):
        victory = True
        game_over = True

# --- Utility: Draw game over/victory message ---
def draw_game_message():
    if game_over or victory:
        glPushAttrib(GL_ALL_ATTRIB_BITS)
        glDisable(GL_DEPTH_TEST)
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(-5, 5, -3, 3)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        glColor3f(1, 1, 1)
        glRasterPos2f(-2, 2.5)
        msg = b"Victory!" if victory else b"Game Over"
        for c in msg:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, c)
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopAttrib()

# --- Utility: Keep tank within arena ---
def check_boundaries(pos):
    pos[0] = max(-arena_size + 1, min(arena_size - 1, pos[0]))
    pos[2] = max(-arena_size + 1, min(arena_size - 1, pos[2]))

# --- GLUT Callbacks ---
def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    if not paused:
        if camera_mode == "third_person":
            rad = math.radians(tank_angle)
            cam_x = tank_pos[0] - 5 * math.sin(rad)
            cam_z = tank_pos[2] - 5 * math.cos(rad)
            cam_y = 3.0
            gluLookAt(cam_x, cam_y, cam_z, 
                     tank_pos[0], tank_pos[1] + 1.0, tank_pos[2], 
                     0, 1, 0)
        else:
            gluLookAt(tank_pos[0], 30, tank_pos[2] + 20, 
                     tank_pos[0], 0, tank_pos[2], 
                     0, 1, 0)
        draw_arena()
        draw_tank(tank_pos, tank_angle, (0, 1, 0))
        draw_all_enemies()
        draw_health_bar(tank_pos[0], tank_pos[2], player_health, (0, 1, 0))
        draw_obstacles()
        if game_mode == "capture_flag":
            glPushMatrix()
            glTranslatef(flag_pos[0], 1.0, flag_pos[2])
            glColor3f(1, 1, 0)
            glutSolidSphere(0.5, 16, 16)
            glPopMatrix()
        glColor3f(1, 1, 0)
        for p in player_projectiles:
            glPushMatrix()
            glTranslatef(p[0], p[1], p[2])
            glutSolidSphere(0.2, 8, 8)
            glPopMatrix()
        for enemy in enemy_tanks:
            glColor3f(1, 0, 0)
            for p in enemy.projectiles:
                glPushMatrix()
                glTranslatef(p[0], p[1], p[2])
                glutSolidSphere(0.2, 8, 8)
                glPopMatrix()
        draw_explosions()
        draw_game_message()
    else:
        draw_menu()
    glutSwapBuffers()

def timer(v):
    if not game_over:
        update_enemy_ai()
        move_projectiles()
        collision_check()
    glutPostRedisplay()
    glutTimerFunc(16, timer, 0)

def keyboard(key, x, y):
    global tank_angle, tank_pos, camera_mode, paused, menu_state, difficulty, game_mode
    if key == b'\x1b':  # ESC key
        paused = not paused
        if paused:
            menu_state = "main"
    if paused:
        if key == b'1':
            if menu_state == "main":
                paused = False
            elif menu_state == "difficulty":
                difficulty = "easy"
            elif menu_state == "mode":
                game_mode = "normal"
        elif key == b'2':
            if menu_state == "main":
                menu_state = "difficulty"
            elif menu_state == "difficulty":
                difficulty = "medium"
            elif menu_state == "mode":
                game_mode = "capture_flag"
        elif key == b'3':
            if menu_state == "main":
                menu_state = "mode"
            elif menu_state == "difficulty":
                difficulty = "hard"
            elif menu_state == "mode":
                menu_state = "main"
        elif key == b'4':
            if menu_state == "main":
                reset_game()
            elif menu_state == "difficulty":
                menu_state = "main"
    else:
        rad = math.radians(tank_angle)
        dx, dz = math.sin(rad), math.cos(rad)
        perp_dx, perp_dz = math.sin(rad + math.pi/2), math.cos(rad + math.pi/2)
        new_pos = tank_pos[:]
        if key == b'w':
            new_pos[0] += dx * 0.5
            new_pos[2] += dz * 0.5
            check_boundaries(new_pos)
            if can_move_to(new_pos):
                tank_pos[0], tank_pos[2] = new_pos[0], new_pos[2]
        elif key == b's':
            new_pos[0] -= dx * 0.5
            new_pos[2] -= dz * 0.5
            check_boundaries(new_pos)
            if can_move_to(new_pos):
                tank_pos[0], tank_pos[2] = new_pos[0], new_pos[2]
        elif key == b'a':
            tank_angle += 5
        elif key == b'd':
            tank_angle -= 5
        elif key == b'q':  # Strafe left
            new_pos[0] += perp_dx * 0.5
            new_pos[2] += perp_dz * 0.5
            check_boundaries(new_pos)
            if can_move_to(new_pos):
                tank_pos[0], tank_pos[2] = new_pos[0], new_pos[2]
        elif key == b'e':  # Strafe right
            new_pos[0] -= perp_dx * 0.5
            new_pos[2] -= perp_dz * 0.5
            check_boundaries(new_pos)
            if can_move_to(new_pos):
                tank_pos[0], tank_pos[2] = new_pos[0], new_pos[2]
        elif key == b'v':
            camera_mode = "bird_eye" if camera_mode == "third_person" else "third_person"

def mouse(button, state, x, y):
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN and not game_over:
        rad = math.radians(tank_angle)
        dx, dz = math.sin(rad), math.cos(rad)
        player_projectiles.append([tank_pos[0], 0.2, tank_pos[2], dx, dz])

def reshape(w, h):
    if h == 0: h = 1
    glViewport(0, 0, w, h)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60.0, float(w)/float(h), 1.0, 100.0)
    glMatrixMode(GL_MODELVIEW)

def init():
    glClearColor(0.1, 0.1, 0.1, 1)
    glEnable(GL_DEPTH_TEST)

def main():
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGBA | GLUT_DEPTH)
    glutInitWindowSize(800, 600)
    glutCreateWindow(b"3D Tank Game with Health Bars & Explosions")
    init()
    glutDisplayFunc(display)
    glutKeyboardFunc(keyboard)
    glutMouseFunc(mouse)
    glutReshapeFunc(reshape)
    glutTimerFunc(0, timer, 0)
    glutMainLoop()

if __name__ == '__main__':
    main()
