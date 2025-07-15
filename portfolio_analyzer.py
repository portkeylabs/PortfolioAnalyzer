import pandas as pd
import numpy as np
import time
from datetime import datetime, date
from typing import Dict, List, Optional
from stock import TICKER_MAP
import yfinance as yf

class PortfolioAnalyzer:
    """Main portfolio analysis engine"""
    
    def __init__(self, transactions_df: pd.DataFrame, stock_fetcher):
        self.transactions_df = transactions_df
        self.stock_fetcher = stock_fetcher
        # Ensure correct dtypes
        self.transactions_df['quantity'] = pd.to_numeric(self.transactions_df['quantity'], errors='coerce')
        self.transactions_df['price'] = pd.to_numeric(self.transactions_df['price'], errors='coerce')
        self.transactions_df = self.transactions_df.dropna(subset=['quantity', 'price'])


    def get_unique_symbols(self) -> List[str]:
        """Get unique stock symbols from transactions (excluding non-stock entries)"""
        # Filter out non-stock symbols
        stock_transactions = self.transactions_df[
            ~self.transactions_df['symbol'].isin(['COMMISSION', 'CASH_WITHDRAWAL', 'CASH_DEPOSIT'])
        ]
        return stock_transactions['symbol'].unique().tolist()
    
    def fetch_yf_info_with_retry(self,  ticker, retries=3, delay=3, history_period=None):
        for attempt in range(retries):
            try:
                yf_stock = yf.Ticker(ticker)
                if history_period:
                    hist = yf_stock.history(period=history_period)
                    if hist is not None and not hist.empty:
                        return hist
                else:
                    info = yf_stock.info
                    if info and not ('code' in info and info['code'] == 'Not Found'):
                        return info
            except Exception as e:
                if attempt < retries - 1:
                    time.sleep(delay)
                else:
                    raise e
        return None
         
    def calculate_current_holdings_without_prices(self) -> pd.DataFrame:
        """Calculate current holdings without current market prices"""
        holdings = []
        
        for symbol in self.get_unique_symbols():
            symbol_transactions = self.transactions_df[
                (self.transactions_df['symbol'] == symbol) & 
                (self.transactions_df['action'].isin(['Buy', 'Sell']))
            ].copy()
            
            if symbol_transactions.empty:
                continue
            
            # Calculate total shares and average cost
            total_shares = 0
            total_cost = 0
            
            for _, transaction in symbol_transactions.iterrows():
                quantity = transaction['quantity']
                price = transaction['price']
                
                if transaction['action'] == 'Buy':
                    total_shares += quantity
                    total_cost += quantity * price
                else:  # Sell
                    total_shares -= quantity
                    # For sells, we reduce the total cost proportionally
                    if total_shares > 0:
                        avg_cost = total_cost / (total_shares + quantity) if (total_shares + quantity) > 0 else 0
                        total_cost -= quantity * avg_cost
            
            if total_shares > 0:
                avg_cost = total_cost / total_shares
                holdings.append({
                    'symbol': symbol,
                    'quantity': total_shares,
                    'avg_cost': avg_cost,
                    'total_invested': total_cost,
                    'current_price': avg_cost,  # Use average cost as placeholder
                    'current_value': total_cost,  # Use total invested as current value
                    'gain_loss': 0.0,  # No gain/loss without current prices
                    'gain_loss_pct': 0.0,
                    'allocation_pct': 0.0  # Will be calculated after all holdings
                })
        
        holdings_df = pd.DataFrame(holdings)
        
        # Calculate allocation percentages
        if not holdings_df.empty:
            total_value = holdings_df['current_value'].sum()
            if total_value > 0:
                holdings_df['allocation_pct'] = (holdings_df['current_value'] / total_value) * 100
        
        return holdings_df
    
    def calculate_current_holdings(self) -> pd.DataFrame:
        """Calculate current holdings and their performance using yfinance, using 'Close' for ETFs if 'currentPrice' is unavailable."""
        holdings = []
        skipped_stocks = []

        for symbol in self.get_unique_symbols():
            ticker = TICKER_MAP.get(symbol, symbol)
            try:
                info = self.fetch_yf_info_with_retry(ticker)
                if not info:
                    skipped_stocks.append({
                        "symbol": symbol,
                        "ticker": ticker,
                        "reason": "No data found"
                    })
                    continue

                current_price = info.get("currentPrice", "N/A")
                market = info.get("market", "N/A")
                sector = info.get("sector", "N/A")
    
                # If current price is N/A, try to get the latest close price from historical data
                if current_price == "N/A":
                    try:
                        hist = self.fetch_yf_info_with_retry(ticker, history_period="1d")
                        if hist is not None and not hist.empty and "Close" in hist.columns:
                            current_price = hist["Close"].iloc[-1]
                    except Exception:
                        current_price = "N/A"
    
                # If still N/A, check market and sector, and skip if both are N/A
                if current_price == "N/A" and (market == "N/A" or sector == "N/A"):
                    skipped_stocks.append({
                        "symbol": symbol,
                        "ticker": ticker,
                        "reason": f"Missing info: price={current_price}, market={market}, sector={sector}"
                    })
                    continue
                
            except Exception as e:
                print(f"Warning: Could not fetch data for {symbol} ({ticker}): {str(e)}")
                skipped_stocks.append({
                    "symbol": symbol,
                    "ticker": ticker,
                    "reason": f"Error fetching data: {str(e)}"
                })
                continue
            
            symbol_transactions = self.transactions_df[
                (self.transactions_df['symbol'] == symbol) & 
                (self.transactions_df['action'].isin(['Buy', 'Sell']))
            ].copy()
    
            if symbol_transactions.empty:
                continue
            
            total_bought = float(symbol_transactions[symbol_transactions['action'] == 'Buy']['quantity'].sum())
            total_cost = float((symbol_transactions[symbol_transactions['action'] == 'Buy']['quantity'] * 
                          symbol_transactions[symbol_transactions['action'] == 'Buy']['price']).sum())
            total_sold = float(symbol_transactions[symbol_transactions['action'] == 'Sell']['quantity'].sum())
    
            current_quantity = total_bought - total_sold
    
            if current_quantity > 0:
                avg_cost = (total_cost - (total_sold / total_bought * total_cost)) / current_quantity if total_bought > 0 else 0
                current_value = current_quantity * current_price
                gain_loss = current_value - (current_quantity * avg_cost)
                gain_loss_pct = (gain_loss / (current_quantity * avg_cost)) * 100 if avg_cost > 0 else 0
    
                holdings.append({
                    'symbol': symbol,
                    'ticker': ticker,
                    'quantity': current_quantity,
                    'avg_cost': avg_cost,
                    'current_price': current_price,
                    'current_value': current_value,
                    'gain_loss': gain_loss,
                    'gain_loss_pct': gain_loss_pct,
                    'market': market,
                    'sector': sector
                })
    
        holdings_df = pd.DataFrame(holdings)
        if not holdings_df.empty:
            total_value = holdings_df['current_value'].sum()
            holdings_df['allocation_pct'] = (holdings_df['current_value'] / total_value) * 100
    
        # Optionally, print skipped stocks for reporting
        if skipped_stocks:
            print("Skipped stocks due to missing info:")
            for s in skipped_stocks:
                print(s)
    
        return holdings_df
    
    def calculate_portfolio_summary_without_prices(self) -> Dict:
        """Calculate overall portfolio summary statistics without current prices"""
        holdings_df = self.calculate_current_holdings_without_prices()
        
        if holdings_df.empty:
            return {
                'total_invested': 0.0,
                'current_value': 0.0,
                'total_gain_loss': 0.0,
                'total_gain_loss_pct': 0.0,
                'realized_gain_loss': 0.0,
                'unrealized_gain_loss': 0.0,
                'num_positions': 0
            }
        
        total_invested = holdings_df['total_invested'].sum()
        current_value = holdings_df['current_value'].sum()
        realized_gain_loss = self._calculate_realized_gains_losses()
        
        return {
            'total_invested': total_invested,
            'current_value': current_value,
            'total_gain_loss': 0.0,  # No gain/loss without current prices
            'total_gain_loss_pct': 0.0,
            'realized_gain_loss': realized_gain_loss,
            'unrealized_gain_loss': 0.0,
            'num_positions': len(holdings_df)
        }
    
    def calculate_portfolio_summary(self, current_prices: Dict[str, float]) -> Dict:
        """Calculate overall portfolio summary statistics"""
        holdings = self.calculate_current_holdings()
        
        # Calculate total invested
        buy_transactions = self.transactions_df[self.transactions_df['action'] == 'Buy']
        total_invested = (buy_transactions['quantity'] * buy_transactions['price']).sum()
        
        # Calculate current value
        current_value = holdings['current_value'].sum() if not holdings.empty else 0
        
        # Calculate realized gains/losses from sales
        realized_gain_loss = self._calculate_realized_gains_losses()
        
        # Calculate unrealized gains/losses
        unrealized_gain_loss = holdings['gain_loss'].sum() if not holdings.empty else 0
        
        # Total gain/loss
        total_gain_loss = realized_gain_loss + unrealized_gain_loss
        
        return {
            'total_invested': total_invested,
            'current_value': current_value,
            'realized_gain_loss': realized_gain_loss,
            'unrealized_gain_loss': unrealized_gain_loss,
            'total_gain_loss': total_gain_loss
        }
    
    def _calculate_realized_gains_losses(self) -> float:
        """Calculate realized gains/losses from completed sales"""
        realized_gl = 0
        
        for symbol in self.get_unique_symbols():
            symbol_transactions = self.transactions_df[
                (self.transactions_df['symbol'] == symbol) & 
                (self.transactions_df['action'].isin(['Buy', 'Sell']))
            ].copy()
            
            if symbol_transactions.empty:
                continue
            
            # Sort by date
            symbol_transactions = symbol_transactions.sort_values('date')
            
            # FIFO calculation for realized gains
            bought_lots = []
            
            for _, transaction in symbol_transactions.iterrows():
                if transaction['action'] == 'Buy':
                    bought_lots.append({
                        'quantity': transaction['quantity'],
                        'price': transaction['price']
                    })
                elif transaction['action'] == 'Sell':
                    remaining_to_sell = transaction['quantity']
                    sale_price = transaction['price']
                    
                    while remaining_to_sell > 0 and bought_lots:
                        lot = bought_lots[0]
                        
                        if lot['quantity'] <= remaining_to_sell:
                            # Sell entire lot
                            realized_gl += lot['quantity'] * (sale_price - lot['price'])
                            remaining_to_sell -= lot['quantity']
                            bought_lots.pop(0)
                        else:
                            # Partial lot sale
                            realized_gl += remaining_to_sell * (sale_price - lot['price'])
                            lot['quantity'] -= remaining_to_sell
                            remaining_to_sell = 0
        
        return realized_gl
    
    def calculate_performance_over_time_without_prices(self) -> pd.DataFrame:
        """Calculate portfolio value over time without current prices"""
        if self.transactions_df.empty:
            return pd.DataFrame()
        
        # Get stock transactions only (exclude dividends, commissions, etc.)
        stock_transactions = self.transactions_df[
            (self.transactions_df['action'].isin(['Buy', 'Sell'])) &
            (~self.transactions_df['symbol'].isin(['COMMISSION', 'CASH_WITHDRAWAL', 'CASH_DEPOSIT']))
        ].copy()
        
        if stock_transactions.empty:
            return pd.DataFrame()
        
        # Sort by date
        stock_transactions = stock_transactions.sort_values('date')
        
        # Calculate cumulative investment over time
        performance_data = []
        cumulative_investment = 0
        
        for _, transaction in stock_transactions.iterrows():
            transaction_value = transaction['quantity'] * transaction['price']
            
            if transaction['action'] == 'Buy':
                cumulative_investment += transaction_value
            else:  # Sell
                cumulative_investment -= transaction_value
            
            performance_data.append({
                'date': transaction['date'],
                'cumulative_investment': cumulative_investment,
                'portfolio_value': cumulative_investment  # Use investment as value without prices
            })
        
        return pd.DataFrame(performance_data)
    
    def calculate_performance_over_time(self, current_prices: Dict[str, float]) -> pd.DataFrame:
        """Calculate portfolio value over time"""
        if self.transactions_df.empty:
            return pd.DataFrame()
        
        # Get date range
        start_date = pd.to_datetime(self.transactions_df['date']).min()
        end_date = pd.to_datetime(datetime.now().date())
        
        # Create monthly date range
        date_range = pd.date_range(start=start_date, end=end_date, freq='M')
        
        performance_data = []
        
        for target_date in date_range:
            # Calculate holdings as of this date
            historical_transactions = self.transactions_df[
                pd.to_datetime(self.transactions_df['date']) <= target_date
            ]
            
            if historical_transactions.empty:
                continue
            
            # Calculate portfolio value at this point
            total_invested = 0
            current_value = 0
            
            for symbol in historical_transactions['symbol'].unique():
                symbol_trans = historical_transactions[
                    (historical_transactions['symbol'] == symbol) &
                    (historical_transactions['action'].isin(['Buy', 'Sell']))
                ]
                
                if symbol_trans.empty:
                    continue
                
                # Calculate position
                total_bought = symbol_trans[symbol_trans['action'] == 'Buy']['quantity'].sum()
                total_sold = symbol_trans[symbol_trans['action'] == 'Sell']['quantity'].sum()
                current_quantity = total_bought - total_sold
                
                if current_quantity > 0:
                    # Calculate total cost for this position
                    buy_cost = (symbol_trans[symbol_trans['action'] == 'Buy']['quantity'] * 
                               symbol_trans[symbol_trans['action'] == 'Buy']['price']).sum()
                    sell_proceeds = (symbol_trans[symbol_trans['action'] == 'Sell']['quantity'] * 
                                   symbol_trans[symbol_trans['action'] == 'Sell']['price']).sum()
                    
                    # Proportional cost for remaining shares
                    if total_bought > 0:
                        cost_per_share = buy_cost / total_bought
                        position_cost = current_quantity * cost_per_share
                        total_invested += position_cost
                        
                        # Current value using current prices
                        current_price = current_prices.get(symbol, cost_per_share)
                        current_value += current_quantity * current_price
            
            performance_data.append({
                'date': target_date,
                'total_invested': total_invested,
                'portfolio_value': current_value,
                'gain_loss': current_value - total_invested
            })
        
        return pd.DataFrame(performance_data)
    
    def calculate_sector_allocation(self, current_prices: Dict[str, float]) -> pd.DataFrame:
        """Calculate portfolio allocation by sector"""
        holdings = self.calculate_current_holdings(current_prices)
        
        if holdings.empty:
            return pd.DataFrame()
        
        # Get sector information for each stock
        sector_data = []
        
        for _, holding in holdings.iterrows():
            symbol = holding['symbol']
            sector = self.stock_fetcher.get_stock_sector(symbol)
            
            sector_data.append({
                'symbol': symbol,
                'sector': sector,
                'value': holding['current_value'],
                'allocation_pct': holding['allocation_pct']
            })
        
        sector_df = pd.DataFrame(sector_data)
        
        if sector_df.empty:
            return pd.DataFrame()
        
        # Aggregate by sector
        sector_summary = sector_df.groupby('sector').agg({
            'value': 'sum',
            'allocation_pct': 'sum'
        }).reset_index()
        
        return sector_summary
    
    def calculate_dividend_summary(self) -> Dict:
        """Calculate dividend income summary"""
        # Get both dividend payments and withdrawals
        dividend_transactions = self.transactions_df[
            self.transactions_df['action'].isin(['Dividend', 'Dividend_Withdrawal'])
        ].copy()
        
        total_dividends = 0
        dividend_count = 0
        dividend_history = pd.DataFrame()
        
        if not dividend_transactions.empty:
            # Calculate net dividends (payments minus withdrawals)
            dividend_payments = dividend_transactions[dividend_transactions['action'] == 'Dividend']['price'].sum()
            dividend_withdrawals = dividend_transactions[dividend_transactions['action'] == 'Dividend_Withdrawal']['price'].sum()
            
            total_dividends = dividend_payments - dividend_withdrawals
            dividend_count = len(dividend_transactions[dividend_transactions['action'] == 'Dividend'])
            
            # Prepare dividend history with proper amount signs
            dividend_history = dividend_transactions[['date', 'symbol', 'price', 'action']].copy()
            dividend_history['amount'] = dividend_history.apply(
                lambda row: row['price'] if row['action'] == 'Dividend' else -row['price'], axis=1
            )
            dividend_history = dividend_history[['date', 'symbol', 'amount']].copy()
            dividend_history = dividend_history.sort_values('date', ascending=False)
        
        return {
            'total_dividends': total_dividends,
            'dividend_count': dividend_count,
            'dividend_history': dividend_history
        }
