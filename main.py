from tkinter import *
import random
import time
import math
import os
import sys
import atexit


# Detecting if sound is available. Sound is only supported on Windows
# as WinSound is a Windows-only library.
def detect_sound():
    global SOUND
    SOUND = False
    if os.name == 'nt':
        SOUND = True
        import subprocess
        import winsound


# Since the audio managers spawn separate threads, a special exit
# handler is required. This handler is registered with both Tk and
# atexit to ensure that it runs before exiting.
SOUND = False
@atexit.register
def kill_music():
    try:
        root.destroy()
    except:
        pass
    if SOUND:
        [mngr.thread.kill() for mngr in AUDIO_CHANNELS]


# const params
def init_const_params():
    global GRAVITY, FPS, WINDOW_DIMS, NET_HEIGHT, MESH_HEIGHT, DRAG_COEFFICIENT, ERROR_TOLERANCE, H, DELAY
    # Gravity, units of pixels per second squared.
    GRAVITY = 3000

    # Max FPS, may run slower if the game lags.
    FPS = 60

    # Tk window dimensions, the program is designed to dynamically
    # place objects based on the dims, however the art will not be
    # resized.
    WINDOW_DIMS = (1280, 960)

    # Height of the net in pixels.
    NET_HEIGHT = 150

    # Height of the mesh in pixels.
    MESH_HEIGHT = 75

    # Drag experienced by the birdie. Velocity is updated by multiplying
    # the velocity by the drag coefficient every frame.
    DRAG_COEFFICIENT = 0.97

    # Error tolerance when simulating. This can be increased if the game
    # lags when called (for example during smashes).
    ERROR_TOLERANCE = 0.1

    # The delta used when simulating. This can be increased if the game
    # lags when called.
    H = 1

    # Minimum delay between frames (in ms), can be used to slow the game down.
    DELAY = 0


# Derived parameters.
def init_derived_params():
    global dt
    dt = 1 / FPS


# Other global parameters.
def init_other_globals():
    global OBJECTS, KEY_PRESSES, STAR_PLATINUM_RACKETS, WAMUU_RACKETS, ZA_HANDO_RACKETS, GAME_BIRDIE, NUMBERS
    OBJECTS = []
    KEY_PRESSES = []
    STAR_PLATINUM_RACKETS = {}
    WAMUU_RACKETS = {}
    ZA_HANDO_RACKETS = {}
    GAME_BIRDIE = None
    NUMBERS = []


# Initialize various meshes used by the game.
def init_meshes():
    global post_verts, play, ok, lock_in
    post_verts = [(WINDOW_DIMS[0] / 2 - 10, WINDOW_DIMS[1] - 5, WINDOW_DIMS[0] / 2 - 10, WINDOW_DIMS[1],
                   WINDOW_DIMS[0] / 2 + 10, WINDOW_DIMS[1], WINDOW_DIMS[0] / 2 + 10, WINDOW_DIMS[1] - 5, \
                   WINDOW_DIMS[0] / 2 + 2, WINDOW_DIMS[1] - 5, WINDOW_DIMS[0] / 2 + 2, WINDOW_DIMS[1] - NET_HEIGHT,
                   WINDOW_DIMS[0] / 2 - 2, WINDOW_DIMS[1] - NET_HEIGHT, WINDOW_DIMS[0] / 2 - 2, WINDOW_DIMS[1] - 5)]

    # Button corners (used to check if mouse click is on the button).
    play = [[355, 637], [910, 795]]
    ok = [[381, 702], [900, 870]]
    lock_in = [[291, 718], [988, 883]]


detect_sound()
init_const_params()
init_derived_params()
init_other_globals()
init_meshes()
# Tkinter initialization.
root = Tk()
root.geometry(str(WINDOW_DIMS[0]) + "x" + str(WINDOW_DIMS[1]) + "+0+0")
s = Canvas(root, width=WINDOW_DIMS[0], height=WINDOW_DIMS[1])
s.pack()
s.update()

if SOUND:
    # A custom class I created to handle concurrent audio since winsound only
    # lets one audio track run at once. This class works by opening the play_audio
    # script I made in a separate process and sending it commands to play certain
    # tracks.
    class ConcurrentAudioManager:
        def __init__(self):
            self.thread = subprocess.Popen([sys.executable, "play_audio.py"], stdin=subprocess.PIPE,
                                           stdout=subprocess.PIPE,
                                           bufsize=0)

        def play(self, sound, loop=False):
            if loop:
                cmd = "loop|" + sound + "\n"
            else:
                cmd = "play|" + sound + "\n"
            self.thread.stdin.write(cmd.encode())


