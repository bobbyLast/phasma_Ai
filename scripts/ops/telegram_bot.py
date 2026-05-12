import asyncio
import requests
import os
from dotenv import load_dotenv
from typing import Dict, Any
from datetime import datetime
from core.config import PhasmaConfig
from utils.why_moving_strip import get_why_moving_strip
from utils.strategy_cue_cards import get_strategy_cards
from utils.price_fetcher import get_price_fetcher

# Load environment variables
load_dotenv()

class TelegramBot:
    def __init__(self, token, chat_id):
        self.token = token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{token}"

    def send_message(self, text):
        """Send a message to the Telegram chat."""
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text
        }
        response = requests.post(url, json=payload)
        print(f"🔍 TELEGRAM API DEBUG: Status {response.status_code}")
        print(f"🔍 TELEGRAM API RESPONSE: {response.text}")
        return response.status_code == 200

    def format_signal_message(self, signal):
        # Check if this is a Kalshi prediction market signal
        signal_source = signal.get('source', 'unknown')
        has_kalshi_signal = signal.get('kalshi_signal', False)
        print(f"🔍 DEBUG: Signal source={signal_source}, has_kalshi_signal={has_kalshi_signal}")
        
        if signal_source == 'kalshi_prediction' or has_kalshi_signal:
            print("📈 Using Kalshi signal formatter (should include trade links)")
            return self.format_kalshi_signal_message(signal)
        elif signal_source == 'options_engine' or 'CALL' in signal.get('action', '') or 'PUT' in signal.get('action', ''):
            print("📊 Using options formatter")
            return self.format_options_signal_message(signal)
        else:
            print("📈 Using regular stock formatter")
            return self.format_stock_signal_message(signal)
        
        # Format for ROBINHOOD/WEBULL Level 2 Options Trading
        symbol = signal.get('symbol', 'UNKNOWN')
        action = signal.get('action', 'BUY_CALL')
        confidence = signal.get('sim_scaled_confidence', signal.get('confidence', 0) * 100)
        position_size = signal.get('position_size', 0)
        pop_from_sim = signal.get('pop_from_sim', 50)

        # Get simulation results
        sim_results = signal.get('simulation_results', {})
        win_rate = sim_results.get('win_rate', 0)
        avg_pnl = sim_results.get('avg_pnl', 0)
        optimal_exit_day = sim_results.get('optimal_exit_day', 5)

        # Get dynamic timeframe info
        days_to_expiry = signal.get('days_to_expiry', optimal_exit_day)
        timeframe_type = signal.get('timeframe_type', 'STANDARD')
        timeframe_reason = signal.get('timeframe_reasoning', 'Standard trade')

        # NEW: Get insight strip and strategy suggestion
        insight_strip = signal.get('insight_strip', '')
        suggested_strategy = signal.get('suggested_strategy', 'BREAKOUT')

        # Make strategy label more readable for humans
        strategy_label = None
        if suggested_strategy:
            try:
                strategy_label = suggested_strategy.replace('_', ' ').title()
            except Exception:
                strategy_label = str(suggested_strategy)

        # Direction for options
        direction = "Call" if "CALL" in action else "Put"

        # Calculate expiration date (use full days_to_expiry, not just optimal exit)
        from datetime import datetime, timedelta
        exp_date = datetime.now() + timedelta(days=days_to_expiry)
        exp_str = exp_date.strftime('%m/%d/%y')  # Robinhood format: 11/12/25

        # Calculate optimal exit date
        exit_date = datetime.now() + timedelta(days=optimal_exit_day)
        exit_str = exit_date.strftime('%m/%d/%y')

        # Get REAL current price - NO DEFAULTS!
        symbol = signal.get('symbol', 'UNKNOWN')
        price_fetcher = get_price_fetcher()
        current_price = signal.get('current_price')

        # If no price in signal, fetch it now
        if not current_price or current_price <= 0:
            current_price = price_fetcher.get_real_price(symbol)
            if not current_price:
                # FAIL LOUDLY - don't trade without real price!
                raise ValueError(f"Cannot get real price for {symbol} - REFUSING TO TRADE!")

        # Calculate strike based on direction and current price
        # For CALL: 2% OTM (not 5% - that was too aggressive)
        # For PUT: 2% OTM
        if "CALL" in action:
            strike = round(current_price * 1.02, 2)  # 2% OTM call
        else:
            strike = round(current_price * 0.98, 2)  # 2% OTM put

        # Premium estimate based on position size and contracts
        contracts = max(1, int(position_size / 100))  # Minimum 1 contract
        premium_per_contract = round(position_size / contracts, 2)

        # Calculate profit targets
        take_profit_price = round(premium_per_contract * 1.75, 2)  # 75% profit
        stop_loss_price = round(premium_per_contract * 0.60, 2)   # 40% loss

        # Max loss per contract
        max_loss = premium_per_contract

        # Total cost
        total_cost = premium_per_contract * contracts

        # Get company info
        company_info = signal.get('fact_check', {}).get('company_info', {})
        company_name = company_info.get('name') or company_info.get('full_name') or symbol

        # Build concise WHY with key data
        why_lines = []
        why_lines.append(f"Strategy: {strategy_label or 'BREAKOUT'}")
        why_lines.append(f"Type: {timeframe_type} - {timeframe_reason}")
        why_lines.append(f"Peak Profit: Day {optimal_exit_day} of {days_to_expiry}")
        why_lines.append(f"Win Rate: {win_rate:.1%} | Avg P&L: ${avg_pnl:.0f}")
        if insight_strip:
            why_lines.append(f"Insight: {insight_strip}")
        why_text = "\n".join(why_lines)

        # Strategy-specific exit guidance
        strategy_exit_text = ""
        if suggested_strategy == "CREDIT_SPREAD":
            strategy_exit_text = "Close at 50-70% credit gain. Roll if price grinds toward short strike."
        elif suggested_strategy == "DIAGONAL":
            strategy_exit_text = "Roll short leg 3-5 days before expiry. Avoid ITM assignment."
        elif suggested_strategy == "BREAKOUT":
            strategy_exit_text = "Sell half at 50% gain if hit quickly. Hold rest for peak day."
        else:
            strategy_exit_text = "Follow exit rules strictly. Don't hold past expiration."

        # ROBINHOOD/WEBULL EXACT FORMAT - Strategy First
        message = f"""🚀 PHASMA AI TRADE SIGNAL - {symbol} ({company_name})

━━━━━━━━━━━━━━━━━━━━━━
🎯 STRATEGY
━━━━━━━━━━━━━━━━━━━━━━

{why_text}

Exit: {strategy_exit_text}

━━━━━━━━━━━━━━━━━━━━━━
📱 COPY TO ROBINHOOD/WEBULL:
━━━━━━━━━━━━━━━━━━━━━━

**Ticker:** {symbol}
**Action:** BUY TO OPEN
**Option Type:** {direction}
**Strike Price:** ${strike:.2f}
**Expiration:** {exp_str}
**Contracts:** {contracts}
**Limit Price:** ${premium_per_contract:.2f} per contract

━━━━━━━━━━━━━━━━━━━━━━
💰 TRADE DETAILS:
━━━━━━━━━━━━━━━━━━━━━━

Total Cost: ${total_cost:.2f}
Max Loss: ${max_loss * contracts:.2f}
Take Profit: ${take_profit_price:.2f} (+75%)
Stop Loss: ${stop_loss_price:.2f} (-40%)

🎯 EXIT: SELL on {exit_str} (Day {optimal_exit_day})
Confidence: {confidence:.1f}% | POP: {pop_from_sim:.1f}%

━━━━━━━━━━━━━━━━━━━━━━
📋 HOW TO ENTER IN APP:
━━━━━━━━━━━━━━━━━━━━━━

1. Search: {symbol}
2. Tap "Trade" → "Options"
3. Select: {exp_str} expiration
4. Choose: ${strike:.2f} {direction}
5. Action: "Buy" (Level 2)
6. Quantity: {contracts} contract(s)
7. Order Type: "Limit"
8. Limit Price: ${premium_per_contract:.2f}
9. Review & Submit

🤖 Phasma AI - Level 2 Options Trading"""

        return message.strip()

    def format_options_signal_message(self, signal):
        """Format options signals with compelling reasoning and profit potential."""
        
        symbol = signal.get('symbol', 'UNKNOWN')
        underlying = signal.get('underlying', symbol.split('_')[0])
        action = signal.get('action', 'BUY_CALL')
        strike = signal.get('strike', 0)
        expiry = signal.get('expiry', '')
        entry_price = signal.get('entry_price', 0)
        take_profit = signal.get('take_profit', 0)
        stop_loss = signal.get('stop_loss', 0)
        confidence = signal.get('confidence', 0) * 100
        pop = signal.get('pop', 0) * 100
        
        # Get company name from fact_check if available
        company_info = signal.get('fact_check', {}).get('company_info', {})
        company_name = company_info.get('name') or company_info.get('full_name') or underlying
        
        # Get stock profit and holding period
        expected_stock_move = signal.get('expected_stock_move', 0)
        optimal_hold_days = signal.get('optimal_hold_days', 5)
        expected_option_return = signal.get('expected_option_return', 0)
        
        # Calculate option profit percentages
        profit_pct = ((take_profit - entry_price) / entry_price) * 100
        loss_pct = ((entry_price - stop_loss) / entry_price) * 100
        
        # Get reasoning
        rationale = signal.get('rationale', '')
        
        # Build concise WHY with key data - Strategy First
        why_lines = []
        why_lines.append(f"Strategy: OPTIONS LEVERAGE")
        if 'breakout' in rationale.lower():
            why_lines.append(f"Type: Breakout - 5-10x leverage")
        elif 'earnings' in rationale.lower():
            why_lines.append(f"Type: Pre-earnings - low IV")
        elif 'oversold' in rationale.lower():
            why_lines.append(f"Type: Oversold bounce")
        else:
            why_lines.append(f"Type: Directional play")
        
        why_lines.append(f"Expected Stock Move: +{expected_stock_move:.0f}%")
        why_lines.append(f"Expected Option Return: +{expected_option_return:.0f}%")
        why_lines.append(f"Hold Time: {optimal_hold_days} days max")
        why_text = "\n".join(why_lines)
        
        # Build message - Strategy First
        message = f"""🚀 PHASMA AI OPTIONS ALERT - {underlying} ({company_name})

━━━━━━━━━━━━━━━━━━━━━━
🎯 STRATEGY
━━━━━━━━━━━━━━━━━━━━━━

{why_text}

Exit: Sell half at 50% gain if hit quickly. Hold rest for full target or stop. Don't hold past expiration.

━━━━━━━━━━━━━━━━━━━━━━
📊 OPTION DETAILS:
━━━━━━━━━━━━━━━━━━━━━━

Underlying: {underlying}
Action: BUY TO OPEN {action.split('_')[-1]}
Strike: ${strike:.2f}
Expiration: {expiry}
Entry Price: ${entry_price:.2f}

━━━━━━━━━━━━━━━━━━━━━━
💰 PROFIT TARGETS:
━━━━━━━━━━━━━━━━━━━━━━

Take Profit: ${take_profit:.2f} (+{profit_pct:.0f}%)
Stop Loss: ${stop_loss:.2f} (-{loss_pct:.0f}%)

━━━━━━━━━━━━━━━━━━━━━━
📈 PROBABILITIES:
━━━━━━━━━━━━━━━━━━━━━━

AI Confidence: {confidence:.0f}%
Probability of Profit: {pop:.0f}%"""
        
        return message.strip()
    
    def format_stock_signal_message(self, signal):
        """Format regular stock signals with compelling reasoning."""
        
        symbol = signal.get('symbol', 'UNKNOWN')
        action = signal.get('action', 'BUY')
        source = signal.get('source', 'unknown')
        
        # Get company name from fact_check if available
        company_info = signal.get('fact_check', {}).get('company_info', {})
        company_name = company_info.get('name') or company_info.get('full_name') or symbol
        
        # Fix confidence format - if it's already a percentage (like 75), don't multiply by 100
        confidence = signal.get('confidence', 0)
        if confidence > 1:
            confidence = confidence / 100  # Convert from percentage to decimal
        confidence_pct = confidence * 100
        
        # ADD CONFLUENCE SCORE if available
        confluence_score = signal.get('confluence_score', confidence_pct)
        
        pop_from_sim = signal.get('pop_from_sim', 50)
        entry_price = signal.get('entry_price', 'N/A')
        target_price = signal.get('target_price', 'N/A')
        
        # Check if this is a fundamental analysis signal (undervalued stock)
        is_fundamental = source == 'fundamental_analysis' or signal.get('valuation_score') is not None
        
        # Build concise WHY with key data - Strategy First
        why_lines = []
        
        if is_fundamental:
            why_lines.append(f"Strategy: VALUE INVESTING")
            
            # Add AI reasoning: why THIS stock, why industry needs it
            ai_reasoning = signal.get('ai_reasoning', '')
            if ai_reasoning:
                # Parse the reasoning to extract key parts
                if 'WHY THIS STOCK:' in ai_reasoning and 'WHY INDUSTRY:' in ai_reasoning:
                    parts = ai_reasoning.split('WHY INDUSTRY:')
                    why_this = parts[0].replace('WHY THIS STOCK:', '').strip()
                    why_industry = parts[1].strip()
                    
                    why_lines.append(f"Type: {why_this[:80]}...")
                    why_lines.append(f"Industry: {why_industry[:80]}...")
                else:
                    why_lines.append(f"Type: {ai_reasoning[:120]}...")
            
            # Add fundamental reasons
            pe_ratio = signal.get('pe_ratio', 0)
            industry_pe = signal.get('industry_pe', 0)
            valuation_score = signal.get('valuation_score', 0)
            valuation_level = signal.get('valuation_level', 'Unknown')
            expected_gain = signal.get('expected_gain', 0)
            
            if pe_ratio > 0 and industry_pe > 0:
                pe_vs_industry = (pe_ratio / industry_pe) * 100
                why_lines.append(f"Valuation: P/E {pe_ratio:.1f} vs Industry {industry_pe:.1f} ({pe_vs_industry:.0f}%)")
            
            if valuation_score:
                why_lines.append(f"Score: {valuation_score}/10 ({valuation_level})")
            
            if expected_gain:
                why_lines.append(f"Expected: +{expected_gain:.1f}%")
            
            # Add growth metrics if available
            eps_growth = signal.get('eps_growth', 0)
            revenue_growth = signal.get('revenue_growth', 0)
            if eps_growth > 0 or revenue_growth > 0:
                growth_info = []
                if eps_growth > 0:
                    growth_info.append(f"EPS +{eps_growth:.1f}%")
                if revenue_growth > 0:
                    growth_info.append(f"Rev +{revenue_growth:.1f}%")
                why_lines.append(f"Growth: {' | '.join(growth_info)}")
            
            why_lines.append(f"Confidence: {confidence_pct:.0f}%")
            
            # Add investment thesis if available
            thesis = signal.get('investment_thesis', '')
            if thesis:
                why_lines.append(f"Thesis: {thesis[:80]}...")
        else:
            # Technical analysis signal
            why_lines.append(f"Strategy: STOCK SWING")
            
            # Get compelling reasoning
            rationale = signal.get('rationale', '')
            patterns = signal.get('patterns', [])
            technical_bias = signal.get('technical_bias', 'NEUTRAL')
            divergence_score = signal.get('divergence_score', 0)
            
            # Add specific reasons based on analysis - concise
            reasons = []
            if 'breakout' in rationale.lower() or 'breaking' in rationale.lower():
                reasons.append("Breakout from consolidation")
            if 'volume' in rationale.lower() or patterns:
                reasons.append("Unusual volume - smart money")
            if 'oversold' in rationale.lower() or technical_bias == 'BULLISH':
                reasons.append("Bullish momentum building")
            if divergence_score > 0.3:
                reasons.append(f"Strong divergence ({divergence_score:.2f})")
            if 'catalyst' in rationale.lower():
                reasons.append("News catalyst driving interest")
            if 'moonshot' in rationale.lower() or signal.get('is_moonshot'):
                reasons.append("🚀 MOONSHOT - overnight catalyst")
            
            if reasons:
                why_lines.append(f"Type: " + " | ".join(reasons))
            else:
                why_lines.append(f"Type: Technical setup")
            
            # Calculate expected gain from simulation results
            try:
                # Get simulation results if available
                sim_results = signal.get('simulation_results', {})
                if sim_results and 'profit_potential' in sim_results:
                    expected_gain = sim_results['profit_potential'] * 100
                    why_lines.append(f"Expected: +{expected_gain:.1f}% (Monte Carlo)")
                else:
                    # Fallback to target/entry calculation
                    target_price = signal.get('target_price', signal.get('entry_price', 0) * 1.05)
                    entry_price = signal.get('entry_price', 0)
                    expected_gain = ((float(target_price)/float(entry_price)-1)*100)
                    why_lines.append(f"Expected: +{expected_gain:.1f}%")
            except Exception:
                why_lines.append(f"Target: ${signal.get('target_price', 'N/A')}")
            
            why_lines.append(f"Confidence: {confidence_pct:.0f}% | Success Rate: {pop_from_sim:.0f}%")
        
        why_text = "\n".join(why_lines)
        
        # Build exit strategy based on signal type
        if is_fundamental:
            exit_text = "Hold for 6-12 months for value realization. Scale out if target reached early. Reassess if fundamentals deteriorate."
        else:
            exit_text = "Scale out 50% at halfway point. Hold remainder for full target if momentum strong. Stop below recent low if price action fails."
        
        # Build message - Strategy First (Compact format)
        message = f"""🚀 PHASMA AI - {action} {symbol} ({company_name})

━━━━━━━━━━━━━━━━━━━━━━
🎯 STRATEGY
━━━━━━━━━━━━━━━━━━━━━━

{why_text}

Exit: {exit_text}

━━━━━━━━━━━━━━━━━━━━━━
📊 KEY LEVELS
━━━━━━━━━━━━━━━━━━━━━━

Entry: ${entry_price} | Target: ${target_price}"""

        # Add combined FUNDAMENTALS & CONFLUENCE section for value stocks
        if is_fundamental:
            pe_ratio = signal.get('pe_ratio', 0)
            industry_pe = signal.get('industry_pe', 0)
            peg_ratio = signal.get('peg_ratio', 0)
            
            message += f"""

━━━━━━━━━━━━━━━━━━━━━━
💎 VALUATION
━━━━━━━━━━━━━━━━━━━━━━

P/E: {pe_ratio:.1f} (Industry: {industry_pe:.1f}) | PEG: {peg_ratio:.2f if peg_ratio else 'N/A'}
Score: {signal.get('valuation_score', 0)}/10 | Confluence: {confluence_score:.0f}/100"""
        
        return message
    
    def format_kalshi_signal_message(self, signal):
        """Format Kalshi prediction market signals with direct trade links."""
        
        symbol = signal.get('symbol', 'UNKNOWN')
        kalshi_signal = signal.get('kalshi_signal', 'BUY_YES')
        kalshi_action = signal.get('kalshi_action', 'BUY_CALL')
        confidence = signal.get('sim_scaled_confidence', signal.get('confidence', 0) * 100)
        pop_from_sim = signal.get('pop_from_sim', 50)
        
        # Get Kalshi-specific data
        kalshi_analysis = signal.get('kalshi_analysis', {})
        rationale = kalshi_analysis.get('rationale', 'AI-generated prediction signal')
        market_assessment = kalshi_analysis.get('market_assessment', {})
        
        # Build concise WHY with key data - Strategy First
        why_lines = []
        why_lines.append(f"Strategy: PREDICTION MARKET")
        why_lines.append(f"Type: Event-based trading")
        why_lines.append(f"Confidence: {confidence:.1f}% | Success Rate: {pop_from_sim:.1f}%")
        why_lines.append(f"Analysis: {rationale[:100]}...")
        why_text = "\n".join(why_lines)
        
        # Build message - Strategy First
        message = f"""🎯 KALSHI PREDICTION MARKET - {symbol}

━━━━━━━━━━━━━━━━━━━━━━
🎯 STRATEGY
━━━━━━━━━━━━━━━━━━━━━━

{why_text}

Exit: Hold until event resolution. Close early if probability shifts against position.

━━━━━━━━━━━━━━━━━━━━━━
📊 MARKET DETAILS:
━━━━━━━━━━━━━━━━━━━━━━

Signal: {kalshi_signal}
Confidence: {confidence:.1f}%
POP: {pop_from_sim:.1f}%

━━━━━━━━━━━━━━━━━━━━━━
📱 TRADE LINK:
━━━━━━━━━━━━━━━━━━━━━━

https://kalshi.com/markets/{symbol}"""
        
        return message

    async def post_signal(self, signal):
        message = self.format_signal_message(signal)
        return self.send_message(message)

    def send_alert(self, signal):
        """Send a high-confidence signal alert during monitoring mode."""
        message = self.format_signal_message(signal)
        return self.send_message(message)

def get_telegram_bot():
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    if not token or not chat_id:
        raise ValueError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set in .env file")
    return TelegramBot(token, chat_id)
