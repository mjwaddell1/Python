import requests, json, sys
from finviz.screener import Screener  # https://github.com/mariostoev/finviz
from datetime import datetime, timedelta, date, timezone
from math import floor
from time import sleep
import yahoo_fin.stock_info as si  # for earnings
from multiprocessing import Process, Pool, freeze_support
from urllib3.exceptions import InsecureRequestWarning
import yfinance as yf

# Screener to search stock options for good bear credit spread opportunities
# Use MBoum data feed

optlogtxt = ""

def GetFridayDate(): # upcoming Friday
	for d in range(7): # 0-6
		if (date.today()+timedelta(days=d)).weekday() == 4: # Monday=0, Friday=4
			return date.today()+timedelta(days=d)  # '2022-02-18'

def GetThursdayDate(): # upcoming Thursday - Use if Friday is holiday
	for d in range(7): # 0-6
		if (date.today()+timedelta(days=d)).weekday() == 3: # Monday=0, Thursday=3, Friday=4
			return date.today()+timedelta(days=d)  # '2022-02-18'

def DaysToExp(dy=4): # days til Friday (4) (Thur if Friday holiday)
	for d in range(7): # 0-6
		if (date.today()+timedelta(days=d)).weekday() == dy: # Monday=0, Thursday=3, Friday=4
			return d

def printx(*arg): # print to screen and final log string
	global optlogtxt
	print(*arg)  # print to screen
	optlogtxt += " ".join(str(x) for x in arg) + "\n"  # write to log file at end of script

def GetEarningsDay(sym, maxdays):  # future earnings dates (days from today)
	try:
		dt = str(yf.Ticker(sym).calendar.iloc[0][0]) # next earnings date
		diff = (datetime.fromisoformat(dt.split(' ')[0]) - datetime.now()).days + 1 # days
		if (0 <= diff < maxdays):  # future earnings call within range, include today
			return (diff,'') # actual number of days to earnings call
		return (-1,'0') # no dates in range
	except Exception as ex:
		printx(sym, 'Earnings error:', ex)
		return (-2,'x')  # error
		
def pct(val, digits=1): # format percent
	val *= 10 ** (digits + 2)
	return '{1:.{0}f}%'.format(digits, floor(val) / 10 ** digits)


# go to FinViz, set filters, copy parameters to list
# https://finviz.com/screener.ashx?v=171&f=fa_curratio_o1,fa_debteq_u1,fa_netmargin_pos,fa_pb_u5,fa_pfcf_u10,fa_roe_pos,sh_opt_option,sh_price_o10,ta_perf_26wup,ta_sma20_pa,ta_volatility_mo2

# https://finviz.com/screener.ashx?v=171&f=fa_curratio_o1,fa_debteq_u2,fa_netmargin_pos,fa_roe_pos,sh_opt_option,ta_perf_26wup,sh_price_o5,fa_pb_u5,fa_epsqoq_o10

# todo - parse filters from URL, document each filter type

# spread - https://finviz.com/screener.ashx?v=111&f=sh_opt_option,sh_price_o90,ta_change_d,ta_perf_13wdown,ta_sma200_pb,ta_sma50_pb,ta_volatility_mo5&ft=3

filters = [
#	'fa_curratio_o1',  		# current ratio over 1
#	'fa_debteq_u2', 		# debt/equity under 2
#	'fa_netmargin_pos',	 	# net profit margin positive  -  for call spread, try negative margin
# 	'fa_pfcf_u15',  		# price/FreeCashFlow under 15
#	'fa_roe_pos',  			# ROE positive
#	'fa_pb_u5', 			# price/book under 5
#	'fa_epsqoq_o10'			# earnings rise %, qtr/qtr
# 	'ta_sma50_pa',  		# price above SMA20 - 20, 50, 200
	'sh_opt_option', 		# optionable
#	'ta_perf_4wdown',  		# performance 4 weeks down (ta_perf_dup - day up, ta_perf_1wup - one week up, ta_perf_4wup - month up, ta_perf_13wup - qtr up, ta_perf_52wup - yr up)
	'sh_price_o50', 		# share price over $50 - commission paid per contract
	'ta_volatility_mo3' 	# volatility month - over 3%
]

