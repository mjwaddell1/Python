import math, time, pygame
from math import sqrt
from random import randint

# This is a simple experiment in swarm intelligence
# A field of random dots will create a circle given only 2 instructions:
#    - Move to\from the center point to match the radius value
#    - Center between neighbors
# note that dot angles are in radians (0-2PI), not degrees (0-360)

class center: x,y = (500,350) # for easier syntax, circle center
class Neighbor: # easier syntax
    def __init__(self, pos=None, neg=None):
        self.pos, self.neg = pos, neg

radius = 200 # target distance dot to center
dotspeed = 0.1 # max pixel movement per step
dot_speed_rad = 2 * math.pi * dotspeed / (2 * math.pi * radius) # max radian movement per step
dot_cnt = 50 # dot count
tracerdots = []  #[0,1,2] # highlight dots for tracking

scr_width = 1000
scr_height = 700
window = pygame.display.set_mode((scr_width, scr_height))
pygame.display.set_caption("Dot Circle")

class Dot:
    def __init__(self, x=0, y=0, index=0):
        self.index = index
        # x, y used when calculating new position of neighbors
        # newx, newy is new position after calculation
        self.x = self.newx = x
        self.y = self.newy = y
        self.on_circle = False # true when dot at correct radius

    def Draw(self, color=(200, 100, 0)): # default orange
        pygame.draw.circle(window, color, (self.newx, self.newy), 2)
        # update position for next cycle
        self.x = self.newx
        self.y = self.newy

    def CenterDist(self): # dot distance from center
        return (sqrt((center.x - self.x) ** 2 + (center.y - self.y) ** 2))

    def Degrees(self): # dot degrees on circle, radians (0-6.28), 0 directly right, 90 degrees (PI/2) is down
        # note that the screen coordinates start at top left (0,0). Y goes down. X goes right.
        deg = math.atan2(self.y - center.y, self.x - center.x) # -PI - PI (-3.14 - 3.14)
        if deg < 0: # convert to full circle
            return math.pi + (math.pi + deg) # 0 - 2PI
        return deg

    def MoveTowardCenter(self, dist): # move to\from circle edge
        # right triangle, just magnify/shrink
        ratio = dist/self.CenterDist() # hypotenuse
        # update draw position, keep x,y for neighbor calcs
        self.newx = center.x + (self.x - center.x) * (1 + ratio)
        self.newy = center.y + (self.y - center.y) * (1 + ratio)

    def MoveDegrees(self, degs): # move around circle
        newdeg = self.Degrees() + degs
        # check if crossed 0 angle
        if newdeg > 2 * math.pi:
            newdeg -= 2 * math.pi
        if newdeg < 0:
            newdeg += 2 * math.pi
        # degrees relative to center
        # keep x,y for neighbor calcs
        self.newx = radius * math.cos(newdeg) + center.x
        self.newy = radius * math.sin(newdeg) + center.y

    def GetNeighbors(self): # get closest neighbor each side
        min_neg = 100
        min_pos = 100
        neighbor_neg = None
        neighbor_pos = None
        deg_diff_pos = deg_diff_neg = 0
        # scan all dots for closest neighbors
        for dot in dots:
            if dot.index != self.index and dot.on_circle: # ignore dots not at circle edge
                other_deg = dot.Degrees()
                self_deg = self.Degrees()
                if other_deg == self_deg: # prevent div/0
                    self_deg += 0.0001
                # for each dot, calc angle on both sides
                if other_deg > self_deg:
                    deg_diff_pos = other_deg - self_deg
                    deg_diff_neg = 2*math.pi - deg_diff_pos
                if other_deg < self_deg:
                    deg_diff_neg = self_deg - other_deg
                    deg_diff_pos = 2*math.pi - deg_diff_neg
                # check if closest
                if deg_diff_pos < min_pos:
                    min_pos = deg_diff_pos
                    neighbor_pos = dot # closest neighbor with larger angle
                if deg_diff_neg < min_neg:
                    min_neg = deg_diff_neg
                    neighbor_neg = dot # closest neighbor with smaller angle
        return Neighbor(neighbor_pos, neighbor_neg)

pygame.font.init() # only needed once
def WriteText(): # instructions
    my_font = pygame.font.SysFont('Arial', 12)
    text_surface = my_font.render('Pause:<Space>  Quit:<Esc>  Move Center:<LeftClick>', False, (200, 200, 200))
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
        if event.type == pygame.MOUSEBUTTONDOWN: # move center
            center.x, center.y = event.dict['pos']

# initialize random dots
dots = []
for i in range(dot_cnt):
    dots.append(Dot(randint(0, scr_width), randint(0, scr_height), i)) # random dot position

paused = False
while True: # run until escape pressed
    CheckEvents() # mouse/escape/space
    if paused: continue
    for i in range(dot_cnt):
        move_dist = round(radius - dots[i].CenterDist(), 5) # move to circle edge
        if move_dist < 0: # move dot in
            dots[i].MoveTowardCenter(-min(-move_dist, dotspeed))
        elif move_dist > 0: # move dot out
            dots[i].MoveTowardCenter(min(move_dist, dotspeed))
        else: # spread around circle
            dots[i].on_circle = True # at correct radius, now space out around circle
            dot_deg = dots[i].Degrees()
            if dot_deg < 0.001: # prevent overflow at 0
                pass
            neighbors = dots[i].GetNeighbors() # closest dots high\low
            if not (neighbors.pos or neighbors.neg): # only one dot on circle
                continue
            deg_high = neighbors.pos.Degrees() # positive side
            deg_low = neighbors.neg.Degrees() # negative side
            deg_diff = deg_high - deg_low # degree gap between neighbors
            mid_deg = deg_low + deg_diff / 2.0 # midpoint degrees between neighbors
            if deg_diff < 0: # negative degrees
                mid_deg += math.pi # make degrees positive
            if mid_deg > 2*math.pi: # past entire circle (over 360 degrees)
                mid_deg -= 2*math.pi # shift down

            mid_deg_diff = mid_deg - dot_deg # degree distance from dot
            if abs(mid_deg_diff) > math.pi: # neighbors crossed 0 angle, goal angle is opposite side of 0
                if dot_deg < mid_deg: # other side of 0 angle
                    mid_deg_diff = -(dot_deg + 2 * math.pi - mid_deg) # add gaps above/below zero
                if mid_deg < deg_high: # other side of 0 angle
                    mid_deg_diff = mid_deg + 2 * math.pi - dot_deg # add gaps below/above zero

            if mid_deg_diff > 0: # move dot clockwise
                dots[i].MoveDegrees(min(mid_deg_diff, dot_speed_rad))
            if mid_deg_diff < 0: # move dot counterclockwise
                dots[i].MoveDegrees(max(mid_deg_diff, -dot_speed_rad))

    window.fill((0, 0, 0)) # clear screen
    WriteText()
    for i in range(dot_cnt): # move dots
        if i in tracerdots:
            dots[i].Draw((255,200,200)) # white, highlight dots for tracking
        else:
            dots[i].Draw() # orange
        # draw index next to dot
        # my_font = pygame.font.SysFont('Arial', 15)
        # text_surface = my_font.render(str(dots[i].index), False, (200, 200, 200))
        # window.blit(text_surface, (dots[i].x, dots[i].y))

    pygame.draw.circle(window, (255,255,255), (center.x, center.y), 5) # circle center
    pygame.display.update() # show updates
    # time.sleep(.1) # slow movement

