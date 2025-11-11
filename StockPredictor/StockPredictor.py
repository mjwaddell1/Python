import requests, csv, json, urllib3, os, time, math, warnings, shelve, copy
from datetime import datetime
import yfinance as yf

warnings.simplefilter(action='ignore', category=FutureWarning) # pandas
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import torch
import torch.nn as nn
from torch.utils.data import DataLoader

# --- Overview ---
# This script loads stock history data from various sources and
#   uses the data as input to a neural network for forcasting stock movement
# Spoiler alert: the model did not produce accurate results and has limited predictive value
# > Main script steps:
#   Get stock data (daily returns, quarterly earnings\dividends\revenue\profit margin) from web
#   Get economic information for training day - stock sector, month, election cycle, yield curve
#   Store stock data to json files
#   Load stock data from json files (web not needed)
#   Generate sample\prediction collection
#   Store s\p data in shelve file (single file)
#   Load s\p data from shelve file
#   Create model
#   Run training

# --- Notes ---
# The sample data is from stocks in the S&P 500 across 5 years
# For each stock, weekly returns a generated
# A monthly return is calculated for the month following the sample (this is the forcast)
# A sample is 100 weeks (2 years of market days)
# The sample range is shifted 1 week to create the next sample
# Total shifts per stock is (5yrs-2yrs-1month)x(50 weeks) = 140
# Total samples (5 years) = (stock count) x (shift count) = 500x140 = 70000
# Due to additional SP500 stocks, actual sample count is 71336
# A single sample has 216 values (stock returns, SP returns, economic data)
# Based on initial testing, no model could effectively predict stock direction
# At the end of the script, there are nested loops to run multiple model configurations
#     I estimate it will take over 50 days to run all configurations



###########################################
#############   Gather Data   #############
###########################################


# https://financialmodelingprep.com/api/v3/historical-price-full/HBAN?apikey=tuTqK1dbVIOaGDV9X7fOO5guCKfBUyOR
# revenue and profit, last 4 qtrs
# https://mboum.com/api/v1/qu/quote/income-statement/?symbol=F&apikey=o6eB0qL4XcBX4tHXXXXXXXXXXXXWLnOpr1HjNhkpfV5G8Kj96kg

fmpKey = "tuTqK1dbVIOXXXXXXXCKfBUyOR" # https://site.financialmodelingprep.com/developer/docs/dashboard, free account
simFinKey = '9eb2f5d7-ef8d-XXXXXXXXX-78c4a37c615a' # https://app.simfin.com/data-api, free account mjwaddell
simFinKey = '48a35cc6-65dc-XXXXXXXX-a295b5051268' # https://app.simfin.com/data-api, free account mike01
mbKey = 'o6eB0qL4XcBX4tHXXXXXXXXXXXXWLnOpr1HjNhkpfV5G8Kj96kg'  # https://mboum.com/api/welcome, basic account

# --url 'https://backend.simfin.com/api/v3/companies/statements/compact?ticker=AAPL&statements=BS&period=Q1,Q2,Q3,Q4' \
# --header 'Authorization: 9ec2f5d7-ef8d-6d1e-b014-78c4a27c615a' \
# --header 'accept: application/json'

def ConvertDate(dateStr): # convert to date object
    if dateStr[2] == '-': # 01-01-2019
        dateStr = f'{dateStr[6:]}-{dateStr[3:5]}-{dateStr[:2]}'
    return datetime.fromisoformat(dateStr)  # '2024-01-01')

def LoadStockList(): # all stock data for S&P 500
    # get SP500 symbol list
    stocks = {}
    # https://github.com/datasets/s-and-p-500-companies/blob/main/data/constituents.csv
    with open(r'StockData\SP500StockList.csv') as f:
        rdr = csv.DictReader(f)
        for row in rdr:
            stocks[row['Symbol']] = row # Symbol,Security,GICS Sector,GICS Sub-Industry,Headquarters Location,Date added,CIK,Founded
        return stocks

