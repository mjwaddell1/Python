import requests, json, sys
from finviz.screener import Screener  # https://github.com/mariostoev/finviz
from datetime import datetime, timedelta
from math import floor
from time import sleep
import yahoo_fin.stock_info as si  # for earnings
#import yfinance as yf
#from yahoo_earnings_calendar import YahooEarningsCalendar  # does not work


# C:\WINDOWS\system32\oo.cmd

optlogfile = "D:/MikeStuff/OptionCallHistorySpread.txt"    # store option results (append)
optlogtxt = ""  # store option results

def printx(*arg): # print to screen and final log string
	global optlogtxt
	print(*arg)  # print to screen
	optlogtxt += " ".join(str(x) for x in arg) + "\n"  # write to log file at end of script

# note that earnings API also returns company name
# note that earnings API also returns full earnings history for trend tracking
def GetEarningsDay(sym, maxdays):  # future earnings dates (days from today)
	try:
		name = '<unknown>'
		#print(dir(si))
		#print(si.get_dividends(sym)) # only past dividends
		#print(yf.Ticker(sym).dividends) # only past dividends
		earnings = si.get_earnings_history(sym) # array of json objects
		name = earnings[0]['companyshortname']
		for e in earnings:
			dt = e['startdatetime']  # 2021-09-29T10:59:00.000Z
			diff = (datetime.fromisoformat(dt.split('T')[0]) - datetime.now()).days + 1 # days
			if (0 <= diff < maxdays):  # future earnings call within range, include today
				return (diff,'',name) # actual number of days to earnings call
		dt = earnings[0]['startdatetime']  # check if no future earnings
		if (datetime.fromisoformat(dt.split('T')[0]) < datetime.now()): # no future earnings?
			diff = (datetime.fromisoformat(dt.split('T')[0]) - datetime.now()).days + 92 # last call + 3 months
			if (0 < diff < maxdays): return (diff,'e', name)  # estimate number of days to earnings call
		return (-1,'0',name) # no dates in range
	except Exception as ex:
		printx(sym, 'Earnings error:', ex)
		return (-2,'x',name)  # error


printx('\nOption Spread Screener -',datetime.now(),'\n') # current date\time

# get company list - error, may be request limit
#printx('Get Company List...')
#stkurl = 'https://api.iextrading.com/1.0/ref-data/symbols'
#stknames = requests.get(stkurl, verify=False).json() 
#sorted(stknames, key=lambda s: s['symbol'])  # sort by symbol
#printx(len(stknames), 'companies found\n')  # company count in stock market

def GetCompanyName(sym):  # look up company name from symbol
	return '#####'
	for stk in stknames:
		if stk['symbol'] == sym:
			return stk['name']
	else:  # for loop ended
		return '<unknown>'  # symbol not found
		
TD_KEY = 'FY5OVMC0--------RFNULRLY' # get your own (free) key from https://developer.tdameritrade.com

#delayed chain, https://developer.tdameritrade.com/option-chains/apis/get/marketdata/chains# - Registration (free) required to get API Key
#url = 'https://api.tdameritrade.com/v1/marketdata/chains?apikey='+TD_KEY+'&symbol=FCX&contractType=CALL&strikeCount=4&toDate=2021-12-30'
#rsp = requests.get(url).json()

#printx(rsp['callExpDateMap'].keys()) # dict_keys(['2021-10-22:2', '2021-10-29:9', '2021-11-05:16', '2021-11-12:23', '2021-11-19:30', '2021-11-26:37', '2021-12-17:58'])3
#printx(rsp['callExpDateMap']['2021-11-19:30'].keys()) # dict_keys(['37.0', '38.0', '39.0', '40.0'])
#printx(rsp['callExpDateMap']['2021-11-19:30']['37.0'][0].keys()) # dict_keys(['putCall', 'symbol', 'description', 'exchangeName', 'bid', 'ask', 'last', 'mark', 'bidSize', 'askSize', 'bidAskSize', 'lastSize', 'highPrice', 'lowPrice', 'openPrice', 'closePrice', 'totalVolume', 'tradeDate', 'tradeTimeInLong', 'quoteTimeInLong', 'netChange', 'volatility', 'delta', 'gamma', 'theta', 'vega', 'rho', 'openInterest', 'timeValue', 'theoreticalOptionValue', 'theoreticalVolatility', 'optionDeliverablesList', 'strikePrice', 'expirationDate', 'daysToExpiration', 'expirationType', 'lastTradingDay', 'multiplier', 'settlementType', 'deliverableNote', 'isIndexOption', 'percentChange', 'markChange', 'markPercentChange', 'intrinsicValue', 'nonStandard', 'inTheMoney', 'mini', 'pennyPilot'])
#printx(rsp['callExpDateMap']['2021-11-19:30']['37.0'][0]['bid']) # 2.83

