import math
import time
import random
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.GLUT.fonts import GLUT_BITMAP_HELVETICA_18  

GRID_LENGTH = 50
TANK_RADIUS = 2
BULLET_SPEED = 0.5
TANK_SPEED = 0.5

camera_distance = 15
camera_height = 10
MIN_CAMERA_DISTANCE = 5
MAX_CAMERA_DISTANCE = 30
MIN_CAMERA_HEIGHT = 5
MAX_CAMERA_HEIGHT = 30

game_state = {
    'tanks': [
        {'position': (0, 0, 0), 'rotation': 0, 'health': 100},
        {'position': (30, 0, 30), 'rotation': 180, 'health': 100}
    ],
    'projectiles': [],
    'scores': [0, 0],
    'camera_mode': True,
    'explosions': [],
    'game_over': False,
    'winner': None,
    'powerup': None,
    'powerup_spawn_time': time.time(),
    'powerup_duration': 15,
    'powerup_active': False,
    'powerup_speed_boost': False,
    'powerup_speed_end_time': 0,
    'enemy_mode': 'chasing',
    'avoiding_frames': 0,
    'avoiding_direction': 0,
    # Pause menu state
    'paused': False,
    'pause_menu_index': 0,
    'pause_menu_mode': 'main',  # 'main', 'difficulty', 'gamemode'
    'difficulty': 'easy',  # 'easy', 'medium', 'hard'
    'game_mode': 'normal',  # 'normal', 'ctf'
    'flag': {
        'status': None,  # None, 'held_by_enemy', 'dropped', 'held_by_player'
        'position': None,
        'holder': None,
        'hold_timer': 0.0
    },
}

obstacles = [
    {'type': 'cube', 'x': 10, 'z': 10, 'size': 3},
    {'type': 'cube', 'x': -15, 'z': -15, 'size': 4},
    {'type': 'cube', 'x': 20, 'z': -10, 'size': 5},
    {'type': 'cube', 'x': -20, 'z': 15, 'size': 3},
    {'type': 'cube', 'x': 0, 'z': -25, 'size': 4}
]

# Enemy projectile damage by difficulty (greatly reduced)
ENEMY_PROJECTILE_DAMAGE = {
    'easy': 2,
    'medium': 4,
    'hard': 2
}
ENEMY_FIRE_COOLDOWN = {
    'easy': 15.0,
    'medium': 12.0,
    'hard': 10.0
}
ENEMY_MISS_CHANCE = {
    'easy': 0.4,   # 40% miss
    'medium': 0.3, # 30% miss
    'hard': 0.2    # 20% miss
}

def check_boundary_collision(pos):
    return abs(pos[0]) > GRID_LENGTH or abs(pos[2]) > GRID_LENGTH

def check_obstacle_collision(pos):
    for obs in obstacles:
        distance = math.sqrt((pos[0] - obs['x'])**2 + (pos[2] - obs['z'])**2)
        if distance < (obs['size'] / 2 + TANK_RADIUS):
            return True
    return False

def draw_arena():
    glPushMatrix()
    glColor3f(0.3, 0.7, 0.3)
    glBegin(GL_QUADS)
    glVertex3f(-GRID_LENGTH, 0, -GRID_LENGTH)
    glVertex3f(GRID_LENGTH, 0, -GRID_LENGTH)
    glVertex3f(GRID_LENGTH, 0, GRID_LENGTH)
    glVertex3f(-GRID_LENGTH, 0, GRID_LENGTH)
    glEnd()
    glColor3f(0.5, 0.5, 0.5)
    glBegin(GL_LINES)
    for i in range(-GRID_LENGTH, GRID_LENGTH + 1, 10):
        glVertex3f(i, 0.01, -GRID_LENGTH)
        glVertex3f(i, 0.01, GRID_LENGTH)
        glVertex3f(-GRID_LENGTH, 0.01, i)
        glVertex3f(GRID_LENGTH, 0.01, i)
    glEnd()
    glColor3f(0.7, 0.7, 0.7)
    # North wall
    glPushMatrix()
    glTranslatef(0, 5, -GRID_LENGTH)
    glScalef(2 * GRID_LENGTH, 10, 1)
    glutSolidCube(1)
    glPopMatrix()
    # South wall
    glPushMatrix()
    glTranslatef(0, 5, GRID_LENGTH)
    glScalef(2 * GRID_LENGTH, 10, 1)
    glutSolidCube(1)
    glPopMatrix()
    # East wall
    glPushMatrix()
    glTranslatef(GRID_LENGTH, 5, 0)
    glScalef(1, 10, 2 * GRID_LENGTH)
    glutSolidCube(1)
    glPopMatrix()
    # West wall
    glPushMatrix()
    glTranslatef(-GRID_LENGTH, 5, 0)
    glScalef(1, 10, 2 * GRID_LENGTH)
    glutSolidCube(1)
    glPopMatrix()
    glPopMatrix()