def LoadYieldRates(): # yield curve history
    rates = {}
    # https://home.treasury.gov/interest-rates-data-csv-archive
    with open(r'StockData\yield-curve-rates-1990-2023.csv') as f:
        rdr = csv.DictReader(f)
        for row in rdr:
            # fix date 12/29/23 -> 2023-12-29
            mo, dy, yr = [int(d) for d in row['Date'].split('/')]
            if yr >= 60:
                yr += 1900
            else:
                yr += 2000
            rates[f'{yr}-{mo}-{dy}'] = row  # Date,1 Mo,2 Mo,3 Mo,4 Mo,6 Mo,1 Yr,2 Yr,3 Yr,5 Yr,7 Yr,10 Yr,20 Yr,30 Yr
        return rates

def GetYieldDiff(rates, dt): # 10yr - 1yr bond
    allDates = sorted([k for k in rates.keys()], reverse=True) # start at latest date
    for d in allDates:
        if d <= dt:
            return float(rates[d]['10 Yr']) - float(rates[d]['1 Yr'])
    print('Rate Not Found -', dt)
    return 0.0

def GetDividendHistoryYF(stks, skip=[]): # yahoo finance
    stk = None
    try:
        data = {}
        for stk in stks:
            print('.', end='', flush=True)
            if stk in skip: continue
            if os.path.isfile(f'StockData/{stk}_Dividends.json'): continue # already done
            hist = yf.ticker.Ticker(stk) # yahoo
            div = {}
            for k in hist.dividends.keys():
                div[str(k)[:10]] = hist.dividends[k]
            with open(f'StockData/{stk}_Dividends.json','w') as f:
                json.dump(div, fp=f)
            data[stk] = div
            time.sleep(.1)
        print()  # carriage return
        return data
    except Exception as ex:
        print('\nGetDividendHistory', '\n', ex, '\n', stk)

def LoadDividendHistory(stks): # load from json files
    data = {}
    for stk in stks:
        print('.', end='', flush=True)
        file = f'StockData/{stk}_Dividends.json'
        if not os.path.isfile(file): continue
        with open(file) as f:
            hist = json.load(f)
        data[stk] = hist
    print() # carriage return
    return data

def GetDailyHistory(stks, skip=()): # daily returns, from web (mboum), save to json files
    url = stk = None
    try:
        data = {}
        for stk in stks:
            print('.', end='', flush=True)
            if stk in skip: continue
            if os.path.isfile(f'StockData/{stk}_Daily.json'): continue
            url = f'https://mboum.com/api/v1/hi/history/?symbol={stk}&interval=1d&diffandsplits=true&apikey={mbKey}'
            hist = requests.get(url).json()['data']
            daily = {}
            lastKey = None # mboum does not have change pct in data, must compare days
            for hKey in hist.keys():
                if not lastKey: # first record, can't calc change
                    lastKey = hKey
                    continue
                h = hist[hKey]
                hp = hist[lastKey] # previous day
                chgPct = (h['close'] - hp['close'])/hp['close']
                daily[h['date']] = {'price':h['close'], 'changepct':chgPct, 'volume':h['volume']}
                lastKey = hKey
            with open(f'StockData/{stk}_Daily.json','w') as f:
                json.dump(daily, fp=f)
            data[stk] = {'daily': daily}
            time.sleep(.1)
        print() # carriage return
        return data
    except Exception as ex:
        print('\nGetDailyHistory', '\n', ex,'\n',url,'\n',stk)

def GetDailyHistoryFMP(stks, skip=[]): # from web, save to json files # free account max 250 calls/day
    url = stk = None
    try:
        data = {}
        for stk in stks:
            print('.', end='', flush=True)
            if stk in skip: continue
            if os.path.isfile(f'StockData/{stk}_Daily.json'): continue
            url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{stk}?apikey={fmpKey}"
            hist = requests.get(url).json()['historical']
            daily = {}
            for h in hist:
                daily[h['date']] = {'changepct':h['changePercent'], 'volume':h['volume']}
            with open(f'StockData/{stk}_Daily.json','w') as f:
                json.dump(daily, fp=f)
            data[stk] = {'daily': daily}
            time.sleep(.1)
        print() # carriage return
        return data
    except Exception as ex:
        print('\nGetDailyHistoryFMP', '\n', ex,'\n',url,'\n',stk)