not_used = [  # save for later
	'fa_div_o1', 			# dividend yield over 1%
	'sh_avgvol_o100', 		# avg volume over 100k
	'sh_short_u5', 			# float short under 5%
	'fa_peg_u1', 			# PEG under 1
	'fa_fpe_u5', 			# forward P/E under 5
	'fa_payoutratio_u10',	# payout ratio under 10
	'fa_ltdebteq_u1', 		# LT debt/equity under 1
	'ta_beta_o1', 			# beta over 1 - ta_beta_o1.5 (over 1.5)
	'ta_rsi_ob70', 			# RSI(14) overbought 70 - ta_rsi_os30 (oversold 30)
	'ta_change_u1' 			# day change up 1% - ta_change_u day change up
]

# get options chain for specific symbol
def GetCallOptionsMB(stk): # MBoum {s['Ticker'], s['Price'], s['Change']}
	retry = 0
	url = ''
	while retry < 3: # if request fails
		retry += 1
		rsp = ''
		try:
			#https://mboum.com/api/v1/op/option/?symbol=AAPL&expiration=1674172800&apikey=demo
			mbkey = 'yOA0bpDZlcMjKn--------------fLLRayeWK4UTVjKJn' # https://mboum.com/api/welcome, free account
			sym = stk['Ticker']
			stkprice = 0
			yfprice = (yf.Ticker(sym)).history(period="3m").iloc[-1]['Close']
			expdate = str(int(datetime.combine(GetFridayDate(), datetime.min.time()).replace(tzinfo=timezone.utc).timestamp()))  # epoch #GetThursdayDate()
			requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
			stkprice = yfprice
			#get option list
			url = 'https://mboum.com/api/v1/op/option/?symbol='+stk['Ticker']+'&expiration='+expdate+'&apikey='+mbkey
			rsp = requests.get(url, verify=False).json() # all call options for this symbol
			stkprice = rsp['data']['optionChain']['result'][0]['quote']['regularMarketPrice'] # realtime
			data = []
			#get option details
			for cll in rsp['data']['optionChain']['result'][0]['options'][0]['calls']:
				if bool(cll['inTheMoney']): continue # skip ITM
				if not 'bid' in cll or float(cll['bid']) < 0.1: break # too far OTM, no price
				if not 'ask' in cll or float(cll['ask']) < 0.1: break 
				data.append({
					'strike' : float(cll['strike']),
					'bid' : float(cll['bid']),
					'ask' : float(cll['ask']),
				})
			print('.', end='')
			return {'sym':sym, 'price':stkprice, 'yprice':stk['Price'], 'ychange':stk['Change'], 'yfprice':yfprice, 'calls':data, 'error':''} # include yahoo price\change
		except Exception as ex:
			if "request limit" in str(rsp): # error: Sorry, you are hitting the request limit of 5 per second
				print('-',end='')
				sleep(1)
				retry=0
			if (retry == 2):
				print("*** error: ", sym, ex, rsp, '\n', url)
				return {'sym':sym, 'price':stkprice, 'yprice':stk['Price'], 'ychange':stk['Change'], 'yfprice':-1, 'calls':None, 'error':ex}


def GetTickerOptionsMB(stks): # MBoum - stks is [{s['Ticker'], s['Price'], s['Change']},,,,]
	pool = Pool(processes=5)	# limit 5 requests/sec
	results = pool.map(GetCallOptionsMB, stks)
	return results