def draw_obstacle(obstacle):
    glPushMatrix()
    glTranslatef(obstacle['x'], obstacle['size'] / 2, obstacle['z'])
    glColor3f(0.5, 0.5, 0.5)
    glutSolidCube(obstacle['size'])
    glPopMatrix()

def draw_tank(tank):
    glPushMatrix()
    glTranslatef(tank['position'][0], 0, tank['position'][2])
    glRotatef(tank['rotation'], 0, 1, 0)
    if tank == game_state['tanks'][0]:
        glColor3f(0.2, 0.2, 0.8)
    else:
        glColor3f(0.8, 0.2, 0.2)
    glutSolidCube(TANK_RADIUS * 2)
    glColor3f(0.3, 0.3, 0.3)
    glTranslatef(0, TANK_RADIUS, 0)
    glutSolidCube(TANK_RADIUS)
    glTranslatef(0, 0, TANK_RADIUS)
    glRotatef(90, 1, 0, 0)
    quadric = gluNewQuadric()
    gluCylinder(quadric, TANK_RADIUS / 3, TANK_RADIUS / 3, TANK_RADIUS * 2, 10, 10)
    glPopMatrix()
    # Healthbar
    glPushMatrix()
    glTranslatef(tank['position'][0], 0, tank['position'][2])
    glRotatef(-tank['rotation'], 0, 1, 0)
    glTranslatef(0, TANK_RADIUS * 2.5, 0)
    health_ratio = max(0, min(1, tank['health'] / 100))
    red = 1.0 - health_ratio
    green = health_ratio
    glColor3f(red, green, 0.0)
    bar_width = 4.0 * health_ratio
    bar_height = 0.5
    glBegin(GL_QUADS)
    glVertex3f(-2.0, 0, 0)
    glVertex3f(-2.0 + bar_width, 0, 0)
    glVertex3f(-2.0 + bar_width, bar_height, 0)
    glVertex3f(-2.0, bar_height, 0)
    glEnd()
    glPopMatrix()

def draw_projectile(projectile):
    glPushMatrix()
    glTranslatef(projectile['position'][0], 0.5, projectile['position'][2])
    if projectile['owner'] == 0:
        glColor3f(0.0, 0.0, 1.0)
    else:
        glColor3f(1.0, 0.0, 0.0)
    quadric = gluNewQuadric()
    gluSphere(quadric, 0.3, 10, 10)
    glPopMatrix()

def draw_explosion(explosion):
    glPushMatrix()
    glTranslatef(explosion['position'][0], 0, explosion['position'][2])
    scale = 1.0 + 1.5 * (1.0 - explosion['lifetime'] / 30.0)
    glScalef(scale, scale, scale)
    glColor3f(1.0, 0.5, 0.0)
    glutSolidSphere(1.0, 16, 16)
    glPopMatrix()

def create_explosion(position):
    explosion = {
        'position': position,
        'lifetime': 30
    }
    game_state['explosions'].append(explosion)

def update_explosions():
    to_remove = []
    for i, explosion in enumerate(game_state['explosions']):
        explosion['lifetime'] -= 1
        if explosion['lifetime'] <= 0:
            to_remove.append(i)
    for i in reversed(to_remove):
        del game_state['explosions'][i]

def spawn_powerup():
    if game_state['powerup'] is not None:
        return
    while True:
        x = random.uniform(-GRID_LENGTH + 5, GRID_LENGTH - 5)
        z = random.uniform(-GRID_LENGTH + 5, GRID_LENGTH - 5)
        pos = (x, 0, z)
        if check_obstacle_collision(pos):
            continue
        collision = False
        for tank in game_state['tanks']:
            dist = math.sqrt((pos[0] - tank['position'][0])**2 + (pos[2] - tank['position'][2])**2)
            if dist < TANK_RADIUS * 2:
                collision = True
                break
        if collision:
            continue
        game_state['powerup'] = {'position': pos, 'spawn_time': time.time()}
        break

def check_powerup_collection():
    if game_state['powerup'] is None:
        return
    player_pos = game_state['tanks'][0]['position']
    powerup_pos = game_state['powerup']['position']
    dist = math.sqrt((player_pos[0] - powerup_pos[0])**2 + (player_pos[2] - powerup_pos[2])**2)
    if dist < TANK_RADIUS * 2:
        if random.random() < 0.5:
            game_state['tanks'][0]['health'] = 100
        else:
            game_state['powerup_speed_boost'] = True
            game_state['powerup_speed_end_time'] = time.time() + 10
        game_state['powerup'] = None
        game_state['powerup_spawn_time'] = time.time()