def GetOptions(sym): # get option chain for symbol
	for x in [1,2,3]:  # loop, 3 tries if connection error
		try:
			optlst = []
			maxdt = (datetime.now() + timedelta(days=60)).strftime('%Y-%m-%d')  # 2 months from now
			url = 'https://api.tdameritrade.com/v1/marketdata/chains?apikey='+TD_KEY+'&symbol='+sym+'&contractType=CALL&strikeCount=50&toDate=' + maxdt
			rsp = requests.get(url).json() # all call options for this symbol
			#if sym == 'GME': print(rsp)
			#print(rsp)
			# create chain list: expiry, strike, bid, days to exp
			for dt in rsp['callExpDateMap'].keys():  # ['2021-10-22:2', '2021-10-29:9', '2021-11-05:16', ...
				expdays = dt.split(':') # ExpDate:DaysToExp
				for strk in rsp['callExpDateMap'][dt].keys(): # ['37.0', '38.0', '39.0', '40.0']
					optlst.append({'exp':expdays[0], 
												 'strike':float(strk), 
												 'bid':float(rsp['callExpDateMap'][dt][strk][0]['bid']), 
												 'ask':float(rsp['callExpDateMap'][dt][strk][0]['ask']), 
												 'days':int(expdays[1])})
			return optlst # return call option list for this symbol
		except Exception as ex: # error retrieving option data
			if x==3: printx(sym, 'Option Error:', ex) # print last error, continue 
			sleep(2)  # wait 2 seconds, retry

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

printx('Run FinViz screener...')

stock_list = Screener(filters=filters, table='Performance', order='price')  # Get the performance table and sort it by price ascending

# FinViz columns
# ['No.', 'Ticker', 'Perf Week', 'Perf Month', 'Perf Quart', 'Perf Half', 'Perf Year', 'Perf YTD', 
#  'Volatility W', 'Volatility M', 'Recom', 'Avg Volume', 'Rel Volume', 'Price', 'Change', 'Volume']

printx('\n', len(stock_list), 'Stocks found (FinViz)\n') # stock count from finviz filter

stksrt = sorted(stock_list.data, key=lambda d: d['Ticker']) # sort by ticker symbol

printx('Process Options Chains (TD API)\n[Symbol Price Change (EarnDay) Name] [Exp (Days) Strike Bid/Ask %Strike %Spread %StrikeGap]\n')

# update these values to change option scan filter
MinReturn  = 5.0/100   # 5% minimum return
MinBuffer  = 6.0/100   # 8% minimum price safety margin (higher value means less chance that option goes ITM)
MinStrGap  = 2.0/100   # 2% minimum price gap between strikes (higher value means more time to exit position if ITM)
MinPremium = 0.50      # minimum sell premium (bid) 50 cents
MinSpread  = 0.50      # minimum premium spread 50 cents (higher is better, etrade commission is $1 per contract (100 shares), 50 cent spread means 2% commission)
MaxExpDays = 5         # maximum 5 days until expiration (lower is better, focus on weekly options)
IgnoreStk  = ['TNA','TQQQ','UPRO','BRZU','TECL','UDOW','HEI-A','MOG-A'] # skip leveraged indexes, very volatile, high risk

