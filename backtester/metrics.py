import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime

class PerformanceMetrics:
    """성과 분석 지표 계산 클래스"""
    
    @staticmethod
    def calculate_returns(portfolio_values: pd.Series) -> pd.Series:
        """수익률 계산"""
        return portfolio_values.pct_change().dropna()
    
    @staticmethod
    def calculate_total_return(initial_value: float, final_value: float) -> float:
        """총 수익률"""
        return (final_value / initial_value - 1) * 100
    
    @staticmethod
    def calculate_annualized_return(total_return: float, days: int) -> float:
        """연환산 수익률"""
        return ((1 + total_return / 100) ** (365 / days) - 1) * 100
    
    @staticmethod
    def calculate_volatility(returns: pd.Series) -> float:
        """변동성 (연환산)"""
        return returns.std() * np.sqrt(252) * 100  # 252일 = 1년 거래일
    
    @staticmethod
    def calculate_sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """샤프 비율"""
        excess_returns = returns - risk_free_rate / 252  # 일일 무위험 수익률
        if excess_returns.std() == 0:
            return 0
        return (excess_returns.mean() / excess_returns.std()) * np.sqrt(252)
    
    @staticmethod
    def calculate_max_drawdown(portfolio_values: pd.Series) -> Tuple[float, str, str]:
        """최대 낙폭 (MDD)"""
        if portfolio_values.empty:
            return 0.0, "N/A", "N/A"
        
        rolling_max = portfolio_values.expanding().max()
        drawdowns = (portfolio_values - rolling_max) / rolling_max
        max_drawdown = drawdowns.min()
        
        # MDD 발생 기간 찾기
        try:
            mdd_end_date = drawdowns.idxmin()
            mdd_start_date = portfolio_values.loc[:mdd_end_date].idxmax()
            
            # 날짜를 문자열로 변환
            if hasattr(mdd_start_date, 'strftime'):
                mdd_start_str = mdd_start_date.strftime('%Y-%m-%d')
            else:
                mdd_start_str = str(mdd_start_date)
                
            if hasattr(mdd_end_date, 'strftime'):
                mdd_end_str = mdd_end_date.strftime('%Y-%m-%d')
            else:
                mdd_end_str = str(mdd_end_date)
                
            return max_drawdown * 100, mdd_start_str, mdd_end_str
        except:
            return max_drawdown * 100, "N/A", "N/A"
    
    @staticmethod
    def calculate_win_rate(trade_history: pd.DataFrame) -> Dict[str, float]:
        """승률 계산"""
        if trade_history.empty:
            return {'win_rate': 0, 'total_trades': 0, 'winning_trades': 0}
        
        # 매수-매도 쌍 매칭
        trades = []
        buy_orders = {}
        
        for _, row in trade_history.iterrows():
            symbol = row['symbol']
            
            if row['action'] == 'BUY':
                if symbol not in buy_orders:
                    buy_orders[symbol] = []
                buy_orders[symbol].append(row)
            
            elif row['action'] == 'SELL' and symbol in buy_orders:
                if buy_orders[symbol]:
                    buy_order = buy_orders[symbol].pop(0)  # FIFO
                    profit = (row['price'] - buy_order['price']) * row['quantity']
                    trades.append({
                        'symbol': symbol,
                        'buy_date': buy_order['date'],
                        'sell_date': row['date'],
                        'buy_price': buy_order['price'],
                        'sell_price': row['price'],
                        'quantity': row['quantity'],
                        'profit': profit,
                        'return': (row['price'] / buy_order['price'] - 1) * 100
                    })
        
        if not trades:
            return {'win_rate': 0, 'total_trades': 0, 'winning_trades': 0}
        
        winning_trades = sum(1 for trade in trades if trade['profit'] > 0)
        total_trades = len(trades)
        win_rate = (winning_trades / total_trades) * 100
        
        return {
            'win_rate': win_rate,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': total_trades - winning_trades
        }
    
    @staticmethod
    def calculate_profit_factor(trade_history: pd.DataFrame) -> float:
        """수익 팩터 (총 수익 / 총 손실)"""
        if trade_history.empty:
            return 0
        
        # 매수-매도 쌍 매칭하여 개별 거래 수익 계산
        trades = []
        buy_orders = {}
        
        for _, row in trade_history.iterrows():
            symbol = row['symbol']
            
            if row['action'] == 'BUY':
                if symbol not in buy_orders:
                    buy_orders[symbol] = []
                buy_orders[symbol].append(row)
            
            elif row['action'] == 'SELL' and symbol in buy_orders:
                if buy_orders[symbol]:
                    buy_order = buy_orders[symbol].pop(0)
                    profit = (row['price'] - buy_order['price']) * row['quantity']
                    trades.append(profit)
        
        if not trades:
            return 0
        
        total_profit = sum(profit for profit in trades if profit > 0)
        total_loss = abs(sum(profit for profit in trades if profit < 0))
        
        if total_loss == 0:
            return float('inf') if total_profit > 0 else 0
        
        return total_profit / total_loss
    
    @classmethod
    def generate_performance_report(cls, portfolio_history: pd.DataFrame, 
                                  trade_history: pd.DataFrame, 
                                  initial_capital: float) -> Dict:
        """종합 성과 보고서 생성"""
        if portfolio_history.empty:
            return {}
        
        portfolio_values = portfolio_history['total_value']
        returns = cls.calculate_returns(portfolio_values)
        
        # 기본 지표
        final_value = portfolio_values.iloc[-1]
        total_return = cls.calculate_total_return(initial_capital, final_value)
        
        # 기간 계산
        start_date = portfolio_history['date'].iloc[0]
        end_date = portfolio_history['date'].iloc[-1]
        days = (end_date - start_date).days
        
        # 성과 지표
        annualized_return = cls.calculate_annualized_return(total_return, days)
        volatility = cls.calculate_volatility(returns)
        sharpe_ratio = cls.calculate_sharpe_ratio(returns)
        max_drawdown, mdd_start, mdd_end = cls.calculate_max_drawdown(portfolio_values)
        
        # 거래 관련 지표
        win_stats = cls.calculate_win_rate(trade_history)
        profit_factor = cls.calculate_profit_factor(trade_history)
        
        report = {
            # 기본 정보
            '초기자본': f"{initial_capital:,.0f}원",
            '최종자본': f"{final_value:,.0f}원",
            '순손익': f"{final_value - initial_capital:,.0f}원",
            
            # 수익률 지표
            '총수익률': f"{total_return:.2f}%",
            '연환산수익률': f"{annualized_return:.2f}%",
            '변동성': f"{volatility:.2f}%",
            '샤프비율': f"{sharpe_ratio:.2f}",
            
            # 리스크 지표
            '최대낙폭': f"{max_drawdown:.2f}%",
            'MDD기간': f"{mdd_start} ~ {mdd_end}",
            
            # 거래 지표
            '총거래횟수': win_stats['total_trades'],
            '승률': f"{win_stats['win_rate']:.2f}%",
            '승리거래': win_stats['winning_trades'],
            '패배거래': win_stats['losing_trades'],
            '수익팩터': f"{profit_factor:.2f}",
            
            # 기간
            '백테스트기간': f"{start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}",
            '운용일수': f"{days}일"
        }
        
        return report
