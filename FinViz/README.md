
This script scrapes Finviz and returns the stock data as a dictionary. The stock filter can be set within the script.

The Finviz page has 2 sections to retrieve data:

Main table (ticker\name\price\change):

![image](https://github.com/mjwaddell1/Python/assets/35202179/ad3f3bb5-a632-459c-90b5-708e3e4fe56c)

Comment (ticker\price\volume):

![image](https://github.com/mjwaddell1/Python/assets/35202179/abf6703c-38db-4748-8be2-a89031731399)

To use these scripts, just copy the code into your script and call the oppropriate function (usually GetFinVizStocksTbl).

To get the desired filters, go to finviz, set filters and copy the filter list from the URL   
https ://finviz.com/screener.ashx?v=111&f=<b>sh_opt_option,sh_price_o500,ta_volatility_mo3</b>&r=1
