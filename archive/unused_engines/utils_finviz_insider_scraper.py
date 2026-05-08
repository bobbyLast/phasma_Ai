"""
FinViz Insider Data Scraper
Fallback when SEC XML parsing fails
Provides reliable insider trading data
"""

import requests
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time


class FinVizInsiderScraper:
    """Scrape insider trading data from FinViz"""
    
    def __init__(self):
        self.base_url = "https://finviz.com/insidertrader.ashx"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
    
    def fetch_recent_insider_buys(self, min_value: int = 50000, days_back: int = 7) -> List[Dict]:
        """Fetch recent insider buys from FinViz"""
        
        print(f"[FINVIZ] Fetching insider buys (min: ${min_value:,}, {days_back} days)...")
        
        try:
            # Construct URL parameters
            params = {
                "tc": "7",  # All insider trades
                "or": "-10",  # Last 10 days
                "tv": "100000000",  # Minimum value filter (will filter later)
                "tvmax": "5000000000",  # Max value
                "t": "b",  # Buys only
                "v": "s"  # Show all
            }
            
            resp = requests.get(self.base_url, params=params, headers=self.headers, timeout=10)
            
            if resp.status_code != 200:
                print(f"[FINVIZ] Failed to fetch data: HTTP {resp.status_code}")
                return []
            
            # Parse the HTML table
            insider_trades = self._parse_finviz_table(resp.text)
            
            # Filter by minimum value and date
            filtered_trades = []
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            for trade in insider_trades:
                # Check value
                if trade.get("value", 0) >= min_value:
                    # Check date
                    try:
                        trade_date = datetime.strptime(trade["date"], "%b %d %I:%M %p")
                        # Add current year (FinViz doesn't show year)
                        trade_date = trade_date.replace(year=datetime.now().year)
                        
                        if trade_date >= cutoff_date:
                            filtered_trades.append(trade)
                    except:
                        # If date parsing fails, include it
                        filtered_trades.append(trade)
            
            print(f"[FINVIZ] Found {len(filtered_trades)} insider buys meeting criteria")
            
            # Group by ticker for clustering
            clustered = self._cluster_by_ticker(filtered_trades)
            
            return clustered
            
        except Exception as e:
            print(f"[FINVIZ] Error fetching data: {e}")
            return []
    
    def _parse_finviz_table(self, html: str) -> List[Dict]:
        """Parse FinViz insider trading table"""
        
        trades = []
        
        # Find all table rows
        rows = re.findall(r'<tr[^>]*class="(?:insider-table-row|[^"]*is-insider-row|table-light-row)[^>]*>.*?</tr>', html, re.DOTALL)
        
        for row in rows:
            try:
                # Extract columns
                cols = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
                
                if len(cols) < 10:
                    continue
                
                # Clean HTML tags
                clean_cols = [re.sub(r'<[^>]+>', '', col).strip() for col in cols]
                
                # Parse data
                ticker = clean_cols[1].strip()
                company = clean_cols[2].strip()
                insider_name = clean_cols[3].strip()
                insider_title = clean_cols[4].strip()
                trade_type = clean_cols[5].strip()
                last_price = clean_cols[6].strip()
                trade_date = clean_cols[7].strip()
                shares = clean_cols[8].strip()
                value = clean_cols[9].strip()
                
                # Only include buys
                if "Buy" not in trade_type:
                    continue
                
                # Parse numeric values
                try:
                    shares_num = self._parse_number(shares)
                    price_num = self._parse_number(last_price)
                    value_num = self._parse_number(value)
                except:
                    continue
                
                # Skip if no value
                if value_num <= 0:
                    continue
                
                trades.append({
                    "ticker": ticker,
                    "company": company,
                    "insider_name": insider_name,
                    "insider_title": insider_title,
                    "trade_type": trade_type,
                    "price": price_num,
                    "shares": shares_num,
                    "value": value_num,
                    "date": trade_date,
                    "source": "FinViz"
                })
                
            except Exception as e:
                print(f"[FINVIZ] Error parsing row: {e}")
                continue
        
        return trades
    
    def _parse_number(self, num_str: str) -> float:
        """Parse number with K/M/B suffixes"""
        
        num_str = num_str.replace('$', '').replace(',', '').strip()
        
        if num_str == '-' or not num_str:
            return 0.0
        
        # Handle K/M/B suffixes
        if num_str[-1].upper() == 'K':
            return float(num_str[:-1]) * 1000
        elif num_str[-1].upper() == 'M':
            return float(num_str[:-1]) * 1000000
        elif num_str[-1].upper() == 'B':
            return float(num_str[:-1]) * 1000000000
        else:
            return float(num_str)
    
    def _cluster_by_ticker(self, trades: List[Dict]) -> List[Dict]:
        """Cluster trades by ticker and add cluster bonuses"""
        
        # Group by ticker
        ticker_groups = {}
        for trade in trades:
            ticker = trade["ticker"]
            if ticker not in ticker_groups:
                ticker_groups[ticker] = []
            ticker_groups[ticker].append(trade)
        
        clustered_signals = []
        
        for ticker, trades_list in ticker_groups.items():
            # Calculate total value for this ticker
            total_value = sum(t["value"] for t in trades_list)
            
            # Create signal for each trade with cluster info
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
                    "source": "finviz_insider"
                }
                
                # Add cluster bonus if multiple insiders
                if len(trades_list) > 1:
                    signal["title"] = f"🚀 CLUSTER: {len(trades_list)} insiders buying {ticker}"
                    signal["moonshot_score"] += 20
                    signal["reasoning"] = f"🚀 CLUSTER ALERT: {len(trades_list)} insiders | " + signal["reasoning"]
                
                clustered_signals.append(signal)
        
        # Sort by moonshot score
        clustered_signals.sort(key=lambda x: x["moonshot_score"], reverse=True)
        
        return clustered_signals
    
    def _calculate_moonshot_score(self, trade: Dict, cluster_size: int = 1) -> int:
        """Calculate moonshot score for insider trade"""
        
        score = 50  # Base score
        
        # Value bonus
        value = trade["value"]
        if value >= 1000000:
            score += 20
        elif value >= 500000:
            score += 15
        elif value >= 100000:
            score += 10
        
        # Price bonus (avoid penny stocks)
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


# Test the scraper
if __name__ == "__main__":
    scraper = FinVizInsiderScraper()
    
    print("Testing FinViz Insider Scraper...")
    
    # Fetch recent buys
    buys = scraper.fetch_recent_insider_buys(min_value=50000, days_back=7)
    
    print(f"\nFound {len(buys)} insider buys:")
    
    for i, buy in enumerate(buys[:10], 1):
        print(f"\n{i}. {buy['ticker']} - Score: {buy['moonshot_score']}/100")
        print(f"   {buy['reasoning']}")
        print(f"   Date: {buy['date']}")
