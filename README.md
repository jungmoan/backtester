# Stock Trading Backtester

주식 자동매매를 위한 백테스팅 시스템입니다.

## 프로젝트 구조

```
backtester/
├── requirements.txt          # 필요한 Python 패키지
├── config/
│   └── config.py            # 설정 파일
├── data/
│   ├── loader.py            # 데이터 로더
│   └── preprocessor.py      # 데이터 전처리
├── strategies/
│   ├── base_strategy.py     # 기본 전략 클래스
│   ├── moving_average.py    # 이동평균 전략
│   └── rsi_strategy.py      # RSI 전략
├── backtester/
│   ├── engine.py            # 백테스팅 엔진
│   ├── portfolio.py         # 포트폴리오 관리
│   └── metrics.py           # 성과 분석 지표
├── visualization/
│   └── analyzer.py          # 결과 시각화
├── results/                 # 백테스트 결과 저장 폴더
├── main.py                  # 메인 실행 파일
├── simple_example.py        # 간단한 사용 예제
└── analyze_results.py       # 결과 분석 및 시각화
```

## 설치

1. 프로젝트 클론
```bash
git clone <repository_url>
cd backtester
```

2. 필요한 패키지 설치
```bash
pip install -r requirements.txt
```

## 실행

### 1. 전체 백테스트 실행
```bash
python main.py
```

### 2. 간단한 예제 실행
```bash
python simple_example.py
```

### 3. 결과 분석 및 시각화
```bash
python analyze_results.py
```

## 주요 기능

### 📈 지원하는 전략
- **이동평균 교차 전략**: 단기/장기 이동평균선의 골든크로스/데드크로스
- **이동평균 추세 전략**: 가격이 상승추세 이동평균선 위에 있을 때 매수
- **RSI 전략**: 과매도/과매수 구간에서의 역추세 매매
- **RSI 평균회귀 전략**: 극단적 RSI 구간에서의 평균회귀 매매

### 📊 성과 분석 지표
- **수익률 지표**: 총수익률, 연환산수익률
- **리스크 지표**: 변동성, 샤프비율, 최대낙폭(MDD)
- **거래 지표**: 승률, 총거래횟수, 수익팩터
- **시각화**: 포트폴리오 성과 차트, 거래 분석, 전략 비교

### 💾 결과 저장
- CSV 형태로 상세한 결과 저장
- 포트폴리오 히스토리, 거래 내역, 성과 보고서
- PNG 형태의 차트 자동 생성

## 사용 예제

### 기본 사용법
```python
from strategies.moving_average import MovingAverageStrategy
from backtester.engine import BacktestEngine

# 전략 생성
strategy = MovingAverageStrategy(short_window=5, long_window=20)

# 백테스트 엔진 생성
engine = BacktestEngine(strategy, initial_capital=10_000_000)

# 백테스트 실행
results = engine.run_backtest(
    symbol='005930.KS',  # 삼성전자
    start_date='2023-01-01',
    end_date='2024-12-31'
)

# 결과 출력 및 저장
engine.print_results()
engine.save_results_to_csv("my_backtest")
```

### 커스텀 전략 만들기
```python
from strategies.base_strategy import BaseStrategy, SignalType

class MyStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("My Custom Strategy")
    
    def generate_signals(self, data):
        df = data.copy()
        df['signal'] = SignalType.HOLD
        
        # 여기에 매매 로직 구현
        # df.loc[buy_condition, 'signal'] = SignalType.BUY
        # df.loc[sell_condition, 'signal'] = SignalType.SELL
        
        return df
    
    def get_description(self):
        return "내가 만든 커스텀 전략"
```

## 설정

`config/config.py`에서 백테스트 설정을 변경할 수 있습니다:

```python
class Config:
    INITIAL_CAPITAL = 10_000_000  # 초기 자본
    COMMISSION_RATE = 0.003       # 수수료율
    SLIPPAGE_RATE = 0.001         # 슬리피지
    POSITION_SIZE = 0.1           # 포지션 크기
    START_DATE = "2020-01-01"     # 기본 시작일
    END_DATE = "2024-12-31"       # 기본 종료일
```

## 지원하는 주식

### 한국 주식 (KRX)
- 삼성전자 (005930.KS)
- SK하이닉스 (000660.KS)
- NAVER (035420.KS)
- LG화학 (051910.KS)
- 삼성SDI (006400.KS)

### 미국 주식 (NYSE/NASDAQ)
- Apple (AAPL)
- Google (GOOGL)
- Microsoft (MSFT)
- Tesla (TSLA)
- NVIDIA (NVDA)

## 결과 파일 설명

백테스트 실행 후 `results/` 폴더에 다음 파일들이 생성됩니다:

- `*_portfolio.csv`: 일별 포트폴리오 가치 변화
- `*_trades.csv`: 상세한 거래 내역
- `*_report.csv`: 성과 지표 요약
- `*_positions.csv`: 최종 보유 포지션
- `*_chart.png`: 포트폴리오 성과 차트
- `*_analysis.png`: 거래 분석 차트
- `strategy_comparison.png`: 전략 비교 차트

## 개발자 정보

이 프로젝트는 주식 자동매매 시스템의 사전 검증을 위한 백테스팅 도구입니다.

## 면책 조항

이 소프트웨어는 교육 및 연구 목적으로만 사용되어야 합니다. 실제 투자 결정에 사용하기 전에 충분한 검토와 테스트를 수행하시기 바랍니다. 투자에는 항상 리스크가 따르며, 과거 성과가 미래 수익을 보장하지 않습니다.