def UpdateStockQuotes(stkdata): # get real-time quotes MBoum
	rsp = ''
	url = ''
	try:
		print('\nUpdateStockQuotes',len(stkdata))
		mbkey = 'yOA0bpDZlcMjK--------------LRayeWK4UTVjKJn' # https://mboum.com/api/welcome, free account
		quotes = {} # dictionary  symbol:price
		urlbase = url = 'https://mboum.com/api/v1/qu/quote/?apikey=' + mbkey + '&symbol='
		ctr=0
		for sd in stkdata:
			url += sd['sym'] + ','
			ctr+=1
			# 50 symbols/request for free version, 200 paid version
			if ctr%200 == 0 or ctr==len(stkdata):  # 5 requests per second
				url = url[:-1] # remove last comma, fucking MBoum
				rsp = requests.get(url, verify=False).json()  #send request
				print(ctr, end='  ')
				for rec in rsp['data']:
					earndate = ''
					if rec['earningsTimestamp']: earndate=rec['earningsTimestamp']['date']
					quotes[rec['symbol']] = {'price':rec['regularMarketPrice'], 'chg':rec['regularMarketChange'], 'chgpct':rec['regularMarketChangePercent'], 'earndate':earndate}
				url=urlbase
				sleep(0.5) # max 5 requests per second
		rsp = url = None
		for sd in stkdata:
			sd['price'] = quotes[sd['sym']]['price'] # overwrite finviz price
			sd['chg'] = quotes[sd['sym']]['chg'] # new field, not post market price
			sd['chgpct'] = quotes[sd['sym']]['chgpct'] # new field
			sd['earndate'] = quotes[sd['sym']]['earndate'] # new field, recent earndate may be in past
		print('\nDone quote update')
	except Exception as ex: # error processing data
		print("quote error:",ex)
		print(url)
		print(rsp)
	
