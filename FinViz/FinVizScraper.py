import requests

def GetFinVizStocksCmt(filters=None):  # scrape comment block if only ticker\price needed
    if not filters:
        filters='sh_opt_option,sh_price_o50,ta_volatility_mo3'  # default

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
            total = int(rsp.text[idx:idx+13].split(' ')[2])  # #1 / 347 Total
        idx = rsp.text.find('<!-- TS')  # start of comment
        if idx == -1: return ([], [])   # comment not found
        idx2 = rsp.text.find('TE -->', idx)  # end of comment
        if idx2 == -1: return ([], [])  # comment not found
        txt = rsp.text[idx:idx2+4]
        lst = txt.split('\n')[1:-1]
        stks.extend([s.split('|')[0] for s in lst])  # symbol
        prcs.extend([float(s.split('|')[1]) for s in lst])  # price
        if len(stks) >= total:
            print('')
            return (stks, prcs)
        pg += len(lst)  # next page

def GetRowData(row):  # parse single data row
    cols = row.split('</td><td')  # each column
    data = []
    for i in [1, 2, 8, 9]:  # symbol, name, price, pct change
        td = cols[i]
        td = td.replace('</span>', '').replace('%', '').replace('><', '')  # clean data row
        idx = td.rfind('>', 0, len(td)-2)
        idx2 = td.rfind('<')
        dp = td[idx+1:idx2]
        data.append(dp)
    # return dictionary   # ['AAON', 'AAON Inc.', 64.06, 8.58]
    return {'Ticker': data[0], 'Name': data[1], 'Price': float(data[2]), 'ChangePct': float(data[3])}

def GetFinVizStocksTbl(filters=None):  # scrape main table - symbol, name, price, pct change
    if not filters:
        filters='sh_opt_option,sh_price_o50,ta_volatility_mo3'  # default

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
        print('#', end='')
        rsp = requests.get(url, headers=hdr)
        if cnt == 1:  # first page, get total
            if rsp.text.find('>0 Total<') > 0: return []  # no stocks passed filter
            idx = rsp.text.find('#1 /')
            if idx == -1: return []  # total not found
            total = int(rsp.text[idx:idx+13].split(' ')[2])  # #1 / 347 Total
        idx = rsp.text.find('</thead>')  # end of table headers
        if idx == -1: return []  # header not found
        idx2 = rsp.text.find('<table ', idx)  # end of data rows
        if idx2 == -1: return []  # tag not found
        txt = rsp.text[idx:idx2]
        lst = txt.split('\n')[1:-1]
        # print("\n".join(lst))
        for row in lst:
            if row.startswith('<td '):  # stock data row
                stks.append(GetRowData(row))
                cnt += 1
        if len(stks) >= total:
            print('')
            return stks


# test
ret = GetFinVizStocksTbl()
print('\n'.join([str(x) for x in ret]))
print(ret[0]['Ticker'])  # test
