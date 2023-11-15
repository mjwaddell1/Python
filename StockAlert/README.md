
This script uses tkinter to monitor selected stocks. An alert will be triggered when the stock price crosses the set alert price.

Stock prices (real-time) are retrieved from FinnHub (free account) every minute.

![image](https://github.com/mjwaddell1/Python/assets/35202179/763c26e8-d6c7-4ab4-bfab-e0c496cd2806)

==== Data fields ====

   Stock Name:   Stock name to check<br/>
   
   Alert Price:  Price to trigger alert
   
   Direction:    Alert when price crosses down\up
   
   Last price:   Stock price at last check
   
   Percent Gap:  % difference between stock and alert price
   
   Alert Flag:   Flash main window when alert triggered
   
   < Escape > - Exit

Click the arrow to reverse cross direction
To delete a row, clear the stock name and click "Delete Empty"
Click Start to load stock prices

Settings are automatically saved in StockAlert.dat



