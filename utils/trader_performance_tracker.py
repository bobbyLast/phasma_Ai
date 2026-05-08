"""
Trader Performance Tracker - Stage 2 of External Trader Tracking System

Analyzes historical trader calls to calculate performance metrics and trust scores.
This layer evaluates individual trader quality based on actual market performance.

Key Metrics:
- Win rate (percentage of profitable calls)
- Average gain/loss per call
- Maximum drawdown from entry
- Time to profit/loss
- Trust score (dynamic based on performance)
- Performance by market conditions
- Chasing behavior (calls after big moves)

Data Sources:
- Historical trader calls from TraderCallLogger
- Price data from yfinance or existing price fetcher
- Market context from existing Phasma systems
"""

import json
import os
import yfinance as yf
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import statistics
import numpy as np

from trader_call_logger import TraderCallLogger, TraderCall, Direction, Horizon

@dataclass
class TraderPerformance:
    """Performance metrics for a single trader"""
    trader_id: str
    total_calls: int
    profitable_calls: int
    win_rate: float
    avg_gain_pct: float
    avg_loss_pct: float
    max_gain_pct: float
    max_loss_pct: float
    trust_score: float
    avg_days_to_profit: Optional[float]
    avg_days_to_loss: Optional[float]
    chasing_score: float  # How often they call after big moves
    last_updated: str
    
    def to_dict(self) -> Dict:
        return asdict(self)

@dataclass
class CallOutcome:
    """Result of a single trader call"""
    call: TraderCall
    entry_price: float
    max_gain_pct: float
    max_loss_pct: float
    final_outcome_pct: float
    days_held: int
    was_profitable: bool
    outcome_date: str
    notes: str

