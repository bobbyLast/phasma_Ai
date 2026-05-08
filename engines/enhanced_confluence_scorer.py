"""
Enhanced Confluence Scorer - Upgrade to existing unified brain

Adds evidence-based scoring without replacing existing logic
"""

from typing import Dict, List
import numpy as np


class EnhancedConfluenceScorer:
    """Adds confluence scoring to existing opportunities"""
    
    def __init__(self):
        self.weights = {
            'macro_alignment': 0.25,
            'value_alignment': 0.25,
            'technical_confirmation': 0.30,
            'news_catalyst': 0.20
        }
    
    def score_opportunity(self, opportunity: Dict, context: Dict) -> Dict:
        """Add confluence score to existing opportunity"""
        
        scores = {}
        
        # 1. Macro alignment (use existing global_macro_monitor)
        if context.get('macro_regime') == 'RISK_ON':
            scores['macro_alignment'] = 0.8 if opportunity.get('action') == 'BUY' else 0.2
        elif context.get('macro_regime') == 'RISK_OFF':
            scores['macro_alignment'] = 0.2 if opportunity.get('action') == 'BUY' else 0.8
        else:
            scores['macro_alignment'] = 0.5
        
        # 2. Value alignment (check if under $50 and has room to grow)
        price = opportunity.get('entry_price', 0)
        target = opportunity.get('target_price', 0)
        
        if 0 < price < 50 and target > price * 1.1:
            scores['value_alignment'] = 0.8
        elif price < 10:
            scores['value_alignment'] = 0.6  # Penny stocks get bonus
        else:
            scores['value_alignment'] = 0.5
        
        # 3. Technical confirmation (use existing patterns)
        patterns = opportunity.get('patterns', [])
        if any(p in ['breakout', 'oversold', 'divergence'] for p in patterns):
            scores['technical_confirmation'] = 0.8
        elif patterns:
            scores['technical_confirmation'] = 0.6
        else:
            scores['technical_confirmation'] = 0.4
        
        # 4. News catalyst (use existing news data)
        if opportunity.get('news_items'):
            scores['news_catalyst'] = 0.7
        else:
            scores['news_catalyst'] = 0.3
        
        # Calculate weighted confluence score
        confluence_score = sum(scores[k] * self.weights[k] for k in scores)
        
        # Add to opportunity without changing existing structure
        opportunity['confluence_score'] = confluence_score * 100
        opportunity['confluence_breakdown'] = scores
        
        return opportunity
    
    def filter_high_conviction(self, opportunities: List[Dict], min_score: float = 70) -> List[Dict]:
        """Filter for high confluence opportunities"""
        return [opp for opp in opportunities if opp.get('confluence_score', 0) >= min_score]
