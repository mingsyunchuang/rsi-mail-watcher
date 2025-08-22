import yfinance as yf
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.header import Header
import os

your_email = "mingsyunapp@gmail.com"
app_password = os.environ.get('GMAIL_APP_PASSWORD')
stock_list = ["2330.TW", "0050.TW", "0056.TW", "00919.TW", "AAPL", "TSLA"]
rsi_days = 14

def get_rsi_and_last_price(symbol, period=14):
    data = yf.download(symbol, period='60d', interval='1d')
    close = data['Close'].dropna()
    if close.empty:
        raise ValueError("無法取得收盤價資料")
    last_date = close.index[-1].strftime('%Y-%m-%d')
    # 取出 float，避免 Series 顯示
    close_value = close.iloc[-1]
    # 若為Series需再取第一個
    if isinstance(close_value, pd.Series):
        last_close = float(close_value.values[0])
    else:
        last_close = float(close_value)
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    last_rsi = float(rsi.dropna().values[-1])
    return last_rsi, last_date, last_close


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
    try:
        rsi_val, last_date, last_close = get_rsi_and_last_price(stock, rsi_days)
        if rsi_val > 30:
            content += f"{stock} 收盤日: {last_date} 收盤價: {last_close:.2f} RSI={rsi_val:.2f} 低於30\n"
    except Exception as e:
        content += f"{stock} 無法取得資料或計算錯誤: {e}\n"

if content:
    send_email("RSI警報", content)