def LoadDailyHistory(stks): # load from json files
    data = {}
    for stk in stks:
        print('.', end='', flush=True)
        file = f'StockData/{stk}_Daily.json'
        if not os.path.isfile(file): continue
        with open(file) as f:
            hist = json.load(f)
        # fix date format:  22-04-2019 -> 2019-04-22
        hist2 = {}
        for k in hist.keys():
            hist2[f'{k[6:]}-{k[3:5]}-{k[:2]}'] = hist[k] # 22-04-2019 -> 2019-04-22
        data[stk] = {'daily': hist2}
    print() # carriage return
    return data

def GetEarningHistory(stks, skip=[]):  # from web, save to json files, earnings history quarterly, includes actual and estimate
    url = stk = None
    try:
        data = {}
        for stk in stks:
            print('.', end='', flush=True)
            if stk in skip: continue
            # if os.path.isfile(f'StockData/{stk}_Earnings.json'): continue
            # https://mboum.com/api/v1/qu/quote/earnings/?symbol=AAPL&apikey=o6eB0qL4XcBX4tHdyrXXXXXXXXXXXXXXXXXXXXjNhkfpV5G8Kj96kg
            url = 'https://mboum.com/api/v1/qu/quote/earnings/?symbol=' + stk + '&apikey=' + mbKey
            rsp = requests.get(url, verify=False).json()
            earnings = rsp["data"]["earningsChart"]["quarterly"] # includes estimate and actual, last 4 qtrs
            tmp = {}
            for e in earnings:
                qtr,yr = e['date'].split('Q')
                qtr = 'Q' + qtr
                if not yr in tmp.keys():
                    tmp[yr] = {}
                if not qtr in tmp[yr].keys():
                    tmp[yr][qtr] = {}
                tmp[yr][qtr] = {'actual': e['actual']['raw'], 'estimate': e['estimate']['raw']}
            with open(f'StockData/{stk}_Earnings.json','w') as f:
                json.dump(tmp, fp=f)
            data[stk] = {'earnings': tmp}
            time.sleep(.1)
        return data
    except Exception as ex:
        print('\nGetEarningHistory', '\n', ex,'\n',url,'\n',stk)

def LoadEarningHistory(stks): # load from json files
    data = {}
    for stk in stks:
        print('.', end='', flush=True)
        file = f'StockData/{stk}_Earnings.json'
        if not os.path.isfile(file): continue
        with open(file) as f:
            hist = json.load(f)
        data[stk] = {'earnings': hist}
    print() # carriage return
    return data

def GetFundamentalHistory(stks, skip=[]): # from web (simfin), save to json files
    url = stk = None
    data = {}
    for stk in stks:
        print(stk + ' ', end='', flush=True)
        if stk in skip: continue
        if os.path.isfile(f'StockData/{stk}_Fundamentals.json'): continue
        # profit\loss (PL) - https://simfin.readme.io/reference/statements-1 - get also get BS, CF, derived (ratios)
        url = 'https://backend.simfin.com/api/v3/companies/statements/compact?ticker=' + stk + '&statements=PL&period=Q1,Q2,Q3,Q4'
        rsp = requests.get(url, verify=False, headers={'Authorization': simFinKey}).json()
        if not len(rsp) or not len(rsp[0]['statements']):
            print('\n', stk, '\n', url, '\n', 'Response:', rsp)
            continue
        cols = rsp[0]['statements'][0]['columns'] # data is split into column array and data array
        if not 'Revenue' in cols and not 'Net Revenue' in cols:
            print('\nMissing Net\Revenue:', stk)
            continue # skip stock
        if 'Revenue' in cols:
            colRev = cols.index('Revenue') # col 8
        else:
            colRev = cols.index('Net Revenue') # col 8
        colPer = cols.index('Fiscal Period') # col 0  quarter: Q1 Q2 Q3 Q4
        colYr = cols.index('Fiscal Year') # col 1
        colInc = cols.index('Net Income') # col 62
        # col_prof = cols.index('Gross Profit') # col 16
        tmp = {}
        for d in rsp[0]['statements'][0]['data']:
            if not d[colYr] in tmp.keys():
                tmp[d[colYr]] = {}
            tmp[d[colYr]][d[colPer]] = {'revenue':d[colRev], 'income':d[colInc]}
        with open(f'StockData/{stk}_Fundamentals.json','w') as f:
            json.dump(tmp, fp=f)
        data[stk] = {'fundamentals': tmp}
        time.sleep(5)
    print() # carriage return
    return data

