import pygame
from math import sqrt
from random import randint, random

neighborRadius = 30 # neighbor radius
birdSpeed = 5 # max movement
minDist = 5 # birds can't overlap
birdCnt = 500

scrWidth = 1000
scrHeight = 700
window = pygame.display.set_mode((scrWidth, scrHeight))
pygame.display.set_caption("Bird Flock")

def Dist(bird1, bird2): # bird to bird
    return (sqrt((bird1.x-bird2.x)**2 + (bird1.y-bird2.y)**2),bird2.x-bird1.x,bird2.y-bird1.y)

def DistPt(bird, x, y): # bird to point
    return (sqrt((x-bird.x)**2 + (y-bird.y)**2))

class Bird:
    def __init__(self, x=0, y=0, index=0):
        self.index = index
        self.x = x
        self.y = y
        self.newX = 0
        self.newY = 0
        self.neighbors = [] # closest birds

    def Draw(self, color=(200, 100, 0)): # default orange
        pygame.draw.circle(window, color, (self.x, self.y), 2)

    def GetNeighbors(self, maxCnt = 10): # 10 closest neighbors within radius
        neighbors = []
        for bird in birds:
            if bird.index != self.index and Dist(self, bird)[0] <= neighborRadius:
                neighbors.append((bird, Dist(self, bird))) # tuple (bird, (dist,distx,disty))
        neighbors.sort(key=lambda b: b[1][0]) # sort by neighbor distance
        self.neighbors = neighbors[:maxCnt] # 10 closest birds
        return self.neighbors

    def CancelMove(self): # stay at current position
        self.newX = self.x
        self.newY = self.y

    def TryMove(self, wantX, wantY, factor=1.0): # move if space available
        wantDistX = wantX - birds[i].x # target position is wantx, wanty
        wantDistY = wantY - birds[i].y
        wantDist = DistPt(birds[i], wantX, wantY)
        moveDist = min([birdSpeed, wantDist]) # can't go faster than bird speed
        if wantDist == 0: # at goal
            self.CancelMove() # keep current position
            return True # okay to stay in position
        else: # move to new position
            birds[i].newX = birds[i].x + (wantDistX * moveDist / wantDist) * factor
            birds[i].newY = birds[i].y + (wantDistY * moveDist / wantDist) * factor
            if not self.CheckMove(): # can't move, revert
                self.CancelMove() # keep current position
                return False # move failed
        return True # will move

    def CheckMove(self):
        if DistPt(goal, self.x, self.y) < DistPt(goal, self.newX, self.newY):
            return False # can't fly away from goal
        val = True
        for bird in self.neighbors:
            if bird.index == -1: continue # skip goal
            if bird[0].index != self.index: # skip self
                val = val and (DistPt(bird[0], self.newX, self.newY) >= minDist)
        return val

pygame.font.init() # only needed once
def WriteText():
    font = pygame.font.SysFont('Arial', 12)
    textSurface = font.render('Pause:<Space>  Quit:<Esc>  Move Target:<LeftClick>', False, (200, 200, 200))
    window.blit(textSurface, (10, scrHeight - 20))

def CheckEvents():
    global paused
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT: # from title bar
            quit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                paused = not paused
            if event.key == pygame.K_ESCAPE:
                quit()
        if event.type == pygame.MOUSEBUTTONDOWN: # move goal
            goal.x, goal.y = event.dict['pos']

goal = Bird(500,350,-1) # final goal, not actually a bird

# initialize birds, some off-screen
birds = []
for i in range(birdCnt):
    birds.append(Bird(randint(0, scrWidth), randint(0, scrHeight), i)) # random bird position

paused = False
while True: # run until escape pressed
    CheckEvents() # mouse/escape/space
    if paused: continue
    for i in range(birdCnt):
        totX = 0
        totY = 0
        # bird wants to move to bird cluster and also to goal
        neighbors = birds[i].GetNeighbors() # within radius, 10 closest
        moved = False
        if len(neighbors): # other birds close enough
            # find center of neighbors
            for bird in neighbors: # bird is tuple (bird,(dist,distx,disty))
                totX += bird[1][1] # total x
                totY += bird[1][2] # total y
            wantX = birds[i].x + totX / len(neighbors)  # center of neighbors (includes goal)
            wantY = birds[i].y + totY / len(neighbors)
            moved = birds[i].TryMove(wantX, wantY) # factor=1, more pull toward neighbors
        if not moved: # if no neighbors or no space within neighbors
            if not birds[i].TryMove(goal.x, goal.y, .8): # try move toward goal, less pull
                # can't move to neighbors or goal, just make random move
                wantX = birds[i].x + random() * birdSpeed * randint(-1, 1)
                wantY = birds[i].y + random() * birdSpeed * randint(-1, 1)
                birds[i].TryMove(wantX, wantY) # random move for edge birds

    window.fill((0, 0, 0)) # clear screen
    WriteText()
    for i in range(birdCnt): # move birds
        birds[i].x = birds[i].newX
        birds[i].y = birds[i].newY
        birds[i].Draw()

    pygame.draw.circle(window, (255,255,255), (goal.x, goal.y), 5) # main goal
    pygame.display.update() # show updates

