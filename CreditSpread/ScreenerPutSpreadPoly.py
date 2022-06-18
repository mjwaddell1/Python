import requests, json, sys
from finviz.screener import Screener  # https://github.com/mariostoev/finviz
from datetime import datetime, timedelta, date
from math import floor
from time import sleep
import yahoo_fin.stock_info as si  # for earnings
from multiprocessing import Process, Pool, freeze_support
from urllib3.exceptions import InsecureRequestWarning
import yfinance as yf

# Screener to search stock options for good bear credit spread opportunities
# Use Polygon.io feed

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
#   'fa_pfcf_u15',  		# price/FreeCashFlow under 15
#	'fa_roe_pos',  			# ROE positive
#	'fa_pb_u5', 			# price/book under 5
#	'fa_epsqoq_o10'			# earnings rise %, qtr/qtr
#   'ta_sma50_pa',  		# price above SMA20 - 20, 50, 200
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


def GetPutOptions(stk): # {s['Ticker'], s['Price'], s['Change']}
	for retry in [0,1,2]:
		try:
			sym = stk['Ticker']
			stkprice = 0
			yfprice = (yf.Ticker(sym)).history(period="3m").iloc[-1]['Close']
			expdate = str(GetFridayDate()) #str(GetThursdayDate())
			#print(sym + ' ', end='' )
			print('.', end='')
			requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
			stkprice = yfprice
			APIKEY='3p4Ch1P--------dubmB1N' # Polygon.io  $99/month realtime
			#get option list
			url = 'https://api.polygon.io/v3/reference/options/contracts?underlying_ticker='+sym+'&contract_type=put&expiration_date='+expdate+'&limit=150&sort=strike_price&order=desc&apiKey='+APIKEY
			rsp = requests.get(url, verify=False).json() # all put options for this symbol
			#print(url,'\n\n',rsp)
			###print(rsp) # option list but no bid\ask prices
			data = []
			#get option details
			for put in rsp['results']:
				if put['strike_price'] > stkprice: continue # skip ITM
				tkr = put['ticker']  # O:QQQ220218C00195000
				url = 'https://api.polygon.io/v3/snapshot/options/'+sym+'/'+tkr+'?apiKey='+APIKEY
				rc = requests.get(url, verify=False).json() # put details with price, realtime
				#stkprice = float(rc['results']['underlying_asset']['price']) # keep this, price may change during option requests
				if put['strike_price'] > stkprice: continue # skip ITM
				if not 'bid' in rc['results']['last_quote']: break # too far OTM, no price
				if not 'ask' in rc['results']['last_quote']: break
				if float(rc['results']['last_quote']['bid']) < 0.1: break # too far OTM, no price
				if float(rc['results']['last_quote']['ask']) < 0.1: break 
				data.append({
					'strike' : float(rc['results']['details']['strike_price']),
					'bid' : float(rc['results']['last_quote']['bid']),
					'ask' : float(rc['results']['last_quote']['ask']),
				})
			return {'sym':sym, 'price':stkprice, 'yprice':stk['Price'], 'ychange':stk['Change'], 'yfprice':yfprice, 'puts':data, 'error':''} # include yahoo price\change
		except Exception as ex:
			printx('Error: Symbol ' + sym, ':', ex)
			if (retry == 2):
				return {'sym':sym, 'price':stkprice, 'yprice':stk['Price'], 'ychange':stk['Change'], 'yfprice':-1, 'puts':None, 'error':ex}


def GetTickerOptions(stks): # stks is [{s['Ticker'], s['Price'], s['Change']},,,,]
	pool = Pool(processes=30)	
	results = pool.map(GetPutOptions, stks)
	return results

def UpdateStockQuotes(stkdata): # get real-time quotes
	print('UpdateStockQuotes',len(stkdata))
	mbkey = 'yOA0bpDZlT-----------vJG0zURmoqj5wNE----------fTVjKJn' # https://mboum.com/api/welcome, free account
	quotes = {} # dictionary  symbol:price
	#https://mboum.com/api/v1/qu/quote/?apikey=yOA0bpDZlcjKng-------LLRayeWK4UG----VjKJn&symbol=AAPL,F
	urlbase = url = 'https://mboum.com/api/v1/qu/quote/?apikey=' + mbkey + '&symbol='
	ctr=0
	for sd in stkdata:
		url += sd['sym'] + ','
		ctr+=1
		if ctr%50 == 0 or ctr==len(stkdata):  # max 50 symbols per request, 5 requests per second
			rsp = requests.get(url, verify=False).json()  #send request
			print('rsp len',len(rsp))
			for rec in rsp['data']:
				quotes[rec['symbol']] = (rec['ask']+rec['bid'])/2.0
			ctr=0
			url=urlbase
			sleep(0.5) # max 5 requests per second
	for sd in stkdata:
		sd['price'] = quotes[sd['sym']]
	print('Done quote update')
		
