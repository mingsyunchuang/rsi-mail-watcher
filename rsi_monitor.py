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

# 股票代號與名稱直接一組
stock_targets = [
    ("1326.TW", "台化"),
    ("2904.TW", "匯僑"),
    ("2414.TW", "精技"),
    ("2330.TW", "台積電"),
    ("2317.TW", "鴻海"),
    ("2324.TW", "仁寶"),
    ("2347.TW", "聯強"),
    ("2376.TW", "技嘉"),
    ("2414.TW", "精技"),
    ("2489.TW", "瑞軒(零_出)"),
    ("2887.TW", "台新金"),
    ("2891.TW", "中信金"),
    ("2904.TW", "匯僑"),
    ("3211.TW", "順達"),
    ("6101.TW", "寬魚國際_出"),
    ("6189.TW", "豐藝"),
    ("6216.TW", "居易"),
    ("0050.TW", "元大台灣50_低買"),
    ("0056.TW", "元大高股息_低買"),
    ("00919.TW", "群益台灣精選高息_低買"),
    ("00875.TW", "國泰網路資安"),
    ("009802.TW","富邦旗艦50"),
    ("00942B.TW","台新美A公司債"),
    ("2308.TW", "台達電_無"),
    ("1295.TW", "生合生技_益生菌.增肌減脂"),
    ("AAL", "American Airlines"),
    ("AAPL", "Apple"),
    ("AMZN", "Amazon"),
    ("CELH", "Celsius 運動飲料80"),
    ("META", "FaceBook"),
    ("NFLX", "Netflix"),
    ("NVDA", "NVIDIA"),
    ("O", "Realty Income"),
    ("QQQ", "Invesco QQQ"),
    ("SPY", "SPDR S&P 500"),
    ("T", "AT&T"),
    ("TSLA", "Tesla"),
    ("ZIM", "以星航運"),
    ("VTI", "Vanguard Total Stock Mkt"),
    ("MSFT", "Microsoft"),
    ("COST", "Costco"),
    ("WRD", "中國廣東.文遠知行.自動駕駛技術開發"),
    ("QS", "QuantumScape.開發新型固態鋰金屬電池")
]
rsi_days = 14

def get_indicators(symbol, rsi_period=14, bb_period=20, bb_std=2):
    data = yf.download(symbol, period='60d', interval='1d')
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
for stock, stock_name in stock_targets:
    try:
        rsi_val, last_date, last_close, bb_upper, bb_lower = get_indicators(stock, rsi_days)
        stock_display = f"{stock} ({stock_name})"
        message = f"{stock_display} 收盤日: {last_date} 收盤價: {last_close:.2f} "
        if rsi_val <= 40:
            content += f"{message}RSI={rsi_val:.2f} 低於40\n"
        if last_close <= bb_lower:
            content += f"{message}低於布林下軌({bb_lower:.2f})\n"
        if last_close >= bb_upper:
            content += f"{message}高於布林上軌({bb_upper:.2f})\n"
    except Exception as e:
        stock_display = f"{stock} ({stock_name})"
        content += f"{stock_display} 無法取得資料或計算錯誤: {e}\n"

if content:
    send_email("RSI/布林警報", content)
