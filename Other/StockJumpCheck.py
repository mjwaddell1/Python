import requests, warnings, urllib3, datetime, time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from time import sleep
import matplotlib.pyplot as plt
import numpy as np

warnings.simplefilter(action='ignore', category=Warning) # suppress requests warning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning) # suppress SSL warning

# --- Overview ---
# Get stocks that have a recent jump and good earnings
# These stocks will probably continue rising
# Send email with stock price\earnings charts

mbkey = 'o6eB0qL4XcBX4tHdyrXXXXXXXXXXXXXXXXXOpr1HjNhkfpV5G8Kj96kg'  # https://mboum.com/api/welcome, free account
sskey = '58f18d4b-XXXXXXXXXXXXX-04465a30199b'  # https://github.com/yongghongg/stock-symbol

def GetStockNames(): # stock name\exchange, could probably just run this once, stock list rarely changes
    print('Get Stock Names..')
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

def CreateChartImage(title, x, y, filename): # x labels, y values
    fig, ax = plt.subplots()
    ax.plot(x,y)
    ax.set(xlabel='Day', ylabel='Close', title=title)
    ax.grid()
    fig.savefig(filename) # save to png file
    plt.close()

def CreateEarningsChart(title, x1, y1, label1, x2, y2, label2, filename):
    fig = plt.figure(figsize=(4,2)) # set image dimensions for email
    x = np.array(x1)
    y = np.array(y1)
    plt.scatter(x, y, label=label1)
    x = np.array(x2)
    y = np.array(y2)
    plt.scatter(x, y, label=label2)
    plt.title(title)
    plt.legend()
    plt.savefig(filename) # save to png file
    # plt.show()
    fig.clf() # clear plot data
    plt.close()

logtxt = ''

# this script is part of an hourly task
if datetime.datetime.now().weekday() > 4:  # only run on weekdays
    print('Market closed.')
    quit()  # 0=mon, 5=sat, 6=sun

if (datetime.datetime.now().hour <= 15):  # run at market close (after 3pm)
    print('Before 3pm')
    quit()

if (datetime.datetime.now().hour > 17):  # run at market close (before 5pm)
    print('After 5pm')
    quit()

def printx(*args):
    global logtxt
    print(*[str(x) for x in args])
    logtxt += ' '.join([str(x) for x in args]) + '\n'

def GetEarningHistory(stks): # last 4 quarters actual\estimate
    print('Get Earnings...')
    url = stk = None
    try:
        data = {}
        for stk in stks:
            print('.', end='', flush=True)
            # https://mboum.com/api/v1/qu/quote/earnings/?symbol=AAPL&apikey=o6eB0qL4XcBX4tHdyrGXXXXXXXXXXXXXXXXHjNhkfpV5G8Kj96kg
            url = 'https://mboum.com/api/v1/qu/quote/earnings/?symbol=' + stk + '&apikey=' + mbkey
            rsp = requests.get(url, verify=False).json()
            earnings = rsp["data"]["earningsChart"]["quarterly"] # includes estimate and actual, last 4 qtrs
            tmp = {}
            for e in earnings:
                qtr,yr = e['date'].split('Q')
                tmp[yr+'Q'+qtr] = {'actual': e['actual']['raw'], 'estimate': e['estimate']['raw']}
            keys = sorted(tmp.keys()) # 4 qtrs, latest last
            data[stk] = [tmp[k] for k in keys]
            time.sleep(.1) # mboum has rate limit
        return data
    except Exception as ex:
        print('\nGetEarningHistory', '\n', ex,'\n',url,'\n',stk)

