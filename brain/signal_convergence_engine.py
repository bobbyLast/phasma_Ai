#!/usr/bin/env python3
"""
Multi-Source Signal Convergence Engine - Combines insights from politician trading,
insider trading, corporate investments, and Kalshi predictions to identify high-confidence
trading opportunities when multiple independent sources align.
"""

import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
from collections import defaultdict
import json

from utils.confidence_utils import format_confidence_fields

logger = logging.getLogger(__name__)

class SignalConvergenceEngine:
    """Aggregates and analyzes signals from multiple data sources to identify convergence trades."""
    
    def __init__(self):
        # Source reliability weights (higher = more reliable)
        self.source_weights = {
            'corporate_investment': 0.9,    # Highest confidence - real money commitments
            'insider_trading': 0.8,         # High confidence - Form 4 buys by executives
            'politician_trading': 0.7,      # Medium-high - politicians' industry bets
            'kalshi_predictions': 0.6       # Medium - crowd wisdom, validation layer
        }
        
        # Convergence multipliers - exponential boost when sources align
        self.convergence_multipliers = {
            1: 1.0,    # Single source = base confidence
            2: 1.8,    # 2 sources align = 80% boost
            3: 2.7,    # 3 sources align = 170% boost  
            4: 3.8     # 4 sources align = 280% boost (maximum convergence)
        }
        
        # Signal storage organized by ticker/sector
        self.signals_by_ticker = defaultdict(list)
        self.signals_by_sector = defaultdict(list)
        self.signals_by_region = defaultdict(list)
        
    def add_signal(self, signal: Dict[str, Any]) -> None:
        """Add a signal from any data source to the convergence engine.
        
        Args:
            signal: Signal data with source, ticker, sector, confidence, etc.
        """
        
        required_fields = ['source', 'ticker', 'confidence', 'timestamp']
        if not all(field in signal for field in required_fields):
            logger.warning(f"Signal missing required fields: {signal}")
            return

        try:
            conf = float(signal.get("confidence") or 0)
        except (TypeError, ValueError):
            conf = 0.0
        # Skip zero-confidence junk (especially Kalshi flood of 0.0% markets)
        if conf <= 0:
            logger.debug(
                "Skipping %s signal for %s — confidence %.3f",
                signal.get("source"),
                signal.get("ticker"),
                conf,
            )
            return
        
        # Normalize signal data
        normalized_signal = {
            'id': f"{signal['source']}_{signal['ticker']}_{signal.get('timestamp', datetime.now().isoformat())}",
            'source': signal['source'],
            'ticker': signal['ticker'],
            'sector': signal.get('sector', self._infer_sector(signal['ticker'])),
            'region': signal.get('region', 'GLOBAL'),
            'confidence': signal['confidence'],
            'source_weight': self.source_weights.get(signal['source'], 0.5),
            'weighted_confidence': signal['confidence'] * self.source_weights.get(signal['source'], 0.5),
            'timestamp': signal.get('timestamp', datetime.now().isoformat()),
            'details': signal.get('details', {}),
            'action': signal.get('action', 'BUY'),
            'position_size': signal.get('position_size', 1000)
        }
        
        # Store signals by different dimensions
        self.signals_by_ticker[normalized_signal['ticker']].append(normalized_signal)
        if normalized_signal['sector']:
            self.signals_by_sector[normalized_signal['sector']].append(normalized_signal)
        if normalized_signal['region'] != 'GLOBAL':
            self.signals_by_region[normalized_signal['region']].append(normalized_signal)
        
        logger.info(f"📊 Added {normalized_signal['source']} signal for {normalized_signal['ticker']} (confidence: {normalized_signal['weighted_confidence']:.1%})")
    
    def find_convergence_opportunities(self, min_sources: int = 2, max_age_days: int = 30) -> List[Dict[str, Any]]:
        """Find high-confidence opportunities where multiple sources align.
        
        Args:
            min_sources: Minimum number of independent sources required
            max_age_days: Maximum age of signals to consider
            
        Returns:
            List of convergence opportunities with combined confidence scores
        """
        
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        convergence_opportunities = []
        
        # Check ticker-level convergence (highest confidence)
        for ticker, signals in self.signals_by_ticker.items():
            recent_signals = [s for s in signals if datetime.fromisoformat(s['timestamp']) > cutoff_date]
            
            if len(recent_signals) >= min_sources:
                convergence = self._analyze_convergence(recent_signals, 'ticker', ticker)
                if convergence:
                    convergence_opportunities.append(convergence)
        
        # Check sector-level convergence (medium confidence)
        for sector, signals in self.signals_by_sector.items():
            recent_signals = [s for s in signals if datetime.fromisoformat(s['timestamp']) > cutoff_date]
            
            if len(recent_signals) >= min_sources:
                convergence = self._analyze_convergence(recent_signals, 'sector', sector)
                if convergence:
                    convergence_opportunities.append(convergence)
        
        # Check region-level convergence (lower confidence but still valuable)
        for region, signals in self.signals_by_region.items():
            recent_signals = [s for s in signals if datetime.fromisoformat(s['timestamp']) > cutoff_date]
            
            if len(recent_signals) >= min_sources:
                convergence = self._analyze_convergence(recent_signals, 'region', region)
                if convergence:
                    convergence_opportunities.append(convergence)
        
        # Sort by convergence score (highest first)
        convergence_opportunities.sort(key=lambda x: x['convergence_score'], reverse=True)
        
        logger.info(f"🎯 Found {len(convergence_opportunities)} convergence opportunities with {min_sources}+ aligned sources")
        return convergence_opportunities
    
    def _analyze_convergence(self, signals: List[Dict[str, Any]], convergence_type: str, target: str) -> Optional[Dict[str, Any]]:
        """Analyze a group of signals for convergence strength and generate unified opportunity.
        
        Args:
            signals: List of aligned signals
            convergence_type: 'ticker', 'sector', or 'region'
            target: Specific ticker, sector, or region
            
        Returns:
            Convergence opportunity analysis or None
        """
        
        # Group signals by source to ensure independence
        sources = set(s['source'] for s in signals)
        unique_sources = len(sources)
        
        if unique_sources < 2:
            return None  # Need multiple independent sources
        
        # Calculate convergence metrics
        total_weighted_confidence = sum(s['weighted_confidence'] for s in signals)
        avg_confidence = total_weighted_confidence / len(signals)
        
        # Apply convergence multiplier
        convergence_multiplier = self.convergence_multipliers.get(min(unique_sources, 4), 1.0)
        convergence_score = avg_confidence * convergence_multiplier
        
        # Cap at 100%
        convergence_score = min(convergence_score, 1.0)
        conf_fields = format_confidence_fields(convergence_score)
        
        # Analyze signal alignment and consistency
        actions = [s['action'] for s in signals]
        action_consensus = max(set(actions), key=actions.count) if actions else 'BUY'
        action_agreement = actions.count(action_consensus) / len(actions) if actions else 0
        
        # Determine opportunity type based on convergence
        if convergence_type == 'ticker':
            opportunity_type = 'DIRECT_TICKER_OPPORTUNITY'
            primary_ticker = target
        elif convergence_type == 'sector':
            opportunity_type = 'SECTOR_WIDE_OPPORTUNITY'
            primary_ticker = self._get_best_ticker_for_sector(signals)
        else:  # region
            opportunity_type = 'REGIONAL_OPPORTUNITY'
            primary_ticker = self._get_best_ticker_for_region(signals)
        
        # Create convergence analysis
        convergence_opportunity = {
            'id': f"convergence_{convergence_type}_{target}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'convergence_type': convergence_type,
            'target': target,
            'opportunity_type': opportunity_type,
            'primary_ticker': primary_ticker,
            'convergence_score': convergence_score,
            'raw_score': conf_fields['raw_score'],
            'confidence_pct': conf_fields['confidence_pct'],
            'confidence_label': conf_fields['confidence_label'],
            'unique_sources': unique_sources,
            'total_signals': len(signals),
            'action_consensus': action_consensus,
            'action_agreement': action_agreement,
            'avg_signal_confidence': avg_confidence,
            'convergence_multiplier': convergence_multiplier,
            'sources_involved': list(sources),
            'signals': signals,
            'investment_thesis': self._generate_convergence_thesis(signals, convergence_type, target),
            'risk_factors': self._assess_convergence_risks(signals),
            'recommended_position_size': self._calculate_convergence_position_size(convergence_score, signals),
            'confidence_level': self._get_confidence_level(convergence_score),
            'timestamp': datetime.now().isoformat()
        }
        
        return convergence_opportunity
    
    def _generate_convergence_thesis(self, signals: List[Dict[str, Any]], convergence_type: str, target: str) -> str:
        """Generate investment thesis explaining why multiple sources align."""
        
        source_descriptions = {
            'corporate_investment': 'Corporate investment commitments',
            'insider_trading': 'Insider trading activity',
            'politician_trading': 'Politician trading patterns',
            'kalshi_predictions': 'Prediction market consensus'
        }
        
        involved_sources = [source_descriptions.get(s['source'], s['source']) for s in signals]
        unique_sources = list(set(involved_sources))
        
        if convergence_type == 'ticker':
            thesis = f"Multiple independent sources ({', '.join(unique_sources)}) all indicate bullish sentiment for {target}"
        elif convergence_type == 'sector':
            thesis = f"Cross-source convergence on {target} sector with {len(unique_sources)} independent data sources showing alignment"
        else:
            thesis = f"Regional convergence in {target} with validation from {len(unique_sources)} independent sources"
        
        # Add specific details from highest confidence signals
        top_signals = sorted(signals, key=lambda x: x['weighted_confidence'], reverse=True)[:2]
        for signal in top_signals:
            if signal['source'] == 'corporate_investment' and 'investment_thesis' in signal.get('details', {}):
                thesis += f". Corporate catalyst: {signal['details']['investment_thesis'][:80]}..."
                break
            elif signal['source'] == 'insider_trading' and 'insider_name' in signal.get('details', {}):
                thesis += f". Insider validation: {signal['details']['insider_name']} position"
                break
        
        return thesis
    
    def _assess_convergence_risks(self, signals: List[Dict[str, Any]]) -> List[str]:
        """Assess risks specific to convergence opportunities."""
        
        risks = []
        
        # Check if signals are too clustered in time (potential herd behavior)
        timestamps = [datetime.fromisoformat(s['timestamp']) for s in signals]
        if max(timestamps) - min(timestamps) < timedelta(days=7):
            risks.append("Signals clustered in short timeframe - potential herd behavior")
        
        # Check source diversity
        sources = set(s['source'] for s in signals)
        if len(sources) == 2 and 'kalshi_predictions' in sources:
            risks.append("Limited source diversity - validation from additional sources preferred")
        
        # Check action agreement
        actions = [s['action'] for s in signals]
        if len(set(actions)) > 1:
            risks.append("Mixed directional signals across sources - reduces conviction")
        
        return risks
    
    def _calculate_convergence_position_size(self, convergence_score: float, signals: List[Dict[str, Any]]) -> int:
        """Calculate recommended position size based on convergence strength."""
        
        base_position = 2000  # Base position for convergence trades
        
        # Scale by convergence score (0.5 to 1.0 = 1x to 2x position)
        score_multiplier = 0.5 + (convergence_score * 1.5)
        
        # Additional boost for more sources
        source_boost = 1.0 + (len(set(s['source'] for s in signals)) - 2) * 0.2
        
        position_size = int(base_position * score_multiplier * source_boost)
        
        # Cap at reasonable maximum
        return min(position_size, 10000)
    
    def _get_confidence_level(self, convergence_score: float) -> str:
        """Convert convergence score to confidence level."""
        
        if convergence_score >= 0.85:
            return 'VERY_HIGH'
        elif convergence_score >= 0.70:
            return 'HIGH'
        elif convergence_score >= 0.55:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _infer_sector(self, ticker: str) -> str:
        """Infer sector from ticker based on common knowledge."""
        
        sector_mapping = {
            'AAPL': 'TECHNOLOGY', 'MSFT': 'TECHNOLOGY', 'GOOGL': 'TECHNOLOGY', 'META': 'TECHNOLOGY',
            'NVDA': 'TECHNOLOGY', 'AMD': 'TECHNOLOGY', 'INTC': 'TECHNOLOGY', 'CSCO': 'TECHNOLOGY',
            'AMZN': 'CONSUMER_DISCRETIONARY', 'TSLA': 'CONSUMER_DISCRETIONARY', 'NFLX': 'CONSUMER_DISCRETIONARY',
            'JPM': 'FINANCIALS', 'BAC': 'FINANCIALS', 'WFC': 'FINANCIALS', 'GS': 'FINANCIALS',
            'JNJ': 'HEALTHCARE', 'PFE': 'HEALTHCARE', 'UNH': 'HEALTHCARE', 'ABT': 'HEALTHCARE',
            'XOM': 'ENERGY', 'CVX': 'ENERGY', 'COP': 'ENERGY', 'SLB': 'ENERGY',
            'BA': 'INDUSTRIALS', 'CAT': 'INDUSTRIALS', 'GE': 'INDUSTRIALS', 'MMM': 'INDUSTRIALS'
        }
        
        from utils.company_resolver import get_resolver
        mapped = sector_mapping.get(ticker.upper())
        if mapped:
            return mapped
        return get_resolver().sector(ticker)
    
    def _get_best_ticker_for_sector(self, signals: List[Dict[str, Any]]) -> str:
        """Get the most representative ticker for a sector convergence."""
        
        # Return ticker with highest weighted confidence
        best_signal = max(signals, key=lambda x: x['weighted_confidence'])
        return best_signal['ticker']
    
    def _get_best_ticker_for_region(self, signals: List[Dict[str, Any]]) -> str:
        """Get the most representative ticker for a regional convergence."""
        
        # Prioritize corporate investment signals for regional plays
        investment_signals = [s for s in signals if s['source'] == 'corporate_investment']
        if investment_signals:
            return investment_signals[0]['ticker']
        
        # Otherwise return highest confidence signal
        best_signal = max(signals, key=lambda x: x['weighted_confidence'])
        return best_signal['ticker']
    
    def get_convergence_summary(self) -> Dict[str, Any]:
        """Get summary of current convergence landscape."""
        
        total_signals = sum(len(signals) for signals in self.signals_by_ticker.values())
        
        # Count signals by source
        source_counts = defaultdict(int)
        for signals in self.signals_by_ticker.values():
            for signal in signals:
                source_counts[signal['source']] += 1
        
        # Find convergence opportunities
        convergence_opps = self.find_convergence_opportunities(min_sources=2)
        
        summary = {
            'total_signals': total_signals,
            'signals_by_source': dict(source_counts),
            'tickers_with_signals': len(self.signals_by_ticker),
            'sectors_with_signals': len(self.signals_by_sector),
            'regions_with_signals': len(self.signals_by_region),
            'convergence_opportunities': len(convergence_opps),
            'high_confidence_convergences': len([opp for opp in convergence_opps if opp['convergence_score'] >= 0.8]),
            'timestamp': datetime.now().isoformat()
        }
        
        return summary

