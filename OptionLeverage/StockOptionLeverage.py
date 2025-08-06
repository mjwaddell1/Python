import requests, warnings, urllib3
import sys, json
from datetime import datetime
from urllib3.exceptions import InsecureRequestWarning

warnings.simplefilter(action='ignore', category=Warning) # suppress requests warning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning) # suppress SSL warning

# --- Overview ---
# Get options for stock and show leverage for each option

token = 'cl1uje1r01qXXXXXXXXXXXXXe1r01qinfqo7eig'  # finhub free account for stock price
mbkey = '12ZAozwUlyRXXXXXXXXXX0bVizhI249OZPTG'  # https://mboum.com/api/welcome, free account
StockSymbol = ''
logtxt = ''

hdrs = {
    "User-Agent": "Mozilla/5.0,(Windows NT 10.0; Win64; x64),AppleWebKit/537.36,(KHTML, like Gecko),Chrome/110.0.0.0,Safari/537.36"}

def printx(*args: object) -> object:
    global logtxt
    print(*[str(x) for x in args])
    logtxt += ' '.join([str(x) for x in args]) + '\n'
    with open(f'StockOptionLeverage_{StockSymbol}.log', 'w') as f:
        f.write(logtxt)  # write full log to log file

def rnd2(val):  # round 2 decimal places
    return str(int(val * 100) / 100.0)

def GetStockPrice(sym):  # latest price
    try:
        global status
        url = f'https://api.finnhub.io/api/v1/quote?symbol={sym}&token='+token
        res = requests.get(url, verify=False)
        stkx = json.loads(res.text)
        printx('\n', sym, 'price', stkx['c'])
        return stkx['c'] # float
    except Exception as ex:
        print(ex)
        return 0

def getOptionExps(stk):
    # get expiration list for stock
    url = f'https://api.mboum.com/api/v3/markets/options/?ticker={stk}&apikey={mbkey}'
    printx('getOptionExps', stk, '\n', url)
    rsp = requests.get(url, verify=False, headers=hdrs).json()  # all option exps for this symbol
    exps = []
    for exp in rsp['meta']['expirations']['monthly']:
        exps.append(exp)
    printx('\n'.join(exps))
    return exps

def getOptions(stk, exp):
    opts = []
    url = f'https://api.mboum.com/api/v3/markets/options/?ticker={stk}&expiration={exp}&apikey={mbkey}'
    printx('getOptions', stk, exp, '\n', url)
    rsp = requests.get(url, verify=False, headers=hdrs).json()  # all options for this symbol/expiration
    for call in rsp['body']['Call']:
        opts.append({
            'stk':stk, # CRDO
            #'exp':call['symbol'].split('|')[1], # 20250815
            'exp':exp, # 2025-08-15
            'strike':float(call['strikePrice']), # 17.50
            'price':float(call['midpoint']), # 83.80
            'delta':float(call['delta']) # 0.9984
        })
    return opts

def processOptions(stk):
    exps = getOptionExps(stk) # get exp list for stock
    printx('\n')
    allOpts = []
    maxExp = '' # for investing, try for LEAP
    for exp in exps: # all call options for every expiration  2025-08-15
        if exp > maxExp: maxExp = exp
        opts = getOptions(stk, exp)
        allOpts.extend(opts)
    stkPrice = GetStockPrice(stk)
    printx('\n>>>>', stk)
    printx('Leverage   ExpDate     Delta  Strike   Price')
    for opt in allOpts:
        lvg = (opt['delta']/opt['price'])/(1/stkPrice)
        opt['leverage'] = lvg
    allOpts.sort(key=lambda o:o['leverage'], reverse=True)
    for opt in allOpts:
        isMaxExp = '*' if opt['exp'] == maxExp else ' '
        printx(
            str("%.2f" % opt['leverage']).rjust(8),'',
            str(opt['exp']),
            str("%.2f" % opt['delta']).rjust(6),
            str("%.2f" % opt['strike']).rjust(8),
            str("%.2f" % opt['price']).rjust(7),
            isMaxExp)

if len(sys.argv) > 1:
    StockSymbol = sys.argv[1].upper()
    printx('\nStock Option Leverage -', StockSymbol, datetime.now(), '\n')  # current date\time
    processOptions(StockSymbol)
else:
    print('Missing stock symbol argument: python StockOptionLeverage.py NVDA')
