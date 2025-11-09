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
dotSpeed = 0.1 # max pixel movement per step
dotSpeedRad = 2 * math.pi * dotSpeed / (2 * math.pi * radius) # max radian movement per step
dotCnt = 50 # dot count
tracerDots = []  #[0,1,2] # highlight dots for tracking

scrWidth = 1000
scrHeight = 700
window = pygame.display.set_mode((scrWidth, scrHeight))
pygame.display.set_caption("Dot Circle")

class Dot:
    def __init__(self, x=0, y=0, index=0):
        self.index = index
        # x, y used when calculating new position of neighbors
        # newx, newy is new position after calculation
        self.x = self.newX = x
        self.y = self.newY = y
        self.onCircle = False # true when dot at correct radius

    def Draw(self, color=(200, 100, 0)): # default orange
        pygame.draw.circle(window, color, (self.newX, self.newY), 2)
        # update position for next cycle
        self.x = self.newX
        self.y = self.newY

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
        self.newX = center.x + (self.x - center.x) * (1 + ratio)
        self.newY = center.y + (self.y - center.y) * (1 + ratio)

    def MoveDegrees(self, degs): # move around circle
        newDeg = self.Degrees() + degs
        # check if crossed 0 angle
        if newDeg > 2 * math.pi:
            newDeg -= 2 * math.pi
        if newDeg < 0:
            newDeg += 2 * math.pi
        # degrees relative to center
        # keep x,y for neighbor calcs
        self.newX = radius * math.cos(newDeg) + center.x
        self.newY = radius * math.sin(newDeg) + center.y

    def GetNeighbors(self): # get closest neighbor each side
        minNeg = 100
        minPos = 100
        neighborNeg = None
        neighborPos = None
        degDiffPos = degDiffNeg = 0
        # scan all dots for closest neighbors
        for dot in dots:
            if dot.index != self.index and dot.onCircle: # ignore dots not at circle edge
                otherDeg = dot.Degrees()
                selfDeg = self.Degrees()
                if otherDeg == selfDeg: # prevent div/0
                    selfDeg += 0.0001
                # for each dot, calc angle on both sides
                if otherDeg > selfDeg:
                    degDiffPos = otherDeg - selfDeg
                    degDiffNeg = 2*math.pi - degDiffPos
                if otherDeg < selfDeg:
                    degDiffNeg = selfDeg - otherDeg
                    degDiffPos = 2*math.pi - degDiffNeg
                # check if closest
                if degDiffPos < minPos:
                    minPos = degDiffPos
                    neighborPos = dot # closest neighbor with larger angle
                if degDiffNeg < minNeg:
                    minNeg = degDiffNeg
                    neighborNeg = dot # closest neighbor with smaller angle
        return Neighbor(neighborPos, neighborNeg)

pygame.font.init() # only needed once
def WriteText(): # instructions
    font = pygame.font.SysFont('Arial', 12)
    textSurface = font.render('Pause:<Space>  Quit:<Esc>  Move Center:<LeftClick>', False, (200, 200, 200))
    window.blit(textSurface, (10, scrHeight - 20))

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
for i in range(dotCnt):
    dots.append(Dot(randint(0, scrWidth), randint(0, scrHeight), i)) # random dot position

paused = False
while True: # run until escape pressed
    CheckEvents() # mouse/escape/space
    if paused: continue
    for i in range(dotCnt):
        moveDist = round(radius - dots[i].CenterDist(), 5) # move to circle edge
        if moveDist < 0: # move dot in
            dots[i].MoveTowardCenter(-min(-moveDist, dotSpeed))
        elif moveDist > 0: # move dot out
            dots[i].MoveTowardCenter(min(moveDist, dotSpeed))
        else: # spread around circle
            dots[i].onCircle = True # at correct radius, now space out around circle
            dotDeg = dots[i].Degrees()
            if dotDeg < 0.001: # prevent overflow at 0
                pass
            neighbors = dots[i].GetNeighbors() # closest dots high\low
            if not (neighbors.pos or neighbors.neg): # only one dot on circle
                continue
            degHigh = neighbors.pos.Degrees() # positive side
            degLow = neighbors.neg.Degrees() # negative side
            degDiff = degHigh - degLow # degree gap between neighbors
            midDeg = degLow + degDiff / 2.0 # midpoint degrees between neighbors
            if degDiff < 0: # negative degrees
                midDeg += math.pi # make degrees positive
            if midDeg > 2*math.pi: # past entire circle (over 360 degrees)
                midDeg -= 2 * math.pi # shift down

            midDegDiff = midDeg - dotDeg # degree distance from dot
            if abs(midDegDiff) > math.pi: # neighbors crossed 0 angle, goal angle is opposite side of 0
                if dotDeg < midDeg: # other side of 0 angle
                    midDegDiff = -(dotDeg + 2 * math.pi - midDeg) # add gaps above/below zero
                if midDeg < degHigh: # other side of 0 angle
                    midDegDiff = midDeg + 2 * math.pi - dotDeg # add gaps below/above zero

            if midDegDiff > 0: # move dot clockwise
                dots[i].MoveDegrees(min(midDegDiff, dotSpeedRad))
            if midDegDiff < 0: # move dot counterclockwise
                dots[i].MoveDegrees(max(midDegDiff, -dotSpeedRad))

    window.fill((0, 0, 0)) # clear screen
    WriteText()
    for i in range(dotCnt): # move dots
        if i in tracerDots:
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

