import warnings, urllib3
import datetime, requests
from time import sleep

warnings.simplefilter(action='ignore', category=Warning) # suppress requests warning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning) # suppress SSL warning

# --- Overview ---
# Get stocks that have a recent jump on high volume, then fall to SMA 50 on low volume
# These stocks will probably bounce back to new high

mbkey = '12|ZAozwUlyRXXXXXXizhI293OFPTG'  # https://mboum.com/api/welcome, business account
sskey = '58f18c4b-xxxxx-04465a33199b'  # https://github.com/yongghongg/stock-symbol

logtxt = ''
curtime = str(datetime.datetime.now()).replace(' ','_').replace('-','').replace(':','')[:15]

def printx(*args): # print to screen and log file
    global logtxt
    print(*[str(x) for x in args]) # screen
    logtxt += ' '.join([str(x) for x in args]) + '\n'
    with open('StockRetraceCheck_'+curtime+'.log', 'w') as f: # StockRetraceCheck_20251010_155438.log
        f.write(logtxt)  # write full log to log file

def rnd2(val):  # round 2 decimal places
    return str(int(val * 100) / 100.0)

def GetStockNames(): # stock name\exchange, could probably just run this once, stock list rarely changes
    printx('Get Stock Names...')
    # get all stock names in US
    # https://stock-symbol.herokuapp.com/api/
    url = 'https://stock-symbol.herokuapp.com/api/'
    headers = {'x-api-key': sskey}
    params = {'market': 'US'}  # , 'index': index}
    StockInfo = requests.get(url + 'symbols', params=params, headers=headers, verify=False).json()
    with open('StockList.json', 'w') as f:
        f.write(str(StockInfo))
    names = StockInfo['data'][0]['quotes']
    d = {n['symbol']:{'name':n['longName'],'exchange':n['exchange']} for n in names} # exchange needed for email link
    return d

def GetStockHistory(sym):  # get history from mboum, business account
    url = None
    try:
      # 1m | 5m | 15m | 30m | 1h | 1d | 1wk | 1mo | 3mo
      iv = '1d'  # 5 yrs data o/h/l/c
      # url='https://mboum.com/api/v1/hi/history/?symbol=F&interval=1d&diffandsplits=true&apikey=demo'
      # url = 'https://mboum.com/api/v1/hi/history/?symbol=' + sym + '&interval=' + iv + '&diffandsplits=true&apikey=' + mbkey
      url = 'https://api.mboum.com/api/v1/markets/stock/history/?symbol=' + sym + '&interval=' + iv + '&diffandsplits=true&apikey=' + mbkey
      hdrs = {
          "User-Agent": "Mozilla/5.0,(Windows NT 10.0; Win64; x64),AppleWebKit/537.36,(KHTML, like Gecko),Chrome/110.0.0.0,Safari/537.36"}
      jsn = requests.get(url, verify=False, headers=hdrs).json()
      if jsn['meta']['instrumentType'] != 'EQUITY':
          return None  # we only want equity stocks, no ETFs or crypto
      hist = []
      for k in jsn['body'].keys(): # all dates (unix date)
          if not k.isnumeric(): continue # "events"
          hist.append((int(k), jsn['body'][k]['date'], jsn['body'][k]['open'], jsn['body'][k]['close'], jsn['body'][k]['volume']))
      # sort by date
      hist.sort(key=lambda x: x[0])
      return hist
    except Exception as ex:
      printx('\nGetStockHistory', '\n', ex, '\n', url, '\n', sym)
      return None

