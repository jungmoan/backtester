#!/usr/bin/env python3
"""
백테스트 엔진 모듈
- 포트폴리오 관리
- 거래 실행
- 성과 분석
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime


class BacktestEngine:
    """백테스트 실행 엔진"""
    
    def __init__(self, initial_capital: float = 10000):
        self.initial_capital = initial_capital
        
    def run_backtest(self, data: pd.DataFrame, strategy_data: pd.DataFrame, stop_loss_pct: float = None, support_resistance_lookback: int = None) -> Dict:
        """백테스트 실행
        
        Args:
            data: 원본 OHLCV 데이터
            strategy_data: 전략 신호가 포함된 데이터
            stop_loss_pct: 손절매 비율 (예: 5.0 = 5% 손실시 매도)
            support_resistance_lookback: 지지/저항선 계산을 위한 lookback 기간
            
        Returns:
            백테스트 결과 딕셔너리
        """
        cash = self.initial_capital
        position = 0
        portfolio_values = []
        trades = []
        buy_signals = []
        sell_signals = []
        buy_price = 0  # 매수가격 기록 (손절매용)
        support_levels = []  # 지지선 레벨들
        
        # 지지/저항선 계산 (옵션)
        if support_resistance_lookback:
            support_levels = self._calculate_support_levels(strategy_data, support_resistance_lookback)
        
        for i, (date, row) in enumerate(strategy_data.iterrows()):
            price = row['Close']
            signal = row.get('Signal', 0)
            
            # 손절매 체크 (포지션이 있을 때만)
            if position > 0:
                stop_loss_triggered = False
                stop_loss_reason = ""
                
                # 1. 비율 기반 손절매
                if stop_loss_pct and buy_price > 0:
                    loss_pct = ((buy_price - price) / buy_price) * 100
                    if loss_pct >= stop_loss_pct:
                        stop_loss_triggered = True
                        stop_loss_reason = f"Stop Loss ({loss_pct:.2f}%)"
                
                # 2. 지지선 기반 손절매 (비율 기반 손절매가 발생하지 않은 경우에만)
                if not stop_loss_triggered and support_resistance_lookback and i < len(support_levels):
                    current_support = support_levels[i]
                    if current_support > 0 and price < current_support * 0.98:  # 지지선 2% 하향 돌파
                        stop_loss_triggered = True
                        stop_loss_reason = f"Support Break ({current_support:.2f})"
                
                # 손절매 실행
                if stop_loss_triggered:
                    cash += position * price
                    trades.append({
                        'date': date,
                        'action': 'STOP_LOSS',
                        'price': price,
                        'shares': position,
                        'portfolio_value': cash,
                        'reason': stop_loss_reason
                    })
                    sell_signals.append({'date': date, 'price': price, 'type': 'stop_loss'})
                    position = 0
                    buy_price = 0
                    # 손절매가 발생하면 이번 루프에서는 다른 신호 처리하지 않음
                
                # 손절매가 발생하지 않은 경우에만 매도 신호 처리
                elif signal == -1:
                    cash += position * price
                    trades.append({
                        'date': date,
                        'action': 'SELL',
                        'price': price,
                        'shares': position,
                        'portfolio_value': cash
                    })
                    sell_signals.append({'date': date, 'price': price, 'type': 'strategy'})
                    position = 0
                    buy_price = 0
            
            # 매수 신호 처리 (포지션이 없을 때만)
            elif position == 0 and signal == 1:
                shares = (cash * 0.95) / price  # 95% 투자 (수수료 고려)
                cash -= shares * price
                position = shares
                buy_price = price  # 매수가격 기록
                trades.append({
                    'date': date,
                    'action': 'BUY',
                    'price': price,
                    'shares': shares,
                    'portfolio_value': cash + position * price
                })
                buy_signals.append({'date': date, 'price': price, 'type': 'strategy'})
            
            # 포트폴리오 가치 기록
            total_value = cash + position * price
            portfolio_values.append({
                'date': date,
                'portfolio_value': total_value,
                'cash': cash,
                'position_value': position * price,
                'price': price
            })
        
        # 최종 청산
        if position > 0:
            final_price = strategy_data['Close'].iloc[-1]
            cash += position * final_price
            sell_signals.append({'date': strategy_data.index[-1], 'price': final_price, 'type': 'final'})
        
        return {
            'portfolio_history': pd.DataFrame(portfolio_values),
            'trades': trades,
            'buy_signals': buy_signals,
            'sell_signals': sell_signals,
            'final_value': cash,
            'strategy_data': strategy_data
        }
    
    def _calculate_support_levels(self, data: pd.DataFrame, lookback: int) -> List[float]:
        """지지선 레벨 계산
        
        Args:
            data: OHLCV 데이터
            lookback: 지지선 계산을 위한 lookback 기간
            
        Returns:
            각 시점별 지지선 레벨 리스트
        """
        support_levels = []
        
        for i in range(len(data)):
            if i < lookback:
                support_levels.append(0)  # 충분한 데이터가 없을 때
                continue
            
            # 과거 lookback 기간의 최저가들을 분석
            recent_data = data.iloc[max(0, i-lookback):i]
            lows = recent_data['Low'].values
            
            # 지지선 후보들 찾기 (지역 최저점들)
            support_candidates = []
            for j in range(2, len(lows)-2):
                if (lows[j] <= lows[j-1] and lows[j] <= lows[j-2] and 
                    lows[j] <= lows[j+1] and lows[j] <= lows[j+2]):
                    support_candidates.append(lows[j])
            
            # 가장 최근의 중요한 지지선 선택
            if support_candidates:
                # 현재 가격과 가까운 지지선 우선 선택
                current_price = data['Close'].iloc[i]
                support_candidates.sort(key=lambda x: abs(current_price - x))
                support_level = support_candidates[0]
            else:
                # 지지선이 없으면 최근 기간의 최저가 사용
                support_level = recent_data['Low'].min()
            
            support_levels.append(support_level)
        
        return support_levels
    
    def validate_trades(self, result: Dict) -> Dict:
        """거래 유효성 검증
        
        Args:
            result: run_backtest의 결과
            
        Returns:
            검증 결과 딕셔너리
        """
        trades = result['trades']
        issues = []
        
        # 포지션 상태 추적
        position = 0
        
        for i, trade in enumerate(trades):
            action = trade['action']
            
            if action == 'BUY':
                if position > 0:
                    issues.append(f"Trade {i}: BUY signal when already holding position")
                position = trade['shares']
                
            elif action in ['SELL', 'STOP_LOSS']:
                if position <= 0:
                    issues.append(f"Trade {i}: {action} signal when no position held")
                position = 0
        
        return {
            'is_valid': len(issues) == 0,
            'issues': issues,
            'total_trades': len(trades),
            'buy_trades': len([t for t in trades if t['action'] == 'BUY']),
            'sell_trades': len([t for t in trades if t['action'] == 'SELL']),
            'stop_loss_trades': len([t for t in trades if t['action'] == 'STOP_LOSS'])
        }
    
    def calculate_metrics(self, result: Dict) -> Dict:
        """성과 지표 계산
        
        Args:
            result: run_backtest의 결과
            
        Returns:
            성과 지표 딕셔너리
        """
        portfolio_df = result['portfolio_history']
        trades = result['trades']
        
        if portfolio_df.empty:
            return {}
        
        # 기본 지표
        final_value = result['final_value']
        total_return = (final_value / self.initial_capital - 1) * 100
        
        # 수익률 시계열
        portfolio_values = portfolio_df['portfolio_value']
        returns = portfolio_values.pct_change().dropna()
        
        # 샤프 비율
        if len(returns) > 1 and returns.std() > 0:
            sharpe_ratio = (returns.mean() / returns.std()) * np.sqrt(252)
        else:
            sharpe_ratio = 0
        
        # 최대 낙폭
        rolling_max = portfolio_values.expanding().max()
        drawdowns = (portfolio_values - rolling_max) / rolling_max
        max_drawdown = drawdowns.min() * 100
        
        # 변동성
        volatility = returns.std() * np.sqrt(252) * 100 if len(returns) > 1 else 0
        
        # 거래 분석
        buy_trades = [t for t in trades if t['action'] == 'BUY']
        sell_trades = [t for t in trades if t['action'] in ['SELL', 'STOP_LOSS']]
        
        # 승률 계산 (손절매는 패배로 처리)
        trade_returns = []
        for i in range(min(len(buy_trades), len(sell_trades))):
            buy_price = buy_trades[i]['price']
            sell_trade = sell_trades[i]
            sell_price = sell_trade['price']
            trade_return = (sell_price - buy_price) / buy_price * 100
            
            # 손절매는 무조건 패배로 처리 (음수 수익률로 강제 설정)
            if sell_trade['action'] == 'STOP_LOSS' and trade_return > 0:
                trade_return = -abs(trade_return)
            
            trade_returns.append(trade_return)
        
        win_rate = 0
        winning_trades = 0
        if trade_returns:
            winning_trades = sum(1 for ret in trade_returns if ret > 0)
            win_rate = (winning_trades / len(trade_returns)) * 100
        
        # 손익비 계산
        profit_loss_ratio = 0
        if trade_returns:
            profits = [ret for ret in trade_returns if ret > 0]
            losses = [ret for ret in trade_returns if ret < 0]
            
            if profits and losses:
                avg_profit = np.mean(profits)
                avg_loss = abs(np.mean(losses))
                profit_loss_ratio = avg_profit / avg_loss
        
        # 연간 수익률
        trading_days = len(portfolio_df)
        if trading_days > 252:
            years = trading_days / 252
            annual_return = ((final_value / self.initial_capital) ** (1/years) - 1) * 100
        else:
            annual_return = total_return
        
        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'final_value': final_value,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'volatility': volatility,
            'win_rate': win_rate,
            'profit_loss_ratio': profit_loss_ratio,
            'total_trades': len(trade_returns),
            'winning_trades': winning_trades,
            'losing_trades': len(trade_returns) - winning_trades,
            'avg_trade_return': np.mean(trade_returns) if trade_returns else 0,
            'best_trade': max(trade_returns) if trade_returns else 0,
            'worst_trade': min(trade_returns) if trade_returns else 0,
            'total_profit': sum(ret for ret in trade_returns if ret > 0),
            'total_loss': sum(ret for ret in trade_returns if ret < 0)
        }
    
    def calculate_advanced_metrics(self, result: Dict) -> Dict:
        """고급 성과 지표 계산"""
        portfolio_df = result['portfolio_history']
        
        if portfolio_df.empty:
            return {}
        
        portfolio_values = portfolio_df['portfolio_value']
        returns = portfolio_values.pct_change().dropna()
        
        # 소르티노 비율 (하락 변동성만 고려)
        downside_returns = returns[returns < 0]
        if len(downside_returns) > 0:
            downside_std = downside_returns.std() * np.sqrt(252)
            sortino_ratio = (returns.mean() * 252) / downside_std
        else:
            sortino_ratio = 0
        
        # 칼마 비율 (연간수익률 / 최대낙폭)
        rolling_max = portfolio_values.expanding().max()
        drawdowns = (portfolio_values - rolling_max) / rolling_max
        max_drawdown_pct = abs(drawdowns.min())
        
        if max_drawdown_pct > 0:
            calmar_ratio = (returns.mean() * 252) / max_drawdown_pct
        else:
            calmar_ratio = 0
        
        # VaR (Value at Risk) 95%
        var_95 = np.percentile(returns, 5) * 100 if len(returns) > 0 else 0
        
        # 최대 연속 손실 일수
        underwater = drawdowns < 0
        max_consecutive_losses = 0
        current_consecutive = 0
        
        for underwater_day in underwater:
            if underwater_day:
                current_consecutive += 1
                max_consecutive_losses = max(max_consecutive_losses, current_consecutive)
            else:
                current_consecutive = 0
        
        return {
            'sortino_ratio': sortino_ratio,
            'calmar_ratio': calmar_ratio,
            'var_95': var_95,
            'max_consecutive_losses': max_consecutive_losses,
            'total_trading_days': len(portfolio_df),
            'profitable_days': len(returns[returns > 0]),
            'losing_days': len(returns[returns < 0])
        }


class PortfolioAnalyzer:
    """포트폴리오 분석 도구"""
    
    @staticmethod
    def calculate_benchmark_comparison(portfolio_data: pd.DataFrame, benchmark_data: pd.DataFrame) -> Dict:
        """벤치마크 대비 성과 분석"""
        if portfolio_data.empty or benchmark_data.empty:
            return {}
        
        portfolio_returns = portfolio_data['portfolio_value'].pct_change().dropna()
        benchmark_returns = benchmark_data['Close'].pct_change().dropna()
        
        # 알파와 베타 계산
        if len(portfolio_returns) > 1 and len(benchmark_returns) > 1:
            covariance = np.cov(portfolio_returns, benchmark_returns)[0][1]
            benchmark_variance = np.var(benchmark_returns)
            
            if benchmark_variance > 0:
                beta = covariance / benchmark_variance
                alpha = portfolio_returns.mean() - beta * benchmark_returns.mean()
            else:
                beta = 0
                alpha = 0
        else:
            beta = 0
            alpha = 0
        
        return {
            'alpha': alpha * 252 * 100,  # 연간화
            'beta': beta,
            'correlation': np.corrcoef(portfolio_returns, benchmark_returns)[0][1] if len(portfolio_returns) > 1 else 0
        }
    
    @staticmethod
    def calculate_monthly_returns(portfolio_data: pd.DataFrame) -> pd.DataFrame:
        """월별 수익률 계산"""
        if portfolio_data.empty:
            return pd.DataFrame()
        
        portfolio_data = portfolio_data.copy()
        portfolio_data['date'] = pd.to_datetime(portfolio_data['date'])
        portfolio_data.set_index('date', inplace=True)
        
        monthly_values = portfolio_data['portfolio_value'].resample('M').last()
        monthly_returns = monthly_values.pct_change().dropna() * 100
        
        return monthly_returns.to_frame('monthly_return')
    
    @staticmethod
    def calculate_rolling_metrics(portfolio_data: pd.DataFrame, window: int = 252) -> pd.DataFrame:
        """롤링 성과 지표 계산"""
        if portfolio_data.empty or len(portfolio_data) < window:
            return pd.DataFrame()
        
        portfolio_values = portfolio_data['portfolio_value']
        returns = portfolio_values.pct_change().dropna()
        
        rolling_sharpe = returns.rolling(window).apply(
            lambda x: (x.mean() / x.std()) * np.sqrt(252) if x.std() > 0 else 0
        )
        
        rolling_volatility = returns.rolling(window).std() * np.sqrt(252) * 100
        
        rolling_max = portfolio_values.rolling(window, min_periods=1).max()
        rolling_drawdown = (portfolio_values - rolling_max) / rolling_max * 100
        
        return pd.DataFrame({
            'rolling_sharpe': rolling_sharpe,
            'rolling_volatility': rolling_volatility,
            'rolling_drawdown': rolling_drawdown
        }, index=portfolio_data['date'])
