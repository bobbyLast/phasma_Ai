"""
Centralized Confluence Service for unified signal scoring
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
import yfinance as market_data
from datetime import datetime, timedelta
import logging

from utils.price_fetcher import get_price_fetcher

try:
    from utils.free_market_data_sources import SimulatedDataProvider
except ImportError:
    SimulatedDataProvider = None

@dataclass
class ConfluenceResult:
    """Result from confluence analysis"""
    ticker: str
    score: float
    confidence: str
    reasoning: str
    sub_scores: Dict[str, float]
    signals: Dict[str, List]
    evidence_items: List[Dict]
    risk_flags: List[str]
    
class ConfluenceService:
    """Centralized service for scoring confluence across all signal types"""
    
    def __init__(self, config, insider_signal_integrator=None, insider_monitor=None, options_filter=None):
        self.config = config
        self.insider_signal_integrator = insider_signal_integrator
        self.insider_monitor = insider_monitor
        self.options_filter = options_filter
        
        from utils.price_filter_config import resolve_price_filter
        self.price_filter_enabled, self.max_price_per_share = resolve_price_filter(config)
        if self.price_filter_enabled:
            print(f"[CONFLUENCE] Budget: ${self.max_price_per_share} max per share")
        else:
            print("[CONFLUENCE] Per-share price filter disabled")
        
        # Strategy profiles
        self.strategies = config.get('strategies', {})
        self.active_strategy_name = self.strategies.get('active_strategy', 'penny_moonshot')
        self.active_strategy = self.strategies.get(self.active_strategy_name, {})
        
        # Insider thresholds
        insider_thresholds = config.get('insider_thresholds', {})
        self.insider_high_threshold = insider_thresholds.get('high', 500000)
        self.insider_medium_threshold = insider_thresholds.get('medium', 250000)
        self.insider_aggregation_window = insider_thresholds.get('aggregation_window_days', 60)
        
        # Options thresholds
        options_filter_config = config.get('options_filter', {})
        self.min_oi_growth_pct = options_filter_config.get('min_oi_growth_pct', 20)
        self.min_block_contracts = options_filter_config.get('min_block_contracts', 500)
        self.require_buyer_initiated = options_filter_config.get('require_buyer_initiated', True)
        
        # Weights from config
        weights = config.get('insider_integrator', {})
        self.weights = {
            'insider': weights.get('insider_weight', 0.4),
            'institutional': weights.get('institutional_weight', 0.1),
            'analyst': weights.get('analyst_weight', 0.15),
            'options': weights.get('options_weight', 0.2),
            'alt_data': weights.get('alt_data_weight', 0.15)
        }
        
        # Alert threshold
        self.alert_threshold = config.get('alert_threshold', 0.5)
        self.logger = logging.getLogger(__name__)
        
        print(f"[CONFLUENCE] Initialized with {self.active_strategy_name} strategy")
        print(f"[CONFLUENCE] Strategy: {self.active_strategy.get('strategy_name', 'unknown')}")
        print(f"[CONFLUENCE] Required signals: {self.active_strategy.get('required_signals', [])}")
        print(f"[CONFLUENCE] Corroboration window: {self.active_strategy.get('corroboration_window_days', 21)} days")
        if self.price_filter_enabled:
            print(f"[CONFLUENCE] Budget: ${self.max_price_per_share} max per share")
        else:
            print("[CONFLUENCE] Per-share price filter disabled")
    
    def _passes_budget_filter(self, ticker: str) -> bool:
        """Quick budget check to save time on expensive stocks"""
        if not self.price_filter_enabled:
            return True
        try:
            max_price = self.max_price_per_share
            current_price = None
            
            try:
                current_price = get_price_fetcher().get_real_price(ticker)
            except Exception as e:
                self.logger.debug(f"Price fetcher failed: {e}")
            
            # Fallback to provider bridge
            if current_price is None:
                try:
                    stock = market_data.Ticker(ticker)
                    info = stock.info
                    current_price = info.get('currentPrice', 0)
                except Exception as e:
                    self.logger.debug(f"Provider bridge failed: {e}")
            
            # Last resort - simulated data
            if current_price is None and SimulatedDataProvider:
                simulated = SimulatedDataProvider()
                data = simulated.get_price(ticker)
                if data:
                    current_price = data['price']
            
            # Skip if we can't afford even one share
            if current_price and current_price > max_price:
                return False
            
            return True
            
        except Exception as e:
            print(f"[CONFLUENCE] Budget filter error for {ticker}: {e}")
            return False
    
    def score(self, ticker: str, raw_signals: Dict = None) -> Optional[ConfluenceResult]:
        """
        Score a ticker based on confluence of all signal types
        
        Args:
            ticker: Stock symbol
            raw_signals: Optional pre-fetched signals
            
        Returns:
            ConfluenceResult with score and breakdown
        """
        try:
            print(f"[CONFLUENCE] Scoring {ticker}...")
            
            # BUDGET FILTER: Skip stocks we can't afford
            if not self._passes_budget_filter(ticker):
                print(f"[CONFLUENCE] {ticker} SKIPPED - Price exceeds ${self.max_price_per_share} budget")
                return None
            
            # Check strategy filters
            if not self._passes_strategy_filter(ticker):
                print(f"[CONFLUENCE] {ticker} FILTERED - Strategy requirements not met:")
                strategy = self.active_strategy
                print(f"   • Max price: ${strategy.get('max_price', 'N/A')}")
                print(f"   • Min market cap: ${strategy.get('min_market_cap', 0)/1_000_000:.0f}M")
                print(f"   • Max market cap: ${strategy.get('max_market_cap', 'N/A')/1_000_000:.0f}M")
                print(f"   • Min ADV shares: {strategy.get('min_ADV_shares', 0):,}")
                print(f"   • Min ADV dollars: ${strategy.get('min_ADV_dollars', 0):,}")
                return None
            
            # Gather all signals
            signals = self._gather_signals(ticker, raw_signals)
            
            # Check evidence requirements
            evidence_items = self._extract_evidence(ticker, signals)
            required_signals = self.active_strategy.get('required_signals', [])
            
            print(f"[CONFLUENCE] Evidence check:")
            print(f"   • Required signals: {required_signals}")
            print(f"   • Evidence items found: {len(evidence_items)}")
            for ev in evidence_items:
                print(f"     - {ev['channel']}: {ev['evidence']}")
            
            # Calculate sub-scores
            sub_scores = {}
            
            # Insider subscore (40%)
            insider_score = self._score_insider_signals(ticker, signals.get('insider', []))
            sub_scores['insider'] = insider_score
            
            # Options subscore (20%)
            options_score = self._score_options_signals(ticker, signals.get('options', []))
            sub_scores['options'] = options_score
            
            # Institutional subscore (10%)
            institutional_score = self._score_institutional_signals(signals.get('institutional', []))
            sub_scores['institutional'] = institutional_score
            
            # Analyst subscore (15%)
            analyst_score = self._score_analyst_signals(signals.get('analyst', []))
            sub_scores['analyst'] = analyst_score
            
            # Alternative data subscore (15%)
            alt_score = self._score_alt_data_signals(signals.get('alt_data', []))
            sub_scores['alt_data'] = alt_score
            
            # Calculate weighted score
            total_score = (
                insider_score * self.weights['insider'] +
                options_score * self.weights['options'] +
                institutional_score * self.weights['institutional'] +
                analyst_score * self.weights['analyst'] +
                alt_score * self.weights['alt_data']
            )
            
            # Generate reasoning
            reasoning = self._generate_reasoning(ticker, signals, sub_scores)
            
            # Determine confidence level
            if total_score >= 0.8:
                confidence = 'VERY HIGH'
            elif total_score >= 0.6:
                confidence = 'HIGH'
            elif total_score >= 0.4:
                confidence = 'MEDIUM'
            else:
                confidence = 'LOW'
            
            result = ConfluenceResult(
                ticker=ticker,
                score=total_score,
                confidence=confidence,
                reasoning=reasoning,
                sub_scores=sub_scores,
                signals=signals,
                evidence_items=self._extract_evidence(ticker, signals),
                risk_flags=self._check_risk_flags(ticker)
            )
            
            print(f"[CONFLUENCE] {ticker}: {total_score:.1%} ({confidence})")
            return result
            
        except Exception as e:
            print(f"[CONFLUENCE] Error scoring {ticker}: {e}")
            return None
    
    def _passes_strategy_filter(self, ticker: str) -> bool:
        """Check if ticker passes strategy-specific filters"""
        try:
            max_price = self.active_strategy.get('max_price', 1000)
            min_market_cap = self.active_strategy.get('min_market_cap', 0)
            max_market_cap = self.active_strategy.get('max_market_cap', float('inf'))
            min_adv_shares = self.active_strategy.get('min_ADV_shares', 0)
            min_adv_dollars = self.active_strategy.get('min_ADV_dollars', 0)
            
            # Get price and market cap
            stock = market_data.Ticker(ticker)
            info = stock.info
            current_price = info.get('currentPrice', 0)
            market_cap = info.get('marketCap', 0)
            avg_volume = info.get('averageVolume', 0)
            
            # Check price
            if current_price > max_price or current_price <= 0:
                return False
            
            # Check market cap range
            if market_cap < min_market_cap or market_cap > max_market_cap:
                return False
            
            # Check ADV
            adv_shares = avg_volume
            adv_dollars = avg_volume * current_price
            if adv_shares < min_adv_shares or adv_dollars < min_adv_dollars:
                return False
            
            return True
            
        except Exception as e:
            print(f"[CONFLUENCE] Filter error for {ticker}: {e}")
            return False
    
    def _gather_signals(self, ticker: str, raw_signals: Dict = None) -> Dict:
        """Gather all signal types for ticker"""
        signals = {
            'insider': [],
            'options': [],
            'institutional': [],
            'analyst': [],
            'alt_data': []
        }
        
        # Use provided signals or fetch
        if raw_signals:
            signals.update(raw_signals)
        else:
            # Fetch insider signals
            if self.insider_monitor.enabled:
                insider_data = self.insider_monitor.get_recent_buys(ticker)
                if insider_data:
                    signals['insider'] = insider_data
            
            # Fetch options signals
            options_data = self.options_filter.analyze_options_flow(ticker)
            if options_data:
                signals['options'] = options_data
        
        return signals
    
    def _score_insider_signals(self, ticker: str, insider_signals: List) -> float:
        """Score insider signals (0-1 scale)"""
        if not insider_signals:
            # Try fallback with lower threshold
            return self._fallback_insider_score(ticker)
        
        # Use integrator for scoring
        try:
            insider_data = {ticker: insider_signals}
            confluence = self.insider_integrator.analyze_stock(ticker, insider_data)
            if confluence:
                return confluence.confluence_score
        except Exception as e:
            print(f"[CONFLUENCE] Insider scoring error: {e}")
        
        return 0.0
    
    def _fallback_insider_score(self, ticker: str) -> float:
        """Fallback scoring when no insider signals found"""
        # Try with lower threshold or aggregated buys
        try:
            # Check for smaller buys
            original_min = self.insider_monitor.min_value
            self.insider_monitor.min_value = 250000  # $250k fallback
            
            insider_data = self.insider_monitor.get_recent_buys(ticker)
            if insider_data:
                score = len(insider_data) * 0.1  # Small score for each buy
                print(f"[CONFLUENCE] Fallback: Found {len(insider_data)} smaller insider buys")
                return min(score, 0.3)  # Cap at 30%
            
            # Restore original
            self.insider_monitor.min_value = original_min
            
        except Exception as e:
            print(f"[CONFLUENCE] Fallback error: {e}")
        
        return 0.0
    
    def _score_options_signals(self, ticker: str, options_signals: List) -> float:
        """Score options signals with OI growth requirement"""
        if not options_signals:
            return 0.0
        
        # Require sweep/block + OI growth
        score = 0.0
        sweep_count = 0
        oi_growth_count = 0
        
        for signal in options_signals:
            if signal.get('type') in ['sweep_trade', 'block_trade']:
                sweep_count += 1
                if signal.get('volume_ratio', 0) > 2:  # OI growth indicator
                    oi_growth_count += 1
        
        # Score based on quality
        if sweep_count > 0 and oi_growth_count > 0:
            score = min(sweep_count * 0.2, 0.8)  # Max 80% for options alone
            if oi_growth_count >= sweep_count:  # All have OI growth
                score = min(score * 1.2, 1.0)
        
        return score
    
    def _score_institutional_signals(self, institutional_signals: List) -> float:
        """Score institutional signals"""
        if not institutional_signals:
            return 0.0
        
        # Simple scoring based on number of institutions
        return min(len(institutional_signals) * 0.1, 0.5)
    
    def _score_analyst_signals(self, analyst_signals: List) -> float:
        """Score analyst signals"""
        if not analyst_signals:
            return 0.0
        
        # Score based on ratings
        score = 0.0
        for signal in analyst_signals:
            if signal.get('rating') == 'STRONG_BUY':
                score += 0.3
            elif signal.get('rating') == 'BUY':
                score += 0.2
            elif signal.get('rating') == 'HOLD':
                score += 0.1
        
        return min(score, 0.6)
    
    def _score_alt_data_signals(self, alt_signals: List) -> float:
        """Score alternative data signals"""
        if not alt_signals:
            return 0.0
        
        # Simple scoring
        return min(len(alt_signals) * 0.15, 0.4)
    
    def _generate_reasoning(self, ticker: str, signals: Dict, sub_scores: Dict) -> str:
        """Generate human-readable reasoning"""
        parts = []
        
        # Insider reasoning
        if sub_scores['insider'] > 0:
            insider_count = len(signals.get('insider', []))
            if insider_count > 0:
                total_amount = sum(s.get('amount', 0) for s in signals['insider'])
                parts.append(f"Insiders buying ${total_amount/1000000:.1f}M")
        
        # Options reasoning
        if sub_scores['options'] > 0:
            sweeps = [s for s in signals.get('options', []) if s.get('type') in ['sweep_trade', 'block_trade']]
            if sweeps:
                parts.append(f"🎯 SMART MONEY: {len(sweeps)} sweep/block trades")
        
        # Analyst reasoning
        if sub_scores['analyst'] > 0:
            buys = [s for s in signals.get('analyst', []) if 'BUY' in s.get('rating', '')]
            if buys:
                parts.append(f"Analysts: {len(buys)} BUY ratings")
        
        # Macro context from integrator
        try:
            macro = self.insider_integrator._get_macro_context(ticker)
            if macro:
                parts.append(macro)
        except:
            pass
        
        return " | ".join(parts) if parts else "Insufficient data"
    
    def _extract_evidence(self, ticker: str, signals: Dict) -> List[Dict]:
        """Extract evidence items with channel IDs/links"""
        evidence = []
        corroboration_window_days = self.active_strategy.get('corroboration_window_days', 21)
        cutoff = datetime.now() - timedelta(days=corroboration_window_days)
        
        # Insider evidence
        for sig in signals.get('insider', []):
            if isinstance(sig, dict):
                evidence.append({
                    'channel': 'SEC_FORM4',
                    'source': 'SEC EDGAR',
                    'evidence': f"Insider buy: ${sig.get('amount', 0):,.0f}",
                    'timestamp': sig.get('timestamp', datetime.now()),
                    'url': f"https://sec.gov/edgar/search/#/searchForm"
                })
        
        # Options evidence
        for sig in signals.get('options', []):
            if isinstance(sig, dict):
                evidence.append({
                    'channel': 'OPTIONS_FLOW',
                    'source': sig.get('source', 'Options Flow'),
                    'evidence': f"{sig.get('type', 'unknown')}: {sig.get('volume', 0)} contracts",
                    'timestamp': datetime.now(),
                    'url': None
                })
        
        # Filter by corroboration window
        evidence = [e for e in evidence if e.get('timestamp', datetime.now()) >= cutoff]
        
        return evidence[:5]  # Top 5 evidence items
    
    def _check_risk_flags(self, ticker: str) -> List[str]:
        """Check for risk flags"""
        flags = []
        
        try:
            stock = market_data.Ticker(ticker)
            info = stock.info
            
            # Check for recent dilution risk
            market_cap = info.get('marketCap', 0)
            if market_cap < 50_000_000:
                flags.append('LOW_MARKET_CAP')
            
            # Check liquidity
            avg_volume = info.get('averageVolume', 0)
            if avg_volume < 100000:
                flags.append('LOW_LIQUIDITY')
                
        except Exception as e:
            flags.append('DATA_UNAVAILABLE')
        
        return flags
