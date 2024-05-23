import math, time, pygame
from math import sqrt
from random import randint

# This script simulates ants foraging for food
# Ants leave nest in random directions and repeat until food is found
# The food trail is used by the other ants until food is moved
# When food is moved, ants must return to nest to get new food trail
# Notes:
#    Ants will return to nest if no food found
#    Ants don't look for new food during return trip
#    Latest found food path is used by rest of colony, previous paths deactivated
#    Food path may not be the most direct route, just latest path found
#    Multiple ants may be at same position, so single dot shown
#    In reality, ants can can smell food 100 miles away if not obstacles

# Possible add-ons:
#    Food runs out, create new food source
#    Multiple food sources
#    Predator attacks nest
#    Staggered dispersal

class Point: # for nest and food
    def __init__(self, x, y):
        self.x, self.y = (x, y)

class FoodTrail (list): # need list with active flag
    def __init__(self, trail=()):
        list.__init__([])
        self.extend(trail)
        self.active = True # new trail always active

nest = Point(500, 350) # ant starting point
food = Point(250, 300) # goal
food_trails = [] # every FoodTrail leading to food
max_steps = 200 # before returning to nest
ant_speed = 3 # max pixel movement per step
ant_cnt = 50 # dot count
food_smell_dist = 30 # ant can detect food
tracer_ants = []  #[0,1,2] # highlight ants for tracking

scr_width = 1000
scr_height = 700
window = pygame.display.set_mode((scr_width, scr_height))
pygame.display.set_caption("Ants")

def DistancePt(pt1, pt2):
    return (sqrt((pt1.x - pt2.x) ** 2 + (pt1.y - pt2.y) ** 2))

def DistanceXY(pt, x, y):
    return (sqrt((pt.x - x) ** 2 + (pt.y - y) ** 2))

def Degrees(pt1, pt2): # pt1 relative to pt2
    # note that the screen coordinates start at top left (0,0). Y goes down. X goes right.
    deg = math.atan2(pt1.y - pt2.y, pt1.x - pt2.x)  # -PI - PI (-3.14 - 3.14)
    if deg < 0:  # convert to full circle
        return math.pi + (math.pi + deg)  # 0 - 2PI
    return deg

