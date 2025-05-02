import math
import time
import random
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

# Constants
GRID_LENGTH = 50
TANK_RADIUS = 2
BULLET_SPEED = 0.5
TANK_SPEED = 0.5
BOSS_HEALTH = 500  # New constant for boss health
BOSS_SPEED = 0.4   # New constant for boss movement speed
PORTAL_RADIUS = 3  # New constant for teleport portal

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
    'boss_active': False,  # New flag for boss mode
    'boss': None,          # New field to store boss data
    'enemy_fire_rate': 0.01,  # New field for enemy fire rate
    'boss_fire_rate': 0.05,   # New field for boss fire rate
    'auto_teleport_enabled': False,  # New flag for auto-teleport
    'last_auto_teleport_time': time.time(),  # New field for teleport timing
    'portal_active': False,  # New field for portal visualization
    'portal_position': (0, 0, 0),  # New field for portal position
    'portal_timer': 0  # New field for portal animation
}

# Enhanced obstacles with dynamic properties
obstacles = [
    {'type': 'cube', 'x': 10, 'z': 10, 'size': 3, 'dynamic': False},
    {'type': 'cube', 'x': -15, 'z': -15, 'size': 4, 'dynamic': True, 'speed': 0.3, 'direction': (1, 0), 'direction_change_time': time.time()},
    {'type': 'cube', 'x': 20, 'z': -10, 'size': 5, 'dynamic': False, 'visible': True, 'toggle_time': time.time(), 'next_toggle': random.uniform(5, 10)},
    {'type': 'barrier', 'x': -20, 'z': 15, 'size': 3, 'dynamic': True, 'rotation': 0, 'rotation_speed': 30},
    {'type': 'cube', 'x': 0, 'z': -25, 'size': 4, 'dynamic': True, 'speed': 0.3, 'direction': (0, 1), 'direction_change_time': time.time()}
]

def check_boundary_collision(pos):
    return abs(pos[0]) > GRID_LENGTH or abs(pos[2]) > GRID_LENGTH

def check_obstacle_collision(pos):
    for obs in obstacles:
        if not obs.get('visible', True):
            continue
        
        if obs['type'] == 'cube':
            distance = math.sqrt((pos[0] - obs['x'])**2 + (pos[2] - obs['z'])**2)
            if distance < (obs['size'] / 2 + TANK_RADIUS):
                return True
        elif obs['type'] == 'barrier':
            distance = math.sqrt((pos[0] - obs['x'])**2 + (pos[2] - obs['z'])**2)
            if distance < (obs['size'] * 1.5 + TANK_RADIUS):
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
    if not obstacle.get('visible', True):
        return
        
    glPushMatrix()
    
    if obstacle['type'] == 'barrier':
        glTranslatef(obstacle['x'], obstacle['size'] / 2, obstacle['z'])
        glRotatef(obstacle['rotation'], 0, 1, 0)
        glScalef(3, 1, 0.5)
        glColor3f(0.5, 0.5, 0.5)
        glutSolidCube(obstacle['size'])
    else:  # 'cube' type
        glTranslatef(obstacle['x'], obstacle['size'] / 2, obstacle['z'])
        glColor3f(0.5, 0.5, 0.5)
        glutSolidCube(obstacle['size'])
        
    glPopMatrix()

