
import tkinter as tk
import requests, json, os
from datetime import datetime, timedelta
from pytz import timezone

from tkinter import messagebox
from ctypes import windll
windll.shcore.SetProcessDpiAwareness(1)  # fix blurry text, may shift text position

from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

mainwin = tk.Tk()  # main window
left = 10 # leftmost widgets
top = 20 # top widget
height = 30  # height per row
running = 0  # update timer stopped
haveprices = False

token = 'cl1ujer01qi----------e1r01qinfo7eig'  # finhub free account

def DataChange(*args):  # user entry change, save settings
    try:
        # save data as JSON
        with open('StockAlert.dat', 'w') as fd:
            fd.write(str([blk.GetData() for blk in blklist]).replace("'", '"').replace(' {', '\n{'))
    except:
        pass  # don't crash on settings error

def GetStockName(sym):  # company name
    url = f'https://api.finnhub.io/api/v1/search?q={sym}&token='+token
    res = requests.get(url, verify=False)
    stks = json.loads(res.text)['result']
    stkx = list(filter(lambda s: s['symbol'] == sym, stks))
    if not stkx:
        return 'unknown'
    return stkx[0]['description']

def GetStockPrice(sym):  # latest price
    try:
        global status
        url = f'https://api.finnhub.io/api/v1/quote?symbol={sym}&token='+token
        res = requests.get(url, verify=False)
        stkx = json.loads(res.text)
        print(sym, stkx['c'])
        return stkx['c']
    except Exception as ex:
        print(ex)
        return 0

def GetStockHistory(sym):  # stock price history
    try:
        dtTo = datetime.now()
        dtFrom = dtTo - timedelta(days=30)  # start 30 days ago (22 mkt days)
        tsTo = int(datetime.timestamp(dtTo))
        tsFrom = int(datetime.timestamp(dtFrom))
        print(tsTo, tsFrom)
        url = f'https://finnhub.io/api/v1/stock/candle?symbol={sym}&resolution=D&from{tsFrom}&to={tsTo}&token='+token
        res = requests.get(url, verify=False)
        j = json.loads(res.text)
        print(len(j['t']), len(j['c']))
        return {'date': j['t'], 'close': j['c']}
    except Exception as ex:
        print(ex)

def Beep():  # 3 beeps
    import winsound
    frequency = 2500 # hertz
    duration = 100 # milliseconds
    for x in range(3):
        winsound.Beep(frequency, duration)

def MarketOpen():  # check if market is open - mon-fri 9-4
    tz = timezone('EST')
    dt = datetime.now(tz)
    return dt.weekday() < 5 and (9 <= dt.hour < 16)  # weekday Monday=0

def ShowHelp():
    msg = '''
        Stock Name: \tStock name to check
        Alert Price: \tPrice to trigger alert
        Direction: \tAlert when price crosses down\\up
        Last price: \tStock price at last check
        Percent Gap: \t% difference between stock and alert price
        Alert Flag: \tFlash main window when alert triggered\n
        <Escape> - Exit
    '''
    messagebox.showinfo('Stock Alert Help', msg)

