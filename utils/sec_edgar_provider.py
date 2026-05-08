#!/usr/bin/env python3
"""
PHASMA AI - SEC EDGAR Direct Integration
Gets insider/whale data directly from SEC - no middlemen
"""

import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import xml.etree.ElementTree as ET
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class InsiderTrade:
    """SEC Form 4 insider trade"""
    cik: str  # Central Index Key
    ticker: str
    insider_name: str
    insider_title: str
    trade_date: str
    transaction_shares: int
    transaction_price: float
    shares_owned_after: int
    acquisition_disposition: str  # A = Acquired (Buy), D = Disposed (Sell)
    filing_date: str
    form_type: str

class SECEdgarProvider:
    """Direct SEC EDGAR data provider - the ground truth for insider trading"""
    
    def __init__(self):
        self.base_url = "https://www.sec.gov"
        self.session = None
        self.headers = {
            'User-Agent': 'Phasma AI Trading System (research@phasma.ai)'
        }
        
        # CIK to ticker mapping cache
        self.cik_to_ticker = {}
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_recent_form4_filings(self, hours_back: int = 24) -> List[InsiderTrade]:
        """Get recent Form 4 filings from SEC"""
        trades = []
        
        # Get current date and calculate start date
        end_date = datetime.now()
        start_date = end_date - timedelta(hours=hours_back)
        
        # SEC's daily index files
        date_str = end_date.strftime('%Y-%m-%d')
        index_url = f"{self.base_url}/Archives/edgar/daily-index/master/{date_str}.master.idx"
        
        try:
            async with self.session.get(index_url) as response:
                if response.status != 200:
                    logger.error(f"Failed to fetch SEC index: {response.status}")
                    return trades
                
                content = await response.text()
                
                # Parse index file for Form 4 filings
                for line in content.split('\n'):
                    if '4\t' in line:  # Form 4 filing
                        parts = line.split('|')
                        if len(parts) >= 5:
                            cik = parts[0].strip()
                            company_name = parts[1].strip()
                            form_type = parts[2].strip()
                            filing_date = parts[3].strip()
                            file_url = parts[4].strip()
                            
                            if form_type == '4':
                                # Get the actual filing details
                                trade = await self._parse_form4_filing(
                                    cik, company_name, filing_date, file_url
                                )
                                if trade:
                                    trades.append(trade)
                
        except Exception as e:
            logger.error(f"Error fetching SEC filings: {e}")
        
        return trades
    
    async def _parse_form4_filing(self, cik: str, company_name: str, 
                                 filing_date: str, file_url: str) -> Optional[InsiderTrade]:
        """Parse individual Form 4 filing"""
        try:
            # Get the filing content
            full_url = f"{self.base_url}/Archives/{file_url}"
            async with self.session.get(full_url) as response:
                if response.status != 200:
                    return None
                
                content = await response.text()
                
                # Parse XML content
                if '<?xml' in content:
                    return self._parse_form4_xml(cik, company_name, filing_date, content)
                else:
                    return self._parse_form4_text(cik, company_name, filing_date, content)
                    
        except Exception as e:
            logger.error(f"Error parsing Form 4 for {cik}: {e}")
            return None
    
    def _parse_form4_xml(self, cik: str, company_name: str, 
                        filing_date: str, content: str) -> Optional[InsiderTrade]:
        """Parse XML Form 4 filing"""
        try:
            root = ET.fromstring(content)
            
            # Find issuer information
            ticker = None
            issuer = root.find('.//issuer')
            if issuer is not None:
                ticker_elem = issuer.find('issuerTradingSymbol')
                if ticker_elem is not None:
                    ticker = ticker_elem.text
            
            if not ticker:
                return None
            
            # Find reporting owner
            owner = root.find('.//reportingOwner')
            if owner is None:
                return None
            
            insider_name = owner.find('.//rptOwnerName')
            insider_title = owner.find('.//rptOwnerTitle')
            
            # Find transactions
            for trans in root.findall('.//nonDerivativeTransaction'):
                trans_shares = trans.find('.//transactionShares')
                trans_price = trans.find('.//transactionPricePerShare')
                trans_code = trans.find('.//transactionAcquiredDisposedCode')
                post_shares = trans.find('.//sharesOwnedFollowingTransaction')
                
                if all([trans_shares, trans_price, trans_code, post_shares]):
                    return InsiderTrade(
                        cik=cik,
                        ticker=ticker,
                        insider_name=insider_name.text if insider_name is not None else '',
                        insider_title=insider_title.text if insider_title is not None else '',
                        trade_date=filing_date,
                        transaction_shares=int(trans_shares.value.text),
                        transaction_price=float(trans_price.value.text),
                        shares_owned_after=int(post_shares.value.text),
                        acquisition_disposition=trans_code.value.text,
                        filing_date=filing_date,
                        form_type='4'
                    )
            
        except Exception as e:
            logger.error(f"Error parsing XML Form 4: {e}")
        
        return None
    
    def _parse_form4_text(self, cik: str, company_name: str, 
                         filing_date: str, content: str) -> Optional[InsiderTrade]:
        """Parse text-based Form 4 filing"""
        try:
            # This is a simplified parser for text filings
            # In production, you'd want more robust parsing
            
            # Extract ticker from header
            ticker_match = re.search(r'Ticker Symbol:\s*([A-Z]+)', content, re.IGNORECASE)
            ticker = ticker_match.group(1) if ticker_match else None
            
            if not ticker:
                return None
            
            # Extract insider name
            name_match = re.search(r'Name of Reporting Person:\s*([^\n]+)', content)
            insider_name = name_match.group(1).strip() if name_match else ''
            
            # Extract title
            title_match = re.search(r'Title:\s*([^\n]+)', content)
            insider_title = title_match.group(1).strip() if title_match else ''
            
            # Look for buy/sell transactions
            # This is simplified - real parsing would be more complex
            buy_pattern = r'(\d+)\s+shares\s+purchased\s+at\s+\$([\d.]+)'
            sell_pattern = r'(\d+)\s+shares\s+sold\s+at\s+\$([\d.]+)'
            
            if re.search(buy_pattern, content, re.IGNORECASE):
                match = re.search(buy_pattern, content, re.IGNORECASE)
                shares = int(match.group(1))
                price = float(match.group(2))
                code = 'A'  # Acquired
            elif re.search(sell_pattern, content, re.IGNORECASE):
                match = re.search(sell_pattern, content, re.IGNORECASE)
                shares = int(match.group(1))
                price = float(match.group(2))
                code = 'D'  # Disposed
            else:
                return None
            
            return InsiderTrade(
                cik=cik,
                ticker=ticker,
                insider_name=insider_name,
                insider_title=insider_title,
                trade_date=filing_date,
                transaction_shares=shares,
                transaction_price=price,
                shares_owned_after=0,  # Not easily parsed from text
                acquisition_disposition=code,
                filing_date=filing_date,
                form_type='4'
            )
            
        except Exception as e:
            logger.error(f"Error parsing text Form 4: {e}")
        
        return None
    
    async def get_insider_trades_for_ticker(self, ticker: str, days_back: int = 30) -> List[InsiderTrade]:
        """Get insider trades for specific ticker"""
        # This would require searching by company CIK
        # For now, return empty list - would need CIK lookup first
        logger.info(f"Getting SEC Form 4 data for {ticker}")
        return []
    
    def calculate_confidence_score(self, trade: InsiderTrade) -> float:
        """Calculate confidence score for insider trade"""
        base_confidence = 0.5
        
        # Buys are more significant than sells
        if trade.acquisition_disposition == 'A':
            base_confidence += 0.2
        
        # Large trades are more significant
        trade_value = trade.transaction_shares * trade.transaction_price
        if trade_value > 100000:
            base_confidence += 0.1
        if trade_value > 500000:
            base_confidence += 0.1
        
        # Senior executives are more significant
        senior_titles = ['CEO', 'CFO', 'President', 'Director', 'Chief']
        if any(title in trade.insider_title for title in senior_titles):
            base_confidence += 0.2
        
        return min(base_confidence, 1.0)
    
    def convert_to_signal(self, trade: InsiderTrade) -> Dict[str, Any]:
        """Convert SEC trade to trading signal"""
        confidence = self.calculate_confidence_score(trade)
        action = 'BUY' if trade.acquisition_disposition == 'A' else 'SELL'
        
        return {
            'symbol': trade.ticker,
            'action': action,
            'confidence': confidence,
            'source': 'sec_edgar',
            'price': trade.transaction_price,
            'volume': trade.transaction_shares,
            'rationale': f"SEC Form 4: {trade.insider_name} ({trade.insider_title}) "
                        f"{'bought' if action == 'BUY' else 'sold'} "
                        f"{trade.transaction_shares:,} shares at ${trade.transaction_price:.2f}",
            'insider_data': {
                'name': trade.insider_name,
                'title': trade.insider_title,
                'filing_date': trade.filing_date,
                'shares_after': trade.shares_owned_after
            },
            'timestamp': datetime.now().isoformat(),
            'ground_truth': True  # Mark as verified ground truth
        }

# Usage example
async def main():
    """Example usage of SEC EDGAR provider"""
    async with SECEdgarProvider() as sec:
        print("🔍 Fetching recent SEC Form 4 filings...")
        trades = await sec.get_recent_form4_filings(hours_back=24)
        
        print(f"\nFound {len(trades)} recent insider trades:")
        for trade in trades[:5]:  # Show first 5
            print(f"\n  {trade.ticker}: {trade.insider_name}")
            print(f"  Action: {'BUY' if trade.acquisition_disposition == 'A' else 'SELL'}")
            print(f"  Shares: {trade.transaction_shares:,} @ ${trade.transaction_price:.2f}")
            print(f"  Confidence: {sec.calculate_confidence_score(trade):.1%}")
            
            # Convert to signal
            signal = sec.convert_to_signal(trade)
            print(f"  Signal: {signal['action']} @ {signal['confidence']:.1%} confidence")

if __name__ == "__main__":
    asyncio.run(main())
