import pygame
from math import sqrt
from random import randint, random

neighborradius = 30 # neighbor radius
birdspeed = 5 # max movement
mindist = 5 # birds can't overlap
birdcnt = 500

scr_width = 1000
scr_height = 700
window = pygame.display.set_mode((scr_width, scr_height))
pygame.display.set_caption("Bird Flock")

def dist(bird1, bird2): # bird to bird
    return (sqrt((bird1.x-bird2.x)**2 + (bird1.y-bird2.y)**2),bird2.x-bird1.x,bird2.y-bird1.y)

def distpt(bird, x, y): # bird to point
    return (sqrt((x-bird.x)**2 + (y-bird.y)**2))

class Bird:
    def __init__(self, x=0, y=0, index=0):
        self.index = index
        self.x = x
        self.y = y
        self.newx = 0
        self.newy = 0
        self.neighbors = [] # closest birds

    def Draw(self, color=(200, 100, 0)): # default orange
        pygame.draw.circle(window, color, (self.x, self.y), 2)

    def GetNeighbors(self, maxcnt = 10): # 10 closest neighbors within radius
        neighbors = []
        for bird in birds:
            if bird.index != self.index and dist(self, bird)[0] <= neighborradius:
                neighbors.append((bird,dist(self, bird))) # tuple (bird, (dist,distx,disty))
        neighbors.sort(key=lambda b: b[1][0]) # sort by neighbor distance
        self.neighbors = neighbors[:maxcnt] # 10 closest birds
        return self.neighbors

    def CancelMove(self): # stay at current position
        self.newx = self.x
        self.newy = self.y

    def TryMove(self, wantx, wanty, factor=1.0): # move if space available
        wantdistx = wantx - birds[i].x # target position is wantx, wanty
        wantdisty = wanty - birds[i].y
        wantdist = distpt(birds[i], wantx, wanty)
        movedist = min([birdspeed, wantdist]) # can't go faster than bird speed
        if wantdist == 0: # at goal
            self.CancelMove() # keep current position
            return True # okay to stay in position
        else: # move to new position
            birds[i].newx = birds[i].x + (wantdistx * movedist / wantdist) * factor
            birds[i].newy = birds[i].y + (wantdisty * movedist / wantdist) * factor
            if not self.CheckMove(): # can't move, revert
                self.CancelMove() # keep current position
                return False # move failed
        return True # will move

    def CheckMove(self):
        if distpt(goal, self.x, self.y) < distpt(goal, self.newx, self.newy):
            return False # can't fly away from goal
        val = True
        for bird in self.neighbors:
            if bird.index == -1: continue # skip goal
            if bird[0].index != self.index: # skip self
                val = val and (distpt(bird[0], self.newx, self.newy) >= mindist)
        return val

pygame.font.init() # only needed once
def WriteText():
    my_font = pygame.font.SysFont('Arial', 12)
    text_surface = my_font.render('Pause:<Space>  Quit:<Esc>  Move Target:<LeftClick>', False, (200, 200, 200))
    window.blit(text_surface, (10, scr_height - 20))

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
for i in range(birdcnt):
    birds.append(Bird(randint(0, scr_width),randint(0, scr_height),i)) # random bird position

paused = False
while True: # run until escape pressed
    CheckEvents() # mouse/escape/space
    if paused: continue
    for i in range(birdcnt):
        totx = 0
        toty = 0
        # bird wants to move to bird cluster and also to goal
        neighbors = birds[i].GetNeighbors() # within radius, 10 closest
        moved = False
        if len(neighbors): # other birds close enough
            # find center of neighbors
            for bird in neighbors: # bird is tuple (bird,(dist,distx,disty))
                totx += bird[1][1] # total x
                toty += bird[1][2] # total y
            wantx = birds[i].x + totx / len(neighbors)  # center of neighbors (includes goal)
            wanty = birds[i].y + toty / len(neighbors)
            moved = birds[i].TryMove(wantx, wanty) # factor=1, more pull toward neighbors
        if not moved: # if no neighbors or no space within neighbors
            if not birds[i].TryMove(goal.x, goal.y, .8): # try move toward goal, less pull
                # can't move to neighbors or goal, just make random move
                wantx = birds[i].x + random()*birdspeed*randint(-1,1)
                wanty = birds[i].y + random()*birdspeed*randint(-1,1)
                birds[i].TryMove(wantx, wanty) # random move for edge birds

    window.fill((0, 0, 0)) # clear screen
    WriteText()
    for i in range(birdcnt): # move birds
        birds[i].x = birds[i].newx
        birds[i].y = birds[i].newy
        birds[i].Draw()

    pygame.draw.circle(window, (255,255,255), (goal.x, goal.y), 5) # main goal
    pygame.display.update() # show updates