def GetFundamentalHistoryMulti(stks, skip=[]): # multiple stocks\statements per call, from web, save to json files
    url = stk = None
    data = {}
    if len(stks)%2 == 1: # odd stock count
        stks.append(stks[-1]) # same stk twice
    stkPairs = []
    for i in range(0,len(stks),2):
        stkPairs.append((stks[i], stks[i+1])) # get data, 2 stocks at a time

    for stk in stkPairs:
        pairUS = f'{stk[0]}_{stk[1]}'
        pairComma = f'{stk[0]},{stk[1]}'
        print(pairUS + ' ', end='', flush=True)
        if stk in skip: continue
        if os.path.isfile(f'StockData/{pairUS}_Fundamentals.json'): continue
        # profit\loss (PL) - https://simfin.readme.io/reference/statements-1 - get also get BS, CF, derived (ratios)
        url = 'https://backend.simfin.com/api/v3/companies/statements/compact?ticker=' + pairComma + '&statements=DERIVED,PL,CF,BS&period=Q1,Q2,Q3,Q4'
        rsp = requests.get(url, verify=False, headers={'Authorization': simFinKey}).json()
        with open(f'StockData/{pairUS}_Fundamentals.json','w') as f:
            json.dump(rsp, fp=f)
        time.sleep(2)

def SplitFundFile(fname): # split multi file into separate files
    print(fname)
    with open(fname) as f:
        j = json.load(f)

    for stkData in j: # file has multiple stocks
        stk = stkData['ticker'] # stock symbol
        print(stk)
        derived = pl = bs = cf = None # statements
        if len(stkData['statements']) == 0: continue
        for st in stkData['statements']:
            if st['statement'] == 'DERIVED': derived = st
            if st['statement'] == 'PL': pl = st
            if st['statement'] == 'CF': cf = st
            if st['statement'] == 'BS': bs = st
        if not derived or not pl: continue
        col_pm  = derived['columns'].index('Net Profit Margin')
        col_eps = derived['columns'].index('Earnings Per Share, Basic')
        col_div = derived['columns'].index('Dividends Per Share')
        col_stk = bs['columns'].index('Common Stock')
        if 'Revenue' in pl['columns']:
            colRev = pl['columns'].index('Revenue')
        else:
            colRev = pl['columns'].index('Net Revenue')
        vals = {}
        for blk in derived['data']:
            if not blk[1] in vals.keys(): # year
                vals[blk[1]] = {}
            vals[blk[1]][blk[0]] = {'Profit Margin':blk[col_pm], 'EPS':blk[col_eps], 'Dividend':blk[col_div]}
        for blk in pl['data']:
            if not blk[1] in vals.keys(): # year
                vals[blk[1]] = {}
            if not blk[0] in vals[blk[1]].keys():
                vals[blk[1]][blk[0]] = {}
            vals[blk[1]][blk[0]]['Revenue'] = blk[colRev]
        for blk in bs['data']:
            if not blk[1] in vals.keys(): # year
                vals[blk[1]] = {}
            if not blk[0] in vals[blk[1]].keys():
                vals[blk[1]][blk[0]] = {}
            vals[blk[1]][blk[0]]['Share Count'] = blk[col_stk]
        with open(f'StockData/{stk}_Fundamentals.json', 'w') as f:
            json.dump(vals, fp=f)

def ParseFundamentalFiles(): # split bulk files
    for f in os.listdir('StockData'):
        if len(f.replace('_','_'*9)) > 32 and 'Funda' in f: # stk1_stk2_Fundamentals.json
            SplitFundFile('StockData/' + f)

def LoadFundamentalHistory(stks):  # load from json files
    data = {}
    for stk in stks:
        print('.', end='', flush=True)
        file = f'StockData/{stk}_Fundamentals.json'
        if not os.path.isfile(file): continue
        with open(file) as f:
            fun = json.load(f)
        data[stk] = {'fundamentals': fun}
    print()  # carriage return
    return data

