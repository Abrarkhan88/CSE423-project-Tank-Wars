import math
import time
import random
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

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
    'avoiding_direction': 0
}

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

obstacles = [
    {'type': 'cube', 'x': 10, 'z': 10, 'size': 3},
    {'type': 'cube', 'x': -15, 'z': -15, 'size': 4},
    {'type': 'cube', 'x': 20, 'z': -10, 'size': 5},
    {'type': 'cube', 'x': -20, 'z': 15, 'size': 3},
    {'type': 'cube', 'x': 0, 'z': -25, 'size': 4}
]


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
            game_state['tans'][0]['position'] = tuple(pos)
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

# def mouseMotionListener(x, y):
#     pass

# Module 2: Projectile System & Collision
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
    
    for i in sorted(projectiles_to_remove, reverse=True):
        if i < len(game_state['projectiles']):
            game_state['projectiles'].pop(i)

def check_projectile_tank_collision(proj_pos, tank_pos):
    distance = math.sqrt((proj_pos[0] - tank_pos[0])**2 + (proj_pos[2] - tank_pos[2])**2)
    return distance < TANK_RADIUS

def check_tank_collision(tank1_pos, tank2_pos):
    distance = math.sqrt((tank1_pos[0] - tank2_pos[0])**2 + (tank1_pos[2] - tank2_pos[2])**2)
    return distance < TANK_RADIUS * 2

def check_boundary_collision(pos):
    return abs(pos[0]) > GRID_LENGTH or abs(pos[2]) > GRID_LENGTH

def check_obstacle_collision(pos):
    for obs in obstacles:
        distance = math.sqrt((pos[0] - obs['x'])**2 + (pos[2] - obs['z'])**2)
        if distance < (obs['size'] / 2 + TANK_RADIUS):
            return True
    return False

def create_explosion(position):
    explosion = {
        'position': position,
        'scale': 0.1,
        'lifetime': 30 
    }
    game_state['explosions'].append(explosion)

def update_explosions():
    explosions_to_remove = []
    
    for i, explosion in enumerate(game_state['explosions']):
        explosion['lifetime'] -= 1
        explosion['scale'] = 2.0 * (1 - explosion['lifetime'] / 30)
        
        if explosion['lifetime'] <= 0:
            explosions_to_remove.append(i)
    
    for i in sorted(explosions_to_remove, reverse=True):
        if i < len(game_state['explosions']):
            game_state['explosions'].pop(i)

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

def check_win_condition():
    if game_state.get('game_over', False):
        return

    if game_state['scores'][0] >= 5:
        game_state['game_over'] = True
        game_state['winner'] = 0
    elif game_state['scores'][1] >= 5:
        game_state['game_over'] = True
        game_state['winner'] = 1

def update_enemy_ai():
    if game_state['game_over']:
        return
        
    # Simple AI for enemy tank
    enemy = game_state['tanks'][1]  
    player = game_state['tanks'][0]  
    
    if 'enemy_mode' not in game_state:
        game_state['enemy_mode'] = 'chasing'
    if 'avoiding_frames' not in game_state:
        game_state['avoiding_frames'] = 0
    if 'avoiding_direction' not in game_state:
        game_state['avoiding_direction'] = 0  # 1 for left, -1 for right
    
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
            pos[0] += TANK_SPEED * 0.5 * math.sin(math.radians(rot))
            pos[2] += TANK_SPEED * 0.5 * math.cos(math.radians(rot))
            
            if check_boundary_collision(pos) or check_obstacle_collision(pos):
                game_state['enemy_mode'] = 'avoiding'
                game_state['avoiding_frames'] = 20
                game_state['avoiding_direction'] = random.choice([1, -1])  # Randomly choose left or right
            else:
                enemy['position'] = tuple(pos)
        
        if abs(angle_diff) < 5 and random.random() < 0.02:
            direction = (math.sin(math.radians(enemy['rotation'])), 
                         0, 
                         math.cos(math.radians(enemy['rotation'])))
            
            projectile = {
                'position': enemy['position'],
                'direction': direction,
                'owner': 1  # Enemy's projectile
            }
            
            game_state['projectiles'].append(projectile)
    
    elif game_state['enemy_mode'] == 'avoiding':
        if game_state['avoiding_frames'] > 0:
            enemy['rotation'] = (enemy['rotation'] + 2 * game_state['avoiding_direction']) % 360
            game_state['avoiding_frames'] -= 1
            
            if game_state['avoiding_frames'] % 5 == 0:
                pos = list(enemy['position'])
                rot = enemy['rotation']
                pos[0] += TANK_SPEED * 0.5 * math.sin(math.radians(rot))
                pos[2] += TANK_SPEED * 0.5 * math.cos(math.radians(rot))
                
                if not check_boundary_collision(pos) and not check_obstacle_collision(pos):
                    enemy['position'] = tuple(pos)
        else:
            game_state['enemy_mode'] = 'chasing'

# Powerup system
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
        # Collect powerup
        #health refill or speed boost
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
        # Remove powerup after 15 seconds if not collected
        if time.time() - game_state['powerup']['spawn_time'] > 15:
            game_state['powerup'] = None
            game_state['powerup_spawn_time'] = time.time()

    # Remove speed boost if expired
    if game_state['powerup_speed_boost'] and time.time() > game_state['powerup_speed_end_time']:
        game_state['powerup_speed_boost'] = False