# Test function with sample convergence scenarios
def test_signal_convergence():
    """Test the convergence engine with sample multi-source scenarios."""
    
    print("🔀 TESTING MULTI-SOURCE SIGNAL CONVERGENCE ENGINE")
    print("=" * 70)
    
    engine = SignalConvergenceEngine()
    
    # Scenario 1: Tech sector convergence - Microsoft gets multiple signals
    print("\n📊 SCENARIO 1: Microsoft Tech Convergence")
    
    # Corporate investment signal
    engine.add_signal({
        'source': 'corporate_investment',
        'ticker': 'MSFT',
        'confidence': 0.85,
        'action': 'BUY_CALL',
        'position_size': 1500,
        'sector': 'TECHNOLOGY',
        'region': 'INDIA',
        'timestamp': (datetime.now() - timedelta(hours=2)).isoformat(),
        'details': {
            'investment_amount': 17.5,
            'investment_thesis': 'Microsoft investing $17.5B in India for data centers due to regulatory compliance'
        }
    })
    
    # Insider trading signal
    engine.add_signal({
        'source': 'insider_trading',
        'ticker': 'MSFT',
        'confidence': 0.75,
        'action': 'BUY_CALL',
        'position_size': 2000,
        'sector': 'TECHNOLOGY',
        'timestamp': (datetime.now() - timedelta(hours=3)).isoformat(),
        'details': {
            'insider_name': 'Satya Nadella',
            'transaction_type': 'BUY',
            'amount': '$500,000'
        }
    })
    
    # Kalshi prediction signal
    engine.add_signal({
        'source': 'kalshi_predictions',
        'ticker': 'MSFT',
        'confidence': 0.70,
        'action': 'BUY_CALL',
        'position_size': 1000,
        'sector': 'TECHNOLOGY',
        'timestamp': (datetime.now() - timedelta(hours=4)).isoformat(),
        'details': {
            'prediction_type': 'cloud_growth',
            'market_probability': 0.76
        }
    })
    
    # Scenario 2: Indian infrastructure convergence
    print("\n📊 SCENARIO 2: Indian Infrastructure Convergence")
    
    # Amazon corporate investment
    engine.add_signal({
        'source': 'corporate_investment',
        'ticker': 'AMZN',
        'confidence': 0.90,
        'action': 'BUY_CALL',
        'position_size': 1500,
        'sector': 'CONSUMER_DISCRETIONARY',
        'region': 'INDIA',
        'timestamp': (datetime.now() - timedelta(hours=1)).isoformat(),
        'details': {
            'investment_amount': 35.0,
            'investment_thesis': 'Amazon investing $35B in India for logistics and data centers'
        }
    })
    
    # Construction company signal (ripple effect)
    engine.add_signal({
        'source': 'corporate_investment',
        'ticker': 'LT',  # Larsen & Toubro - Indian construction
        'confidence': 0.80,
        'action': 'BUY_CALL',
        'position_size': 2250,
        'sector': 'INDUSTRIALS',
        'region': 'INDIA',
        'timestamp': (datetime.now() - timedelta(minutes=30)).isoformat(),
        'details': {
            'ripple_effect': 'construction_infrastructure',
            'catalyst': 'Amazon $35B India investment'
        }
    })
    
    # Regional ETF signal
    engine.add_signal({
        'source': 'insider_trading',
        'ticker': 'INDA',  # India ETF
        'confidence': 0.65,
        'action': 'BUY_CALL',
        'position_size': 1500,
        'sector': 'ETF',
        'region': 'INDIA',
        'timestamp': (datetime.now() - timedelta(hours=1, minutes=15)).isoformat(),
        'details': {
            'insider_name': 'Multiple Fund Managers',
            'trend': 'Emerging market inflows'
        }
    })
    
    # Find convergence opportunities
    convergence_opps = engine.find_convergence_opportunities(min_sources=2)
    
    print(f"\n🎯 CONVERGENCE OPPORTUNITIES FOUND: {len(convergence_opps)}")
    
    for i, opp in enumerate(convergence_opps, 1):
        print(f"\n📈 OPPORTUNITY {i}: {opp['opportunity_type']}")
        print(f"   🎯 Target: {opp['target']}")
        print(f"   📊 Convergence Score: {opp['convergence_score']:.1%}")
        print(f"   🏆 Confidence Level: {opp['confidence_level']}")
        print(f"   🔗 Sources: {opp['unique_sources']} unique ({', '.join(opp['sources_involved'])})")
        print(f"   💡 Thesis: {opp['investment_thesis'][:100]}...")
        print(f"   📊 Recommended Position: ${opp['recommended_position_size']:,}")
        print(f"   ⚠️  Risks: {len(opp['risk_factors'])} factors")
        
        if opp['risk_factors']:
            print(f"   🚨 Risk Details:")
            for risk in opp['risk_factors']:
                print(f"      • {risk}")
    
    # Show convergence summary
    summary = engine.get_convergence_summary()
    print(f"\n📊 CONVERGENCE SUMMARY:")
    print(f"   Total Signals: {summary['total_signals']}")
    print(f"   Signals by Source: {summary['signals_by_source']}")
    print(f"   Convergence Opportunities: {summary['convergence_opportunities']}")
    print(f"   High Confidence Convergences: {summary['high_confidence_convergences']}")
    
    print(f"\n🎉 SIGNAL CONVERGENCE TEST COMPLETE")
    return True

if __name__ == "__main__":
    test_signal_convergence()
