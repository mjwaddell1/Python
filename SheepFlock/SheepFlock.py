import math, time, pygame
from math import sqrt
from random import randint, random, sample

# This script simulates a sheep flock
# Dogs gather the sheep and push them to the shepherd
# Notes
#    Each dog has slice of circle
#    Dog slices overlap to prevent sheep from jumping between dogs
#    Dog speed must be higher than sheep so dog can pass sheep
#    Sheep can overlap position

flock_radius = 50 # target flock area, move sheep into circle
sheep_speed = 0.25 # max pixel movement per step
dog_speed = 0.75 # max pixel movement per step, should be higher than sheep
sheep_cnt = 250
dog_cnt = 8 # more has faster convergence, but over 20 can cause crowding (sheep blocked by other dogs)
force_dist = 25 # sheep avoid dog
tracerdots = []  #[0,1,2] # highlight dots for tracking

scr_width = 1000
scr_height = 700
window = pygame.display.set_mode((scr_width, scr_height))
pygame.display.set_caption("Sheep")

class shepherd: x,y = (500,350) # for easier syntax, goal/shepherd
class Sheep:
    def __init__(self, x, y, index):
        self.x, self.y, self.index = x, y, index

class Dog:
    def __init__(self, x=0, y=0, index=0):
        self.x, self.y, self.index = x, y, index
        self.angle_start = 0
        self.angle_end = 0
        self.sheep = [] # sheep in dog circle slice
        self.mid_angle = 0 # middle of slice
        self.CheckAngle = None # if sheep in slice

    def SetAngleRange(self, angle_start, angle_end):
        if angle_start < 0: # first dog overlaps last dog
            angle_start += 2*math.pi
        if angle_end > 2*math.pi: # last dog overlaps first dog
            angle_end -= 2*math.pi
        if angle_start < angle_end: # normal
            self.mid_angle = (angle_end + angle_start)/2
            self.CheckAngle = self.__CheckAngle # set check method
        else: # crossed zero, 2 checks required for angle
            self.mid_angle = (angle_end + 2*math.pi - angle_start)/2 + angle_start
            if self.mid_angle > 2*math.pi:
                self.mid_angle -= 2*math.pi
            self.CheckAngle = self.__CheckAngleSplit # set check method
        self.angle_start = angle_start
        self.angle_end = angle_end

    def __CheckAngle(self, angle): # normal
        return self.angle_start <= angle <= self.angle_end

    def __CheckAngleSplit(self, angle): # crossed zero angle, check high and low
        return angle >= self.angle_start or angle <= self.angle_end

    def MoveTowardXY(self, x, y):
        deg = DegreesXY(x, y, self)
        dist = min(DistanceXY(self, x, y), dog_speed)
        self.x = dist * math.cos(deg) + self.x
        self.y = dist * math.sin(deg) + self.y

def DistancePt(pt1, pt2):
    return (sqrt((pt1.x - pt2.x) ** 2 + (pt1.y - pt2.y) ** 2))

def DistanceXY(pt, x, y):
    return (sqrt((pt.x - x) ** 2 + (pt.y - y) ** 2))

def Draw(animal, color=(200, 100, 0), radius = 2): # default orange, used by sheep and dog
    pygame.draw.circle(window, color, (animal.x, animal.y), radius)

def Degrees(pt1, pt2): # pt1 relative to pt2
    # note that the screen coordinates start at top left (0,0). Y goes down. X goes right.
    degx = math.atan2(pt1.y - pt2.y, pt1.x - pt2.x)  # -PI - PI (-3.14 - 3.14)
    if degx < 0:  # convert to full circle
        return math.pi + (math.pi + degx)  # 0 - 2PI
    return degx

def DegreesXY(x, y, pt1): # x,y relative to pt1
    # note that the screen coordinates start at top left (0,0). Y goes down. X goes right.
    degx = math.atan2(y - pt1.y, x - pt1.x)  # -PI - PI (-3.14 - 3.14)
    if degx < 0:  # convert to full circle
        return math.pi + (math.pi + degx)  # 0 - 2PI
    return degx

pygame.font.init() # only needed once
def WriteText(): # instructions
    my_font = pygame.font.SysFont('Arial', 12)
    text_surface = my_font.render('Pause:<Space>  Quit:<Esc>  Move Shepherd:<LeftClick>', False, (200, 200, 200))
    window.blit(text_surface, (10, scr_height - 20))

def CheckEvents(): # check if user clicked key/mouse
    global paused, center
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT: # from title bar
            quit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                paused = not paused
            if event.key == pygame.K_ESCAPE:
                quit()
        if event.type == pygame.MOUSEBUTTONDOWN: # move shepherd
            shepherd.x, shepherd.y = event.dict['pos']