def GetRowData(row):  # FinViz, parse single data row
    cols = row.split('</td><td')  # each column
    data = []
    for i in [1, 2, 8, 9]:  # columns - symbol, name, price, pct change
        td = cols[i]
        td = td.replace('</span>', '').replace('%', '').replace('><', '')
        idx = td.rfind('>', 0, len(td) - 2)
        idx2 = td.rfind('<')
        dp = td[idx + 1:idx2]
        data.append(dp)
    # return dictionary   # ['AAON', 'AAON Inc.', 64.06, 8.58]
    # print(data[:4])
    if data[2] == '-' or data[3] == '-' or '-' in data[0]: # missing price or dash in ticker (AIIA-U)
        return None
    return {'Ticker': data[0], 'Name': data[1], 'Price': float(data[2]), 'ChangePct': float(data[3])}

def GetFinVizStocksTbl(filters=None):  # FinViz, scrape main table
    if not filters:
        filters = 'sh_opt_option,sh_price_o50,ta_volatility_mo3'  # default

    hdr = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) "
                      "Chrome/23.0.1271.64 Safari/537.11"
    }

    cnt = 1  # first stock in table
    stks = []  # final list
    total = 0  # total stock count
    while True:  # all pages
        # get finviz table, Overview (v=111), start with first stock (r=1)
        url = f'https://finviz.com/screener.ashx?v=111&f={filters}&r={cnt}'
        if cnt == 1:
            printx(url)
            print('FinViz: ', end='')
        # url = 'https://finviz.com/screener.ashx?v=111&f=sh_opt_option,sh_price_o50,ta_volatility_mo3&r=1'
        print('#', end='', flush=True)
        rsp = requests.get(url, headers=hdr)
        if cnt == 1:  # first page, get total
            if rsp.text.find('>0 Total<') > 0: return []  # no stocks passed filter
            idx = rsp.text.find('#1 /')
            if idx == -1: return []  # total not found
            total = int(rsp.text[idx:idx + 13].split(' ')[2])  # #1 / 347 Total
        idx = rsp.text.find('</thead>')  # end of table headers
        if idx == -1: return []  # header not found
        idx2 = rsp.text.find('<table ', idx)  # end of data rows
        if idx2 == -1: return []  # tag not found
        txt = rsp.text[idx:idx2]
        lst = txt.split('\n')[1:-1]
        for row in lst:
            if row.startswith('<td '):  # stock data row
                dr = GetRowData(row)
                if dr: stks.append(dr)
                cnt += 1
        if cnt >= total:
            printx(url+'\nFinViz stocks:\n' + '\n'.join([str(stk) for stk in stks]))
            print('')
            return stks
        sleep(0.1)  # must pause between pages


# https://finviz.com/screener.ashx?v=111&f=ta_highlow52w_nh,ta_sma20_pa10,fa_netmargin_pos,fa_epsyoy_pos&r=1
# remember to add comma to each item
filtersFV = [  # finviz, initial filter for stocks, can have multiple filter lists
    ('fa_epsyoy_pos,'      # earnings increase year/year
     'fa_netmargin_pos,'   # positive net margin
     'ta_sma200_sb50,'     # SMA 50 > SMA 200
     'sh_price_o5,'        # price over $5
     'geo_usa,'            # US companies
     'an_recom_buybetter,' # analysts recommend buy
     'ipodate_more1,'      # IPO over 1 year ago
     'fa_epsyoyttm_pos,'   # earnings increase last 12 months
     'ta_sma50_pb')        # price below SMA 50
]

def GetStockList():
    allStks = []
    syms = [] # for dup check
    for f in filtersFV: # run all filters, merge results
        stks = GetFinVizStocksTbl(f) # single filter
        for stk in stks:
            if stk['Ticker'] not in syms: # prevent repeats
                syms.append(stk['Ticker'])
                allStks.append(stk)
    allStks.sort(key=lambda s: s['Ticker']) # sort by stock symbol
    return allStks # combined list

def GetStockName(stk):
    if stk in stknames:
        return stknames[stk]
    return {'name': '-Unknown-', 'exchange': ''}

def GetSingleEMA(arry, idx, smastart, multiplier, period):
    # if len(arry) == period: # first entry
    #     print(arry, idx, smastart, multiplier)
    if len(arry) == 1:
        return smastart
    return arry[-1][idx]*multiplier + (1-multiplier)*GetSingleEMA(arry[:-1], idx, smastart, multiplier, period)

