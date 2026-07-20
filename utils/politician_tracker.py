"""
Politician Trading Tracker for Phasma AI
Monitors congressional and government official trading activity
Uses multiple free data sources for comprehensive coverage
"""

import requests
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import re

load_dotenv()

logger = logging.getLogger(__name__)

# Module-level: skip Finnhub after first 401 to avoid log spam
_finnhub_auth_failed = False


class PoliticianTracker:
    """
    Tracks trading activity of US politicians (Congress, Senate, etc.)
    Provides valuable financial intelligence from government disclosures
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.enabled = self.config.get('enabled', True)
        self.lookback_days = self.config.get('lookback_days', 30)
        self.min_value = self.config.get('min_value', 1000)  # Minimum trade value to track
        self.focus_tickers = self.config.get('tickers', [])  # Specific tickers to monitor
        self.use_live = bool(self.config.get('politician_trades_use_live', False))
        
        # Data sources (web scraping since APIs are failing)
        self.capitol_trades_url = "https://www.capitoltrades.com/trades"
        self.finnhub_api_key = os.getenv('FINNHUB_API_KEY')
        self.finnhub_url = f"https://finnhub.io/api/v1/congressional-trading"
        
        # Cache for recent trades
        self.recent_trades = []
        self.last_fetch = None
        self.using_live_data = False
        
        print("🏛️ Politician Trading Tracker initialized")
        print(f"   - Monitoring trades over last {self.lookback_days} days")
        print(f"   - Minimum trade value: ${self.min_value:,}")
        print(f"   - Live API: {'enabled' if self.use_live else 'disabled (demo/sample only)'}")
        if self.focus_tickers:
            print(f"   - Focused tickers: {', '.join(self.focus_tickers)}")
    
    def get_sample_politician_trades(self) -> List[Dict]:
        """
        Get sample politician trades for demonstration
        Returns: List of sample trade dictionaries
        """
        logger.info("Using sample politician trades for demonstration")
        
        sample_trades = [
            {
                'politician': 'Nancy Pelosi',
                'ticker': 'NVDA',
                'action': 'BUY',
                'amount': 500000,
                'date': '12/05/2024',
                'raw_text': 'Nancy Pelosi purchased NVIDIA Corporation (NVDA) stock worth $500,000'
            },
            {
                'politician': 'Kevin McCarthy',
                'ticker': 'AAPL',
                'action': 'BUY',
                'amount': 250000,
                'date': '12/04/2024',
                'raw_text': 'Kevin McCarthy bought Apple Inc. (AAPL) shares valued at $250,000'
            },
            {
                'politician': 'Mitch McConnell',
                'ticker': 'JPM',
                'action': 'SELL',
                'amount': 150000,
                'date': '12/03/2024',
                'raw_text': 'Mitch McConnell sold JPMorgan Chase & Co. (JPM) stock worth $150,000'
            },
            {
                'politician': 'Chuck Schumer',
                'ticker': 'MSFT',
                'action': 'BUY',
                'amount': 300000,
                'date': '12/02/2024',
                'raw_text': 'Chuck Schumer acquired Microsoft Corporation (MSFT) stock valued at $300,000'
            },
            {
                'politician': 'Elise Stefanik',
                'ticker': 'TSLA',
                'action': 'BUY',
                'amount': 100000,
                'date': '12/01/2024',
                'raw_text': 'Elise Stefanik purchased Tesla Inc. (TSLA) shares worth $100,000'
            },
            {
                'politician': 'Josh Hawley',
                'ticker': 'GOOGL',
                'action': 'SELL',
                'amount': 75000,
                'date': '11/30/2024',
                'raw_text': 'Josh Hawley sold Alphabet Inc. (GOOGL) stock valued at $75,000'
            },
            {
                'politician': 'Alexandria Ocasio-Cortez',
                'ticker': 'META',
                'action': 'BUY',
                'amount': 200000,
                'date': '11/29/2024',
                'raw_text': 'Alexandria Ocasio-Cortez bought Meta Platforms Inc. (META) stock worth $200,000'
            },
            {
                'politician': 'Ted Cruz',
                'ticker': 'XOM',
                'action': 'BUY',
                'amount': 125000,
                'date': '11/28/2024',
                'raw_text': 'Ted Cruz purchased Exxon Mobil Corporation (XOM) shares valued at $125,000'
            }
        ]
        
        print(f"✅ Generated {len(sample_trades)} sample politician trades (DEMO DATA)")
        return sample_trades
    
    def _parse_trade_element(self, element) -> Optional[Dict]:
        """
        Parse a single trade element from Capitol Trades website
        """
        try:
            text = element.get_text(strip=True)
            
            # Debug: Print first few elements to understand structure
            if not hasattr(self, '_debug_printed'):
                print(f"🔍 DEBUG: First trade element text: {text[:200]}...")
                self._debug_printed = True
            
            # Look for ticker patterns ($AAPL, TSLA, etc.)
            ticker_match = re.search(r'\$([A-Z]{1,5})\b|([A-Z]{1,5})\s*(?:stock|shares)', text, re.I)
            if not ticker_match:
                return None
            
            ticker = ticker_match.group(1) or ticker_match.group(2)
            
            # Look for politician names (usually before the ticker)
            politician_match = re.search(r'([A-Z][a-z]+ [A-Z][a-z]+)', text)
            politician = politician_match.group(1) if politician_match else 'name pending'
            
            # Look for buy/sell indicators
            action = 'action pending'
            if re.search(r'\bbuy\b|purchase\b|acquired\b', text, re.I):
                action = 'BUY'
            elif re.search(r'\bsell\b|sold\b|disposed\b', text, re.I):
                action = 'SELL'
            
            # Look for amount ranges ($1K-$15K, $50K-$100K, etc.)
            amount = 0
            amount_match = re.search(r'\$(\d+K?)-?\$?(\d*K?)', text)
            if amount_match:
                amount1 = self._parse_amount(amount_match.group(1))
                amount2 = self._parse_amount(amount_match.group(2)) if amount_match.group(2) else amount1
                amount = max(amount1, amount2)  # Use the higher value as estimate
            else:
                # Look for single amounts
                single_amount_match = re.search(r'\$(\d+K?)', text)
                if single_amount_match:
                    amount = self._parse_amount(single_amount_match.group(1))
            
            # Look for dates
            date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', text)
            date = date_match.group(1) if date_match else datetime.now().strftime('%m/%d/%Y')
            
            return {
                'politician': politician,
                'ticker': ticker,
                'action': action,
                'amount': amount,
                'date': date,
                'raw_text': text
            }
            
        except Exception as e:
            return None
    
    def fetch_finnhub_trades(self) -> List[Dict]:
        """
        Fetch congressional trades from Finnhub API
        Returns: List of trade dictionaries
        """
        global _finnhub_auth_failed
        if _finnhub_auth_failed:
            return []
        if not self.finnhub_api_key:
            return []
            
        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=self.lookback_days)
            
            params = {
                'from': start_date.strftime('%Y-%m-%d'),
                'to': end_date.strftime('%Y-%m-%d'),
                'token': self.finnhub_api_key
            }
            
            response = requests.get(self.finnhub_url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                trades = data.get('data', [])
                logger.info("Finnhub: retrieved %s congressional trades", len(trades))
                return trades
            if response.status_code in (401, 403):
                _finnhub_auth_failed = True
                logger.debug("Finnhub congressional API unauthorized — skipping for this session")
                return []
            logger.debug("Finnhub congressional API status %s", response.status_code)
            return []
                
        except Exception as e:
            logger.debug("Finnhub congressional fetch failed: %s", e)
            return []
    
    def normalize_trade_data(self, raw_trades: List[Dict], source: str) -> List[Dict]:
        """
        Normalize trade data from different sources to consistent format
        """
        normalized = []
        
        for trade in raw_trades:
            try:
                if source == 'capitol_trades_scrape' or source == 'sample_data':
                    ticker = str(trade.get('ticker') or '').upper().strip() or 'pending ticker'
                    normalized_trade = {
                        'politician': trade.get('politician') or 'name pending',
                        'chamber': 'chamber pending',
                        'party': 'party pending',
                        'state': 'state pending',
                        'ticker': ticker,
                        'company': trade.get('company') or ticker,
                        'action': trade.get('action') or 'action pending',
                        'amount': trade.get('amount', 0),
                        'date': trade.get('date') or 'date pending',
                        'source': 'Capitol Trades (Sample Data)' if source == 'sample_data' else 'Capitol Trades',
                        'description': trade.get('raw_text', ''),
                        'raw_data': trade,
                        'is_demo': source == 'sample_data',
                    }
                elif source == 'finnhub':
                    person = trade.get('person') or {}
                    ticker = str(trade.get('symbol') or '').upper().strip() or 'pending ticker'
                    normalized_trade = {
                        'politician': person.get('name') or 'name pending',
                        'chamber': person.get('chamber') or 'chamber pending',
                        'party': person.get('politicalParty') or 'party pending',
                        'state': person.get('state') or 'state pending',
                        'ticker': ticker,
                        'company': trade.get('assetName') or ticker,
                        'action': trade.get('transaction') or 'action pending',
                        'amount': self._parse_amount(trade.get('amount')),
                        'date': trade.get('transactionDate') or 'date pending',
                        'source': 'Finnhub',
                        'description': trade.get('comment', ''),
                        'raw_data': trade,
                        'is_demo': False,
                    }
                else:
                    continue

                # Resolve real company name when ticker is valid
                try:
                    from utils.signal_identity import ensure_signal_identity
                    id_sig = {
                        "symbol": normalized_trade["ticker"],
                        "company_name": normalized_trade.get("company"),
                    }
                    ok, name = ensure_signal_identity(id_sig)
                    if ok and name:
                        normalized_trade["company"] = name
                except Exception:
                    pass
                
                # Apply filters
                if self._should_include_trade(normalized_trade):
                    normalized.append(normalized_trade)
                    
            except Exception as e:
                logger.debug("Error normalizing trade: %s", e)
                continue
        
        return normalized
    
    def _parse_amount(self, amount_str: str) -> int:
        """
        Parse amount string to integer value
        """
        if not amount_str or str(amount_str).strip().lower() in ("unknown", "n/a", "none", ""):
            return 0
            
        try:
            # Handle various amount formats
            amount_str = str(amount_str).upper().replace('$', '').replace(',', '')
            
            if 'K' in amount_str:
                return int(float(amount_str.replace('K', '')) * 1000)
            elif 'M' in amount_str:
                return int(float(amount_str.replace('M', '')) * 1000000)
            elif 'B' in amount_str:
                return int(float(amount_str.replace('B', '')) * 1000000000)
            else:
                return int(float(amount_str))
        except:
            return 0
    
    def _should_include_trade(self, trade: Dict) -> bool:
        """
        Determine if trade should be included based on filters
        """
        # Check minimum value
        if trade['amount'] < self.min_value:
            return False
        
        # Check focused tickers
        if self.focus_tickers and trade['ticker'] not in self.focus_tickers:
            return False
        
        # Exclude incomplete / invalid data
        pol = str(trade.get('politician') or '').strip().lower()
        tick = str(trade.get('ticker') or '').strip().lower()
        if pol in ('', 'unknown', 'n/a', 'name pending') or tick in ('', 'unknown', 'n/a', 'pending ticker'):
            return False
        
        return True
    
    def fetch_recent_trades(self) -> List[Dict]:
        """
        Fetch and combine trades from all sources
        """
        if not self.enabled:
            print("⚠️ Politician tracker is disabled")
            return []
        
        print(f"🏛️ Fetching politician trades from all sources...")
        
        all_trades = []
        self.using_live_data = False
        
        if self.use_live:
            finnhub_trades = self.fetch_finnhub_trades()
            if finnhub_trades:
                normalized = self.normalize_trade_data(finnhub_trades, 'finnhub')
                all_trades.extend(normalized)
                self.using_live_data = True
        else:
            print("🏛️ Politician tracker: live API disabled — skipping (no demo/sample trades)")
            return []
        
        # Sort by date (most recent first)
        all_trades.sort(key=lambda x: x['date'], reverse=True)
        
        # Update cache
        self.recent_trades = all_trades
        self.last_fetch = datetime.now()
        
        print(f"🏛️ Total politician trades found: {len(all_trades)}")
        return all_trades
    
    def get_top_trades(self, limit: int = 10) -> List[Dict]:
        """
        Get top trades by value
        """
        if not self.recent_trades:
            self.fetch_recent_trades()
        
        return sorted(self.recent_trades, key=lambda x: x['amount'], reverse=True)[:limit]
    
    def get_trades_by_ticker(self, ticker: str) -> List[Dict]:
        """
        Get all trades for a specific ticker
        """
        if not self.recent_trades:
            self.fetch_recent_trades()
        
        return [trade for trade in self.recent_trades if trade['ticker'].upper() == ticker.upper()]
    
    def get_trades_by_politician(self, politician: str) -> List[Dict]:
        """
        Get all trades by a specific politician
        """
        if not self.recent_trades:
            self.fetch_recent_trades()
        
        return [trade for trade in self.recent_trades if politician.lower() in trade['politician'].lower()]
    
    def get_summary_stats(self) -> Dict:
        """
        Get summary statistics of recent trades
        """
        if not self.recent_trades:
            self.fetch_recent_trades()
        
        if not self.recent_trades:
            return {}
        
        # Calculate statistics
        total_trades = len(self.recent_trades)
        buys = len([t for t in self.recent_trades if t['action'].upper() in ['BUY', 'PURCHASE']])
        sells = len([t for t in self.recent_trades if t['action'].upper() in ['SELL', 'SALE']])
        total_value = sum(t['amount'] for t in self.recent_trades)
        
        # Top tickers
        ticker_counts = {}
        for trade in self.recent_trades:
            ticker = trade['ticker']
            ticker_counts[ticker] = ticker_counts.get(ticker, 0) + 1
        
        top_tickers = sorted(ticker_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Top politicians by trade count
        politician_counts = {}
        for trade in self.recent_trades:
            politician = trade['politician']
            politician_counts[politician] = politician_counts.get(politician, 0) + 1
        
        top_politicians = sorted(politician_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'total_trades': total_trades,
            'buys': buys,
            'sells': sells,
            'total_value': total_value,
            'average_trade_value': total_value / total_trades if total_trades > 0 else 0,
            'top_tickers': top_tickers,
            'top_politicians': top_politicians,
            'last_updated': self.last_fetch.isoformat() if self.last_fetch else None
        }
    
    def format_trade_for_telegram(self, trade: Dict) -> str:
        """
        Format a trade for Telegram notification
        """
        emoji = "🟢" if trade['action'].upper() in ['BUY', 'PURCHASE'] else "🔴"
        demo_banner = "⚠️ **DEMO DATA**\n\n" if trade.get('is_demo') else ""
        
        return (
            f"{demo_banner}"
            f"{emoji} **Politician Trade Alert**\n\n"
            f"👤 **Politician:** {trade['politician']} ({trade['party']}-{trade['state']})\n"
            f"🏛️ **Chamber:** {trade['chamber']}\n"
            f"📈 **Action:** {trade['action']} {trade['ticker']}\n"
            f"🏢 **Company:** {trade['company']}\n"
            f"💰 **Value:** ${trade['amount']:,}\n"
            f"📅 **Date:** {trade['date']}\n"
            f"📊 **Source:** {trade['source']}\n"
            f"📝 **Notes:** {trade['description'][:100]}..."
        )

# Example usage and testing
if __name__ == "__main__":
    tracker = PoliticianTracker()
    
    # Fetch recent trades
    trades = tracker.fetch_recent_trades()
    print(f"\nFound {len(trades)} recent trades")
    
    # Show top trades
    top_trades = tracker.get_top_trades(5)
    print(f"\nTop 5 trades by value:")
    for i, trade in enumerate(top_trades, 1):
        print(f"{i}. {trade['politician']} {trade['action']} {trade['ticker']} - ${trade['amount']:,}")
    
    # Show summary stats
    stats = tracker.get_summary_stats()
    print(f"\nSummary Statistics:")
    print(f"Total trades: {stats.get('total_trades', 0)}")
    print(f"Buys: {stats.get('buys', 0)}")
    print(f"Sells: {stats.get('sells', 0)}")
    print(f"Total value: ${stats.get('total_value', 0):,}")
