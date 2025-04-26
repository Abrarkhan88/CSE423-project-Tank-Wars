import math
import time
import random
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

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
    'winner': None
}
obstacles = [
    {'type': 'cube', 'x': 10, 'z': 10, 'size': 3},
    {'type': 'cube', 'x': -15, 'z': -15, 'size': 4},
    {'type': 'cube', 'x': 20, 'z': -10, 'size': 5},
    {'type': 'cube', 'x': -20, 'z': 15, 'size': 3},
    {'type': 'cube', 'x': 0, 'z': -25, 'size': 4}
]

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

def draw_obstacle(obstacle):
    glPushMatrix()
    glTranslatef(obstacle['x'], obstacle['size'] / 2, obstacle['z'])
    glColor3f(0.5, 0.5, 0.5)
    glutSolidCube(obstacle['size'])
    glPopMatrix()

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
            0, 80, 0,    # Camera position
            0, 0, 0,      # Look at center
            0, 0, -1      # Up vector
        )

def draw_shapes():
    draw_arena()
    for obs in obstacles:
        draw_obstacle(obs)

def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    setupCamera()
    draw_shapes()
    glutSwapBuffers()

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
    glutCreateWindow(b"Tank Wars")
    init()
    glutDisplayFunc(display)
    glutMainLoop()

if __name__ == "__main__":
    main()
