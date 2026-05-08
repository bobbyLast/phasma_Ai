"""
Strategy Cue Cards - Clear, actionable strategy explanations
"""
from typing import Dict, List
from enum import Enum

class StrategyType(Enum):
    BREAKOUT = "BREAKOUT"
    REVERSAL = "REVERSAL"
    HALO_SMART_MONEY = "HALO_SMART_MONEY"
    MICROCAP_SPIKE = "MICROCAP_SPIKE"
    EARNINGS_PLAY = "EARNINGS_PLAY"
    CREDIT_SPREAD = "CREDIT_SPREAD"
    DEBIT_SPREAD = "DEBIT_SPREAD"
    DIAGONAL = "DIAGONAL"
    BUTTERFLY = "BUTTERFLY"
    PROTECTIVE_PUT = "PROTECTIVE_PUT"
    SCALP_INTRADAY = "SCALP_INTRADAY"

class StrategyCueCards:
    """
    Provides clear, actionable strategy explanations for different trade types
    """
    def __init__(self):
        self.cards = self._build_strategy_cards()

    def _build_strategy_cards(self) -> Dict[StrategyType, Dict]:
        """Build the strategy cue cards"""
        return {
            StrategyType.BREAKOUT: {
                'title': '🚀 BREAKOUT MODE',
                'description': 'Momentum + News + Float Filter Alignment',
                'trigger_conditions': [
                    'Volume surge 2x+ average',
                    'Price breaks recent resistance',
                    'News catalyst present',
                    'Float < 50M shares (tight supply)'
                ],
                'entry_rules': [
                    'Enter on break confirmation',
                    'Use 2% stop below breakout level',
                    'Scale in 25% at a time'
                ],
                'exit_rules': [
                    'Take profits at 2x risk (minimum)',
                    'Exit if volume dries up',
                    'Trail stop on strength'
                ],
                'risk_management': 'Max 1% of bankroll per trade',
                'timeframe': '1-5 days',
                'success_factors': ['Strong volume', 'Clean breakout', 'Positive news flow']
            },

            StrategyType.REVERSAL: {
                'title': '🔄 REVERSAL MODE',
                'description': 'Oversold Bounce + Insider/Dark Pool Divergence',
                'trigger_conditions': [
                    'RSI < 30 (oversold)',
                    'Recent sell-off > 15%',
                    'Insider buying detected',
                    'Dark pool accumulation'
                ],
                'entry_rules': [
                    'Wait for reversal candle',
                    'Enter on first green candle',
                    'Use wider stops (3-5%)'
                ],
                'exit_rules': [
                    'Take profits at resistance',
                    'Exit on bearish divergence',
                    'Use time stops (3-5 days)'
                ],
                'risk_management': 'Max 0.5% of bankroll (higher risk)',
                'timeframe': '3-10 days',
                'success_factors': ['Insider interest', 'Oversold bounce', 'Volume confirmation']
            },

            StrategyType.HALO_SMART_MONEY: {
                'title': '🎯 HALO (SMART MONEY)',
                'description': 'Unusual Block Trades + Options Sweep Detection',
                'trigger_conditions': [
                    'Block trade > $1M detected',
                    'Options sweep in calls',
                    'Unusual put/call ratio shift',
                    'Institutional accumulation pattern'
                ],
                'entry_rules': [
                    'Enter following smart money',
                    'Use 1% stops',
                    'Scale into position'
                ],
                'exit_rules': [
                    'Follow institutional lead',
                    'Exit on distribution pattern',
                    'Take profits on target hits'
                ],
                'risk_management': 'Max 1.5% of bankroll',
                'timeframe': '5-15 days',
                'success_factors': ['Block trade confirmation', 'Options flow', 'Institutional interest']
            },

            StrategyType.MICROCAP_SPIKE: {
                'title': '💎 MICROCAP SPIKE',
                'description': 'Low Float + High Volatility + Sudden Catalyst',
                'trigger_conditions': [
                    'Float < 20M shares',
                    'Volatility > 50%',
                    'Sudden news catalyst',
                    'Volume spike 3x+ average'
                ],
                'entry_rules': [
                    'Enter on spike confirmation',
                    'Use 3% stops (volatile)',
                    'Small position size only'
                ],
                'exit_rules': [
                    'Take quick profits (1-2 days)',
                    'Exit on volatility contraction',
                    'Cut losses fast'
                ],
                'risk_management': 'Max 0.25% of bankroll (very risky)',
                'timeframe': '1-3 days',
                'success_factors': ['Tight float', 'News catalyst', 'Volume surge']
            },

            StrategyType.EARNINGS_PLAY: {
                'title': '📊 EARNINGS PLAY',
                'description': 'Pre/Post Earnings Catalyst Trade',
                'trigger_conditions': [
                    'Earnings within 1 week',
                    'Options IV > 50%',
                    'Analyst expectations gap',
                    'Pre-earnings volume buildup'
                ],
                'entry_rules': [
                    'Enter 1-2 days pre-earnings',
                    'Use earnings-specific stops',
                    'Position for expected move'
                ],
                'exit_rules': [
                    'Exit immediately post-earnings',
                    'Take profits on gap moves',
                    'Cut losses if wrong direction'
                ],
                'risk_management': 'Max 0.75% of bankroll',
                'timeframe': '1-2 days',
                'success_factors': ['Earnings surprise', 'Options pricing', 'Volume pattern']
            },

            StrategyType.CREDIT_SPREAD: {
                'title': '💵 CREDIT SPREAD',
                'description': 'High IV, Directional Bias, Premium Capture',
                'trigger_conditions': [
                    'IV rank > 70 (expensive premium)',
                    'Directional catalyst aligns with bias',
                    'Support/resistance structure defined',
                    'Risk/Reward ≥ 1.5'
                ],
                'entry_rules': [
                    'Sell spread 30-45 DTE for theta decay',
                    'Use $5-$10 wide spreads on liquid underlyings',
                    'Enter on retest of support/resistance zone'
                ],
                'exit_rules': [
                    'Take 50% profit on premium decay',
                    'Exit if underlying breaks key level',
                    'Close ahead of major catalyst reversal'
                ],
                'risk_management': 'Max 0.75% of bankroll, ensure defined risk distance',
                'timeframe': '7-30 days',
                'success_factors': ['High IV rank', 'Clean technical levels', 'Directional edge']
            },

            StrategyType.DEBIT_SPREAD: {
                'title': '📈 DEBIT SPREAD',
                'description': 'Moderate IV, Controlled Directional Exposure',
                'trigger_conditions': [
                    'IV rank 30-70',
                    'Directional trend confirmation',
                    'Catalyst-driven move expected',
                    'Supportive volume + momentum'
                ],
                'entry_rules': [
                    'Buy spread with 20-40 DTE',
                    'Use strikes that target expected move',
                    'Position size off net debit only'
                ],
                'exit_rules': [
                    'Take profits at 70-80% of max value',
                    'Cut if trend invalidated',
                    'Roll if catalyst extends timeframe'
                ],
                'risk_management': 'Max 0.6% of bankroll per structure',
                'timeframe': '10-25 days',
                'success_factors': ['Confirmed trend', 'Balanced IV', 'Momentum alignment']
            },

            StrategyType.DIAGONAL: {
                'title': '📐 DIAGONAL POSITION',
                'description': 'Earn Theta + Ride Trend Through Catalyst',
                'trigger_conditions': [
                    'Catalyst 1-4 weeks out',
                    'IV term structure favourable (near > far)',
                    'Directional bias with consolidation',
                    'Desire to finance long exposure'
                ],
                'entry_rules': [
                    'Sell front-month premium against longer dated option',
                    'Use same direction strikes with slight ITM bias',
                    'Re-evaluate short leg weekly'
                ],
                'exit_rules': [
                    'Close before catalyst if IV collapses',
                    'Roll short leg if breached',
                    'Take profits once trend target met'
                ],
                'risk_management': 'Max 0.8% of bankroll, monitor assignment risk',
                'timeframe': '14-45 days',
                'success_factors': ['Catalyst timing', 'Term structure edge', 'Trend persistence']
            },

            StrategyType.BUTTERFLY: {
                'title': '🦋 BUTTERFLY',
                'description': 'Range-Bound Play on Elevated IV Crush',
                'trigger_conditions': [
                    'IV rank > 60 with expected contraction',
                    'Clear price target or pin risk',
                    'Low realized vol relative to implied',
                    'Event with predictable range (earnings, Fed)'
                ],
                'entry_rules': [
                    'Enter 7-15 DTE',
                    'Center strikes at expected pin level',
                    'Keep width manageable ($5-$10) for fills'
                ],
                'exit_rules': [
                    'Take 50-70% profit pre-event',
                    'Exit if underlying breaks outside wings',
                    'Cut quickly if realized vol expands'
                ],
                'risk_management': 'Max 0.4% of bankroll per butterfly',
                'timeframe': '5-15 days',
                'success_factors': ['Pin bias', 'IV crush potential', 'Tight range adherence']
            },

            StrategyType.PROTECTIVE_PUT: {
                'title': '🛡️ PROTECTIVE PUT',
                'description': 'Crash Hedging & Downside Insurance',
                'trigger_conditions': [
                    'Crash detector alert level ≥ 1',
                    'Portfolio long exposure vulnerable',
                    'IV elevated but trending higher',
                    'Macro risk or sector stress developing'
                ],
                'entry_rules': [
                    'Buy OTM puts 30-60 DTE',
                    'Size hedge to cover % of portfolio delta',
                    'Consider put spreads to manage cost'
                ],
                'exit_rules': [
                    'Take profits when drawdown covered',
                    'Roll if risk persists beyond expiry',
                    'Close if market stabilizes and signals flip'
                ],
                'risk_management': 'Allocate 0.5-1% bankroll for hedges in defensive regimes',
                'timeframe': '14-45 days',
                'success_factors': ['Timely trigger', 'Sufficient delta coverage', 'Volatility expansion']
            },

            StrategyType.SCALP_INTRADAY: {
                'title': '⚡ SCALP / INTRADAY',
                'description': 'Exploit Momentum Bursts with Tight Risk',
                'trigger_conditions': [
                    'Volume surge 3x+ intraday',
                    'Momentum shorts covering / breakout tape',
                    'Float constraints driving fast moves',
                    'Clear liquidity for quick exits'
                ],
                'entry_rules': [
                    'Use same-day or 0DTE contracts',
                    'Enter on break + immediate follow-through',
                    'Hard stop < 25% premium'
                ],
                'exit_rules': [
                    'Scale out at +40%, +75%',
                    'Flatten if volume stalls',
                    'Never hold past power hour unless extension confirmed'
                ],
                'risk_management': 'Risk ≤ 0.2% of bankroll per scalp, limit to two attempts',
                'timeframe': 'Same-day',
                'success_factors': ['Tape speed', 'Volume confirmation', 'Discipline on exits']
            }
        }

    def get_card(self, strategy_type: StrategyType) -> Dict:
        """Get strategy cue card for specific type"""
        return self.cards.get(strategy_type, {})

    def format_card_message(self, strategy_type: StrategyType) -> str:
        """Format strategy card for display"""
        card = self.get_card(strategy_type)
        if not card:
            return "Strategy card not found"

        message = f"**{card['title']}**\n"
        message += f"*{card['description']}*\n\n"

        message += "🎯 **TRIGGER CONDITIONS:**\n"
        for condition in card['trigger_conditions']:
            message += f"• {condition}\n"

        message += "\n💰 **ENTRY RULES:**\n"
        for rule in card['entry_rules']:
            message += f"• {rule}\n"

        message += "\n📈 **EXIT RULES:**\n"
        for rule in card['exit_rules']:
            message += f"• {rule}\n"

        message += f"\n⚠️ **RISK MANAGEMENT:** {card['risk_management']}\n"
        message += f"⏰ **TIMEFRAME:** {card['timeframe']}\n"

        message += "\n✅ **SUCCESS FACTORS:**\n"
        for factor in card['success_factors']:
            message += f"• {factor}\n"

        return message

    def get_all_cards_summary(self) -> str:
        """Get summary of all available strategy cards"""
        message = "🎯 **PHASMA STRATEGY CARDS** 🎯\n\n"

        for strategy_type, card in self.cards.items():
            message += f"**{strategy_type.value}**\n"
            message += f"{card['description']}\n"
            message += f"Timeframe: {card['timeframe']} | Risk: {card['risk_management']}\n\n"

        message += "Use `/strategy [type]` for detailed card\n"
        message += "Available: breakout, reversal, halo, microcap, earnings"

        return message

    def suggest_strategy(self, signal_data: Dict) -> StrategyType:
        """
        Suggest appropriate strategy based on signal characteristics
        """
        # Analyze signal characteristics
        volume_surge_value = signal_data.get('volume_surge', 1.0)
        volume_surge = volume_surge_value > 2
        float_tight = signal_data.get('float_millions', 100) < 50
        volatility = signal_data.get('volatility', 0)
        volatility_high = volatility > 0.5
        news_catalyst = bool(signal_data.get('news_catalyst'))
        earnings_near = signal_data.get('days_to_earnings', 30) <= 7
        block_trades = signal_data.get('block_trades_detected', False)
        options_sweep = signal_data.get('options_sweep', False)
        oversold = signal_data.get('rsi', 50) < 30
        action = signal_data.get('action', 'BUY_CALL')
        iv_rank = signal_data.get('iv_rank')
        pop = signal_data.get('pop', 0)
        divergence = signal_data.get('divergence_score', 0)
        pattern_strength = signal_data.get('pattern_strength', 0)
        win_rate = signal_data.get('win_rate', 0)
        is_defensive_mode = signal_data.get('is_defensive_mode', False)
        days_to_expiry = signal_data.get('days_to_expiry', 14)

        if is_defensive_mode or action.endswith('PUT') and pop >= 35:
            return StrategyType.PROTECTIVE_PUT

        if earnings_near:
            return StrategyType.DIAGONAL if iv_rank and iv_rank >= 55 else StrategyType.EARNINGS_PLAY

        if iv_rank is not None:
            if iv_rank >= 80 and 'CALL' in action:
                return StrategyType.CREDIT_SPREAD
            if iv_rank >= 80 and 'PUT' in action:
                return StrategyType.DEBIT_SPREAD
            if 40 <= iv_rank <= 75 and days_to_expiry >= 20:
                return StrategyType.DIAGONAL
            if iv_rank < 30 and win_rate >= 0.5:
                return StrategyType.DEBIT_SPREAD

        if volume_surge and news_catalyst and days_to_expiry <= 3 and pop >= 45:
            return StrategyType.SCALP_INTRADAY

        if block_trades or options_sweep:
            return StrategyType.HALO_SMART_MONEY

        if float_tight and volatility_high and volume_surge:
            return StrategyType.MICROCAP_SPIKE

        if oversold and volume_surge:
            return StrategyType.REVERSAL

        if divergence >= 0.2 and pattern_strength >= 0.2:
            return StrategyType.BUTTERFLY

        if volume_surge and news_catalyst:
            return StrategyType.BREAKOUT

        if win_rate >= 0.55 and days_to_expiry >= 15:
            return StrategyType.DEBIT_SPREAD

        return StrategyType.BREAKOUT  # Default

# Global instance
_strategy_cards = None

def get_strategy_cards() -> StrategyCueCards:
    """Get singleton strategy cards"""
    global _strategy_cards
    if _strategy_cards is None:
        _strategy_cards = StrategyCueCards()
    return _strategy_cards