# Base object class.
class Obj:
    xVel = 0.001
    yVel = 0
    x = None
    y = None
    theta = None
    g = GRAVITY
    tk_obj = None

    def __init__(self, _x, _y, _theta, _mass, _inertia, _translation_fixed, _rotation_fixed):
        self.x = _x
        self.y = _y
        self.theta = _theta
        self.mass = _mass
        self.inertia = _inertia
        self.translation_fixed = _translation_fixed
        self.rotation_fixed = _rotation_fixed


# Function to load all of the birdie images. Since PIL is
# not installed on the school computers, the asset_creator
# script was ran to create images of the assets in five
# degree increments.
def load_birdie_assets():
    imgs = {}
    for a in range(0, 361, 5):
        imgs[a] = PhotoImage(file="assets/birdies/birdie-" + str(a) + ".gif")

    return imgs


# Function to round an integer to the nearest multiple of 5.
def r(x):
    return round(x / 5) * 5

# Birdie inherits from the base object class.
class Birdie(Obj):
    # Birdie vars/consts.
    r = 10
    netCollided = False
    images = load_birdie_assets()
    lastx = 0
    lasty = 0

    # tick function. Program is structured so that each object
    # has a tick function which is called once every frame.
    def tick(self):
        global LEFT_SCORE, RIGHT_SCORE, PAUSE
        self.erase()

        # Update position and velocities.
        self.yVel += self.g * dt
        self.ang = math.atan2(self.yVel, self.xVel)
        self.lastx = self.x
        self.lasty = self.y
        self.mag = math.hypot(self.xVel, self.yVel)
        self.mag *= DRAG_COEFFICIENT
        self.xVel = self.mag * math.cos(self.ang)
        self.yVel = self.mag * math.sin(self.ang)
        self.x += self.xVel * dt
        self.y += self.yVel * dt
        self.theta = math.degrees(math.atan2(-(self.y - self.lasty), self.x - self.lastx))

        # Bounds checking.
        if self.x + self.r > WINDOW_DIMS[0]:
            self.x = WINDOW_DIMS[0] - self.r
            self.xVel *= -0.4
        elif self.x - self.r < 0:
            self.x = self.r
            self.xVel *= -0.4

        # Check if point was scored.
        if self.y + self.r > WINDOW_DIMS[1]:
            if self.x < WINDOW_DIMS[0] / 2:
                RIGHT_SCORE += 1
                self.x = 3 * WINDOW_DIMS[0] / 4
                self.y = WINDOW_DIMS[1] / 4
            else:
                self.x = WINDOW_DIMS[0] / 4
                self.y = WINDOW_DIMS[1] / 4
                LEFT_SCORE += 1

            # Update the score countner.
            update_score_counter()

            # Pause game after point is scored.
            PAUSE = True

            # Reset velocities.
            self.xVel = 0
            self.yVel = 0

        # Otherwise if the birdie it the ceiling,
        # make the birdie bounce off.
        elif self.y - self.r < 0:
            self.y = self.r
            self.yVel *= -0.4

        # Net collisions detection.
        if sim(self.xVel, self.yVel, 20, self.x, self.y, self.r, True)[2]:
            self.xVel *= -0.2

        # Render bridie image.
        self.draw()

    def draw(self):
        # Creating the birdie image based on the angle.
        self.tk_obj = s.create_image(self.x, self.y, image=self.images[r(self.theta) % 360])

    def erase(self):
        s.delete(self.tk_obj)


