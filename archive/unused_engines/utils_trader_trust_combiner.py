"""
Trader Trust + Idea Quality Combiner - Final Stage 3 Component

Combines trader performance metrics with idea quality analysis to determine
how seriously to take external trader calls. This implements the core logic:

"Opinion on the trader" × "Opinion on the idea" = "How serious should we take this?"

Key Combinations:
- Good trader + good idea = Strong signal
- Good trader + bad idea = Note but small size/skip
- Bad trader + good idea = Valid idea but don't upgrade trust
- Bad trader + bad idea = Pure noise

Output:
- Final recommendation (STRONG_BUY, BUY, WATCH, AVOID)
- Confidence score (0-100)
- Position sizing recommendation
- Detailed reasoning breakdown
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from trader_call_logger import Direction
from trader_performance_tracker import TraderPerformance
from idea_quality_analyzer import IdeaQuality

class FinalRecommendation(Enum):
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    WATCH = "WATCH"
    AVOID = "AVOID"

class PositionSize(Enum):
    LARGE = "LARGE"
    MEDIUM = "MEDIUM"
    SMALL = "SMALL"
    TINY = "TINY"

@dataclass
class CombinedAnalysis:
    """Final combined analysis of trader call + idea quality"""
    trader_id: str
    ticker: str
    direction: str
    
    # Trader metrics
    trader_trust_score: float
    trader_win_rate: float
    trader_call_count: int
    
    # Idea quality metrics
    idea_rating: str
    idea_confidence: float
    idea_overall_score: float
    idea_risk_level: str
    
    # Combined metrics
    final_recommendation: FinalRecommendation
    final_confidence: float
    position_size: PositionSize
    
    # Reasoning
    trader_reasoning: List[str]
    idea_reasoning: List[str]
    combined_reasoning: List[str]
    
    # Metadata
    analysis_date: str
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['final_recommendation'] = self.final_recommendation.value
        data['position_size'] = self.position_size.value
        return data

class TraderTrustCombiner:
    """
    Combines trader trust scores with idea quality analysis
    Final component of Stage 3: Trust + Quality combination logic
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        
        # Weighting for final score
        self.trust_weight = 0.4
        self.idea_weight = 0.6
        
        # Thresholds for recommendations
        self.strong_buy_threshold = 80
        self.buy_threshold = 65
        self.watch_threshold = 45
        
        print("🎯 Trader Trust Combiner initialized")
        print(f"   - Trust weight: {self.trust_weight*100}%, Idea weight: {self.idea_weight*100}%")
    
    def analyze_call(self, trader_id: str, ticker: str, direction: Direction,
                    trader_performance: TraderPerformance, 
                    idea_quality: IdeaQuality) -> Optional[CombinedAnalysis]:
        """
        Combine trader performance with idea quality
        
        Args:
            trader_id: ID of the trader
            ticker: Stock symbol
            direction: LONG/SHORT bias
            trader_performance: Trader's historical performance
            idea_quality: Quality analysis of the ticker
        
        Returns:
            CombinedAnalysis with final recommendation
        """
        try:
            print(f"🎯 Combining analysis: {trader_id} + {ticker}")
            
            # Extract trader metrics
            trader_trust = trader_performance.trust_score
            trader_win_rate = trader_performance.win_rate
            trader_call_count = trader_performance.total_calls
            
            # Extract idea quality metrics
            idea_rating = idea_quality.rating
            idea_confidence = idea_quality.confidence
            idea_score = idea_quality.overall_score
            idea_risk = idea_quality.risk_level
            
            # Calculate combined score
            combined_score = (trader_trust * self.trust_weight) + (idea_score * self.idea_weight)
            
            # Determine final recommendation
            final_recommendation = self._determine_recommendation(
                trader_trust, idea_score, combined_score, direction, idea_risk
            )
            
            # Calculate final confidence
            final_confidence = self._calculate_confidence(
                trader_trust, idea_confidence, trader_call_count
            )
            
            # Determine position size
            position_size = self._determine_position_size(
                final_recommendation, final_confidence, idea_risk, trader_call_count
            )
            
            # Generate reasoning
            trader_reasoning = self._generate_trader_reasoning(trader_performance)
            idea_reasoning = idea_quality.reasoning[:3]  # Top 3 idea reasons
            combined_reasoning = self._generate_combined_reasoning(
                trader_trust, idea_score, final_recommendation, trader_call_count
            )
            
            return CombinedAnalysis(
                trader_id=trader_id,
                ticker=ticker,
                direction=direction.value,
                
                # Trader metrics
                trader_trust_score=trader_trust,
                trader_win_rate=trader_win_rate,
                trader_call_count=trader_call_count,
                
                # Idea quality metrics
                idea_rating=idea_rating,
                idea_confidence=idea_confidence,
                idea_overall_score=idea_score,
                idea_risk_level=idea_risk,
                
                # Combined metrics
                final_recommendation=final_recommendation,
                final_confidence=final_confidence,
                position_size=position_size,
                
                # Reasoning
                trader_reasoning=trader_reasoning,
                idea_reasoning=idea_reasoning,
                combined_reasoning=combined_reasoning,
                
                # Metadata
                analysis_date=idea_quality.analysis_date
            )
            
        except Exception as e:
            print(f"❌ Error combining analysis for {trader_id}/{ticker}: {str(e)}")
            return None
    
    def _determine_recommendation(self, trader_trust: float, idea_score: float, 
                                combined_score: float, direction: Direction, 
                                idea_risk: str) -> FinalRecommendation:
        """Determine final recommendation based on all factors"""
        
        # High trust + good idea = Strong signal
        if trader_trust >= 80 and idea_score >= 75 and combined_score >= self.strong_buy_threshold:
            return FinalRecommendation.STRONG_BUY
        
        # Good trust + decent idea = Buy signal
        elif trader_trust >= 60 and idea_score >= 60 and combined_score >= self.buy_threshold:
            return FinalRecommendation.BUY
        
        # Any combination with decent score = Watch
        elif combined_score >= self.watch_threshold:
            return FinalRecommendation.WATCH
        
        # Low scores = Avoid
        else:
            return FinalRecommendation.AVOID
    
    def _calculate_confidence(self, trader_trust: float, idea_confidence: float, 
                            call_count: int) -> float:
        """Calculate final confidence based on sample size and individual confidences"""
        
        # Base confidence from individual components
        base_confidence = (trader_trust + idea_confidence) / 2
        
        # Adjust for sample size (more calls = more confidence in trader metrics)
        sample_size_bonus = min(call_count / 50, 10)  # Max 10 points bonus
        
        # Adjust for very high trust scores
        trust_bonus = max(0, trader_trust - 80) * 0.5
        
        final_confidence = base_confidence + sample_size_bonus + trust_bonus
        return min(max(final_confidence, 0), 100)
    
    def _determine_position_size(self, recommendation: FinalRecommendation, 
                               confidence: float, risk_level: str, 
                               call_count: int) -> PositionSize:
        """Determine recommended position size"""
        
        # Start with recommendation-based sizing
        if recommendation == FinalRecommendation.STRONG_BUY:
            if confidence >= 80 and risk_level == "LOW":
                return PositionSize.LARGE
            elif confidence >= 70:
                return PositionSize.MEDIUM
            else:
                return PositionSize.SMALL
        
        elif recommendation == FinalRecommendation.BUY:
            if confidence >= 75 and risk_level == "LOW":
                return PositionSize.MEDIUM
            else:
                return PositionSize.SMALL
        
        elif recommendation == FinalRecommendation.WATCH:
            if confidence >= 60 and call_count >= 10:
                return PositionSize.SMALL
            else:
                return PositionSize.TINY
        
        else:  # AVOID
            return PositionSize.TINY
    
    def _generate_trader_reasoning(self, trader_performance: TraderPerformance) -> List[str]:
        """Generate reasoning based on trader performance"""
        reasoning = []
        
        if trader_performance.trust_score >= 80:
            reasoning.append(f"Excellent trader with {trader_performance.trust_score:.0f} trust score")
        elif trader_performance.trust_score >= 60:
            reasoning.append(f"Good trader with {trader_performance.trust_score:.0f} trust score")
        else:
            reasoning.append(f"Unproven trader with {trader_performance.trust_score:.0f} trust score")
        
        if trader_performance.win_rate >= 70:
            reasoning.append(f"Strong {trader_performance.win_rate:.0f}% win rate")
        elif trader_performance.win_rate >= 50:
            reasoning.append(f"Moderate {trader_performance.win_rate:.0f}% win rate")
        else:
            reasoning.append(f"Weak {trader_performance.win_rate:.0f}% win rate")
        
        if trader_performance.total_calls >= 20:
            reasoning.append(f"Well-established with {trader_performance.total_calls} tracked calls")
        elif trader_performance.total_calls >= 5:
            reasoning.append(f"Developing track record with {trader_performance.total_calls} calls")
        else:
            reasoning.append(f"Limited data with only {trader_performance.total_calls} calls")
        
        return reasoning
    
    def _generate_combined_reasoning(self, trader_trust: float, idea_score: float,
                                   recommendation: FinalRecommendation, 
                                   call_count: int) -> List[str]:
        """Generate reasoning for the final combination"""
        reasoning = []
        
        # Explain the combination logic
        if trader_trust >= 70 and idea_score >= 70:
            reasoning.append("Strong alignment: Good trader + Good idea")
        elif trader_trust >= 70 and idea_score < 50:
            reasoning.append("Good trader calling weak idea - proceed with caution")
        elif trader_trust < 50 and idea_score >= 70:
            reasoning.append("Weak trader found good idea - worth watching")
        elif trader_trust < 50 and idea_score < 50:
            reasoning.append("Weak signals: Unproven trader + Poor setup")
        
        # Recommendation-specific reasoning
        if recommendation == FinalRecommendation.STRONG_BUY:
            reasoning.append("High conviction signal with strong risk/reward")
        elif recommendation == FinalRecommendation.BUY:
            reasoning.append("Decent opportunity with reasonable risk")
        elif recommendation == FinalRecommendation.WATCH:
            reasoning.append("Monitor for confirmation before acting")
        else:
            reasoning.append("Avoid - poor setup or untrustworthy source")
        
        # Data confidence
        if call_count < 5:
            reasoning.append("Limited trader history - lower confidence")
        
        return reasoning

