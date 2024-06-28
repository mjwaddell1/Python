import pygame, time, threading
import numpy as np

pygame.init() # required for screen info
# open full screen
infoObject = pygame.display.Info()
scr_width = infoObject.current_w  #1500
scr_height = infoObject.current_h  #900
window = pygame.display.set_mode((scr_width, scr_height))
pygame.display.set_caption("Fractal")

drag = False # drawing selection rectangle
drawing = False # drawing fractal in progress

def CheckEvents():
    global drag, sel_rect, fract_rect
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
                sel_rect[0], sel_rect[1] = event.pos
                sel_rect[2], sel_rect[3] = 0, 0
            if event.type == pygame.MOUSEBUTTONUP:
                drag = False # done selection
            if event.type == pygame.MOUSEMOTION:
                if drag: # mouse button pressed
                    sel_rect[2], sel_rect[3] = event.pos # adjust selection rectangle
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE: # reset image
                    fract_rect = fract_rect_start[:] # copy
                    sel_rect = [0, 0, 0, 0] # reset selection
                    DrawFractal()
                if event.key == pygame.K_RETURN: # process selection rectangle
                    temp = (fract_rect[0], fract_rect[1], fract_rect[2], fract_rect[3])
                    # new fractal boundaries based on selection rectangle
                    fract_rect[0] = temp[0] + (temp[2] - temp[0]) / scr_width * sel_rect[0]
                    fract_rect[2] = temp[0] + (temp[2] - temp[0]) / scr_width * sel_rect[2]
                    fract_rect[1] = temp[1] + (temp[3] - temp[1]) / scr_height * sel_rect[1]
                    fract_rect[3] = temp[1] + (temp[3] - temp[1]) / scr_height * sel_rect[3]
                    sel_rect = [0, 0, 0, 0] # clear selection rectangle
                    DrawFractal()

# https://medium.com/nerd-for-tech/programming-fractals-in-python-d42db4e2ed33
def mandelbrot(c, z):
   iterations = 100
   count = 0
   for a in range(iterations):
      z = z**2 + c
      count += 1
      if(abs(z) > 4):
         break
   return count

# def mandelbrot_thread(x,y,i):
#     for j in range(len(y)):
#         c = complex(x[i], y[j])
#         z = complex(0, 0)
#         count = mandelbrot(c, z)
#         window.set_at((i,j), (0, (count*7)%200, 0)) # shades of green
#         pygame.display.update()  # each column
#
# threads = []
# def mandelbrot_set(x, y): # use multithreading
#    ctr_start = time.perf_counter()
#    for i in range(len(x)):
#       t1 = threading.Thread(target=mandelbrot_thread, args=(x,y,i)) # each column
#       threads.append(t1)
#       t1.start()
#    for th in threads:
#        th.join() # wait for all threads to finish
#    ctr_stop = time.perf_counter()
#    print('Draw Time:', ctr_stop - ctr_start) # 20 seconds
#    CheckEvents()  # check quit event

def mandelbrot_set(x, y):
   ctr_start = time.perf_counter()
   for i in range(len(x)):
      for j in range(len(y)):
         c = complex(x[i], y[j])
         z = complex(0, 0)
         count = mandelbrot(c, z)
         window.set_at((i,j), (0, (count*7)%200, 0)) # shades of green
         CheckEvents() # check quit event
      pygame.display.update() # each column
   ctr_stop = time.perf_counter()
   print('Draw Time:', ctr_stop - ctr_start) # 10 seconds

fract_rect_start = [-2.6, -1.5, 1.5, 1.5] # intial fractal boundaries
fract_rect = fract_rect_start[:] # for image reset

sfc_fractal = None # store fractal image
def DrawFractal():
    global drawing
    drawing = True
    global sfc_fractal
    # creating our x and y arrays
    x = np.linspace(fract_rect[0], fract_rect[2], scr_width)
    y = np.linspace(fract_rect[1], fract_rect[3], scr_height)
    # create our mandelbrot set
    mandelbrot_set(x, y) # generate fractal image
    sfc_fractal = window.copy() # store fractal image for quick redraw
    drawing = False

DrawFractal() # initial screen

sel_rect = [0, 0, 0, 0] # selection rectangle

if __name__ =="__main__":
    while True: # run until escape pressed
        CheckEvents() # mouse/escape/space
        window.fill((0, 0, 0))  # clear screen
        window.blit(sfc_fractal, (0, 0)) # redraw fractal image first
        r2 = (sel_rect[0], sel_rect[1], sel_rect[2]-sel_rect[0], sel_rect[3]-sel_rect[1]) # x,y,x_width,y_width
        pygame.draw.rect(window, (200, 200, 200), r2, 2) # selection rectangle
        pygame.display.update()  # update screen
