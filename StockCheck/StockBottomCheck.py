import requests, warnings, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import datetime, yfinance as yf
from urllib3.exceptions import InsecureRequestWarning

warnings.simplefilter(action='ignore', category=FutureWarning)
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

# --- Overview ---
# This scripts checks a selected list of stocks for a low (trigger) price
# An email is sent if any alerts are triggered

logtxt = ''

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

def rnd2(val):  # round 2 decimal places
    return str(int(val * 100) / 100.0)

def SendEmail(htmlmsg, subject):
    printx('\nSending email...')
    smtp_server = 'smtprelayna.aon.net'
    port = 25
    sender_email = 'michael.waddell@aon.com'  # 'gate.system@aon.com'
    receiver_email = 'michael.waddell@aon.com;mjwaddell@gmail.com'

    message = MIMEMultipart('alternative')
    message['Subject'] = subject
    message['From'] = sender_email
    message['To'] = receiver_email

    # email client will try to send html message. If error, will send text.
    textmsg = '-- html message failed --\n\n' + htmlmsg.replace('<br/>', '\n')

    # Turn these into plain/html MIMEText objects
    part1 = MIMEText(textmsg, 'plain')
    part2 = MIMEText(htmlmsg, 'html')

    # Add HTML/plain-text parts to MIMEMultipart message
    # The email client will try to render the last part first
    message.attach(part1)
    message.attach(part2)

    server = smtplib.SMTP(smtp_server, port)
    server.sendmail(sender_email, receiver_email, message.as_string())
    server.quit()

sample = {  # from finhub
    "c": 176.55,
    "d": 1.51,  # change
    "dp": 0.8627,  # pct change
    "h": 178.36,
    "l": 174.21,
    "o": 174.285,
    "pc": 175.04,  # prev close
    "t": 1712952001
}

token = 'cl1uje1r01qinXXXXXXXXXXinfqo7eig'  # finhub free account

stocks = [
    # ('VIX',  'Volatility Index', 'NASDAQ', 12), # volatility
    ('AMD',  'Advanced Micro Devices', 'NASDAQ', 70), # AMD
    ('AMZN', 'Amazon', 'NASDAQ', 100), # Amazon
    ('BRZU', 'Brazil', 'NYSEARCA', 60), # Brazil
    ('CFA',  'Volatility Index', 'NASDAQ', 60), # volatility
    ('CURE', 'Healthcare', 'NYSEARCA', 80), # Healthcare
    ('DFEN', 'Defence', 'NYSEARCA', 14), # Defense
    ('DIS',  'Disney', 'NYSE', 80), # Disney
    ('EPR',  'REIT', 'NYSE', 36), # REIT
    ('EURL', 'Europe Index', 'NYSEARCA', 16), # Europe
    ('EXPE', 'Expedia', 'NASDAQ', 95), # Expedia
    ('FLYU', 'Travel Index', 'NYSEARCA', 25), # Travel
    ('GDXU', 'Gold', 'NYSEARCA', 20), # Gold
    ('GM',   'General Motors', 'NYSE', 30), # Gen Motors
    ('GUSH', 'Oil', 'NYSEARCA', 30), # Oil
    ('IAG',  'Gold', 'NYSE', 2.3), # Gold
    ('INTC', 'Intel', 'NASDAQ', 26), # Intel
    ('JPM',  'Chase', 'NYSE', 120), # Chase
    ('LABU', 'Biotech', 'NYSEARCA', 90), # Biotech
    ('MEXX', 'Mexico', 'NYSEARCA', 20), # Mexico
    ('NRGU', 'Oil', 'NYSEARCA', 400), # Oil
    ('NUE',  'Steel', 'NYSE', 145), # Steel
    ('NUGT', 'Gold', 'NYSEARCA', 25), # Gold
    ('OLLI', 'Ollies Bargain Outlet', 'NASDAQ', 45), # Ollies
    ('ON',   'Semiconductor', 'NASDAQ', 60), # Semiconductor
    ('ORLY', 'OReilly Auto', 'NASDAQ', 930), # OReilly Auto
    ('SKYU', 'Cloud Computing', 'NYSEARCA', 16), # Cloud computing
    ('TECL', 'Technology', 'NYSEARCA', 16), # Technology
    ('THO',  'Thor RV', 'NYSE', 70), # Thor RV
    ('TM',   'Toyota', 'NYSE', 175), # Toyota
    ('TNA',  'Small Cap Index', 'NYSEARCA', 25), # Small cap
    ('TQQQ', 'NASDAQ Index', 'NYSEARCA', 20), # NASDAQ
    ('UTSL', 'Volatility Index', 'NASDAQ', 20), # VG utility index
    ('VAW',  'Materials Index', 'NASDAQ', 150), # VG materials index
    ('WGO',  'Winnebago', 'NYSE', 40), # Winnebago
    ('WMT',  'Walmart', 'NYSE', 50), # Walmart
]

curdate = datetime.datetime.today().isoformat()[:10]
prevdate = (datetime.datetime.today() - datetime.timedelta(days=5)).isoformat()[:10]

def GetStockPrice(sym):  # latest price
    # print(curdate,prevdate)
    data = yf.download(sym, start=prevdate, end=curdate)
    dt = max([str(d)[:10] for d in data.index]) # latest date
    # print(data['Close'][dt])
    return data['Close'][dt]

printx('Getting stock data...')

alerts = []
for stk in stocks:
    price = GetStockPrice(stk[0])
    printx((stk, rnd2(price)))
    if price <= stk[3]:
        alerts.append((stk, rnd2(price)))

if len(alerts):  # send email
    printx('\n'.join(str(s) for s in alerts))
    # build html for email
    outstr = ''
    for stk in alerts:
        clr = 'blue'
        symlink = f'<a href="https://www.google.com/finance/quote/{stk[0][0]}:{stk[0][2]}">{stk[0][0]}</a>' # symbol:exchange
        outstr += f'<TR><TD>&nbsp;{symlink}</TD><TD>&nbsp;{stk[0][1]}</TD><TD>&nbsp;{rnd2(stk[0][3])}</TD><TD style="color:blue;">&nbsp;{stk[1]}</TD></TR>\n'

    html = '''\
   <html>
     <body>
       <br/>
       <p>Stock Alerts</p>
       <table border="1" cellspacing="0" cellpadding="2">
       <tr><th>&nbsp;Symbol&nbsp;</th><th>&nbsp;Name&nbsp;</th><th>&nbsp;Trigger&nbsp;</th><th>&nbsp;Price&nbsp;</th></tr>
       xxx
       </table>
     </body>
   </html>
   '''.replace('xxx', outstr)
    subject = f'Stock Bottom Alert - {len(alerts)}'
    printx(html)
    SendEmail(html, subject)

with open('StockBottomCheck.log', 'w') as f:
    f.write(logtxt)  # write full log to log file
