#!/usr/bin/env python3
"""
단일 종목 SMI 전략 테스트 스크립트
"""

import yfinance as yf
import pandas as pd
from strategies import StrategyManager

def test_single_stock():
    """단일 종목으로 SMI 전략 테스트"""
    
    # 테스트할 종목
    symbol = "AAPL"
    
    print(f"Testing SMI strategy on {symbol}...")
    
    try:
        # 데이터 다운로드
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="1y")
        
        if data.empty:
            print(f"No data for {symbol}")
            return
        
        # 주말 제거
        data = data[data.index.dayofweek < 5]
        data = data[data['Volume'] > 0]
        
        print(f"Data shape: {data.shape}")
        print(f"Data columns: {data.columns.tolist()}")
        print(f"Data sample:\n{data.head()}")
        
        # 전략 매니저 생성
        strategy_manager = StrategyManager()
        
        # SMI 전략 파라미터
        strategy_params = {
            'bb_period': 20,
            'bb_mult': 2.0,
            'kc_period': 20,
            'kc_mult': 1.5,
            'momentum_period': 12
        }
        
        print(f"\nApplying SMI strategy with params: {strategy_params}")
        
        # 전략 신호 계산
        strategy_data = strategy_manager.calculate_signals("Squeeze Momentum", data, **strategy_params)
        
        print(f"Strategy data shape: {strategy_data.shape}")
        print(f"Strategy data columns: {strategy_data.columns.tolist()}")
        print(f"Signal column sample:\n{strategy_data['Signal'].value_counts()}")
        
        print(f"✅ SMI strategy test successful for {symbol}")
        
    except Exception as e:
        print(f"❌ Error testing {symbol}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_single_stock()
