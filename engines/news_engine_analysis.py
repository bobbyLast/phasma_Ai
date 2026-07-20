"""
News Engine Analysis Module
Pattern detection and technical analysis
"""

import os
import re
from typing import List, Dict, Any, Tuple

class NewsAnalyzer:
    """Technical analysis and pattern detection for news"""

    def __init__(self, config):
        self.config = config
        
        # Keywords for detecting partnerships and contracts
        self.PARTNERSHIP_KEYWORDS = [
            "partners with", "teams up with", "collaborates with",
            "strategic alliance", "joins forces with", "partnership with",
            "NVDA and PLTR", "NVIDIA and Palantir", "collaboration between",
            "teaming up with", "announces partnership"
        ]
        
        self.CONTRACT_KEYWORDS = [
            "government contract", "defense contract", r"\$[0-9.]+ billion deal",
            "awarded contract", "secures deal", "wins contract", 
            "DOJ", "defense department", "government deal", "military contract",
            "federal contract", "awarded by"
        ]
        
        # Known company pairs for partnership detection
        self.KNOWN_PAIRS = [
            ("NVDA", "PLTR"), ("NVIDIA", "Palantir"),
            ("AMD", "USGOV"), ("Advanced Micro Devices", "U.S. Government"),
            ("AMD", "DoD"), ("AMD", "Department of Defense")
        ]

    def calculate_layered_divergence(self, news_item: Dict) -> Dict:
        """Calculate layered divergence analysis based on real sentiment"""
        title = news_item.get('title', '')
        sentiment = news_item.get('sentiment', 0)

        # Technical divergence based on sentiment strength (deterministic)
        title_hash = sum(ord(c) for c in title[:40]) % 21
        technical_divergence = sentiment * 0.3 + (title_hash - 10) / 100.0

        # Sentiment divergence based on catalyst score
        catalyst_score = news_item.get('catalyst_score', 0)
        sentiment_divergence = sentiment * 0.4 + catalyst_score * 0.2

        # Overall divergence score
        divergence_score = (sentiment + catalyst_score) / 2

        return {
            'divergence_score': max(0.1, min(1.0, divergence_score)),
            'technical_divergence': max(-1.0, min(1.0, technical_divergence)),
            'sentiment_divergence': max(-1.0, min(1.0, sentiment_divergence)),
            'overall_bias': 'BULLISH' if divergence_score > 0.5 else 'BEARISH',
            'confidence': max(0.1, min(1.0, divergence_score))
        }

    def detect_partnerships_and_contracts(self, news_item: Dict) -> Tuple[List[str], float]:
        """Detect partnership and contract patterns in news"""
        patterns = []
        confidence_boost = 0.0
        
        title = news_item.get('title', '').lower()
        content = news_item.get('content', '').lower()
        
        # Check for partnership patterns
        if any(keyword in title or keyword in content for keyword in self.PARTNERSHIP_KEYWORDS):
            patterns.append('strategic_partnership')
            confidence_boost += 0.3
            
        # Check for contract awards
        if any(re.search(keyword, title) or re.search(keyword, content) for keyword in self.CONTRACT_KEYWORDS):
            patterns.append('government_contract')
            confidence_boost += 0.4
            
        # Check for known company pairs
        for company1, company2 in self.KNOWN_PAIRS:
            if (company1.lower() in title and company2.lower() in title) or \
               (company1.lower() in content and company2.lower() in content):
                patterns.append('high_profile_partnership')
                confidence_boost += 0.5
                break
                
        return patterns, confidence_boost

    def detect_technical_patterns(self, news_items: List[Dict]) -> List[Dict]:
        """Detect technical patterns based on news sentiment and catalysts"""
        pattern_signals = []

        for item in news_items:
            patterns_detected = []
            pattern_strength = 0.3
            technical_bias = 'NEUTRAL'
            
            # Detect partnerships and contracts first
            partnership_patterns, confidence_boost = self.detect_partnerships_and_contracts(item)
            patterns_detected.extend(partnership_patterns)
            pattern_strength += confidence_boost

            # Analyze sentiment for pattern strength
            sentiment = item.get('sentiment', 0)
            catalyst_score = item.get('catalyst_score', 0)

            # Strong positive sentiment = potential breakout
            if sentiment > 0.3 and catalyst_score > 0.5:
                patterns_detected.append('breakout')
                pattern_strength += 0.3

            # High catalyst score = momentum potential
            if catalyst_score > 0.6:
                patterns_detected.append('momentum')
                pattern_strength += 0.2

            # Multiple news sources mentioning same symbol = volume spike
            symbol = item.get('symbol', '')
            symbol_mentions = sum(1 for i in news_items if i.get('symbol') == symbol)
            if symbol_mentions > 1:
                patterns_detected.append('volume_spike')
                pattern_strength += 0.2

            # Check for high-impact catalyst patterns
            title_lower = item.get('title', '').lower()
            content_lower = item.get('content', '').lower()
            
            catalyst_keywords = [
                'breakthrough', 'revolutionary', 'game-changing', 
                'disruptive', 'innovative', 'milestone', 'landmark',
                'transformative', 'pioneering', 'groundbreaking'
            ]
            
            if any(word in title_lower or word in content_lower for word in catalyst_keywords):
                patterns_detected.append('high_impact_catalyst')
                pattern_strength += 0.3  # Slightly higher weight

            # Determine technical bias
            if sentiment > 0.2:
                technical_bias = 'BULLISH'
            elif sentiment < -0.2:
                technical_bias = 'BEARISH'

            # General alignment score based on sentiment and catalysts
            alignment_score = 0.5 + (sentiment * 0.3) + (catalyst_score * 0.2)
            if 'breakout' in patterns_detected:
                alignment_score += 0.1
            if 'momentum' in patterns_detected:
                pattern_strength += 0.1

            pattern_signal = {
                'patterns_detected': patterns_detected,
                'pattern_strength': max(0.1, min(1.0, pattern_strength)),
                'technical_bias': technical_bias,
                'alignment_score': min(1.0, alignment_score),
                'confidence': max(0.1, min(1.0, pattern_strength))
            }

            pattern_signals.append(pattern_signal)

        return pattern_signals

    def calculate_position_size(self, confidence: float, fact_check: Dict, is_moonshot: bool) -> float:
        """Calculate position size based on pattern analysis"""
        base_size = 1000  # Base position size

        # Adjust for confidence
        confidence_multiplier = confidence

        # Adjust for fact check validation
        validation_multiplier = fact_check.get('validation_score', 0.5)

        # Adjust for moonshot potential
        moonshot_multiplier = 2.0 if is_moonshot else 1.0

        # Adjust for risk level
        risk_level = fact_check.get('risk_level', 'MEDIUM')
        risk_multipliers = {
            'LOW': 1.5,
            'MEDIUM': 1.0,
            'HIGH': 0.5
        }
        risk_multiplier = risk_multipliers.get(risk_level, 1.0)

        # Calculate position size (AI tracks all trades for learning)
        position_size = base_size * confidence_multiplier * validation_multiplier * moonshot_multiplier * risk_multiplier

        # Cap position size
        max_size = 10000
        min_size = 100

        return max(min_size, min(max_size, position_size))

    def analyze_sector_trends(self, news_items: List[Dict]) -> Dict[str, Any]:
        """Analyze trends by sector"""
        sector_data = {}

        for item in news_items:
            from utils.company_resolver import get_resolver
            sector = item.get('sector') or get_resolver().sector(item.get('symbol', ''), item.get('title'))
            if sector not in sector_data:
                sector_data[sector] = {
                    'count': 0,
                    'total_sentiment': 0,
                    'total_catalyst': 0,
                    'symbols': set()
                }

            sector_data[sector]['count'] += 1
            sector_data[sector]['total_sentiment'] += item.get('sentiment', 0)
            sector_data[sector]['total_catalyst'] += item.get('catalyst_score', 0)
            sector_data[sector]['symbols'].add(item.get('symbol', ''))

        # Calculate averages and trends
        for sector, data in sector_data.items():
            if data['count'] > 0:
                data['avg_sentiment'] = data['total_sentiment'] / data['count']
                data['avg_catalyst'] = data['total_catalyst'] / data['count']
                data['unique_symbols'] = len(data['symbols'])
                data['trend'] = 'BULLISH' if data['avg_sentiment'] > 0.2 else 'BEARISH' if data['avg_sentiment'] < -0.2 else 'NEUTRAL'

        return sector_data

    def identify_moonshot_opportunities(self, news_items: List[Dict]) -> List[Dict[str, Any]]:
        """Identify potential moonshot opportunities"""
        moonshots = []

        for item in news_items:
            catalyst_score = item.get('catalyst_score', 0)
            sentiment = item.get('sentiment', 0)

            # Moonshot criteria
            is_potential_moonshot = (
                catalyst_score > 0.7 and  # High catalyst score
                sentiment > 0.4           # Strong positive sentiment
            )

            if is_potential_moonshot:
                item['is_moonshot'] = True
                item['moonshot_score'] = (catalyst_score + sentiment) / 2
                moonshots.append(item)

        # Sort by moonshot score
        moonshots.sort(key=lambda x: x.get('moonshot_score', 0), reverse=True)

        return moonshots