def GetStockHistory(sym):  # get history from mboum, basic account
    # 1m | 5m | 15m | 30m | 1h | 1d | 1wk | 1mo | 3mo
    iv = '1d'  # 5 yrs data o/h/l/c
    # url='https://mboum.com/api/v1/hi/history/?symbol=F&interval=1d&diffandsplits=true&apikey=demo'
    url = 'https://mboum.com/api/v1/hi/history/?symbol=' + sym + '&interval=' + iv + '&diffandsplits=true&apikey=' + mbkey
    hdrs = {
        "User-Agent": "Mozilla/5.0,(Windows NT 10.0; Win64; x64),AppleWebKit/537.36,(KHTML, like Gecko),Chrome/110.0.0.0,Safari/537.36"}
    jsn = requests.get(url, verify=False, headers=hdrs).json()
    hist = []
    for k in jsn['data'].keys():
        hist.append((int(k), jsn['data'][k]['date'], jsn['data'][k]['open'], jsn['data'][k]['close']))
    # sort from latest date
    hist.sort(key=lambda x: x[0])
    return hist

def GetImageData(filename): # for email
    with open(filename, 'rb') as f:
        return f.read()

def SendEmail(html, subj, images): # send email with chart images
    printx('Sending email...')
    # Define these once; use them twice!
    strFrom = 'michael.waddell@aon.com'
    strTo = 'michael.waddell@aon.com'

    # Create the root message and fill in the from, to, and subject headers
    msgRoot = MIMEMultipart('related')
    msgRoot['Subject'] = subj
    msgRoot['From'] = strFrom
    msgRoot['To'] = strTo
    msgRoot.preamble = 'This is a multi-part message in MIME format.'

    # Encapsulate the plain and HTML versions of the message body in an
    # 'alternative' part, so message agents can decide which they want to display.
    msgAlternative = MIMEMultipart('alternative')
    msgRoot.attach(msgAlternative)

    msgText = MIMEText('Not HTML.')
    msgAlternative.attach(msgText)

    # We reference the image in the IMG SRC attribute by the ID we give it below
    msgText = MIMEText(html, 'html')
    msgAlternative.attach(msgText)

    for img in images: # chart assets (images)
        with open(img, 'rb') as fp:
            msgImage = MIMEImage(fp.read())
        txt = img.split('.')[0]
        msgImage.add_header('Content-ID', f'<{txt}>') # NVDA or NVDA_Earnings
        msgRoot.attach(msgImage)

    # Send the email (this example assumes SMTP authentication is required)
    import smtplib
    smtp = smtplib.SMTP()
    smtp.connect('smtprelayna.aon.net')
    smtp.sendmail(strFrom, strTo, msgRoot.as_string())
    smtp.quit()

#  FinViz scraper functions
def GetFinVizStocksCmt(filters=None):  # scrape FinViz comment block
    if not filters:
        filters = 'sh_opt_option,sh_price_o50,ta_volatility_mo3'  # default

    hdr = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) "
                      "Chrome/23.0.1271.64 Safari/537.11"
    }

    print('FinViz: ', end='')

    pg = 1  # first stock index on page
    stks = []  # stock tickers
    prcs = []  # stock prices
    total = 0  # total stock count
    while True:
        url = f'https://finviz.com/screener.ashx?v=111&f={filters}&r={pg}'
        # url = 'https://finviz.com/screener.ashx?v=111&f=sh_opt_option,sh_price_o50,ta_volatility_mo3&r=1'
        print('#', end='')
        rsp = requests.get(url, headers=hdr)
        if pg == 1:  # first page
            if rsp.text.find('>0 Total<') > 0: return []  # no stocks passed filter
            idx = rsp.text.find('#1 /')
            if idx == -1: return ([], [])  # total not found
            total = int(rsp.text[idx:idx + 13].split(' ')[2])  # #1 / 347 Total
        idx = rsp.text.find('<!-- TS')  # start of comment
        if idx == -1: return ([], [])  # comment not found
        idx2 = rsp.text.find('TE -->', idx)  # end of comment
        if idx2 == -1: return ([], [])  # comment not found
        txt = rsp.text[idx:idx2 + 4]
        lst = txt.split('\n')[1:-1]
        stks.extend([s.split('|')[0] for s in lst])  # symbol
        prcs.extend([float(s.split('|')[1]) for s in lst])  # price
        if len(stks) >= total:
            print('')
            return (stks, prcs)
        pg += len(lst)  # next page

