#!/usr/bin/env python3
"""
PHASMA AI - OpenInsider Scraper
Free SEC Form 4 insider trading data from OpenInsider.com
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import re
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class OpenInsiderScraper:
    """Scrapes insider trading data from OpenInsider.com"""
    
    def __init__(self):
        self.base_url = "https://www.openinsider.com"
        self.session = None
        self.timeout = aiohttp.ClientTimeout(total=30)
        
        # User agent to avoid blocking
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=self.timeout,
            headers=self.headers
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def scrape_latest_insider_trades(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Scrape latest insider trades"""
        try:
            url = f"{self.base_url}/screener?s=&o=&pl=&ph=&ll=&lh=&fd=730&fdmin=0&fdmax=30&sd=0&sdmin=0&sdmax=0&sortcol=0&cnt={limit}&page=1"
            
            async with self.session.get(url) as response:
                if response.status != 200:
                    logger.error(f"OpenInsider returned status {response.status}")
                    return []
                
                html = await response.text()
                return self._parse_insider_table(html)
        except Exception as e:
            logger.error(f"Error scraping OpenInsider: {e}")
            return []
    
    async def scrape_insider_trades_for_symbol(self, symbol: str, days_back: int = 30) -> List[Dict[str, Any]]:
        """Scrape insider trades for specific symbol"""
        try:
            # Format the URL for specific symbol
            url = f"{self.base_url}/trading/{symbol}"
            
            async with self.session.get(url) as response:
                if response.status != 200:
                    logger.error(f"OpenInsider returned status {response.status} for {symbol}")
                    return []
                
                html = await response.text()
                return self._parse_insider_table(html, symbol)
        except Exception as e:
            logger.error(f"Error scraping {symbol} from OpenInsider: {e}")
            return []
    
    def _parse_insider_table(self, html: str, symbol_filter: str = None) -> List[Dict[str, Any]]:
        """Parse the insider trading table from HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        trades = []
        
        try:
            # Find the main table
            table = soup.find('table', {'class': 'tinytable'})
            if not table:
                # Try alternative table class
                table = soup.find('table', id='table')
            
            if not table:
                logger.warning("Could not find insider trading table")
                return []
            
            # Parse rows
            rows = table.find_all('tr')[1:]  # Skip header row
            
            for row in rows[:50]:  # Limit to 50 trades
                cells = row.find_all('td')
                if len(cells) < 8:
                    continue
                
                try:
                    # Extract data from cells
                    trade_data = self._extract_trade_data(cells)
                    if trade_data and (not symbol_filter or trade_data['symbol'] == symbol_filter):
                        trades.append(trade_data)
                except Exception as e:
                    logger.debug(f"Error parsing row: {e}")
                    continue
            
            logger.info(f"Parsed {len(trades)} insider trades from OpenInsider")
            return trades
            
        except Exception as e:
            logger.error(f"Error parsing HTML: {e}")
            return []
    
    def _extract_trade_data(self, cells: List) -> Optional[Dict[str, Any]]:
        """Extract trade data from table cells"""
        try:
            # Cell indices based on OpenInsider table structure
            filing_date = self._clean_text(cells[0].text)
            trade_date = self._clean_text(cells[1].text)
            ticker = self._clean_text(cells[2].text)
            company_name = self._clean_text(cells[3].text)
            insider_name = self._clean_text(cells[4].text)
            insider_title = self._clean_text(cells[5].text)
            trade_type = self._clean_text(cells[6].text)
            price = self._clean_text(cells[7].text)
            qty = self._clean_text(cells[8].text)
            owned = self._clean_text(cells[9].text)
            
            # Parse numeric values
            price = self._parse_price(price)
            qty = self._parse_quantity(qty)
            
            # Determine if it's a buy or sell
            is_buy = 'Buy' in trade_type or 'Purchase' in trade_type
            is_sell = 'Sell' in trade_type or 'Sale' in trade_type
            
            # Skip if not a clear buy/sell
            if not is_buy and not is_sell:
                return None
            
            # Calculate value
            value = price * qty if price and qty else 0
            
            return {
                'symbol': ticker,
                'company_name': company_name,
                'insider_name': insider_name,
                'insider_title': insider_title,
                'filing_date': self._parse_date(filing_date),
                'trade_date': self._parse_date(trade_date),
                'trade_type': trade_type,
                'action': 'BUY' if is_buy else 'SELL',
                'price': price,
                'quantity': qty,
                'value': value,
                'shares_owned': self._parse_quantity(owned),
                'source': 'openinsider',
                'confidence': self._calculate_confidence(is_buy, insider_title, value),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.debug(f"Error extracting trade data: {e}")
            return None
    
    def _clean_text(self, text: str) -> str:
        """Clean text from HTML"""
        if not text:
            return ""
        return re.sub(r'\s+', ' ', text.strip())
    
    def _parse_price(self, price_str: str) -> Optional[float]:
        """Parse price string"""
        if not price_str or price_str == '$':
            return None
        
        # Remove $ and commas
        price_str = price_str.replace('$', '').replace(',', '')
        
        try:
            return float(price_str)
        except ValueError:
            return None
    
    def _parse_quantity(self, qty_str: str) -> Optional[int]:
        """Parse quantity string"""
        if not qty_str:
            return None
        
        # Remove commas and convert to int
        qty_str = qty_str.replace(',', '')
        
        try:
            return int(qty_str)
        except ValueError:
            return None
    
    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parse date string"""
        if not date_str:
            return None
        
        # Try different date formats
        formats = ['%Y-%m-%d', '%m/%d/%Y', '%b %d %Y']
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.isoformat()
            except ValueError:
                continue
        
        return date_str  # Return original if can't parse
    
    def _calculate_confidence(self, is_buy: bool, title: str, value: float) -> float:
        """Calculate confidence score for insider trade"""
        base_confidence = 0.5
        
        # Higher confidence for buys (insiders buy for one reason)
        if is_buy:
            base_confidence += 0.2
        
        # Higher confidence for certain titles
        high_confidence_titles = ['CEO', 'CFO', 'CTO', 'President', 'Director']
        if any(title_word in title for title_word in high_confidence_titles):
            base_confidence += 0.2
        
        # Higher confidence for large trades
        if value > 100000:  # $100k+
            base_confidence += 0.1
        elif value > 500000:  # $500k+
            base_confidence += 0.1
        
        return min(base_confidence, 1.0)
    
    async def get_top_insider_buys(self, min_value: int = 50000, limit: int = 20) -> List[Dict[str, Any]]:
        """Get top insider buys above minimum value"""
        all_trades = await self.scrape_latest_insider_trades(limit=100)
        
        # Filter for buys above minimum value
        top_buys = [
            trade for trade in all_trades
            if trade['action'] == 'BUY' and trade['value'] and trade['value'] >= min_value
        ]
        
        # Sort by value descending
        top_buys.sort(key=lambda x: x['value'] or 0, reverse=True)
        
        return top_buys[:limit]
    
    async def get_insider_signals(self) -> List[Dict[str, Any]]:
        """Convert insider trades to trading signals"""
        trades = await self.get_top_insider_buys(min_value=100000, limit=10)
        signals = []
        
        for trade in trades:
            # Convert to signal format
            signal = {
                'symbol': trade['symbol'],
                'action': 'BUY',
                'confidence': trade['confidence'],
                'position_size': min(trade['value'] / 1000, 1000),  # Cap at 1000
                'rationale': f"Insider {trade['insider_name']} ({trade['insider_title']}) bought ${trade['value']:,.0f} worth",
                'source': 'openinsider',
                'current_price': trade['price'],
                'trade_type': 'STOCK',
                'insider_data': trade,
                'timestamp': datetime.now().isoformat()
            }
            signals.append(signal)
        
        return signals

# Usage example
async def main():
    """Example usage of OpenInsider scraper"""
    async with OpenInsiderScraper() as scraper:
        # Get latest insider trades
        trades = await scraper.scrape_latest_insider_trades(limit=20)
        print(f"Found {len(trades)} recent insider trades")
        
        # Get top buys
        top_buys = await scraper.get_top_insider_buys(min_value=100000)
        print(f"\nTop {len(top_buys)} insider buys:")
        for trade in top_buys[:5]:
            print(f"  {trade['symbol']}: {trade['insider_name']} bought ${trade['value']:,.0f}")
        
        # Get signals
        signals = await scraper.get_insider_signals()
        print(f"\nGenerated {len(signals)} trading signals")
        for signal in signals[:3]:
            print(f"  {signal['symbol']}: {signal['confidence']:.1%} confidence")

if __name__ == "__main__":
    asyncio.run(main())