def draw_tank(tank, is_boss=False):
    glPushMatrix()
    
    scale = 2.0 if is_boss else 1.0
    
    glTranslatef(tank['position'][0], 0, tank['position'][2])
    glRotatef(tank['rotation'], 0, 1, 0)
    
    if tank == game_state['tanks'][0]:
        glColor3f(0.2, 0.2, 0.8)  # Blue for player
    elif is_boss:
        glColor3f(0.5, 0.0, 0.5)  # Purple for boss
    else:
        glColor3f(0.8, 0.2, 0.2)  # Red for enemy
    
    glScalef(scale, scale, scale)
    glutSolidCube(TANK_RADIUS * 2)
    
    glColor3f(0.3, 0.3, 0.3)
    glTranslatef(0, TANK_RADIUS, 0)
    glutSolidCube(TANK_RADIUS)
    
    glTranslatef(0, 0, TANK_RADIUS)
    glRotatef(90, 1, 0, 0)
    quadric = gluNewQuadric()
    gluCylinder(quadric, TANK_RADIUS / 3, TANK_RADIUS / 3, TANK_RADIUS * 2, 10, 10)
    
    glPopMatrix()
    
    # Health bar (fixed orientation)
    glPushMatrix()
    glTranslatef(tank['position'][0], 0, tank['position'][2])
    glRotatef(-tank['rotation'], 0, 1, 0)
    glTranslatef(0, TANK_RADIUS * 2.5 * scale, 0)
    
    max_health = BOSS_HEALTH if is_boss else 100
    health_ratio = max(0, min(1, tank['health'] / max_health))
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
        glColor3f(0.0, 0.0, 1.0)  # Blue for player
    else:
        glColor3f(1.0, 0.0, 0.0)  # Red for enemy/boss
    
    quadric = gluNewQuadric()
    gluSphere(quadric, 0.3, 10, 10)
    glPopMatrix()

def draw_explosion(explosion):
    glPushMatrix()
    
    # Position the explosion
    glTranslatef(explosion['position'][0], 0, explosion['position'][2])
    
    # Calculate scale based on lifetime (grows then shrinks)
    scale = 1.0 + 1.5 * (1.0 - explosion['lifetime'] / 30.0)
    glScalef(scale, scale, scale)
    
    # Adjust color brightness based on lifetime
    brightness = explosion['lifetime'] / 30.0
    glColor3f(1.0, 0.5 * brightness, 0.0)
    
    # Draw explosion sphere
    glutSolidSphere(1.0, 16, 16)
    
    glPopMatrix()

def draw_portal():
    if not game_state.get('portal_active', False):
        return
        
    glPushMatrix()
    
    # Position the portal
    glTranslatef(game_state['portal_position'][0], TANK_RADIUS / 2, game_state['portal_position'][2])
    
    # Rotate for visual effect
    glRotatef(time.time() * 50 % 360, 0, 1, 0)
    
    # Use blue-green color
    portal_timer = game_state.get('portal_timer', 0)
    brightness = min(1.0, portal_timer / 20.0)
    glColor3f(0.0, brightness, brightness)
    
    # Draw a torus for the portal
    glutSolidTorus(0.2, PORTAL_RADIUS, 10, 10)
    
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
            
        if game_state['boss_active'] and check_tank_collision(pos, game_state['boss']['position']):
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

