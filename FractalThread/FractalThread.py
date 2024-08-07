import pygame, time, threading, colorsys
import numpy as np

pygame.init() # required for screen info
# open full screen
infoObject = pygame.display.Info()
scr_width = infoObject.current_w   # 1920
scr_height = infoObject.current_h  # 1080
window = pygame.display.set_mode((scr_width, scr_height))
pygame.display.set_caption("Fractal")

class Frame: # for render history
    def __init__(self, fractal_rect, surface, selection_rect):
        self.fractal_rect = fractal_rect
        self.surface = surface
        self.selection_rect = selection_rect

drag = False # drawing selection rectangle
drawing = False # drawing fractal in progress

def CheckEvents():
    global drag, frames, cur_frame, sel_rect
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT: # from title bar
            quit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                quit()
        if not drawing: # drawing fractal
            if event.type == pygame.MOUSEBUTTONDOWN: # start selection
                drag = True
                sel_rect = [0, 0, 0, 0]
                sel_rect[0], sel_rect[1] = event.pos
                frames[cur_frame].selection_rect = sel_rect
            if event.type == pygame.MOUSEBUTTONUP:
                drag = False # done selection
            if event.type == pygame.MOUSEMOTION:
                if drag: # mouse button pressed
                    sel_rect[2], sel_rect[3] = event.pos # adjust selection rectangle
                    frames[cur_frame].selection_rect = sel_rect
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE: # reset image
                    cur_frame = 0
                    frames[0].selection_rect = [0, 0, 0, 0] # reset selection
                    frames = frames[:1] # trim to 1st frame
                if (event.key == pygame.K_RETURN # process selection rectangle
                        and sel_rect[2] - sel_rect[0] > 0
                        and sel_rect[3] - sel_rect[1] > 0):
                    fract_rect = frames[cur_frame].fractal_rect[:] # don't overwrite history
                    temp = (fract_rect[0], fract_rect[1], fract_rect[2], fract_rect[3])
                    # new fractal boundaries based on selection rectangle
                    fract_rect[0] = temp[0] + (temp[2] - temp[0]) / scr_width * sel_rect[0]
                    fract_rect[2] = temp[0] + (temp[2] - temp[0]) / scr_width * sel_rect[2]
                    fract_rect[1] = temp[1] + (temp[3] - temp[1]) / scr_height * sel_rect[1]
                    fract_rect[3] = temp[1] + (temp[3] - temp[1]) / scr_height * sel_rect[3]
                    sfcx = DrawFractal(fract_rect)
                    frames = frames[:cur_frame+1] # remove later frames
                    cur_frame += 1
                    sel_rect = [0, 0, 0, 0] # clear selection rectangle
                    frames.append(Frame(fract_rect, sfcx, sel_rect))
                if event.key == pygame.K_LEFT and cur_frame > 0: # left arrow
                    cur_frame -= 1
                if event.key == pygame.K_RIGHT and cur_frame < len(frames)-1: # right arrow
                    cur_frame += 1


iterations = 1000 # even number, higher value has more detail, longer render time

def GenerateColors(): # color wheel
    colors = []
    for hue in range(iterations):
        clr = colorsys.hsv_to_rgb(hue/float(iterations), 0.5, 0.5)
        colors.append((int(clr[0]*255), int(clr[1]*255), int(clr[2]*255)))
    mid = int(iterations * 0.7)
    colors = colors[mid:] + colors[:mid] # shift starting color
    return colors

colors = GenerateColors()

# https://medium.com/nerd-for-tech/programming-fractals-in-python-d42db4e2ed33
def Mandelbrot(c, z): # calculate single point
   count = 0
   for a in range(iterations):
      z = z**2 + c
      count += 1
      if(abs(z) > 4):
         break
   return count

def MandelbrotThread(x,y,i): # generate single column
    for j in range(len(y)):
        c = complex(x[i], y[j])
        z = complex(0, 0)
        count = Mandelbrot(c, z)
        # window.set_at((i,j), (0, (count*5) % 200, 0)) # shades of green, more contrast
        # window.set_at((i,j), (0, count/iterations*200, 0)) # shades of green, single scale
        window.set_at((i, j), colors[count-1])  # color wheel
   
threads = []
def MandelbrotSet(x, y): # use multithreading
    print('Multi Thread')
    global threads
    ctr_start = time.perf_counter()
    for i in range(len(x)):
        t1 = threading.Thread(target=MandelbrotThread, args=(x,y,i)) # each column
        threads.append(t1)
        CheckEvents()  # check quit event
        t1.start() # threads are queued here
        if i%12 == 0: # 12 cores
           for th in threads:
               th.join() # wait for threads to finish
           threads=[]
           pygame.display.update()  # 12 columns
    pygame.display.update()  # each column
    ctr_stop = time.perf_counter()
    print('Draw Time:', ctr_stop - ctr_start) # 14 seconds
    CheckEvents()  # check quit event

# def MandelbrotSet(x, y): # single thread
#    print('Single Thread')
#    ctr_start = time.perf_counter()
#    for i in range(len(x)):
#       for j in range(len(y)):
#          c = complex(x[i], y[j])
#          z = complex(0, 0)
#          count = mandelbrot(c, z)
#          window.set_at((i,j), (0, (count*7)%200, 0)) # shades of green
#          CheckEvents() # check quit event
#       pygame.display.update() # each column
#    ctr_stop = time.perf_counter()
#    print('Draw Time:', ctr_stop - ctr_start) # 15 seconds

def DrawFractal(fract_rect):
    global drawing
    drawing = True # render in progress
    # creating our x and y arrays
    x = np.linspace(fract_rect[0], fract_rect[2], scr_width)
    y = np.linspace(fract_rect[1], fract_rect[3], scr_height)
    # create our mandelbrot set
    MandelbrotSet(x, y) # generate fractal image
    sfc_fractal = window.copy() # store fractal image for quick redraw
    drawing = False
    return sfc_fractal

fract_rect_start = [-2.6, -1.5, 1.5, 1.5] # initial fractal boundaries
sel_rect = [0, 0, 0, 0] # no selection rectangle
sfc = DrawFractal(fract_rect_start) # initial screen
frames = [Frame(fract_rect_start, sfc, sel_rect)] # image history for quick rendering undo\redo
cur_frame = 0 # initial image

if __name__ =="__main__": # needed for threading
    while True: # run until escape pressed
        CheckEvents() # mouse/escape/space
        window.fill((0, 0, 0))  # clear screen
        window.blit(frames[cur_frame].surface, (0, 0)) # redraw fractal image first
        sel_rect = frames[cur_frame].selection_rect
        r2 = (sel_rect[0], sel_rect[1], sel_rect[2]-sel_rect[0], sel_rect[3]-sel_rect[1]) # x,y,x_width,y_width
        if r2[2] > 0 and r2[3] > 0:
            pygame.draw.rect(window, (200, 200, 200), r2, 2) # selection rectangle
        pygame.display.update()  # update screen