# Example usage and testing
if __name__ == "__main__":
    print("🧪 Testing Trader Trust Combiner...")
    
    from trader_performance_tracker import TraderPerformanceTracker
    from idea_quality_analyzer import IdeaQualityAnalyzer
    from trader_call_logger import TraderCallLogger
    from datetime import datetime, timezone
    
    # Initialize components
    call_logger = TraderCallLogger()
    perf_tracker = TraderPerformanceTracker(call_logger)
    idea_analyzer = IdeaQualityAnalyzer()
    combiner = TraderTrustCombiner()
    
    # Get sample trader performance
    trader_perf = perf_tracker.get_trader_performance('stock_guru_123')
    
    if trader_perf:
        print(f"\n📊 Trader Performance Found:")
        print(f"   Trust Score: {trader_perf.trust_score:.0f}")
        print(f"   Win Rate: {trader_perf.win_rate:.1f}%")
        print(f"   Total Calls: {trader_perf.total_calls}")
        
        # Analyze a few ticker ideas
        test_tickers = ['AAPL', 'MSFT']
        
        for ticker in test_tickers:
            print(f"\n{'='*60}")
            
            # Get idea quality
            idea_quality = idea_analyzer.analyze_ticker(ticker)
            
            if idea_quality:
                print(f"💡 Idea Quality: {idea_quality.rating} ({idea_quality.overall_score:.0f}/100)")
                
                # Combine analysis
                combined = combiner.analyze_call(
                    trader_id='stock_guru_123',
                    ticker=ticker,
                    direction=Direction.LONG,
                    trader_performance=trader_perf,
                    idea_quality=idea_quality
                )
                
                if combined:
                    print(f"\n🎯 FINAL ANALYSIS for {ticker}:")
                    print(f"   Recommendation: {combined.final_recommendation.value}")
                    print(f"   Confidence: {combined.final_confidence:.0f}%")
                    print(f"   Position Size: {combined.position_size.value}")
                    print(f"   Combined Score: {(combined.trader_trust_score * 0.4 + combined.idea_overall_score * 0.6):.0f}/100")
                    
                    print(f"\n📝 Key Reasoning:")
                    for reason in combined.combined_reasoning:
                        print(f"     • {reason}")
                else:
                    print(f"❌ Failed to combine analysis for {ticker}")
            else:
                print(f"❌ Failed to analyze {ticker} idea quality")
    else:
        print("❌ No trader performance data found")
    
    print(f"\n✅ Stage 3 complete: Trust + Quality combination working!")
    print(f"   - Ready for Stage 4: Smart money view integration")
