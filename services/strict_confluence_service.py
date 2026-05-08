#!/usr/bin/env python3
"""
PHASMA AI - Enhanced Confluence Service with Strict Reality Validation
Only processes verified ground truth data - no exceptions
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
import asyncio

# Import strict reality components
from utils.strict_reality_architecture import StrictRealityValidator, ValidationResult
from utils.ground_truth_data_cache import GroundTruthDataCache

logger = logging.getLogger(__name__)

@dataclass
class ConfluenceResult:
    """Result from confluence analysis with ground truth verification"""
    ticker: str
    score: float
    confidence: str
    reasoning: str
    sub_scores: Dict[str, float]
    signals: Dict[str, List]
    evidence_items: List[Dict]
    risk_flags: List[str]
    ground_truth_verified: bool
    validation_failures: List[str]

class StrictConfluenceService:
    """Confluence service that only processes verified ground truth data"""
    
    def __init__(self, config):
        self.config = config
        self.validator = StrictRealityValidator()
        self.cache = GroundTruthDataCache()
        
        # Budget filter
        trading_budget = getattr(config, 'trading_budget', config.get('trading_budget', {}))
        self.max_price_per_share = trading_budget.get('max_price_per_share', 1000)  # Updated to $1000
        
        # Strategy configuration
        self.strategies = config.get('strategies', {})
        self.active_strategy_name = self.strategies.get('active_strategy', 'balanced')
        self.active_strategy = self.strategies.get(self.active_strategy_name, {})
        
        # Validation thresholds
        self.validation_config = {
            'max_price_per_share': self.max_price_per_share,
            'min_volume': 100,
            'max_spread_pct': 5.0,  # 5% max bid-ask spread
            'max_age_minutes': 15,  # Data must be fresh
            'verified_sources': {
                'alpaca', 'sec_edgar', 'finnhub', 'alpha_vantage', 
                'polygon', 'iex', 'yahoo', 'openinsider'
            }
        }
        
        logger.info(f"Strict Confluence Service initialized")
        logger.info(f"Max price per share: ${self.max_price_per_share}")
        logger.info(f"Only verified sources: {self.validation_config['verified_sources']}")
    
    async def calculate_confluence(self, ticker: str, signals: Dict[str, List]) -> Optional[ConfluenceResult]:
        """Calculate confluence score with strict validation"""
        validation_failures = []
        
        # 1. Validate ticker and get current price
        price_data = await self._get_validated_price(ticker)
        if not price_data:
            validation_failures.append(f"No valid price data for {ticker}")
            return None
        
        # 2. Check budget filter
        if price_data['price'] > self.max_price_per_share:
            validation_failures.append(f"Price ${price_data['price']:.2f} exceeds budget ${self.max_price_per_share}")
            return None
        
        # 3. Validate all signals
        validated_signals = {}
        for source, signal_list in signals.items():
            validated = []
            for signal in signal_list:
                validation = self.validator.validate_signal(signal)
                if validation.is_valid:
                    validated.append(validation.data)
                else:
                    validation_failures.append(f"Invalid signal from {source}: {validation.reason}")
            
            if validated:
                validated_signals[source] = validated
        
        if not validated_signals:
            validation_failures.append("No valid signals after validation")
            return None
        
        # 4. Calculate confluence score
        score, sub_scores = self._calculate_confluence_score(validated_signals)
        
        # 5. Generate reasoning
        reasoning = self._generate_reasoning(validated_signals, sub_scores, validation_failures)
        
        # 6. Collect evidence
        evidence_items = self._collect_evidence(validated_signals, price_data)
        
        # 7. Check risk flags
        risk_flags = self._check_risk_flags(validated_signals, price_data)
        
        # 8. Determine confidence level
        confidence = self._determine_confidence(score, len(validated_signals), validation_failures)
        
        return ConfluenceResult(
            ticker=ticker,
            score=score,
            confidence=confidence,
            reasoning=reasoning,
            sub_scores=sub_scores,
            signals=validated_signals,
            evidence_items=evidence_items,
            risk_flags=risk_flags,
            ground_truth_verified=len(validation_failures) == 0,
            validation_failures=validation_failures
        )
    
    async def _get_validated_price(self, ticker: str) -> Optional[Dict]:
        """Get validated price data"""
        # Try cache first
        cached = self.cache.get_price(ticker, max_age_minutes=5)
        if cached:
            validation = self.validator.validate_price_data(cached)
            if validation.is_valid:
                return validation.data
        
        # Get fresh data (would use ground_truth_provider in real implementation)
        logger.warning(f"Need fresh price for {ticker} - implement ground truth provider")
        return None
    
    def _calculate_confluence_score(self, signals: Dict[str, List]) -> Tuple[float, Dict[str, float]]:
        """Calculate confluence score from validated signals"""
        sub_scores = {}
        total_weight = 0
        weighted_score = 0
        
        # Source weights
        weights = {
            'insider': 0.35,
            'institutional': 0.25,
            'news': 0.20,
            'social': 0.10,
            'options': 0.10
        }
        
        for source, signal_list in signals.items():
            if not signal_list:
                continue
            
            # Calculate average confidence for this source
            avg_confidence = sum(s.get('confidence', 0) for s in signal_list) / len(signal_list)
            
            # Apply weight
            weight = weights.get(source, 0.1)
            weighted_score += avg_confidence * weight
            total_weight += weight
            
            sub_scores[source] = avg_confidence
        
        # Normalize score
        final_score = weighted_score / total_weight if total_weight > 0 else 0
        
        # Apply confluence bonus for multiple sources
        source_count = len([s for s in signals.values() if s])
        if source_count >= 3:
            final_score *= 1.3  # 30% bonus for 3+ sources
        elif source_count >= 2:
            final_score *= 1.15  # 15% bonus for 2 sources
        
        return min(final_score, 1.0), sub_scores
    
    def _generate_reasoning(self, signals: Dict[str, List], sub_scores: Dict[str, float], 
                          failures: List[str]) -> str:
        """Generate reasoning for the confluence score"""
        reasons = []
        
        # Positive signals
        for source, score in sub_scores.items():
            if score > 0.7:
                reasons.append(f"Strong {source} signals ({score:.1%})")
            elif score > 0.5:
                reasons.append(f"Moderate {source} signals ({score:.1%})")
        
        # Source count
        source_count = len([s for s in signals.values() if s])
        if source_count >= 3:
            reasons.append(f"High convergence across {source_count} sources")
        elif source_count >= 2:
            reasons.append(f"Convergence across {source_count} sources")
        
        # Validation failures
        if failures:
            reasons.append(f"Note: {len(failures)} signals filtered out")
        
        return "; ".join(reasons) if reasons else "Insufficient validated signals"
    
    def _collect_evidence(self, signals: Dict[str, List], price_data: Dict) -> List[Dict]:
        """Collect evidence items from validated signals"""
        evidence = []
        
        # Add price data as evidence
        evidence.append({
            'type': 'price',
            'value': price_data['price'],
            'source': price_data['source'],
            'timestamp': price_data['timestamp'],
            'verified': True
        })
        
        # Add signal evidence
        for source, signal_list in signals.items():
            for signal in signal_list[:3]:  # Limit to top 3 per source
                evidence.append({
                    'type': source,
                    'confidence': signal.get('confidence', 0),
                    'rationale': signal.get('rationale', ''),
                    'timestamp': signal.get('timestamp', ''),
                    'verified': True
                })
        
        return evidence
    
    def _check_risk_flags(self, signals: Dict[str, List], price_data: Dict) -> List[str]:
        """Check for risk flags"""
        flags = []
        
        # Low volume flag
        volume = price_data.get('volume', 0)
        if volume < self.validation_config['min_volume']:
            flags.append(f"Low volume: {volume:,}")
        
        # Stale data flag
        timestamp = price_data.get('timestamp')
        if timestamp:
            try:
                ts = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                if datetime.now() - ts > timedelta(minutes=self.validation_config['max_age_minutes']):
                    flags.append("Stale price data")
            except:
                flags.append("Invalid timestamp")
        
        # Spread check (if available)
        spread = price_data.get('spread_pct', 0)
        if spread > self.validation_config['max_spread_pct']:
            flags.append(f"Wide spread: {spread:.1f}%")
        
        return flags
    
    def _determine_confidence(self, score: float, source_count: int, failures: List[str]) -> str:
        """Determine confidence level"""
        if failures:
            return "LOW" if len(failures) > 2 else "MEDIUM"
        
        if score >= 0.8 and source_count >= 3:
            return "HIGH"
        elif score >= 0.6 and source_count >= 2:
            return "MEDIUM"
        else:
            return "LOW"
    
    def validate_signal_batch(self, signals: List[Dict]) -> Tuple[List[Dict], List[str]]:
        """Validate a batch of signals"""
        validated = []
        failures = []
        
        for signal in signals:
            validation = self.validator.validate_signal(signal)
            if validation.is_valid:
                validated.append(validation.data)
            else:
                failures.append(f"{signal.get('symbol', 'Unknown')}: {validation.reason}")
        
        return validated, failures
    
    def get_validation_summary(self) -> Dict:
        """Get summary of validation rules"""
        return {
            'verified_sources': list(self.validation_config['verified_sources']),
            'max_price_per_share': self.max_price_per_share,
            'min_volume': self.validation_config['min_volume'],
            'max_spread_pct': self.validation_config['max_spread_pct'],
            'max_age_minutes': self.validation_config['max_age_minutes'],
            'strict_mode': True,
            'ground_truth_only': True
        }

# Factory function
def create_strict_confluence_service(config) -> StrictConfluenceService:
    """Create confluence service with strict validation"""
    return StrictConfluenceService(config)