def update_powerup():
    if game_state['game_over']:
        return
    if game_state['powerup'] is None:
        if time.time() - game_state['powerup_spawn_time'] > random.uniform(15, 20):
            spawn_powerup()
    else:
        if time.time() - game_state['powerup']['spawn_time'] > 15:
            game_state['powerup'] = None
            game_state['powerup_spawn_time'] = time.time()
    if game_state['powerup_speed_boost'] and time.time() > game_state['powerup_speed_end_time']:
        game_state['powerup_speed_boost'] = False

def draw_powerup():
    if game_state['powerup'] is None:
        return
    glPushMatrix()
    glTranslatef(game_state['powerup']['position'][0],
                 TANK_RADIUS / 2 + 0.5 * math.sin(time.time() * 2),
                 game_state['powerup']['position'][2])
    glRotatef(time.time() * 50 % 360, 0, 1, 0)
    glColor3f(1.0, 1.0, 0.0)
    glutSolidCube(1.0)
    glPopMatrix()

def draw_text(text, x, y):
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, 800, 0, 600, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glColor3f(1, 1, 1)
    glRasterPos2i(x, y)
    for char in text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_minimap():
    # Minimap boundaries
    minimap_left = 600
    minimap_right = 780
    minimap_bottom = 500
    minimap_top = 580
    minimap_width = minimap_right - minimap_left
    minimap_height = minimap_top - minimap_bottom
    arena_size = GRID_LENGTH * 2

    def world_to_minimap(x, z):
        mx = minimap_left + ((x + GRID_LENGTH) / arena_size) * minimap_width
        mz = minimap_bottom + ((z + GRID_LENGTH) / arena_size) * minimap_height
        return mx, mz

    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, 800, 0, 600, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    # Draw minimap background
    glColor3f(0.1, 0.1, 0.1)
    glBegin(GL_QUADS)
    glVertex2f(minimap_left, minimap_bottom)
    glVertex2f(minimap_right, minimap_bottom)
    glVertex2f(minimap_right, minimap_top)
    glVertex2f(minimap_left, minimap_top)
    glEnd()

    # Draw grid lines
    glColor3f(0.3, 0.3, 0.3)
    grid_step = minimap_width // 6
    for i in range(0, 7):
        x = minimap_left + i * grid_step
        glBegin(GL_LINES)
        glVertex2f(x, minimap_bottom)
        glVertex2f(x, minimap_top)
        glEnd()
    grid_step = minimap_height // 4
    for i in range(0, 5):
        y = minimap_bottom + i * grid_step
        glBegin(GL_LINES)
        glVertex2f(minimap_left, y)
        glVertex2f(minimap_right, y)
        glEnd()

    # Draw North indicator at top center
    glColor3f(1.0, 1.0, 1.0)
    glRasterPos2f((minimap_left + minimap_right) / 2 - 5, minimap_top - 10)
    glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord('N'))

    # Draw obstacles as small squares
    glColor3f(0.5, 0.5, 0.5)
    for obs in obstacles:
        x, z = world_to_minimap(obs['x'], obs['z'])
        size = obs['size'] * (minimap_width / arena_size)
        glBegin(GL_QUADS)
        glVertex2f(x - size/2, z - size/2)
        glVertex2f(x + size/2, z - size/2)
        glVertex2f(x + size/2, z + size/2)
        glVertex2f(x - size/2, z + size/2)
        glEnd()

    # Draw projectiles as dots
    for proj in game_state['projectiles']:
        x, z = world_to_minimap(proj['position'][0], proj['position'][2])
        if proj['owner'] == 0:
            glColor3f(0.0, 0.7, 1.0)  # Player: blue
        else:
            glColor3f(1.0, 0.2, 0.2)  # Enemy: red
        glBegin(GL_POLYGON)
        for a in range(12):
            angle = 2 * math.pi * a / 12
            glVertex2f(x + 3 * math.cos(angle), z + 3 * math.sin(angle))
        glEnd()

    # Draw player tank (green triangle)
    player = game_state['tanks'][0]
    x, z = world_to_minimap(player['position'][0], player['position'][2])
    glColor3f(0.0, 1.0, 0.0)
    glPushMatrix()
    glTranslatef(x, z, 0)
    glRotatef(player['rotation'], 0, 0, 1)
    glBegin(GL_TRIANGLES)
    glVertex2f(0, 6)
    glVertex2f(-4, -4)
    glVertex2f(4, -4)
    glEnd()
    glPopMatrix()

    # Draw enemy tanks (red triangles)
    for i, enemy in enumerate(game_state['tanks'][1:], 1):
        x, z = world_to_minimap(enemy['position'][0], enemy['position'][2])
        glColor3f(1.0, 0.0, 0.0)
        glPushMatrix()
        glTranslatef(x, z, 0)
        glRotatef(enemy['rotation'], 0, 0, 1)
        glBegin(GL_TRIANGLES)
        glVertex2f(0, 6)
        glVertex2f(-4, -4)
        glVertex2f(4, -4)
        glEnd()
        glPopMatrix()

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_pause_menu():
    # Draw semi-transparent overlay
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, 800, 0, 600, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(0, 0, 0, 0.7)
    glBegin(GL_QUADS)
    glVertex2f(0, 0)
    glVertex2f(800, 0)
    glVertex2f(800, 600)
    glVertex2f(0, 600)
    glEnd()
    glDisable(GL_BLEND)
    # Draw menu box
    glColor3f(0.2, 0.2, 0.2)
    glBegin(GL_QUADS)
    glVertex2f(250, 180)
    glVertex2f(550, 180)
    glVertex2f(550, 420)
    glVertex2f(250, 420)
    glEnd()
    # Menu options
    main_options = ["Resume", "Restart", "Difficulty Settings", "Game Mode"]
    diff_options = ["Easy", "Medium", "Hard"]
    mode_options = ["Normal", "Capture the Flag"]
    y_start = 370
    x_arrow = 295
    x_text = 320
    arrow_size = 10
    if game_state['pause_menu_mode'] == 'main':
        for i, opt in enumerate(main_options):
            y = y_start - i * 50
            if i == game_state['pause_menu_index']:
                # Draw yellow triangle indicator
                glColor3f(1, 1, 0)
                glBegin(GL_TRIANGLES)
                glVertex2f(x_arrow, y + 7)
                glVertex2f(x_arrow - arrow_size, y)
                glVertex2f(x_arrow, y - 7)
                glEnd()
            color = (1, 1, 0) if i == game_state['pause_menu_index'] else (1, 1, 1)
            glColor3f(*color)
            draw_text(opt, x_text, y)
    elif game_state['pause_menu_mode'] == 'difficulty':
        for i, opt in enumerate(diff_options):
            y = y_start - i * 50
            label = opt + (" (current)" if opt.lower() == game_state['difficulty'] else "")
            if i == game_state['pause_menu_index']:
                glColor3f(1, 1, 0)
                glBegin(GL_TRIANGLES)
                glVertex2f(x_arrow, y + 7)
                glVertex2f(x_arrow - arrow_size, y)
                glVertex2f(x_arrow, y - 7)
                glEnd()
            color = (1, 1, 0) if i == game_state['pause_menu_index'] else (1, 1, 1)
            glColor3f(*color)
            draw_text(label, x_text, y)
    elif game_state['pause_menu_mode'] == 'gamemode':
        for i, opt in enumerate(mode_options):
            y = y_start - i * 50
            label = opt + (" (current)" if (opt.lower() == game_state['game_mode'] or (opt == 'Normal' and game_state['game_mode'] == 'normal')) else "")
            if i == game_state['pause_menu_index']:
                glColor3f(1, 1, 0)
                glBegin(GL_TRIANGLES)
                glVertex2f(x_arrow, y + 7)
                glVertex2f(x_arrow - arrow_size, y)
                glVertex2f(x_arrow, y - 7)
                glEnd()
            color = (1, 1, 0) if i == game_state['pause_menu_index'] else (1, 1, 1)
            glColor3f(*color)
            draw_text(label, x_text, y)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_hud():
    if game_state.get('paused', False):
        draw_pause_menu()
        return
    draw_text(f"Player: {game_state['scores'][0]}  Enemy: {game_state['scores'][1]}", 10, 580)
    draw_text(f"Player Health: {game_state['tanks'][0]['health']}", 10, 560)
    draw_text(f"Enemy Health: {game_state['tanks'][1]['health']}", 10, 540)
    if game_state['powerup_speed_boost']:
        time_left = int(game_state['powerup_speed_end_time'] - time.time())
        draw_text(f"Speed Boost: {time_left}s", 10, 520)
    draw_text(f"Enemy Mode: {game_state['enemy_mode']}", 10, 500)
    # CTF HUD
    if game_state.get('game_mode', 'normal') == 'ctf':
        flag = game_state['flag']
        if flag['status'] == 'held_by_player':
            draw_text(f"Flag held! Hold for {max(0, int(1000-flag['hold_timer']))}s to win!", 250, 560)
        elif flag['status'] == 'dropped':
            draw_text(f"Flag dropped! Pick it up!", 250, 560)
        elif flag['status'] == 'held_by_enemy':
            draw_text(f"Enemy has the flag!", 250, 560)
    if game_state.get('game_over', False):
        winner = game_state.get('winner', None)
        if winner is not None:
            text = f"PLAYER {winner + 1} WINS! Press R to restart"
            draw_text(text, 250, 300)
    draw_minimap()

