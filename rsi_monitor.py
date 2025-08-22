import yfinance as yf
import smtplib
from email.mime.text import MIMEText
from email.header import Header
import os

your_email = "mingsyunapp@gmail.com"
app_password = os.environ.get('GMAIL_APP_PASSWORD')
stock_list = ["2330.TW", "0050.TW", "AAPL"]
rsi_days = 14

def get_rsi(symbol, days=14):
    data = yf.download(symbol, period=f'{days+30}d', interval='1d')
    if data.shape[0] < days + 1:
        return None
    close = data['Close']
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -1 * delta.clip(upper=0)
    avg_gain = gain.rolling(window=days, min_periods=days).mean()
    avg_loss = loss.rolling(window=days, min_periods=days).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]

def send_email(subject, body):
    msg = MIMEText(body, 'plain', 'utf-8')
    msg['From'] = your_email
    msg['To'] = your_email
    msg['Cc'] = "mingsyun@hotmail.com"
    msg['Subject'] = Header(subject, 'utf-8').encode()
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(your_email, app_password)
        server.sendmail(your_email, [your_email], msg.as_string())

content = ""
for stock in stock_list:
    rsi_val = get_rsi(stock, rsi_days)
    if rsi_val is not None and not rsi_val.empty and rsi_val.iloc[-1] > 30:
        content += f"{stock} RSI={rsi_val:.2f} 低於30\n"

if content:
    send_email("RSI警報", content)