# initialize sheep - random position
sheep = []
for i in range(sheep_cnt):
    sheep.append(Sheep(randint(0, scr_width), randint(0, scr_height), i)) # random sheep position

# initialize dogs, start at shepherd
dogs = []
angle = 0
angle_rng = 2 * math.pi / dog_cnt # each dog has equal slice
for i in range(dog_cnt):
    dg = Dog(shepherd.x, shepherd.y, i)  # dogs start at shepherd
    # each dog has slice of circle
    angle_start = angle
    angle += angle_rng
    angle_end = angle
    # set dog slice with overlap
    dg.SetAngleRange(angle_start - angle_rng * 0.05, angle_end + angle_rng * 0.05)
    dogs.append(dg)

sheep_chk = sample(range(sheep_cnt), 30) # spread these apart

# main loop
paused = False
while True: # run until escape pressed
    CheckEvents() # mouse/escape/space
    if paused: continue
    for dg in dogs: # sheep move, so need to reset sheep collection for each dog
        dg.sheep = []
    for i in range(sheep_cnt):
        shp = sheep[i]
        dog_close = False
        for dg in dogs: # check if dog near sheep
            if DistancePt(dg, shp) < force_dist: # move sheep away from dog
                deg = Degrees(shp, dg)
                dist = sheep_speed
                x = dist * math.cos(deg) + shp.x
                y = dist * math.sin(deg) + shp.y
                shp.x, shp.y = x, y # may move multiple times (once per dog)
                dog_close = True
        if not dog_close: # no dogs nearby, random movement
            if i in sheep_chk: # check for sheep cluster, move to open space
                for ctr in range(4): # 4 tries
                    deg = randint(0, 1000) * 2 * math.pi / 1000.0
                    dist = sheep_speed
                    x = dist * math.cos(deg) + shp.x
                    y = dist * math.sin(deg) + shp.y
                    found = True
                    for shpx in sheep:
                        if shpx.index == i:
                            continue # same sheep
                        if DistanceXY(shpx, x, y) < sheep_speed: # gap to nearest sheep
                            found = False
                    if found:
                        break # exit retry loop
            else:
                deg = randint(0, 1000) * 2 * math.pi / 1000.0
                dist = sheep_speed/2 + sheep_speed/2 * random() # random speed
                x = dist * math.cos(deg) + shp.x
                y = dist * math.sin(deg) + shp.y
            shp.x, shp.y = x, y
        angle = Degrees(shp, shepherd)
        for dg in dogs:
            if dg.CheckAngle(angle):
                dg.sheep.append(shp)
    for dg in dogs: # process sheep for each dog
        degx = Degrees(dg, shepherd)
        dist = DistancePt(dg, shepherd)
        if dist < flock_radius + force_dist or not dg.CheckAngle(degx): # shepherd moved, dogs must move out
            # calc target position for dog (relative to shepherd)
            degx = dg.mid_angle
            dist = flock_radius + force_dist + 1
            x = dist * math.cos(degx) + shepherd.x
            y = dist * math.sin(degx) + shepherd.y
            dg.MoveTowardXY(x, y)
        else: # find the furthest sheep and push toward shepherd
            maxsheep = None
            maxdist = 0
            for shp in dg.sheep:
                dist = DistancePt(shp, shepherd)
                if dist > flock_radius and dist > maxdist: # outermost sheep
                    maxsheep = shp
                    maxdist = dist
            if maxsheep: # move dog toward\past outermost sheep
                # calc dog target position (inline past sheep, so sheep moves toward shepherd)
                degx = Degrees(maxsheep, shepherd)
                dist = DistancePt(maxsheep, shepherd) + force_dist * 0.5
                x = dist * math.cos(degx) + shepherd.x
                y = dist * math.sin(degx) + shepherd.y
                dg.MoveTowardXY(x, y)
            else: # no sheep in sector, move to shepherd
                # calc target position
                dist = flock_radius + force_dist
                x = dist * math.cos(dg.mid_angle) + shepherd.x
                y = dist * math.sin(dg.mid_angle) + shepherd.y
                dg.MoveTowardXY(x, y)

    window.fill((0, 100, 0)) # clear screen
    WriteText()
    for i in range(sheep_cnt): # draw sheep
        if i in tracerdots:
            Draw(sheep[i], (0, 0, 255)) # blue, highlight dots for tracking
        else:
            Draw(sheep[i], (200, 200, 200)) # white
    for i in range(dog_cnt): # draw dogs
        if i in tracerdots:
            Draw(dogs[i], (0, 0, 255), 3) # blue, highlight dots for tracking
        else:
            Draw(dogs[i], (100, 50, 0), 3) # orange

    pygame.draw.circle(window, (50, 50, 50), (shepherd.x, shepherd.y), 5) # circle center
    pygame.display.update() # show updates
    # time.sleep(.1) # slow movement