def GetSMAEMA(arry, idx, period, smooth=2): # get SMA and EMA for stock
    # assume array starts with earliest date
    # set starting entries -1 because can't average less than period
    #print('======= SMA =======')
    smalst = [-1 for _ in range(period-1)]
    for i in range(period-1,len(arry)):
        avg = sum([r[idx] for r in arry[i-period+1:i+1]])/period
        #print('SMA',avg,arry[i])
        smalst.append(avg)
    multiplier = smooth/(period+1) # smooth=2 is most common, use higher value for closer line, lower value for smoother line
    #print('======= EMA =======')
    emalst = [-1 for _ in range(period*2-2)] # EMA requires SMA to start, so double (minus 1) invalid entries
    for i in range(period*2-1, len(arry)):
        ema = GetSingleEMA(arry[i-period:i],3,smalst[i-period], multiplier, period) # first ema is sma
        #print('EMA', ema, arry[i])
        emalst.append(ema)
    return smalst, emalst

# for period=5
# 012345678 day
# ----S   SMA (first 4 are invalid)
# --------E   EMA (first 8 are invalid)

# main script
stkdict = {}
stknames = GetStockNames() # US market, all stocks
stock_list = GetStockList()
if not len(stock_list):
    printx('No stocks from FinViz') # no stocks passed filter
    quit()
printx('FinViz', len(stock_list), 'stocks')
baselink = 'https://www.google.com/finance/quote/' # for quote link in email
stock_list = [s['Ticker'] for s in stock_list] # just tickers
for stk in stock_list: # check each stock
    print(stk+' ', end='', flush=True)
    name = GetStockName(stk)
    if name['name'][0] == '-': # probably ETF
        continue
    histall = GetStockHistory(stk) # full stock history # array of tuples [(dateunix, datestring, open, close, volume),...]
    if not histall:
        print('\n', stk, 'histall=None')
        continue
    if len(histall) < 550: # need at least (SMA+EMA+6mo) = (200+200+125) = 525 days
        continue # new stock, skip
    # calculate moving averages
    SMA050, EMA050 = GetSMAEMA(histall, 3, 50) # stock price MA
    SMA150, EMA150 = GetSMAEMA(histall, 3, 150)
    SMA200, EMA200 = GetSMAEMA(histall, 3, 200)
    SMA050Vol, EMA050Vol = GetSMAEMA(histall, 4, 50, 4) # volume MA
    price = histall[-1][3] # last entry in history (closing price)
    # check if price < EMA050
    if price > EMA050[-1]: # latest entry
        continue # price over EMA 50
    # check if price > EMA050 - 5%
    if price < EMA050[-1]*.95: # latest entry
        continue # price too far below EMA 50
    # check if SMA050 > SMA150 > SMA200
    if SMA050[-1] < SMA150[-1] or SMA150[-1] < SMA200[-1]:
        continue # failing stock
    # check if price > SMA150
    if price < SMA150[-1]:
        continue # failing stock
    # scan back 6 months (125 market days) for price peak
    peakprice = 0
    peakvol = 0 # vol EMA
    peakdate = ''
    peakidx = 0
    for i in range(125):
        if histall[-i][3] > peakprice:
            peakprice = histall[-i][3]
            peakvol = EMA050Vol[-i]
            peakdate = histall[-i][1] # 2025-10-16
            peakidx = i
    if peakidx == 124:
        continue  # peak was at start of 6mo range, skip
    # if EMAVolPeak > EMAVolCur*1.2: good stock
    if peakvol < EMA050Vol[-1] * 1.2: # vol at peak 20% higher than retracement vol
        continue # volume difference not big enough
    printx('\n >>> ', stk, peakdate, GetStockName(stk)) # stock fits pattern

print('\n-- Done --')