def GetShareCounts(stks, skip=()): # must do separately with mbaum, simfin returns null as share count
    data = {}
    for stk in stks:
        print(stk, end=' ', flush=True)
        if stk in skip: continue
        url = f'https://mboum.com/api/v1/qu/quote/statistics/?symbol={stk}&apikey={mbKey}'
        rsp = requests.get(url).json()
        data[stk] = rsp['data']['sharesOutstanding']['raw']
        print(data[stk])
        time.sleep(1)
    with open('StockData/ShareCounts.json','w') as f:
        json.dump(data, f)

def LoadShareCounts(): # all stocks from single file, most recent count
    with open('StockData/ShareCounts.json') as f:
        return json.load(f)

def GetStockDataFromWeb(stks): # download stock data and save to json files
    print('Get Daily Data...')
    GetDailyHistory(stks)
    GetDailyHistory(['SPY']) # SP500 index
    print('Get Fundamental Data...')
    GetFundamentalHistory(stks)
    print('Get Earnings Data...')
    GetEarningHistory(stks, skip=['FOX','NWS']) # skip bad data
    print('Get Dividends Data...')
    GetDividendHistoryYF(stks, skip=[])

def LoadStockData(stks, stockInfo): # from data json files
    print('Load Daily Data...')
    daily = LoadDailyHistory(stks)
    # dailySPY = LoadDailyHistory(['SPY'])
    print('Load Fundamental Data...')
    fundamentals = LoadFundamentalHistory(stks)
    # print('Load Earnings Data...')
    # earnings = LoadEarningHistory(stks)
    print('Load Dividends Data...')
    dividends = LoadDividendHistory(stks)
    shareCounts = LoadShareCounts()
    stockData = {}
    for stk in stks: # group stock data into single collection
        if stk in daily.keys() and stk in fundamentals.keys():
            stockData[stk] = {'info': stockInfo[stk], 'daily': daily[stk]['daily'],
                               'fundamentals': fundamentals[stk]['fundamentals']}
            stockData[stk]['info']['Share Count'] = shareCounts[stk]
    return stockData


########################################################
##########   Create Samples for training   #############
########################################################

def CheckDates(stockData): # check all stocks for missing dates
    allkeys = []
    for stk in stockData.keys():
        if len(allkeys) == 0:
            allkeys = stockData[stk]['daily'].keys()
            continue
        for k in stockData[stk]['daily'].keys():
            if not k in allkeys:
                print('Missing key:', stk, k)

def SetRatios(stk, year, qtr, stockData, fundData): # convert EPS\dividend\revenue to percent (of price)
    # need share price at qtr end
    qtr_dates = [None, ('03','31'), ('06','30'), ('09','30'), ('12','31')] # Q1 - Q4
    qtr_date = f'{year}-{qtr_dates[qtr][0]}-{qtr_dates[qtr][1]}'
    price = 0
    for d in sorted(stockData['daily'].keys(), reverse=True): # start at latest
        if d <= qtr_date:
            price = stockData['daily'][d]['price']
    fundData['EPS'] = fundData['EPS'] / price  # percent price
    fundData['Dividend'] = fundData['Dividend'] / price  # percent price
    fundData['Revenue'] = fundData['Revenue'] / stockData['info']['Share Count'] / price  # per share
    if fundData['EPS'] > 1000: fundData['EPS'] = 0 # bad data AON
    if fundData['Dividend'] > 1000: fundData['Dividend'] = 0 # bad data AON
    return fundData

def GetTrailingPL(stk, stockData, dt, cnt=3): # last 3 PL statements for stock
    fundData = stockData['fundamentals']

    # get available qtrs, may not be most recent quarter
    availQtrs = []
    for yr in fundData:
        for qtr in fundData[yr]:
            availQtrs.append(f'{yr}{qtr}')
    availQtrs.sort() # sometimes years out of order

    # get latest quarter based on date
    dt_obj = datetime.fromisoformat(dt)
    year, month, day = dt_obj.year, dt_obj.month, dt_obj.day
    md = month * 100 + day
    if md >= 1001: qtr = 4
    elif md >= 701: qtr = 3
    elif md >= 401: qtr = 2
    else: qtr = 1

    # get previous quarters (if available)
    prevQtrs = []
    while True:
        qtr -= 1 # moving backwards from current quarter
        if qtr == 0:
            year -= 1
            qtr = 4
        if f'{year}Q{qtr}' < min(availQtrs): break # passed available quarters
        if f'{year}Q{qtr}' in availQtrs:
            fd = fundData[str(year)]['Q'+str(qtr)]
            for k in ["Profit Margin", "EPS", "Dividend", "Revenue"]:
                if not k in fd.keys(): fd[k] = 0
                if not fd[k]: fd[k] = 0 # no dividend (null)
            fdNew = copy.deepcopy(fd) # else existing object gets updated
            SetRatios(stk, year, qtr, stockData, fdNew) # set values based on stock price
            prevQtrs.append(fdNew) # revenue \ profit \ eps \ dividend
        if len(prevQtrs) == cnt: break # got last 3 quarters
    if len(prevQtrs) != cnt:
        print('Error GetTrailingPL', stk, 'Cnt', len(prevQtrs))
    return prevQtrs # returns qtrs