class StockBlock:  # includes widgets and data for single stock

    def __init__(self, sym=None, alertprice=0.0, lastprice='0.0', direction='>', alertflag=True, pos=0):
        # observables
        self.symbol = tk.StringVar(mainwin, sym)
        self.alertprice = tk.DoubleVar(mainwin, alertprice)
        self.lastprice = tk.StringVar(mainwin, lastprice)
        self.direction = tk.StringVar(mainwin, direction)
        self.alertflag = tk.BooleanVar(mainwin, alertflag)
        self.pctgap = tk.DoubleVar(mainwin, 0)
        self.pos = pos
        # add trace for saving settings
        self.symbol.trace_add('write', DataChange)
        self.alertprice.trace_add('write', DataChange)
        self.alertflag.trace_add('write', DataChange)
        self.direction.trace_add('write', DataChange)

    def ToggleDirection(self, *args): # toggle arrow (call\put)
        if self.direction.get() == '<':
            self.direction.set('>')
        else:
            self.direction.set('<')
        self.CheckAlert()

    def CheckAlert(self): # check if stock price passed alert price
        alerted = False
        if self.direction.get() == '>': # call, check if price > alert price
            self.lblLastPrice['bg'] = '#CCFFCC'  # green
            self.lblPctGap['bg'] = '#CCFFCC'  # green
            if float(self.alertprice.get()) < float(self.lastprice.get()):
                alerted = True
        if self.direction.get() == '<': # put, check if price < alert price
            self.lblLastPrice['bg'] = '#CCFFCC'  # green
            self.lblPctGap['bg'] = '#CCFFCC'  # green
            if float(self.alertprice.get()) > float(self.lastprice.get()):
                alerted = True
        if alerted:
            self.lblLastPrice['bg'] = '#FFCCCC'   # red
            self.lblPctGap['bg'] = '#FFCCCC'   # red
            if self.alertflag.get():
                mainwin.attributes('-topmost', 1)  # bring to top
                mainwin.attributes('-topmost', 0)
                Beep()
                for ctr in [1, 200, 400]: # flash main window
                    mainwin.after(ctr, lambda :mainwin.config(bg='red')) # set background red
                    mainwin.after(ctr+100, lambda :mainwin.config(bg='SystemButtonFace')) # back to default grey

    def Draw(self): # create\place widgets
        self.entStock = tk.Entry(mainwin, textvariable=self.symbol)
        self.entStock.place(x=left, y=top+self.pos*height, width=40)
        self.entAlertPrice = tk.Entry(mainwin, textvariable=self.alertprice, justify=tk.RIGHT)
        self.entAlertPrice.place(x=left+50, y=top+self.pos*height, width=40)
        self.lblDirection = tk.Label(mainwin, textvariable=self.direction, font=("Arial", "16", "bold"))
        self.lblDirection.place(x=left + 100, y=top + self.pos * height - 5, width=10)
        self.lblDirection.bind("<Button-1>", self.ToggleDirection) # click arrow to reverse
        self.lblLastPrice = tk.Label(mainwin, textvariable=self.lastprice, anchor='e', bg='#CCFFCC', highlightthickness=1, highlightbackground='grey')  # bg='#98FB98')
        self.lblLastPrice.place(x=left+120, y=top+self.pos*height-2, width=50)
        self.lblPctGap = tk.Label(mainwin, textvariable=self.pctgap, anchor='e', bg='#CCFFCC', highlightthickness=1, highlightbackground='grey')  # bg='#98FB98')
        self.lblPctGap.place(x=left+180, y=top+self.pos*height-2, width=40)
        self.chkAlertFlag = tk.Checkbutton(mainwin, variable=self.alertflag)
        self.chkAlertFlag.place(x=left+225, y=top+self.pos*height-1)

    def ReDraw(self): # move existing widgets
        self.entStock.place(x=left, y=top+self.pos*height, width=40)
        self.entAlertPrice.place(x=left+50, y=top+self.pos*height, width=40)
        self.lblDirection.place(x=left + 100, y=top + self.pos * height - 5, width=10)
        self.lblLastPrice.place(x=left+120, y=top+self.pos*height - 2, width=50)
        self.lblPctGap.place(x=left+180, y=top+self.pos*height - 2, width=40)
        self.chkAlertFlag.place(x=left+225, y=top+self.pos*height - 1)

    def GetPrice(self, sync=True): # get last price
        if sync: # get price
            prc = float(GetStockPrice(self.symbol.get()))
            self.lastprice.set(str('%.2f' % prc))
            gap = int((self.alertprice.get() - prc)/prc*1000)/10  # round 1 digit
            self.pctgap.set(gap) # pct diff between price and alert price
            self.CheckAlert()  # set green\red background
        else: # allow gui update then recall same method
            mainwin.after(100 + self.pos * 20, self.GetPrice) # stagger price request

    def GetData(self): # for saving to setting file
        datax = {
            'symbol': self.symbol.get(),
            'alertprice': self.alertprice.get(),
            'alertflag': [False, True].index(self.alertflag.get()),
            'direction': self.direction.get()
        }
        return datax