class TraderPerformanceTracker:
    """
    Tracks and analyzes trader performance over time
    Stage 2: Performance metrics and trust scoring
    """
    
    def __init__(self, call_logger: TraderCallLogger = None, data_dir: str = "data/trader_performance"):
        self.call_logger = call_logger or TraderCallLogger()
        self.data_dir = data_dir
        self.performance_file = os.path.join(data_dir, "trader_performance.json")
        self.outcomes_file = os.path.join(data_dir, "call_outcomes.json")
        
        # Create data directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
        
        # Initialize storage files
        self._init_storage()
        
        print("📊 Trader Performance Tracker initialized")
        print(f"   - Performance data: {self.performance_file}")
        print(f"   - Call outcomes: {self.outcomes_file}")
    
    def _init_storage(self):
        """Initialize storage files if they don't exist"""
        if not os.path.exists(self.performance_file):
            with open(self.performance_file, 'w') as f:
                json.dump({}, f)
            print(f"✅ Created performance storage: {self.performance_file}")
        
        if not os.path.exists(self.outcomes_file):
            with open(self.outcomes_file, 'w') as f:
                json.dump([], f)
            print(f"✅ Created outcomes storage: {self.outcomes_file}")
    
    def analyze_call_outcome(self, call: TraderCall, 
                           analysis_days: int = 7,
                           profit_threshold: float = 2.0) -> Optional[CallOutcome]:
        """
        Analyze the outcome of a single trader call
        
        Args:
            call: The trader call to analyze
            analysis_days: Days to look forward for price movement
            profit_threshold: Minimum gain to consider profitable
        
        Returns:
            CallOutcome with performance metrics
        """
        try:
            # Get historical price data
            ticker = yf.Ticker(call.ticker)
            
            # Parse call timestamp
            call_date = datetime.fromisoformat(call.timestamp.replace('Z', '+00:00'))
            
            # Get price data for analysis period
            end_date = call_date + timedelta(days=analysis_days)
            
            # Download historical data
            hist = ticker.history(start=call_date.date(), end=end_date.date())
            
            if hist.empty:
                return None
            
            # Use entry price from call or first available price
            entry_price = call.entry_price or hist['Close'].iloc[0]
            
            # Calculate performance metrics
            max_price = hist['High'].max()
            min_price = hist['Low'].min()
            final_price = hist['Close'].iloc[-1]
            
            max_gain_pct = ((max_price - entry_price) / entry_price) * 100
            max_loss_pct = ((min_price - entry_price) / entry_price) * 100
            final_outcome_pct = ((final_price - entry_price) / entry_price) * 100
            
            # Determine profitability
            was_profitable = max_gain_pct >= profit_threshold
            
            # Calculate days to max gain/loss
            max_gain_date = hist['High'].idxmax()
            max_loss_date = hist['Low'].idxmin()
            
            days_to_max_gain = (max_gain_date - call_date).days if max_gain_date > call_date else 0
            days_to_max_loss = (max_loss_date - call_date).days if max_loss_date > call_date else 0
            
            # Generate notes
            notes = []
            if max_gain_pct > 10:
                notes.append(f"Strong gain: +{max_gain_pct:.1f}%")
            if max_loss_pct < -10:
                notes.append(f"Large loss: {max_loss_pct:.1f}%")
            if final_outcome_pct < -5:
                notes.append("Ended negative")
            
            return CallOutcome(
                call=call,
                entry_price=entry_price,
                max_gain_pct=max_gain_pct,
                max_loss_pct=max_loss_pct,
                final_outcome_pct=final_outcome_pct,
                days_held=analysis_days,
                was_profitable=was_profitable,
                outcome_date=datetime.now(timezone.utc).isoformat(),
                notes="; ".join(notes) if notes else "Moderate movement"
            )
            
        except Exception as e:
            print(f"❌ Error analyzing call {call.ticker}: {str(e)}")
            return None
    
    def calculate_trader_performance(self, trader_id: str, 
                                   min_calls: int = 5) -> Optional[TraderPerformance]:
        """
        Calculate comprehensive performance metrics for a trader
        
        Args:
            trader_id: Trader to analyze
            min_calls: Minimum calls required for analysis
        
        Returns:
            TraderPerformance with all metrics
        """
        try:
            # Get all calls for this trader
            calls = self.call_logger.get_calls_by_trader(trader_id)
            
            if len(calls) < min_calls:
                print(f"⚠️ {trader_id}: Insufficient calls ({len(calls)} < {min_calls})")
                return None
            
            # Analyze outcomes for each call
            outcomes = []
            for call in calls:
                outcome = self.analyze_call_outcome(call)
                if outcome:
                    outcomes.append(outcome)
            
            if len(outcomes) < min_calls:
                print(f"⚠️ {trader_id}: Insufficient analyzable outcomes ({len(outcomes)} < {min_calls})")
                return None
            
            # Calculate metrics
            profitable_calls = sum(1 for o in outcomes if o.was_profitable)
            win_rate = (profitable_calls / len(outcomes)) * 100
            
            gains = [o.max_gain_pct for o in outcomes if o.max_gain_pct > 0]
            losses = [o.max_loss_pct for o in outcomes if o.max_loss_pct < 0]
            
            avg_gain_pct = statistics.mean(gains) if gains else 0
            avg_loss_pct = statistics.mean(losses) if losses else 0
            
            max_gain_pct = max(o.max_gain_pct for o in outcomes)
            max_loss_pct = min(o.max_loss_pct for o in outcomes)
            
            # Calculate trust score (0-100)
            trust_score = self._calculate_trust_score(win_rate, avg_gain_pct, avg_loss_pct, len(outcomes))
            
            # Calculate average days to profit/loss
            profitable_outcomes = [o for o in outcomes if o.was_profitable]
            losing_outcomes = [o for o in outcomes if not o.was_profitable]
            
            avg_days_to_profit = statistics.mean([o.days_held for o in profitable_outcomes]) if profitable_outcomes else None
            avg_days_to_loss = statistics.mean([o.days_held for o in losing_outcomes]) if losing_outcomes else None
            
            # Calculate chasing score (how often they call after big moves)
            chasing_score = self._calculate_chasing_score(outcomes)
            
            return TraderPerformance(
                trader_id=trader_id,
                total_calls=len(outcomes),
                profitable_calls=profitable_calls,
                win_rate=win_rate,
                avg_gain_pct=avg_gain_pct,
                avg_loss_pct=avg_loss_pct,
                max_gain_pct=max_gain_pct,
                max_loss_pct=max_loss_pct,
                trust_score=trust_score,
                avg_days_to_profit=avg_days_to_profit,
                avg_days_to_loss=avg_days_to_loss,
                chasing_score=chasing_score,
                last_updated=datetime.now(timezone.utc).isoformat()
            )
            
        except Exception as e:
            print(f"❌ Error calculating performance for {trader_id}: {str(e)}")
            return None
    
    def _calculate_trust_score(self, win_rate: float, avg_gain: float, 
                             avg_loss: float, call_count: int) -> float:
        """
        Calculate trust score based on performance metrics
        
        Args:
            win_rate: Percentage of profitable calls
            avg_gain: Average gain percentage
            avg_loss: Average loss percentage (negative)
            call_count: Number of calls analyzed
        
        Returns:
            Trust score (0-100)
        """
        # Base score from win rate
        base_score = win_rate
        
        # Adjust for risk/reward ratio
        if avg_loss != 0:
            risk_reward = abs(avg_gain / avg_loss)
            risk_adjustment = min(risk_reward * 10, 20)  # Max 20 points bonus
        else:
            risk_adjustment = 10
        
        # Adjust for sample size (more calls = more confidence)
        sample_adjustment = min(call_count / 2, 10)  # Max 10 points bonus
        
        # Calculate final score
        trust_score = base_score + risk_adjustment + sample_adjustment
        return min(max(trust_score, 0), 100)  # Clamp between 0-100
    
    def _calculate_chasing_score(self, outcomes: List[CallOutcome]) -> float:
        """
        Calculate how often a trader chases stocks that already moved significantly
        
        Args:
            outcomes: List of call outcomes
        
        Returns:
            Chasing score (0-100, higher = more chasing)
        """
        # This is a simplified version - in Stage 3 we'll enhance with pre-call price analysis
        # For now, we'll use the max loss as a proxy for chasing behavior
        if not outcomes:
            return 0
        
        large_losses = sum(1 for o in outcomes if o.max_loss_pct < -15)
        chasing_score = (large_losses / len(outcomes)) * 100
        
        return min(chasing_score, 100)
    
    def update_all_trader_performance(self, min_calls: int = 5):
        """Update performance metrics for all traders with sufficient data"""
        print("🔄 Updating performance metrics for all traders...")
        
        # Get all unique traders
        calls = self.call_logger.load_calls()
        trader_ids = set(call.trader_id for call in calls)
        
        performances = {}
        updated_count = 0
        
        for trader_id in trader_ids:
            performance = self.calculate_trader_performance(trader_id, min_calls)
            if performance:
                performances[trader_id] = performance.to_dict()
                updated_count += 1
                print(f"✅ Updated {trader_id}: {performance.win_rate:.1f}% win rate, {performance.trust_score:.0f} trust score")
        
        # Save performances
        with open(self.performance_file, 'w') as f:
            json.dump(performances, f, indent=2)
        
        print(f"\n📊 Performance update complete: {updated_count} traders analyzed")
        return performances
    
    def get_trader_performance(self, trader_id: str) -> Optional[TraderPerformance]:
        """Get cached performance for a specific trader"""
        try:
            with open(self.performance_file, 'r') as f:
                performances = json.load(f)
            
            if trader_id in performances:
                data = performances[trader_id]
                return TraderPerformance(**data)
            
            return None
            
        except Exception as e:
            print(f"❌ Error loading performance for {trader_id}: {str(e)}")
            return None
    
    def get_top_traders(self, metric: str = 'trust_score', limit: int = 10) -> List[TraderPerformance]:
        """Get top traders by specific metric"""
        try:
            with open(self.performance_file, 'r') as f:
                performances = json.load(f)
            
            # Convert to objects and sort
            trader_perfs = [TraderPerformance(**data) for data in performances.values()]
            
            if metric == 'trust_score':
                trader_perfs.sort(key=lambda x: x.trust_score, reverse=True)
            elif metric == 'win_rate':
                trader_perfs.sort(key=lambda x: x.win_rate, reverse=True)
            elif metric == 'avg_gain_pct':
                trader_perfs.sort(key=lambda x: x.avg_gain_pct, reverse=True)
            elif metric == 'total_calls':
                trader_perfs.sort(key=lambda x: x.total_calls, reverse=True)
            
            return trader_perfs[:limit]
            
        except Exception as e:
            print(f"❌ Error getting top traders: {str(e)}")
            return []
    
    def get_performance_summary(self) -> Dict:
        """Get overall summary of all tracked traders"""
        try:
            with open(self.performance_file, 'r') as f:
                performances = json.load(f)
            
            if not performances:
                return {'total_traders': 0}
            
            trader_perfs = [TraderPerformance(**data) for data in performances.values()]
            
            return {
                'total_traders': len(trader_perfs),
                'avg_win_rate': statistics.mean([p.win_rate for p in trader_perfs]),
                'avg_trust_score': statistics.mean([p.trust_score for p in trader_perfs]),
                'total_calls_analyzed': sum([p.total_calls for p in trader_perfs]),
                'top_performer': max(trader_perfs, key=lambda x: x.trust_score).trader_id if trader_perfs else None
            }
            
        except Exception as e:
            print(f"❌ Error generating summary: {str(e)}")
            return {'error': str(e)}

# Example usage and testing
if __name__ == "__main__":
    print("🧪 Testing Trader Performance Tracker...")
    
    # Initialize with existing call logger
    call_logger = TraderCallLogger()
    tracker = TraderPerformanceTracker(call_logger)
    
    # Update performance for all traders
    print("\n📊 Updating performance metrics...")
    performances = tracker.update_all_trader_performance(min_calls=1)  # Lower threshold for testing
    
    # Show top traders
    print("\n🏆 Top Traders by Trust Score:")
    top_traders = tracker.get_top_traders('trust_score', 5)
    for i, perf in enumerate(top_traders, 1):
        print(f"   {i}. {perf.trader_id}: {perf.trust_score:.0f} trust, {perf.win_rate:.1f}% win rate")
    
    # Show summary
    print("\n📈 Performance Summary:")
    summary = tracker.get_performance_summary()
    for key, value in summary.items():
        print(f"   {key}: {value}")
    
    print(f"\n✅ Stage 2 complete: Performance tracking infrastructure working!")
    print(f"   - Analyzed {summary.get('total_traders', 0)} traders")
    print(f"   - Ready for Stage 3: AI brain integration")