# StarPlatinum character object, inherits from the object base class.
class StarPlatinum(Obj):
    # Star Platinum constants.
    jump = 1100 / dt
    y_clip = 45
    x_clip = 27
    arm_length = 80
    visual_arm_offset_x = 15
    visual_arm_offset_y = -10
    ms = 1100
    power = 2.5 / dt
    smash_power = 3
    accuracy = 100
    reach = 45
    hit = False
    side = None
    keys = None
    imgs = []
    racket_obj = None
    r_angle = 0
    anim_speed = 20
    start_angles = (180, 180, 100, -100)  # right_over, left_over, right_under, left_under
    end_angles = (360, 0, -40, 40)
    overhand = None
    idle = True
    running_delay = 15
    running_ctr = 0
    num_frames = 1
    index = None
    sounds = ["reg_hit_new", "ora_new"]

    def set_side(self, side):
        self.side = side
        # very interesting note:    without this line, python gives this variable the same memory pointer to both StarPlatinum objects,
        #                           you can try commening out the following line and uncomment the print(id(self.imgs)) line to see it
        #                           in action. This will also break the code too, this is an issue with the cpython interpreter.
        self.imgs = []
        if side == 'left':
            self.keys = ['w', 'd', 'a', 's']
            self.sign = 1
            self.index = 1
        else:
            self.keys = ['Up', 'Right', 'Left', 'Down']
            self.sign = -1
            self.index = 2

        for i in range(self.num_frames):
            self.imgs.append(PhotoImage(file="assets/star-platinum-" + str(i) + "-" + self.side + ".gif"))

        # print(id(self.imgs))

    def tick(self):
        self.erase()

        if self.idle is False:
            if self.overhand:
                if self.side == 'right':
                    if self.r_angle >= self.end_angles[0]:
                        self.idle = True
                    else:
                        self.r_angle += self.anim_speed
                else:
                    if self.r_angle <= self.end_angles[1]:
                        self.idle = True
                    else:
                        self.r_angle -= self.anim_speed
            else:
                if self.side == 'right':
                    if self.r_angle <= self.end_angles[2]:
                        self.idle = True
                    else:
                        self.r_angle -= self.anim_speed
                else:
                    if self.r_angle >= self.end_angles[3]:
                        self.idle = True
                    else:
                        self.r_angle += self.anim_speed
        else:
            self.r_angle = 0

        if self.keys[0] in KEY_PRESSES and abs(self.y + self.y_clip - WINDOW_DIMS[1]) < 5:
            self.yVel -= self.jump * dt

        if self.keys[1] in KEY_PRESSES:
            # self.x += self.ms * dt
            self.xVel = self.ms
        elif self.keys[2] in KEY_PRESSES:
            # self.x -= self.ms * dt
            self.xVel = -self.ms
        else:
            self.xVel = 0

        if self.keys[3] in KEY_PRESSES:
            self.yVel += self.jump / 10 * dt

        self.yVel += self.g * dt

        self.x += self.xVel * dt
        self.y += self.yVel * dt

        if self.side == 'left':
            if self.x + self.x_clip > WINDOW_DIMS[0] / 2:
                self.x = WINDOW_DIMS[0] / 2 - self.x_clip
                self.xVel = 0
            elif self.x - self.x_clip < 0:
                self.x = self.x_clip
                self.xVel = 0
        else:
            if self.x + self.x_clip > WINDOW_DIMS[0]:
                self.x = WINDOW_DIMS[0] - self.x_clip
                self.xVel = 0
            elif self.x - self.x_clip < WINDOW_DIMS[0] / 2:
                self.x = WINDOW_DIMS[0] / 2 + self.x_clip
                self.xVel = 0

        if self.y + self.y_clip > WINDOW_DIMS[1]:
            self.y = WINDOW_DIMS[1] - self.y_clip
            self.yVel = 0
        elif self.y + self.y_clip < 0:
            self.y = self.y_clip
            self.yVel = 0

        self.check_ball_hit()
        self.draw()

    def draw(self):
        self.running_ctr += 1
        self.running_ctr %= self.running_delay * self.num_frames

        ra = math.radians(self.r_angle)
        self.tk_obj = s.create_image(self.x, self.y, image=self.imgs[self.running_ctr // self.running_delay])
        if self.side == 'left':
            self.racket_obj = s.create_image(self.x - self.visual_arm_offset_x, self.y + self.visual_arm_offset_y,
                                             image=STAR_PLATINUM_RACKETS[str(self.r_angle % 360) + "-" + self.side])
        else:
            self.racket_obj = s.create_image(self.x + self.visual_arm_offset_x, self.y + self.visual_arm_offset_y,
                                             image=STAR_PLATINUM_RACKETS[str(self.r_angle % 360) + "-" + self.side])

    def erase(self):
        s.delete(self.tk_obj, self.racket_obj)

    def check_ball_hit(self):
        if dist_sq(GAME_BIRDIE.x, GAME_BIRDIE.y, self.x, self.y) < \
                (math.sqrt(
                    dist_sq(0, 0, self.x_clip, self.y_clip)) + GAME_BIRDIE.r + self.reach) ** 2 and self.hit is False \
                and (GAME_BIRDIE.x > WINDOW_DIMS[0] / 2 - 4 or self.side == 'left') and (
                GAME_BIRDIE.x < WINDOW_DIMS[0] / 2 + 4 or self.side == 'right') \
                and (
                GAME_BIRDIE.x < self.x - self.x_clip or self.side == 'left' or GAME_BIRDIE.y < self.y + self.y_clip / 1.5) and (
                GAME_BIRDIE.x > self.x + self.x_clip or self.side == 'right' or GAME_BIRDIE.y < self.y + self.y_clip / 1.5):
            self.idle = False

            if GAME_BIRDIE.y - 30 > self.y:
                self.overhand = False
            else:
                self.overhand = True

            if self.side == 'right':
                if self.overhand:
                    self.r_angle = self.start_angles[0] + self.anim_speed
                else:
                    self.r_angle = self.start_angles[2] - self.anim_speed
            else:
                if self.overhand:
                    self.r_angle = self.start_angles[1] - self.anim_speed
                else:
                    self.r_angle = self.start_angles[3] + self.anim_speed

            if self.y - self.reach < WINDOW_DIMS[1] - NET_HEIGHT - MESH_HEIGHT and GAME_BIRDIE.y < WINDOW_DIMS[
                1] - NET_HEIGHT - MESH_HEIGHT:
                if SOUND:
                    AUDIO_CHANNELS[self.index].play(self.sounds[1])
                power = 10 * self.power * self.smash_power + math.hypot(GAME_BIRDIE.xVel, GAME_BIRDIE.yVel) * 0.2
                GAME_BIRDIE.xVel, GAME_BIRDIE.yVel = calculate_smash_vel(GAME_BIRDIE.x, GAME_BIRDIE.y, power,
                                                                         GAME_BIRDIE.r,
                                                                         self.sign)

            else:
                if SOUND:
                    AUDIO_CHANNELS[self.index].play(self.sounds[0])

                height_above_net = random.uniform(0, self.accuracy)

                dist_y = abs(WINDOW_DIMS[1] - NET_HEIGHT - MESH_HEIGHT - self.y) + height_above_net
                dist_x = abs(WINDOW_DIMS[0] / 2 - self.x)

                GAME_BIRDIE.xVel, GAME_BIRDIE.yVel = calculate_hit_vel(
                    self.power + math.hypot(GAME_BIRDIE.xVel, GAME_BIRDIE.yVel) * 0.01, dist_y, dist_x, self.x, self.y,
                    GAME_BIRDIE.r)
                GAME_BIRDIE.xVel += self.xVel * self.sign / 3
            self.hit = time.perf_counter()

            # GAME_BIRDIE.xVel += self.xVel*0.9
            GAME_BIRDIE.xVel *= self.sign

        else:
            if time.perf_counter() - self.hit > 0.2:
                self.hit = False


class Wamuu(StarPlatinum):
    def set_side(self, side):
        self.side = side
        # very interesting note:    without this line, python gives this variable the same memory pointer to both StarPlatinum objects,
        #                           you can try commening out the following line and uncomment the print(id(self.imgs)) line to see it
        #                           in action. This will also break the code too, this is an issue with the cpython interpreter.
        self.imgs = []
        self.sounds = self.sounds.copy()
        self.sounds[1] = "hando_new"
        if side == 'left':
            self.keys = ['w', 'd', 'a', 's']
            self.sign = 1
            self.index = 1
        else:
            self.keys = ['Up', 'Right', 'Left', 'Down']
            self.sign = -1
            self.index = 2

        for i in range(self.num_frames):
            self.imgs.append(PhotoImage(file="assets/wamuu-" + str(i) + "-" + self.side + ".gif"))

    def draw(self):
        self.running_ctr += 1
        self.running_ctr %= self.running_delay * self.num_frames

        ra = math.radians(self.r_angle)
        self.tk_obj = s.create_image(self.x, self.y, image=self.imgs[self.running_ctr // self.running_delay])
        if self.side == 'left':
            self.racket_obj = s.create_image(self.x - self.visual_arm_offset_x, self.y + self.visual_arm_offset_y,
                                             image=WAMUU_RACKETS[str(self.r_angle % 360) + "-" + self.side])
        else:
            self.racket_obj = s.create_image(self.x + self.visual_arm_offset_x, self.y + self.visual_arm_offset_y,
                                             image=WAMUU_RACKETS[str(self.r_angle % 360) + "-" + self.side])

        # print(id(self.imgs))


class ZaHando(StarPlatinum):
    def set_side(self, side):
        self.side = side
        # very interesting note:    without this line, python gives this variable the same memory pointer to both StarPlatinum objects,
        #                           you can try commening out the following line and uncomment the print(id(self.imgs)) line to see it
        #                           in action. This will also break the code too, this is an issue with the cpython interpreter.
        self.imgs = []
        self.sounds = self.sounds.copy()
        self.sounds[1] = "hando_new"
        if side == 'left':
            self.keys = ['w', 'd', 'a', 's']
            self.sign = 1
            self.index = 1
        else:
            self.keys = ['Up', 'Right', 'Left', 'Down']
            self.sign = -1
            self.index = 2

        for i in range(self.num_frames):
            self.imgs.append(PhotoImage(file="assets/za-hando-" + str(i) + "-" + self.side + ".gif"))

    def draw(self):
        self.running_ctr += 1
        self.running_ctr %= self.running_delay * self.num_frames

        ra = math.radians(self.r_angle)
        self.tk_obj = s.create_image(self.x, self.y, image=self.imgs[self.running_ctr // self.running_delay])
        if self.side == 'left':
            self.racket_obj = s.create_image(self.x - self.visual_arm_offset_x, self.y + self.visual_arm_offset_y,
                                             image=ZA_HANDO_RACKETS[str(self.r_angle % 360) + "-" + self.side])
        else:
            self.racket_obj = s.create_image(self.x + self.visual_arm_offset_x, self.y + self.visual_arm_offset_y,
                                             image=ZA_HANDO_RACKETS[str(self.r_angle % 360) + "-" + self.side])

        # print(id(self.imgs))


# This function simulates the path a birdie would take given the inputs.
def sim(vx, vy, sx, _x, _y, r, return_on_collision_with_net, maxX=None):
    x = _x
    y = _y
    collides_with_net = False
    _dt = dt / 10
    ctr = 0
    if maxX:
        if x > maxX:
            direction = "left"
        else:
            direction = "right"
    # print()
    while abs(x - _x) < sx:

        if maxX:
            if (x > maxX and direction == "right") or (x < maxX and direction == "left"):
                return x, y, collides_with_net

        if ctr % 10 == 0:
            vx *= DRAG_COEFFICIENT
            vy *= DRAG_COEFFICIENT

        if x - r - 10 <= WINDOW_DIMS[0] / 2 <= x + r + 10:
            if y >= WINDOW_DIMS[1] - NET_HEIGHT - MESH_HEIGHT:
                vx *= -0.2
                collides_with_net = True

        if return_on_collision_with_net:
            if collides_with_net:
                return x, y, True
        # s.create_line(px, py, x, y, fill="green")
        # print(x, y)
        px = x
        py = y
        x += vx * _dt

        dx = abs(px - x)
        if dx < ERROR_TOLERANCE:
            return x, y, collides_with_net

        vy += GRAVITY * _dt
        y += vy * _dt
        ctr += 1

    return x, y, collides_with_net


# Function to calculate the velocity a birdie should receive
# after a smash based on the inputs.
def calculate_smash_vel(_x, _y, p, r, sign):
    vx = 0
    vy = 0

    try:
        while True:
            vy -= H
            vx = math.sqrt(p ** 2 - vy ** 2) * sign
            __x, __y, collides = sim(vx, vy, WINDOW_DIMS[0] / 2, _x, _y, r, True, maxX=WINDOW_DIMS[0] / 2)

            if sgn(__x - WINDOW_DIMS[0] / 2) != sgn(_x - WINDOW_DIMS[0] / 2) and not collides:
                break
    except:
        vy = -p / 2
        vx = math.sqrt(p ** 2 - vy ** 2) * sign

    return vx * sign, vy


# Function to calculate the velocity a birdie should receive
# after a volley based on the inputs.
def calculate_hit_vel(p, dy, dx, _x, _y, r):
    # initial guess
    vx = 0
    vy = p
    y = sim(vx, vy, dx, _x, _y, r, False)[0]

    while abs(abs(y) - abs(dy)) > ERROR_TOLERANCE and abs(vy) < p:
        vy -= H
        vx = math.sqrt(p ** 2 - vy ** 2)
        y = sim(vx, vy, dx, _x, _y, r, False)[0]
        # print(y, dy, vx, vy)

    if abs(abs(y) - abs(dy)) > ERROR_TOLERANCE:
        return 15 * p * math.sqrt(1 / 2) * random.uniform(1, 2), -15 * p * math.sqrt(1 / 2)

    return vx, -vy


# Checks if input is bounded by two values.
def bounded(x, b1, b2):
    if b2 <= x <= b1 or b1 <= x <= b2:
        return True
    return False


# Returns the sign of x, x=0 -> 0.
def sgn(x):
    if x == 0:
        return 0
    else:
        return x / abs(x)



# Euclidean distance between two points.
def dist_sq(x1, y1, x2, y2):
    return (x2 - x1)**2+(y2 - y1)**2


# Click event handler.
def click(event):
    global CLICKED_PLAY, CLICKED_OK, LOCKED_IN
    if bounded(event.x, play[0][0], play[1][0]) and bounded(event.y, play[0][1], play[1][1]) and not CLICKED_PLAY:
        CLICKED_PLAY = True
    elif CLICKED_PLAY and bounded(event.x, ok[0][0], ok[1][0]) and bounded(event.y, ok[0][1],
                                                                           ok[1][1]) and not CLICKED_OK:
        CLICKED_OK = True
    elif CLICKED_PLAY and CLICKED_OK and bounded(event.x, lock_in[0][0], lock_in[1][0]) and bounded(event.y,
                                                                                                    lock_in[0][1],
                                                                                                    lock_in[1][1]):
        LOCKED_IN = True

# Key down event handler. Key presses are stored in a global array.
def key_down(event):
    if event.keysym not in KEY_PRESSES:
        KEY_PRESSES.append(event.keysym)


def key_up(event):
    global KEY_PRESSES
    try:
        KEY_PRESSES.remove(event.keysym)
    except ValueError:
        pass


def draw_net():
    s.create_polygon(post_verts, fill="grey", outline="black")
    s.create_rectangle(WINDOW_DIMS[0] / 2 - 1, WINDOW_DIMS[1] - NET_HEIGHT - 1, WINDOW_DIMS[0] / 2 + 1,
                       WINDOW_DIMS[1] - NET_HEIGHT - MESH_HEIGHT, fill="white", outline="white")


def init():
    global GAME_BIRDIE, WINNER, OBJECTS, LEFT_WIN_PIC, RIGHT_WIN_PIC, HOVERED_CHARACTERS, PAUSE
    OBJECTS = []
    HOVERED_CHARACTERS = {'left': [0, None], 'right': [0, None]}
    for side in ['left', 'right']:
        for a in range(0, 360, 5):
            STAR_PLATINUM_RACKETS[str(a) + "-" + side] = PhotoImage(
                file="assets/star-platinum-rackets/star-platinum-racket-arm-" + side + "-" + str(a) + ".gif")
    for side in ['left', 'right']:
        for a in range(0, 360, 5):
            WAMUU_RACKETS[str(a) + "-" + side] = PhotoImage(
                file="assets/wamuu-rackets/wamuu-racket-arm-" + side + "-" + str(a) + ".gif")

    for side in ['left', 'right']:
        for a in range(0, 360, 5):
            ZA_HANDO_RACKETS[str(a) + "-" + side] = PhotoImage(
                file="assets/za-hando-rackets/za-hando-racket-arm-" + side + "-" + str(a) + ".gif")
    GAME_BIRDIE = Birdie(random.choice([WINDOW_DIMS[0] / 4, 3 * WINDOW_DIMS[0] / 4]), 100, 0, 0, 0, False, False)
    OBJECTS.append(GAME_BIRDIE)
    WINNER = None
    PAUSE = False
    LEFT_WIN_PIC = PhotoImage(file="assets/left_win.gif")
    RIGHT_WIN_PIC = PhotoImage(file="assets/right_win.gif")
    for i in range(8):
        NUMBERS.append(PhotoImage(file="assets/numbers/" + str(i) + ".gif"))


def update_score_counter():
    global LEFT_SCORE, LEFT_SCORE_OBJ, RIGHT_SCORE, RIGHT_SCORE_OBJ, WINNER
    s.delete(LEFT_SCORE_OBJ, RIGHT_SCORE_OBJ)
    LEFT_SCORE_OBJ = s.create_image(100, 50, image=NUMBERS[LEFT_SCORE])
    RIGHT_SCORE_OBJ = s.create_image(WINDOW_DIMS[0] - 100, 50, image=NUMBERS[RIGHT_SCORE])
    if LEFT_SCORE > 6:
        WINNER = "left"
    elif RIGHT_SCORE > 6:
        WINNER = "right"


def game_over():
    global WINNER, LEFT_WIN_PIC, RIGHT_WIN_PIC
    if WINNER == 'left':
        s.create_image(WINDOW_DIMS[0] / 2, 60, image=LEFT_WIN_PIC)
    elif WINNER == 'right':
        s.create_image(WINDOW_DIMS[0] / 2, 60, image=RIGHT_WIN_PIC)
    s.update()
    root.after(5000, init_calls)


def del_ready_draw_go():
    global GO_TEXT
    s.delete(READY_TEXT)
    GO_TEXT = s.create_image(WINDOW_DIMS[0] / 2, 60, image=go_img)
    s.update()
    root.after(1000, del_go_call_tick)


def del_go_call_tick():
    s.delete(GO_TEXT)
    root.after(0, tick)


def tick():
    global WINNER, PAUSE, READY_TEXT
    start = time.perf_counter()
    [obj.tick() for obj in OBJECTS]
    s.update()
    delta = time.perf_counter() - start
    if not WINNER:
        if not PAUSE:
            root.after(max(round((dt - delta) * 1000), 0) + DELAY, tick)
        else:
            PAUSE = False
            READY_TEXT = s.create_image(WINDOW_DIMS[0] / 2, 60, image=ready_img)
            s.update()
            root.after(2000, del_ready_draw_go)
    else:
        game_over()


def tick_once():
    [obj.tick() for obj in OBJECTS]
    s.update()


def draw_main_menu():
    return s.create_image(WINDOW_DIMS[0] / 2, WINDOW_DIMS[1] / 2, image=TITLE_SCREEN)


def await_click():
    global INSTRUCTIONS_IMG
    if not CLICKED_PLAY:
        root.after(0, await_click)
    else:
        s.delete(MAIN_IMG)
        INSTRUCTIONS_IMG = s.create_image(WINDOW_DIMS[0] / 2, WINDOW_DIMS[1] / 2, image=instructions)
        s.update()
        root.after(0, help_screen)


def splash():
    global START_TIME, SPLASH_TK
    if time.perf_counter() - START_TIME > 2:
        s.delete(SPLASH_TK)
        root.quit()
        init_calls()
    else:
        root.after(0, splash)


def help_screen():
    global CHARACTER_SELECT_IMG, HOVERED_CHARACTERS
    if not CLICKED_OK:
        root.after(0, help_screen)
    else:
        s.delete(INSTRUCTIONS_IMG)
        CHARACTER_SELECT_IMG = s.create_image(WINDOW_DIMS[0] / 2, WINDOW_DIMS[1] / 2, image=select_bg)
        for i in range(2):
            side = ['left', 'right'][i]
            HOVERED_CHARACTERS[side][1] = [
                s.create_image(CHAR_COORDS[i], image=CHARACTER_SPRITES[HOVERED_CHARACTERS[side][0]][side]), \
                s.create_image(NAME_COORDS[i], image=CHARACTER_NAME_TAGS[HOVERED_CHARACTERS[side][0]])]
        s.update()
        root.after(0, character_select)


def set_tick():
    root.after(0, tick)


def character_select():
    global LEFT_SCORE, LEFT_SCORE_OBJ, RIGHT_SCORE, RIGHT_SCORE_OBJ, HOVERED_CHARACTERS, KEY_PRESSES, PAUSE
    if not LOCKED_IN:
        for i in range(2):
            side = ['left', 'right'][i]
            keys = [['a', 'd'], ['Left', 'Right']][i]
            delta = False

            if keys[0] in KEY_PRESSES:
                delta = True
                HOVERED_CHARACTERS[side][0] -= 1
                KEY_PRESSES.remove(keys[0])
            if keys[1] in KEY_PRESSES:
                delta = True
                HOVERED_CHARACTERS[side][0] += 1
                KEY_PRESSES.remove(keys[1])

            if delta:
                HOVERED_CHARACTERS[side][0] %= len(CHARACTER_SPRITES)
                [s.delete(_) for _ in HOVERED_CHARACTERS[side][1]]
                HOVERED_CHARACTERS[side][1] = [
                    s.create_image(CHAR_COORDS[i], image=CHARACTER_SPRITES[HOVERED_CHARACTERS[side][0]][side]), \
                    s.create_image(NAME_COORDS[i], image=CHARACTER_NAME_TAGS[HOVERED_CHARACTERS[side][0]])]
                s.update()

        root.after(0, character_select)
    else:
        sides = ['left', 'right']
        spawns = [WINDOW_DIMS[0] / 4, 3 * WINDOW_DIMS[0] / 4]
        for i in range(2):
            side = sides[i]
            if HOVERED_CHARACTERS[side][0] == 0:
                t = StarPlatinum(spawns[i], 900, 0, 0, 0, False, False)
            elif HOVERED_CHARACTERS[side][0] == 1:
                t = Wamuu(spawns[i], 900, 0, 0, 0, False, False)
            elif HOVERED_CHARACTERS[side][0] == 2:
                t = ZaHando(spawns[i], 900, 0, 0, 0, False, False)
            t.set_side(side)
            OBJECTS.append(t)
        s.delete(CHARACTER_SELECT_IMG)
        s.create_image(WINDOW_DIMS[0] / 2, WINDOW_DIMS[1] / 2, image=game_bg)
        s.create_image(WINDOW_DIMS[0] / 2, 50, image=header)
        draw_net()
        [[s.delete(_) for _ in HOVERED_CHARACTERS[side][1]] for side in ['left', 'right']]
        LEFT_SCORE = 0
        LEFT_SCORE_OBJ = s.create_image(100, 50, image=NUMBERS[0])
        RIGHT_SCORE = 0
        RIGHT_SCORE_OBJ = s.create_image(WINDOW_DIMS[0] - 100, 50, image=NUMBERS[0])
        root.config(cursor='none')
        s.update()
        PAUSE = True
        root.after(0, tick)


def init_calls():
    global MAIN_IMG, CLICKED_PLAY, CLICKED_OK, LOCKED_IN
    if SOUND:
        AUDIO_CHANNELS[0].play("awaken", loop=True)
    CLICKED_PLAY = False
    CLICKED_OK = False
    LOCKED_IN = False
    s.delete("all")
    init()
    s.focus_set()
    MAIN_IMG = draw_main_menu()
    s.update()
    root.config(cursor='')
    root.after(0, await_click)
    root.mainloop()


def run():
    global SPLASH_TK, AUDIO_CHANNELS, CHARACTERS, CHARACTER_SPRITES, CHARACTER_NAME_TAGS, CHAR_COORDS, \
        NAME_COORDS, instructions, select_bg, game_bg, header, ready_img, go_img, TITLE_SCREEN, START_TIME

    if SOUND:
        AUDIO_CHANNELS = [ConcurrentAudioManager() for i in range(3)]
    s.bind("<Key>", key_down)
    s.bind("<KeyRelease>", key_up)
    s.bind("<Button-1>", click)
    root.attributes("-topmost", True)
    root.protocol("WM_DELETE_WINDOW", kill_music)
    CHARACTERS = ["star-platinum", "wamuu", "za-hando"]
    CHARACTER_SPRITES = []
    CHARACTER_NAME_TAGS = []
    CHAR_COORDS = [[225, 370], [WINDOW_DIMS[0] - 225, 370]]
    NAME_COORDS = [[225, 500], [WINDOW_DIMS[0] - 225, 500]]
    for i in range(len(CHARACTERS)):
        CHARACTER_SPRITES.append({})
        for side in ['left', 'right']:
            CHARACTER_SPRITES[i][side] = PhotoImage(
                file="assets/character-select/" + CHARACTERS[i] + "-" + side + ".gif")

    for name in CHARACTERS:
        CHARACTER_NAME_TAGS.append(PhotoImage(file="assets/character-select/" + name + ".gif"))

    splash_art = PhotoImage(file="assets/splash.gif")
    instructions = PhotoImage(file="assets/instructions.gif")
    select_bg = PhotoImage(file="assets/select.gif")
    game_bg = PhotoImage(file="assets/bg.gif")
    header = PhotoImage(file="assets/header.gif")
    ready_img = PhotoImage(file="assets/ready.gif")
    go_img = PhotoImage(file="assets/go.gif")
    TITLE_SCREEN = PhotoImage(file="assets/title.gif")
    SPLASH_TK = s.create_image(WINDOW_DIMS[0] / 2, WINDOW_DIMS[1] / 2, image=splash_art)
    s.update()
    START_TIME = time.perf_counter()
    root.after(0, splash)
    root.mainloop()


run()