def StockAdd(*args): # add stock entry to form
    sbx = StockBlock('GOOG', 100, '0', '>', True, len(blklist))  # default
    sbx.Draw()
    blklist.append(sbx)
    mainwin.geometry("335x" + str(len(blklist)*height+height+20))  # WxH
    mainwin.after(100, SetStatusPosition) # move status bar to bottom
    DataChange()  # save setting file

def StockDelete(*args): # delete empty entries
    global blklist
    pos = 0
    idx = 0
    while idx < len(blklist):
        if blklist[idx].symbol.get(): # active symbol
            blklist[idx].pos = pos
            blklist[idx].ReDraw()
            pos += 1
            idx += 1
        else:  # blank symbol
            blklist[idx].pos = 9999  # move off-screen
            blklist[idx].ReDraw()
            del blklist[idx]  # remove reference

    mainwin.geometry("335x" + str(len(blklist)*height+height+20))  # wxh
    mainwin.after(100, SetStatusPosition) # must resize first
    DataChange() # save settings

def RunUpdate(): # get all stock prices
    global afterid, haveprices
    if haveprices and not MarketOpen():
        mainwin.after(100, lambda: status.set('Market Closed - ' + datetime.now().strftime('%H:%M:%S')))
    else:
        mainwin.after(100, lambda: status.set('Last update: ' + datetime.now().strftime('%H:%M:%S')))
        print('Run Update:', datetime.now())
        for blk in blklist:
            blk.GetPrice(False)
        haveprices = True
    if running:
        afterid = mainwin.after(60000, RunUpdate) # rerun every minute

def ToggleRun(*args): # start\stop stock updates
    global running, afterid
    running = 1-running
    if afterid:
        mainwin.after_cancel(afterid) # cancel update timer
    if running:
        afterid = mainwin.after(1000, RunUpdate) # start updates after 1 second
    # toggle start button appearance
    btnStart['text'] = ['Start', 'Stop'][running]
    btnStart['bg'] = ['lightgreen', 'pink'][running]
    mainwin.title('StockAlert - ' + ['Stopped', 'Running'][running])

def SetStatusPosition(): # status bar at window bottom
    lblStatus.place(x=0, y=mainwin.winfo_height() - 20, width=mainwin.winfo_width())

afterid = '' # timer id for updates

# default list if no settings file
stklist = ['NVDA', 'TSLA', 'SMCI', 'SRPT', 'RH']  # , 'F', 'GM', 'AMZN', 'DELL', 'MCD']

blklist = []
status = tk.StringVar(mainwin, '')
lblStatus = tk.Label(mainwin, textvariable=status, bg='lightyellow')

# buttons
top2 = top
btnStart = tk.Button(mainwin, text='Start', command=ToggleRun, bg='lightgreen')
btnStart.place(x=270, y=top2, width=50)
btnAdd = tk.Button(mainwin, text='Add', command=StockAdd, bg='lightblue')
btnAdd.place(x=270, y=top2+40, width=50)
btnDelete = tk.Button(mainwin, text='Delete\nEmpty', command=StockDelete, bg='lightpink')
btnDelete.place(x=270, y=top2+80, width=50)
btnHelp = tk.Button(mainwin, text='?', command=ShowHelp, bg='white')
btnHelp.place(x=285, y=top2+140, width=20)

# load settings
if os.path.isfile('StockAlert.dat'):
    with open('StockAlert.dat') as f:
        data = json.loads(f.read())
        for i, stk in enumerate(data):
            sb = StockBlock(stk['symbol'], stk['alertprice'], '0', stk['direction'], stk['alertflag'], i)
            sb.Draw()
            blklist.append(sb)
else: # use default list
    for i, stk in enumerate(stklist):
        sb = StockBlock(stk, 100, '0', '>', True, i)
        sb.Draw()
        blklist.append(sb)

status.set('Ready')

mainwin.title('StockAlert - Stopped')
mainwin.geometry("335x" + str(len(blklist)*height+height+20))  # WxH window size
mainwin.minsize(100, top2+200)  # below buttons, can't shrink window smaller

mainwin.after(100, SetStatusPosition)  # must resize first

mainwin.bind_all("<Escape>", lambda x: quit()) # escape exits program
mainwin.mainloop()