def CreateSamples(stockData, rates): # create inputs for training, return numpy array
    print('Create Samples...')

    rates = LoadYieldRates() # bond yields
    # find min\max price date
    minDate = datetime.fromisoformat('2000-01-01')
    maxDate = datetime.fromisoformat('2030-01-01')
    cd = ConvertDate
    for stk in stockData.keys():
        allDates = [cd(k) for k in stockData[stk]['daily'].keys()]
        stkMin = min(allDates)
        stkMax = max(allDates)
        if stkMin > minDate: minDate = stkMin
        if stkMax < maxDate: maxDate = stkMax
    minDate = str(minDate)[:10] # date only, to match data keys
    maxDate = str(maxDate)[:10]
    print(f'min {minDate}  max {maxDate}')
    CheckDates(stockData) # data check okay

    # create list of market dates for easy traversal, use IBM date list
    allDates = []
    for dt in stockData['IBM']['daily'].keys():
        if dt >= minDate and dt <= maxDate:
            if not dt in allDates:
                allDates.append(dt)
    allDates.sort() # from earliest date

    samples = [] # all stocks x all shifts, sample is tuple: (features, outret), outret is return for following month (20 days)
    predictions = [] # return for following month (label)
    groupSize = 5 # days (1 week)
    groupCnt = 100 # 2 years (market days)
    forGroupSize = 20 # 1 month, forcast return
    sampleRetLen = groupCnt * groupSize + forGroupSize
    shiftCnt = (len(allDates) - sampleRetLen)//groupSize + 1 # total shifts possible in date range
    lastStk = ''
    for stk in stockData.keys():
        if stk == 'SPY': continue # index ETF, not actual stock
        if stk != lastStk:
            print(stk, end=' ', flush=True)
            lastStk = stk
        for shiftCtr in range(shiftCnt):
            curSample = []
            stkReturns = [] # weekly returns
            spReturns = [] # weekly returns
            dateIndex = shiftCtr * groupSize # start date for this shift
            for ctr in range(groupCnt): # 0-99, 100 weeks, 2 years
                # total return for day group (week), multiply daily returns
                ret = math.prod([1 + stockData[stk]['daily'][allDates[idx]]['changepct']
                                 for idx in range(dateIndex,dateIndex+groupSize)]) - 1
                stkReturns.append(ret) # append return for the week
                spRet = math.prod([1 + stockData['SPY']['daily'][allDates[idx]]['changepct']
                                    for idx in range(dateIndex,dateIndex+groupSize)]) - 1
                spReturns.append(spRet) # append return for the week
                dateIndex += groupSize # shift 1 week
            fundData = GetTrailingPL(stk, stockData[stk], allDates[dateIndex]) # previous 3 revenue\profit\eps\dividend
            checkDate = allDates[dateIndex] # end of sample, start of forcast
            month = int(checkDate[5:7]) # 2012-10-03 -> 10
            year = int(checkDate[:4]) # 2012-10-03 -> 2012
            electionCycle = (year - 1900) % 4  # 0-3, 0 is election year
            yieldDiff = GetYieldDiff(rates, checkDate)
            predRet = math.prod([1 + stockData[stk]['daily'][allDates[idx]]['changepct']  # forcast return
                                  for idx in range(dateIndex, dateIndex + forGroupSize)]) - 1
            # for neural network, data elements must be integers, so all returns\prices -> ret = int(ret*100)
            stkReturns = [int(r*100) for r in stkReturns]
            spReturns = [int(r*100) for r in spReturns]
            yieldDiff = int(yieldDiff*100)
            sector = stockData[stk]['info']['GICS Index']
            fundData = [{"Profit Margin": int(fd["Profit Margin"]*100), "EPS": int(fd["EPS"]*100),
                          "Dividend": int(fd["Dividend"]*100), "Revenue": fd["Revenue"]*100} for fd in fundData]
            predRet = int(predRet*100) # prediction
            # flatten data to single int array (203 elements)
            curSample.extend(stkReturns) # 50
            curSample.extend(spReturns) # 50
            curSample.extend([sector, month, electionCycle, yieldDiff]) # 3
            for fd in fundData: # 3 rows
                curSample.extend([fd['Profit Margin'], fd['EPS'], fd['Dividend'], fd['Revenue']]) # 4
            samples.append(curSample) # X in model
            predictions.append(predRet) # Y in model
    return (samples, predictions)

