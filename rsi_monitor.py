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

# 股票代號與中文名稱對應表
stock_name_map = {
    "1326.TW": "台化",
    "2904.TW": "匯僑",
    "2414.TW": "精技",
    "2330.TW": "台積電",
    "2317.TW": "鴻海",
    "2376.TW": "技嘉",
    "6216.TW": "居易",
    "0050.TW": "元大台灣50",
    "0056.TW": "元大高股息",
    "00919.TW": "群益台灣精選高息",
    "00875.TW": "國泰永續高股息",
    "QQQ": "Invesco QQQ",
    "SPY": "SPDR S&P 500",
    "VTI": "Vanguard Total Stock Mkt",
    "AAPL": "Apple",
    "TSLA": "Tesla",
    "NVDA": "NVIDIA",
    "AMZN": "Amazon",
    "NFLX": "Netflix",
    "MSFT": "Microsoft",
    "AAL": "American Airlines",
    "T": "AT&T",
    "COST": "Costco",
    "CELH": "Celsius",
    "O": "Realty Income"
}

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
        stock_name = stock_name_map.get(stock, "")
        if stock_name:
            stock_display = f"{stock} ({stock_name})"
        else:
            stock_display = stock
        message = f"{stock_display} 收盤日: {last_date} 收盤價: {last_close:.2f} "
        # 僅當RSI 低於40觸發
        if rsi_val <= 40:
            content += f"{message}RSI={rsi_val:.2f} 低於40\n"
        # 僅當收盤價低於布林下軌
        if last_close <= bb_lower:
            content += f"{message}低於布林下軌({bb_lower:.2f})\n"
        # 僅當收盤價高於布林上軌
        if last_close >= bb_upper:
            content += f"{message}高於布林上軌({bb_upper:.2f})\n"
    except Exception as e:
        stock_name = stock_name_map.get(stock, "")
        if stock_name:
            stock_display = f"{stock} ({stock_name})"
        else:
            stock_display = stock
        content += f"{stock_display} 無法取得資料或計算錯誤: {e}\n"

if content:
    send_email("RSI/布林警報", content)
