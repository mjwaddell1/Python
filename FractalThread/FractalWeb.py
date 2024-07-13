import pygame, time, threading, json, colorsys, os, sys, requests
from bottle import route, run, template, request
import numpy as np

######################################################
################ web service - start #################
######################################################

# if multiple computers, extract server block to separate script

import psutil, signal
iterations = 1000 # even number, higher value has more detail, longer render time

def QuitServer():
    # Bottle has no way to exit server, must kill server process
    psutil.Process().send_signal(signal.SIGTERM) # kill this process

# https://medium.com/nerd-for-tech/programming-fractals-in-python-d42db4e2ed33
def Mandelbrot(c, z): # calculate single point
   count = 0
   for a in range(iterations):
      z = z**2 + c
      count += 1
      if(abs(z) > 4):
         break
   return count

def MandelbrotWeb(x,y,i): # generate single column
    points = []
    for j in range(len(y)):
        c = complex(x, y[j])
        z = complex(0, 0)
        count = Mandelbrot(c, z)
        points.append(count)
    return points

@route('/') # GET
def index():  # web service only has one endpoint
    if 'quit' in request.params.keys(): # quit signal received
        threading.Timer(1, QuitServer).start() # kill server after 1 second
        return
    dd = json.load(request.body) # x[i], y, i  # input data for single column
    print(dd[2], end='') # column index
    pts = MandelbrotWeb(dd[0], dd[1], dd[2]) # get results for single column
    return template('{{data}}', data=pts) # return result array

# python FractalWeb.py 8181
if len(sys.argv) == 2:  # port number received, start web server
    run(host='localhost', port=int(sys.argv[1])) # loop forever
    quit() # never gets here

####################################################
################ web service - end #################
####################################################

# machine list to handle fractal processing, using localhost for testing
server_list = \
    [
        ('http://localhost', 8181),
        ('http://localhost', 8182),
        ('http://localhost', 8183),
        ('http://localhost', 8184),
        ('http://localhost', 8185),
        ('http://localhost', 8186),
        ('http://localhost', 8187),
        ('http://localhost', 8188),
        ('http://localhost', 8189),
        ('http://localhost', 8190),
        ('http://localhost', 8191),
        ('http://localhost', 8192)
     ]

def StartServers(): # for testing, start local server processes
    print('Start servers...')
    for svr in server_list:
        # start same script, pass in port number
        os.system("start cmd /c python FractalWeb.py " + str(svr[1])) # windows

def StopServers(): # for testing, close local server processes
    print('Stop servers...')
    for svr in server_list:
        try:
            requests.get(f'{svr[0]}:{svr[1]}?quit=1') # send quit signal
        except Exception as ex:
            print('StopServers ', svr, ex)

StartServers() # testing, start local server processes in separate cmd windows

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
            StopServers()
            quit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                StopServers()
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

def GetWebData(x, y, i, svridx): # call web service
    s = json.dumps((x, list(y), i)) # convert array to string
    svr = f'{server_list[svridx][0]}:{server_list[svridx][1]}'
    resp = requests.get(svr, data=s) # process single column
    jsn = resp.json()
    for j, pt in enumerate(jsn):
        # window.set_at((i,j), (0, (count*5) % 200, 0)) # shades of green, more contrast
        # window.set_at((i,j), (0, count/iterations*200, 0)) # shades of green, single scale
        window.set_at((i, j), colors[pt - 1])  # color wheel, screen update done in caller

def MandelbrotSet(x, y): # use web services
    threads = []
    print('Multi Web')
    ctr_start = time.perf_counter()
    svr_idx = 0 # track server
    for i in range(len(x)):
        # call server from background thread, assign single column
        t1 = threading.Thread(target=GetWebData, args=(x[i], y, i, svr_idx)) # each column
        threads.append(t1)
        CheckEvents()  # check quit event
        t1.start()
        svr_idx += 1 # move to next server
        if svr_idx == len(server_list): # all servers processing
            for th in threads:
                th.join() # wait for all threads to finish
            svr_idx = 0
            threads = []
            pygame.display.update() # update screen
        pygame.display.update() # final update
    ctr_stop = time.perf_counter()
    print('Draw Time:', ctr_stop - ctr_start) # 20 seconds
    CheckEvents()  # check quit event

def DrawFractal(fract_rect): # render screen
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

fract_rect_start = [-2.6, -1.5, 1.5, 1.5] # intial fractal boundaries
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
