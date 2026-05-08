"""
Underground Stock Discovery Engine
Finds early-stage, under-covered stocks before mainstream attention
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import requests
import re
from datetime import datetime, timedelta
import yfinance as yf
import xml.etree.ElementTree as ET
from dateutil.parser import parse

@dataclass
class UndergroundSignal:
    """Signal for underground stock discovery"""
    ticker: str
    signal_type: str  # 'sec_filing', 'niche_news', 'social_chatter', 'alt_data'
    strength: float  # 0-1
    evidence: str
    timestamp: datetime
    sources: List[str]
    liquidity_score: float  # 0-1
    dilution_risk: str  # 'LOW', 'MEDIUM', 'HIGH'

class UndergroundStockDiscovery:
    """Engine to discover under-covered stocks with high potential"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.min_market_cap = config.get('underground_discovery', {}).get('min_market_cap', 10_000_000)
        self.max_market_cap = config.get('underground_discovery', {}).get('max_market_cap', 500_000_000)
        self.min_adv = config.get('underground_discovery', {}).get('min_adv', 50_000)
        
        # Strategy-specific thresholds
        self.strategy = config.get('underground_discovery', {}).get('strategy', 'penny_moonshot')
        
        if self.strategy == 'penny_moonshot':
            self.high_buy_threshold = 250_000  # Lower for penny stocks
            self.medium_buy_threshold = 100_000
            self.low_buy_threshold = 50_000
            self.aggregation_window_days = 60
        else:  # smallcap_compounder
            self.high_buy_threshold = 500_000
            self.medium_buy_threshold = 250_000
            self.low_buy_threshold = 100_000
            self.aggregation_window_days = 90
        
        # Store recent transactions for aggregation
        self.recent_transactions = {}  # ticker: list of all transactions
        self.last_fetch_time = None
        
        # Diagnostics
        self.diagnostics = {
            'total_filings': 0,
            'buys': 0,
            'sells': 0,
            'tax_events': 0,
            'exercises': 0,
            'parser_errors': 0,
            'signals_generated': 0
        }
        
        # SEC EDGAR RSS feeds
        self.sec_form4_url = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type=4&company=&dateb=&owner=only&count=100&output=atom"
        self.sec_8k_url = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type=8-K&company=&dateb=&owner=include&count=100&output=atom"
        
        # Session for requests
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": "PhasmaAI Underground Discovery (https://sec.gov)"
        })
        
        # Niche news sources (small-cap focused)
        self.niche_sources = [
            'https://seekingalpha.com/symbol/news',
            'https://smallcapdaily.com',
            'https://microcapreview.com',
            'https://pennystocks.com',
            'https://otcmarkets.com/news'
        ]
        
        # SEC filing patterns for early signals
        self.sec_patterns = {
            'partnership': ['partnership', 'agreement', 'collaboration', 'joint venture'],
            'milestone': ['fda approval', 'clinical trial', 'patent grant', 'design win'],
            'financing': ['offering', 'financing', 'investment', 'funding round'],
            'expansion': ['opening', 'expansion', 'new facility', 'launch']
        }
        
        # Social keywords for early buzz
        self.social_keywords = [
            'hidden gem', 'undiscovered', 'under the radar',
            'next big thing', 'breakout candidate', 'moonshot'
        ]
        
        print("[UNDERGROUND] Discovery engine initialized")
        print(f"[UNDERGROUND] Market cap range: ${self.min_market_cap/1_000_000:.0f}M - ${self.max_market_cap/1_000_000:.0f}M")
    
    def scan_for_opportunities(self) -> List[UndergroundSignal]:
        """Main scan combining all discovery methods"""
        opportunities = []
        
        print("\n[UNDERGROUND] === SCANNING FOR UNDERGROUND STOCKS ===")
        print(f"[UNDERGROUND] Market cap range: ${self.min_market_cap/1_000_000:.0f}M - ${self.max_market_cap/1_000_000:.0f}M")
        print(f"[UNDERGROUND] Minimum ADV: ${self.min_adv:,.0f}")
        
        # 1. Scan SEC filings for early milestones
        print("\n[UNDERGROUND] 1. Scanning SEC filings...")
        sec_signals = self._scan_sec_filings()
        opportunities.extend(sec_signals)
        print(f"[UNDERGROUND] SEC scan complete: {len(sec_signals)} signals")
        
        # 2. Monitor niche news sources
        print("\n[UNDERGROUND] 2. Scanning niche news sources...")
        news_signals = self._scan_niche_news()
        opportunities.extend(news_signals)
        print(f"[UNDERGROUND] News scan complete: {len(news_signals)} signals")
        
        # 3. Check for unusual options activity (early smart money)
        print("\n[UNDERGROUND] 3. Scanning options activity...")
        options_signals = self._scan_options_activity()
        opportunities.extend(options_signals)
        print(f"[UNDERGROUND] Options scan complete: {len(options_signals)} signals")
        
        # 4. Look for hiring/expansion patterns
        print("\n[UNDERGROUND] 4. Scanning hiring patterns...")
        hiring_signals = self._scan_hiring_patterns()
        opportunities.extend(hiring_signals)
        print(f"[UNDERGROUND] Hiring scan complete: {len(hiring_signals)} signals")
        
        # Filter and rank
        filtered = self._filter_and_rank(opportunities)
        
        print(f"\n[UNDERGROUND] === SCAN RESULTS ===")
        print(f"[UNDERGROUND] Raw signals found: {len(opportunities)}")
        print(f"[UNDERGROUND] Qualified after filters: {len(filtered)}")
        
        if len(opportunities) == 0:
            print("\n[UNDERGROUND] ⚠️  NO SIGNALS DETECTED - DEBUG INFO:")
            print("[UNDERGROUND] • SEC EDGAR API: Not implemented (TODO)")
            print("[UNDERGROUND] • News RSS/API: Not implemented (TODO)")
            print("[UNDERGROUND] • Options Flow API: Not implemented (TODO)")
            print("[UNDERGROUND] • Job Scraping: Not implemented (TODO)")
            print("[UNDERGROUND] → System needs real data feeds to generate signals")
        
        return filtered
    
    def _scan_sec_filings(self) -> List[UndergroundSignal]:
        """Scan SEC filings for early indicators"""
        signals = []
        
        print("[UNDERGROUND]   • SEC EDGAR: Checking for Form 4/8-K filings...")
        
        try:
            # Fetch Form 4 filings (insider trades)
            form4_signals = self._fetch_form4_filings()
            signals.extend(form4_signals)
            print(f"[UNDERGROUND]   • Form 4 filings: {len(form4_signals)} signals")
            
            # Fetch 8-K filings (material events)
            eightk_signals = self._fetch_8k_filings()
            signals.extend(eightk_signals)
            print(f"[UNDERGROUND]   • 8-K filings: {len(eightk_signals)} signals")
            
        except Exception as e:
            print(f"[UNDERGROUND]   • SEC EDGAR: Error - {e}")
        
        return signals
    
    def _fetch_form4_filings(self) -> List[UndergroundSignal]:
        """Fetch and parse Form 4 filings with aggregation logic"""
        signals = []
        
        try:
            response = self._session.get(self.sec_form4_url, timeout=30)
            if response.status_code != 200:
                print(f"[UNDERGROUND]     • Form 4 HTTP error: {response.status_code}")
                return signals
            
            # Parse XML
            root = ET.fromstring(response.content)
            
            # Define namespace
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            
            entries = root.findall('atom:entry', ns)
            print(f"[UNDERGROUND]     • Processing {len(entries)} Form 4 filings...")
            
            # Clear old transactions and refresh
            self._refresh_transaction_cache()
            
            for i, entry in enumerate(entries[:30]):  # Check more filings
                try:
                    # Get title and extract CIK
                    title = entry.find('atom:title', ns).text
                    
                    # Extract CIK from title
                    cik_match = re.search(r'\((\d{10})\)', title)
                    if not cik_match:
                        continue
                    
                    cik = cik_match.group(1)
                    
                    # Get filing link
                    link = entry.find('atom:link', ns)
                    if link is None:
                        continue
                    
                    filing_url = link.get('href')
                    
                    # Get publication date
                    updated = entry.find('atom:updated', ns)
                    if updated is None:
                        continue
                    pub_dt = parse(updated.text).replace(tzinfo=None)
                    
                    # Parse ALL transactions from the filing
                    transactions = self._parse_form4_transactions(filing_url)
                    
                    if transactions:
                        # Get ticker from transactions (XML format includes it)
                        ticker = None
                        for t in transactions:
                            if t.get('ticker'):
                                ticker = t['ticker']
                                break
                        
                        # Fallback to CIK lookup if no ticker found
                        if not ticker:
                            ticker = self._cik_to_ticker(cik)
                        
                        if not ticker:
                            continue
                        
                        # Store ALL transactions for aggregation
                        for trans in transactions:
                            if ticker not in self.recent_transactions:
                                self.recent_transactions[ticker] = []
                            
                            self.recent_transactions[ticker].append({
                                'amount': trans['amount'],
                                'date': pub_dt,
                                'insider': trans['insider'],
                                'code': trans['code'],
                                'type': trans['type'],
                                'flags': trans.get('flags', [])
                            })
                            
                            # Update diagnostics
                            self.diagnostics['total_filings'] += 1
                            if trans['type'] == 'buy':
                                self.diagnostics['buys'] += 1
                            elif trans['type'] == 'sell':
                                self.diagnostics['sells'] += 1
                            elif trans['type'] == 'tax':
                                self.diagnostics['tax_events'] += 1
                            
                            if 'exercise' in trans.get('flags', []):
                                self.diagnostics['exercises'] += 1
                        
                        # Show summary
                        buys = [t for t in transactions if t['type'] == 'buy']
                        sells = [t for t in transactions if t['type'] == 'sell']
                        taxes = [t for t in transactions if t['type'] == 'tax']
                        
                        if buys or sells or taxes:
                            print(f"[UNDERGROUND]     • {ticker}: {len(buys)} buys, {len(sells)} sells, {len(taxes)} tax events")
                
                except Exception as e:
                    self.diagnostics['parser_errors'] += 1
                    print(f"[UNDERGROUND]     • Error processing filing {i}: {e}")
                    continue
            
            # Now evaluate with new aggregation logic
            signals = self._evaluate_aggregated_signals()
            
            # Print diagnostics
            print(f"\n[UNDERGROUND]     • DIAGNOSTICS:")
            print(f"[UNDERGROUND]       - Total filings: {self.diagnostics['total_filings']}")
            print(f"[UNDERGROUND]       - Buys: {self.diagnostics['buys']} ({self.diagnostics['buys']/max(1,self.diagnostics['total_filings'])*100:.1f}%)")
            print(f"[UNDERGROUND]       - Sells: {self.diagnostics['sells']} ({self.diagnostics['sells']/max(1,self.diagnostics['total_filings'])*100:.1f}%)")
            print(f"[UNDERGROUND]       - Tax events: {self.diagnostics['tax_events']}")
            print(f"[UNDERGROUND]       - Exercises: {self.diagnostics['exercises']}")
            print(f"[UNDERGROUND]       - Parser errors: {self.diagnostics['parser_errors']}")
            
            # Check for fallback sensitivity mode
            borderline_candidates = self.check_fallback_sensitivity()
            if borderline_candidates:
                print(f"\n[UNDERGROUND]     • FALLBACK MODE: {len(borderline_candidates)} borderline candidates for review")
                for candidate in borderline_candidates[:3]:  # Show top 3
                    print(f"[UNDERGROUND]       - {candidate['ticker']}: {candidate['reason']}")
                
                # TODO: Send to human gate
                # self._send_to_human_gate(borderline_candidates)
            
        except Exception as e:
            print(f"[UNDERGROUND]     • Form 4 parse error: {e}")
        
        return signals
    
    def _parse_form4_transactions(self, filing_url: str) -> List[Dict]:
        """Parse all transactions from a Form 4 filing"""
        transactions = []
        
        try:
            # Get the document link
            response = self._session.get(filing_url, timeout=10)
            if response.status_code != 200:
                return transactions
            
            # Look for the actual document link
            content = response.text
            doc_match = re.search(r'href="(/Archives/edgar/data/[^"]+\.txt)"', content)
            if not doc_match:
                return transactions
            
            doc_url = "https://www.sec.gov" + doc_match.group(1)
            
            # Fetch the actual filing text
            doc_response = self._session.get(doc_url, timeout=10)
            if doc_response.status_code != 200:
                return transactions
            
            filing_text = doc_response.text
            
            # Check if it's XML format
            if '<XML>' in filing_text:
                # Parse XML format
                transactions = self._parse_xml_form4(filing_text)
            else:
                # Parse plain text format (older filings)
                transactions = self._parse_text_form4(filing_text)
            
        except Exception as e:
            print(f"[UNDERGROUND]     • Transaction parse error: {e}")
        
        return transactions
    
    def _parse_xml_form4(self, filing_text: str) -> List[Dict]:
        """Parse XML format Form 4 with robust error handling"""
        transactions = []
        
        try:
            # Extract the XML section
            xml_start = filing_text.find('<XML>')
            xml_end = filing_text.find('</XML>')
            
            if xml_start == -1 or xml_end == -1:
                return transactions
            
            xml_content = filing_text[xml_start:xml_end + 6]
            
            # Multiple attempts to fix XML
            attempts = [
                lambda x: x,  # Original
                lambda x: x.replace('&', '&amp;'),  # Fix unescaped ampersands
                lambda x: re.sub(r'&[^;]+;', '', x),  # Remove invalid entities
                lambda x: re.sub(r'[^\x20-\x7E\x09\x0A\x0D]', '', x)  # Remove non-ASCII
            ]
            
            root = None
            last_error = None
            
            for i, fix_attempt in enumerate(attempts):
                try:
                    fixed_xml = fix_attempt(xml_content)
                    
                    # Try to extract just the ownershipDocument part
                    doc_start = fixed_xml.find('<ownershipDocument>')
                    doc_end = fixed_xml.find('</ownershipDocument>') + len('</ownershipDocument>')
                    
                    if doc_start > -1 and doc_end > doc_start:
                        fixed_xml = fixed_xml[doc_start:doc_end]
                    
                    root = ET.fromstring(fixed_xml)
                    break
                    
                except ET.ParseError as e:
                    last_error = e
                    continue
            
            if root is None:
                print(f"[UNDERGROUND]     • XML parse failed after {len(attempts)} attempts")
                return transactions
            
            # Find issuer info
            issuer_ticker = None
            issuer_elem = root.find('.//issuerTradingSymbol')
            if issuer_elem is not None:
                issuer_ticker = issuer_elem.text
            
            # Find reporting owner name
            owner_name = "Unknown"
            owner_elem = root.find('.//rptOwnerName')
            if owner_elem is not None:
                owner_name = owner_elem.text
            
            # Check for 10b5-1 plan
            aff10b5_one = root.find('.//aff10b5One')
            is_10b5_1 = aff10b5_one is not None and aff10b5_one.text == '1'
            
            # Parse non-derivative transactions
            non_deriv_table = root.find('.//nonDerivativeTable')
            if non_deriv_table is not None:
                for trans in non_deriv_table.findall('.//nonDerivativeTransaction'):
                    try:
                        # Get transaction details
                        trans_date_elem = trans.find('.//transactionDate/value')
                        trans_code_elem = trans.find('.//transactionCode/value')
                        shares_elem = trans.find('.//transactionShares/value')
                        price_elem = trans.find('.//transactionPricePerShare/value')
                        acquired_elem = trans.find('.//transactionAcquiredDisposedCode/value')
                        
                        if all(x is not None for x in [trans_date_elem, trans_code_elem, acquired_elem]):
                            trans_date = trans_date_elem.text
                            trans_code = trans_code_elem.text
                            acquired = acquired_elem.text
                            
                            shares = 0
                            price = 0
                            amount = 0
                            
                            if shares_elem is not None:
                                try:
                                    shares = float(shares_elem.text.replace(',', ''))
                                except:
                                    shares = 0
                            
                            if price_elem is not None:
                                try:
                                    price = float(price_elem.text.replace('$', '').replace(',', ''))
                                except:
                                    price = 0
                            
                            amount = shares * price
                            
                            # Determine transaction type with flags
                            trans_type = 'other'
                            flags = []
                            
                            if trans_code == 'P' and acquired == 'A':
                                trans_type = 'buy'  # Open market purchase
                            elif trans_code == 'S' and acquired == 'D':
                                trans_type = 'sell'  # Open market sale
                            elif trans_code == 'F' and acquired == 'D':
                                trans_type = 'tax'  # Tax withholding (not a real transaction)
                            elif trans_code == 'M' and acquired == 'A':
                                trans_type = 'buy'  # Exercise/convert
                                flags.append('exercise')
                            elif trans_code == 'A' and acquired == 'A':
                                trans_type = 'buy'  # Grant/Award
                                flags.append('award')
                            elif trans_code == 'P' and acquired == 'D':
                                trans_type = 'sell'  # Disposition of acquired shares
                                flags.append('disposition')
                            
                            if is_10b5_1:
                                flags.append('10b5-1')
                            
                            transactions.append({
                                'type': trans_type,
                                'code': trans_code,
                                'amount': amount,
                                'shares': shares,
                                'price': price,
                                'date': trans_date,
                                'insider': owner_name,
                                'ticker': issuer_ticker,
                                'flags': flags
                            })
                    
                    except Exception as e:
                        continue
            
        except Exception as e:
            print(f"[UNDERGROUND]     • XML parse error: {e}")
        
        return transactions
    
    def _parse_text_form4(self, filing_text: str) -> List[Dict]:
        """Parse plain text format Form 4 (older format)"""
        transactions = []
        
        # Look for transaction patterns in text
        transaction_pattern = r'(\d{4}-\d{2}-\d{2})\s+([A-Z])\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)\s+([\d,]+)\s+(\$[\d,.,]+)'
        
        matches = re.findall(transaction_pattern, filing_text)
        
        for match in matches:
            try:
                transaction_date = match[0]
                transaction_code = match[1]
                
                shares_str = match[5].replace(',', '')
                price_str = match[6].replace('$', '').replace(',', '')
                
                shares = float(shares_str)
                price = float(price_str)
                amount = shares * price
                
                # Determine transaction type
                if transaction_code == 'P':
                    trans_type = 'buy'
                elif transaction_code == 'S':
                    trans_type = 'sell'
                else:
                    trans_type = 'other'
                
                transactions.append({
                    'type': trans_type,
                    'code': transaction_code,
                    'amount': amount,
                    'shares': shares,
                    'price': price,
                    'date': transaction_date,
                    'insider': 'Unknown',
                    'ticker': None
                })
                
            except (ValueError, IndexError):
                continue
        
        return transactions
    
    def _refresh_transaction_cache(self):
        """Clear old transactions outside aggregation window"""
        cutoff = datetime.now() - timedelta(days=self.aggregation_window_days)
        
        for ticker in list(self.recent_transactions.keys()):
            self.recent_transactions[ticker] = [
                trans for trans in self.recent_transactions[ticker]
                if trans['date'] > cutoff
            ]
            
            if not self.recent_transactions[ticker]:
                del self.recent_transactions[ticker]
    
    def _evaluate_aggregated_signals(self) -> List[UndergroundSignal]:
        """Evaluate all transactions with tiered aggregation logic"""
        signals = []
        
        print(f"\n[UNDERGROUND]     • Evaluating aggregated signals for {len(self.recent_transactions)} tickers...")
        
        for ticker, transactions in self.recent_transactions.items():
            if not self._check_market_cap_range(ticker):
                continue
            
            # Separate buys by type
            open_market_buys = [t for t in transactions if t['type'] == 'buy' and not any(f in t.get('flags', []) for f in ['exercise', 'award'])]
            exercise_buys = [t for t in transactions if t['type'] == 'buy' and 'exercise' in t.get('flags', [])]
            award_buys = [t for t in transactions if t['type'] == 'buy' and 'award' in t.get('flags', [])]
            
            # Calculate totals
            open_market_total = sum(b['amount'] for b in open_market_buys)
            exercise_total = sum(b['amount'] for b in exercise_buys)
            total_buys = open_market_total + exercise_total * 0.5 + award_total * 0.3  # Discount exercises/awards
            
            unique_insiders = len(set(t['insider'] for t in open_market_buys))
            total_insiders = len(set(t['insider'] for t in transactions))
            
            print(f"[UNDERGROUND]       • {ticker}:")
            print(f"         - Open market: ${open_market_total:,.0f} ({len(open_market_buys)} trades)")
            print(f"         - Exercises: ${exercise_total:,.0f} ({len(exercise_buys)} trades)")
            print(f"         - Weighted total: ${total_buys:,.0f}")
            print(f"         - Unique insiders: {unique_insiders}/{total_insiders}")
            
            # Determine confidence tier
            confidence = 0
            evidence = ""
            tier = "NONE"
            
            # HIGH CONFIDENCE: Single large buy or high aggregated total
            if any(b['amount'] >= self.high_buy_threshold for b in open_market_buys):
                confidence = 0.9
                tier = "HIGH"
                largest_buy = max(open_market_buys, key=lambda x: x['amount'])
                evidence = f"Large open market buy: ${largest_buy['amount']:,.0f} by {largest_buy['insider']}"
            elif total_buys >= self.high_buy_threshold:
                confidence = 0.85
                tier = "HIGH"
                evidence = f"High aggregated buying: ${total_buys:,.0f} across {len(open_market_buys)} open market trades"
            
            # MEDIUM CONFIDENCE: Medium aggregation or multiple insiders
            elif total_buys >= self.medium_buy_threshold:
                confidence = 0.75
                tier = "MEDIUM"
                evidence = f"Medium aggregated buying: ${total_buys:,.0f} from {unique_insiders} insiders"
            elif unique_insiders >= 2 and total_buys >= self.low_buy_threshold:
                confidence = 0.7
                tier = "MEDIUM"
                evidence = f"Multiple insider activity: {unique_insiders} insiders, ${total_buys:,.0f} total"
            elif len(exercise_buys) >= 3 and exercise_total >= self.medium_buy_threshold:
                confidence = 0.65
                tier = "MEDIUM"
                evidence = f"Coordinated exercises: ${exercise_total:,.0f} across {len(exercise_buys)} insiders"
            
            # LOW CONFIDENCE: Small but consistent buying
            elif total_buys >= self.low_buy_threshold:
                confidence = 0.55
                tier = "LOW"
                evidence = f"Small accumulation: ${total_buys:,.0f} in {len(open_market_buys)} trades"
            
            # Check for corroboration with other signals (placeholder for now)
            corroboration = self._check_corroboration(ticker)
            if corroboration and confidence > 0:
                confidence = min(0.95, confidence + 0.1)  # Boost confidence
                evidence += f" + {corroboration}"
                if tier == "LOW":
                    tier = "MEDIUM"
            
            if confidence >= 0.5:  # Minimum threshold for signal
                signal = UndergroundSignal(
                    ticker=ticker,
                    signal_type='sec_filing',
                    strength=confidence,
                    evidence=f"[{tier}] {evidence}",
                    timestamp=max(t['date'] for t in transactions),
                    sources=['SEC EDGAR'],
                    liquidity_score=self._check_liquidity(ticker),
                    dilution_risk=self._check_dilution_risk(ticker)
                )
                signals.append(signal)
                self.diagnostics['signals_generated'] += 1
                print(f"         ✓ {tier} CONFIDENCE SIGNAL: {evidence}")
            else:
                print(f"         ✗ Below threshold (confidence: {confidence:.2f})")
        
        return signals
    
    def get_aggregation_audit(self, ticker: str, window_days: int = None) -> Dict:
        """Return detailed aggregation breakdown for audit"""
        if window_days is None:
            window_days = self.aggregation_window_days
        
        cutoff = datetime.now() - timedelta(days=window_days)
        
        if ticker not in self.recent_transactions:
            return {
                'ticker': ticker,
                'window_days': window_days,
                'total_buys': 0,
                'weighted_total': 0,
                'insiders': [],
                'breakdown': {},
                'provenance': []
            }
        
        # Filter by window
        recent_trans = [t for t in self.recent_transactions[ticker] if t['date'] > cutoff]
        
        # Separate by type
        open_market = [t for t in recent_trans if t['type'] == 'buy' and not any(f in t.get('flags', []) for f in ['exercise', 'award'])]
        exercises = [t for t in recent_trans if t['type'] == 'buy' and 'exercise' in t.get('flags', [])]
        awards = [t for t in recent_trans if t['type'] == 'buy' and 'award' in t.get('flags', [])]
        
        # Calculate totals
        open_total = sum(t['amount'] for t in open_market)
        exercise_total = sum(t['amount'] for t in exercises)
        award_total = sum(t['amount'] for t in awards)
        weighted_total = open_total + exercise_total * 0.5 + award_total * 0.3
        
        # Insider breakdown
        insider_breakdown = {}
        for t in open_market:
            insider = t['insider']
            if insider not in insider_breakdown:
                insider_breakdown[insider] = {'amount': 0, 'trades': 0}
            insider_breakdown[insider]['amount'] += t['amount']
            insider_breakdown[insider]['trades'] += 1
        
        return {
            'ticker': ticker,
            'window_days': window_days,
            'total_buys': len(open_market),
            'weighted_total': weighted_total,
            'open_market_total': open_total,
            'exercise_total': exercise_total,
            'award_total': award_total,
            'insiders': list(insider_breakdown.keys()),
            'insider_breakdown': insider_breakdown,
            'breakdown': {
                'open_market': len(open_market),
                'exercises': len(exercises),
                'awards': len(awards)
            },
            'latest_date': max(t['date'] for t in recent_trans) if recent_trans else None,
            'provenance': [f"SEC EDGAR - {len(recent_trans)} transactions"]  # Simplified
        }
    
    def check_fallback_sensitivity(self) -> List[Dict]:
        """Check if we should lower thresholds due to low signal rate"""
        # If no buys in last 7 days, enable fallback mode
        recent_cutoff = datetime.now() - timedelta(days=7)
        recent_buys = 0
        
        for ticker, trans in self.recent_transactions.items():
            buys = [t for t in trans if t['type'] == 'buy' and t['date'] > recent_cutoff]
            recent_buys += len(buys)
        
        if recent_buys == 0:
            return self._generate_borderline_candidates()
        
        return []
    
    def _generate_borderline_candidates(self) -> List[Dict]:
        """Generate borderline candidates for human review"""
        candidates = []
        
        for ticker, trans in self.recent_transactions.items():
            if not self._check_market_cap_range(ticker):
                continue
            
            # Calculate with relaxed thresholds
            open_market = [t for t in trans if t['type'] == 'buy' and not any(f in t.get('flags', []) for f in ['exercise', 'award'])]
            total = sum(t['amount'] for t in open_market)
            unique_insiders = len(set(t['insider'] for t in open_market))
            
            # Very low threshold for borderline
            if total >= 25000 or (unique_insiders >= 2 and total >= 10000):
                audit = self.get_aggregation_audit(ticker, 90)
                
                candidates.append({
                    'ticker': ticker,
                    'score': 0.4,  # Low score
                    'reason': f"Borderline: ${total:,.0f} from {unique_insiders} insiders",
                    'evidence': {
                        'aggregation_audit': audit,
                        'latest_transactions': open_market[-3:],  # Last 3 buys
                        'market_cap': self._get_market_cap(ticker),
                        'liquidity': self._check_liquidity(ticker)
                    },
                    'recommended': 'WATCH'  # Not trade, just watch
                })
        
        return candidates[:10]  # Limit to top 10
    
    def _get_market_cap(self, ticker: str) -> Optional[float]:
        """Get market cap for a ticker"""
        # Placeholder - would integrate with market data provider
        return None
    
    def _is_form4_purchase(self, filing_url: str) -> bool:
        """Check if Form 4 contains purchase transactions"""
        try:
            # Get the document link
            response = self._session.get(filing_url, timeout=10)
            if response.status_code != 200:
                return False
            
            # Look for the actual document link
            content = response.text
            import re
            doc_match = re.search(r'Interactive Data Page</a>\s*<a href="([^"]+)"', content)
            if not doc_match:
                # Try alternative pattern
                doc_match = re.search(r'href="(/Archives/edgar/data/[^"]+\.txt)"', content)
            
            if not doc_match:
                return False
            
            # Build full URL
            if doc_match.group(1).startswith('/'):
                doc_url = "https://www.sec.gov" + doc_match.group(1)
            else:
                doc_url = doc_match.group(1)
            
            # Fetch the actual filing text
            doc_response = self._session.get(doc_url, timeout=10)
            if doc_response.status_code != 200:
                return False
            
            # Check for purchase indicators
            filing_text = doc_response.text.upper()
            
            # Look for purchase codes
            purchase_indicators = [
                'P - PURCHASE',
                'COMMON STOCK',
                'ACQUIRED',
                'BUY'
            ]
            
            # Must have "P - PURCHASE" code
            if 'P - PURCHASE' not in filing_text:
                return False
            
            # Exclude exercises and conversions
            exclude_indicators = [
                'EXERCISED',
                'CONVERTED',
                'DERIVATIVE',
                'OPTION'
            ]
            
            for excl in exclude_indicators:
                if excl in filing_text and 'EXERCISE' in filing_text:
                    return False
            
            return True
            
        except Exception as e:
            return False
    
    def _cik_to_ticker(self, cik: str) -> Optional[str]:
        """Convert CIK to ticker symbol"""
        try:
            # Use SEC's CIK lookup
            url = f"https://www.sec.gov/cgi-bin/browse-edgar?CIK={cik}&owner=exclude&count=10"
            response = self._session.get(url, timeout=10)
            
            if response.status_code == 200:
                content = response.text
                # Look for ticker in the page
                match = re.search(r'Ticker:</span>[^>]+>([A-Z]{1,5})<', content)
                if match:
                    return match.group(1)
            
            return None
            
        except Exception:
            return None
    
    def _fetch_8k_filings(self) -> List[UndergroundSignal]:
        """Fetch and parse 8-K material event filings"""
        signals = []
        
        try:
            response = self._session.get(self.sec_8k_url, timeout=30)
            if response.status_code != 200:
                print(f"[UNDERGROUND]     • 8-K HTTP error: {response.status_code}")
                return signals
            
            # Parse XML
            root = ET.fromstring(response.content)
            
            # Define namespace
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            
            for entry in root.findall('atom:entry', ns):
                try:
                    # Get title
                    title = entry.find('atom:title', ns).text
                    
                    # Look for milestone keywords
                    milestone_found = False
                    milestone_type = None
                    
                    for pattern_type, keywords in self.sec_patterns.items():
                        for keyword in keywords:
                            if keyword.lower() in title.lower():
                                milestone_found = True
                                milestone_type = pattern_type
                                break
                        if milestone_found:
                            break
                    
                    if not milestone_found:
                        continue
                    
                    # Extract ticker
                    ticker_match = re.search(r'8-K\s+([A-Z]{1,5})', title.upper())
                    if not ticker_match:
                        continue
                    
                    ticker = ticker_match.group(1)
                    
                    # Get publication date
                    pub_date = entry.find('atom:published', ns).text
                    pub_dt = parse(pub_date).replace(tzinfo=None)
                    
                    # Skip if too old
                    if pub_dt < datetime.now() - timedelta(days=21):
                        continue
                    
                    # Check market cap range
                    if not self._check_market_cap_range(ticker):
                        continue
                    
                    # Create signal
                    signal = UndergroundSignal(
                        ticker=ticker,
                        signal_type='sec_filing',
                        strength=0.7,  # Medium-high for 8-K
                        evidence=f"8-K filing: {milestone_type}",
                        timestamp=pub_dt,
                        sources=['SEC EDGAR'],
                        liquidity_score=self._check_liquidity(ticker),
                        dilution_risk=self._check_dilution_risk(ticker)
                    )
                    signals.append(signal)
                    print(f"[UNDERGROUND]     • Found: {ticker} 8-K - {milestone_type}")
                    
                except Exception as e:
                    continue
            
        except Exception as e:
            print(f"[UNDERGROUND]     • 8-K parse error: {e}")
        
        return signals
    
    def _scan_niche_news(self) -> List[UndergroundSignal]:
        """Scan niche news sources for early coverage"""
        signals = []
        
        print("[UNDERGROUND]   • News Sources: Checking RSS feeds...")
        print(f"[UNDERGROUND]   • Sources configured: {len(self.niche_sources)}")
        for source in self.niche_sources[:3]:  # Show first 3
            print(f"[UNDERGROUND]     - {source}")
        if len(self.niche_sources) > 3:
            print(f"[UNDERGROUND]     ... and {len(self.niche_sources) - 3} more")
        
        # NO DEMO DATA - return empty unless real feeds exist
        try:
            # TODO: Implement real news RSS/API connection
            print("[UNDERGROUND]   • News Sources: RSS parser not connected - no data available")
        except Exception as e:
            print(f"[UNDERGROUND]   • News Sources: Error - {e}")
        
        return signals
    
    def _scan_options_activity(self) -> List[UndergroundSignal]:
        """Look for unusual options activity in small caps"""
        signals = []
        
        print("[UNDERGROUND]   • Options Flow: Checking for unusual volume...")
        print(f"[UNDERGROUND]   • Min volume threshold: 5x average")
        print(f"[UNDERGROUND]   • Min contracts: {self.min_adv // 1000}K")
        
        # NO DEMO DATA - return empty unless real feeds exist
        try:
            # TODO: Implement real options flow API connection
            print("[UNDERGROUND]   • Options Flow: Data vendor not connected - no data available")
        except Exception as e:
            print(f"[UNDERGROUND]   • Options Flow: Error - {e}")
        
        return signals
    
    def _scan_hiring_patterns(self) -> List[UndergroundSignal]:
        """Look for aggressive hiring in key roles"""
        signals = []
        
        print("[UNDERGROUND]   • Job Postings: Checking for hiring spikes...")
        print("[UNDERGROUND]   • Target: +100%+ growth in key roles")
        print("[UNDERGROUND]   • Sources: LinkedIn, Indeed, company careers")
        
        # NO DEMO DATA - return empty unless real feeds exist
        try:
            # TODO: Implement real job posting scraping
            print("[UNDERGROUND]   • Job Postings: Web scraper not connected - no data available")
        except Exception as e:
            print(f"[UNDERGROUND]   • Job Postings: Error - {e}")
        
        return signals
    
    def _check_market_cap_range(self, ticker: str) -> bool:
        """Check if ticker is in target market cap range"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            market_cap = info.get('marketCap', 0)
            
            return self.min_market_cap <= market_cap <= self.max_market_cap
        except:
            return False
    
    def _is_undercovered(self, ticker: str) -> bool:
        """Check if stock has low analyst coverage"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            analysts = info.get('numberOfAnalystOpinions', 0)
            
            # Undercovered = less than 5 analysts
            return analysts < 5
        except:
            return True  # Assume undercovered if can't check
    
    def _check_liquidity(self, ticker: str) -> float:
        """Score liquidity based on volume and market cap"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            avg_volume = info.get('averageVolume', 0)
            market_cap = info.get('marketCap', 0)
            
            # Daily volume ratio
            volume_ratio = (avg_volume * info.get('currentPrice', 1)) / market_cap
            
            if volume_ratio > 0.01:  # >1% of market cap trades daily
                return 0.8
            elif volume_ratio > 0.005:  # >0.5% daily
                return 0.6
            else:
                return 0.3
        except:
            return 0.1  # Very low if can't determine
    
    def _check_dilution_risk(self, ticker: str) -> str:
        """Assess dilution risk based on recent activity"""
        # Demo - would check recent offerings, share count changes
        return 'MEDIUM'  # Conservative default
    
    def get_diagnostics(self) -> Dict:
        """Return comprehensive diagnostics for operations"""
        # Calculate additional metrics
        total_transactions = sum(len(trans) for trans in self.recent_transactions.values())
        
        # Buy/sell ratio
        buy_ratio = self.diagnostics['buys'] / max(1, self.diagnostics['total_filings']) * 100
        sell_ratio = self.diagnostics['sells'] / max(1, self.diagnostics['total_filings']) * 100
        
        # Top tickers by activity
        ticker_activity = {}
        for ticker, trans in self.recent_transactions.items():
            buys = len([t for t in trans if t['type'] == 'buy'])
            ticker_activity[ticker] = buys
        
        top_tickers = sorted(ticker_activity.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Exclusion reasons
        exclusions = {
            'tax_events': self.diagnostics['tax_events'],
            'exercises': self.diagnostics['exercises'],
            'parser_errors': self.diagnostics['parser_errors']
        }
        
        return {
            'timestamp': datetime.now().isoformat(),
            'strategy': self.strategy,
            'thresholds': {
                'high': self.high_buy_threshold,
                'medium': self.medium_buy_threshold,
                'low': self.low_buy_threshold,
                'window_days': self.aggregation_window_days
            },
            'filings': {
                'total': self.diagnostics['total_filings'],
                'buys': self.diagnostics['buys'],
                'sells': self.diagnostics['sells'],
                'buy_ratio': f"{buy_ratio:.1f}%",
                'sell_ratio': f"{sell_ratio:.1f}%"
            },
            'exclusions': exclusions,
            'signals': {
                'generated': self.diagnostics['signals_generated'],
                'pending_review': len(self.check_fallback_sensitivity())
            },
            'activity': {
                'total_transactions': total_transactions,
                'active_tickers': len(self.recent_transactions),
                'top_tickers': dict(top_tickers)
            },
            'health': {
                'parser_errors': self.diagnostics['parser_errors'],
                'error_rate': f"{self.diagnostics['parser_errors']/max(1,self.diagnostics['total_filings'])*100:.1f}%"
            }
        }
    
    def _check_corroboration(self, ticker: str) -> str:
        """Check for corroborating signals from other sources"""
        # Placeholder for future implementation
        # Will check for options flow, news, hiring spikes
        return 'MEDIUM'  # Conservative default
    
    def _filter_and_rank(self, signals: List[UndergroundSignal]) -> List[UndergroundSignal]:
        """Filter signals and rank by opportunity score"""
        # Remove duplicates
        unique_signals = {}
        for signal in signals:
            key = f"{signal.ticker}_{signal.signal_type}"
            if key not in unique_signals or signal.strength > unique_signals[key].strength:
                unique_signals[key] = signal
        
        # Filter by minimum liquidity
        filtered = [s for s in unique_signals.values() if s.liquidity_score > 0.3]
        
        # Sort by composite score
        def opportunity_score(s: UndergroundSignal) -> float:
            return (s.strength * 0.5 + 
                   s.liquidity_score * 0.3 + 
                   (1 if s.signal_type == 'sec_filing' else 0) * 0.2)
        
        ranked = sorted(filtered, key=opportunity_score, reverse=True)
        
        return ranked[:10]  # Top 10 opportunities
