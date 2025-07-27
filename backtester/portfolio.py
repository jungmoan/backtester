import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional

class Position:
    """포지션 클래스"""
    
    def __init__(self, symbol: str, quantity: int, entry_price: float, entry_date: datetime):
        self.symbol = symbol
        self.quantity = quantity
        self.entry_price = entry_price
        self.entry_date = entry_date
        
    def get_value(self, current_price: float) -> float:
        """현재 포지션 가치"""
        return self.quantity * current_price
    
    def get_unrealized_pnl(self, current_price: float) -> float:
        """미실현 손익"""
        return (current_price - self.entry_price) * self.quantity

class Portfolio:
    """포트폴리오 관리 클래스"""
    
    def __init__(self, initial_capital: float, commission_rate: float = 0.003, slippage_rate: float = 0.001):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.commission_rate = commission_rate
        self.slippage_rate = slippage_rate
        self.positions: Dict[str, Position] = {}
        self.trade_history: List[Dict] = []
        self.portfolio_history: List[Dict] = []
        
    def buy_stock(self, symbol: str, price: float, quantity: int, date: datetime) -> bool:
        """주식 매수"""
        # 슬리피지 적용
        adjusted_price = price * (1 + self.slippage_rate)
        
        # 수수료 포함 총 비용
        total_cost = adjusted_price * quantity
        commission = total_cost * self.commission_rate
        total_cost_with_commission = total_cost + commission
        
        # 현금 충분한지 확인
        if self.cash < total_cost_with_commission:
            return False
        
        # 매수 실행
        self.cash -= total_cost_with_commission
        
        if symbol in self.positions:
            # 기존 포지션에 추가
            existing_pos = self.positions[symbol]
            new_quantity = existing_pos.quantity + quantity
            new_avg_price = ((existing_pos.entry_price * existing_pos.quantity) + 
                           (adjusted_price * quantity)) / new_quantity
            self.positions[symbol] = Position(symbol, new_quantity, new_avg_price, existing_pos.entry_date)
        else:
            # 새 포지션 생성
            self.positions[symbol] = Position(symbol, quantity, adjusted_price, date)
        
        # 거래 기록
        self.trade_history.append({
            'date': date,
            'symbol': symbol,
            'action': 'BUY',
            'quantity': quantity,
            'price': adjusted_price,
            'commission': commission,
            'total_cost': total_cost_with_commission
        })
        
        return True
    
    def sell_stock(self, symbol: str, price: float, quantity: int, date: datetime) -> bool:
        """주식 매도"""
        if symbol not in self.positions:
            return False
        
        position = self.positions[symbol]
        if position.quantity < quantity:
            return False
        
        # 슬리피지 적용
        adjusted_price = price * (1 - self.slippage_rate)
        
        # 매도 수익
        total_revenue = adjusted_price * quantity
        commission = total_revenue * self.commission_rate
        net_revenue = total_revenue - commission
        
        # 매도 실행
        self.cash += net_revenue
        position.quantity -= quantity
        
        # 포지션이 0이 되면 제거
        if position.quantity == 0:
            del self.positions[symbol]
        
        # 거래 기록
        self.trade_history.append({
            'date': date,
            'symbol': symbol,
            'action': 'SELL',
            'quantity': quantity,
            'price': adjusted_price,
            'commission': commission,
            'net_revenue': net_revenue
        })
        
        return True
    
    def get_portfolio_value(self, current_prices: Dict[str, float]) -> float:
        """현재 포트폴리오 총 가치"""
        positions_value = sum(
            pos.get_value(current_prices.get(symbol, pos.entry_price)) 
            for symbol, pos in self.positions.items()
        )
        return self.cash + positions_value
    
    def get_positions_summary(self, current_prices: Dict[str, float]) -> pd.DataFrame:
        """현재 포지션 요약"""
        if not self.positions:
            return pd.DataFrame()
        
        data = []
        for symbol, position in self.positions.items():
            current_price = current_prices.get(symbol, position.entry_price)
            data.append({
                '종목': symbol,
                '수량': position.quantity,
                '매수가격': position.entry_price,
                '현재가격': current_price,
                '총가치': position.get_value(current_price),
                '미실현손익': position.get_unrealized_pnl(current_price),
                '수익률': (current_price / position.entry_price - 1) * 100
            })
        
        return pd.DataFrame(data)
    
    def record_portfolio_state(self, date: datetime, current_prices: Dict[str, float]):
        """포트폴리오 상태 기록"""
        total_value = self.get_portfolio_value(current_prices)
        
        self.portfolio_history.append({
            'date': date,
            'cash': self.cash,
            'positions_value': total_value - self.cash,
            'total_value': total_value,
            'return': (total_value / self.initial_capital - 1) * 100
        })
    
    def get_trade_history_df(self) -> pd.DataFrame:
        """거래 내역을 DataFrame으로 반환"""
        return pd.DataFrame(self.trade_history)
    
    def get_portfolio_history_df(self) -> pd.DataFrame:
        """포트폴리오 내역을 DataFrame으로 반환"""
        return pd.DataFrame(self.portfolio_history)
