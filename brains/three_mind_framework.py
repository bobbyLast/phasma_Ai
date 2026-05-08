"""
Three-Mind Trading Framework - Main Orchestrator

Coordinates the three minds: Macro Navigator, Value Selector, and Micro Execution.
Generates high-conviction signals based on confluence across all three minds.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import json
import asyncio

from brains.macro_navigator import MacroNavigator, RegimeState
from brains.value_selector import ValueSelector, ValueScore
from brains.micro_execution_engine import MicroExecutionEngine, MicroSignal, TradePlan


@dataclass
class ThreeMindSignal:
    """Complete trading signal from three-mind framework"""
    symbol: str
    action: str
    confluence_score: float  # 0-100
    macro_alignment: Dict
    value_assessment: Dict
    technical_setup: Dict
    trade_plan: TradePlan
    reasoning: str
    timestamp: datetime
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['trade_plan'] = asdict(self.trade_plan)
        return data


class ThreeMindFramework:
    """Main orchestrator for the three-mind trading system"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        
        # Initialize the three minds
        self.macro_navigator = MacroNavigator(config)
        self.value_selector = ValueSelector(config)
        self.micro_engine = MicroExecutionEngine(config)
        
        # Framework parameters
        self.min_confluence_score = 70  # Minimum score to generate signal
        self.max_signals_per_cycle = 5
        
        # Trade journal for learning
        self.trade_journal = []
        
    async def analyze_opportunity(self, symbol: str, price_data: Dict, 
                                market_data: Dict) -> Optional[ThreeMindSignal]:
        """Complete three-mind analysis for a single opportunity"""
        
        try:
            # Mind 1: Macro Analysis
            macro_regime = self.macro_navigator.analyze_regime(market_data)
            macro_alignment = self._assess_macro_alignment(symbol, macro_regime)
            
            # Mind 2: Value Analysis
            value_score = self.value_selector.analyze_value(symbol)
            value_assessment = self._assess_value_alignment(value_score)
            
            # Mind 3: Micro Technical Analysis
            micro_signal = self.micro_engine.analyze_micro_setup(
                symbol, price_data, 
                macro_alignment.get('score', 0),
                value_assessment.get('score', 0)
            )
            
            if not micro_signal:
                return None
            
            # Calculate confluence score
            confluence_score = self._calculate_confluence_score(
                macro_alignment, value_assessment, micro_signal
            )
            
            # Skip if confluence too low
            if confluence_score < self.min_confluence_score:
                return None
            
            # Create trade plan
            trade_plan = self.micro_engine.create_trade_plan(
                micro_signal, macro_alignment, value_assessment
            )
            
            # Generate reasoning
            reasoning = self._generate_reasoning(
                symbol, macro_alignment, value_assessment, micro_signal
            )
            
            return ThreeMindSignal(
                symbol=symbol,
                action=trade_plan.action,
                confluence_score=confluence_score,
                macro_alignment=macro_alignment,
                value_assessment=value_assessment,
                technical_setup=asdict(micro_signal),
                trade_plan=trade_plan,
                reasoning=reasoning,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            print(f"Error in three-mind analysis for {symbol}: {e}")
            return None
    
    async def scan_universe(self, symbols: List[str], price_data: Dict, 
                           market_data: Dict) -> List[ThreeMindSignal]:
        """Scan universe for high-conviction opportunities"""
        
        signals = []
        
        # Analyze each symbol
        for symbol in symbols:
            if symbol not in price_data:
                continue
                
            signal = await self.analyze_opportunity(
                symbol, price_data[symbol], market_data
            )
            
            if signal:
                signals.append(signal)
                
                # Limit signals per cycle
                if len(signals) >= self.max_signals_per_cycle:
                    break
        
        # Sort by confluence score
        signals.sort(key=lambda x: x.confluence_score, reverse=True)
        
        return signals
    
    def _assess_macro_alignment(self, symbol: str, regime: RegimeState) -> Dict:
        """Assess how symbol aligns with current macro regime"""
        
        alignment = {
            'regime': regime.name,
            'risk_on_off': regime.risk_on_off,
            'preferred_strategies': regime.preferred_strategies,
            'score': 0.5,  # Base score
            'reasoning': ''
        }
        
        # Sector-specific macro alignment
        if 'energy' in symbol.lower() and regime.risk_on_off == "RISK_ON":
            alignment['score'] = 0.8
            alignment['reasoning'] = "Energy stocks favored in risk-on environment"
        elif 'tech' in symbol.lower() and regime.volatility_regime == "LOW":
            alignment['score'] = 0.7
            alignment['reasoning'] = "Tech stocks perform well in low volatility"
        elif regime.risk_on_off == "RISK_OFF" and 'utility' in symbol.lower():
            alignment['score'] = 0.8
            alignment['reasoning'] = "Defensive utilities preferred in risk-off"
        
        # Adjust for regime strength
        alignment['score'] *= regime.confidence
        
        return alignment
    
    def _assess_value_alignment(self, value_score: Optional[ValueScore]) -> Dict:
        """Assess value proposition"""
        
        if not value_score:
            return {
                'grade': 'UNKNOWN',
                'margin_of_safety': 0,
                'quality_score': 0,
                'score': 0,
                'reasoning': 'No fundamental data available'
            }
        
        # Convert value grade to score
        grade_scores = {
            'DEEP_VALUE': 1.0,
            'VALUE': 0.8,
            'FAIR': 0.5,
            'OVERVALUED': 0.2,
            'JUNK': 0.0
        }
        
        return {
            'grade': value_score.value_grade,
            'margin_of_safety': value_score.margin_of_safety,
            'quality_score': value_score.quality_score,
            'score': grade_scores.get(value_score.value_grade, 0) * value_score.conviction,
            'reasoning': value_score.thesis
        }
    
    def _calculate_confluence_score(self, macro: Dict, value: Dict, 
                                  technical: MicroSignal) -> float:
        """Calculate overall confluence score (0-100)"""
        
        # Weight the three minds
        macro_weight = 0.3
        value_weight = 0.3
        technical_weight = 0.4
        
        # Get individual scores (0-1)
        macro_score = macro.get('score', 0)
        value_score = value.get('score', 0)
        technical_score = technical.confidence
        
        # Bonus for strong alignment across all minds
        alignment_bonus = 0
        if macro_score > 0.7 and value_score > 0.7 and technical_score > 0.7:
            alignment_bonus = 0.1
        
        # Calculate weighted average
        confluence = (
            macro_score * macro_weight +
            value_score * value_weight +
            technical_score * technical_weight +
            alignment_bonus
        ) * 100
        
        return min(confluence, 100)
    
    def _generate_reasoning(self, symbol: str, macro: Dict, value: Dict, 
                          technical: MicroSignal) -> str:
        """Generate comprehensive reasoning for the trade"""
        
        reasoning = f"THREE-MIND CONFLUENCE SIGNAL for {symbol}\n\n"
        
        reasoning += f"🌍 MACRO: {macro.get('reasoning', 'Neutral macro environment')} "
        reasoning += f"(Regime: {macro.get('regime', 'Unknown')})\n"
        
        reasoning += f"💰 VALUE: {value.get('reasoning', 'No value thesis')} "
        reasoning += f"(Grade: {value.get('grade', 'Unknown')})\n"
        
        reasoning += f"📈 TECHNICAL: {technical.thesis} "
        reasoning += f"(Pattern: {technical.pattern_type}, R/R: {technical.risk_reward:.1f}:1)\n\n"
        
        reasoning += f"CONFLUENCE SCORE: {self._calculate_confluence_score(macro, value, technical):.0f}/100"
        
        return reasoning
    
    def log_signal(self, signal: ThreeMindSignal):
        """Log signal to trade journal"""
        
        self.trade_journal.append({
            'signal': signal.to_dict(),
            'status': 'ACTIVE',
            'entry_date': datetime.now().isoformat()
        })
        
        # Save to file
        with open('three_mind_journal.json', 'a') as f:
            json.dump(signal.to_dict(), f)
            f.write('\n')
    
    def update_trade_status(self, symbol: str, status: str, exit_price: float = None, 
                           pnl: float = None, notes: str = None):
        """Update trade status in journal"""
        
        for trade in self.trade_journal:
            if trade['signal']['symbol'] == symbol and trade['status'] == 'ACTIVE':
                trade['status'] = status
                trade['exit_date'] = datetime.now().isoformat()
                
                if exit_price:
                    trade['exit_price'] = exit_price
                if pnl:
                    trade['pnl'] = pnl
                if notes:
                    trade['exit_notes'] = notes
                
                # Analyze which mind was right/wrong
                self._analyze_trade_attribution(trade)
                break
    
    def _analyze_trade_attribution(self, trade: Dict):
        """Analyze which mind contributed most to success/failure"""
        
        signal = trade['signal']
        
        # This would implement learning logic
        # For now, just save the data
        attribution = {
            'macro_correct': None,  # To be determined
            'value_correct': None,
            'technical_correct': None,
            'primary_driver': None
        }
        
        trade['attribution'] = attribution
    
    def get_performance_metrics(self) -> Dict:
        """Calculate performance metrics from trade journal"""
        
        completed_trades = [t for t in self.trade_journal if t['status'] in ['WIN', 'LOSS']]
        
        if not completed_trades:
            return {'message': 'No completed trades yet'}
        
        wins = [t for t in completed_trades if t['status'] == 'WIN']
        
        win_rate = len(wins) / len(completed_trades)
        avg_pnl = sum(t.get('pnl', 0) for t in completed_trades) / len(completed_trades)
        
        return {
            'total_trades': len(completed_trades),
            'win_rate': win_rate,
            'avg_pnl': avg_pnl,
            'total_pnl': sum(t.get('pnl', 0) for t in completed_trades)
        }