# For each stock from FinViz, get call option chain
# Goal is to find 2 call options where short strike is >= 5% under stock price 
#    AND (short bid - long ask) >= $1 
#    AND (short bid - long ask)/(short strike - long strike) > 10% 
#    Expiry must be under 5 days (weekly).
skip = False # used for earnings check
for trycnt in [1,2]: # if options error, retry failed stocks
	stkretry = [] # error stocks
	for stk in stksrt:  # each stock from finviz
		try:
			if stk['Ticker'] in IgnoreStk: 
				printx('Skipping ignored stock:', stk['Ticker'])
				continue
			disp = False # don't show stock unless option found
			pr = float(stk['Price'])  # stock price
			# print all strikes for each expiry date
			stkcalls = GetOptions(stk['Ticker'])  # list of dictionaries
			#print (stkputs)
			if not stkcalls: 
				stkretry.append(stk) # retry
				continue # no options returned for this symbol
			#print('found calls', stk['Ticker'], pr)
			for cll in stkcalls: # for each call option in option list
				if skip: break # failed earnings check, move to next stock
				if cll['days'] > MaxExpDays: continue# 5 days max, skip these options (too long until expiration) Weekly only
				strike = cll['strike']  # option strike price
				#print(cll)
				# check if possible short option
				if strike >= pr * (1 + MinBuffer) and cll['bid'] > MinPremium: # 5% over price (safety margin), premium > 50 cents
					#print(cll)
					# scan for possible long option
					for cll2 in stkcalls: # scan all calls, ignore calls closer to ATM
						if cll2['days'] != cll['days']: continue # same exp date
						if cll2['strike'] <= cll['strike']: continue  # closer to ATM
						if (cll2['strike'] - cll['strike'])/cll['strike'] < MinStrGap: continue # strikes too close together (if stocks goes ITM, will quickly cross entire spread)
						#if cll2['strike'] <= cll['strike'] * 1.10: continue  # must be at least 5% buffer (safety margin)
						if cll['bid'] - cll2['ask'] <= MinSpread: continue  # premium spread must be at least 50 cents
						if cll['bid'] == 0: continue  # useless call
						#print(cll, '\n', cll2)
						if (cll['bid'] - cll2['ask'])/(cll2['strike'] - cll['strike']) >= MinReturn:	# at least 10% return			
							if not disp: # first option for this stock
								earndays, msg, name = GetEarningsDay(stk['Ticker'], 50) # days until earnings call
								if earndays >= 0 and earndays <= MaxExpDays: # skip stock, high risk if earnings day during option life, stock price may spike
									printx('Skipping earnings stock:', stk['Ticker'])
									skip = True # stop checking options, move to next stock
									break
								# print stock data once
								printx('++', 
											 stk['Ticker'].ljust(6), 
											 str(pr).rjust(7), 
											 str(stk['Change']).rjust(7), 
											 '('+('-' if earndays < 0 else (msg + str(earndays)))+')', 
											 '  ', 
											 name)  #GetCompanyName(stk['Ticker']))
								disp=True # stock already displayed
							# print option data
							printx('>>> ',
										 cll['exp'][5:].rjust(9), 
										 '('+str(cll['days']).rjust(2)+')', 
										 str(cll['strike']).rjust(8), 
										 str(cll['bid']).rjust(8))
							printx('<<<                ',
										 str(cll2['strike']).rjust(8), 
										 str(cll2['ask']).rjust(8), 
										 pct(strike/pr - 1).rjust(8),
										 pct((cll['bid'] - cll2['ask'])/(cll2['strike'] - cll['strike'])).rjust(8),
										 ('    ['+pct((cll2['strike'] - cll['strike'])/cll['strike']).rjust(5)+']'))
			skip = False # reset flag
		except Exception as ex: # error processing data
			printx(stk['Ticker'], 'Error:', ex) # print error, move to next stock
	if trycnt == 1: printx('Retry['+str(trycnt)+']:', [s['Ticker'] for s in stkretry])
	stksrt = stkretry # retry option error
	
printx('\n -- Done --\n')

with open(optlogfile, 'a') as f:
	f.write(optlogtxt)  # write final log to log file



