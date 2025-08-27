import yfinance as yf
import smtplib
from email.mime.text import MIMEText
from email.header import Header
import os
import pandas as pd
from ta.momentum import RSIIndicator

your_email = "mingsyunapp@gmail.com"
cc_emails = ["mingsyun@hotmail.com"]
app_password = os.environ.get('GMAIL_APP_PASSWORD')
stock_list = [
    "1326.TW", "2904.TW", "2414.TW", "2330.TW", "2317.TW", "2376.TW", "6216.TW",
    "0050.TW", "0056.TW", "00919.TW", "00875.TW",
    "QQQ","SPY","VTI", "AAPL", "TSLA", "NVDA", "AMZN", "NFLX", "MSFT", "AAL", "T", "COST", "CELH","O"
]
rsi_days = 14

def get_indicators(symbol, rsi_period=14, bb_period=20, bb_std=2):
    data = yf.download(symbol, period='60d', interval='1d')
    # 防止多層DataFrame，取正確symbol資料
    if isinstance(data['Close'], pd.DataFrame):
        close = data['Close'][symbol].dropna()
    else:
        close = data['Close'].dropna()
    if close.empty:
        raise ValueError("無法取得收盤價資料")
    last_date = close.index[-1].strftime('%Y-%m-%d')
    last_close = float(close.iloc[-1])
    from ta.momentum import RSIIndicator
    rsi = RSIIndicator(close, window=rsi_period).rsi()
    last_rsi = float(rsi.dropna().values[-1])
    ma = close.rolling(window=bb_period).mean()
    std = close.rolling(window=bb_period).std()
    upper = float(ma.iloc[-1] + bb_std * std.iloc[-1])
    lower = float(ma.iloc[-1] - bb_std * std.iloc[-1])
    return last_rsi, last_date, last_close, upper, lower


def send_email(subject, body):
    to_emails = [your_email]
    all_recipients = to_emails + cc_emails
    msg = MIMEText(body, 'plain', 'utf-8')
    msg['From'] = your_email
    msg['To'] = ', '.join(to_emails)
    msg['Cc'] = ', '.join(cc_emails)
    msg['Subject'] = Header(subject, 'utf-8').encode()
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(your_email, app_password)
        server.sendmail(your_email, all_recipients, msg.as_string())

content = ""
for stock in stock_list:
    try:
        rsi_val, last_date, last_close, bb_upper, bb_lower = get_indicators(stock, rsi_days)
        message = f"{stock} 收盤日: {last_date} 收盤價: {last_close:.2f} "
        # 僅當RSI 低於30觸發
        if rsi_val <= 40:
            content += f"{message}RSI={rsi_val:.2f} 低於30\n"
        # 僅當收盤價低於布林下軌
        if last_close <= bb_lower:
            content += f"{message}低於布林下軌({bb_lower:.2f})\n"
        # 僅當收盤價高於布林上軌
        if last_close >= bb_upper:
            content += f"{message}高於布林上軌({bb_upper:.2f})\n"
    except Exception as e:
        content += f"{stock} 無法取得資料或計算錯誤: {e}\n"

if content:
    send_email("RSI/布林警報", content)
