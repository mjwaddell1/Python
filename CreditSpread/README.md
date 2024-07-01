Scripts for screening stock options for potential credit spread opportunities

Latest script uses data from MBoum (https://mboum.com/api/overview). I subscribe to the business plan.

You can learn about credit spreads here:
https://www.tastytrade.com/concepts-strategies/vertical-spread

My screeners look for short call or short put spreads using weekly options.

I have had better luck with call spreads vs put spreads.<br/>
ScreenerCallSpreadMB is the latest script and most up to date.

<br/>Sample output of call screener (first rows expanded for explanation):<br/><br/>&nbsp;&nbsp;
![image](https://github.com/mjwaddell1/Python/assets/35202179/6d0f55d5-7a75-46c3-83b6-d403b4d48a7e)

Notes:
- The goal is to sell/write the first option and buy the second option. Profit is made if both options expire out-of-the-money (OTM). 
- The Earnings Date only appears if the date is prior to option expiration. Otherwise a dash (-) is displayed.
- The Hit % is the probability of the sell option going in-the-money (ITM) before expiration. This is based on the previous year.
- The Strike % is the differece between the current stock price and the sell option strike price. The stock price must rise this percent for the option to go ITM.
- The Profit % is the profit if the credit spread is successful and both options expire OTM.
- The Strike Gap % is the percent the stock price must rise (after going ITM) to lose the entire investement.
- All option combinations are checked based on minimum required values (profit %, strike gap, option price, price spread) set in script.
