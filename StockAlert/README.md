
This script uses tkinter to monitor selected stocks. An alert will be triggered when the stock price crosses the set alert price.

Stock prices (real-time) are retrieved from FinnHub (free account) every minute.

![image](https://github.com/mjwaddell1/Python/assets/35202179/763c26e8-d6c7-4ab4-bfab-e0c496cd2806)

Data fields:<br />
&nbsp;&nbsp;&nbsp; Stock Name:   Stock name to check<br />
&nbsp;&nbsp;&nbsp; Alert Price:  Price to trigger alert<br />
&nbsp;&nbsp;&nbsp; Direction:    Alert when price crosses down\up<br />
&nbsp;&nbsp;&nbsp; Last price:   Stock price at last check<br />
&nbsp;&nbsp;&nbsp; Percent Gap:  % difference between stock and alert price<br />
&nbsp;&nbsp;&nbsp; Alert Flag:   Flash main window when alert triggered<br />
&nbsp;&nbsp;&nbsp; < Escape > - Exit<br />
<br />
Click the arrow to reverse cross direction<br />
To delete a row, clear the stock name and click "Delete Empty"<br />
Click Start to load stock prices<br />

Settings are automatically saved in StockAlert.dat<br />