# Drawing functions
def draw_tank(tank):
    glPushMatrix()
    
    glTranslatef(tank['position'][0], 0, tank['position'][2])
    
    glRotatef(tank['rotation'], 0, 1, 0)
    
    if tank == game_state['tanks'][0]:
        glColor3f(0.2, 0.2, 0.8)  # Blue for player
    else:
        glColor3f(0.8, 0.2, 0.2)  # Red for enemy
    
    glutSolidCube(TANK_RADIUS * 2)
    
    glColor3f(0.3, 0.3, 0.3)
    glTranslatef(0, TANK_RADIUS, 0)
    glutSolidCube(TANK_RADIUS)
    
    glTranslatef(0, 0, TANK_RADIUS)
    glRotatef(90, 1, 0, 0)
    quadric = gluNewQuadric()
    gluCylinder(quadric, TANK_RADIUS / 3, TANK_RADIUS / 3, TANK_RADIUS * 2, 10, 10)
    
    glPopMatrix()

    glPushMatrix()
    
    glTranslatef(tank['position'][0], 0, tank['position'][2])
    
    glRotatef(-tank['rotation'], 0, 1, 0)
    
    glTranslatef(0, TANK_RADIUS * 2.5, 0)
    
    #health bar color (green to red)
    health_ratio = max(0, min(1, tank['health'] / 100))
    red = 1.0 - health_ratio
    green = health_ratio
    glColor3f(red, green, 0.0)
    
    #horizontal rectangle as health bar
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
        glColor3f(1.0, 0.0, 0.0)  # Red for enemy
    
    quadric = gluNewQuadric()
    gluSphere(quadric, 0.3, 10, 10)
    
    glPopMatrix()

def draw_explosion(explosion):
    glPushMatrix()
    
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    glTranslatef(explosion['position'][0], 0, explosion['position'][2])
    
    alpha = max(0.0, explosion['lifetime'] / 30.0)
    
    glColor4f(1.0, 0.5, 0.0, alpha)
    
    scale = explosion['scale'] * 1.5
    glutSolidSphere(scale, 10, 10)
    
    glDisable(GL_BLEND)
    
    glPopMatrix()

def draw_obstacle(obstacle):
    glPushMatrix()
    
    glTranslatef(obstacle['x'], obstacle['size'] / 2, obstacle['z'])
    
    glColor3f(0.5, 0.5, 0.5)
    glutSolidCube(obstacle['size'])
    
    glPopMatrix()

def draw_powerup():
    if game_state['powerup'] is None:
        return
    
    glPushMatrix()
    
    #powerup rotate and float
    glTranslatef(game_state['powerup']['position'][0], 
                 TANK_RADIUS / 2 + 0.5 * math.sin(time.time() * 2), 
                 game_state['powerup']['position'][2])
    glRotatef(time.time() * 50 % 360, 0, 1, 0)
    
    glColor3f(1.0, 1.0, 0.0)
    glutSolidCube(1.0)
    
    glPopMatrix()

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
    
    #boundary walls
    glColor3f(0.7, 0.7, 0.7)
    
    glPushMatrix()
    glTranslatef(0, 5, -GRID_LENGTH)
    glScalef(2 * GRID_LENGTH, 10, 1)
    glutSolidCube(1)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(0, 5, GRID_LENGTH)
    glScalef(2 * GRID_LENGTH, 10, 1)
    glutSolidCube(1)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(GRID_LENGTH, 5, 0)
    glScalef(1, 10, 2 * GRID_LENGTH)
    glutSolidCube(1)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(-GRID_LENGTH, 5, 0)
    glScalef(1, 10, 2 * GRID_LENGTH)
    glutSolidCube(1)
    glPopMatrix()
    
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
    #scores
    draw_text(f"Player: {game_state['scores'][0]}  Enemy: {game_state['scores'][1]}", 10, 580)
    
    #health bars
    draw_text(f"Player Health: {game_state['tanks'][0]['health']}", 10, 560)
    draw_text(f"Enemy Health: {game_state['tanks'][1]['health']}", 10, 540)
    
    if game_state['powerup_speed_boost']:
        time_left = int(game_state['powerup_speed_end_time'] - time.time())
        draw_text(f"Speed Boost: {time_left}s", 10, 520)
    
    draw_text(f"Enemy Mode: {game_state['enemy_mode']}", 10, 500)
    
    if game_state.get('game_over', False):
        winner = game_state.get('winner', None)
        if winner is not None:
            text = f"PLAYER {winner + 1} WINS! Press R to restart"
            # Draw large centered text
            draw_text(text, 250, 300)

def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, 800/600, 0.1, 1000)
    
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    
    if game_state['camera_mode']:
        #Third-person camera
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
        # Top-down view
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
    
    for proj in game_state['projectiles']:
        draw_projectile(proj)
    
    for explosion in game_state['explosions']:
        draw_explosion(explosion)
    
    draw_hud()

def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
    setupCamera()
    
    draw_shapes()
    
    glutSwapBuffers()

def idle():
    update_projectiles()
    
    update_explosions()
    
    update_powerup()
    check_powerup_collection()
    
    update_enemy_ai()
    
    check_win_condition()
    
    glutPostRedisplay()

def init():
    glClearColor(0.0, 0.0, 0.0, 0.0)
    
    glEnable(GL_DEPTH_TEST)
    
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    
    light_position = [0, 100, 0, 1]
    glLightfv(GL_LIGHT0, GL_POSITION, light_position)
    
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT, GL_AMBIENT_AND_DIFFUSE)

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
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