if __name__ == '__main__':
	freeze_support()  # needed for Windows
	
	printx('\nOption Spread Screener -',datetime.now(),'\n') # current date\time
	
	optlogfile = "D:/MikeStuff/OptionCallHistorySpread.txt"    # store option results (append)
	optlogtxt = ""  # store option results
	expdate = GetFridayDate()  #str(GetThursdayDate())
	expts = datetime.combine(expdate, datetime.min.time()).replace(tzinfo=timezone.utc).timestamp()

	printx('Exp Date:', str(expdate), '   (' + str(int(expts)) + ')')
	printx('Run FinViz screener...')

	stock_list = Screener(filters=filters, table='Performance', order='ticker')  # Get the performance table and sort it by symbol ascending

	# FinViz columns
	# ['No.', 'Ticker', 'Perf Week', 'Perf Month', 'Perf Quart', 'Perf Half', 'Perf Year', 'Perf YTD', 
	#  'Volatility W', 'Volatility M', 'Recom', 'Avg Volume', 'Rel Volume', 'Price', 'Change', 'Volume']

	printx('\n', len(stock_list), 'Stocks found (FinViz)\n') # stock count from finviz filter

	# update these values to change option scan filter
	MinReturn  = 2.0/100   # 2% minimum return
	MinBuffer  = 6.0/100   # 6% minimum price safety margin (higher value means less chance that option goes ITM)
	MinStrGap  = 2.0/100   # 2% minimum price gap between strikes (higher value means more time to exit position if ITM)
	MinPremium = 0.50      # minimum sell premium (bid) 50 cents
	MinSpread  = 0.50      # minimum premium spread 50 cents (higher is better, etrade commission is $1 per contract (100 shares), 50 cent spread means 2% commission)
	MaxExpDays = 5         # maximum 5 days until expiration (lower is better, focus on weekly options)
	IgnoreStk  = ['TNA','TQQQ','SQQQ','UPRO','BRZU','TECL','UDOW','NAIL','HEI-A','MOG-A','XLNX', 'FAS','UCO','GUSH','LABU','LABD','BOIL','SOXS'] # skip leveraged indexes, very volatile, high risk
	
	stks = [{'Ticker':s['Ticker'], 'Price':s['Price'], 'Change':s['Change']} for s in stock_list.data]  # symbol, price, change only
	stks = list(filter(lambda s: s['Ticker'] not in IgnoreStk, stks)) # remove ignored
	

	printx('Get Option Chains (MBoum)....')

	stkdata = GetTickerOptionsMB(stks) # all option data for all stocks

	# update stock data with real-time quotes (MBoum)
	UpdateStockQuotes(stkdata)
	
	stksrt = sorted(stkdata, key=lambda d: d['sym']) # sort by ticker symbol
	
	printx('\n\nProcess Option Chains....')
	printx('[Symbol Price Change (EarnDay) Name] [Strike Bid/Ask %Strike %Spread %StrikeGap]\n')
	
	daysToExp = DaysToExp()
	
	# For each stock from FinViz, get call option chain
	# Goal is to find 2 call options where short strike is >= 5% under stock price 
	#    AND (short bid - long ask) >= $1 
	#    AND (short bid - long ask)/(short strike - long strike) > 10% 
	#    Expiry must be under 5 days (weekly).
	skip = False # used for earnings check
	for trycnt in [1]: # if options error, retry failed stocks
		stkretry = [] # error stocks
		for stk in stksrt:  # each stock from MB
			try:
				disp = False # don't show stock unless option found
				pr = float(stk['price'])  # stock price
				stkcalls = stk['calls']  # list of strike\bid\ask
				if not stkcalls: continue # error, no options for this stock
				for cll in stkcalls: # for each call option in option list
					if skip: break # failed earnings check, move to next stock
					strike = cll['strike']  # option strike price
					# check if possible short option
					if strike >= pr * (1 + MinBuffer) and cll['bid'] > MinPremium: # 5% over price (safety margin), premium > 50 cents
						# scan for possible long option
						for cll2 in stkcalls: # scan all calls, ignore calls closer to ATM
							if cll2['strike'] <= cll['strike']: continue  # closer to ATM
							if (cll2['strike'] - cll['strike'])/cll['strike'] < MinStrGap: continue # strikes too close together (if stocks goes ITM, will quickly cross entire spread)
							if cll['bid'] - cll2['ask'] <= MinSpread: continue  # premium spread must be at least 50 cents
							if cll['bid'] == 0: continue  # useless call
							if (cll['bid'] - cll2['ask'])/(cll2['strike'] - cll['strike']) >= MinReturn:	# at least 10% return			
								if not disp: # first option for this stock
									# TODO - calc earn date from stock quote > stk['earndate']
									earndays, msg = GetEarningsDay(stk['sym'], 10) # days until earnings call
									if earndays >= 0 and earndays < daysToExp: 
										printx('Skipping earnings stock:', stk['sym'], '('+str(earndays)+')')
										skip = True # stop checking options, move to next stock
										break
									# print stock data once
									name = yf.Ticker(stk['sym']).info['shortName']
									printx('++', 
												 stk['sym'].ljust(6), 
												 str("%.1f" % pr).rjust(7), 
												 str(pct(stk['chgpct']/100)).rjust(7),
												 '('+('-' if earndays < 0 else (msg + str(earndays)))+')', 
												 '  ', 
												 name)  #GetCompanyName(stk['Ticker']))
									disp=True # stock already displayed
								# print option data
								printx('>>> ',											 
											 str(cll['strike']).rjust(8), 
											 str("%.1f" % cll['bid']).rjust(8))
								printx('<<< ',
											 str(cll2['strike']).rjust(8), 
											 str("%.1f" % cll2['ask']).rjust(8), 
											 pct(strike/pr - 1).rjust(8),
											 pct((cll['bid'] - cll2['ask'])/(cll2['strike'] - cll['strike'])).rjust(8),
											 ('    ['+pct((cll2['strike'] - cll['strike'])/cll['strike']).rjust(5)+']'))
				skip = False # reset flag
			except Exception as ex: # error processing data
				printx(stk['sym'], 'Error:', ex) # print error, move to next stock
		
	printx('\n -- Done --\n')

	with open(optlogfile, 'a') as f:
		f.write(optlogtxt)  # write final log to log file



