import yfinance as yf
import pandas as pd
import streamlit as st
from typing import Dict, List, Optional
import time
from datetime import datetime, timedelta

class StockDataFetcher:
    """Handle stock data fetching from Yahoo Finance"""
    
    def __init__(self):
        self.sector_cache = {}
        self.price_cache = {}
        self.cache_timestamp = {}
        self.cache_duration = 300  # 5 minutes cache
    
    def get_current_prices(self, symbols: List[str]) -> Dict[str, float]:
        """Fetch current stock prices for given symbols"""
        prices = {}
        
        if not symbols:
            return prices
        
        try:
            # Check cache first
            current_time = time.time()
            cached_symbols = []
            fresh_symbols = []
            
            for symbol in symbols:
                if (symbol in self.price_cache and 
                    symbol in self.cache_timestamp and
                    current_time - self.cache_timestamp[symbol] < self.cache_duration):
                    prices[symbol] = self.price_cache[symbol]
                    cached_symbols.append(symbol)
                else:
                    fresh_symbols.append(symbol)
            
            if cached_symbols:
                st.info(f"📋 Using cached prices for {len(cached_symbols)} symbols")
            
            # Fetch fresh data for uncached symbols
            if fresh_symbols:
                st.info(f"🔄 Fetching current prices for {len(fresh_symbols)} symbols...")
                
                # Batch fetch for efficiency
                symbols_str = ' '.join(fresh_symbols)
                
                try:
                    tickers = yf.Tickers(symbols_str)
                    
                    for symbol in fresh_symbols:
                        try:
                            ticker = tickers.tickers[symbol]
                            hist = ticker.history(period="1d")
                            
                            if not hist.empty:
                                current_price = hist['Close'].iloc[-1]
                                prices[symbol] = float(current_price)
                                
                                # Update cache
                                self.price_cache[symbol] = float(current_price)
                                self.cache_timestamp[symbol] = current_time
                            else:
                                st.warning(f"⚠️ No price data found for {symbol}")
                                prices[symbol] = 0.0
                                
                        except Exception as e:
                            st.warning(f"⚠️ Error fetching price for {symbol}: {str(e)}")
                            prices[symbol] = 0.0
                            
                except Exception as e:
                    st.error(f"❌ Error in batch price fetch: {str(e)}")
                    # Fallback to individual fetching
                    for symbol in fresh_symbols:
                        prices[symbol] = self._fetch_individual_price(symbol)
                        
        except Exception as e:
            st.error(f"❌ Error fetching stock prices: {str(e)}")
            # Return zero prices as fallback
            for symbol in symbols:
                prices[symbol] = 0.0
        
        return prices
    
    def _fetch_individual_price(self, symbol: str) -> float:
        """Fetch price for individual symbol as fallback"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1d")
            
            if not hist.empty:
                return float(hist['Close'].iloc[-1])
            else:
                return 0.0
                
        except Exception as e:
            st.warning(f"⚠️ Error fetching individual price for {symbol}: {str(e)}")
            return 0.0
    
    def get_stock_sector(self, symbol: str) -> str:
        """Get sector information for a stock symbol"""
        if symbol in self.sector_cache:
            return self.sector_cache[symbol]
        
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            sector = info.get('sector', 'Unknown')
            if sector is None:
                sector = 'Unknown'
            
            # Cache the result
            self.sector_cache[symbol] = sector
            return sector
            
        except Exception as e:
            # Default sector if fetch fails
            default_sector = 'Unknown'
            self.sector_cache[symbol] = default_sector
            return default_sector
    
    def get_stock_info(self, symbol: str) -> Dict:
        """Get comprehensive stock information"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            return {
                'symbol': symbol,
                'company_name': info.get('longName', symbol),
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown'),
                'market_cap': info.get('marketCap', 0),
                'pe_ratio': info.get('trailingPE', 0),
                'dividend_yield': info.get('dividendYield', 0),
                'beta': info.get('beta', 0)
            }
            
        except Exception as e:
            return {
                'symbol': symbol,
                'company_name': symbol,
                'sector': 'Unknown',
                'industry': 'Unknown',
                'market_cap': 0,
                'pe_ratio': 0,
                'dividend_yield': 0,
                'beta': 0
            }
    
    def get_historical_prices(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Get historical price data for a symbol"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(start=start_date, end=end_date)
            
            if not hist.empty:
                hist = hist.reset_index()
                hist['Symbol'] = symbol
                return hist[['Date', 'Symbol', 'Open', 'High', 'Low', 'Close', 'Volume']]
            else:
                return pd.DataFrame()
                
        except Exception as e:
            st.warning(f"⚠️ Error fetching historical data for {symbol}: {str(e)}")
            return pd.DataFrame()
    
    def validate_symbols(self, symbols: List[str]) -> Dict[str, bool]:
        """Validate if stock symbols exist"""
        validation_results = {}
        
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="5d")
                validation_results[symbol] = not hist.empty
                
            except Exception:
                validation_results[symbol] = False
        
        return validation_results
    
    def clear_cache(self):
        """Clear all cached data"""
        self.price_cache.clear()
        self.sector_cache.clear()
        self.cache_timestamp.clear()
        st.success("✅ Price cache cleared")