def draw_hud():
    draw_text(f"Player: {game_state['scores'][0]} Enemy: {game_state['scores'][1]}", 10, 580)
    draw_text(f"Player Health: {game_state['tanks'][0]['health']}", 10, 560)
    
    if game_state['boss_active']:
        draw_text(f"Boss Health: {game_state['boss']['health']}", 10, 540)
    else:
        draw_text(f"Enemy Health: {game_state['tanks'][1]['health']}", 10, 540)
    
    if game_state['powerup_speed_boost']:
        time_left = int(game_state['powerup_speed_end_time'] - time.time())
        draw_text(f"Speed Boost: {time_left}s", 10, 520)
    
    if not game_state['boss_active']:
        draw_text(f"Enemy Mode: {game_state['enemy_mode']}", 10, 500)
    
    if game_state['auto_teleport_enabled']:
        time_to_teleport = 30 - int(time.time() - game_state['last_auto_teleport_time'])
        draw_text(f"Auto-Teleport: ON (Next in {time_to_teleport}s)", 10, 480)
    
    if game_state.get('game_over', False):
        winner = game_state.get('winner', None)
        if winner == 0:
            text = "PLAYER WINS! Press R to restart"
        else:
            text = "ENEMY WINS! Press R to restart"
        draw_text(text, 250, 300)

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
    # Fixed rendering order (no depth sorting)
    draw_arena()
    
    for obs in obstacles:
        draw_obstacle(obs)
    
    draw_powerup()
    draw_portal()
    
    for tank in game_state['tanks']:
        if tank['health'] > 0:
            draw_tank(tank)
    
    if game_state['boss_active'] and game_state['boss']['health'] > 0:
        draw_tank(game_state['boss'], is_boss=True)
    
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
        x = (2 * (tank_idx % 2) - 1) * (GRID_LENGTH - 10) * (0.3 + 0.7 * random.random())
        z = (2 * (tank_idx // 2) - 1) * (GRID_LENGTH - 10) * (0.3 + 0.7 * random.random())
        pos = (x, 0, z)
        
        valid_position = not check_obstacle_collision(pos)
        
        for other_idx, other_tank in enumerate(game_state['tanks']):
            if other_idx != tank_idx and check_tank_collision(pos, other_tank['position']):
                valid_position = False
                break
                
        if game_state['boss_active'] and check_tank_collision(pos, game_state['boss']['position']):
            valid_position = False
    
    game_state['tanks'][tank_idx]['position'] = pos
    game_state['tanks'][tank_idx]['rotation'] = 0 if tank_idx == 0 else 180

def spawn_boss():
    game_state['boss'] = {
        'position': (0, 0, 30),
        'rotation': 180,
        'health': BOSS_HEALTH
    }
    game_state['boss_active'] = True
    game_state['tanks'][1]['health'] = 0  # Remove regular enemy

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
    game_state['boss_active'] = False
    game_state['boss'] = None
    game_state['enemy_fire_rate'] = 0.01
    game_state['boss_fire_rate'] = 0.05
    game_state['auto_teleport_enabled'] = False
    game_state['last_auto_teleport_time'] = time.time()
    game_state['portal_active'] = False
    
    global obstacles
    obstacles = [
        {'type': 'cube', 'x': 10, 'z': 10, 'size': 3, 'dynamic': False},
        {'type': 'cube', 'x': -15, 'z': -15, 'size': 4, 'dynamic': True, 'speed': 0.3, 'direction': (1, 0), 'direction_change_time': time.time()},
        {'type': 'cube', 'x': 20, 'z': -10, 'size': 5, 'dynamic': False, 'visible': True, 'toggle_time': time.time(), 'next_toggle': random.uniform(5, 10)},
        {'type': 'barrier', 'x': -20, 'z': 15, 'size': 3, 'dynamic': True, 'rotation': 0, 'rotation_speed': 30},
        {'type': 'cube', 'x': 0, 'z': -25, 'size': 4, 'dynamic': True, 'speed': 0.3, 'direction': (0, 1), 'direction_change_time': time.time()}
    ]

def check_win_condition():
    if game_state.get('game_over', False):
        return
        
    if game_state['scores'][0] >= 2 and not game_state['boss_active']:
        spawn_boss()
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
                    
                    game_state['tanks'][tank_idx]['health'] -= 20
                    
                    if game_state['tanks'][tank_idx]['health'] <= 0:
                        game_state['scores'][proj['owner']] += 1
                        respawn_tank(tank_idx)
                    
                    break
        
        if game_state['boss_active'] and proj['owner'] == 0:
            boss = game_state['boss']
            if check_projectile_tank_collision(pos, boss['position']):
                projectiles_to_remove.append(i)
                create_explosion(pos)
                
                boss['health'] -= 20
                
                if boss['health'] <= 0:
                    game_state['game_over'] = True
                    game_state['winner'] = 0
    
    for i in sorted(projectiles_to_remove, reverse=True):
        if i < len(game_state['projectiles']):
            game_state['projectiles'].pop(i)

def update_enemy_ai():
    if game_state['game_over'] or game_state['boss_active']:
        return
        
    enemy = game_state['tanks'][1]
    player = game_state['tanks'][0]
    
    dx = player['position'][0] - enemy['position'][0]
    dz = player['position'][2] - enemy['position'][2]
    
    target_angle = math.degrees(math.atan2(dx, dz)) % 360
    current_angle = enemy['rotation']
    angle_diff = (target_angle - current_angle + 180) % 360 - 180
    
    distance = math.sqrt(dx**2 + dz**2)
    
    if game_state['enemy_mode'] == 'chasing':
        if abs(angle_diff) > 5:
            if angle_diff > 0:
                enemy['rotation'] = (current_angle + 2) % 360
            else:
                enemy['rotation'] = (current_angle - 2) % 360
        
        if distance > 20 and abs(angle_diff) < 10:
            pos = list(enemy['position'])
            rot = enemy['rotation']
            pos[0] += TANK_SPEED * 0.1 * math.sin(math.radians(rot))
            pos[2] += TANK_SPEED * 0.1 * math.cos(math.radians(rot))
            
            if check_boundary_collision(pos) or check_obstacle_collision(pos):
                game_state['enemy_mode'] = 'avoiding'
                game_state['avoiding_frames'] = 20
                game_state['avoiding_direction'] = random.choice([1, -1])
            else:
                enemy['position'] = tuple(pos)
        
        if abs(angle_diff) < 5 and random.random() < game_state['enemy_fire_rate']:
            direction = (math.sin(math.radians(enemy['rotation'])), 0, math.cos(math.radians(enemy['rotation'])))
            projectile = {'position': enemy['position'], 'direction': direction, 'owner': 1}
            game_state['projectiles'].append(projectile)
    
    elif game_state['enemy_mode'] == 'avoiding':
        if game_state['avoiding_frames'] > 0:
            enemy['rotation'] = (enemy['rotation'] + 2 * game_state['avoiding_direction']) % 360
            game_state['avoiding_frames'] -= 1
            
            if game_state['avoiding_frames'] % 5 == 0:
                pos = list(enemy['position'])
                rot = enemy['rotation']
                pos[0] += TANK_SPEED * 0.1 * math.sin(math.radians(rot))
                pos[2] += TANK_SPEED * 0.1 * math.cos(math.radians(rot))
                
                if not check_boundary_collision(pos) and not check_obstacle_collision(pos):
                    enemy['position'] = tuple(pos)
        else:
            game_state['enemy_mode'] = 'chasing'

def update_boss_ai():
    if not game_state['boss_active']:
        return
        
    boss = game_state['boss']
    player = game_state['tanks'][0]
    
    dx = player['position'][0] - boss['position'][0]
    dz = player['position'][2] - boss['position'][2]
    
    target_angle = math.degrees(math.atan2(dx, dz)) % 360
    current_angle = boss['rotation']
    angle_diff = (target_angle - current_angle + 180) % 360 - 180
    
    distance = math.sqrt(dx**2 + dz**2)
    
    # Rotate towards player faster than regular enemy
    if abs(angle_diff) > 5:
        boss['rotation'] = (current_angle + 4 * (1 if angle_diff > 0 else -1)) % 360
    
    # Move towards player if far away
    if distance > 15 and abs(angle_diff) < 15:
        pos = list(boss['position'])
        rot = boss['rotation']
        pos[0] += BOSS_SPEED * 0.25 * math.sin(math.radians(rot))
        pos[2] += BOSS_SPEED * 0.25 * math.cos(math.radians(rot))
        
        if not (check_boundary_collision(pos) or check_obstacle_collision(pos)):
            boss['position'] = tuple(pos)
    
    # Fire multiple projectiles when facing player
    if abs(angle_diff) < 10 and random.random() < game_state['boss_fire_rate']:
        direction = (math.sin(math.radians(boss['rotation'])), 0, math.cos(math.radians(boss['rotation'])))
        
        # Create two projectiles with slightly different angles
        projectile1 = {'position': boss['position'], 'direction': direction, 'owner': 1}
        projectile2 = {
            'position': boss['position'], 
            'direction': (
                math.sin(math.radians(boss['rotation'] + 10)), 
                0, 
                math.cos(math.radians(boss['rotation'] + 10))
            ), 
            'owner': 1
        }
        
        game_state['projectiles'].extend([projectile1, projectile2])

def update_dynamic_obstacles():
    for obs in obstacles:
        if obs.get('dynamic'):
            if obs['type'] == 'cube':
                # Update position based on direction and speed
                pos = [obs['x'], obs['z']]
                pos[0] += obs['speed'] * obs['direction'][0]
                pos[1] += obs['speed'] * obs['direction'][1]
                
                # Bounce at boundaries
                if abs(pos[0]) > GRID_LENGTH - obs['size']/2 or abs(pos[1]) > GRID_LENGTH - obs['size']/2:
                    obs['direction'] = (-obs['direction'][0], -obs['direction'][1])
                
                # Periodically change direction
                if time.time() - obs.get('direction_change_time', time.time()) > 5:
                    angle = random.uniform(0, 360)
                    obs['direction'] = (math.sin(math.radians(angle)), math.cos(math.radians(angle)))
                    obs['direction_change_time'] = time.time()
                
                obs['x'], obs['z'] = pos[0], pos[1]
            
            elif obs['type'] == 'barrier':
                # Update rotation for rotating barriers
                obs['rotation'] = (obs['rotation'] + obs['rotation_speed']) % 360
        
        # Handle visibility toggling
        if 'toggle_time' in obs and 'next_toggle' in obs:
            if obs.get('visible', True) and time.time() - obs['toggle_time'] > obs['next_toggle']:
                obs['visible'] = False
                obs['toggle_time'] = time.time()
                obs['next_toggle'] = random.uniform(3, 7)
            elif not obs.get('visible', True) and time.time() - obs['toggle_time'] > obs['next_toggle']:
                obs['visible'] = True
                obs['toggle_time'] = time.time()
                obs['next_toggle'] = random.uniform(5, 10)

def teleport_player():
    # Create a portal effect
    game_state['portal_active'] = True
    game_state['portal_timer'] = 30  # Duration of portal effect
    
    attempts = 0
    while attempts < 100:  # Limit attempts to prevent infinite loop
        x = random.uniform(-GRID_LENGTH + 5, GRID_LENGTH - 5)
        z = random.uniform(-GRID_LENGTH + 5, GRID_LENGTH - 5)
        pos = (x, 0, z)
        
        valid = not check_boundary_collision(pos) and not check_obstacle_collision(pos)
        
        if valid:
            # Check for collisions with tanks
            if check_tank_collision(pos, game_state['tanks'][1]['position']):
                valid = False
                
            if game_state['boss_active'] and check_tank_collision(pos, game_state['boss']['position']):
                valid = False
            
            if valid:
                # Set portal position for visual effect
                game_state['portal_position'] = pos
                # Teleport player
                game_state['tanks'][0]['position'] = pos
                break
        
        attempts += 1
    
    glutPostRedisplay()

def update_portal_effect():
    if game_state['portal_active']:
        game_state['portal_timer'] -= 1
        if game_state['portal_timer'] <= 0:
            game_state['portal_active'] = False

def keyboardListener(key, x, y):
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
    elif key == b'q':
        # Toggle auto-teleport
        game_state['auto_teleport_enabled'] = not game_state['auto_teleport_enabled']
        if game_state['auto_teleport_enabled']:
            game_state['last_auto_teleport_time'] = time.time()
            teleport_player()
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
    update_projectiles()
    update_explosions()
    update_powerup()
    check_powerup_collection()
    update_enemy_ai()
    update_boss_ai()
    update_dynamic_obstacles()
    update_portal_effect()
    check_win_condition()
    
    # Handle auto-teleport
    if game_state['auto_teleport_enabled'] and time.time() - game_state['last_auto_teleport_time'] >= 30:
        teleport_player()
        game_state['last_auto_teleport_time'] = time.time()
    
    glutPostRedisplay()

def init():
    glClearColor(0.0, 0.0, 0.0, 0.0)
    # No depth testing, lighting, or blending

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

if __name__ == "__main__":
    main()
