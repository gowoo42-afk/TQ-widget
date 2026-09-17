import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from PIL import Image, ImageEnhance
import requests
import io
import os

# 1. 폰트 설정 (Ubuntu GitHub Actions의 나눔고딕)
plt.rcParams['font.family'] = 'NanumGothic'
plt.rcParams['axes.unicode_minus'] = False

def create_widget():
    # 2. TQQQ 데이터 수집 (최근 350거래일)
    ticker = yf.Ticker("TQQQ")
    df = ticker.history(period="18mo")
    if df.empty:
        raise Exception("데이터를 가져오지 못했습니다.")

    # 3. 200일 이동평균선 및 지표 계산
    df['MA200'] = df['Close'].rolling(window=200).mean()
    df = df.dropna().tail(80) # 차트에는 최근 80거래일 표시

    latest = df.iloc[-1]
    prev = df.iloc[-2]

    curr_price = latest['Close']
    prev_price = prev['Close']
    ma200_val = latest['MA200']

    chg = curr_price - prev_price
    chg_pct = (chg / prev_price) * 100
    gap_pct = ((curr_price / ma200_val) - 1) * 100
    is_bull = curr_price >= ma200_val

    # 전략 신호 판별
    signal_text = "매수/보유" if is_bull else "매도/관망"
    signal_color = "#4ADE80" if is_bull else "#F87171"

    # 4. 차트 그래픽 설정 (4x2 비율: 800 x 380px 고화질)
    fig = plt.figure(figsize=(8, 3.8), dpi=150, facecolor='#0F172A')
    ax = fig.add_axes([0.06, 0.12, 0.88, 0.55]) # [left, bottom, width, height]
    ax.set_facecolor('#0F172A')

    # 차트 선 그리기
    dates = df.index
    ax.plot(dates, df['MA200'], color='#38BDF8', linewidth=2.0, label='200 MA', zorder=2)
    ax.plot(dates, df['Close'], color='#FFFFFF', linewidth=2.5, label='Close', zorder=3)

    # 종가 하단 은은한 그라데이션 채우기
    ax.fill_between(dates, df['Close'], df['MA200'].min()*0.95, color='#FFFFFF', alpha=0.06, zorder=1)

    # 축 & 눈금 정리
    ax.spines['top'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_color('rgba(255,255,255,0.15)')
    ax.spines['right'].set_visible(False)

    ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
    ax.tick_params(axis='x', colors='#64748B', labelsize=9)
    ax.yaxis.tick_right()
    ax.tick_params(axis='y', colors='#64748B', labelsize=9)
    ax.grid(True, linestyle='--', alpha=0.08, color='#FFFFFF')

    # 5. 상단 텍스트 헤더 렌더링
    # TQQQ 가격
    fig.text(0.06, 0.88, f"TQQQ ${curr_price:.2f}", fontsize=18, fontweight='bold', color='#FFFFFF')
    
    # 등락률
    chg_sign = "+" if chg >= 0 else ""
    fig.text(0.35, 0.88, f"{chg_sign}{chg:.2f} ({chg_sign}{chg_pct:.2f}%)", 
             fontsize=12, fontweight='bold', color="#4ADE80" if chg >= 0 else "#F87171")

    # 200선 & 이격도
    gap_sign = "+" if gap_pct >= 0 else ""
    fig.text(0.06, 0.74, f"200선 ${ma200_val:.1f}  |  이격도 {gap_sign}{gap_pct:.1f}%", 
             fontsize=10.5, color='#94A3B8')

    # 시그널 배지
    fig.text(0.80, 0.88, f"● {signal_text}", fontsize=12, fontweight='bold', 
             color=signal_color, bbox=dict(boxstyle='round,pad=0.4', facecolor='rgba(255,255,255,0.05)', edgecolor=signal_color, alpha=0.8))

    # 임시 이미지 버퍼 저장
    buf = io.BytesIO()
    plt.savefig(buf, format='png', facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    buf.seek(0)

    # 6. 피카츄 공식 일러스트 합성 (Pillow)
    base_img = Image.open(buf).convert("RGBA")
    pika_url = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/25.png"
    pika_res = requests.get(pika_url)
    pika_img = Image.open(io.BytesIO(pika_res.content)).convert("RGBA")

    # 하락장(매도/관망)일 땐 톤다운 및 흑백 처리
    if not is_bull:
        pika_img = ImageEnhance.Color(pika_img).enhance(0.2)
        pika_img = ImageEnhance.Brightness(pika_img).enhance(0.8)

    # 피카츄 리사이즈 (가로세로 95px)
    pika_img = pika_img.resize((95, 95), Image.Resampling.LANCZOS)

    # 상단 적정 위치에 합성 (X: 470px, Y: 10px)
    base_img.paste(pika_img, (490, 15), pika_img)

    # 최종 widget.png 저장
    base_img.save("widget.png", "PNG")
    print("widget.png 생성 완료!")

if __name__ == "__main__":
    create_widget()
