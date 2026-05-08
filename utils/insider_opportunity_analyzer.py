#!/usr/bin/env python3
"""
Enhanced Insider Trading Opportunity Analyzer
Combines RSS monitoring with market timing analysis to assess investment viability
"""

import re
import requests
import time
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional, Tuple
import xml.etree.ElementTree as ET
import yfinance as yf
from dateutil import parser as date_parser

# SEC EDGAR Form 4 RSS feed - authoritative source for insider trading
SEC_EDGAR_URL = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type=4&company=&dateb=&owner=only&count=100&output=atom"


class InsiderOpportunityAnalyzer:
    """
    Enhanced insider trading monitor that analyzes large purchases
    and assesses whether it's still viable to follow the insider.
    """

    def __init__(self, config: Dict):
        self.config = config or {}
        self.enabled = bool(self.config.get("insider_monitor", {}).get("enabled", False))
        self.penny_only = bool(self.config.get("insider_monitor", {}).get("penny_only", False))
        self.min_value = float(self.config.get("insider_monitor", {}).get("min_value", 100000))  # $100K default for meaningful purchases
        self.tickers = set([t.upper() for t in self.config.get("insider_monitor", {}).get("tickers", [])])
        self.lookback_days = int(self.config.get("insider_monitor", {}).get("lookback_days", 7))
        
        # New thresholds for opportunity analysis
        self.max_gain_since_purchase = float(self.config.get("insider_monitor", {}).get("max_gain_since_purchase", 20.0))  # 20% max gain
        self.max_days_since_purchase = int(self.config.get("insider_monitor", {}).get("max_days_since_purchase", 30))
        self.min_market_cap = float(self.config.get("insider_monitor", {}).get("min_market_cap", 500_000_000))  # $500M minimum
        self.min_avg_volume = int(self.config.get("insider_monitor", {}).get("min_avg_volume", 500_000))  # 500K minimum
        self.target_sectors = [s.lower() for s in self.config.get("insider_monitor", {}).get("target_sectors", [])]  # Target sectors
        self._session = requests.Session()
        self._last_sec_request = 0.0
        self._sec_min_interval = float(self.config.get("insider_monitor", {}).get("sec_min_interval", 0.2))
        self._market_data_cache: Dict[str, Optional[Dict]] = {}

    def _sec_get(self, url: str, timeout: int = 10) -> Optional[requests.Response]:
        """Rate-limited SEC request with proper headers."""
        now = time.time()
        sleep_for = self._sec_min_interval - (now - self._last_sec_request)
        if sleep_for > 0:
            time.sleep(sleep_for)
        self._last_sec_request = time.time()

        headers = {
            "User-Agent": "PhasmaAI/InsiderMonitor (https://sec.gov)",
            "Accept": "application/atom+xml,application/xml,text/xml;q=0.9,*/*;q=0.8",
        }
        try:
            return self._session.get(url, headers=headers, timeout=timeout)
        except Exception as e:
            print(f"[INSIDER] SEC request failed: {e}")
            return None

    def _fetch_form4_xml(self, filing_index_url: str) -> Optional[str]:
        """Fetch the actual Form 4 XML from a filing index page."""
        resp = self._sec_get(filing_index_url, timeout=15)
        if resp is None or resp.status_code != 200:
            return None

        xml_matches = re.findall(r'href="([^"]*\.xml)"', resp.text)
        xml_urls = [m for m in xml_matches if 'xslF345X05' not in m]
        if not xml_urls:
            return None

        for xml_url in xml_urls[:6]:
            if not xml_url.startswith("http"):
                xml_url = "https://www.sec.gov" + xml_url

            xml_resp = self._sec_get(xml_url, timeout=15)
            if xml_resp is None or xml_resp.status_code != 200:
                continue

            xml_text = xml_resp.text or ""
            head = xml_text.lstrip()[:300].lower()
            if "<html" in head:
                continue
            if "<ownershipdocument" not in head and "<ownershipdocument" not in xml_text.lower():
                continue

            return xml_text

        return None

    def _parse_form4_transactions(self, xml_content: str) -> List[Dict]:
        """Parse Form 4 XML to extract transaction details."""
        try:
            root = ET.fromstring(xml_content)
        except Exception as e:
            print(f"[INSIDER] XML parsing failed: {e}")
            return []

        # Remove namespaces
        for elem in root.iter():
            if '}' in elem.tag:
                elem.tag = elem.tag.split('}', 1)[1]

        # Get ticker
        issuer = root.find("issuer")
        ticker = None
        if issuer is not None:
            ticker_text = issuer.findtext("issuerTradingSymbol")
            if ticker_text:
                ticker = ticker_text.strip().upper()
        if not ticker:
            return []

        # Get insider info
        insider_name = None
        insider_role = None
        reporting_owner = root.find("reportingOwner")
        if reporting_owner is not None:
            name_text = reporting_owner.findtext("reportingOwnerId/rptOwnerName")
            if name_text:
                insider_name = name_text.strip()

            relationship = reporting_owner.find("reportingOwnerRelationship")
            if relationship is not None:
                is_director = (relationship.findtext("isDirector") or "").strip().lower() == "true"
                is_officer = (relationship.findtext("isOfficer") or "").strip().lower() == "true"
                is_ten_pct = (relationship.findtext("isTenPercentOwner") or "").strip().lower() == "true"
                officer_title = (relationship.findtext("officerTitle") or "").strip()

                if is_officer and officer_title:
                    insider_role = officer_title
                elif is_officer:
                    insider_role = "Officer"
                elif is_director:
                    insider_role = "Director"
                elif is_ten_pct:
                    insider_role = "10% Owner"

        # Parse transactions
        non_deriv_table = root.find("nonDerivativeTable")
        if non_deriv_table is None:
            return []

        transactions: List[Dict] = []
        for tx in non_deriv_table.findall("nonDerivativeTransaction"):
            code = (tx.findtext("transactionCoding/transactionCode") or "").strip()
            if code != "P":  # Only purchases
                continue

            shares_text = (tx.findtext("transactionAmounts/transactionShares/value") or "").replace(",", "").strip()
            price_text = (tx.findtext("transactionAmounts/transactionPricePerShare/value") or "").replace(",", "").strip()
            ad_code = (tx.findtext("transactionAmounts/transactionAcquiredDisposedCode/value") or "").strip()
            tx_date = (tx.findtext("transactionDate/value") or "").strip() or None

            if not shares_text or not price_text:
                continue

            try:
                shares_num = float(shares_text)
                price_num = float(price_text)
            except Exception:
                continue

            if shares_num <= 0 or price_num <= 0:
                continue

            transactions.append({
                "ticker": ticker,
                "date": tx_date,
                "transaction_code": code,
                "shares": shares_num,
                "price": price_num,
                "acquired_disposed": ad_code or None,
                "total_value": shares_num * price_num,
                "insider_name": insider_name,
                "insider_role": insider_role,
            })

        return transactions

    def _parse_sec_edgar(self, content: str) -> List[Dict]:
        """Parse SEC EDGAR Atom feed and extract Form 4 entries."""
        root = ET.fromstring(content)
        
        # Handle XML namespace
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        entries = []
        
        for entry in root.findall('atom:entry', ns):
            title_el = entry.find('atom:title', ns)
            link_el = entry.find('atom:link', ns)
            summary_el = entry.find('atom:summary', ns)
            updated_el = entry.find('atom:updated', ns)
            
            title = title_el.text if title_el is not None else ""
            link = link_el.get('href') if link_el is not None else ""
            summary = summary_el.text if summary_el is not None else ""
            published = updated_el.text if updated_el is not None else ""
            
            entries.append({
                "title": title,
                "link": link,
                "summary": summary,
                "published": published
            })
        
        return entries

    def _extract_ticker_and_price(self, title: str) -> Tuple[Optional[str], Optional[float]]:
        """
        Enhanced extraction to find ticker and insider purchase price.
        Looks for patterns like "AAPL - $1,500,000" or "MSFT at $45.67"
        """
        ticker = None
        price = None

        # Enhanced ticker extraction - look for common patterns
        patterns = [
            r"\b([A-Z]{1,5})\b.*?\$",  # TICKER ... $price
            r"\$.*?\b([A-Z]{1,5})\b",  # $price ... TICKER
            r"([A-Z]{1,5})\s*-\s*\$",  # TICKER - $price
            r"([A-Z]{1,5})\s+at\s+\$",  # TICKER at $price
        ]
        
        for pattern in patterns:
            m_ticker = re.search(pattern, title)
            if m_ticker:
                ticker = m_ticker.group(1)
                break

        # Enhanced price extraction - handle large values with commas
        price_patterns = [
            r"\$([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?)",  # $1,500,000 or $45.67
            r"\$([0-9]+(?:\.[0-9]+)?)([KM])",  # $1.5M or $500K
        ]
        
        for pattern in price_patterns:
            m_price = re.search(pattern, title)
            if m_price:
                try:
                    price_str = m_price.group(1).replace(",", "")
                    price = float(price_str)
                    
                    # Handle K/M suffixes
                    if len(m_price.groups()) > 1 and m_price.group(2):
                        suffix = m_price.group(2).upper()
                        if suffix == "K":
                            price *= 1_000
                        elif suffix == "M":
                            price *= 1_000_000
                    break
                except Exception:
                    price = None

        return ticker, price

    def _is_purchase(self, title: str) -> bool:
        """Enhanced purchase detection."""
        title_lower = title.lower()
        purchase_keywords = ["purchase", "buy", "acquired", "acquisition"]
        sale_keywords = ["sale", "sell", "sold", "disposed"]
        
        # Must contain purchase keyword and no sale keywords
        has_purchase = any(keyword in title_lower for keyword in purchase_keywords)
        has_sale = any(keyword in title_lower for keyword in sale_keywords)
        
        return has_purchase and not has_sale

    def _extract_insider_value(self, title: str) -> Optional[float]:
        """
        Extract the total value of insider transaction.
        Looks for patterns like "$1,500,000", "$2.5M", "$500K"
        """
        patterns = [
            r"\$([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?)",  # $1,500,000
            r"\$([0-9]+(?:\.[0-9]+)?)([KM])",  # $2.5M or $500K
        ]
        
        for pattern in patterns:
            m_val = re.search(pattern, title)
            if m_val:
                try:
                    val_str = m_val.group(1).replace(",", "")
                    val = float(val_str)
                    
                    # Handle K/M suffixes
                    if len(m_val.groups()) > 1 and m_val.group(2):
                        suffix = m_val.group(2).upper()
                        if suffix == "K":
                            val *= 1_000
                        elif suffix == "M":
                            val *= 1_000_000
                    
                    return val
                except Exception:
                    continue
        
        return None

    def _get_market_data(self, ticker: str) -> Optional[Dict]:
        """Fetch current market data for analysis."""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            hist = stock.history(period="1mo")
            
            if not info or hist.empty:
                return None
                
            current_price = hist['Close'].iloc[-1]
            avg_volume = int(hist['Volume'].mean()) if not hist.empty else 0
            market_cap = info.get('marketCap', 0)
            sector = info.get('sector', '')
            industry = info.get('industry', '')
            
            # Check if sector matches target sectors
            if self.target_sectors and sector:
                sector_match = any(target in sector.lower() for target in self.target_sectors)
                industry_match = any(target in industry.lower() for target in self.target_sectors)
                if not (sector_match or industry_match):
                    print(f"[INSIDER] {ticker}: Not in target sectors ({sector}/{industry})")
                    return None
            
            return {
                'current_price': current_price,
                'avg_volume': avg_volume,
                'market_cap': market_cap,
                'sector': sector,
                'industry': industry,
                'price_change_1d': hist['Close'].pct_change().iloc[-1] if len(hist) > 1 else 0,
                'price_change_5d': hist['Close'].pct_change(5).iloc[-1] if len(hist) > 5 else 0,
            }
        except Exception as e:
            print(f"[INSIDER] Error fetching market data for {ticker}: {e}")
            return None

    def _calculate_opportunity_score(self, insider_data: Dict, market_data: Dict) -> Tuple[float, str]:
        """
        Calculate opportunity score and reasoning.
        Returns (score, reasoning) where score is 0-100.
        """
        score = 0
        reasoning_parts = []
        
        # Check if it's too late (already moved too much)
        insider_price = insider_data.get('purchase_price', 0)
        current_price = market_data.get('current_price', 0)
        
        if insider_price > 0 and current_price > 0:
            gain_pct = ((current_price - insider_price) / insider_price) * 100
            
            if gain_pct > self.max_gain_since_purchase:
                score -= 30
                reasoning_parts.append(f"Too late: already up {gain_pct:.1f}%")
            elif gain_pct > 10:
                score -= 10
                reasoning_parts.append(f"Some move already: up {gain_pct:.1f}%")
            elif gain_pct < -5:
                score += 15
                reasoning_parts.append(f"Below purchase price: down {abs(gain_pct):.1f}%")
            else:
                score += 20
                reasoning_parts.append(f"Good entry: up only {gain_pct:.1f}%")
        
        # Market cap quality
        market_cap = market_data.get('market_cap', 0)
        if market_cap >= self.min_market_cap:
            score += 15
            reasoning_parts.append(f"Strong market cap: ${market_cap/1e9:.1f}B")
        else:
            score -= 20
            reasoning_parts.append(f"Small market cap: ${market_cap/1e6:.1f}M")
        
        # Volume quality
        avg_volume = market_data.get('avg_volume', 0)
        if avg_volume >= self.min_avg_volume:
            score += 15
            reasoning_parts.append(f"Good volume: {avg_volume:,}")
        else:
            score -= 15
            reasoning_parts.append(f"Low volume: {avg_volume:,}")
        
        # Recent momentum
        price_change_5d = market_data.get('price_change_5d', 0)
        if price_change_5d > 0.05:  # Up 5%+ in 5 days
            score -= 10
            reasoning_parts.append(f"Recent momentum strong: +{price_change_5d*100:.1f}%")
        elif price_change_5d < -0.10:  # Down 10%+ in 5 days
            score += 10
            reasoning_parts.append(f"Recent weakness: {price_change_5d*100:.1f}%")
        
        # Insider transaction size
        insider_value = insider_data.get('transaction_value', 0)
        if insider_value >= 1_000_000:  # $1M+
            score += 20
            reasoning_parts.append(f"Large insider purchase: ${insider_value/1e6:.1f}M")
        elif insider_value >= 500_000:  # $500K+
            score += 10
            reasoning_parts.append(f"Significant purchase: ${insider_value/1e3:.0f}K")
        
        # Time since purchase
        days_since = insider_data.get('days_since_purchase', 0)
        if days_since <= 7:
            score += 10
            reasoning_parts.append(f"Very recent: {days_since} days ago")
        elif days_since <= 30:
            score += 5
            reasoning_parts.append(f"Recent: {days_since} days ago")
        else:
            score -= 10
            reasoning_parts.append(f"Older: {days_since} days ago")
        
        # Sector bonus for AI/tech focus
        sector = market_data.get('sector', '')
        industry = market_data.get('industry', '')
        if self.target_sectors:
            ai_keywords = ['artificial intelligence', 'ai', 'software', 'semiconductor', 'technology']
            sector_bonus = 0
            
            for keyword in ai_keywords:
                if keyword in sector.lower() or keyword in industry.lower():
                    sector_bonus = 15
                    reasoning_parts.append(f"AI/Tech sector: {sector}")
                    break
            
            score += sector_bonus
        
        # Cap score at 0-100
        score = max(0, min(100, score))
        reasoning = " | ".join(reasoning_parts) if reasoning_parts else "Insufficient data"
        
        return score, reasoning

    def fetch_and_analyze_opportunities(self) -> List[Dict]:
        """Fetch insider buys and analyze investment opportunities using real Form 4 XML."""
        if not self.enabled:
            return []

        try:
            print("[INSIDER] Fetching SEC EDGAR Form 4 data...")
            resp = self._sec_get(SEC_EDGAR_URL, timeout=30)
            if resp is None:
                print("[INSIDER] Failed to fetch SEC data: no response")
                return []
            if resp.status_code != 200:
                print(f"[INSIDER] Failed to fetch SEC data: status {resp.status_code}")
                return []
            
            root = ET.fromstring(resp.content)
            opportunities = []
            seen_tickers = set()  # Track tickers to avoid duplicates
            processed_count = 0  # Track processed entries
            
            for entry in root.findall('{http://www.w3.org/2005/Atom}entry'):
                # Parse publication date
                pub_date = entry.find('{http://www.w3.org/2005/Atom}published')
                if pub_date is None:
                    continue
                
                try:
                    from dateutil.parser import parse
                    pub_dt = parse(pub_date.text).replace(tzinfo=None)
                except Exception as e:
                    print(f"[INSIDER] Date parse error: {e}")
                    continue
                
                if pub_dt < self.cutoff:
                    continue

                # Fetch and parse the actual Form 4 XML
                link = entry.find('{http://www.w3.org/2005/Atom}link')
                if link is None:
                    continue
                
                xml_content = self._fetch_form4_xml(link.get('href'))
                if not xml_content:
                    continue

                transactions = self._parse_form4_transactions(xml_content)
                if not transactions:
                    continue

                for tx in transactions:
                    ticker = tx["ticker"]
                    
                    # Skip if we already processed this ticker
                    if ticker in seen_tickers:
                        continue
                    seen_tickers.add(ticker)
                    
                    # Apply filters
                    if self.tickers and ticker not in self.tickers:
                        continue
                    if tx["total_value"] < self.min_value:
                        continue

                    # Get market data (with cache)
                    market_data = self._market_data_cache.get(ticker)
                    if market_data is None:
                        market_data = self._get_market_data(ticker)
                        self._market_data_cache[ticker] = market_data
                    
                    if not market_data:
                        print(f"[INSIDER] Skipping {ticker} - no market data")
                        continue

                    # Calculate opportunity score
                    days_since = (datetime.now(timezone.utc) - pub_dt).days
                    insider_data = {
                        'ticker': ticker,
                        'title': entry.get("title", ""),
                        'link': link,
                        'published': pub_raw,
                        'purchase_price': tx["price"],
                        'transaction_value': tx["total_value"],
                        'days_since_purchase': days_since,
                        'insider_name': tx.get('insider_name'),
                        'insider_role': tx.get('insider_role'),
                    }

                    score, reasoning = self._calculate_opportunity_score(insider_data, market_data)
                    
                    if score >= 50:  # Minimum threshold
                        opportunity = {
                            **insider_data,
                            **market_data,
                            'opportunity_score': score,
                            'reasoning': reasoning,
                            'recommendation': self._get_recommendation(score),
                        }
                        opportunities.append(opportunity)
                        print(f"[INSIDER] ✅ {ticker}: Score {score:.0f} - {reasoning}")

                processed_count += 1
                if processed_count >= 20:  # Early stop after processing 20 entries
                    break

            # Sort by opportunity score
            opportunities.sort(key=lambda x: x['opportunity_score'], reverse=True)
            print(f"[INSIDER] Found {len(opportunities)} actionable opportunities")
            
            if len(opportunities) == 0:
                print("[INSIDER] No actionable opportunities found")
            
            return opportunities[:5]  # Return top 5
            
        except Exception as e:
            print(f"[INSIDER] Error in analysis: {e}")
            return []

    def _get_recommendation(self, score: float) -> str:
        """Get investment recommendation based on score."""
        if score >= 80:
            return "STRONG BUY - Excellent opportunity"
        elif score >= 70:
            return "BUY - Good opportunity"
        elif score >= 60:
            return "CONSIDER - Decent opportunity"
        else:
            return "MONITOR - Marginal opportunity"

    def generate_simple_explanation(self, opportunity: Dict) -> str:
        """Generate a simple explanation for non-traders."""
        ticker = opportunity.get('ticker', '')
        insider_name = opportunity.get('insider_name', 'A company insider')
        value = opportunity.get('transaction_value', 0)
        score = opportunity.get('opportunity_score', 0)
        
        # Format the insider purchase amount
        if value >= 1_000_000:
            amount_str = f"${value/1_000_000:.1f} million"
        else:
            amount_str = f"${value/1_000:.0f} thousand"
        
        # Create simple explanation
        explanation = f"""📈 **{ticker} - Insider Buying Alert**

**What's happening:** {insider_name} just bought {amount_str} worth of {ticker} stock.

**Why it matters:** Company insiders buy their own stock when they believe the price will go up. They know more about the business than anyone else.

**What to do:** This could be a good buying opportunity, especially if the stock hasn't moved much yet. The insider's confidence score is {score}/100.

**Simple advice:** Consider buying if you're comfortable with the risk - insiders are usually right about their own company's stock."""
        
        return explanation

    def get_recent_buys(self, ticker: str = None) -> List[Dict]:
        """Get recent insider buys for a specific ticker or all tickers"""
        if not self.enabled:
            return []
        
        try:
            # Fetch all opportunities
            opportunities = self.fetch_and_analyze_opportunities()
            
            # Filter by ticker if specified
            if ticker:
                opportunities = [opp for opp in opportunities if opp.get('ticker') == ticker.upper()]
            
            # Convert to expected format
            buys = []
            for opp in opportunities:
                buys.append({
                    'ticker': opp.get('ticker'),
                    'insider_name': opp.get('insider_name'),
                    'title': opp.get('title'),
                    'type': 'buy',
                    'amount': opp.get('amount', 0),
                    'price': opp.get('price', 0),
                    'transaction_code': opp.get('transaction_code', 'P'),
                    'days_ago': opp.get('days_ago', 0)
                })
            
            return buys
            
        except Exception as e:
            print(f"[INSIDER] Error getting recent buys: {e}")
            return []
    
    def get_recent_signals(self) -> List[Dict]:
        """Return formatted insider signals for main.py integration."""
        opportunities = self.fetch_and_analyze_opportunities()
        signals = []
        
        for opp in opportunities:
            # Generate simple explanation for non-traders
            simple_explanation = self.generate_simple_explanation(opp)
            
            signal = {
                "ticker": opp.get("ticker", ""),
                "title": opp.get("title", ""),
                "score": opp.get("opportunity_score", 0),
                "source": "insider_trading",
                "reasoning": opp.get("reasoning", ""),
                "price": opp.get("purchase_price", 0),
                "date": opp.get("published", ""),
                "insider": opp.get("insider_name", ""),
                "value": opp.get("transaction_value", 0),
                "is_moonshot": opp.get("opportunity_score", 0) >= 70,
                "moonshot_score": opp.get("opportunity_score", 0),
                "opportunity_score": opp.get("opportunity_score", 0),
                "confidence": min(0.95, 0.5 + (opp.get("opportunity_score", 0) / 100) * 0.45),
                "action": "BUY",
                "position_size": 1500,
                "sector": opp.get("sector", "UNKNOWN"),
                "region": "GLOBAL",
                "timestamp": datetime.now().isoformat(),
                "details": {
                    "insider_name": opp.get("insider_name", ""),
                    "insider_role": opp.get("insider_role", ""),
                    "transaction_type": "Purchase",
                    "amount": f"${opp.get('transaction_value', 0):,.0f}",
                    "filing_date": opp.get("published", ""),
                    "recommendation": opp.get("recommendation", "")
                },
                "simple_explanation": simple_explanation  # Add simple explanation
            }
            signals.append(signal)
        
        return signals


# Global instance
_insider_analyzer: Optional[InsiderOpportunityAnalyzer] = None


def get_insider_analyzer(config: Dict) -> InsiderOpportunityAnalyzer:
    global _insider_analyzer
    if _insider_analyzer is None:
        _insider_analyzer = InsiderOpportunityAnalyzer(config)
    return _insider_analyzer