def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, 800/600, 0.1, 1000)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    if game_state['camera_mode']:
        tank_pos = game_state['tanks'][0]['position']
        tank_rot = game_state['tanks'][0]['rotation']
        global camera_distance, camera_height
        rot_rad = math.radians(tank_rot)
        camera_x = tank_pos[0] - camera_distance * math.sin(rot_rad)
        camera_z = tank_pos[2] - camera_distance * math.cos(rot_rad)
        gluLookAt(
            camera_x, camera_height, camera_z,
            tank_pos[0], 0, tank_pos[2],
            0, 1, 0
        )
    else:
        gluLookAt(
            0, 80, 0,
            0, 0, 0,
            0, 0, -1
        )

def draw_shapes():
    draw_arena()
    
    for obs in obstacles:
        draw_obstacle(obs)
    
    draw_powerup()
   
    for tank in game_state['tanks']:
        draw_tank(tank)
 
    # Draw flag if in CTF mode
    if game_state.get('game_mode', 'normal') == 'ctf' and game_state['flag']['status']:
        if game_state['flag']['status'] == 'dropped':
            draw_flag('dropped', flag_pos=game_state['flag']['position'])
        elif game_state['flag']['status'] == 'held_by_enemy':
            holder = game_state['flag']['holder']
            if holder is not None and holder < len(game_state['tanks']):
                draw_flag('held_by_enemy', tank=game_state['tanks'][holder])
        elif game_state['flag']['status'] == 'held_by_player':
            draw_flag('held_by_player', tank=game_state['tanks'][0])
   
    for proj in game_state['projectiles']:
        draw_projectile(proj)
   
    for explosion in game_state['explosions']:
        draw_explosion(explosion)
   
    draw_hud()