if __name__ == '__main__':
	freeze_support()  # needed for Windows

	printx('\nOption Spread Screener -',datetime.now(),'\n') # current date\time
	
	optlogfile = "D:/MikeStuff/OptionPutHistorySpread.txt"    # store option results (append)
	optlogtxt = ""  # store option results
	expdate = str(GetFridayDate()) #str(GetThursdayDate())

	printx('Exp Date:', expdate)
	printx('Run FinViz screener...')

	stock_list = Screener(filters=filters, table='Performance', order='ticker')  # Get the performance table and sort it by price ascending

	# FinViz columns
	# ['No.', 'Ticker', 'Perf Week', 'Perf Month', 'Perf Quart', 'Perf Half', 'Perf Year', 'Perf YTD', 
	#  'Volatility W', 'Volatility M', 'Recom', 'Avg Volume', 'Rel Volume', 'Price', 'Change', 'Volume']

	printx('\n', len(stock_list), 'Stocks found (FinViz)\n') # stock count from finviz filter

	# update these values to change option scan filter
	MinReturn  = 2.0/100   # 5% minimum return
	MinBuffer  = 8.0/100   # 6% minimum price safety margin (higher value means less chance that option goes ITM)
	MinStrGap  = 2.0/100   # 2% minimum price gap between strikes (higher value means more time to exit position if ITM)
	MinPremium = 0.50      # minimum sell premium (bid) 50 cents
	MinSpread  = 0.50      # minimum premium spread 50 cents (higher is better, etrade commission is $1 per contract (100 shares), 50 cent spread means 2% commission)
	MaxExpDays = 5         # maximum 5 days until expiration (lower is better, focus on weekly options)
	IgnoreStk  = ['TNA','TQQQ','UPRO','BRZU','TECL','UDOW','NAIL','HEI-A','MOG-A','XLNX','FAS','UCO','GUSH','LABU','LABD','BOIL'] # skip leveraged indexes, very volatile, high risk
	
	stks = [{'Ticker':s['Ticker'], 'Price':s['Price'], 'Change':s['Change']} for s in stock_list.data]  # symbol, price, change only
	stks = list(filter(lambda s: s['Ticker'] not in IgnoreStk, stks)) # remove ignored

	printx('Get Option Chains (Polygon)....')
	stkdata = GetTickerOptions(stks) # all option data for all stocks
		

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
		for stk in stksrt:  # each stock from polygon
			try:
				disp = False # don't show stock unless option found
				pr = float(stk['price'])  # yahoo stock price, fucking poly has issues
				stkputs = stk['puts']  # list of strike\bid\ask
				if not stkputs: continue # error
				for put in stkputs: # for each put option in option list
					if skip: break # failed earnings check, move to next stock
					strike = put['strike']  # option strike price
					# check if possible short option
					if strike <= pr * (1 - MinBuffer) and put['bid'] > MinPremium: # 5% over price (safety margin), premium > 50 cents
						# scan for possible long option
						for put2 in stkputs: # scan all puts, ignore puts closer to ATM
							if put2['strike'] >= put['strike']: continue  # closer to ATM
							if (put['strike'] - put2['strike'])/put['strike'] < MinStrGap: continue # strikes too close together (if stocks goes ITM, will quickly cross entire spread)
							if put['bid'] - put2['ask'] <= MinSpread: continue  # premium spread must be at least 50 cents
							if put2['bid'] == 0: continue  # useless option
							if (put['bid'] - put2['ask'])/(put['strike'] - put2['strike']) >= MinReturn:	# at least 10% return			
								if not disp: # first option for this stock
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
												 str(stk['ychange']).rjust(7), 
												 '('+('-' if earndays < 0 else (msg + str(earndays)))+')', 
												 '  ', 
												 name)  #GetCompanyName(stk['Ticker']))
									disp=True # stock already displayed
								# print option data
								printx('>>> ',											 
											 str(put['strike']).rjust(8), 
											 str("%.1f" % put['bid']).rjust(8))
								printx('<<< ',
											 str(put2['strike']).rjust(8), 
											 str("%.1f" % put2['ask']).rjust(8), 
											 pct(strike/pr - 1).rjust(8),
											 pct((put['bid'] - put2['ask'])/(put2['strike'] - put['strike'])).rjust(8),
											 ('    ['+pct((put['strike'] - put2['strike'])/put['strike']).rjust(5)+']'))
				skip = False # reset flag
			except Exception as ex: # error processing data
				printx(stk['sym'], 'Error:', ex) # print error, move to next stock
		
	printx('\n -- Done --\n')

	with open(optlogfile, 'a') as f:
		f.write(optlogtxt)  # write final log to log file