class Ant:
    def __init__(self, x=0, y=0, index=0):
        self.index = index # mostly for debugging
        self.x = x
        self.y = y
        self.trail = [(nest.x, nest.y)] # every trail starts at nest
        self.nest_dist = 0 # distance to nest
        self.direction = 1 # leaving nest
        self.found_food = False
        self.food_trail_index = -1 # if following food trail
        self.cancel_food = False # on food trail, food not there
        self.trail_pos = 0

    def Draw(self, color=(200, 100, 0)): # default orange
        # add random delta so multiple dots visible (instead of single dot)
        xd = randint(0, 100)/50.0
        yd = randint(0, 100)/50.0
        pygame.draw.circle(window, color, (self.x + xd, self.y + yd), 2)

    def MoveStep(self, dist):
        global food_trails
        if len(self.trail) == 1: # at nest (direction is 0 or 1)
            food_trail_idx = -1 # food trail index
            # find active food trail
            for i in range(len(food_trails)):
                if food_trails[i].active:
                    food_trail_idx = i
                    self.trail = food_trails[i][:] # copy food trail to ant
            if food_trail_idx > -1: # found active trail to food
                self.direction = 1 # moving out
                self.food_trail_index = food_trail_idx
                self.trail_pos = 1
                self.x, self.y = self.trail[self.trail_pos]
            else: # no food trail, move out in random direction
                self.direction = 1 # move out
                dist = ant_speed # max ant speed
                deg = randint(0, 1000) * 2 * math.pi / 1000.0
                x = dist * math.cos(deg) + self.x
                y = dist * math.sin(deg) + self.y
                self.nest_dist = 0 # ant distance from nest
                self.x, self.y = x, y
                self.trail.append((self.x, self.y))
            return
        if self.direction == 1 and self.food_trail_index > -1: # on food trail, moving toward food
            self.trail_pos += 1
            if self.trail_pos >= len(self.trail): # at food
                if DistancePt(self, food) > 1: # food not there
                    self.cancel_food = True
                    self.direction = -1 # return to nest
                    self.trail_pos -= 1
                else: # found food
                    self.direction = -1 # return to nest
                    self.trail_pos -= 1
            else: # next step toward food
                self.x, self.y = self.trail[self.trail_pos]
            return
        if self.direction == 1: # moving out randomly
            # near food?
            food_dist = DistancePt(food, self)
            if food_dist < 0.01: # close enough
                self.found_food = True
                self.direction = -1 # return to nest
                return
            if food_dist < food_smell_dist:  # detect food, go toward food
                deg = Degrees(food, self)
                dist = min(food_dist, ant_speed)
                x = dist * math.cos(deg) + self.x
                y = dist * math.sin(deg) + self.y
                self.x, self.y = x, y
                self.trail.append((self.x, self.y)) # extend trail
                self.trail_pos += 1
            else: # just moving away from nest, searching for food
                # random direction out
                while True: # move away from nest
                    deg = randint(0, 1000) * 2*math.pi/1000.0
                    x = dist * math.cos(deg) + self.x
                    y = dist * math.sin(deg) + self.y
                    dist_nst = DistanceXY(nest, x, y)
                    if dist_nst >= self.nest_dist - .5: # further from nest
                        break
                self.nest_dist = dist_nst
                self.x, self.y = x, y
                self.trail.append((self.x, self.y))
                if len(self.trail) > max_steps: # too far from nest, give up search
                    self.direction = -1 # return to nest
                self.trail_pos += 1
            return
        if self.direction == -1: # returning to nest
            self.trail_pos -= 1
            if self.trail_pos == 0: # at nest
                self.direction = 0 # wait for now
                if self.found_food: # save food trail for other ants
                    if self.food_trail_index == -1: # not existing food trail
                        # deactivate previous trails
                        for ft in food_trails:
                            ft.active = False
                        food_trails.append(FoodTrail(self.trail[:])) # save new active trail
                elif self.cancel_food: # food not found (moved)
                    food_trails[self.food_trail_index].active = False # deactivate trail
                    self.food_trail_index = -1
                    self.cancel_food = False
                self.found_food = False
                self.trail = [(nest.x, nest.y)] # reset ant trail
                self.trail_pos = 0
                return
            self.x, self.y = self.trail[self.trail_pos]
            return

pygame.font.init() # only needed once
def WriteText(): # instructions
    my_font = pygame.font.SysFont('Arial', 12)
    text_surface = my_font.render('Pause:<Space>  Quit:<Esc>  Move Food:<LeftClick>', False, (200, 200, 200))
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
        if event.type == pygame.MOUSEBUTTONDOWN: # move food
            food.x, food.y = event.dict['pos']

# initialize random dots
ants = []
for i in range(ant_cnt):
    ants.append(Ant(nest.x, nest.y, i)) # start at nest

paused = False
while True: # run until escape pressed
    CheckEvents() # mouse/escape/space
    if paused: continue
    for i in range(ant_cnt):
        ants[i].MoveStep(ant_speed)

    # update screen with new positions
    window.fill((0, 0, 0)) # clear screen
    WriteText() # instruction text
    for i in range(ant_cnt): # move dots
        if i in tracer_ants:
            ants[i].Draw((255,200,200)) # white, highlight dots for tracking
        else:
            ants[i].Draw((i*5,255-i*5,200)) # multiple colors for easier tracking
        # draw index next to dot for debugging
        # my_font = pygame.font.SysFont('Arial', 15)
        # text_surface = my_font.render(str(dots[i].index), False, (200, 200, 200))
        # window.blit(text_surface, (dots[i].x, dots[i].y))

    pygame.draw.circle(window, (255,255,255), (nest.x, nest.y), 5) # circle center
    pygame.draw.circle(window, (55,255,55), (food.x, food.y), 5) # circle center
    pygame.display.update() # show updates
    time.sleep(.1) # slow movement