def display():
    glClear(GL_COLOR_BUFFER_BIT)
    setupCamera()
    draw_shapes()
    glutSwapBuffers()

def check_projectile_tank_collision(proj_pos, tank_pos):
    distance = math.sqrt((proj_pos[0] - tank_pos[0])**2 + (proj_pos[2] - tank_pos[2])**2)
    return distance < TANK_RADIUS

def check_tank_collision(tank1_pos, tank2_pos):
    distance = math.sqrt((tank1_pos[0] - tank2_pos[0])**2 + (tank1_pos[2] - tank2_pos[2])**2)
    return distance < TANK_RADIUS * 2

def respawn_tank(tank_idx):
    game_state['tanks'][tank_idx]['health'] = 100
    valid_position = False
    while not valid_position:
        x = (2 * (tank_idx % 2) - 1) * (GRID_LENGTH - 10) * (0.3 + 0.7 * (random.random()))
        z = (2 * (tank_idx // 2) - 1) * (GRID_LENGTH - 10) * (0.3 + 0.7 * (random.random()))
        pos = (x, 0, z)
        valid_position = True
        if check_obstacle_collision(pos):
            valid_position = False
            continue
        for other_idx, other_tank in enumerate(game_state['tanks']):
            if other_idx != tank_idx and check_tank_collision(pos, other_tank['position']):
                valid_position = False
                break
    game_state['tanks'][tank_idx]['position'] = pos
    game_state['tanks'][tank_idx]['rotation'] = 0 if tank_idx == 0 else 180

def reset_game():
    game_state['scores'] = [0, 0]
    for i in range(len(game_state['tanks'])):
        respawn_tank(i)
    game_state['projectiles'] = []
    game_state['explosions'] = []
    game_state['game_over'] = False
    game_state['winner'] = None
    game_state['powerup'] = None
    game_state['powerup_spawn_time'] = time.time()
    game_state['powerup_speed_boost'] = False
    game_state['enemy_mode'] = 'chasing'
    game_state['avoiding_frames'] = 0
    game_state['avoiding_direction'] = 0
    game_state['flag'] = {
        'status': None,
        'position': None,
        'holder': None,
        'hold_timer': 0.0
    }

def check_win_condition():
    if game_state.get('game_over', False):
        return
    if game_state['scores'][0] >= 5:
        game_state['game_over'] = True
        game_state['winner'] = 0
    elif game_state['scores'][1] >= 5:
        game_state['game_over'] = True
        game_state['winner'] = 1

def update_projectiles():
    if game_state['game_over']:
        return
    projectiles_to_remove = []
    for i, proj in enumerate(game_state['projectiles']):
        pos = list(proj['position'])
        dir_vector = proj['direction']
        pos[0] += dir_vector[0] * BULLET_SPEED
        pos[1] += dir_vector[1] * BULLET_SPEED
        pos[2] += dir_vector[2] * BULLET_SPEED
        proj['position'] = tuple(pos)
        if (abs(pos[0]) > GRID_LENGTH or abs(pos[2]) > GRID_LENGTH):
            projectiles_to_remove.append(i)
            continue
        if check_obstacle_collision(pos):
            projectiles_to_remove.append(i)
            create_explosion(pos)
            continue
        for tank_idx, tank in enumerate(game_state['tanks']):
            if proj['owner'] != tank_idx:
                if check_projectile_tank_collision(pos, tank['position']):
                    projectiles_to_remove.append(i)
                    create_explosion(pos)
                    # Use different damage for player/enemy
                    if proj['owner'] == 0:
                        tank['health'] -= 20
                    else:
                        tank['health'] -= ENEMY_PROJECTILE_DAMAGE.get(game_state.get('difficulty', 'easy'), 10)
                    if tank['health'] <= 0:
                        # CTF: If player kills enemy holding flag, drop flag
                        if game_state.get('game_mode', 'normal') == 'ctf' and tank_idx != 0 and game_state['flag']['status'] == 'held_by_enemy' and game_state['flag']['holder'] == tank_idx:
                            game_state['flag']['status'] = 'dropped'
                            game_state['flag']['position'] = tank['position']
                            game_state['flag']['holder'] = None
                            game_state['flag']['hold_timer'] = 0.0
                        # CTF: If player is killed while holding flag, enemy wins
                        if game_state.get('game_mode', 'normal') == 'ctf' and tank_idx == 0 and game_state['flag']['status'] == 'held_by_player':
                            game_state['game_over'] = True
                            game_state['winner'] = 1
                        game_state['scores'][proj['owner']] += 1
                        respawn_tank(tank_idx)
                    break
    for i in sorted(projectiles_to_remove, reverse=True):
        if i < len(game_state['projectiles']):
            game_state['projectiles'].pop(i)

def update_enemy_ai():
    if game_state['game_over']:
        return
    # For each enemy tank (all except player)
    for idx, enemy in enumerate(game_state['tanks'][1:], 1):
        player = game_state['tanks'][0]
        if 'enemy_mode' not in enemy:
            enemy['enemy_mode'] = 'chasing'
        if 'avoiding_frames' not in enemy:
            enemy['avoiding_frames'] = 0
        if 'avoiding_direction' not in enemy:
            enemy['avoiding_direction'] = 0
        if 'fire_cooldown' not in enemy:
            enemy['fire_cooldown'] = 0
        dx = player['position'][0] - enemy['position'][0]
        dz = player['position'][2] - enemy['position'][2]
        target_angle = math.degrees(math.atan2(dx, dz)) % 360
        current_angle = enemy['rotation']
        angle_diff = (target_angle - current_angle + 180) % 360 - 180
        distance = math.sqrt(dx**2 + dz**2)
        # Smoother rotation and movement
        ROT_SPEED = 1.2 if game_state['difficulty'] == 'easy' else 1.5 if game_state['difficulty'] == 'medium' else 1.0
        MOVE_SPEED = TANK_SPEED * (0.4 if game_state['difficulty'] == 'hard' else 0.5)
        if enemy['enemy_mode'] == 'chasing':
            if abs(angle_diff) > 5:
                if angle_diff > 0:
                    enemy['rotation'] = (current_angle + ROT_SPEED) % 360
                else:
                    enemy['rotation'] = (current_angle - ROT_SPEED) % 360
            if distance > 20 and abs(angle_diff) < 10:
                pos = list(enemy['position'])
                rot = enemy['rotation']
                pos[0] += MOVE_SPEED * math.sin(math.radians(rot))
                pos[2] += MOVE_SPEED * math.cos(math.radians(rot))
                if check_boundary_collision(pos) or check_obstacle_collision(pos):
                    enemy['enemy_mode'] = 'avoiding'
                    enemy['avoiding_frames'] = 20
                    enemy['avoiding_direction'] = random.choice([1, -1])
                else:
                    enemy['position'] = tuple(pos)
            # Fire cooldown
            if enemy['fire_cooldown'] > 0:
                enemy['fire_cooldown'] -= 1/60.0
            if abs(angle_diff) < 5 and distance < 40 and enemy['fire_cooldown'] <= 0:
                # MISS CHANCE
                miss_chance = ENEMY_MISS_CHANCE.get(game_state['difficulty'], 0.3)
                fire_angle = enemy['rotation']
                if random.random() < miss_chance:
                    fire_angle += random.uniform(-40, 40)  # Miss by up to ±40 degrees
                direction = (
                    math.sin(math.radians(fire_angle)),
                    0,
                    math.cos(math.radians(fire_angle))
                )
                projectile = {
                    'position': enemy['position'],
                    'direction': direction,
                    'owner': idx
                }
                game_state['projectiles'].append(projectile)
                enemy['fire_cooldown'] = ENEMY_FIRE_COOLDOWN.get(game_state['difficulty'], 1.2)
        elif enemy['enemy_mode'] == 'avoiding':
            if enemy['avoiding_frames'] > 0:
                enemy['rotation'] = (enemy['rotation'] + 2 * enemy['avoiding_direction']) % 360
                enemy['avoiding_frames'] -= 1
                if enemy['avoiding_frames'] % 5 == 0:
                    pos = list(enemy['position'])
                    rot = enemy['rotation']
                    pos[0] += MOVE_SPEED * math.sin(math.radians(rot))
                    pos[2] += MOVE_SPEED * math.cos(math.radians(rot))
                    if not check_boundary_collision(pos) and not check_obstacle_collision(pos):
                        enemy['position'] = tuple(pos)
            else:
                enemy['enemy_mode'] = 'chasing'

def keyboardListener(key, x, y):
    if key == b'\x1b':  # ESC
        if not game_state['paused']:
            game_state['paused'] = True
            game_state['pause_menu_index'] = 0
            game_state['pause_menu_mode'] = 'main'
        else:
            game_state['paused'] = False
        glutPostRedisplay()
        return
    if game_state['paused']:
        # Menu navigation
        if key == b'\r' or key == b'\n':  # Enter
            if game_state['pause_menu_mode'] == 'main':
                if game_state['pause_menu_index'] == 0:  # Resume
                    game_state['paused'] = False
                elif game_state['pause_menu_index'] == 1:  # Restart
                    reset_game()
                    game_state['paused'] = False
                elif game_state['pause_menu_index'] == 2:  # Difficulty
                    game_state['pause_menu_mode'] = 'difficulty'
                    game_state['pause_menu_index'] = ['easy', 'medium', 'hard'].index(game_state['difficulty'])
                elif game_state['pause_menu_index'] == 3:  # Game Mode
                    game_state['pause_menu_mode'] = 'gamemode'
                    game_state['pause_menu_index'] = 0 if game_state['game_mode'] == 'normal' else 1
            elif game_state['pause_menu_mode'] == 'difficulty':
                selected = ['easy', 'medium', 'hard'][game_state['pause_menu_index']]
                if selected != game_state['difficulty']:
                    game_state['difficulty'] = selected
                    if selected == 'medium':
                        # Increase enemy fire rate
                        pass  # Will implement in AI logic
                    elif selected == 'hard':
                        # Add 2 more tanks if not already present
                        while len(game_state['tanks']) < 4:
                            import random
                            pos = (random.uniform(-GRID_LENGTH+5, GRID_LENGTH-5), 0, random.uniform(-GRID_LENGTH+5, GRID_LENGTH-5))
                            game_state['tanks'].append({'position': pos, 'rotation': random.randint(0, 359), 'health': 100})
                    elif selected == 'easy':
                        # Remove extra tanks if present
                        game_state['tanks'] = game_state['tanks'][:2]
                game_state['pause_menu_mode'] = 'main'
                game_state['pause_menu_index'] = 2
            elif game_state['pause_menu_mode'] == 'gamemode':
                selected = ['normal', 'ctf'][game_state['pause_menu_index']]
                game_state['game_mode'] = selected
                game_state['pause_menu_mode'] = 'main'
                game_state['pause_menu_index'] = 3
            glutPostRedisplay()
        elif key == b'\x1b':  # ESC in menu
            if game_state['pause_menu_mode'] == 'main':
                game_state['paused'] = False
            else:
                game_state['pause_menu_mode'] = 'main'
                game_state['pause_menu_index'] = 0
            glutPostRedisplay()
        elif key == b'w':  # Up
            game_state['pause_menu_index'] = (game_state['pause_menu_index'] - 1) % (4 if game_state['pause_menu_mode']=='main' else 3 if game_state['pause_menu_mode']=='difficulty' else 2)
            glutPostRedisplay()
        elif key == b's':  # Down
            game_state['pause_menu_index'] = (game_state['pause_menu_index'] + 1) % (4 if game_state['pause_menu_mode']=='main' else 3 if game_state['pause_menu_mode']=='difficulty' else 2)
            glutPostRedisplay()
        return
    if game_state['game_over']:
        if key == b'r':
            reset_game()
        return
    if key == b'w':
        pos = list(game_state['tanks'][0]['position'])
        rot = game_state['tanks'][0]['rotation']
        speed_multiplier = 2.0 if game_state['powerup_speed_boost'] else 1.0
        pos[0] += TANK_SPEED * speed_multiplier * math.sin(math.radians(rot))
        pos[2] += TANK_SPEED * speed_multiplier * math.cos(math.radians(rot))
        if not check_boundary_collision(pos) and not check_obstacle_collision(pos):
            game_state['tanks'][0]['position'] = tuple(pos)
    elif key == b's':
        pos = list(game_state['tanks'][0]['position'])
        rot = game_state['tanks'][0]['rotation']
        speed_multiplier = 2.0 if game_state['powerup_speed_boost'] else 1.0
        pos[0] -= TANK_SPEED * speed_multiplier * math.sin(math.radians(rot))
        pos[2] -= TANK_SPEED * speed_multiplier * math.cos(math.radians(rot))
        if not check_boundary_collision(pos) and not check_obstacle_collision(pos):
            game_state['tanks'][0]['position'] = tuple(pos)
    elif key == b'a':
        game_state['tanks'][0]['rotation'] = (game_state['tanks'][0]['rotation'] + 5) % 360
    elif key == b'd':
        game_state['tanks'][0]['rotation'] = (game_state['tanks'][0]['rotation'] - 5) % 360
    elif key == b'c':
        game_state['scores'][0] += 1
    elif key == b'v':
        game_state['scores'][1] += 1
    elif key == b'r':
        reset_game()
    glutPostRedisplay()

def specialKeyListener(key, x, y):
    global camera_distance, camera_height
    if key == GLUT_KEY_F1:
        game_state['camera_mode'] = not game_state['camera_mode']
    elif key == GLUT_KEY_UP:
        camera_distance = max(MIN_CAMERA_DISTANCE, camera_distance - 1)
        camera_height = max(MIN_CAMERA_HEIGHT, camera_height - 1)
    elif key == GLUT_KEY_DOWN:
        camera_distance = min(MAX_CAMERA_DISTANCE, camera_distance + 1)
        camera_height = min(MAX_CAMERA_HEIGHT, camera_height + 1)
    glutPostRedisplay()

def mouseListener(button, state, x, y):
    if game_state['game_over']:
        return
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        tank_pos = game_state['tanks'][0]['position']
        rotation = game_state['tanks'][0]['rotation']
        rad = math.radians(rotation)
        direction = (math.sin(rad), 0, math.cos(rad))
        projectile = {
            'position': tank_pos,
            'direction': direction,
            'owner': 0
        }
        game_state['projectiles'].append(projectile)
    glutPostRedisplay()

def idle():
    if game_state.get('paused', False):
        return
    update_projectiles()
    update_explosions()
    update_powerup()
    check_powerup_collection()
    update_enemy_ai()
    check_flag_logic()
    check_win_condition()
    glutPostRedisplay()

def init():
    glClearColor(0.0, 0.0, 0.0, 0.0)

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)
    glutInitWindowSize(800, 600)
    glutCreateWindow(b"3D Tank Battle Arena")
    init()
    glutDisplayFunc(display)
    glutIdleFunc(idle)
    glutKeyboardFunc(keyboardListener)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutMainLoop()

def draw_flag(flag_status, flag_pos=None, tank=None):
    glPushMatrix()
    if flag_status == 'dropped' and flag_pos is not None:
        glTranslatef(flag_pos[0], 2.5, flag_pos[2])
    elif flag_status in ['held_by_enemy', 'held_by_player'] and tank is not None:
        glTranslatef(tank['position'][0], 2.5 + TANK_RADIUS * 2.5, tank['position'][2])
    else:
        glPopMatrix()
        return
    # Draw flag pole (thin cylinder)
    glColor3f(0.8, 0.8, 0.8)
    glPushMatrix()
    glRotatef(-90, 1, 0, 0)
    quadric = gluNewQuadric()
    gluCylinder(quadric, 0.08, 0.08, 2.5, 8, 1)
    glPopMatrix()
    # Draw flag (triangle)
    glColor3f(1.0, 1.0, 0.0)
    glBegin(GL_TRIANGLES)
    glVertex3f(0, 2.2, 0)
    glVertex3f(1.0, 1.7, 0)
    glVertex3f(0, 1.7, 0)
    glEnd()
    glPopMatrix()

def check_flag_logic():
    if game_state.get('game_mode', 'normal') != 'ctf':
        return
    flag = game_state['flag']
    # Initial state: enemy holds flag
    if flag['status'] is None:
        flag['status'] = 'held_by_enemy'
        flag['holder'] = 1
        flag['position'] = None
        flag['hold_timer'] = 0.0
    # If flag is held by player, increment timer
    if flag['status'] == 'held_by_player':
        flag['hold_timer'] += 1/60.0
        if flag['hold_timer'] >= 1000.0:
            game_state['game_over'] = True
            game_state['winner'] = 0
    # If flag is dropped, check if player picks it up
    if flag['status'] == 'dropped' and flag['position'] is not None:
        player_pos = game_state['tanks'][0]['position']
        dist = math.sqrt((player_pos[0] - flag['position'][0])**2 + (player_pos[2] - flag['position'][2])**2)
        if dist < TANK_RADIUS * 2:
            flag['status'] = 'held_by_player'
            flag['holder'] = 0
            flag['position'] = None
            flag['hold_timer'] = 0.0

if __name__ == "__main__":
    main()