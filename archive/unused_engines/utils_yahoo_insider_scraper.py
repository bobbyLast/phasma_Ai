"""
Yahoo Finance Insider Data Scraper
Reliable source for insider trading data
"""

import yfinance as yf
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import re


class YahooInsiderScraper:
    """Scrape insider trading data from Yahoo Finance"""
    
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
    
    def fetch_insider_buys_for_tickers(self, tickers: List[str], min_value: int = 50000, days_back: int = 7) -> List[Dict]:
        """Fetch insider buys for a list of tickers"""
        
        print(f"[YAHOO] Checking insider buys for {len(tickers)} tickers...")
        
        all_buys = []
        
        for ticker in tickers:
            try:
                buys = self._fetch_ticker_insider_data(ticker, min_value, days_back)
                all_buys.extend(buys)
                
                # Small delay to avoid rate limiting
                import time
                time.sleep(0.5)
                
            except Exception as e:
                print(f"[YAHOO] Error fetching {ticker}: {e}")
                continue
        
        print(f"[YAHOO] Found {len(all_buys)} insider buys total")
        
        # Cluster by ticker
        clustered = self._cluster_by_ticker(all_buys)
        
        return clustered
    
    def _fetch_ticker_insider_data(self, ticker: str, min_value: int, days_back: int) -> List[Dict]:
        """Fetch insider data for a specific ticker"""
        
        # Use yfinance to get insider data
        try:
            stock = yf.Ticker(ticker)
            
            # Get insider transactions
            insider_data = stock.insider_transactions
            
            if insider_data is None or insider_data.empty:
                return []
            
            # Filter for buys within date range
            buys = []
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            for _, row in insider_data.iterrows():
                # Check if it's a buy
                if "Buy" not in str(row.get("Position", "")):
                    continue
                
                # Parse date
                try:
                    trade_date = pd.to_datetime(row.get("Start Date", ""))
                    if trade_date < cutoff_date:
                        continue
                except:
                    continue
                
                # Calculate value
                shares = row.get("Shares", 0)
                price = row.get("Value", 0) / shares if shares > 0 else 0
                value = row.get("Value", 0)
                
                if value < min_value:
                    continue
                
                buys.append({
                    "ticker": ticker,
                    "insider_name": row.get("Name", ""),
                    "insider_title": row.get("Position", ""),
                    "shares": shares,
                    "price": price,
                    "value": value,
                    "date": trade_date.strftime("%Y-%m-%d"),
                    "source": "Yahoo"
                })
            
            return buys
            
        except Exception as e:
            print(f"[YAHOO] Error fetching {ticker}: {e}")
            return []
    
    def _cluster_by_ticker(self, trades: List[Dict]) -> List[Dict]:
        """Cluster trades by ticker and create signals"""
        
        # Group by ticker
        ticker_groups = {}
        for trade in trades:
            ticker = trade["ticker"]
            if ticker not in ticker_groups:
                ticker_groups[ticker] = []
            ticker_groups[ticker].append(trade)
        
        clustered_signals = []
        
        for ticker, trades_list in ticker_groups.items():
            # Create signal for each trade
            for trade in trades_list:
                signal = {
                    "ticker": trade["ticker"],
                    "title": f"🚀 Insider Buy: {trade['insider_name']} at {trade['ticker']}",
                    "reasoning": f"{trade['insider_title']} bought {trade['shares']:,.0f} shares at ${trade['price']:.2f} (${trade['value']:,.0f} value)",
                    "moonshot_score": self._calculate_moonshot_score(trade, len(trades_list)),
                    "is_moonshot": True,
                    "transaction_value": trade["value"],
                    "insider_name": trade["insider_name"],
                    "insider_role": trade["insider_title"],
                    "price": trade["price"],
                    "date": trade["date"],
                    "source": "yahoo_insider"
                }
                
                # Add cluster bonus
                if len(trades_list) > 1:
                    signal["title"] = f"🚀 CLUSTER: {len(trades_list)} insiders buying {ticker}"
                    signal["moonshot_score"] += 20
                    signal["reasoning"] = f"🚀 CLUSTER ALERT: {len(trades_list)} insiders | " + signal["reasoning"]
                
                clustered_signals.append(signal)
        
        # Sort by score
        clustered_signals.sort(key=lambda x: x["moonshot_score"], reverse=True)
        
        return clustered_signals
    
    def _calculate_moonshot_score(self, trade: Dict, cluster_size: int = 1) -> int:
        """Calculate moonshot score"""
        
        score = 50  # Base score
        
        # Value bonus
        value = trade["value"]
        if value >= 1000000:
            score += 20
        elif value >= 500000:
            score += 15
        elif value >= 100000:
            score += 10
        
        # Price bonus
        price = trade["price"]
        if 1.0 <= price <= 50.0:
            score += 10
        elif price > 50.0:
            score += 5
        
        # Title bonus
        title = trade["insider_title"].lower()
        if any(role in title for role in ["ceo", "chief executive", "president"]):
            score += 15
        elif any(role in title for role in ["cfo", "chief financial", "director"]):
            score += 10
        elif any(role in title for role in ["vp", "vice president", "officer"]):
            score += 5
        
        # Cluster bonus
        score += cluster_size * 5
        
        return min(score, 100)
    
    def scan_popular_stocks(self, num_stocks: int = 50) -> List[Dict]:
        """Scan popular stocks for insider activity"""
        
        # Popular stock list
        popular_tickers = [
            "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK-B",
            "JPM", "JNJ", "V", "PG", "UNH", "HD", "MA", "BAC", "XOM", "CVX",
            "LLY", "ABBV", "PFE", "KO", "PEP", "TMO", "COST", "ABT", "CRM",
            "ACN", "MRK", "DHR", "MCD", "VZ", "ADBE", "NFLX", "PYPL", "INTC",
            "CSCO", "CMCSA", "KO", "PEP", "T", "DIS", "NKE", "WMT", "IBM"
        ]
        
        return self.fetch_insider_buys_for_tickers(popular_tickers[:num_stocks])


# Test the scraper
if __name__ == "__main__":
    import pandas as pd
    
    scraper = YahooInsiderScraper()
    
    print("Testing Yahoo Insider Scraper...")
    
    # Test with a few tickers
    test_tickers = ["AAPL", "MSFT", "NVDA", "TSLA", "GME"]
    
    buys = scraper.fetch_insider_buys_for_tickers(test_tickers, min_value=50000, days_back=7)
    
    print(f"\nFound {len(buys)} insider buys:")
    
    for i, buy in enumerate(buys[:5], 1):
        print(f"\n{i}. {buy['ticker']} - Score: {buy['moonshot_score']}/100")
        print(f"   {buy['reasoning']}")
