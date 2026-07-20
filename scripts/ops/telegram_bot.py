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
from utils.signal_data_quality import resolve_pop_pct

# Load environment variables
load_dotenv()

class TelegramBot:
    def __init__(self, token, chat_id):
        self.token = token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.request_timeout = 10

    def send_message(self, text):
        """Send a message to the Telegram chat (hard network timeout)."""
        if not text or not str(text).strip():
            print("[TELEGRAM] Skip empty message (unresolved company / suppressed)")
            return False
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text
        }
        try:
            response = requests.post(url, json=payload, timeout=self.request_timeout)
        except requests.Timeout:
            print(f"[TELEGRAM] API timeout after {self.request_timeout}s")
            return False
        except requests.RequestException as exc:
            print(f"[TELEGRAM] API request failed: {exc}")
            return False
        print(f"[TELEGRAM] API status {response.status_code}")
        if response.status_code != 200:
            print(f"[TELEGRAM] API response: {response.text[:200]}")
        return response.status_code == 200

    async def send_message_async(self, text):
        """Non-blocking send — keeps the asyncio event loop free."""
        return await asyncio.to_thread(self.send_message, text)

    def send_alert(self, signal):
        """Send a high-confidence signal alert during monitoring mode."""
        from utils.signal_identity import ensure_signal_identity, ensure_trade_levels
        data = self._as_signal_dict(signal)
        ok, _ = ensure_signal_identity(data)
        if not ok and not (
            str(data.get("symbol") or "").upper().startswith("KX")
            or data.get("kalshi_signal")
            or data.get("prediction_market")
        ):
            print(f"[TELEGRAM] Cannot resolve company for {data.get('symbol')} — resolving failed")
            return False
        ensure_trade_levels(data)
        message = self.format_signal_message(data)
        return self.send_message(message)

    async def send_alert_async(self, signal):
        return await asyncio.to_thread(self.send_alert, signal)

    @staticmethod
    def _as_signal_dict(signal) -> Dict[str, Any]:
        """Normalize Meta-Brain Signal objects or dicts for formatters."""
        if isinstance(signal, dict):
            return signal
        if signal is None:
            return {}
        if hasattr(signal, "to_dict") and callable(signal.to_dict):
            try:
                data = signal.to_dict()
                if isinstance(data, dict):
                    return data
            except Exception:
                pass
        out: Dict[str, Any] = {}
        for key in (
            "symbol", "ticker", "action", "confidence", "source", "title",
            "entry_price", "current_price", "target_price", "stop_price",
            "rationale", "kalshi_signal", "kalshi_action", "trade_link",
            "kalshi_analysis", "sim_scaled_confidence", "pop_from_sim",
            "monte_carlo_sim_score", "simulation_pop", "position_size",
            "fact_check", "details", "yes_price", "no_price",
            "implied_probability", "market_title",
        ):
            if hasattr(signal, key):
                val = getattr(signal, key)
                if val is not None:
                    out[key] = val
        details = getattr(signal, "details", None)
        if isinstance(details, dict):
            for k, v in details.items():
                out.setdefault(k, v)
        # Nested opportunity payloads sometimes carry the real trade link
        for nest_key in ("details", "kalshi_analysis", "kalshi_market_data"):
            nest = out.get(nest_key)
            if isinstance(nest, dict) and nest.get("trade_link") and not out.get("trade_link"):
                out["trade_link"] = nest["trade_link"]
        return out

    def format_signal_message(self, signal):
        signal = self._as_signal_dict(signal)
        # Check if this is a Kalshi prediction market signal
        signal_source = signal.get('source', 'unknown')
        has_kalshi_signal = signal.get('kalshi_signal', False)
        print(f"🔍 DEBUG: Signal source={signal_source}, has_kalshi_signal={has_kalshi_signal}")
        
        if signal_source == 'kalshi_prediction' or has_kalshi_signal:
            print("📈 Using Kalshi signal formatter (should include trade links)")
            return self.format_kalshi_signal_message(signal)
        elif signal_source == 'options_engine' or 'CALL' in str(signal.get('action', '')) or 'PUT' in str(signal.get('action', '')):
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
        pop_from_sim = resolve_pop_pct(signal)
        if pop_from_sim is None:
            raise ValueError(f"Cannot post {symbol} — no real POP from simulation")

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
        try:
            from utils.company_identity_registry import get_identity_registry
            resolved = get_identity_registry().resolve_for_alert(signal if isinstance(signal, dict) else {})
            if resolved:
                company_name = resolved
            elif str(company_name).strip().lower() in ("unknown", "n/a", ""):
                return ""
        except Exception:
            pass

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
        pop = resolve_pop_pct(signal)
        if pop is None:
            raise ValueError(f"Cannot post options alert for {underlying} — no real POP")
        
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
        from utils.signal_identity import (
            ensure_signal_identity,
            ensure_trade_levels,
            format_money,
        )

        if not isinstance(signal, dict):
            signal = self._as_signal_dict(signal)

        ok, company_name = ensure_signal_identity(signal)
        if not ok or not company_name:
            print(f"[TELEGRAM] Could not resolve real company for {signal.get('symbol')} — not posting Unknown")
            return ""
        ensure_trade_levels(signal)

        symbol = signal.get('symbol', '')
        action = signal.get('action', 'BUY')
        source = str(signal.get('source', 'unknown') or 'unknown').lower()
        asset_class = str(signal.get('asset_class') or signal.get('ledger_asset_class') or '').upper()
        is_day_trade = (
            asset_class == 'DAY_TRADE'
            or source in ('day_trading', 'heavy_mover', 'heavy_mover_watch', 'day_trade')
            or bool(signal.get('day_trade'))
            or str(signal.get('strategy') or '').lower() in ('day_trade', 'scalp', 'intraday')
        )

        # Fix confidence format - if it's already a percentage (like 75), don't multiply by 100
        confidence = signal.get('confidence', 0)
        if confidence > 1:
            confidence = confidence / 100  # Convert from percentage to decimal
        confidence_pct = confidence * 100

        # ADD CONFLUENCE SCORE if available
        confluence_score = signal.get('confluence_score', confidence_pct)

        pop_from_sim = resolve_pop_pct(signal)
        entry_price = format_money(signal.get('entry_price') or signal.get('current_price'))
        target_price = format_money(signal.get('target_price'))
        stop_price = format_money(signal.get('stop_loss') or signal.get('stop_price'))
        rr = signal.get('reward_risk_ratio') or signal.get('risk_reward_ratio')
        try:
            from utils.stock_reward_risk import compute_reward_risk
            if rr is None:
                rr = compute_reward_risk(
                    signal.get('entry_price') or signal.get('current_price'),
                    signal.get('stop_loss') or signal.get('stop_price'),
                    signal.get('target_price'),
                )
        except Exception:
            pass
        rr_display = f"{float(rr):.1f}:1" if rr is not None else "sized to 5:1"

        # Check if this is a fundamental analysis signal (undervalued stock)
        is_fundamental = source == 'fundamental_analysis' or signal.get('valuation_score') is not None

        # Build concise WHY with key data - Strategy First
        why_lines = []

        if is_day_trade:
            why_lines.append("Strategy: DAY TRADING")
            why_lines.append("Horizon: same session / intraday — not a swing hold")
            rationale = str(signal.get('rationale') or signal.get('title') or '')[:120]
            if rationale:
                why_lines.append(f"Type: {rationale}")
            why_lines.append(f"Confidence: {confidence_pct:.0f}%")
            if pop_from_sim is not None:
                why_lines.append(f"Success Rate: {pop_from_sim:.0f}%")
        elif is_fundamental:
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
            valuation_level = signal.get('valuation_level') or ''
            if str(valuation_level).strip().lower() in ('unknown', 'n/a', ''):
                valuation_level = ''
            expected_gain = signal.get('expected_gain', 0)
            
            if pe_ratio > 0 and industry_pe > 0:
                pe_vs_industry = (pe_ratio / industry_pe) * 100
                why_lines.append(f"Valuation: P/E {pe_ratio:.1f} vs Industry {industry_pe:.1f} ({pe_vs_industry:.0f}%)")
            
            if valuation_score and valuation_level:
                why_lines.append(f"Score: {valuation_score}/10 ({valuation_level})")
            elif valuation_score:
                why_lines.append(f"Score: {valuation_score}/10")
            
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
                why_lines.append(f"Target: ${format_money(signal.get('target_price'))}")
            
            why_lines.append(f"Confidence: {confidence_pct:.0f}%")
            if pop_from_sim is not None:
                why_lines.append(f"Success Rate: {pop_from_sim:.0f}%")
        
        why_text = "\n".join(why_lines)
        
        # Build exit strategy based on signal type
        if is_day_trade:
            exit_text = "Day trade: flatten before session close. Trail stop after +1R. Do not overnight unless explicitly promoted to swing."
        elif is_fundamental:
            exit_text = "Hold for 6-12 months for value realization. Scale out if target reached early. Reassess if fundamentals deteriorate."
        else:
            exit_text = "Scale out 50% at halfway point. Hold remainder for full target if momentum strong. Stop below recent low if price action fails."
        
        # Build message - Strategy First (Compact format)
        header = "DAY TRADE" if is_day_trade else action
        message = f"""🚀 PHASMA AI - {header} {symbol} ({company_name})

━━━━━━━━━━━━━━━━━━━━━━
🎯 STRATEGY
━━━━━━━━━━━━━━━━━━━━━━

{why_text}

Exit: {exit_text}

━━━━━━━━━━━━━━━━━━━━━━
📊 KEY LEVELS
━━━━━━━━━━━━━━━━━━━━━━

        Entry: ${entry_price} | Stop: ${stop_price} | Target: ${target_price}
        Angle: {rr_display} reward:risk (min 5:1)"""

        message += self._execution_status_block(signal)
        message += self._win_rate_block(signal)

        # Add combined FUNDAMENTALS & CONFLUENCE section for value stocks
        if is_fundamental:
            pe_ratio = signal.get('pe_ratio', 0)
            industry_pe = signal.get('industry_pe', 0)
            peg_ratio = signal.get('peg_ratio', 0)
            
            message += f"""

━━━━━━━━━━━━━━━━━━━━━━
💎 VALUATION
━━━━━━━━━━━━━━━━━━━━━━

P/E: {pe_ratio:.1f} (Industry: {industry_pe:.1f}) | PEG: {f'{peg_ratio:.2f}' if peg_ratio else 'not available'}
Score: {signal.get('valuation_score', 0)}/10 | Confluence: {confluence_score:.0f}/100"""
        
        return message
    
    def _win_rate_block(self, signal: Dict[str, Any]) -> str:
        """Rolling measured win-rates from the performance ledger."""
        from utils.signal_identity import format_sample_label

        overall = signal.get("win_rate_overall")
        stocks = signal.get("win_rate_stocks")
        day = signal.get("win_rate_day_trade")
        kalshi = signal.get("win_rate_kalshi")
        if not any([overall, stocks, day, kalshi]):
            try:
                from utils.trade_performance_ledger import (
                    ASSET_DAY_TRADE,
                    ASSET_KALSHI,
                    ASSET_STOCK,
                    get_trade_performance_ledger,
                )
                ledger = get_trade_performance_ledger()
                overall = ledger.win_rate().get("label")
                stocks = ledger.win_rate(asset_class=ASSET_STOCK).get("label")
                day = ledger.win_rate(asset_class=ASSET_DAY_TRADE).get("label")
                kalshi = ledger.win_rate(asset_class=ASSET_KALSHI).get("label")
            except Exception:
                return ""
        return (
            "\n\n━━━━━━━━━━━━━━━━━━━━━━\n"
            "📊 MEASURED WIN RATES\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Overall: {format_sample_label(overall)}\n"
            f"Stocks: {format_sample_label(stocks)} | Day trades: {format_sample_label(day)}\n"
            f"Kalshi (virtual): {format_sample_label(kalshi)}"
        )

    def _execution_status_block(self, signal: Dict[str, Any]) -> str:
        """Honest execution/reporting footer — report only, never implies live brokerage."""
        mode = signal.get("execution_mode", "ALERT_ONLY")
        decision = signal.get("execution_decision", "skipped")
        reason = signal.get("execution_reason") or signal.get("skip_reason") or ""
        label = signal.get("execution_alert_label") or ""
        if decision in ("filled", "submitted") and mode == "PAPER_ALPACA":
            label = "PAPER FILL (Alpaca)"
            fill_px = signal.get("fill_price")
            fill_qty = signal.get("fill_quantity")
            if fill_px is not None:
                reason = f"filled {fill_qty or 1} @ ${float(fill_px):.2f}" + (f" | {reason}" if reason else "")
        elif decision in ("skipped", "rejected") and not label:
            label = "NO TRADE"
        elif decision in ("filled", "submitted") and "PAPER" not in str(label).upper():
            label = "PAPER TRADE" if str(mode).startswith("PAPER") else label

        conf_type = signal.get("confidence_type", "heuristic")
        data_age = signal.get("data_age_seconds")
        data_age_str = f"{int(data_age)}s" if data_age is not None else "not stamped"
        price_source = signal.get("price_source", "signal")
        kalshi_intel = signal.get("kalshi_intel_only", False)
        mem_recent = signal.get("memory_recently_traded", False)
        risk_gate = signal.get("risk_gate") or "not evaluated"
        if str(risk_gate).lower() in ("n/a", "na", "unknown"):
            risk_gate = "not evaluated"
        sim_pop = signal.get("simulation_pop") or signal.get("monte_carlo_sim_score") or signal.get("pop_from_sim")
        sim_txt = f"{float(sim_pop):.1f}" if sim_pop is not None else "not simulated yet"
        lp = signal.get("llm_prediction") if isinstance(signal.get("llm_prediction"), dict) else {}
        lp_score = lp.get("prediction_score")
        lp_line = (
            f"LLM prediction: {lp_score}/100 ({lp.get('verdict')}) | grounding: {lp.get('grounding_status')}"
            if lp_score is not None
            else "LLM prediction: pending"
        )

        lines = [
            "",
            "━━━━━━━━━━━━━━━━━━━━━━",
            "🛡️ EXECUTION STATUS",
            "━━━━━━━━━━━━━━━━━━━━━━",
            f"Mode: {mode}",
            f"Execution: {decision}",
            f"Label: {label or 'pending report'}",
            f"Data age: {data_age_str} | Price source: {price_source}",
            f"Confidence type: {conf_type}",
            f"Simulation score (assumption-based): {sim_txt}",
            lp_line,
            f"Kalshi intel-only: {'yes' if kalshi_intel else 'no'}",
            f"Memory recently traded: {'yes' if mem_recent else 'no'}",
            f"Risk gate: {risk_gate}",
        ]
        if reason:
            lines.append(f"Skip/block reason: {reason}")
        return "\n".join(lines)

    def format_kalshi_signal_message(self, signal):
        """Format Kalshi prediction market signals with direct trade links."""
        signal = self._as_signal_dict(signal)

        symbol = signal.get('symbol') or signal.get('ticker') or 'pending symbol'
        kalshi_signal = str(signal.get('kalshi_signal') or signal.get('action') or 'BUY_YES').upper()
        confidence_raw = signal.get('sim_scaled_confidence', signal.get('confidence', 0))
        try:
            confidence = float(confidence_raw)
            if confidence <= 1.0:
                confidence *= 100.0
        except (TypeError, ValueError):
            confidence = 0.0

        pop_from_sim = resolve_pop_pct(signal)
        # Watch/intel alerts may not have a simulation POP — still post the bet link
        pop_display = f"{pop_from_sim:.1f}%" if pop_from_sim is not None else "not simulated yet"

        kalshi_analysis = signal.get('kalshi_analysis') or {}
        if not isinstance(kalshi_analysis, dict):
            kalshi_analysis = {}
        details = signal.get('details') if isinstance(signal.get('details'), dict) else {}
        market_data = signal.get('kalshi_market_data') or details.get('kalshi_market_data') or {}
        if not isinstance(market_data, dict):
            market_data = {}

        market_title = (
            signal.get('market_title')
            or signal.get('title')
            or market_data.get('title')
            or kalshi_analysis.get('market_title')
            or symbol
        )
        # Prefer live Kalshi API title over stale web-scrape labels
        if isinstance(market_title, str) and (
            "leaves apple" in market_title.lower()
            or "tim cook" in market_title.lower() and "kalshi" not in market_title.lower()
        ):
            api_title = market_data.get("title") or kalshi_analysis.get("rationale")
            if api_title:
                market_title = api_title

        rationale = kalshi_analysis.get('rationale') or signal.get('rationale') or 'AI-generated prediction signal'
        yes_price = (
            signal.get('yes_price')
            or market_data.get('yes_price')
            or market_data.get('yes_bid')
            or kalshi_analysis.get('yes_price')
        )
        no_price = (
            signal.get('no_price')
            or market_data.get('no_price')
            or market_data.get('no_bid')
            or kalshi_analysis.get('no_price')
        )
        implied = signal.get('implied_probability') or market_data.get('implied_probability')
        try:
            if implied is not None and float(implied) <= 1.0:
                yes_pct = float(implied) * 100.0
            elif yes_price is not None and float(yes_price) <= 1.0:
                yes_pct = float(yes_price) * 100.0
            elif yes_price is not None:
                yes_pct = float(yes_price)
            else:
                yes_pct = None
        except (TypeError, ValueError):
            yes_pct = None

        if "NO" in kalshi_signal:
            pick = "BUY NO"
            pick_detail = f"NO @ {float(no_price):.0f}¢" if no_price is not None and float(no_price) > 1 else (
                f"NO @ {float(no_price)*100:.0f}¢" if no_price is not None else "NO"
            )
        else:
            pick = "BUY YES"
            pick_detail = f"YES @ {float(yes_price):.0f}¢" if yes_price is not None and float(yes_price) > 1 else (
                f"YES @ {float(yes_price)*100:.0f}¢" if yes_price is not None else "YES"
            )

        trade_link = (
            signal.get('trade_link')
            or details.get('trade_link')
            or market_data.get('trade_link')
            or kalshi_analysis.get('trade_link')
        )
        if not trade_link:
            # Prefer event URL shape used by KalshiEngine.get_market_trade_link
            event = str(symbol).lower()
            if '-' in event:
                parts = event.split('-')
                if len(parts) > 2 and parts[-1].isdigit():
                    event = '-'.join(parts[:-1])
            trade_link = f"https://kalshi.com/events/{event}"

        yes_line = f"YES odds: {yes_pct:.1f}%" if yes_pct is not None else "YES odds: awaiting quote"
        why_lines = [
            "Strategy: PREDICTION MARKET",
            f"Market: {str(market_title)[:120]}",
            f"Pick: {pick} ({pick_detail})",
            yes_line,
            f"Confidence: {confidence:.1f}% | POP: {pop_display}",
            f"Analysis: {str(rationale)[:100]}",
        ]
        why_text = "\n".join(why_lines)

        message = f"""🎯 KALSHI TRADE ALERT (VIRTUAL) — {symbol}
Not live money — tracked in Phasma virtual book for win-rate learning.
Live Kalshi API orders: OFF

━━━━━━━━━━━━━━━━━━━━━━
🎯 STRATEGY
━━━━━━━━━━━━━━━━━━━━━━

{why_text}

Exit: Hold until event resolution. Close early if probability shifts against position.

━━━━━━━━━━━━━━━━━━━━━━
📊 BET (VIRTUAL BOOK)
━━━━━━━━━━━━━━━━━━━━━━

• YES — {pick_detail if pick == 'BUY YES' else 'alternate side'}
• NO  — {(pick_detail if pick == 'BUY NO' else 'alternate side')}
AI pick: {pick}

━━━━━━━━━━━━━━━━━━━━━━
📱 OPEN ON KALSHI (you place the bet yourself if you want)
━━━━━━━━━━━━━━━━━━━━━━

{trade_link}"""

        try:
            from engines.kalshi_virtual_book import get_kalshi_virtual_book
            wr = get_kalshi_virtual_book().win_rate_label()
            message += f"\n\nKalshi virtual win-rate: {wr}"
        except Exception:
            pass
        message += self._win_rate_block(signal)

        return message

    def format_heavy_mover_watchlist(self, movers, max_items=10):
        """One ranked watch digest for new-circulation / heavy-mover candidates."""
        if not movers:
            return None

        lines = [
            "NEW CIRCULATION — Potential heavy movers",
            "Pay attention to these stocks:",
            "",
        ]
        for i, mover in enumerate(movers[:max_items], 1):
            symbol = str(mover.get("symbol", "UNKNOWN")).upper()
            change = float(mover.get("change_pct", 0) or 0)
            vol_ratio = float(mover.get("volume_ratio", 0) or 0)
            price = mover.get("price")
            reason = str(mover.get("reason") or "Elevated volume + move").strip()
            if len(reason) > 90:
                reason = reason[:87] + "..."
            price_bit = f" ${price:.2f}" if isinstance(price, (int, float)) else ""
            lines.append(
                f"{i}. {symbol}{price_bit}  {change:+.1f}%  vol {vol_ratio:.1f}x — {reason}"
            )

        lines.append("")
        lines.append(f"Watch list: {min(len(movers), max_items)} of {len(movers)} qualified")
        lines.append("Watch only — not a trade signal.")
        return "\n".join(lines)

    async def post_signal(self, signal):
        message = self.format_signal_message(signal)
        if not message or not str(message).strip():
            print("[TELEGRAM] Signal suppressed — missing company identity or empty formatter")
            return False
        return await self.send_message_async(message)

def get_telegram_bot():
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    if not token or not chat_id:
        raise ValueError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set in .env file")
    return TelegramBot(token, chat_id)