def GetRowData(row):  # FinViz, parse single data row
    cols = row.split('</td><td')  # each column
    data = []
    for i in [1, 2, 8, 9]:  # symbol, name, price, pct change
        td = cols[i]
        td = td.replace('</span>', '').replace('%', '').replace('><', '')
        idx = td.rfind('>', 0, len(td) - 2)
        idx2 = td.rfind('<')
        dp = td[idx + 1:idx2]
        data.append(dp)
    # return dictionary   # ['AAON', 'AAON Inc.', 64.06, 8.58]
    return {'Ticker': data[0], 'Name': data[1], 'Price': float(data[2]), 'ChangePct': float(data[3])}

def GetFinVizStocksTbl(filters=None):  # FinViz, scrape main table
    if not filters:
        filters = 'sh_opt_option,sh_price_o50,ta_volatility_mo3'  # default

    hdr = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) "
                      "Chrome/23.0.1271.64 Safari/537.11"
    }

    print('FinViz: ', end='')

    cnt = 1  # first stock in table
    stks = []  # final list
    total = 0  # total stock count
    while True:  # all pages
        # get finviz table, Overview (v=111), start with first stock (r=1)
        url = f'https://finviz.com/screener.ashx?v=111&f={filters}&r={cnt}'
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
                stks.append(GetRowData(row))
                cnt += 1
        if len(stks) >= total:
            print('')
            return stks
        sleep(0.1)  # must pause between pages

filters = [ # finviz
    'ta_highlow52w_nh',  # 52 week high
    'ta_sma20_pa10',     # price 10% above SMA 20 day
    'fa_netmargin_pos',  # positive net profit margin
    'fa_epsyoy_pos'      # earnings rise yr/yr
]

stks = GetStockNames() # US market, all stocks
stock_list = GetFinVizStocksTbl(','.join(filters)) # finviz filter
if not len(stock_list):
    printx('No stocks from FinViz') # no recent jumps
    quit()

baselink = 'https://www.google.com/finance/quote/' # for quote link in email
stock_list = [s['Ticker'] for s in stock_list] # just tickers
earnings_all = GetEarningHistory(stock_list) # from mbaum, last 4 quarters
earnings = {}
for e in earnings_all.keys():
    if earnings_all[e][-1]['estimate'] <= earnings_all[e][-1]['actual']: # show only positive surprises
        earnings[e] = earnings_all[e]
stock_list = list(earnings.keys()) # filter list based on earnings
printx(earnings)
x = [1,2,3,4] # earnings chart x axis

images = []
print('Get Stock History\\Build Charts...')
html = '<html><body><center>'
for stk in stock_list:
    # price line chart
    hist = GetStockHistory(stk)[-250:]
    CreateChartImage(stk + ' - ' + stks[stk]['name'], list(range(len(hist))), [p[3] for p in hist], stk + '.png')
    images.append(stk + '.png') # for email
    # earnings scatter plot
    yact = [e['actual'] for e in earnings[stk]]
    yest = [e['estimate'] for e in earnings[stk]]
    CreateEarningsChart('Earnings '+stk, x, yact, 'Act', x, yest, 'Est', stk+'_Earnings.png')
    images.append(stk + '_Earnings.png') # for email
    # add images to email
    html += f'<br/><img src="cid:{stk}"><br/>\n'
    html += f'<br/><img src="cid:{stk}_Earnings"><br/>\n'
    html += f'<br/><a href="{baselink}{stk}:{stks[stk]["exchange"]}">GoogleFinance {stk}</a><br/>\n'
html+='</center></body></html>'
printx(html)

SendEmail(html,f'Stock Jump Alert ({len(stock_list)})', images)

with open('StockJumpCheck.log', 'w') as f:
    f.write(logtxt)  # write full log to log file
