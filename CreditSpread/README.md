Scripts for screening stock options for potential credit spread opportunities

Latest script uses data from MBoum (https://mboum.com/api/overview). I subscribe to the business plan.

You can learn about credit spreads here:
https://www.tastytrade.com/concepts-strategies/vertical-spread

My screeners look for short call or short put spreads using weekly options.

<br/>Sample output of call screener (first rows expanded for explanation):<br/><br/>
![image](https://github.com/mjwaddell1/Python/assets/35202179/46dfdec4-9432-4a6a-a18e-b1b7d110c3f8)

Notes:
- The goal is to sell/write the first option and buy the second option. Profit is made if both options expire out-of-the-money (OTM). 
- The Earnings Date only appears if the date is prior to option expiration. Otherwise a dish (-) is displayed.
- The hit rate (Hit %) is the probability of the sell option going in-the-money (ITM) before expiration. Based on previous 5 years.
- The Strike % is the differece between the current stock price and the sell option strike price. The stock price must rise that percent for the option to go ITM.
- The Profit % is the profit id the credit spread is successfully and both options expire OTM.
- The Strike Gap is the percent the stock price must rise (after going ITM) to lose the entire investement.
