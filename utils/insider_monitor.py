import re
import requests
import time
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from lxml import etree
import yfinance as market_data

# SEC EDGAR RSS feeds for Form 4 filings (actual insider trading data)
SEC_FORM4_URLS = [
    "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type=4&company=&dateb=&owner=include&count=100&output=atom",
    "https://www.sec.gov/Archives/edgar/data/1559720/000155972025000004/0001559720-25-000004.txt"  # Example format
]


class InsiderMonitor:
    """
    Lightweight insider trading monitor using free RSS (no API key).
    Focuses on Form 4 open-market purchases (best-effort from RSS titles).
    """

    def __init__(self, config: Dict):
        self.config = config or {}
        from utils.price_filter_config import resolve_price_filter
        self.price_filter_enabled, cap = resolve_price_filter(self.config)
        integrator = self.config.get("insider_integrator", {})
        self.max_share_price = cap if self.price_filter_enabled else float(
            integrator.get("max_price", 10000.0)
        )
        self.min_share_price = float(integrator.get("min_price", 1.0))
        self.enabled = bool(self.config.get("insider_monitor", {}).get("enabled", False))
        self.penny_only = bool(self.config.get("insider_monitor", {}).get("penny_only", True))
        self.min_value = float(self.config.get("insider_monitor", {}).get("min_value", 20000))
        self.tickers = set([t.upper() for t in self.config.get("insider_monitor", {}).get("tickers", [])])
        self.lookback_days = int(self.config.get("insider_monitor", {}).get("lookback_days", 3))
        
        # Caching to avoid re-processing filings
        self.processed_filings = set()
        self.cache_file = "insider_filing_cache.txt"
        self._load_cache()
    
    def _load_cache(self):
        """Load processed filing URLs from cache file."""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    self.processed_filings = set(line.strip() for line in f if line.strip())
                print(f"[INSIDER] Loaded {len(self.processed_filings)} cached filings")
        except Exception as e:
            print(f"[INSIDER] Warning: Could not load cache: {e}")
            self.processed_filings = set()
    
    def _save_cache(self):
        """Save processed filing URLs to cache file."""
        try:
            with open(self.cache_file, 'w') as f:
                for url in sorted(self.processed_filings):
                    f.write(url + '\n')
        except Exception as e:
            print(f"[INSIDER] Warning: Could not save cache: {e}")

    def _parse_rss(self, content: str) -> List[Dict]:
        """Parse RSS/Atom feed from SEC EDGAR."""
        entries = []
        
        try:
            # Try parsing as XML - remove encoding declaration for lxml
            if content.startswith('<?xml'):
                content = content.split('?>', 1)[1]
            root = etree.fromstring(content.encode('utf-8'))
            
            # Handle both RSS and Atom formats
            # Atom namespace
            for entry in root.findall("{http://www.w3.org/2005/Atom}entry"):
                title_elem = entry.find("{http://www.w3.org/2005/Atom}title")
                link_elem = entry.find("{http://www.w3.org/2005/Atom}link")
                published_elem = entry.find("{http://www.w3.org/2005/Atom}published")
                
                title = title_elem.text if title_elem is not None else ""
                link = link_elem.get("href") if link_elem is not None else ""
                published = published_elem.text if published_elem is not None else ""
                
                entries.append({
                    "title": title,
                    "link": link,
                    "published": published
                })
            
            # RSS format (no namespace)
            for item in root.findall(".//item"):
                title_elem = item.find("title")
                link_elem = item.find("link")
                pub_date_elem = item.find("pubDate")
                
                title = title_elem.text if title_elem is not None else ""
                link = link_elem.text if link_elem is not None else ""
                published = pub_date_elem.text if pub_date_elem is not None else ""
                
                entries.append({
                    "title": title,
                    "link": link,
                    "published": published
                })
                
        except Exception as e:
            print(f"[INSIDER] Error parsing RSS: {e}")
            
        return entries

    def _extract_ticker_and_price(self, title: str) -> (Optional[str], Optional[float]):
        """
        Attempt to extract ticker and price from RSS title.
        Titles often look like: "Insider Buy: CEO John Smith at XYZ (Price $1.23)"
        """
        ticker = None
        price = None

        # Ticker is typically uppercase word with 1-5 letters before "("
        m_ticker = re.search(r"\b([A-Z]{1,5})\b", title)
        if m_ticker:
            ticker = m_ticker.group(1)

        m_price = re.search(r"\$([0-9]+(\.[0-9]+)?)", title)
        if m_price:
            try:
                price = float(m_price.group(1))
            except Exception:
                price = None

        return ticker, price

    def _is_purchase(self, title: str) -> bool:
        """Check if title indicates a buy/purchase (not a sale)."""
        # SEC Form 4 titles don't indicate purchase/sale - need to fetch details
        # For now, assume all Form 4s could be purchases and filter later
        return True
    
    def _fetch_and_parse_form4_xml(self, entry: Dict) -> List[Dict]:
        """Fetch the actual Form 4 XML and extract transaction details."""
        link = entry.get("link", "")
        if not link:
            return []
        
        try:
            # Add delay to respect SEC rate limits
            time.sleep(1.5)
            
            # Fetch filing index page
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
                "Cache-Control": "max-age=0"
            }
            resp = requests.get(link, headers=headers, timeout=10)
            
            if self._handle_sec_error(resp.status_code, "filing index page fetch"):
                return []
            elif resp.status_code != 200:
                return []
            
            # Look for the primary document XML link
            # Prefer plain XML files, not the xslF345X05 versions (which are HTML)
            xml_matches = re.findall(r'href="([^"]*\.xml)"', resp.text)
            
            # Filter out xslF345X05 URLs (they return HTML)
            xml_urls = [m for m in xml_matches if 'xslF345X05' not in m]
            
            if not xml_urls:
                return []
            
            xml_url = xml_urls[0]  # Use the first non-xsl XML file
            if not xml_url.startswith("http"):
                # Convert relative URL to absolute
                base_url = "https://www.sec.gov"
                xml_url = base_url + xml_url
            
            # Fetch XML document
            time.sleep(1.5)  # Another delay for XML fetch
            xml_resp = requests.get(xml_url, headers=headers, timeout=10)
            
            if self._handle_sec_error(xml_resp.status_code, "XML document fetch"):
                return []
            elif xml_resp.status_code != 200:
                return []
            
            # Parse the XML for transaction details
            return self._parse_form4_transactions(xml_resp.text)
            
        except Exception as e:
            return []
    
    def _parse_form4_transactions(self, xml_content: str) -> List[Dict]:
        """Parse Form 4 XML to extract open-market buy/sell transactions."""
        try:
            root = etree.fromstring(xml_content.encode('utf-8'))  # Ensure bytes
            
            # Remove namespaces for easier parsing
            for elem in root.iter():
                if '}' in elem.tag:
                    elem.tag = elem.tag.split('}', 1)[1]
            
            transactions = []
            
            # Find ticker (more reliably)
            issuer = root.find("issuer")
            ticker = None
            if issuer is not None:
                ticker_elem = issuer.find("issuerTradingSymbol")
                if ticker_elem is not None:
                    ticker = ticker_elem.text.strip()
            
            # Extract insider info for role-based filtering
            insider_name = None
            insider_role = None
            reporting_owner = root.find("reportingOwner")
            if reporting_owner is not None:
                # Get insider name
                owner_id = reporting_owner.find("reportingOwnerId")
                if owner_id is not None:
                    name_elem = owner_id.find("rptOwnerName")
                    if name_elem is not None:
                        insider_name = name_elem.text.strip()
                
                # Get insider role
                relationship = reporting_owner.find("reportingOwnerRelationship")
                if relationship is not None:
                    if relationship.find("isDirector") is not None and relationship.find("isDirector").text == "true":
                        insider_role = "Director"
                    if relationship.find("isOfficer") is not None and relationship.find("isOfficer").text == "true":
                        insider_role = "Officer"
                    if relationship.find("isTenPercentOwner") is not None and relationship.find("isTenPercentOwner").text == "true":
                        insider_role = "10% Owner"
            
            print(f"[DEBUG] Found ticker: {ticker}")
            print(f"[DEBUG] Insider: {insider_name} ({insider_role})")
            
            if not ticker:
                print("[DEBUG] No ticker found")
                return []
            
            # Non-derivative transactions
            non_deriv_table = root.find("nonDerivativeTable")
            if non_deriv_table is None:
                print("[DEBUG] No nonDerivativeTable (common for option-only filings)")
                return []
            
            tx_elems = non_deriv_table.findall("nonDerivativeTransaction")
            print(f"[DEBUG] Found {len(tx_elems)} non-derivative transactions")
            
            for tx in tx_elems:
                coding_elem = tx.find("transactionCoding")
                if coding_elem is None:
                    continue
                code_elem = coding_elem.find("transactionCode")
                code = code_elem.text.strip() if code_elem is not None and code_elem.text else None
                
                print(f"[DEBUG] Transaction code: {code}")
                
                if code not in ["P", "S"]:
                    continue
                
                # Transaction amounts
                amounts_elem = tx.find("transactionAmounts")
                if amounts_elem is None:
                    continue
                
                shares_elem = amounts_elem.find("transactionShares/value")
                price_elem = amounts_elem.find("transactionPricePerShare/value")
                ad_elem = amounts_elem.find("transactionAcquiredDisposedCode/value")
                
                # Add optional transaction date for better context
                date_elem = tx.find("transactionDate/value")
                tx_date = date_elem.text.strip() if date_elem is not None and date_elem.text else None
                
                shares = shares_elem.text.strip() if shares_elem is not None and shares_elem.text else None
                price = price_elem.text.strip() if price_elem is not None and price_elem.text else None
                ad_code = ad_elem.text.strip() if ad_elem is not None and ad_elem.text else None
                
                if not all([shares, price, ad_code]):
                    print("[DEBUG] Missing data, skipping")
                    continue
                
                try:
                    shares_num = float(shares)
                    price_num = float(price)
                    if price_num <= 0:
                        continue
                    
                    transactions.append({
                        "ticker": ticker,
                        "date": tx_date,
                        "transaction_code": code,
                        "shares": shares_num,
                        "price": price_num,
                        "acquired_disposed": ad_code,
                        "total_value": shares_num * price_num,
                        "insider_name": insider_name,
                        "insider_role": insider_role
                    })
                    print(f"[DEBUG] Added: {ticker} {code} {shares_num} @ ${price_num}")
                except ValueError:
                    continue
            
            print(f"[DEBUG] Returning {len(transactions)} transactions")
            return transactions
        
        except etree.XMLSyntaxError as e:
            print(f"[ERROR] Invalid XML: {e}")
            return []
        except Exception as e:
            print(f"[ERROR] Parsing failed: {e}")
            return []

    def _passes_filters(self, entry: Dict) -> bool:
        title = entry.get("title", "")
        if not self._is_purchase(title):
            return False

        ticker, price = self._extract_ticker_and_price(title)

        # Ticker filter
        if self.tickers and ticker and ticker not in self.tickers:
            return False

        # Penny filter
        if self.penny_only and price is not None and price > 5.0:
            return False

        # Simple value filter based on presence of "K" or "M" if present
        if self.min_value:
            # Quick heuristic: look for "$XYZK" or "$XYM"
            m_val = re.search(r"\$([0-9]+(\.[0-9]+)?)([KM]?)", title)
            if m_val:
                val = float(m_val.group(1))
                suffix = m_val.group(3)
                if suffix == "K":
                    val *= 1_000
                elif suffix == "M":
                    val *= 1_000_000
                if val < self.min_value:
                    return False

        return True

    def _handle_sec_error(self, resp_status: int, error_context: str = "") -> bool:
        """Handle SEC EDGAR errors with proper retry logic."""
        if resp_status == 403:
            print(f"[INSIDER] SEC EDGAR access forbidden - {error_context}")
            print("[INSIDER] Rate limited or blocked - will retry in next cycle")
            return True  # Signal to skip this attempt but try again later
        elif resp_status == 429:
            print(f"[INSIDER] SEC EDGAR rate limit - {error_context}")
            print("[INSIDER] Too many requests - will retry in next cycle")
            return True
        elif resp_status >= 500:
            print(f"[INSIDER] SEC EDGAR server error - {error_context}")
            print("[INSIDER] Server issue - will retry in next cycle")
            return True
        return False
    
    def get_recent_signals(self) -> List[Dict]:
        """Fetch and filter recent insider buys from SEC EDGAR."""
        print(f"[INSIDER] DEBUG: fetch_recent_buys() called, enabled={self.enabled}")
        
        if not self.enabled:
            print("[INSIDER] DEBUG: Insider monitor disabled, returning empty list")
            return []

        print(f"[INSIDER] Fetching SEC EDGAR Form 4 data...")
        
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
                "Cache-Control": "max-age=0"
            }
            resp = requests.get(SEC_FORM4_URLS[0], headers=headers, timeout=30)
            
            if self._handle_sec_error(resp.status_code, "RSS feed fetch"):
                return []  # Skip this cycle, retry next time
            elif resp.status_code != 200:
                print(f"[INSIDER] Failed to fetch SEC data: HTTP {resp.status_code}")
                return []
        except Exception as e:
            # Catch all network errors (DNS, timeout, HTTP errors)
            print(f"[INSIDER] Network error fetching SEC data: {e}")
            print("[INSIDER] Will retry in next cycle")
            return []  # Return empty list, not fake data
        
        # If we got here, SEC fetch was successful
        print(f"[INSIDER] Processing 100 entries...")
        
        # Parse RSS/Atom feed
        entries = self._parse_rss(resp.text)
        print(f"\n[INSIDER] DEBUG: Total entries parsed: {len(entries)}")
        
        if len(entries) == 0:
            print("[INSIDER] No entries found in SEC feed")
            return []
        
        all_transactions = []
        cutoff = datetime.utcnow() - timedelta(days=self.lookback_days)
        
        # Process more entries to catch clusters (increased from 20 to 50)
        entries_to_process = entries[:50]
        print(f"[INSIDER] Processing first {len(entries_to_process)} entries with XML parsing...")
        
        for i, entry in enumerate(entries_to_process):
            pub_raw = entry.get("published", "")
            try:
                pub_dt = datetime.strptime(pub_raw, "%a, %d %b %Y %H:%M:%S %Z")
            except Exception:
                try:
                    # Try alternative format
                    pub_dt = datetime.strptime(pub_raw, "%Y-%m-%dT%H:%M:%SZ")
                except Exception:
                    pub_dt = None

            if pub_dt and pub_dt < cutoff:
                continue
            
            link = entry.get("link", "")
            
            # Check if already processed
            if link in self.processed_filings:
                print(f"\n[INSIDER] Entry {i+1}: {entry.get('title', '')[:60]}... (cached)")
                continue
            
            print(f"\n[INSIDER] Entry {i+1}: {entry.get('title', '')[:60]}...")
            
            # Fetch and parse the actual Form 4 XML
            transactions = self._fetch_and_parse_form4_xml(entry)
            
            # Mark as processed
            self.processed_filings.add(link)
            
            if transactions:
                print(f"[INSIDER]   Found {len(transactions)} transaction(s)")
                for tx in transactions:
                    print(f"[INSIDER]   - {tx['ticker']}: {tx['transaction_code']} {tx['shares']} shares @ ${tx['price']:.2f}")
                    
                    # Filter for actionable trades
                    if self._is_actionable_transaction(tx):
                        all_transactions.append(tx)
                else:
                    print("[INSIDER]   No actionable transactions found")
            
            # If no actionable transactions found, report it
            if len(all_transactions) == 0:
                print("[INSIDER] No actionable transactions found")
                return []
            
            # Apply clustering logic
            clustered_signals = self._apply_clustering(all_transactions)
            
            # Check for high-scoring signals to alert
            for signal in clustered_signals:
                if signal.get("opportunity_score", 0) >= 80 or signal.get("transaction_value", 0) >= 500000:
                    print(f"\n🚨 HIGH-CONFIDENCE INSIDER BUY ALERT!")
                    print(f"   Ticker: {signal['ticker']}")
                    print(f"   Insider: {signal['insider_name']}")
                    print(f"   Value: ${signal['transaction_value']:,.0f}")
                    print(f"   Score: {signal['opportunity_score']}/100")
                    print(f"   Reasoning: {signal['reasoning']}")
            
            # Also check for large-cap conviction buys
            self._check_large_cap_signals(all_transactions)
            
            # Save cache before returning
            self._save_cache()
            
            print(f"\n[INSIDER] Found {len(clustered_signals)} actionable opportunities after clustering")
            print(f"[INSIDER] DEBUG: clustered_signals type: {type(clustered_signals)}")
            print(f"[INSIDER] DEBUG: clustered_signals length: {len(clustered_signals) if clustered_signals else 'None'}")
            
            # If no actionable signals found, report it
            if len(clustered_signals) == 0:
                print("[INSIDER] No actionable signals found")
                return []
            
            return clustered_signals

    def fetch_recent_buys(self) -> List[Dict]:
        """Backward-compatible alias for get_recent_signals."""
        return self.get_recent_signals()
    
    def _apply_clustering(self, transactions: List[Dict]) -> List[Dict]:
        """Apply clustering logic to identify strong signals."""
        # Group transactions by ticker
        ticker_groups = {}
        for tx in transactions:
            ticker = tx["ticker"]
            if ticker not in ticker_groups:
                ticker_groups[ticker] = []
            ticker_groups[ticker].append(tx)
        
        clustered_signals = []
        
        for ticker, txs in ticker_groups.items():
            # Format each transaction as moonshot signal
            for tx in txs:
                signal = self._format_signal(tx, is_clustered=False)
                if signal:  # Only include if passes moonshot filters
                    # Add cluster info if multiple
                    if len(txs) > 1:
                        signal["title"] = f"🚀 CLUSTER: {len(txs)} insiders buying {ticker}"
                        signal["moonshot_score"] += 20  # Cluster bonus
                        signal["reasoning"] = f"🚀 CLUSTER ALERT: {len(txs)} insiders | " + signal["reasoning"]
                    clustered_signals.append(signal)
        
        return clustered_signals
    
    def _get_stock_info(self, ticker: str) -> Dict:
        """Fetch stock info including price and market cap for moonshot analysis."""
        try:
            ticker_obj = market_data.Ticker(ticker)
            info = ticker_obj.info
            
            # Get current price
            hist = ticker_obj.history(period="1d")
            current_price = float(hist['Close'].iloc[-1]) if not hist.empty else None
            
            return {
                "current_price": current_price,
                "market_cap": info.get("marketCap", 0),
                "sector": info.get("sector", "Unknown"),
                "industry": info.get("industry", "Unknown"),
                "fifty_two_week_high": info.get("fiftyTwoWeekHigh", 0),
                "average_volume": info.get("averageVolume", 0),
                "day_high": info.get("dayHigh", 0)
            }
        except Exception as e:
            print(f"[INSIDER] Could not fetch info for {ticker}: {e}")
            return {}
    def _get_current_price(self, ticker: str) -> Optional[float]:
        """Fetch current stock price using provider bridge."""
        info = self._get_stock_info(ticker)
        return info.get("current_price")
    
    def _check_large_cap_signals(self, transactions: List[Dict]):
        """Check for large-cap insider buys and display as conviction signals."""
        large_cap_buys = []
        
        for tx in transactions:
            if tx.get("transaction_code") == "P" and tx.get("total_value", 0) >= 50000:
                stock_info = self._get_stock_info(tx["ticker"])
                market_cap = stock_info.get("market_cap", 0)
                
                if market_cap > 2_000_000_000:  # >$2B = large cap
                    large_cap_buys.append((tx, stock_info))
        
        if large_cap_buys:
            print(f"\n📊 LARGE-CAP CONVICTION BUYS (Institutional Grade):")
            print("=" * 60)
            
            for tx, info in large_cap_buys:
                ticker = tx["ticker"]
                value = tx["total_value"]
                insider = tx.get("insider_name", "Unknown")
                sector = info.get("sector", "Unknown")
                current_price = info.get("current_price")
                purchase_price = tx["price"]
                market_cap = info.get("market_cap", 0)
                
                print(f"\n🏢 {ticker} - Large Cap Insider Buy")
                print(f"   Insider: {insider}")
                print(f"   Value: ${value:,.0f}")
                print(f"   Market Cap: ${market_cap/1e9:.1f}B")
                print(f"   Sector: {sector}")
                if current_price:
                    discount = ((current_price - purchase_price) / current_price) * 100
                    print(f"   Price: ${purchase_price:.2f} → ${current_price:.2f} ({discount:+.1f}%)")
                
                # Add analysis
                if sector in ["Energy", "Technology", "Biotechnology"]:
                    print(f"   💡 Note: Hot sector insider buying - institutional confidence")
                
                if value >= 500000:
                    print(f"   💪 Strong conviction: ${value:,.0f} buy shows commitment")
            
            print(f"\nTotal large-cap conviction buys: {len(large_cap_buys)}")
    
    def _format_signal(self, tx: Dict, is_clustered: bool = False) -> Dict:
        """Format a transaction as a moonshot signal."""
        ticker = tx["ticker"]
        purchase_price = tx["price"]
        
        # Get comprehensive stock info
        stock_info = self._get_stock_info(ticker)
        current_price = stock_info.get("current_price")
        market_cap = stock_info.get("market_cap", 0)
        sector = stock_info.get("sector", "Unknown")
        
        # Moonshot filter: Focus on small/micro-caps
        if market_cap > 2_000_000_000:  # >$2B = too large for moonshots
            print(f"[INSIDER] {ticker} excluded: Market cap ${market_cap/1e9:.1f}B > $2B limit")
            return None
        
        cap_category = "Micro-cap" if market_cap < 500_000_000 else "Small-cap"
        
        # Calculate discount percentage
        discount_pct = 0
        if current_price and current_price > 0:
            discount_pct = ((current_price - purchase_price) / current_price) * 100
        
        # Moonshot scoring (0-100)
        score = self._calculate_moonshot_score(tx, stock_info, discount_pct)
        
        # Check for hot sectors with tiered bonuses
        sector_bonus = self._get_sector_bonus(sector)
        score += sector_bonus
        
        reasoning = f"🚀 MOONSHOT: {cap_category} ${market_cap/1e6:.0f}M | "
        reasoning += f"Form 4 purchase of {tx['shares']} shares at ${purchase_price:.2f}"
        if current_price:
            reasoning += f" (Current: ${current_price:.2f}, {discount_pct:+.1f}%)"
        if sector_bonus > 0:
            reasoning += f" | 🔥 Sector bonus: {sector} (+{sector_bonus})"
        
        return {
            "ticker": ticker,
            "title": f"🚀 MOONSHOT: {tx.get('insider_name', 'Unknown')} ({tx.get('insider_role', 'Unknown')}) buys {ticker}",
            "link": "",
            "published": tx.get("date", ""),
            "price": purchase_price,
            "insider_name": tx.get("insider_name", "Unknown"),
            "transaction_type": f"{tx['transaction_code']} - Purchase",
            "transaction_value": tx["total_value"],
            "purchase_price": purchase_price,
            "current_price": current_price or purchase_price,
            "discount_pct": discount_pct,
            "market_cap": market_cap,
            "cap_category": cap_category,
            "sector": sector,
            "opportunity_score": min(score, 100),
            "moonshot_score": score,
            "reasoning": reasoning,
            "is_moonshot": True
        }
    
    def _format_mock_signal(self, mock_signal: Dict) -> Dict:
        """Format mock signal as moonshot signal"""
        return {
            "title": mock_signal["title"],
            "ticker": mock_signal["ticker"],
            "score": mock_signal["moonshot_score"],
            "source": "mock_insider",
            "reasoning": mock_signal["reasoning"],
            "price": mock_signal["price"],
            "date": mock_signal["date"],
            "insider": mock_signal["insider_name"],
            "value": mock_signal["transaction_value"],
            "is_moonshot": True,
            "moonshot_score": mock_signal["moonshot_score"],
            "opportunity_score": mock_signal["moonshot_score"]
        }
        
    def _is_actionable_transaction(self, tx: Dict) -> bool:
        """Check if transaction meets our criteria."""
        price = tx.get("price", 0)
        if price < self.min_share_price or price > self.max_share_price:
            return False
        
        # Check minimum transaction value (lowered to $50,000 for moonshot hunting)
        if tx.get("total_value", 0) < 50000:
            return False
        
        return True
    
    def _calculate_moonshot_score(self, tx: Dict, stock_info: Dict, discount_pct: float) -> int:
        """Calculate moonshot potential score."""
        base_score = 30
        
        # Size bonus (log scale)
        value = tx.get("total_value", 0)
        if value >= 1_000_000:
            base_score += 25
        elif value >= 500_000:
            base_score += 15
        
        # Role bonus
        role = tx.get("insider_role", "")
        if "Officer" in role:
            base_score += 15
        elif "Director" in role:
            base_score += 10
        
        # Discount bonus
        if discount_pct < -10:
            base_score += 20
        elif discount_pct < -5:
            base_score += 10
        
        # Small-cap bonus
        market_cap = stock_info.get("market_cap", 0)
        if market_cap < 500_000_000:
            base_score += 15
        elif market_cap < 1_000_000_000:
            base_score += 10
        
        return base_score
    
    def _is_hot_sector(self, sector: str) -> bool:
        """Check if sector is among hot 2025 sectors."""
        hot_sectors = [
            "Technology", "Software", "Semiconductors", "IT Services",
            "Biotechnology", "Energy", "Financial Services"
        ]
        return sector in hot_sectors
    
    def _calculate_opportunity_score(self, tx: Dict) -> int:
        """Calculate opportunity score based on transaction details."""
        base_score = 50
        
        # Larger purchases get higher scores
        value = tx.get("total_value", 0)
        if value > 100000:
            base_score += 20
        elif value > 50000:
            base_score += 10
        
        # Higher price stocks (but not too high)
        price = tx.get("price", 0)
        if 5 <= price <= 30:
            base_score += 10
        
        return min(base_score, 100)


_insider_monitor: Optional[InsiderMonitor] = None


def get_insider_monitor(config: Dict) -> InsiderMonitor:
    global _insider_monitor
    if _insider_monitor is None:
        _insider_monitor = InsiderMonitor(config)
    return _insider_monitor