doFileLoad = False # data stored in json files
if doFileLoad: # load data from data files
    print('Get Stock List (SP500)..') # from CSV file
    stockInfo = LoadStockList() # includes company info

    stks = [k for k in sorted(LoadStockList().keys()) if '.' not in k] # alpha sort, skip BF.B
    # remove recent SP500 stocks
    stks = [k for k in stks if k not in ['ABNB','CEG','GEHC','KVUE','CARR','CTVA','OTIS','UBER']]
    # 2020-12-11 ABNB Airbnb
    # 2022-01-20 CEG Constellation Energy
    # 2022-12-16 GEHC GE HealthCare
    # 2023-05-05 KVUE Kenvue
    # 2020-03-20 CARR Carrier Global
    # 2019-05-28 CTVA Corteva
    # 2020-03-20 OTIS Otis Worldwide
    # 2019-05-13 UBER Uber

    skipWebLoad = True # load data from web, skip after initial download
    if not skipWebLoad: # from web data, save to text files
        GetStockDataFromWeb(stks)

    stockData = LoadStockData(stks, stockInfo) # daily, fundamentals, earnings, dividends
    stks = stockData.keys()
    print('Stock Count:', len(stks))

    # add stock sector
    gicsList = [] # industry, need index for data - ignore sub-industry, too many
    for stk in stks:
        gics = stockData[stk]['info']['GICS Sector'] #+ '_' + stock_data[stk]['info']['GICS Sub-Industry']
        if not gics in gicsList:
            gicsList.append(gics)
        stockData[stk]['info']['GICS Index'] = gicsList.index(gics)

    stockData['SPY'] = {'daily': LoadDailyHistory(['SPY'])['SPY']['daily']}

    rates = LoadYieldRates() # from file, daily yield curve
    samples, predictions = CreateSamples(stockData, rates)

    # save stock sample data to single file, data values are float
    print('\nWrite shelve file...')
    sh = shelve.open('StockData/SampleData.sh')
    sh['samples'] = samples
    sh['predictions'] = predictions
    sh.close()
    print()


###########################################
##########   Machine Learning   ###########
###########################################

# load sample data as lists
print('Load shelve file...')
sh = shelve.open('StockData/SampleData.sh')
# cast all data to int - This causes an error -> mat1 and mat2 must have the same dtype
# samples = [[int(v) for v in col] for col in sh['samples']]
# predictions = [int(v) for v in sh['predictions']]
samples = sh['samples']
predictions = sh['predictions']
print(len(samples), len(predictions), len(samples[0]))
sh.close()

def ReturnClass(ret): # split stock return into class
    lst = [0,0,0,0,0]
    if ret > 5: lst[0] = 1
    elif ret > 1: lst[1] = 1
    elif ret > -1: lst[2] = 1
    elif ret > -5: lst[3] = 1
    else: lst[4] = 1 # below -5
    return lst  #lst.index(max(lst))

predictions = [ReturnClass(r) for r in predictions] # convert float return to class

class Data(Dataset):
    def __init__(self, samples, predictions):
        self.x = torch.tensor(samples, dtype=torch.float) # convert list to tensor
        self.y = torch.tensor(predictions, dtype=torch.float)
        self.len = self.x.shape[0]

    def __getitem__(self, index):
        return self.x[index], self.y[index]

    def __len__(self):
        return self.len

