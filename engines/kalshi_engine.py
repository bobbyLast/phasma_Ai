"""Kalshi Prediction Market Integration (read-only skeleton)

Provides a thin client around Kalshi's public market data API so Phasma can
compare its own probabilities (e.g. crash odds) against market-implied odds.

This module is intentionally read-only for now. Trading/execution endpoints
would require explicit API keys and additional safety checks.

Geopolitical analysis integration added.
"""

import os
from typing import Any, Dict, List, Optional

import requests
import statistics

try:
    from engines.news_engine_core import NewsAPIIntegration
except ImportError:
    NewsAPIIntegration = None

try:
    from engines.weather_validation_engine import WeatherValidationEngine
except ImportError:
    WeatherValidationEngine = None

try:
    from engines.weather_consistency_engine import WeatherConsistencyEngine
except ImportError:
    WeatherConsistencyEngine = None


class KalshiPredictionEngine:
    """Lightweight client for Kalshi market data.

    Uses the public market data endpoints documented at:
    https://docs.kalshi.com/
    """

    def __init__(self, config):
        self.config = config
        # Kalshi API base URL - elections API (working with API key)
        self.base_url = "https://api.elections.kalshi.com/trade-api/v2"
        self.session = requests.Session()
        # Optional API key (not required for public market data)
        self.api_key: Optional[str] = os.getenv("KALSHI_API_KEY") or self.config.get(
            "kalshi.api_key", None
        )

        # Set authorization header if API key is available
        if self.api_key:
            self.session.headers.update({"Authorization": f"Bearer {self.api_key}"})
            
        # Cache for analyzed races to avoid redundant processing
        self._analyzed_races = {}

        # Initialize news engine for real-time prediction context
        self.news_engine = NewsAPIIntegration(self.config) if NewsAPIIntegration else None
        
        # Initialize weather validation engine for temperature markets
        self.weather_engine = WeatherValidationEngine(self.config) if WeatherValidationEngine else None
        
        # Initialize weather consistency engine for high win-rate weather trading
        self.consistency_engine = WeatherConsistencyEngine() if WeatherConsistencyEngine else None
        
        # Trading parameters for position sizing
        self.bankroll = self.config.get('trading', {}).get('bankroll', 5000)
        self.risk_per_trade = self.config.get('trading', {}).get('risk_per_trade', 0.02)  # 2%
        self.min_contracts = self.config.get('trading', {}).get('min_contracts', 2)
        self.max_contracts = self.config.get('trading', {}).get('max_contracts', 20)

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Internal helper for GET requests with basic error handling."""
        url = f"{self.base_url.rstrip('/')}/{path.lstrip('/') }"
        try:
            resp = self.session.get(url, params=params, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"WARNING Kalshi GET error for {url}: {e}")
            return None

    def get_series_info(self, series_ticker: str) -> Optional[Dict[str, Any]]:
        """Get information about a series (this endpoint may not exist in current API)."""
        # Note: Current Kalshi API may not have series-specific endpoints
        # This is kept for compatibility but may return None
        return self._get(f"series/{series_ticker}")

    def get_open_markets_for_series(self, series_ticker: str) -> List[Dict[str, Any]]:
        """Return all currently open markets, filtered by series ticker if possible."""
        # Get all markets and filter by series ticker
        data = self._get("markets", params={"status": "open", "limit": 200})
        if not data or "markets" not in data:
            return []

        # Filter markets by series ticker
        markets = data["markets"] or []
        if not series_ticker:
            return markets

        # First try exact series_ticker match
        exact_matches = [m for m in markets if m.get("series_ticker") == series_ticker]
        if exact_matches:
            return exact_matches

        query = str(series_ticker).lower()
        fuzzy_matches: List[Dict[str, Any]] = []
        for m in markets:
            title = str(m.get("title", "")).lower()
            event_ticker = str(m.get("event_ticker", "")).lower()
            if query in title or query in event_ticker:
                fuzzy_matches.append(m)

        if fuzzy_matches:
            return fuzzy_matches

        return markets

    @staticmethod
    def implied_probability_from_yes_price(yes_price_cents: Optional[float]) -> float:
        """Convert Kalshi YES price in cents to an implied probability (0-1)."""
        try:
            price = float(yes_price_cents or 0.0)
        except Exception:
            price = 0.0
        price = max(0.0, min(price, 100.0))
        return price / 100.0

    def scan_all_markets(self, min_volume: int = 1000, max_markets: int = 50, use_playbook: bool = False) -> List[Dict[str, Any]]:
        """Scan all available markets and return high-quality opportunities.
        
        Args:
            min_volume: Minimum volume threshold (default 1000)
            max_markets: Maximum markets to analyze (default 50)
            use_playbook: Use AI Playbook strategy (default False for backward compatibility)
        
        Returns:
            List of market opportunities
        """
        if use_playbook:
            # Use the new AI Playbook system
            try:
                from engines.kalshi_ai_playbook import KalshiAIPlaybook
                playbook = KalshiAIPlaybook(self.config)
                opportunities = playbook.find_opportunities()
                print(f"   📊 AI Playbook found {len(opportunities)} opportunities")
                
                # Convert to expected format
                formatted_opps = []
                for opp in opportunities:
                    print(f"   - {opp['ticker']}: EV={opp['ev']:.1%}, Price=${opp['yes_price']:.2f}")
                    formatted_opps.append({
                        'market': {
                            'ticker': opp['ticker'],
                            'title': opp['title'],
                            'yes_price': int(opp['yes_price'] * 100),  # Convert to cents
                            'volume': opp['volume']
                        },
                        'implied_probability': opp['yes_price'],
                        'analysis': {
                            'signal': opp['trade_signal'],
                            'confidence': opp['confidence'],
                            'rationale': opp['rationale']
                        },
                        'ev': opp['ev'],
                        'playbook_opportunity': True
                    })
                
                return formatted_opps
                
            except ImportError:
                print("⚠️ AI Playbook not available, using legacy scan")
                use_playbook = False
        
        # Legacy scanning logic (existing code)
        print(f"🎯 Scanning Kalshi markets for high-probability opportunities...")
        
        opportunities = []
        
        try:
            # Get all event series
            series_url = f"{self.base_url}/series"
            response = self.session.get(series_url)
            response.raise_for_status()
            
            series_data = response.json().get('series', [])
            print(f"   Found {len(series_data)} event series")
            if series_data:
                # Categories are empty in API response
                pass
            
            # Focus on weather-related markets for initial testing
            priority_keywords = [
                'weather', 'temperature', 'rain', 'snow', 'hurricane', 'tornado',
                'precipitation', 'heat', 'cold', 'flood', 'drought', 'wind'
            ]
            
            # Filter by keywords in title since categories are empty
            priority_series = []
            for s in series_data:
                title = s.get('title', '').lower()
                if any(keyword.lower() in title for keyword in priority_keywords):
                    priority_series.append(s)
            
            print(f"   Priority series by keyword: {len(priority_series)}")
            
            for series in priority_series[:max_markets]:
                try:
                    series_ticker = series.get('ticker')
                    if not series_ticker:
                        continue
                    
                    # Get markets for this series
                    markets_url = f"{self.base_url}/markets?series_ticker={series_ticker}"
                    markets_response = self.session.get(markets_url)
                    markets_response.raise_for_status()
                    
                    markets = markets_response.json().get('markets', [])
                    
                    for market in markets:
                        # Skip expired or settled markets
                        if market.get('status') not in ['active', 'open']:
                            continue
                            
                        # Filter for high-probability YES markets
                        # Calculate implied probability from last_price (in cents)
                        last_price = market.get('last_price', 0)
                        implied_prob = last_price / 100.0  # Convert cents to percentage
                        volume = market.get('volume', 0)
                        days_to_expiry = self._calculate_days_to_expiry(market.get('expiration_time'))
                        
                        # Only include markets with reasonable odds and volume
                        if (implied_prob > 0.30 and  # Lowered to 30% probability
                            volume >= min_volume):  # Minimum volume (no expiry limit)
                            
                            # Analyze this market
                            analysis = self.analyze_market_opportunity(market)
                            confidence = analysis.get('confidence', 0)
                            
                            # Skip confidence filter for now - let POP calculation handle it
                            opportunity = {
                                'market': market,
                                'analysis': analysis,
                                'implied_probability': implied_prob,
                                'volume': volume,
                                'days_to_expiry': days_to_expiry
                            }
                            opportunities.append(opportunity)
                            print(f"   ✅ WEATHER SIGNAL: {market.get('title', 'Unknown')} - {implied_prob:.1%} | Vol: {volume:,}")
                
                except Exception as e:
                    print(f"   ⚠️ Error processing series {series.get('ticker')}: {e}")
                    continue
            
            # Sort by probability and confidence
            opportunities.sort(key=lambda x: (
                x['implied_probability'] * x['analysis'].get('confidence', 0)
            ), reverse=True)
            
            print(f"\n   📊 Found {len(opportunities)} high-probability Kalshi opportunities")
            
        except Exception as e:
            print(f"   ❌ Error scanning Kalshi markets: {e}")
        
        return opportunities
    
    def _get_all_available_markets(self) -> List[Dict[str, Any]]:
        """Get all available markets from Kalshi API"""
        try:
            markets_url = f"{self.base_url}/markets"
            response = self.session.get(markets_url)
            response.raise_for_status()
            return response.json().get('markets', [])
        except Exception as e:
            print(f"   Error fetching markets: {e}")
            return []
    
    def _get_all_available_markets(self) -> List[Dict[str, Any]]:
        """Fetch ALL available markets from Kalshi API without series filtering."""
        try:
            print("   SCANNING FETCHING ALL KALSHI MARKETS (NO SERIES FILTER)...")
            
            all_markets = []
            cursor = None
            limit = 100
            page_count = 0
            
            # Fetch all pages of markets
            while True:
                try:
                    # Build URL with pagination
                    if cursor:
                        url = f"markets?status=open&limit={limit}&cursor={cursor}"
                    else:
                        url = f"markets?status=open&limit={limit}"
                    
                    response = self._get(url)
                    
                    if response and isinstance(response, dict):
                        markets = response.get('markets', [])
                        next_cursor = response.get('next_cursor')
                        
                        if markets:
                            print(f"   PASS Found {len(markets)} markets on page {page_count + 1}")
                            all_markets.extend(markets)
                            page_count += 1
                            
                            # Continue pagination if more pages exist
                            if next_cursor and page_count < 10:  # Limit to 10 pages max
                                cursor = next_cursor
                            else:
                                print(f"   END Reached last page or page limit")
                                break
                        else:
                            print(f"   EMPTY No markets on page {page_count + 1}")
                            break
                    else:
                        print(f"   WARNING Invalid response on page {page_count + 1}")
                        break
                        
                except Exception as e:
                    print(f"   WARNING Error fetching page {page_count + 1}: {e}")
                    break
            
            print(f"   TARGET TOTAL MARKETS FOUND: {len(all_markets)}")
            
            # Remove duplicates by ticker
            seen_tickers = set()
            unique_markets = []
            for market in all_markets:
                ticker = market.get('ticker', '')
                if ticker and ticker not in seen_tickers:
                    seen_tickers.add(ticker)
                    unique_markets.append(market)
            
            print(f"   LIST UNIQUE MARKETS: {len(unique_markets)}")
            return unique_markets
            
        except Exception as e:
            print(f"FAIL Error fetching all markets: {e}")
            return []
    
    def _preprocess_market_data(self, market: Dict[str, Any]) -> Dict[str, Any]:
        """Preprocess raw market data with calculated fields for analysis."""
        # Calculate yes price
        yes_price = None
        if "yes_ask" in market and market["yes_ask"] > 0:
            yes_price = market["yes_ask"]
        elif "yes_price" in market and market["yes_price"] > 0:
            yes_price = market["yes_price"]
        elif "last_price" in market and market["last_price"] > 0:
            yes_price = market["last_price"]
        
        # Calculate implied probability
        implied_prob = self.implied_probability_from_yes_price(yes_price)
        
        # Calculate expiration date and days to expiry
        expiration_date = market.get('expiration_time') or market.get('close_time')
        days_to_expiry = self._calculate_days_to_expiry(expiration_date)
        is_short_term = days_to_expiry <= 14 and days_to_expiry > 0
        
        # Return processed market data
        processed = market.copy()
        processed.update({
            'yes_price': yes_price,
            'implied_probability': implied_prob,
            'expiration_date': expiration_date,
            'days_to_expiry': days_to_expiry,
            'is_short_term': is_short_term
        })
        
        return processed
    
    def get_market_implied_view(self, series_ticker: str) -> List[Dict[str, Any]]:
        """Convenience helper to fetch open markets and attach implied probabilities.

        Returns a list of dicts with market data including implied probabilities and expiration info.
        """
        markets = self.get_open_markets_for_series(series_ticker)
        views: List[Dict[str, Any]] = []

        for m in markets:
            # Check for yes_price in different possible formats (FIXED FIELD MAPPINGS)
            yes_price = None
            if "yes_ask" in m and m["yes_ask"] > 0:
                yes_price = m["yes_ask"]
            elif "yes_price" in m and m["yes_price"] > 0:
                yes_price = m["yes_price"]
            elif "last_price" in m and m["last_price"] > 0:
                yes_price = m["last_price"]

            p_imp = self.implied_probability_from_yes_price(yes_price)

            # Extract expiration information directly from market (not nested)
            expiration_date = m.get('expiration_time') or m.get('close_time')
            print(f"SCANNING KALSHI DEBUG: expiration_date={expiration_date} for ticker={m.get('ticker')}")
            
            # Check all available date fields
            print(f"SCANNING KALSHI DEBUG: Available date fields:")
            print(f"   expiration_time: {m.get('expiration_time')}")
            print(f"   close_time: {m.get('close_time')}")
            print(f"   expected_expiration_time: {m.get('expected_expiration_time')}")
            print(f"   latest_expiration_time: {m.get('latest_expiration_time')}")
            
            days_to_expiry = self._calculate_days_to_expiry(expiration_date)
            print(f"SCANNING KALSHI DEBUG: calculated days_to_expiry={days_to_expiry}")

            # Determine if this is a short-term opportunity (1-2 weeks)
            is_short_term = days_to_expiry <= 14 and days_to_expiry > 0

            views.append({
                "ticker": m.get("ticker"),
                "title": m.get("title"),
                "series_ticker": m.get("series_ticker"),
                "event_ticker": m.get("event_ticker"),
                "yes_price": yes_price,
                "volume": m.get("volume", 0),
                "open_interest": m.get("open_interest", 0),
                "implied_probability": p_imp,
                "expiration_date": expiration_date,
                "days_to_expiry": days_to_expiry,
                "is_short_term": is_short_term
            })

    def get_market_trade_link(self, ticker: str) -> str:
        """Get direct trading link for a Kalshi market."""
        # For weather markets, the entire ticker is usually the event ticker
        # Kalshi event URLs follow the pattern: https://kalshi.com/events/{event_ticker}
        
        # Remove any contract-specific suffixes
        # Weather markets typically don't have complex suffixes like political markets
        if '-' in ticker:
            parts = ticker.split('-')
            # For weather markets, usually format is EVENT-YEAR or EVENT-YEAR-VALUE
            # Take everything except the last part if it looks like a specific value
            if len(parts) > 2 and parts[-1].isdigit():
                event_ticker = '-'.join(parts[:-1])
            else:
                event_ticker = ticker
        else:
            event_ticker = ticker
            
        return f"https://kalshi.com/events/{event_ticker.lower()}"
    
    def calculate_position_metrics(self, yes_price: float, signal: str, confidence: float) -> Dict[str, Any]:
        """Calculate position sizing, risk, and ROI for Kalshi binary contracts.
        
        Args:
            yes_price: Current YES contract price (0-1)
            signal: Trading signal (BUY_YES or BUY_NO)
            confidence: Confidence level (0-1)
            
        Returns:
            Dictionary with position metrics and calculations
        """
        try:
            # Calculate risk amount per trade
            risk_amount = self.bankroll * self.risk_per_trade
            
            # Determine contract price and risk based on signal
            if signal == "BUY_YES":
                contract_price = yes_price
                max_loss_per_contract = contract_price  # Lose full price if wrong
                max_profit_per_contract = 1.0 - contract_price  # Settle at $1.00 if correct
            elif signal == "BUY_NO":
                contract_price = 1.0 - yes_price  # NO contract price
                max_loss_per_contract = contract_price  # Lose full price if wrong
                max_profit_per_contract = yes_price  # Settle at $1.00 - yes_price if correct
            else:
                return {"error": "Invalid signal"}
            
            # Calculate position size based on risk
            if max_loss_per_contract > 0:
                max_contracts_by_risk = int(risk_amount / max_loss_per_contract)
            else:
                max_contracts_by_risk = self.max_contracts
            
            # Apply position limits
            contracts = min(max_contracts_by_risk, self.max_contracts)
            contracts = max(contracts, self.min_contracts)
            
            # Calculate total position metrics
            total_cost = contracts * contract_price
            max_loss = contracts * max_loss_per_contract
            max_profit = contracts * max_profit_per_contract
            
            # ROI calculations
            if total_cost > 0:
                roi_if_correct = (max_profit / total_cost) * 100
                risk_reward_ratio = max_profit / max_loss if max_loss > 0 else 0
            else:
                roi_if_correct = 0
                risk_reward_ratio = 0
            
            # Expected value based on confidence
            ev = (confidence * max_profit) - ((1 - confidence) * max_loss)
            ev_percentage = (ev / total_cost * 100) if total_cost > 0 else 0
            
            # Position size as percentage of bankroll
            position_percentage = (total_cost / self.bankroll) * 100
            
            return {
                "contracts": contracts,
                "contract_price": round(contract_price, 3),
                "total_cost": round(total_cost, 2),
                "max_loss": round(max_loss, 2),
                "max_profit": round(max_profit, 2),
                "roi_if_correct": round(roi_if_correct, 1),
                "risk_reward_ratio": round(risk_reward_ratio, 2),
                "expected_value": round(ev, 2),
                "ev_percentage": round(ev_percentage, 1),
                "position_percentage": round(position_percentage, 1),
                "risk_amount": round(risk_amount, 2),
                "bankroll": self.bankroll,
                "confidence": round(confidence * 100, 1)
            }
            
        except Exception as e:
            print(f"WARNING Error calculating position metrics: {e}")
            return {"error": str(e)}

    def analyze_market_opportunity(self, market_data: Dict[str, Any], phasma_prediction: Optional[float] = None) -> Dict[str, Any]:
        """Analyze a Kalshi market for trading opportunity with full AI analysis and cross-market opportunities.
        
        Args:
            market_data: Market data from get_market_implied_view
            phasma_prediction: Phasma's own probability prediction (0-1)
            
        Returns:
            Dict with analysis results and trading signal
        """
        # First, use the consistency engine for weather markets
        if self.consistency_engine:
            title = market_data.get('title', '').lower()
            if any(weather_word in title for weather_word in ['temperature', 'temp', 'rain', 'snow', 'weather', '°f', '°c']):
                consistency_result = self.consistency_engine.evaluate_trade_opportunity(market_data)
                
                if not consistency_result.get('trade', False):
                    # Consistency engine says don't trade
                    return {
                        'ticker': market_data.get('ticker', ''),
                        'signal': None,
                        'confidence': 0,
                        'rationale': f"Consistency filter: {consistency_result.get('reason', 'Unknown')}",
                        'action': None,
                        'position_size': 0,
                        'stability_score': consistency_result.get('stability', 0),
                        'agreement_score': consistency_result.get('agreement', 0),
                        'edge': consistency_result.get('edge', 0)
                    }
                
                # Use consistency engine's confidence if it's higher
                base_confidence = consistency_result.get('confidence', 0)
        
        implied_prob = market_data.get('implied_probability', 0.5)
        volume = market_data.get('volume', 0)
        ticker = market_data.get('ticker', '')
        days_to_expiry = market_data.get('days_to_expiry', 0)
        is_short_term = market_data.get('is_short_term', False)
        
        # KALSHI WEATHER-ONLY RESTRICTION
        if not self._is_weather_market(ticker):
            return {
                'ticker': ticker,
                'signal': None,
                'confidence': 0,
                'rationale': f"Non-weather market skipped: {ticker} (Kalshi restricted to weather only)",
                'action': None,
                'position_size': 0,
                'trade_link': self.get_market_trade_link(ticker),
                'market_type': 'non_weather'
            }
        
        implied_prob = market_data.get('implied_probability', 0.5)
        volume = market_data.get('volume', 0)
        ticker = market_data.get('ticker', '')
        days_to_expiry = market_data.get('days_to_expiry', 0)
        is_short_term = market_data.get('is_short_term', False)
        
        analysis = {
            'ticker': ticker,
            'market_probability': implied_prob,
            'volume': volume,
            'days_to_expiry': days_to_expiry,
            'is_short_term': is_short_term,
            'signal': None,
            'confidence': 0.0,
            'rationale': '',
            'action': None,
            'position_size': 0.0,
            'trade_link': self.get_market_trade_link(ticker),
            'market_assessment': {},
            'expiration_analysis': self._analyze_expiration_timing(days_to_expiry),
            'catalyst_score': 0.0,  # For unified analysis compatibility
            'sentiment': 0.5,  # Neutral sentiment for prediction markets
            'source': 'kalshi_prediction',
            'cross_market_signals': [],
            'market_impact_analysis': {},
            'traditional_asset_opportunities': []
        }
        
        # Skip low volume markets
        if volume < 10:
            analysis['rationale'] = f"Low volume ({volume}) - insufficient liquidity"
            return analysis
            
        # Skip expired markets
        if days_to_expiry <= 0:
            analysis['rationale'] = f"Market expired or unknown expiration ({days_to_expiry} days)"
            return analysis
            
        # Skip far-future political markets (too speculative)
        max_days_ahead = 90  # Maximum 90 days ahead for political bets
        if days_to_expiry > max_days_ahead and self._is_political_market(ticker):
            analysis['rationale'] = f"Political market too far in future ({days_to_expiry} days > {max_days_ahead}) - too speculative"
            return analysis
            
        # Allow extreme probabilities for long-term markets (different risk profile than options)
        # Only filter extreme probabilities for short-term markets
        if is_short_term and (implied_prob < 0.05 or implied_prob > 0.95):
            analysis['rationale'] = f"Extreme probability ({implied_prob:.1%}) too risky for short-term market"
            return analysis
        
        # For political markets, analyze candidate viability and compare with other candidates
        if self._is_political_market(ticker):
            candidate_viability = self._analyze_candidate_viability(ticker)
            analysis['candidate_viability'] = candidate_viability
            
            # Skip candidates with very low viability
            if candidate_viability < 0.20:
                analysis['rationale'] = f"Candidate has very low viability ({candidate_viability:.1%}) - likely trolling/nonsense"
                return analysis
            
            # For multi-choice markets, compare with other candidates
            if self._is_multi_choice_market(ticker):
                race_analysis = self._analyze_race_comparatively(ticker, market_data)
                if 'skip_reason' in race_analysis:
                    analysis['rationale'] = race_analysis['skip_reason']
                    analysis['race_analysis'] = race_analysis
                    return analysis
                analysis['race_analysis'] = race_analysis
        
        # Perform comprehensive market assessment
        market_assessment = self._assess_market_context(market_data)
        analysis['market_assessment'] = market_assessment
        
        # Adjust probability based on market context
        adjusted_probability = self._adjust_probability_for_context(implied_prob, market_assessment)
        
        # Determine Yes/No outcome direction
        is_yes_outcome = self._determine_yes_no_direction(market_data, market_assessment)
        
        # Calculate specialized POP for prediction markets
        pop_score = self._calculate_prediction_market_pop(implied_prob, volume, days_to_expiry, is_short_term)
        analysis['pop_from_sim'] = pop_score  # For unified analysis compatibility
        
        # NEW: Analyze for ANY cross-market opportunities (not just CEOs)
        market_impact = self._analyze_market_impact_on_traditional_assets(market_data, implied_prob)
        analysis['market_impact_analysis'] = market_impact
        
        if market_impact.get('has_traditional_asset_impact'):
            # Generate cross-market signals for traditional assets
            asset_signals = self._generate_traditional_asset_signals_from_market_impact(market_impact, days_to_expiry)
            analysis['traditional_asset_opportunities'] = asset_signals
            analysis['cross_market_signals'].extend(asset_signals)
            
            # Boost confidence for market-impact-driven signals
            impact_strength = market_impact.get('impact_strength', 0.5)
            analysis['confidence'] = min(analysis.get('confidence', 0) * (1 + impact_strength), 0.95)
        
        # CEO analysis (keep this as a special case since it has detailed track records)
        ceo_analysis = self._analyze_ceo_appointment_opportunity(market_data, implied_prob)
        analysis['ceo_impact_analysis'] = ceo_analysis
        
        if ceo_analysis.get('is_ceo_market') and ceo_analysis.get('high_probability_ceo'):
            # Generate cross-market signals for company stock
            company_signals = self._generate_company_stock_signals_from_ceo(ceo_analysis, days_to_expiry)
            analysis['company_stock_opportunities'] = company_signals
            analysis['cross_market_signals'].extend(company_signals)
            
            # Boost confidence for CEO-driven signals
            ceo_boost = 1.3 if ceo_analysis.get('ceo_track_record', {}).get('positive', False) else 1.0
        else:
            ceo_boost = 1.0
        
        # WEATHER ANALYSIS - Look for "quick money" weather trades
        # Weather markets are highly predictable based on seasonal patterns
        weather_analysis = self._analyze_weather_market_opportunity(market_data, implied_prob)
        analysis['weather_analysis'] = weather_analysis
        
        if weather_analysis.get('is_weather_market') and weather_analysis.get('quick_money_potential'):
            # Boost confidence for weather markets with strong seasonal edges
            weather_boost = weather_analysis.get('confidence_boost', 1.0)
            analysis['confidence'] = min(analysis.get('confidence', 0) * weather_boost, 0.95)
            
            # Add weather rationale to main rationale
            if analysis.get('rationale'):
                analysis['rationale'] += f" | WEATHER: {weather_analysis.get('rationale', '')}"
            else:
                analysis['rationale'] = f"WEATHER EDGE: {weather_analysis.get('rationale', '')}"
        
        # MACRO CALENDAR ANALYSIS - Look for economic data easy trades
        # CPI, NFP, Fed decisions with systematic forecast errors
        macro_analysis = self._analyze_macro_calendar_opportunity(market_data, implied_prob)
        analysis['macro_calendar_analysis'] = macro_analysis
        
        if macro_analysis.get('is_macro_event') and macro_analysis.get('easy_trade_potential'):
            # Boost confidence for macro events with strong edges
            macro_boost = macro_analysis.get('confidence_boost', 1.0)
            analysis['confidence'] = min(analysis.get('confidence', 0) * macro_boost, 0.95)
            
            # Add macro rationale to main rationale
            if analysis.get('rationale'):
                analysis['rationale'] += f" | MACRO: {macro_analysis.get('rationale', '')}"
            else:
                analysis['rationale'] = f"MACRO EDGE: {macro_analysis.get('rationale', '')}"
        
        # EARNINGS DRIFT ANALYSIS - Look for post-earnings reaction patterns
        # Beat/miss patterns and guidance impacts
        earnings_analysis = self._analyze_earnings_drift_opportunity(market_data, implied_prob)
        analysis['earnings_drift_analysis'] = earnings_analysis
        
        if earnings_analysis.get('is_earnings_market') and earnings_analysis.get('easy_trade_potential'):
            # Boost confidence for earnings markets with drift potential
            earnings_boost = earnings_analysis.get('confidence_boost', 1.0)
            analysis['confidence'] = min(analysis.get('confidence', 0) * earnings_boost, 0.95)
            
            # Add earnings rationale to main rationale
            if analysis.get('rationale'):
                analysis['rationale'] += f" | EARNINGS: {earnings_analysis.get('rationale', '')}"
            else:
                analysis['rationale'] = f"EARNINGS EDGE: {earnings_analysis.get('rationale', '')}"
        
        # CALENDAR SEASONALITY ANALYSIS - Look for holiday/tax/quarter-end patterns
        # Christmas rally, tax selling, window dressing
        calendar_analysis = self._analyze_calendar_seasonality_opportunity(market_data, implied_prob)
        analysis['calendar_seasonality_analysis'] = calendar_analysis
        
        if calendar_analysis.get('is_seasonal_event') and calendar_analysis.get('easy_trade_potential'):
            # Boost confidence for seasonal patterns
            calendar_boost = calendar_analysis.get('confidence_boost', 1.0)
            analysis['confidence'] = min(analysis.get('confidence', 0) * calendar_boost, 0.95)
            
            # Add calendar rationale to main rationale
            if analysis.get('rationale'):
                analysis['rationale'] += f" | SEASONAL: {calendar_analysis.get('rationale', '')}"
            else:
                analysis['rationale'] = f"SEASONAL EDGE: {calendar_analysis.get('rationale', '')}"
        
        # SPORTS ANALYSIS - Look for player prop and game outcome edges
        # Statistical anomalies in sports markets
        sports_analysis = self._analyze_sports_opportunity(market_data, implied_prob)
        analysis['sports_analysis'] = sports_analysis
        
        if sports_analysis.get('is_sports_market') and sports_analysis.get('easy_trade_potential'):
            # Boost confidence for sports markets with statistical edges
            sports_boost = sports_analysis.get('confidence_boost', 1.0)
            analysis['confidence'] = min(analysis.get('confidence', 0) * sports_boost, 0.95)
            
            # Add sports rationale to main rationale
            if analysis.get('rationale'):
                analysis['rationale'] += f" | SPORTS: {sports_analysis.get('rationale', '')}"
            else:
                analysis['rationale'] = f"SPORTS EDGE: {sports_analysis.get('rationale', '')}"
        
        # EVENT STRUCTURE ANALYSIS - Look for contract wording arbitrage
        # Settlement rules, payoff asymmetry, impossible outcomes
        structure_analysis = self._analyze_event_structure_opportunity(market_data, implied_prob)
        analysis['event_structure_analysis'] = structure_analysis
        
        if structure_analysis.get('is_contract_market') and structure_analysis.get('easy_trade_potential'):
            # Boost confidence for structural arbitrage opportunities
            structure_boost = structure_analysis.get('confidence_boost', 1.0)
            analysis['confidence'] = min(analysis.get('confidence', 0) * structure_boost, 0.95)
            
            # Add structure rationale to main rationale
            if analysis.get('rationale'):
                analysis['rationale'] += f" | STRUCTURE: {structure_analysis.get('rationale', '')}"
            else:
                analysis['rationale'] = f"STRUCTURAL EDGE: {structure_analysis.get('rationale', '')}"
        
        # RANGE BARRIER ANALYSIS - Look for volatility regime edges
        # Low-vol assets staying in ranges, high-vol hitting barriers
        range_barrier_analysis = self._analyze_range_barrier_opportunity(market_data, implied_prob)
        analysis['range_barrier_analysis'] = range_barrier_analysis
        
        if range_barrier_analysis.get('is_barrier_market') and range_barrier_analysis.get('easy_trade_potential'):
            # Boost confidence for volatility-based edges
            barrier_boost = range_barrier_analysis.get('confidence_boost', 1.0)
            analysis['confidence'] = min(analysis.get('confidence', 0) * barrier_boost, 0.95)
            
            # Add barrier rationale to main rationale
            if analysis.get('rationale'):
                analysis['rationale'] += f" | VOLATILITY: {range_barrier_analysis.get('rationale', '')}"
            else:
                analysis['rationale'] = f"VOLATILITY EDGE: {range_barrier_analysis.get('rationale', '')}"
        
        # MICROSTRUCTURE ANALYSIS - Look for order flow anomalies
        # Volume spikes, price impacts, short-term reversions
        microstructure_analysis = self._analyze_microstructure_opportunity(market_data, implied_prob)
        analysis['microstructure_analysis'] = microstructure_analysis
        
        if microstructure_analysis.get('is_microstructure_market') and microstructure_analysis.get('easy_trade_potential'):
            # Boost confidence for microstructure edges
            micro_boost = microstructure_analysis.get('confidence_boost', 1.0)
            analysis['confidence'] = min(analysis.get('confidence', 0) * micro_boost, 0.95)
            
            # Add microstructure rationale to main rationale
            if analysis.get('rationale'):
                analysis['rationale'] += f" | MICRO: {microstructure_analysis.get('rationale', '')}"
            else:
                analysis['rationale'] = f"MICRO EDGE: {microstructure_analysis.get('rationale', '')}"
        
        # CORPORATE ACTIONS ANALYSIS - Look for stock splits, buybacks, dividends
        # Predictable reaction patterns in corporate events
        corporate_analysis = self._analyze_corporate_actions_opportunity(market_data, implied_prob)
        analysis['corporate_actions_analysis'] = corporate_analysis
        
        if corporate_analysis.get('is_corporate_action') and corporate_analysis.get('easy_trade_potential'):
            # Boost confidence for corporate action reaction patterns
            corporate_boost = corporate_analysis.get('confidence_boost', 1.0)
            analysis['confidence'] = min(analysis.get('confidence', 0) * corporate_boost, 0.95)
            
            # Add corporate rationale to main rationale
            if analysis.get('rationale'):
                analysis['rationale'] += f" | CORPORATE: {corporate_analysis.get('rationale', '')}"
            else:
                analysis['rationale'] = f"CORPORATE EDGE: {corporate_analysis.get('rationale', '')}"
        
        # Short-term market bonus (1-2 weeks = "easy wins") - but be realistic about available markets
        short_term_bonus = 1.5 if is_short_term else 1.0
        # Long-term markets get smaller position sizing due to time decay and uncertainty
        time_decay_multiplier = max(0.3, min(1.0, 90 / days_to_expiry))  # Smaller positions for very long-term
        timing_multiplier = market_assessment.get('timing_multiplier', 1.0)
        
        # If we have Phasma's prediction, compare with market
        if phasma_prediction is not None:
            prob_diff = phasma_prediction - adjusted_probability
            
            # Significant edge detected (lower threshold for short-term markets)
            edge_threshold = 0.04 if is_short_term else 0.03  # Lower threshold for long-term
            if abs(prob_diff) > edge_threshold:
                if prob_diff > 0:  # Phasma more bullish than market
                    analysis['signal'] = 'BUY_YES' if is_yes_outcome else 'BUY_NO'
                    analysis['action'] = 'BUY_CALL'  # Equivalent in options terms
                    # ENHANCED: More appropriate confidence for prediction markets
                    # A 5% probability edge in prediction markets is actually quite valuable
                    base_confidence = 0.25  # Start with 25% base confidence for any edge
                    edge_confidence = abs(prob_diff) * 4.0  # 4x multiplier for probability edges
                    analysis['confidence'] = min(base_confidence + edge_confidence * short_term_bonus * ceo_boost, 0.90)  # Higher confidence for short-term
                    analysis['rationale'] = f"Phasma edge: predicts {phasma_prediction:.1%} vs market {adjusted_probability:.1%} - {days_to_expiry} days left"
                else:  # Market more bullish than Phasma
                    analysis['signal'] = 'BUY_NO' if is_yes_outcome else 'BUY_YES'
                    analysis['action'] = 'BUY_PUT'  # Equivalent in options terms
                    # ENHANCED: Apply same confidence formula to both sides
                    base_confidence = 0.25  # Start with 25% base confidence for any edge
                    edge_confidence = abs(prob_diff) * 4.0  # 4x multiplier for probability edges
                    analysis['confidence'] = min(base_confidence + edge_confidence * short_term_bonus * ceo_boost, 0.90)
                    analysis['rationale'] = f"Market overvalues at {adjusted_probability:.1%}, Phasma sees {phasma_prediction:.1%} - {days_to_expiry} days left"
                    
                # Enhanced position sizing for prediction markets
                base_size = 150 if is_short_term else 80  # Smaller base for long-term prediction markets
                volume_multiplier = min(volume / 5000, 3)  # Moderate volume bonus for prediction markets
                edge_multiplier = abs(prob_diff) * 2.2  # Moderate edge multiplier
                analysis['position_size'] = base_size * volume_multiplier * edge_multiplier * timing_multiplier * time_decay_multiplier * short_term_bonus
                
            else:
                analysis['rationale'] = f"No significant edge: Phasma {phasma_prediction:.1%} vs market {adjusted_probability:.1%} - {days_to_expiry} days to expiry"
        else:
            # No Phasma prediction - use market context and momentum signals with expiration awareness
            analysis_result = self._analyze_market_momentum_with_expiration(market_data, market_assessment, adjusted_probability, days_to_expiry, is_short_term)
            if analysis_result['signal']:
                analysis.update(analysis_result)
                # Apply time-based adjustments
                if days_to_expiry > 365:  # Very long-term markets
                    analysis['confidence'] = min(analysis['confidence'] * 0.7, 0.6)  # Reduce confidence for very long-term
                    analysis['position_size'] = analysis['position_size'] * 0.5  # Smaller positions for long-term uncertainty
                    analysis['rationale'] += f" - LONG-TERM MARKET ({days_to_expiry} days)"
            else:
                # Set minimum confidence for markets with decent probability
                if implied_prob > 0.60:
                    analysis['confidence'] = 0.3  # Minimum confidence for high-probability markets
                    analysis['signal'] = 'BUY_YES'
                    analysis['action'] = 'BUY_CALL'
                    analysis['rationale'] = f"High probability market ({implied_prob:.1%}) with volume {volume:,}"
                elif implied_prob < 0.40:
                    analysis['confidence'] = 0.3  # Minimum confidence for low-probability markets
                    analysis['signal'] = 'BUY_NO'
                    analysis['action'] = 'BUY_PUT'
                    analysis['rationale'] = f"Low probability market ({implied_prob:.1%}) with volume {volume:,}"
                # Apply short-term bonus to momentum signals too
                elif is_short_term:
                    analysis['confidence'] = min(analysis['confidence'] * 1.3, 0.85)
                    analysis['position_size'] = analysis['position_size'] * 1.4
                    analysis['rationale'] += f" - SHORT-TERM BONUS ({days_to_expiry} days)"
                
        # Set catalyst score for unified analysis compatibility (lower for prediction markets)
        analysis['catalyst_score'] = analysis.get('confidence', 0) * 0.6
        
        # Add pattern strength for unified analysis compatibility
        if phasma_prediction is not None and 'signal' in analysis:
            edge = abs(phasma_prediction - adjusted_probability)
            analysis['pattern_strength'] = max(0.2, min(0.9, 0.2 + edge))
        else:
            analysis['pattern_strength'] = 0.0
        
        return analysis

    def _calculate_days_to_expiry(self, expiration_date) -> int:
        """Calculate days until market expiration.
        
        Args:
            expiration_date: Expiration date (string or datetime)
            
        Returns:
            Number of days until expiration (0 if expired or unknown)
        """
        print(f"SCANNING DEBUG _calculate_days_to_expiry: Input = '{expiration_date}' (type: {type(expiration_date)})")
        
        if not expiration_date:
            print("SCANNING DEBUG: expiration_date is None/empty, returning 0")
            return 0
            
        try:
            from datetime import datetime, timezone
            from engines.weather_consistency_engine_new import WeatherConsistencyEngine
            
            # Handle different date formats
            if isinstance(expiration_date, str):
                # Try common date formats (FIXED: Added microseconds format)
                for fmt in ['%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%dT%H:%M:%S.%fZ']:
                    try:
                        print(f"SCANNING DEBUG: Trying format '{fmt}' on '{expiration_date}'")
                        exp_dt = datetime.strptime(expiration_date, fmt)
                        print(f"SCANNING DEBUG: Successfully parsed with format '{fmt}', exp_dt = {exp_dt}")
                        break
                    except ValueError as e:
                        print(f"SCANNING DEBUG: Format '{fmt}' failed: {e}")
                        continue
                else:
                    print("SCANNING DEBUG: All formats failed, returning 0")
                    return 0  # Couldn't parse date
            else:
                exp_dt = expiration_date
                print(f"SCANNING DEBUG: Using datetime object directly: {exp_dt}")
                
            # Calculate days difference
            now = datetime.now()
            days_diff = (exp_dt - now).days
            
            return max(0, days_diff)  # Don't return negative days
            
        except Exception:
            return 0

    def _analyze_expiration_timing(self, days_to_expiry: int) -> Dict[str, Any]:
        """Analyze expiration timing for position management and risk assessment.
        
        Args:
            days_to_expiry: Days until market expires
            
        Returns:
            Dict with expiration analysis
        """
        analysis = {
            'days_to_expiry': days_to_expiry,
            'urgency_level': 'low',
            'time_decay_risk': 'low',
            'early_exit_premium': 1.0,
            'position_hold_strategy': 'hold_to_expiry'
        }
        
        if days_to_expiry <= 1:
            analysis.update({
                'urgency_level': 'critical',
                'time_decay_risk': 'extreme',
                'early_exit_premium': 2.0,
                'position_hold_strategy': 'monitor_closely'
            })
        elif days_to_expiry <= 3:
            analysis.update({
                'urgency_level': 'high',
                'time_decay_risk': 'high',
                'early_exit_premium': 1.8,
                'position_hold_strategy': 'consider_early_exit'
            })
        elif days_to_expiry <= 7:
            analysis.update({
                'urgency_level': 'medium',
                'time_decay_risk': 'medium',
                'early_exit_premium': 1.4,
                'position_hold_strategy': 'hold_with_monitoring'
            })
        elif days_to_expiry <= 14:
            analysis.update({
                'urgency_level': 'low',
                'time_decay_risk': 'low',
                'early_exit_premium': 1.2,
                'position_hold_strategy': 'hold_comfortably'
            })
        else:
            analysis.update({
                'urgency_level': 'very_low',
                'time_decay_risk': 'minimal',
                'early_exit_premium': 1.0,
                'position_hold_strategy': 'long_term_hold'
            })
            
        return analysis

    def _calculate_prediction_market_pop(self, probability: float, volume: int, days_to_expiry: int, is_short_term: bool) -> float:
        """Calculate specialized Probability of Profit for prediction markets.
        
        For YES bets: higher probability = higher POP
        For NO bets: lower probability = higher POP
        """
        # Base POP is the probability itself (for YES bets) or complement (for NO bets)
        # We'll assume YES bets for now, so higher probability = higher chance of winning
        base_pop = probability
        
        # Volume adjustment (higher volume = more reliable, up to 30% bonus)
        volume_bonus = min(volume / 5000, 0.3)
        
        # Short-term bonus (easier to predict)
        short_term_bonus = 0.20 if is_short_term else 0.0
        
        # Expiration timing factor (closer to expiry = higher certainty)
        if days_to_expiry <= 7:
            timing_factor = 0.15
        elif days_to_expiry <= 14:
            timing_factor = 0.10
        elif days_to_expiry <= 30:
            timing_factor = 0.05
        else:
            timing_factor = 0.0
            
        # Add bonuses but don't exceed 95%
        pop_score = base_pop + volume_bonus + short_term_bonus + timing_factor
        return max(0.25, min(0.95, pop_score))  # Clamp between 25% and 95%

    def _analyze_market_momentum_with_expiration(self, market_data: Dict[str, Any], assessment: Dict[str, Any], adjusted_probability: float, days_to_expiry: int, is_short_term: bool) -> Dict[str, Any]:
        """Analyze market momentum for mean reversion or momentum opportunities with expiration awareness."""
        implied_prob = market_data.get('implied_probability', 0.5)
        volume = market_data.get('volume', 0)
        
        result = {
            'signal': None,
            'confidence': 0.0,
            'rationale': '',
            'action': None,
            'position_size': 0.0
        }
        
        efficiency = assessment.get('market_efficiency', 'moderately_efficient')
        timing_multiplier = assessment.get('timing_multiplier', 1.0)
        
        # Enhanced short-term focus for "easy wins"
        if is_short_term:
            # Lower thresholds for short-term markets - more opportunities
            if implied_prob < 0.30:
                # Very low probability in short-term market - potential long opportunity
                result['signal'] = 'BUY_YES'
                result['action'] = 'BUY_CALL'
                result['confidence'] = (0.5 - implied_prob) * 1.4 * timing_multiplier
                result['position_size'] = 100 * (0.5 - implied_prob) * 3 * timing_multiplier
                result['rationale'] = f"SHORT-TERM OPPORTUNITY: Low probability ({implied_prob:.1%}) in {days_to_expiry}-day market - easy win potential"
            elif implied_prob > 0.70:
                # Very high probability in short-term market - potential short opportunity
                result['signal'] = 'BUY_NO'
                result['action'] = 'BUY_PUT'
                result['confidence'] = (implied_prob - 0.5) * 1.4 * timing_multiplier
                result['position_size'] = 100 * (implied_prob - 0.5) * 3 * timing_multiplier
                result['rationale'] = f"SHORT-TERM OPPORTUNITY: High probability ({implied_prob:.1%}) in {days_to_expiry}-day market - mean reversion play"
        else:
            # Standard analysis for longer-term markets
            # Mean reversion opportunities in inefficient markets
            if efficiency == 'extreme_probability':
                if implied_prob < 0.25:
                    result['signal'] = 'BUY_YES'
                    result['action'] = 'BUY_CALL'
                    result['confidence'] = (0.5 - implied_prob) * 1.2 * timing_multiplier
                    result['position_size'] = 75 * (0.5 - implied_prob) * 2 * timing_multiplier
                    result['rationale'] = f"Extreme low probability ({implied_prob:.1%}) - mean reversion opportunity with {assessment['timing_assessment']}"
                elif implied_prob > 0.75:
                    result['signal'] = 'BUY_NO'
                    result['action'] = 'BUY_PUT'
                    result['confidence'] = (implied_prob - 0.5) * 1.2 * timing_multiplier
                    result['position_size'] = 75 * (implied_prob - 0.5) * 2 * timing_multiplier
                    result['rationale'] = f"Extreme high probability ({implied_prob:.1%}) - mean reversion opportunity with {assessment['timing_assessment']}"
                    
        # Look for momentum in efficient, liquid markets (only for longer-term)
        if not is_short_term and efficiency == 'efficient_market' and volume > 5000:
            if implied_prob > 0.6 and timing_multiplier > 1.2:
                # Strong momentum in high-stakes timing
                result['signal'] = 'BUY_YES'
                result['action'] = 'BUY_CALL'
                result['confidence'] = (implied_prob - 0.5) * 1.1
                result['position_size'] = 50 * (implied_prob - 0.5) * timing_multiplier
                result['rationale'] = f"Strong momentum ({implied_prob:.1%}) in {assessment['timing_assessment']}"
            elif implied_prob < 0.4 and timing_multiplier > 1.2:
                # Weak momentum in high-stakes timing
                result['signal'] = 'BUY_NO'
                result['action'] = 'BUY_PUT'
                result['confidence'] = (0.5 - implied_prob) * 1.1
                result['position_size'] = 50 * (0.5 - implied_prob) * timing_multiplier
                result['rationale'] = f"Weak momentum ({implied_prob:.1%}) in {assessment['timing_assessment']}"
        elif not result['signal']:
            # No signal found
            if is_short_term:
                result['rationale'] = f"Short-term market ({days_to_expiry} days) probability ({implied_prob:.1%}) in neutral range - waiting for better setup"
            else:
                result['rationale'] = f"Market probability ({implied_prob:.1%}) in neutral range - {assessment['context_assessment']}"
                
        return result
                
    def _analyze_ceo_appointment_opportunity(self, market_data: Dict[str, Any], implied_prob: float) -> Dict[str, Any]:
        """Analyze if this is a CEO appointment market and identify high-probability candidates.
        
        Args:
            market_data: Market data from get_market_implied_view
            implied_prob: Current market-implied probability
            
        Returns:
            Dict with CEO analysis results
        """
        title = market_data.get('title', '').upper()
        ticker = market_data.get('ticker', '').upper()
        
        analysis = {
            'is_ceo_market': False,
            'company_ticker': None,
            'high_probability_ceo': None,
            'ceo_candidates': [],
            'ceo_track_record': {},
            'market_impact_potential': 'unknown'
        }
        
        # Check if this is a CEO appointment market
        ceo_keywords = ['CEO', 'CHIEF EXECUTIVE', 'EXECUTIVE', 'LEADER', 'SUCCESSOR', 'APPOINTMENT']
        is_ceo_market = any(keyword in title for keyword in ceo_keywords)
        
        if not is_ceo_market:
            return analysis
            
        analysis['is_ceo_market'] = True
        
        # Extract company ticker from market title/ticker
        # Look for company patterns in the title
        title_words = title.split()
        potential_tickers = []
        
        for word in title_words:
            # Look for words that might be company tickers (2-5 characters, all caps)
            if 2 <= len(word) <= 5 and word.isalpha() and word.isupper():
                potential_tickers.append(word)
        
        # Enhanced company mapping with more companies
        known_companies = {
            'AAPL': 'Apple Inc.',
            'MSFT': 'Microsoft Corporation', 
            'GOOGL': 'Alphabet Inc.',
            'AMZN': 'Amazon.com Inc.',
            'TSLA': 'Tesla Inc.',
            'NVDA': 'NVIDIA Corporation',
            'META': 'Meta Platforms Inc.',
            'NFLX': 'Netflix Inc.',
            'DIS': 'Walt Disney Company',
            'UBER': 'Uber Technologies Inc.',
            'LYFT': 'Lyft Inc.',
            'SPOT': 'Spotify Technology S.A.',
            'ZOOM': 'Zoom Video Communications Inc.',
            'SHOP': 'Shopify Inc.',
            'SQ': 'Block Inc.',
            'PYPL': 'PayPal Holdings Inc.',
            'COIN': 'Coinbase Global Inc.',
            'MSTR': 'MicroStrategy Incorporated',
            'RIOT': 'Riot Blockchain Inc.',
            'MARA': 'Marathon Digital Holdings Inc.',
            'CRM': 'Salesforce Inc.',
            'ORCL': 'Oracle Corporation',
            'INTC': 'Intel Corporation',
            'AMD': 'Advanced Micro Devices Inc.',
            'QCOM': 'Qualcomm Incorporated',
            'TXN': 'Texas Instruments Incorporated'
        }
        
        # First try exact matches
        for ticker_candidate in potential_tickers:
            if ticker_candidate in known_companies:
                analysis['company_ticker'] = ticker_candidate
                break
        
        # If no exact match, try to infer from company names in title
        if not analysis['company_ticker']:
            company_name_map = {v.lower(): k for k, v in known_companies.items()}
            title_lower = title.lower()
            
            for company_name, ticker in company_name_map.items():
                # Look for company name mentions
                company_words = company_name.split()
                if len(company_words) > 1:
                    # Multi-word company name
                    if all(word in title_lower for word in company_words[:2]):  # Check first 2 words
                        analysis['company_ticker'] = ticker
                        break
                else:
                    # Single word company name - check exact match
                    if company_words[0] in title_lower:
                        analysis['company_ticker'] = ticker
                        break
            
            # Special handling for common company names that might not be in full form
            special_companies = {
                'apple': 'AAPL',
                'microsoft': 'MSFT', 
                'google': 'GOOGL',
                'amazon': 'AMZN',
                'tesla': 'TSLA',
                'nvidia': 'NVDA',
                'meta': 'META',
                'netflix': 'NFLX'
            }
            
            if not analysis['company_ticker']:
                for company_word, ticker in special_companies.items():
                    if company_word in title_lower:
                        analysis['company_ticker'] = ticker
                        break
        
        # Analyze CEO candidates from market title
        # Look for names in the title
        ceo_candidates = self._extract_ceo_candidates_from_title(title)
        analysis['ceo_candidates'] = ceo_candidates
        
        # Find high probability CEO (prioritize known CEOs with high confidence)
        if implied_prob > 0.60:
            # Sort candidates by confidence (highest first)
            sorted_candidates = sorted(ceo_candidates, key=lambda x: x.get('confidence', 0), reverse=True)
            
            # Pick the highest confidence candidate
            if sorted_candidates:
                analysis['high_probability_ceo'] = sorted_candidates[0]
        
        # Analyze CEO track record if we have a high-probability candidate
        if analysis['high_probability_ceo']:
            ceo_name = analysis['high_probability_ceo'].get('name', '')
            track_record = self._analyze_ceo_track_record(ceo_name, analysis.get('company_ticker'))
            analysis['ceo_track_record'] = track_record
            
            # Assess market impact potential
            if track_record.get('positive', False):
                analysis['market_impact_potential'] = 'high_positive'
            elif track_record.get('mixed', False):
                analysis['market_impact_potential'] = 'moderate'
            else:
                analysis['market_impact_potential'] = 'uncertain'
        
        return analysis
    
    def _extract_ceo_candidates_from_title(self, title: str) -> List[Dict[str, Any]]:
        """Extract potential CEO candidate names from market title.
        
        Args:
            title: Market title string
            
        Returns:
            List of candidate dictionaries with name and context
        """
        candidates = []
        
        # Common CEO name patterns
        title_lower = title.lower()
        
        # Look for "vs" or "versus" patterns (indicating multiple candidates)
        if ' vs ' in title_lower or ' versus ' in title_lower:
            # Split on vs/versus and extract names
            parts = title_lower.replace(' versus ', ' vs ').split(' vs ')
            
            for part in parts:
                # Extract potential names (look for capitalized words that could be names)
                words = part.strip().split()
                for i in range(len(words)-1):
                    # Look for patterns like "First Last" where both words are capitalized
                    if words[i][0].isupper() and words[i+1][0].isupper():
                        potential_name = ' '.join(words[i:i+2]).title()
                        if len(potential_name.split()) >= 2 and len(potential_name) > 4:
                            candidates.append({
                                'name': potential_name,
                                'context': part.strip(),
                                'confidence': 0.8
                            })
        
        # Look for specific CEO appointment patterns
        elif any(keyword in title_lower for keyword in ['appointed', 'named', 'selected', 'chosen', 'reappointed', 'remain']):
            # Try to extract the name after appointment keywords
            appointment_keywords = ['appointed as', 'named as', 'selected as', 'chosen as', 'reappointed as', 'remain as']
            for keyword in appointment_keywords:
                if keyword in title_lower:
                    idx = title_lower.find(keyword)
                    remaining = title[idx + len(keyword):].strip()
                    # Take first 2-3 words as potential name
                    words = remaining.split()[:3]
                    potential_name = ' '.join(words).title()
                    if potential_name and len(potential_name) > 4:
                        candidates.append({
                            'name': potential_name,
                            'context': remaining,
                            'confidence': 0.9
                        })
                        break
        
        # Look for "Will [Name] be" patterns (very common in prediction markets)
        elif 'will' in title_lower and 'be' in title_lower:
            will_idx = title_lower.find('will')
            be_idx = title_lower.find('be', will_idx)
            if will_idx >= 0 and be_idx > will_idx:
                between_will_be = title[will_idx + 4:be_idx].strip()
                # Extract potential name (usually 2 words)
                words = between_will_be.split()
                if len(words) >= 2:
                    potential_name = ' '.join(words[:2]).title()
                    if potential_name and len(potential_name) > 4:
                        candidates.append({
                            'name': potential_name,
                            'context': between_will_be,
                            'confidence': 0.85
                        })
        
        # Look for CEO name patterns in the title
        # Common CEO names that appear in markets
        known_ceos = ['Tim Cook', 'Satya Nadella', 'Sundar Pichai', 'Andy Jassy', 'Elon Musk', 
                     'Jensen Huang', 'Lisa Su', 'Mark Zuckerberg', 'Jeff Bezos', 'Warren Buffett']
        
        for ceo_name in known_ceos:
            if ceo_name.lower() in title_lower:
                candidates.append({
                    'name': ceo_name,
                    'context': title,
                    'confidence': 0.95  # High confidence for known CEOs
                })
        
        return candidates
    
    def _analyze_ceo_track_record(self, ceo_name: str, company_ticker: str = None) -> Dict[str, Any]:
        """Analyze a CEO candidate's track record and potential market impact.
        
        Args:
            ceo_name: Name of the CEO candidate
            company_ticker: Company ticker if known
            
        Returns:
            Dict with track record analysis
        """
        track_record = {
            'positive': False,
            'mixed': False,
            'negative': False,
            'experience_years': 0,
            'previous_companies': [],
            'stock_performance': {},
            'reputation_score': 0.5
        }
        
        if not ceo_name:
            return track_record
        
        # Simplified CEO database - in production this would be a comprehensive database
        ceo_database = {
            'Tim Cook': {
                'experience_years': 15,
                'previous_companies': ['Apple'],
                'performance': 'excellent',
                'reputation': 0.95
            },
            'Satya Nadella': {
                'experience_years': 25,
                'previous_companies': ['Microsoft'],
                'performance': 'excellent',
                'reputation': 0.92
            },
            'Sundar Pichai': {
                'experience_years': 20,
                'previous_companies': ['Google', 'Alphabet'],
                'performance': 'excellent',
                'reputation': 0.90
            },
            'Andy Jassy': {
                'experience_years': 20,
                'previous_companies': ['Amazon'],
                'performance': 'strong',
                'reputation': 0.85
            },
            'Elon Musk': {
                'experience_years': 15,
                'previous_companies': ['Tesla', 'SpaceX', 'Neuralink'],
                'performance': 'volatile',
                'reputation': 0.75
            }
        }
        
        # Look up CEO in database
        ceo_key = ceo_name.strip().title()
        if ceo_key in ceo_database:
            ceo_info = ceo_database[ceo_key]
            
            track_record.update({
                'experience_years': ceo_info['experience_years'],
                'previous_companies': ceo_info['previous_companies']
            })
            
            # Assess performance
            performance = ceo_info.get('performance', 'unknown')
            if performance == 'excellent':
                track_record['positive'] = True
                track_record['reputation_score'] = ceo_info.get('reputation', 0.8)
            elif performance == 'strong':
                track_record['positive'] = True
                track_record['reputation_score'] = ceo_info.get('reputation', 0.75)
            elif performance == 'volatile':
                track_record['mixed'] = True
                track_record['reputation_score'] = ceo_info.get('reputation', 0.6)
            else:
                track_record['mixed'] = True
                track_record['reputation_score'] = 0.5
        else:
            # Unknown CEO - conservative assessment
            track_record['mixed'] = True
            track_record['reputation_score'] = 0.5
        
        return track_record
    
    def _generate_company_stock_signals_from_ceo(self, ceo_analysis: Dict[str, Any], days_to_expiry: int) -> List[Dict[str, Any]]:
        """Generate stock trading signals based on CEO appointment analysis.
        
        Args:
            ceo_analysis: Results from CEO analysis
            days_to_expiry: Days until CEO market expires
            
        Returns:
            List of stock trading signals
        """
        signals = []
        
        company_ticker = ceo_analysis.get('company_ticker')
        ceo_track_record = ceo_analysis.get('ceo_track_record', {})
        market_impact = ceo_analysis.get('market_impact_potential', 'unknown')
        
        if not company_ticker:
            return signals
        
        # Only generate signals for positive CEO track records
        if not ceo_track_record.get('positive', False):
            return signals
        
        # Calculate expected impact timeframe
        # CEO appointment typically takes 30-90 days to show in stock price
        impact_timeframe = min(days_to_expiry + 60, 90)  # Impact within 60-90 days
        
        # Generate buy signal for company stock
        confidence = ceo_track_record.get('reputation_score', 0.7) * 0.8  # Slightly lower for stock impact
        
        stock_signal = {
            'symbol': company_ticker,
            'action': 'BUY_CALL',
            'confidence': confidence,
            'position_size': 1000,  # Standard stock position
            'rationale': f"CEO APPOINTMENT IMPACT: Positive CEO candidate with strong track record - expected stock impact in {impact_timeframe} days",
            'source': 'kalshi_ceo_cross_market',
            'days_to_expiry': impact_timeframe,
            'catalyst_type': 'CEO_Appointment',
            'ceo_analysis': ceo_analysis,
            'pop_from_sim': confidence,  # Use confidence as POP
            'catalyst_score': confidence * 0.9
        }
        
        signals.append(stock_signal)
        
        # If very high confidence CEO, also generate options signal
        if confidence > 0.8:
            options_signal = stock_signal.copy()
            options_signal.update({
                'action': 'BUY_CALL',
                'position_size': 500,  # Smaller options position
                'rationale': f"CEO APPOINTMENT: High-confidence CEO appointment - options play on stock surge",
                'days_to_expiry': min(impact_timeframe, 45)  # Shorter options expiry
            })
            signals.append(options_signal)
        
        return signals

    def _analyze_geopolitical_market_opportunity(self, market_data: Dict[str, Any], implied_prob: float) -> Dict[str, Any]:
        """Analyze geopolitical Kalshi markets for "easy trades" based on historical patterns.
        
        Focuses on countries that have avoided peace treaties and have high bombing history,
        making certain outcomes more predictable.
        
        Args:
            market_data: Market data from get_market_implied_view
            implied_prob: Current market-implied probability
            
        Returns:
            Dict with geopolitical analysis results
        """
        title = market_data.get('title', '').upper()
        
        analysis = {
            'is_geopolitical_market': False,
            'countries_involved': [],
            'event_type': 'unknown',
            'easy_trade_potential': False,
            'confidence_boost': 1.0,
            'rationale': '',
            'historical_patterns': [],
            'risk_assessment': 'unknown'
        }
        
        # Check if this is a geopolitical market
        geopolitical_keywords = [
            'BOMB', 'ATTACK', 'STRIKE', 'MISSILE', 'WAR', 'INVASION', 'OCCUPY',
            'PEACE', 'TREATY', 'AGREEMENT', 'VIOLATION', 'SANCTION', 'EMBARGO',
            'TERRORIST', 'CONFLICT', 'BATTLE', 'OIL', 'GAZA', 'UKRAINE', 'SYRIA'
        ]
        
        is_geopolitical = any(keyword in title for keyword in geopolitical_keywords)
        
        if not is_geopolitical:
            return analysis
            
        analysis['is_geopolitical_market'] = True
        
        # Initialize geopolitical engine if available
        try:
            from engines.geopolitical_engine import GeopoliticalAnalysisEngine
            geo_engine = GeopoliticalAnalysisEngine(self, None)  # Simplified for now
            
            # Analyze the market
            geo_analysis = geo_engine.analyze_geopolitical_market(market_data)
            
            if geo_analysis:
                analysis.update({
                    'countries_involved': geo_analysis.countries_involved,
                    'event_type': geo_analysis.event_type,
                    'historical_patterns': geo_analysis.historical_precedents,
                    'rationale': geo_analysis.rationale
                })
                
                # Check for easy trade potential
                # Countries with poor treaty compliance + high aggression = predictable
                untrustworthy_countries = []
                for country_code in geo_analysis.countries_involved:
                    if country_code in geo_engine.country_profiles:
                        profile = geo_engine.country_profiles[country_code]
                        trust_score = profile.calculate_overall_trust_score()
                        if trust_score < 0.4:  # Low trust countries
                            untrustworthy_countries.append(country_code)
                
                # Easy trade if untrustworthy countries are involved in conflict events
                conflict_events = ['bombing_attack', 'invasion', 'treaty_violation', 'war_conflict']
                if (untrustworthy_countries and 
                    geo_analysis.event_type in conflict_events and 
                    geo_analysis.confidence > 0.5):
                    
                    analysis['easy_trade_potential'] = True
                    analysis['confidence_boost'] = 1.4  # Significant boost for easy trades
                    
                    # Enhanced rationale
                    country_names = [geo_engine.country_profiles.get(code, {'country_name': code})['country_name'] 
                                   for code in untrustworthy_countries]
                    analysis['rationale'] = f"UNTRUSTWORTHY ACTORS: {', '.join(country_names)} have history of avoiding peace treaties and high conflict involvement - {geo_analysis.event_type.replace('_', ' ')} highly likely"
                    
        except ImportError:
            # Fallback analysis without full geopolitical engine
            analysis['rationale'] = "Geopolitical market detected but detailed analysis unavailable"
        
        return analysis

    def _analyze_weather_market_opportunity(self, market_data: Dict[str, Any], implied_prob: float) -> Dict[str, Any]:
        """Analyze weather Kalshi markets for "quick money" trades based on seasonal patterns.

        Weather markets are often the most predictable in prediction markets due to
        meteorological data and seasonal trends.

        Args:
            market_data: Market data from get_market_implied_view
            implied_prob: Current market-implied probability

        Returns:
            Dict with weather analysis results
        """
        title = market_data.get('title', '').upper()

        analysis = {
            'is_weather_market': False,
            'location': '',
            'weather_type': '',
            'season': '',
            'quick_money_potential': False,
            'confidence_boost': 1.0,
            'seasonal_edge': 0.0,
            'rationale': '',
            'recommended_action': ''
        }

        # Check if this is a weather market
        weather_keywords = [
            'TEMPERATURE', 'TEMP', 'DEGREE', 'AVERAGE TEMP',
            'PRECIPITATION', 'RAIN', 'SNOW', 'SNOWFALL',
            'HURRICANE', 'STORM', 'WEATHER',
            'SUMMER', 'WINTER', 'SPRING', 'FALL', 'SEASON'
        ]

        is_weather = any(keyword in title for keyword in weather_keywords)

        if not is_weather:
            return analysis

        analysis['is_weather_market'] = True

        # Initialize weather engine if available
        try:
            from engines.weather_engine import WeatherAnalysisEngine
            weather_engine = WeatherAnalysisEngine(self, None)  # Simplified for now

            # Analyze the market
            weather_analysis = weather_engine.analyze_weather_market(market_data)

            if weather_analysis:
                analysis.update({
                    'location': weather_analysis.location,
                    'weather_type': weather_analysis.weather_type,
                    'season': weather_analysis.season,
                    'seasonal_edge': weather_analysis.seasonal_edge,
                    'rationale': weather_analysis.rationale
                })

                # Check for quick money potential
                if weather_analysis.quick_money_potential and weather_analysis.seasonal_edge > 0.15:
                    analysis['quick_money_potential'] = True
                    analysis['confidence_boost'] = 1.3  # Significant boost for quick money trades

                    # Get recommended action
                    action = weather_engine._get_weather_trade_action(weather_analysis)
                    analysis['recommended_action'] = action

                    # Enhanced rationale
                    analysis['rationale'] = f"QUICK MONEY WEATHER: {weather_analysis.seasonal_edge:.1%} seasonal edge in {weather_analysis.location} {weather_analysis.season} - {weather_analysis.weather_type} highly predictable"

        except ImportError:
            # Fallback analysis without full weather engine
            analysis['rationale'] = "Weather market detected but detailed analysis unavailable"

        return analysis

    def _analyze_macro_calendar_opportunity(self, market_data: Dict[str, Any], implied_prob: float) -> Dict[str, Any]:
        """Analyze macroeconomic calendar events for systematic forecast errors."""

        title = market_data.get('title', '').upper()

        analysis = {
            'is_macro_event': False,
            'event_type': '',
            'easy_trade_potential': False,
            'confidence_boost': 1.0,
            'rationale': '',
            'recommended_action': ''
        }

        # Check if this is a macro calendar event
        macro_keywords = [
            'CPI', 'CONSUMER PRICE', 'INFLATION',
            'NFP', 'NON-FARM', 'PAYROLL', 'EMPLOYMENT',
            'FED', 'FOMC', 'FUNDS RATE', 'INTEREST RATE',
            'GDP', 'GROSS DOMESTIC PRODUCT',
            'RETAIL SALES', 'DURABLES',
            'UNEMPLOYMENT', 'JOBLESS',
            'HOUSING STARTS', 'BUILDING PERMITS'
        ]

        is_macro = any(keyword in title for keyword in macro_keywords)

        if not is_macro:
            return analysis

        analysis['is_macro_event'] = True

        # Initialize macro engine if available
        try:
            from engines.macro_calendar_engine import MacroCalendarEngine
            macro_engine = MacroCalendarEngine(self, None)

            # Extract event type from title
            event_type = 'CPI'  # default
            if 'NFP' in title or 'PAYROLL' in title:
                event_type = 'NFP'
            elif 'FED' in title or 'FOMC' in title or 'FUNDS' in title:
                event_type = 'FED_FUNDS'
            elif 'GDP' in title:
                event_type = 'GDP'
            elif 'UNEMPLOYMENT' in title:
                event_type = 'UNEMPLOYMENT'
            elif 'RETAIL' in title:
                event_type = 'RETAIL_SALES'

            analysis['event_type'] = event_type

            # Analyze the macro event
            macro_analysis = macro_engine.analyze_macro_event({
                'event_name': event_type,
                'forecast': 0.0,  # Would be extracted from market data
                'market_probability': implied_prob
            })

            if macro_analysis and macro_analysis.easy_trade_confidence > 0.75:
                analysis.update({
                    'easy_trade_potential': True,
                    'confidence_boost': 1.2,
                    'rationale': f"Macro calendar edge: {macro_analysis.rationale}",
                    'recommended_action': macro_analysis.recommended_action
                })

        except ImportError:
            analysis['rationale'] = "Macro calendar event detected but detailed analysis unavailable"

        return analysis

    def _analyze_earnings_drift_opportunity(self, market_data: Dict[str, Any], implied_prob: float) -> Dict[str, Any]:
        """Analyze earnings-related markets for post-earnings drift patterns."""

        title = market_data.get('title', '').upper()

        analysis = {
            'is_earnings_market': False,
            'company': '',
            'easy_trade_potential': False,
            'confidence_boost': 1.0,
            'rationale': '',
            'recommended_action': ''
        }

        # Check if this is an earnings market
        earnings_keywords = [
            'EARNINGS', 'EPS', 'REVENUE', 'BEAT', 'MISS',
            'GUIDANCE', 'OUTLOOK', 'QUARTER', 'Q1', 'Q2', 'Q3', 'Q4',
            'APPLE', 'MICROSOFT', 'AMAZON', 'GOOGLE', 'META', 'TESLA'
        ]

        is_earnings = any(keyword in title for keyword in earnings_keywords)

        if not is_earnings:
            return analysis

        analysis['is_earnings_market'] = True

        # Extract company (simplified)
        companies = ['AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META', 'TSLA', 'NVDA']
        company = 'AAPL'  # default
        for comp in companies:
            if comp in title:
                company = comp
                break
        analysis['company'] = company

        # Initialize earnings engine if available
        try:
            from engines.earnings_drift_engine import EarningsDriftEngine
            earnings_engine = EarningsDriftEngine(self, None)

            earnings_analysis = earnings_engine.analyze_earnings_opportunity({
                'company_ticker': company,
                'eps_forecast': 0.0,
                'revenue_forecast': 0.0,
                'guidance_expectation': 'maintain',
                'market_price': 100.0  # placeholder
            })

            if earnings_analysis and earnings_analysis.easy_trade_confidence > 0.75:
                analysis.update({
                    'easy_trade_potential': True,
                    'confidence_boost': 1.25,
                    'rationale': f"Earnings drift pattern: {earnings_analysis.rationale}",
                    'recommended_action': earnings_analysis.recommended_action
                })

        except ImportError:
            analysis['rationale'] = "Earnings market detected but detailed analysis unavailable"

        return analysis

    def _analyze_calendar_seasonality_opportunity(self, market_data: Dict[str, Any], implied_prob: float) -> Dict[str, Any]:
        """Analyze calendar-driven seasonal patterns."""

        title = market_data.get('title', '').upper()

        analysis = {
            'is_seasonal_event': False,
            'pattern_type': '',
            'easy_trade_potential': False,
            'confidence_boost': 1.0,
            'rationale': '',
            'recommended_action': ''
        }

        # Check if this is a seasonal market
        seasonal_keywords = [
            'CHRISTMAS', 'HOLIDAY', 'SEASON', 'BLACK FRIDAY',
            'TAX', 'APRIL', 'YEAR END', 'QUARTER END',
            'JANUARY', 'SUMMER', 'WINTER', 'HALLOWEEN',
            'THANKSGIVING', 'CHRISTMAS', 'NEW YEAR'
        ]

        is_seasonal = any(keyword in title for keyword in seasonal_keywords)

        if not is_seasonal:
            return analysis

        analysis['is_seasonal_event'] = True

        # Determine pattern type
        if 'CHRISTMAS' in title or 'HOLIDAY' in title:
            pattern = 'Christmas_Rally'
        elif 'TAX' in title or 'APRIL' in title:
            pattern = 'April_Tax_Deadline'
        elif 'QUARTER' in title:
            pattern = 'Quarter_End_Rebalancing'
        elif 'JANUARY' in title:
            pattern = 'January_Effect'
        else:
            pattern = 'Month_End_Window_Dressing'

        analysis['pattern_type'] = pattern

        try:
            from engines.calendar_seasonality_engine import CalendarSeasonalityEngine
            calendar_engine = CalendarSeasonalityEngine(self, None)

            calendar_analysis = calendar_engine.analyze_calendar_opportunity({
                'pattern_name': pattern,
                'days_to_trigger': 7,  # Assume 1 week out
                'market_condition': 'any'
            })

            if calendar_analysis and calendar_analysis.easy_trade_confidence > 0.75:
                analysis.update({
                    'easy_trade_potential': True,
                    'confidence_boost': 1.25,
                    'rationale': f"Seasonal pattern: {calendar_analysis.rationale}",
                    'recommended_action': calendar_analysis.recommended_action
                })

        except ImportError:
            analysis['rationale'] = "Seasonal market detected but detailed analysis unavailable"

        return analysis

    def _analyze_sports_opportunity(self, market_data: Dict[str, Any], implied_prob: float) -> Dict[str, Any]:
        """Analyze sports markets for statistical edges."""

        title = market_data.get('title', '').upper()

        analysis = {
            'is_sports_market': False,
            'sport': '',
            'easy_trade_potential': False,
            'confidence_boost': 1.0,
            'rationale': '',
            'recommended_action': ''
        }

        # Check if this is a sports market
        sports_keywords = [
            'NFL', 'NBA', 'MLB', 'NHL', 'SOCCER', 'TENNIS',
            'POINTS', 'REBOUNDS', 'YARDS', 'TOUCHDOWNS',
            'OVER', 'UNDER', 'SPREAD', 'MONEYLINE',
            'MAHOMES', 'JAMES', 'CURRY', 'BETTS', 'OHTANI'
        ]

        is_sports = any(keyword in title for keyword in sports_keywords)

        if not is_sports:
            return analysis

        analysis['is_sports_market'] = True

        # Determine sport
        if 'NFL' in title or 'MAHOMES' in title or 'KUPP' in title:
            sport = 'NFL'
        elif 'NBA' in title or 'JAMES' in title or 'CURRY' in title:
            sport = 'NBA'
        elif 'MLB' in title or 'OHTANI' in title or 'BETTS' in title:
            sport = 'MLB'
        else:
            sport = 'NFL'  # default

        analysis['sport'] = sport

        try:
            from engines.sports_analysis_engine import SportsAnalysisEngine
            sports_engine = SportsAnalysisEngine(self, None)

            # Extract player (simplified)
            players = ['Patrick Mahomes', 'Cooper Kupp', 'LeBron James', 'Stephen Curry', 'Shohei Ohtani', 'Mookie Betts']
            player = players[0]  # default
            for p in players:
                if p.split()[-1].upper() in title:  # Last name match
                    player = p
                    break

            sports_analysis = sports_engine.analyze_sports_market({
                'market_type': 'player_prop',
                'player_name': player,
                'prop_type': 'points',  # simplified
                'target_value': 25.0,  # placeholder
                'market_probability': implied_prob,
                'is_home': True,
                'opponent_rating': 0.5,
                'weather_impact': 0.0
            })

            if sports_analysis and sports_analysis.easy_trade_confidence > 0.75:
                analysis.update({
                    'easy_trade_potential': True,
                    'confidence_boost': 1.3,
                    'rationale': f"Sports statistical edge: {sports_analysis.rationale}",
                    'recommended_action': sports_analysis.recommended_action
                })

        except ImportError:
            analysis['rationale'] = "Sports market detected but detailed analysis unavailable"

        return analysis

    def _analyze_event_structure_opportunity(self, market_data: Dict[str, Any], implied_prob: float) -> Dict[str, Any]:
        """Analyze contract structure for arbitrage opportunities."""

        title = market_data.get('title', '').upper()

        analysis = {
            'is_contract_market': False,
            'contract_type': '',
            'easy_trade_potential': False,
            'confidence_boost': 1.0,
            'rationale': '',
            'recommended_action': ''
        }

        # Check if this is a contract we can analyze
        contract_keywords = [
            'ELECTION', 'PRESIDENTIAL', 'WIN', 'LOSE',
            'AWARD', 'OSCAR', 'TONY', 'EMMY', 'GRAMMY',
            'RECORD', 'HIGHEST', 'LOWEST', 'BEST',
            'CHAMPIONSHIP', 'FINAL', 'TITLE'
        ]

        is_contract = any(keyword in title for keyword in contract_keywords)

        if not is_contract:
            return analysis

        analysis['is_contract_market'] = True

        # Determine contract type
        if 'ELECTION' in title or 'PRESIDENTIAL' in title:
            contract_type = 'PRESIDENTIAL_ELECTION'
        elif 'AWARD' in title or 'OSCAR' in title:
            contract_type = 'CELEBRITY_EVENT'
        elif 'RECORD' in title:
            contract_type = 'WEATHER_RECORD'
        elif 'CHAMPIONSHIP' in title:
            contract_type = 'SPORTS_CHAMPIONSHIP'
        else:
            contract_type = 'CORPORATE_EARNINGS'

        analysis['contract_type'] = contract_type

        try:
            from engines.event_structure_engine import EventStructureEngine
            structure_engine = EventStructureEngine(self, None)

            structure_analysis = structure_engine.analyze_contract_structure({
                'contract_id': contract_type,
                'contract_title': title,
                'market_data': {'market_price': implied_prob}
            })

            if structure_analysis and structure_analysis.easy_trade_confidence > 0.75:
                analysis.update({
                    'easy_trade_potential': True,
                    'confidence_boost': 1.4,
                    'rationale': f"Contract structure arbitrage: {structure_analysis.rationale}",
                    'recommended_action': structure_analysis.recommended_action
                })

        except ImportError:
            analysis['rationale'] = "Contract structure detected but detailed analysis unavailable"

        return analysis

    def _analyze_range_barrier_opportunity(self, market_data: Dict[str, Any], implied_prob: float) -> Dict[str, Any]:
        """Analyze range/barrier markets for volatility edges."""

        title = market_data.get('title', '').upper()

        analysis = {
            'is_barrier_market': False,
            'asset_type': '',
            'easy_trade_potential': False,
            'confidence_boost': 1.0,
            'rationale': '',
            'recommended_action': ''
        }

        # Check if this is a range/barrier market
        barrier_keywords = [
            'ABOVE', 'BELOW', 'OVER', 'UNDER',
            'BARRIER', 'RANGE', 'STAYS WITHIN',
            'HITS', 'BREAKS', 'VOLATILITY',
            'SPY', 'QQQ', 'TLT', 'GLD', 'BTC', 'VIG'
        ]

        is_barrier = any(keyword in title for keyword in barrier_keywords)

        if not is_barrier:
            return analysis

        analysis['is_barrier_market'] = True

        # Determine asset type
        if 'SPY' in title or 'QQQ' in title:
            asset_type = 'equity_index'
        elif 'TLT' in title:
            asset_type = 'bond_etf'
        elif 'GLD' in title:
            asset_type = 'commodity_etf'
        elif 'BTC' in title:
            asset_type = 'crypto'
        else:
            asset_type = 'equity_index'

        analysis['asset_type'] = asset_type

        # Map to specific asset
        asset_map = {
            'equity_index': 'SPY',
            'bond_etf': 'TLT',
            'commodity_etf': 'GLD',
            'crypto': 'BTC'
        }
        asset_name = asset_map.get(asset_type, 'SPY')

        try:
            from engines.range_barrier_engine import RangeBarrierEngine
            barrier_engine = RangeBarrierEngine(self, None)

            barrier_analysis = barrier_engine.analyze_range_barrier_market({
                'asset_name': asset_name,
                'barrier_type': 'stays_within',  # simplified
                'barrier_level': 100.0,  # placeholder
                'current_price': 95.0,   # placeholder
                'time_to_barrier': 30,
                'market_probability': implied_prob,
                'current_volatility': 0.02  # placeholder
            })

            if barrier_analysis and barrier_analysis.easy_trade_confidence > 0.75:
                analysis.update({
                    'easy_trade_potential': True,
                    'confidence_boost': 1.35,
                    'rationale': f"Volatility regime edge: {barrier_analysis.rationale}",
                    'recommended_action': barrier_analysis.recommended_action
                })

        except ImportError:
            analysis['rationale'] = "Range/barrier market detected but detailed analysis unavailable"

        return analysis

    def _analyze_microstructure_opportunity(self, market_data: Dict[str, Any], implied_prob: float) -> Dict[str, Any]:
        """Analyze microstructure for short-term anomalies."""

        analysis = {
            'is_microstructure_market': True,  # All markets have microstructure
            'market_type': 'prediction_market',
            'easy_trade_potential': False,
            'confidence_boost': 1.0,
            'rationale': '',
            'recommended_action': ''
        }

        try:
            from engines.microstructure_engine import MicrostructureEngine
            micro_engine = MicrostructureEngine(self, None)

            microstructure_analysis = micro_engine.analyze_microstructure_opportunity({
                'market_name': 'KALSHI',  # Default to Kalshi
                'market_type': 'prediction_market',
                'current_volume': market_data.get('volume', 1000),
                'recent_avg_volume': market_data.get('avg_volume', 800),
                'current_price': implied_prob,
                'recent_prices': [implied_prob] * 5,  # placeholder
                'bid_volume': 100,
                'ask_volume': 80,
                'time_since_anomaly': 5
            })

            if microstructure_analysis and microstructure_analysis.easy_trade_confidence > 0.75:
                analysis.update({
                    'easy_trade_potential': True,
                    'confidence_boost': 1.25,
                    'rationale': f"Microstructure anomaly: {microstructure_analysis.rationale}",
                    'recommended_action': microstructure_analysis.recommended_action
                })

        except ImportError:
            analysis['rationale'] = "Microstructure analysis available but detailed engine not loaded"

        return analysis

    def _analyze_corporate_actions_opportunity(self, market_data: Dict[str, Any], implied_prob: float) -> Dict[str, Any]:
        """Analyze corporate actions for predictable reaction patterns."""

        title = market_data.get('title', '').upper()

        analysis = {
            'is_corporate_action': False,
            'action_type': '',
            'company': '',
            'easy_trade_potential': False,
            'confidence_boost': 1.0,
            'rationale': '',
            'recommended_action': ''
        }

        # Check if this is a corporate action market
        corporate_keywords = [
            'STOCK SPLIT', 'SPLIT', 'REVERSE SPLIT',
            'BUYBACK', 'SHARE REPURCHASE', 'STOCK BUYBACK',
            'DIVIDEND', 'SPECIAL DIVIDEND', 'CASH DIVIDEND',
            'MERGER', 'ACQUISITION', 'TAKEOVER',
            'SPINOFF', 'SPIN-OFF', 'SEPARATION',
            'RIGHTS OFFERING', 'OFFERING', 'SECURITIES OFFERING',
            'GOING PRIVATE', 'PRIVATIZATION', 'DELISTING'
        ]

        is_corporate = any(keyword in title for keyword in corporate_keywords)

        if not is_corporate:
            return analysis

        analysis['is_corporate_action'] = True

        # Determine action type
        action_type = 'stock_split'
        if 'BUYBACK' in title or 'REPURCHASE' in title:
            action_type = 'buyback'
        elif 'DIVIDEND' in title:
            action_type = 'special_dividend'
        elif 'MERGER' in title or 'ACQUISITION' in title:
            action_type = 'merger'
        elif 'RIGHTS' in title or 'OFFERING' in title:
            action_type = 'rights_offering'
        elif 'PRIVATE' in title or 'DELISTING' in title:
            action_type = 'delisting'

        analysis['action_type'] = action_type

        # Extract company (simplified)
        companies = ['AAPL', 'TSLA', 'MSFT', 'JPM', 'BAC', 'WFC']
        company = companies[0]  # default
        for comp in companies:
            if comp in title:
                company = comp
                break
        analysis['company'] = company

        # Initialize corporate actions engine if available
        try:
            from engines.corporate_actions_engine import CorporateActionsEngine
            corporate_engine = CorporateActionsEngine(self, None)

            corporate_analysis = corporate_engine.analyze_corporate_action({
                'company_ticker': company,
                'action_type': action_type,
                'action_date': datetime.now(),
                'days_to_action': 30,  # Assume 30 days out
                'current_price': 100.0  # placeholder
            })

            if corporate_analysis and corporate_analysis.easy_trade_confidence > 0.75:
                analysis.update({
                    'easy_trade_potential': True,
                    'confidence_boost': 1.35,
                    'rationale': f"Corporate action edge: {corporate_analysis.rationale}",
                    'recommended_action': corporate_analysis.recommended_action
                })

        except ImportError:
            analysis['rationale'] = "Corporate action detected but detailed analysis unavailable"

        return analysis

    def _assess_market_context(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive assessment of market context, timing, and conditions."""
        ticker = market_data.get('ticker', '')
        volume = market_data.get('volume', 0)
        implied_prob = market_data.get('implied_probability', 0.5)
        
        assessment = {
            'liquidity_assessment': 'unknown',
            'timing_assessment': 'unknown', 
            'context_assessment': 'unknown',
            'market_efficiency': 'unknown',
            'timing_multiplier': 1.0,
            'event_horizon': 'unknown'
        }
        
        # Liquidity assessment
        if volume < 1000:
            assessment['liquidity_assessment'] = 'low_liquidity'
        elif volume < 10000:
            assessment['liquidity_assessment'] = 'moderate_liquidity'
        else:
            assessment['liquidity_assessment'] = 'high_liquidity'
            
        # Extract event timing from ticker
        if 'NOV' in ticker:
            assessment['event_horizon'] = 'election_day_november'
            assessment['timing_assessment'] = 'critical_election_timing'
            assessment['timing_multiplier'] = 1.5  # Higher stakes near election
        elif 'DEC' in ticker or 'JAN' in ticker:
            assessment['event_horizon'] = 'post_election_transition'
            assessment['timing_assessment'] = 'transition_period'
            assessment['timing_multiplier'] = 1.2
        elif 'FED' in ticker or 'RATE' in ticker:
            assessment['event_horizon'] = 'fed_meeting_imminent'
            assessment['timing_assessment'] = 'high_stakes_economic_event'
            assessment['timing_multiplier'] = 1.4
        else:
            assessment['event_horizon'] = 'ongoing_event'
            assessment['timing_assessment'] = 'standard_timing'
            
        # Market efficiency assessment based on probability distribution
        if 0.45 <= implied_prob <= 0.55:
            assessment['market_efficiency'] = 'efficient_market'
            assessment['context_assessment'] = 'fair_probability_distribution'
        elif implied_prob < 0.3 or implied_prob > 0.7:
            assessment['market_efficiency'] = 'extreme_probability'
            assessment['context_assessment'] = 'market_showing_extreme_bias'
        else:
            assessment['market_efficiency'] = 'moderately_efficient'
            assessment['context_assessment'] = 'market_showing_moderate_confidence'
            
        return assessment

    def _analyze_market_impact_on_traditional_assets(self, market_data: Dict[str, Any], implied_prob: float) -> Dict[str, Any]:
        """Analyze if this Kalshi market could impact traditional assets (stocks, crypto, commodities).
        
        This creates cross-market arbitrage opportunities by identifying prediction markets
        that predict events affecting traditional asset prices.
        
        Args:
            market_data: Market data from get_market_implied_view
            implied_prob: Current market-implied probability
            
        Returns:
            Dict with market impact analysis
        """
        title = market_data.get('title', '').upper()
        ticker = market_data.get('ticker', '').upper()
        
        analysis = {
            'has_traditional_asset_impact': False,
            'impact_strength': 0.0,
            'affected_assets': [],
            'bullish_assets': [],
            'bearish_assets': [],
            'impact_timing': 'unknown',
            'market_category': 'general',
            'confidence_in_impact': 0.0,
            'potential_profit_opportunity': 'low'
        }
        
        # Extract potential price levels from titles (for crypto/stock predictions)
        price_predictions = self._extract_price_predictions(title)
        if price_predictions:
            analysis.update(price_predictions)
            analysis['has_traditional_asset_impact'] = True
            analysis['impact_strength'] = 0.9
            return analysis
        
        # Analyze for company-specific news/events
        company_impacts = self._analyze_company_specific_impacts(title, implied_prob)
        if company_impacts['has_impact']:
            analysis.update(company_impacts)
            analysis['has_traditional_asset_impact'] = True
            return analysis
        
        # Analyze for macroeconomic events
        macro_impacts = self._analyze_macroeconomic_impacts(title, implied_prob)
        if macro_impacts['has_impact']:
            analysis.update(macro_impacts)
            analysis['has_traditional_asset_impact'] = True
            return analysis
        
        # Analyze for sector-specific events
        sector_impacts = self._analyze_sector_specific_impacts(title, implied_prob)
        if sector_impacts['has_impact']:
            analysis.update(sector_impacts)
            analysis['has_traditional_asset_impact'] = True
            return analysis
        
        # Analyze for geopolitical events
        geo_impacts = self._analyze_geopolitical_impacts(title, implied_prob)
        if geo_impacts['has_impact']:
            analysis.update(geo_impacts)
            analysis['has_traditional_asset_impact'] = True
            return analysis
        
        return analysis
    
    def _extract_price_predictions(self, title: str) -> Optional[Dict[str, Any]]:
        """Extract price predictions from market titles (e.g., Bitcoin hitting specific prices).
        
        Args:
            title: Market title
            
        Returns:
            Dict with price prediction analysis or None
        """
        title_lower = title.lower()
        
        # Bitcoin price predictions
        btc_patterns = [
            r'bitcoin.*\$?(\d+)[k]?\b',
            r'btc.*\$?(\d+)[k]?\b',
            r'bitcoin.*above.*\$?(\d+)',
            r'btc.*above.*\$?(\d+)'
        ]
        
        import re
        for pattern in btc_patterns:
            matches = re.findall(pattern, title_lower)
            if matches:
                try:
                    # Extract the price target
                    price_str = matches[0]
                    if 'k' in price_str.lower():
                        price = int(price_str.lower().replace('k', '')) * 1000
                    else:
                        price = int(price_str)
                    
                    # Assess current Bitcoin market conditions
                    current_btc_price = self._get_current_asset_price('BTC')
                    if current_btc_price:
                        price_ratio = price / current_btc_price
                        
                        # Determine if this is bullish or bearish
                        if price_ratio > 2.0:  # Very ambitious target
                            bullish_probability = 0.3
                            bearish_probability = 0.7
                        elif price_ratio > 1.5:  # Ambitious target
                            bullish_probability = 0.4
                            bearish_probability = 0.6
                        elif price_ratio < 0.7:  # Conservative target
                            bullish_probability = 0.7
                            bearish_probability = 0.3
                        else:  # Moderate target
                            bullish_probability = 0.6
                            bearish_probability = 0.4
                        
                        return {
                            'has_traditional_asset_impact': True,
                            'impact_strength': 0.9,
                            'affected_assets': ['BTC-USD'],
                            'bullish_assets': ['BTC-USD'] if bullish_probability > bearish_probability else [],
                            'bearish_assets': ['BTC-USD'] if bearish_probability > bullish_probability else [],
                            'impact_timing': 'long_term',  # Price predictions are usually long-term
                            'market_category': 'crypto_price_prediction',
                            'confidence_in_impact': 0.8,
                            'potential_profit_opportunity': 'high',
                            'price_target': price,
                            'current_price': current_btc_price,
                            'price_ratio': price_ratio
                        }
                except (ValueError, IndexError):
                    continue
        
        return None
    
    def _get_current_asset_price(self, symbol: str) -> Optional[float]:
        """Get current price for an asset (simplified implementation).
        
        In production, this would integrate with real-time price feeds.
        """
        # Simplified price lookup - in production would use real-time data
        price_map = {
            'BTC': 95000,  # Example current price
            'ETH': 3200,
            'SPY': 450,
            'QQQ': 380,
            'AAPL': 180,
            'TSLA': 220,
            'NVDA': 850
        }
        return price_map.get(symbol, None)
    
    def _analyze_company_specific_impacts(self, title: str, probability: float) -> Dict[str, Any]:
        """Analyze company-specific events that could impact stock prices."""
        result = {
            'has_impact': False,
            'impact_strength': 0.0,
            'affected_assets': [],
            'bullish_assets': [],
            'bearish_assets': [],
            'impact_timing': 'medium_term',
            'ripple_effect_opportunities': [],
            'investment_thesis': ''
        }
        
        title_upper = title.upper()
        
        # CORPORATE INVESTMENT DETECTION - NEW INSIDER FEATURE
        if any(keyword in title_upper for keyword in ['INVEST', 'INVESTMENT', 'BILLION', '$35B', '$17.5B', 'JOBS', 'EXPANSION']):
            # Extract investment details
            investment_analysis = self._analyze_corporate_investment(title_upper, probability)
            if investment_analysis['has_investment']:
                result.update(investment_analysis)
                result['has_impact'] = True
                return result
        
        # FDA approval markets
        if 'FDA' in title_upper and ('APPROVE' in title_upper or 'APPROVAL' in title_upper):
            # Find company mentions
            companies = self._extract_companies_from_title(title)
            if companies:
                result['has_impact'] = True
                result['impact_strength'] = 0.9
                result['affected_assets'] = companies
                result['bullish_assets'] = companies  # FDA approval is bullish
                result['market_category'] = 'fda_approval'
                result['confidence_in_impact'] = 0.8
                result['potential_profit_opportunity'] = 'high'
        
        # Earnings surprise markets
        elif 'EARNINGS' in title_upper and ('BEAT' in title_upper or 'SURPRISE' in title_upper):
            companies = self._extract_companies_from_title(title)
            if companies:
                result['has_impact'] = True
                result['impact_strength'] = 0.8
                result['affected_assets'] = companies
                result['bullish_assets'] = companies if probability > 0.6 else []
                result['bearish_assets'] = companies if probability < 0.4 else []
                result['market_category'] = 'earnings_surprise'
                result['confidence_in_impact'] = 0.7
        
        return result
    
    def _analyze_corporate_investment(self, title: str, probability: float) -> Dict[str, Any]:
        """Analyze corporate investment announcements for ripple effect opportunities."""
        result = {
            'has_investment': False,
            'investing_company': None,
            'investment_amount': 0,
            'target_region': None,
            'investment_type': None,
            'ripple_effect_opportunities': [],
            'investment_thesis': ''
        }
        
        # Detect major tech companies investing
        tech_companies = {
            'AMAZON': {'ticker': 'AMZN', 'sector': 'tech_ecommerce'},
            'MICROSOFT': {'ticker': 'MSFT', 'sector': 'tech_cloud'},
            'GOOGLE': {'ticker': 'GOOGL', 'sector': 'tech_ads'},
            'APPLE': {'ticker': 'AAPL', 'sector': 'tech_hardware'},
            'META': {'ticker': 'META', 'sector': 'tech_social'},
            'TESLA': {'ticker': 'TSLA', 'sector': 'tech_ev'}
        }
        
        # Detect investment amounts
        import re
        amount_patterns = [
            r'\$(\d+(?:\.\d+)?)B',  # $35B, $17.5B
            r'\$(\d+(?:\.\d+)?)\s*BILLION',
            r'(\d+(?:\.\d+)?)\s*BILLION'
        ]
        
        investment_amount = 0
        for pattern in amount_patterns:
            match = re.search(pattern, title)
            if match:
                investment_amount = float(match.group(1))
                break
        
        # Detect target regions
        regions = {
            'INDIA': {'etfs': ['INDA', 'INDY'], 'construction': ['LT', 'SBIN'], 'local_tech': ['INFY', 'TCS']},
            'EUROPE': {'etfs': ['IEUR', 'EZU'], 'construction': ['SI', 'VOW'], 'local_tech': ['SAP', 'ASML']},
            'CHINA': {'etfs': ['MCHI', 'FXI'], 'construction': ['600519.SS', '000002.SZ'], 'local_tech': ['BABA', 'JD']},
            'SOUTHEAST ASIA': {'etfs': ['ASEA', 'EEM'], 'construction': ['BBL', 'VALE'], 'local_tech': ['0788.HK', 'Z74.SI']}
        }
        
        target_region = None
        for region_name in regions.keys():
            if region_name in title:
                target_region = region_name
                break
        
        # Find investing company
        investing_company = None
        for company_name, company_data in tech_companies.items():
            if company_name in title:
                investing_company = company_data
                break
        
        # Generate ripple effect opportunities if we have key components
        if investing_company and investment_amount >= 10 and target_region:
            result['has_investment'] = True
            result['investing_company'] = investing_company
            result['investment_amount'] = investment_amount
            result['target_region'] = target_region
            result['impact_strength'] = min(0.9, 0.5 + (investment_amount / 100))
            result['market_category'] = 'corporate_investment'
            result['confidence_in_impact'] = 0.8
            result['investment_timing_analysis'] = {
                'timing_recommendation': 'IMMEDIATE_ENTRY',
                'investment_thesis': f"Major {investment_amount}B investment by {investing_company['ticker']} in {target_region} creates ripple effect opportunities"
            }
            
            # Generate ripple effect opportunities
            region_data = regions[target_region]
            ripple_opportunities = []
            
            # 1. Construction/Infrastructure stocks (build for the investment)
            construction_stocks = region_data['construction']
            ripple_opportunities.extend([
                {
                    'ticker': ticker,
                    'reason': f'Infrastructure construction for {investment_amount}B {target_region} investment',
                    'timing': 'GOOD_TIMING',
                    'category': 'construction_infrastructure'
                } for ticker in construction_stocks[:3]
            ])
            
            # 2. Regional ETFs (broad market exposure)
            regional_etfs = region_data['etfs']
            ripple_opportunities.extend([
                {
                    'ticker': etf,
                    'reason': f'Regional ETF benefiting from {investment_amount}B investment inflow',
                    'timing': 'GOOD_TIMING',
                    'category': 'regional_etf'
                } for etf in regional_etfs[:2]
            ])
            
            # 3. Local tech companies (partners/suppliers to the investing company)
            local_tech = region_data['local_tech']
            ripple_opportunities.extend([
                {
                    'ticker': ticker,
                    'reason': f'Local tech partner/supplier for {investing_company["ticker"]} {target_region} expansion',
                    'timing': 'SUPER_EARLY' if investment_amount >= 30 else 'GOOD_TIMING',
                    'category': 'local_tech_partner'
                } for ticker in local_tech[:3]
            ])
            
            # 4. "Follow the leader" opportunities (other tech companies likely to follow)
            other_tech = [data for name, data in tech_companies.items() if name != investing_company['ticker']]
            ripple_opportunities.extend([
                {
                    'ticker': company['ticker'],
                    'reason': f'Likely follow-on investment to {target_region} after {investing_company["ticker"]} lead',
                    'timing': 'GOOD_TIMING',
                    'category': 'follow_the_leader'
                } for company in other_tech[:3]
            ])
            
            result['ripple_effect_opportunities'] = ripple_opportunities
            result['affected_assets'] = [opp['ticker'] for opp in ripple_opportunities]
            result['bullish_assets'] = [opp['ticker'] for opp in ripple_opportunities]
            result['investment_thesis'] = f"Ride the coattails of {investment_amount}B {target_region} investment through construction, regional ETFs, and follow-the-leader tech plays"
            
        return result
    
    def _analyze_macroeconomic_impacts(self, title: str, probability: float) -> Dict[str, Any]:
        """Analyze macroeconomic events affecting broad markets."""
        result = {
            'has_impact': False,
            'impact_strength': 0.0,
            'affected_assets': [],
            'bullish_assets': [],
            'bearish_assets': [],
            'impact_timing': 'short_term'
        }
        
        title_lower = title.lower()
        
        # Interest rate decisions
        if ('FED' in title or 'RATE' in title) and ('CUT' in title or 'RAISE' in title or 'INCREASE' in title):
            result['has_impact'] = True
            result['impact_strength'] = 0.7
            result['affected_assets'] = ['SPY', 'QQQ', 'BTC-USD']  # Broad market impact
            
            if 'CUT' in title:
                result['bullish_assets'] = ['SPY', 'QQQ', 'BTC-USD']  # Rate cuts are bullish
            else:  # RAISE
                result['bearish_assets'] = ['SPY', 'QQQ']  # Rate hikes are bearish for stocks
            
            result['market_category'] = 'interest_rates'
            result['confidence_in_impact'] = 0.8
        
        # Inflation reports
        elif 'INFLATION' in title or 'CPI' in title:
            result['has_impact'] = True
            result['impact_strength'] = 0.6
            result['affected_assets'] = ['SPY', 'BTC-USD']
            
            if probability > 0.6:  # High inflation expected
                result['bearish_assets'] = ['SPY', 'BTC-USD']
            else:  # Low inflation expected
                result['bullish_assets'] = ['SPY', 'BTC-USD']
            
            result['market_category'] = 'inflation'
            result['confidence_in_impact'] = 0.6
        
        return result
    
    def _analyze_sector_specific_impacts(self, title: str, probability: float) -> Dict[str, Any]:
        """Analyze sector-specific events with thematic mapping and investment timing."""
        result = {
            'has_impact': False,
            'impact_strength': 0.0,
            'affected_assets': [],
            'bullish_assets': [],
            'bearish_assets': [],
            'impact_timing': 'medium_term',
            'thematic_category': None,
            'investment_timing_analysis': {}
        }
        
        title_upper = title.upper()
        
        # SPACE/MARS THEMATIC ANALYSIS
        if any(keyword in title_upper for keyword in ['MARS', 'SPACE', 'COLONIZE', 'ELON MUSK', 'SPACEX', 'ROCKET']):
            result['has_impact'] = True
            result['impact_strength'] = 0.8
            result['thematic_category'] = 'space_exploration'
            result['market_category'] = 'space_sector'
            result['confidence_in_impact'] = 0.75
            
            # Space companies with timing analysis
            space_stocks = {
                'SPCE': {'stage': 'early', 'timing': 'super_early', 'reason': 'Pre-revenue space tourism'},
                'RKLB': {'stage': 'early', 'timing': 'super_early', 'reason': 'Micro-cap rocket launch services'},
                'ASTR': {'stage': 'early', 'timing': 'super_early', 'reason': 'Pre-commercial satellite deployment'},
                'MACH': {'stage': 'early', 'timing': 'super_early', 'reason': 'Pre-revenue hypersonic technology'},
                'BA': {'stage': 'mature', 'timing': 'good_timing', 'reason': 'Established aerospace with space exposure'},
                'LMT': {'stage': 'mature', 'timing': 'good_timing', 'reason': 'Defense contractor with space division'},
                'NOC': {'stage': 'mature', 'timing': 'good_timing', 'reason': 'Space and defense systems leader'}
            }
            
            result['affected_assets'] = list(space_stocks.keys())
            
            # Generate timing-weighted recommendations for all space events
            if probability > 0.1:  # Any meaningful confidence in space event
                # Prioritize early-stage companies for highest upside
                early_stage = [ticker for ticker, data in space_stocks.items() if data['timing'] == 'super_early']
                growth_stage = [ticker for ticker, data in space_stocks.items() if data['timing'] == 'good_timing']
                
                result['bullish_assets'] = early_stage + growth_stage
                result['investment_timing_analysis'] = {
                    'super_early_opportunities': early_stage,
                    'good_timing_opportunities': growth_stage,
                    'investment_thesis': f"High confidence ({probability:.1%}) space prediction creates opportunity for early-stage space companies with highest growth potential",
                    'timing_recommendation': 'SUPER_EARLY_ENTRY' if len(early_stage) > 0 else 'GROWTH_STAGE_ENTRY'
                }
            
        # AI/Tech sector developments
        elif any(keyword in title_upper for keyword in ['AI', 'ARTIFICIAL', 'MACHINE LEARNING', 'CHATGPT', 'OPENAI', 'ANTHROPIC']):
            result['has_impact'] = True
            result['impact_strength'] = 0.7
            result['thematic_category'] = 'ai_technology'
            result['market_category'] = 'ai_tech_sector'
            result['confidence_in_impact'] = 0.7
            
            # AI companies with timing analysis
            ai_stocks = {
                'NVDA': {'stage': 'mature', 'timing': 'good_timing', 'reason': 'AI chip leader with strong growth'},
                'AMD': {'stage': 'growth', 'timing': 'good_timing', 'reason': 'Growing AI chip market share'},
                'MSFT': {'stage': 'mature', 'timing': 'good_timing', 'reason': 'Azure AI services scaling'},
                'GOOGL': {'stage': 'mature', 'timing': 'good_timing', 'reason': 'AI research and cloud integration'},
                'META': {'stage': 'growth', 'timing': 'good_timing', 'reason': 'AI research and metaverse integration'},
                'PLTR': {'stage': 'growth', 'timing': 'super_early', 'reason': 'AI analytics with government contracts'},
                'SNOW': {'stage': 'growth', 'timing': 'good_timing', 'reason': 'AI-powered data platform'}
            }
            
            result['affected_assets'] = list(ai_stocks.keys())
            
            if probability > 0.6:
                early_ai = [ticker for ticker, data in ai_stocks.items() if data['timing'] == 'super_early']
                growth_ai = [ticker for ticker, data in ai_stocks.items() if data['timing'] == 'good_timing']
                
                result['bullish_assets'] = growth_ai + early_ai
                result['investment_timing_analysis'] = {
                    'super_early_opportunities': early_ai,
                    'good_timing_opportunities': growth_ai,
                    'investment_thesis': f"AI advancement prediction supports both established leaders and emerging AI specialists",
                    'timing_recommendation': 'GROWTH_STAGE_ENTRY' if len(growth_ai) > 2 else 'SUPER_EARLY_ENTRY'
                }
        
        # CLIMATE/ENERGY THEMATIC ANALYSIS  
        elif any(keyword in title_upper for keyword in ['CLIMATE', 'RENEWABLE', 'SOLAR', 'WIND', 'ENERGY', 'EARTHQUAKE']):
            result['has_impact'] = True
            result['impact_strength'] = 0.6
            result['thematic_category'] = 'climate_energy'
            result['market_category'] = 'climate_energy_sector'
            result['confidence_in_impact'] = 0.65
            
            # Climate/energy companies with timing analysis
            climate_stocks = {
                'ENPH': {'stage': 'growth', 'timing': 'good_timing', 'reason': 'Solar energy with strong growth'},
                'SEDG': {'stage': 'growth', 'timing': 'good_timing', 'reason': 'Solar inverter technology'},
                'FSLR': {'stage': 'growth', 'timing': 'good_timing', 'reason': 'Solar panel manufacturing'},
                'TSLA': {'stage': 'growth', 'timing': 'good_timing', 'reason': 'Energy storage and EV integration'},
                'BE': {'stage': 'early', 'timing': 'super_early', 'reason': 'Battery technology development'},
                'QS': {'stage': 'early', 'timing': 'super_early', 'reason': 'Pre-commercial battery tech'},
                'CLNE': {'stage': 'early', 'timing': 'super_early', 'reason': 'Hydrogen fuel infrastructure'}
            }
            
            result['affected_assets'] = list(climate_stocks.keys())
            
            if probability > 0.6:
                early_climate = [ticker for ticker, data in climate_stocks.items() if data['timing'] == 'super_early']
                growth_climate = [ticker for ticker, data in climate_stocks.items() if data['timing'] == 'good_timing']
                
                result['bullish_assets'] = growth_climate + early_climate
                result['investment_timing_analysis'] = {
                    'super_early_opportunities': early_climate,
                    'good_timing_opportunities': growth_climate,
                    'investment_thesis': f"Climate/energy event prediction supports renewable transition and energy storage companies",
                    'timing_recommendation': 'GROWTH_STAGE_ENTRY' if len(growth_climate) > 2 else 'SUPER_EARLY_ENTRY'
                }
        
        return result
    
    def _analyze_geopolitical_impacts(self, title: str, probability: float) -> Dict[str, Any]:
        """Analyze geopolitical events affecting markets."""
        result = {
            'has_impact': False,
            'impact_strength': 0.0,
            'affected_assets': [],
            'bullish_assets': [],
            'bearish_assets': [],
            'impact_timing': 'short_term'
        }
        
        # Oil-related geopolitical events
        if any(keyword in title for keyword in ['OIL', 'CRUDE', 'SAUDI', 'RUSSIA', 'MIDDLE EAST']):
            result['has_impact'] = True
            result['impact_strength'] = 0.8
            result['affected_assets'] = ['XOM', 'CVX', 'BTC-USD']  # Oil companies and crypto
            
            if probability > 0.6:  # Crisis/disruption likely
                result['bullish_assets'] = ['XOM', 'CVX']  # Oil prices up = oil stocks up
                result['bearish_assets'] = ['BTC-USD']  # Risk-off = crypto down
            else:
                result['bearish_assets'] = ['XOM', 'CVX']
                result['bullish_assets'] = ['BTC-USD']
            
            result['market_category'] = 'geopolitical_oil'
            result['confidence_in_impact'] = 0.7
        
        return result
    
    def _extract_companies_from_title(self, title: str) -> List[str]:
        """Extract company tickers from market title."""
        companies = []
        title_words = title.split()
        
        # Known company tickers
        company_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX']
        
        for ticker in company_tickers:
            if ticker in title:
                companies.append(ticker)
        
        return companies
    
    def _generate_traditional_asset_signals_from_market_impact(self, market_impact: Dict[str, Any], days_to_expiry: int) -> List[Dict[str, Any]]:
        """Generate traditional asset trading signals based on market impact analysis."""
        signals = []
        
        affected_assets = market_impact.get('affected_assets', [])
        bullish_assets = market_impact.get('bullish_assets', [])
        bearish_assets = market_impact.get('bearish_assets', [])
        impact_strength = market_impact.get('impact_strength', 0.5)
        confidence = market_impact.get('confidence_in_impact', 0.5)
        
        # Calculate impact timeframe (when the market event would affect asset prices)
        if days_to_expiry <= 30:
            impact_timeframe = min(days_to_expiry + 30, 60)  # Short-term impact
        else:
            impact_timeframe = min(days_to_expiry + 60, 120)  # Medium-term impact
        
        # Generate bullish signals with timing analysis
        timing_analysis = market_impact.get('investment_timing_analysis', {})
        super_early = timing_analysis.get('super_early_opportunities', [])
        good_timing = timing_analysis.get('good_timing_opportunities', [])
        timing_rec = timing_analysis.get('timing_recommendation', 'UNKNOWN')
        
        for asset in bullish_assets:
            # Determine company-specific timing and reasoning
            if asset in super_early:
                asset_timing = 'SUPER_EARLY'
                timing_reason = 'Pre-revenue micro-cap with highest growth potential'
            elif asset in good_timing:
                asset_timing = 'GOOD_TIMING'
                timing_reason = 'Growth stage with scaling revenue'
            else:
                asset_timing = 'UNKNOWN'
                timing_reason = 'Timing analysis not available'
            
            signal = {
                'symbol': asset,
                'action': 'BUY_CALL',
                'confidence': confidence * impact_strength,
                'position_size': 1500,  # Standard position for cross-market plays
                'rationale': f"PREDICTION MARKET IMPACT: Favorable outcome likely - bullish for {asset}",
                'thesis': f"{timing_reason} | {market_impact.get('market_category', 'thematic')} exposure",
                'source': 'kalshi_cross_market',
                'days_to_expiry': impact_timeframe,
                'catalyst_type': market_impact.get('market_category', 'prediction_market_impact'),
                'market_impact': market_impact,
                'timing_recommendation': asset_timing,
                'pop_from_sim': confidence * impact_strength,
                'catalyst_score': confidence * impact_strength * 0.8
            }
            signals.append(signal)
        
        # Generate bearish signals
        for asset in bearish_assets:
            signal = {
                'symbol': asset,
                'action': 'BUY_PUT',
                'confidence': confidence * impact_strength,
                'position_size': 1500,
                'rationale': f"PREDICTION MARKET IMPACT: Adverse outcome likely - bearish for {asset}",
                'source': 'kalshi_cross_market',
                'days_to_expiry': impact_timeframe,
                'catalyst_type': market_impact.get('market_category', 'prediction_market_impact'),
                'market_impact': market_impact,
                'pop_from_sim': confidence * impact_strength,
                'catalyst_score': confidence * impact_strength * 0.8
            }
            signals.append(signal)
        
        return signals

    def _adjust_probability_for_context(self, raw_probability: float, assessment: Dict[str, Any]) -> float:
        """Adjust raw market probability based on context factors."""
        adjusted_prob = raw_probability
        
        # Timing adjustments
        timing_multiplier = assessment.get('timing_multiplier', 1.0)
        if timing_multiplier > 1.2:  # High stakes timing
            # Slightly regress extreme probabilities toward 50% for high-stakes events
            if raw_probability < 0.3:
                adjusted_prob = raw_probability + 0.05
            elif raw_probability > 0.7:
                adjusted_prob = raw_probability - 0.05
                
        # Liquidity adjustments - less liquid markets may have more noise
        liquidity = assessment.get('liquidity_assessment', 'moderate_liquidity')
        if liquidity == 'low_liquidity':
            # Regress toward 50% slightly for low liquidity
            adjusted_prob = 0.5 + (adjusted_prob - 0.5) * 0.9
            
        return max(0.01, min(0.99, adjusted_prob))

    def _determine_yes_no_direction(self, market_data: Dict[str, Any], assessment: Dict[str, Any]) -> bool:
        """Determine if this market represents a Yes or No outcome."""
        ticker = market_data.get('ticker', '').upper()
        title = market_data.get('title', '').upper()
        
        # Election markets - determine if it's a positive outcome
        if 'POLPRES' in ticker or 'PRESIDENT' in title:
            # D = Democrat (often considered "Yes" for certain outcomes)
            # R = Republican (often considered "No" for certain outcomes)
            if 'D' in ticker or 'DEMOCRAT' in title:
                return True  # Yes = Democrat wins
            elif 'R' in ticker or 'REPUBLICAN' in title:
                return False  # No = Republican wins
                
        # Fed rate markets
        elif 'FED' in ticker or 'RATE' in title:
            if 'UP' in ticker or 'RAISE' in title or 'INCREASE' in title:
                return True  # Yes = Rates go up
            elif 'DOWN' in ticker or 'CUT' in title or 'DECREASE' in title:
                return False  # No = Rates go down
                
        # Volatility markets
        elif 'VOL' in ticker or 'VIX' in title:
            if 'UP' in ticker or 'HIGH' in title or 'ABOVE' in title:
                return True  # Yes = Volatility increases
            elif 'DOWN' in ticker or 'LOW' in title or 'BELOW' in title:
                return False  # No = Volatility decreases
                
        # Default to analyzing title for Yes/No indicators
        if 'YES' in title or 'TRUE' in title or 'UP' in title:
            return True
        elif 'NO' in title or 'FALSE' in title or 'DOWN' in title:
            return False
            
        return True  # Default to Yes if unclear

    def _analyze_market_momentum(self, market_data: Dict[str, Any], assessment: Dict[str, Any], adjusted_probability: float) -> Dict[str, Any]:
        """Analyze market momentum for mean reversion or momentum opportunities."""
        implied_prob = market_data.get('implied_probability', 0.5)
        volume = market_data.get('volume', 0)
        
        result = {
            'signal': None,
            'confidence': 0.0,
            'rationale': '',
            'action': None,
            'position_size': 0.0
        }
        
        efficiency = assessment.get('market_efficiency', 'moderately_efficient')
        timing_multiplier = assessment.get('timing_multiplier', 1.0)
        
        # Mean reversion opportunities in inefficient markets
        if efficiency == 'extreme_probability':
            if implied_prob < 0.25:
                # Very low probability - potential long opportunity
                result['signal'] = 'BUY_YES'
                result['action'] = 'BUY_CALL'
                result['confidence'] = (0.5 - implied_prob) * 1.2 * timing_multiplier
                result['position_size'] = 75 * (0.5 - implied_prob) * 2 * timing_multiplier
                result['rationale'] = f"Extreme low probability ({implied_prob:.1%}) - mean reversion opportunity with {assessment['timing_assessment']}"
            elif implied_prob > 0.75:
                # Very high probability - potential short opportunity  
                result['signal'] = 'BUY_NO'
                result['action'] = 'BUY_PUT'
                result['confidence'] = (implied_prob - 0.5) * 1.2 * timing_multiplier
                result['position_size'] = 75 * (implied_prob - 0.5) * 2 * timing_multiplier
                result['rationale'] = f"Extreme high probability ({implied_prob:.1%}) - mean reversion opportunity with {assessment['timing_assessment']}"
        elif efficiency == 'efficient_market' and volume > 5000:
            # Look for momentum in efficient, liquid markets
            if implied_prob > 0.6 and timing_multiplier > 1.2:
                # Strong momentum in high-stakes timing
                result['signal'] = 'BUY_YES'
                result['action'] = 'BUY_CALL'
                result['confidence'] = (implied_prob - 0.5) * 1.1
                result['position_size'] = 50 * (implied_prob - 0.5) * timing_multiplier
                result['rationale'] = f"Strong momentum ({implied_prob:.1%}) in {assessment['timing_assessment']}"
            elif implied_prob < 0.4 and timing_multiplier > 1.2:
                # Weak momentum in high-stakes timing
                result['signal'] = 'BUY_NO'
                result['action'] = 'BUY_PUT'
                result['confidence'] = (0.5 - implied_prob) * 1.1
                result['position_size'] = 50 * (0.5 - implied_prob) * timing_multiplier
                result['rationale'] = f"Weak momentum ({implied_prob:.1%}) in {assessment['timing_assessment']}"
        else:
            result['rationale'] = f"Market probability ({implied_prob:.1%}) in neutral range - {assessment['context_assessment']}"
                
        return result
                
    def generate_phasma_prediction(self, market_data: Dict[str, Any]) -> Optional[float]:
        """Generate Phasma's own probability prediction for a Kalshi market.
        
        This uses real-time RSS/news data, sentiment analysis, and market context
        to predict outcomes instead of hardcoded heuristics.
        Returns probability between 0.0 and 1.0, or None if no prediction available.
        """
        ticker = market_data.get('ticker', '').upper()
        title = market_data.get('title', '').upper()
        
        # Map Kalshi markets to relevant news topics and keywords
        market_keywords = self._map_market_to_keywords(ticker, title)
        if not market_keywords:
            return None
        
        # Use news engine to get real-time context
        if not self.news_engine:
            return self._fallback_prediction(ticker, title)
        
        try:
            # Search recent news (last 48 hours) for relevant articles
            news_articles = self.news_engine.search_news_memory(
                keywords=market_keywords,
                hours_back=48
            )
            
            # Limit to most recent 20 articles for performance
            news_articles = news_articles[:20]
            
            if not news_articles:
                return self._fallback_prediction(ticker, title)
            
            # Calculate sentiment from articles
            sentiment_scores = []
            for article in news_articles:
                title_text = article.get('title', '')
                summary_text = article.get('summary', '')
                full_text = f"{title_text} {summary_text}"
                
                try:
                    sentiment = self.news_engine.analyzer.calculate_sentiment(full_text)
                    sentiment_scores.append(sentiment)
                except Exception:
                    continue
            
            if not sentiment_scores:
                return self._fallback_prediction(ticker, title)
            
            # Average sentiment across all relevant articles
            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
            
            # Convert sentiment (-1 to 1) to probability (0 to 1)
            # Neutral sentiment = 0.5 probability
            # Strongly positive = higher probability
            # Strongly negative = lower probability
            probability = 0.5 + (avg_sentiment * 0.3)  # Scale sentiment to +/-30% from neutral
            probability = max(0.1, min(0.9, probability))  # Clamp between 10% and 90%
            
            # Confidence based on number of articles and sentiment consistency
            article_count = len(sentiment_scores)
            sentiment_std = statistics.stdev(sentiment_scores) if len(sentiment_scores) > 1 else 0
            
            # Higher confidence with more articles and consistent sentiment
            confidence = min(0.8, (article_count * 0.1) + (1 - sentiment_std) * 0.4)
            
            if confidence >= 0.4:
                print(f"SCANNING Kalshi prediction for {ticker}: {probability:.1%} confidence "
                      f"(from {article_count} articles, avg sentiment: {avg_sentiment:.2f})")
                return probability
                
        except Exception as e:
            print(f"WARNING Error generating RSS-based Kalshi prediction: {e}")
            return self._fallback_prediction(ticker, title)
        
        return None
    
    def _map_market_to_keywords(self, ticker: str, title: str) -> List[str]:
        """Map Kalshi market to relevant news keywords."""
        ticker_upper = ticker.upper()
        title_upper = title.upper()
        
        # Election markets
        if 'POLPRES' in ticker_upper or 'PRESIDENT' in title_upper or 'ELECTION' in title_upper:
            if 'D' in ticker_upper or 'DEMOCRAT' in title_upper:
                return ['democrat', 'democrats', 'biden', 'kamala', 'harris', 'democratic party', 'election 2024']
            elif 'R' in ticker_upper or 'REPUBLICAN' in title_upper:
                return ['republican', 'republicans', 'trump', 'donald', 'desantis', 'election 2024']
            else:
                return ['election 2024', 'president', 'polls', 'voting', 'democrat', 'republican']
        
        # Fed rate markets
        elif 'FED' in ticker_upper or 'RATE' in title_upper:
            if 'UP' in ticker_upper or 'RAISE' in title_upper or 'INCREASE' in title_upper:
                return ['fed rate hike', 'federal reserve', 'interest rates', 'powell', 'fomc', 'inflation']
            elif 'DOWN' in ticker_upper or 'CUT' in title_upper or 'LOWER' in title_upper:
                return ['fed rate cut', 'federal reserve', 'interest rates', 'powell', 'fomc', 'economy']
            else:
                return ['federal reserve', 'fed', 'interest rates', 'powell', 'fomc']
        
        # Market volatility markets
        elif 'VOL' in ticker_upper or 'VIX' in title_upper or 'VOLATILITY' in title_upper:
            if 'UP' in ticker_upper or 'HIGH' in title_upper or 'SPIKE' in title_upper:
                return ['volatility spike', 'vix', 'fear index', 'market crash', 'volatility']
            elif 'DOWN' in ticker_upper or 'LOW' in title_upper:
                return ['volatility low', 'vix', 'market calm', 'volatility', 'stable markets']
            else:
                return ['volatility', 'vix', 'fear index', 'market volatility']
        
        # Weather markets
        elif 'WEATHER' in title_upper or 'TEMP' in ticker_upper:
            return ['weather', 'temperature', 'climate', 'forecast', 'meteorology']
        
        # Sports markets
        elif 'SPORTS' in title_upper or any(sport in title_upper for sport in ['NFL', 'NBA', 'MLB', 'SOCCER', 'FOOTBALL']):
            return ['sports', 'nfl', 'nba', 'mlb', 'soccer', 'football', 'basketball', 'baseball']
        
        # Economic indicators
        elif any(indicator in title_upper for indicator in ['CPI', 'GDP', 'UNEMPLOYMENT', 'JOBS']):
            return ['economy', 'cpi', 'gdp', 'unemployment', 'jobs', 'economic data', 'federal reserve']
        
        return []
    
    def _fallback_prediction(self, ticker: str, title: str) -> Optional[float]:
        """Fallback prediction when news data is unavailable."""
        # Keep some basic heuristics as backup
        ticker_upper = ticker.upper()
        title_upper = title.upper()
        
        # GDP markets - use historical growth patterns
        if 'GDP' in ticker_upper or 'GDP' in title_upper:
            # Q4 GDP typically grows 1-3% annually
            if '1.25' in title_upper:
                return 0.65  # Likely to exceed 1.25%
            elif '1.75' in title_upper:
                return 0.45  # Less likely to exceed 1.75%
            elif '2.0' in title_upper:
                return 0.35  # Unlikely to exceed 2.0%
            else:
                return 0.50  # Neutral for other GDP thresholds
        
        # Temperature markets - use seasonal patterns
        elif 'TEMP' in title_upper or 'HIGH TEMP' in title_upper:
            # December NYC temps are typically 40-50F
            if '>45' in title_upper:
                return 0.40  # Less likely to be >45F in December
            elif '<38' in title_upper:
                return 0.30  # Less likely to be <38F in December
            elif '44-45' in title_upper:
                return 0.60  # More likely to be in this range
            else:
                return 0.50  # Neutral for other temp ranges
        
        if 'POLPRES' in ticker_upper or 'PRESIDENT' in title_upper:
            if 'D' in ticker_upper or 'DEMOCRAT' in title_upper:
                return 0.52
            elif 'R' in ticker_upper or 'REPUBLICAN' in title_upper:
                return 0.48
                
        elif 'FED' in ticker_upper or 'RATE' in title_upper:
            if 'UP' in ticker_upper or 'RAISE' in title_upper:
                return 0.45
            elif 'DOWN' in ticker_upper or 'CUT' in title_upper:
                return 0.35
                
        elif 'VOL' in ticker_upper or 'VIX' in title_upper:
            if 'UP' in ticker_upper or 'HIGH' in title_upper:
                return 0.55
            elif 'DOWN' in ticker_upper or 'LOW' in title_upper:
                return 0.45
                
        return None
    
    def _is_weather_market(self, ticker: str) -> bool:
        """Check if a Kalshi market is weather-related.
        
        Kalshi should ONLY trade weather markets per user requirement.
        """
        ticker_upper = ticker.upper()
        
        # Weather keywords and patterns
        weather_patterns = [
            # Temperature patterns
            'HIGH', 'LOW', 'TEMP', 'TEMPERATURE',
            # Precipitation
            'RAIN', 'SNOW', 'PRECIP', 'PRECIPITATION',
            # Weather conditions
            'WEATHER', 'WIND', 'HUMIDITY', 'DEWPOINT',
            # Location codes (major cities)
            'NYC', 'CHI', 'LA', 'MIA', 'DAL', 'SEA', 'DEN',
            # Specific Kalshi weather patterns
            'HIGHNY', 'LOWNY', 'RAINNY', 'SNOWNY',
            'HIGHCHI', 'LOWCHI', 'RAINCHI', 'SNOWCHI',
            'HIGHMIA', 'LOWMIA', 'RAINMIA', 'SNOWMIA',
            # Generic weather event codes
            'WX', 'WTHR'
        ]
        
        # Check if any weather pattern is in the ticker
        for pattern in weather_patterns:
            if pattern in ticker_upper:
                return True
        
        # Additional check: Weather tickers typically have number ranges
        # Example: HIGHNY0-25-85 (NYC high > 85°F on Dec 25)
        import re
        # Pattern for weather with temperature thresholds
        if re.match(r'.*[0-9]-[0-9]+-[0-9]+', ticker_upper):
            # Likely a weather market with date and threshold
            return True
        
        # If none of the weather patterns match, it's not a weather market
        return False
    
    def _is_political_market(self, ticker: str) -> bool:
        """Check if a market is political (president, senate, etc.)"""
        ticker_upper = ticker.upper()
        political_keywords = [
            'PRES', 'PRESIDENT', 'SENATE', 'GOVERNOR', 'CONGRESS', 
            'POLPRES', 'KXPERSONPRES', 'KXNEXTISRAELPM'
        ]
        return any(keyword in ticker_upper for keyword in political_keywords)
    
    def _get_multi_choice_info(self, ticker: str) -> List[Dict[str, Any]]:
        """Get information about all choices in a multi-choice market.
        
        For now, returns a simplified structure. In production,
        this would fetch all submarkets from the API.
        """
        # Extract base event from ticker
        import re
        match = re.match(r'([A-Z]+-[A-Z]+)', ticker.upper())
        if not match:
            # Try different pattern for PERSONPRES markets
            match = re.match(r'(KXPERSONPRES)', ticker.upper())
            if match:
                base_event = match.group(1)
            else:
                return []
        else:
            base_event = match.group(1)
        
        # For demonstration, return mock choices
        # In production, this would query the API for all submarkets
        if 'PRES' in base_event or 'PERSONPRES' in base_event:
            return [
                {'title': 'Fuentes', 'implied_probability': 0.35, 'ticker': f'{base_event}FUENTES'},
                {'title': 'Mam', 'implied_probability': 0.30, 'ticker': f'{base_event}MAM'},
                {'title': 'Biden', 'implied_probability': 0.20, 'ticker': f'{base_event}BIDEN'},
                {'title': 'Trump', 'implied_probability': 0.15, 'ticker': f'{base_event}TRUMP'}
            ]
        elif 'VS' in ticker.upper():
            # For "vs" markets (sports, etc.)
            return [
                {'title': 'Team A', 'implied_probability': 0.60, 'ticker': f'{base_event}TEAMA'},
                {'title': 'Team B', 'implied_probability': 0.40, 'ticker': f'{base_event}TEAMB'}
            ]
        
        return []
    
    def _is_multi_choice_market(self, ticker: str) -> bool:
        """Check if market has multiple choices (election with multiple candidates)"""
        # Multi-choice markets indicators:
        # 1. Candidate identifiers in ticker (e.g., KXPERSONPRESFUENTES-45)
        # 2. "vs" or "versus" in title
        # 3. Election-related keywords
        ticker_upper = ticker.upper()
        
        # Check for election keywords
        election_keywords = ['PRES', 'PRESIDENT', 'SENATE', 'GOVERNOR', 'PERSONPRES']
        if any(keyword in ticker_upper for keyword in election_keywords):
            return True
        
        # Check for "vs" in ticker (sports matches)
        if 'VS' in ticker_upper:
            return True
        
        # Check for candidate identifiers (usually 2-4 letters at end)
        import re
        # Pattern: EVENT-CANDIDATE (e.g., PERSONPRESFUENTES-45)
        match = re.match(r'([A-Z]+)-([A-Z]+)', ticker_upper)
        if match:
            event_part, candidate_part = match.groups()
            # If candidate part is 2-4 letters, likely a candidate code
            if 2 <= len(candidate_part) <= 4:
                return True
        
        return False
    
    def _analyze_candidate_viability(self, ticker: str) -> float:
        """Analyze candidate viability based on current political landscape"""
        # This is a simplified heuristic - in production, would use real data
        ticker_upper = ticker.upper()
        
        # Check if candidate is actually running/active
        active_candidates = {
            'BIDEN': 0.85,  # Incumbent president
            'TRUMP': 0.80,  # Former president with strong base
            'HARRIS': 0.70,  # Current VP
            'NEWSOM': 0.60,  # Governor with national profile
            'DESANTIS': 0.55,  # Governor with presidential ambitions
            'HALEY': 0.50,  # Former governor/UN ambassador
        }
        
        for candidate, viability in active_candidates.items():
            if candidate in ticker_upper:
                return viability
        
        # Unknown candidate - lower viability
        return 0.30
    
    def _extract_race_group(self, ticker: str) -> str:
        """Extract the race/event group from a ticker (e.g., KXPERSONPRES from KXPERSONPRESFUENTES-45)"""
        import re
        # Pattern: EVENT-CANDIDATE-YEAR
        match = re.match(r'([A-Z]+[A-Z]+)-([A-Z]+)', ticker.upper())
        if match:
            return match.group(1)
        return ticker
    
    def _analyze_race_comparatively(self, ticker: str, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a political market by comparing all candidates in the same race"""
        race_group = self._extract_race_group(ticker)
        
        # Check if we've already analyzed this race recently
        if race_group in self._analyzed_races:
            race_analysis = self._analyzed_races[race_group]
            # Check if this candidate is among the top viable ones
            candidate_viability = self._analyze_candidate_viability(ticker)
            top_candidates = race_analysis.get('top_candidates', [])
            
            if ticker not in top_candidates:
                return {
                    'skip_reason': f'Not among top candidates in {race_group} race',
                    'top_candidates': top_candidates,
                    'candidate_rank': len([c for c in top_candidates if self._analyze_candidate_viability(c) > candidate_viability])
                }
            return {'proceed': True}
        
        # For now, return proceed since we don't have access to all markets
        # In a full implementation, we'd fetch all markets for this race
        return {'proceed': True}