class Net(nn.Module): # model class
    def __init__(self, D_in, H, D_out): # neuron counts - input\hidden\output
        super(Net, self).__init__()
        if len(H) == 0:
            lyrs = [nn.Linear(D_in, D_out)] # input\output
        else:
            lyrs = [nn.Linear(D_in, H[0])]  # input\hidden
            for ctr in range(len(H)-1):
                lyrs.append(nn.Linear(H[ctr], H[ctr+1])) # hidden/hidden
            lyrs.append(nn.Linear(H[-1], D_out)) # hidden\output
        self.mods = nn.ModuleList(lyrs) # must use modulelist to connect layers

    def forward(self, x):
        for m in self.mods: # each layer
            x = m(x)
        # normalize values 0-1
        x -= x.min(1, keepdim=True)[0]
        x /= x.max(1, keepdim=True)[0]
        return x

def Train(model, criterion, train_loader, optimizer, epochs=10):
    cost = []
    for epoch in range(epochs):
        print(epoch, end=' ', flush=True)
        total = 0
        for x, y in train_loader:
            optimizer.zero_grad() # reset gradient
            yhat = model(x) # prediction
            loss = criterion(yhat, y) # loss calculator
            loss.backward() # derivative, calc step
            optimizer.step() # take step
            total += loss.item()
        cost.append(int(total))
    print()
    return cost

data_set=Data(samples, predictions) # new dataset, all samples

print('Process model...')

def RunModel(): # single run
    model = Net(216,[50,50],5)
    #model = nn.Sequential(nn.Linear(216, 5))
    learning_rate = 0.01
    criterion = nn.MSELoss() # mean squared
    # criterion = nn.BCELoss() # binary cross entropy
    # criterion = nn.CrossEntropyLoss() # mean squared
    optimizer = torch.optim.SGD(model.parameters(), lr=learning_rate, momentum=0.9)
    # optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    train_loader = DataLoader(dataset=data_set, batch_size=100)
    cost = Train(model,criterion, train_loader, optimizer, epochs=100)
    return (max(cost), min(cost))
    # print(cost) # small movement, bad data? noisy features? bad model?

def RunModel(lyrs, epcnt, crt, opt, lr, mom): # for dynamic configuration
    info = [lyrs, epcnt, crt, opt, lr, mom] # hidden layers, epoch count, criterion, optimizer, learning rate, momentum
    print(f'{datetime.now()}      RunModel: {info}')
    model = Net(216, lyrs,5) # every model requires 216 inputs and 5 outputs (return class)
    learning_rate = lr
    criterion = crt() # function passed in
    if mom:
        optimizer = opt(model.parameters(), lr=learning_rate, momentum=mom)
    else: # adam does not use momentum
        optimizer = opt(model.parameters(), lr=learning_rate)
    train_loader = DataLoader(dataset=data_set, batch_size=100)
    cost = Train(model,criterion, train_loader, optimizer, epochs=epcnt)
    print(max(cost), min(cost))
    return (info, max(cost), min(cost)) # model structure and cost result
    # print(cost) # barely moves, bad data? noisy features? bad model?

# try multiple configurations to find best prediction
# based on initial testing, this loop will take over 50 days to complete on single PC
# based on first 200 cost entries, model does not accurately predict label (stock forcast)
costList = []
for lyr1 in [10,30,50,100]:
    lyrs = [lyr1] # 1st hidden layer
    for lyr2 in [0, 10,30,50,100]:
        if lyr2: lyrs.append(lyr2) # multiple layers
        for epcnt in [50,100,150,200,250,300,350,400,450,500]: # epoch count
            for lr in [0.2, 0.5, 0.7, 1]: # learning rate
                for crt in [nn.MSELoss, nn.BCELoss, nn.CrossEntropyLoss]: # criterion
                    costList.append(RunModel(lyrs, epcnt, crt, torch.optim.Adam, lr, 0)) # adam
                    for mom in [0.2, 0.5, 0.7, 1]: # momentum
                        costList.append(RunModel(lyrs, epcnt, crt, torch.optim.SGD, lr, mom)) # gradient descent
                        with open('CostResults.txt','w') as f:
                            print('\n'.join([str(c) for c in costList]), file=f)
print(costList)
print('-- Done --')

