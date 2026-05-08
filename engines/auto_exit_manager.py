"""
Automated Exit Manager - Smart Position Exits
Implements AI Feedback: Automated stop-loss and profit-taking execution
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import os

class AutoExitManager:
    """Automatically manage position exits based on rules and simulations"""

    EXIT_REASONS = {
        'STOP_LOSS': 'Stop loss triggered',
        'PROFIT_TARGET': 'Profit target reached',
        'TIME_EXIT': 'Time-based exit',
        'TRAILING_STOP': 'Trailing stop triggered',
        'THETA_DECAY': 'Excessive theta decay',
        'IV_CRUSH': 'IV crush detected',
        'CRASH_ALERT': 'Market crash alert',
        'MANUAL': 'Manual exit requested',
        'SIMULATION_EXIT': 'Simulation-based exit'
    }

    def __init__(self, trade_db=None, broker_api=None, telegram_bot=None, config=None):
        """Initialize auto exit manager"""
        self.trade_db = trade_db
        self.broker_api = broker_api
        self.telegram_bot = telegram_bot
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Exit tracking
        self.exit_history = []
        self.pending_exits = []

        # Default exit rules
        self.default_rules = {
            'stop_loss_pct': -0.10,      # -10% stop loss (will be overridden by simulation)
            'profit_target_pct': 0.20,    # +20% profit target (will be overridden by simulation)
            'max_hold_days': 30,          # Max 30 days
            'trailing_stop_pct': 0.05,    # 5% trailing stop
            'theta_threshold': -0.15      # Exit if theta > 15% of position
        }

        # Memory path
        self.memory_path = 'phasma_core_memory/auto_exits'
        os.makedirs(self.memory_path, exist_ok=True)

        # Initialize Monte Carlo engine for simulation-based exits
        self.monte_carlo_engine = None
        try:
            from engines.monte_carlo_engine import get_monte_carlo_engine
            self.monte_carlo_engine = get_monte_carlo_engine(config)
            self.logger.info("Monte Carlo engine initialized for simulation-based exits")
        except Exception as e:
            self.logger.warning(f"Could not initialize Monte Carlo engine: {e}")
    
    async def monitor_positions(self, check_interval: int = 60):
        """
        Continuously monitor positions for exit conditions
        
        Args:
            check_interval: Seconds between checks (default 60)
        """
        self.logger.info("Starting automated exit monitoring...")
        
        while True:
            try:
                positions = self._get_open_positions()
                
                for position in positions:
                    await self._check_exit_conditions(position)
                
                # Wait before next check
                await asyncio.sleep(check_interval)
                
            except Exception as e:
                self.logger.error(f"Error in position monitoring: {e}")
                await asyncio.sleep(check_interval)
    
    async def _check_exit_conditions(self, position: Dict):
        """Check if position meets any exit conditions"""
        try:
            symbol = position['symbol']
            current_price = self._get_current_price(symbol)

            if not current_price:
                return

            # Calculate P&L
            entry_price = position['entry_price']
            pnl_pct = (current_price - entry_price) / entry_price

            # Get position rules (custom or default)
            rules = position.get('exit_rules', self.default_rules)

            # RUN SIMULATION-BASED EXIT ANALYSIS
            simulation_exit = await self._check_simulation_exit(position, current_price)
            if simulation_exit:
                await self.execute_exit(position, 'SIMULATION_EXIT', simulation_exit)
                return

            # Check stop loss
            if pnl_pct <= rules.get('stop_loss_pct', -0.10):
                await self.execute_exit(position, 'STOP_LOSS', {
                    'trigger_price': current_price,
                    'pnl_pct': pnl_pct
                })
                return

            # Check profit target
            target_pct = rules.get('profit_target_pct', position.get('target_pct', 0.20))
            if pnl_pct >= target_pct:
                await self.execute_exit(position, 'PROFIT_TARGET', {
                    'trigger_price': current_price,
                    'pnl_pct': pnl_pct
                })
                return

            # Check trailing stop
            if self._check_trailing_stop(position, current_price):
                await self.execute_exit(position, 'TRAILING_STOP', {
                    'trigger_price': current_price,
                    'pnl_pct': pnl_pct
                })
                return

            # Check time-based exit
            if self._should_exit_by_time(position):
                await self.execute_exit(position, 'TIME_EXIT', {
                    'trigger_price': current_price,
                    'pnl_pct': pnl_pct,
                    'days_held': position.get('days_held', 0)
                })
                return

            # Check theta decay (options only)
            if position.get('type') in ['CALL', 'PUT']:
                if self._check_theta_decay(position):
                    await self.execute_exit(position, 'THETA_DECAY', {
                        'trigger_price': current_price,
                        'theta': position.get('theta', 0)
                    })
                    return

        except Exception as e:
            self.logger.error(f"Error checking exit conditions for {position.get('symbol')}: {e}")

    async def _check_simulation_exit(self, position: Dict, current_price: float) -> Optional[Dict]:
        """
        Use Monte Carlo simulation to estimate optimal exit point

        Returns exit details if simulation suggests exiting, None otherwise
        """
        if not self.monte_carlo_engine:
            return None

        try:
            symbol = position['symbol']
            entry_price = position['entry_price']
            current_pnl_pct = (current_price - entry_price) / entry_price

            # Create signal for simulation
            signal = {
                'symbol': symbol,
                'current_price': current_price,
                'entry_price': entry_price,
                'confidence': position.get('confidence', 0.5),
                'sector': position.get('sector', 'Unknown'),
                'action': position.get('action', 'BUY'),
                'holding_days': position.get('days_held', 1)
            }

            # Run stock simulation
            sim_results = self.monte_carlo_engine.run_stock_simulation(signal)

            win_rate = sim_results.get('win_rate', 0.5)
            profit_potential = sim_results.get('profit_potential', 0)
            optimal_exit_day = sim_results.get('optimal_exit_day', 5)
            volatility = sim_results.get('volatility_used', 0.35)

            # SIMULATION-BASED EXIT LOGIC
            exit_reasons = []

            # 1. Exit if win rate drops below 40% (simulation shows low probability of success)
            if win_rate < 0.40:
                exit_reasons.append(f"Low win rate ({win_rate:.1%})")

            # 2. Exit if profit potential is negative (simulation expects decline)
            if profit_potential < -0.05:
                exit_reasons.append(f"Negative profit potential ({profit_potential:.1%})")

            # 3. Exit if already holding longer than optimal exit day
            days_held = position.get('days_held', 0)
            if days_held > optimal_exit_day:
                exit_reasons.append(f"Held {days_held} days vs optimal {optimal_exit_day}")

            # 4. Exit if volatility is extreme and we're in profit (lock in gains)
            if volatility > 0.50 and current_pnl_pct > 0.05:
                exit_reasons.append(f"High volatility ({volatility:.1%}) with profit ({current_pnl_pct:.1%})")

            # 5. Exit if simulation shows downside risk > 20%
            percentile_10 = sim_results.get('percentile_10', 0)
            downside_risk = (percentile_10 - current_price) / current_price
            if downside_risk < -0.20:
                exit_reasons.append(f"High downside risk ({downside_risk:.1%})")

            # If any exit conditions met, return exit details
            if exit_reasons:
                return {
                    'trigger_price': current_price,
                    'pnl_pct': current_pnl_pct,
                    'simulation_details': {
                        'win_rate': win_rate,
                        'profit_potential': profit_potential,
                        'optimal_exit_day': optimal_exit_day,
                        'volatility': volatility,
                        'downside_risk': downside_risk,
                        'exit_reasons': exit_reasons
                    }
                }

            # Update position with simulation-based stop loss
            # Calculate dynamic stop loss based on simulation downside risk
            if downside_risk < -0.10:  # If simulation shows >10% downside risk
                dynamic_stop_pct = max(downside_risk * 0.8, -0.15)  # Use 80% of downside risk, max -15%
                if self.trade_db:
                    new_stop_price = entry_price * (1 + dynamic_stop_pct)
                    self.trade_db.update_position_stop(position['id'], new_stop_price)
                    self.logger.info(f"Updated dynamic stop for {symbol} to ${new_stop_price:.2f} ({dynamic_stop_pct:.1%})")

            return None

        except Exception as e:
            self.logger.error(f"Error in simulation exit check for {position.get('symbol')}: {e}")
            return None
    
    async def execute_exit(self, position: Dict, reason: str, details: Dict = None):
        """
        Execute position exit
        
        Args:
            position: Position details
            reason: Exit reason code
            details: Additional exit details
        """
        try:
            symbol = position['symbol']
            
            self.logger.info(f"Executing exit for {symbol}: {reason}")
            
            # Build exit order
            exit_order = {
                'symbol': symbol,
                'action': 'SELL' if position['action'] == 'BUY' else 'BUY',
                'quantity': position['quantity'],
                'type': 'MARKET',
                'timestamp': datetime.now().isoformat(),
                'reason': reason,
                'details': details or {}
            }
            
            # Execute through broker API
            if self.broker_api:
                execution_result = await self._execute_broker_order(exit_order)
                exit_order['execution'] = execution_result
            else:
                # Simulated execution
                exit_order['execution'] = {
                    'status': 'SIMULATED',
                    'fill_price': details.get('trigger_price', position['entry_price']),
                    'timestamp': datetime.now().isoformat()
                }
            
            # Update position in database
            if self.trade_db:
                self.trade_db.close_position(
                    position['id'],
                    exit_price=exit_order['execution']['fill_price'],
                    exit_reason=reason
                )
            
            # Log exit
            self._log_exit(position, exit_order)
            
            # Send notification
            await self._send_exit_notification(position, exit_order)
            
            return exit_order
            
        except Exception as e:
            self.logger.error(f"Error executing exit: {e}")
            return {'error': str(e)}
    
    async def execute_partial_exit(
        self,
        position: Dict,
        exit_pct: float = 0.50,
        reason: str = 'PARTIAL_PROFIT_TARGET',
        details: Dict = None
    ):
        """
        Execute partial position exit (scale out)
        ChatGPT Enhancement: Sell part at target, let rest ride
        
        Args:
            position: Position details
            exit_pct: Percentage of position to exit (default 50%)
            reason: Exit reason code
            details: Additional exit details
        """
        try:
            symbol = position['symbol']
            partial_quantity = position['quantity'] * exit_pct
            
            self.logger.info(f"Executing partial exit for {symbol}: {exit_pct:.0%} of position")
            
            # Build partial exit order
            exit_order = {
                'symbol': symbol,
                'action': 'SELL' if position['action'] == 'BUY' else 'BUY',
                'quantity': partial_quantity,
                'type': 'MARKET',
                'timestamp': datetime.now().isoformat(),
                'reason': f"{reason}_PARTIAL_{exit_pct:.0%}",
                'details': details or {}
            }
            
            # Execute through broker API
            if self.broker_api:
                execution_result = await self._execute_broker_order(exit_order)
                exit_order['execution'] = execution_result
            else:
                # Simulated execution
                exit_order['execution'] = {
                    'status': 'SIMULATED',
                    'fill_price': details.get('trigger_price', position['entry_price']),
                    'timestamp': datetime.now().isoformat()
                }
            
            # Update position quantity
            remaining_quantity = position['quantity'] - partial_quantity
            if self.trade_db:
                self.trade_db.update_position_quantity(
                    position['id'],
                    remaining_quantity
                )
            
            # Tighten stop on remaining position
            # Move stop to breakeven or tighter trailing stop
            if self.trade_db:
                new_stop = position['entry_price']  # Breakeven
                self.trade_db.update_position_stop(position['id'], new_stop)
            
            # Log partial exit
            self._log_exit(position, exit_order)
            
            # Send notification
            await self._send_partial_exit_notification(position, exit_order, exit_pct)
            
            return exit_order
            
        except Exception as e:
            self.logger.error(f"Error executing partial exit: {e}")
            return {'error': str(e)}
    
    async def _send_partial_exit_notification(
        self,
        position: Dict,
        exit_order: Dict,
        exit_pct: float
    ):
        """Send partial exit notification via Telegram"""
        try:
            if not self.telegram_bot:
                return
            
            pnl_pct = exit_order.get('details', {}).get('pnl_pct', 0)
            
            message = f"""
🎯 PARTIAL EXIT EXECUTED

Symbol: {position['symbol']}
Closed: {exit_pct:.0%} of position
Remaining: {1-exit_pct:.0%}

Entry: ${position['entry_price']:.2f}
Exit: ${exit_order['execution']['fill_price']:.2f}
P&L: {pnl_pct:+.1%}

Stop moved to breakeven on remaining position ✓
"""
            
            await self.telegram_bot.send_message(message)
            
        except Exception as e:
            self.logger.error(f"Error sending partial exit notification: {e}")
    
    def _get_open_positions(self) -> List[Dict]:
        """Get all open positions"""
        if not self.trade_db:
            return []
        
        try:
            return self.trade_db.get_open_positions()
        except Exception as e:
            self.logger.error(f"Error getting positions: {e}")
            return []
    
    def _get_current_price(self, symbol: str) -> Optional[float]:
        """Get current market price for symbol"""
        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            data = ticker.history(period='1d', interval='1m')
            
            if not data.empty:
                return data['Close'].iloc[-1]
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting price for {symbol}: {e}")
            return None
    
    def _check_trailing_stop(self, position: Dict, current_price: float) -> bool:
        """Check if trailing stop is triggered"""
        try:
            # Get highest price since entry
            high_price = position.get('high_price', position['entry_price'])
            
            # Update high if current is higher
            if current_price > high_price:
                high_price = current_price
                if self.trade_db:
                    self.trade_db.update_position_high(position['id'], high_price)
            
            # Calculate drawdown from high
            drawdown = (current_price - high_price) / high_price
            
            # Trigger if drawdown exceeds trailing stop
            trailing_pct = position.get('trailing_stop_pct', 0.05)
            return drawdown <= -trailing_pct
            
        except Exception as e:
            self.logger.error(f"Error checking trailing stop: {e}")
            return False
    
    def _should_exit_by_time(self, position: Dict) -> bool:
        """Check if position should exit based on time"""
        try:
            entry_date = position.get('entry_date')
            if not entry_date:
                return False
            
            if isinstance(entry_date, str):
                entry_date = datetime.fromisoformat(entry_date)
            
            days_held = (datetime.now() - entry_date).days
            max_days = position.get('max_hold_days', self.default_rules['max_hold_days'])
            
            return days_held >= max_days
            
        except Exception as e:
            self.logger.error(f"Error checking time exit: {e}")
            return False
    
    def _check_theta_decay(self, position: Dict) -> bool:
        """Check if theta decay is excessive"""
        try:
            theta = abs(position.get('theta', 0))
            position_value = position.get('current_value', 0)
            
            if position_value == 0:
                return False
            
            # If daily theta decay is > 15% of position value, exit
            theta_pct = theta / position_value
            threshold = abs(self.default_rules['theta_threshold'])
            
            return theta_pct > threshold
            
        except Exception as e:
            self.logger.error(f"Error checking theta decay: {e}")
            return False
    
    async def _execute_broker_order(self, order: Dict) -> Dict:
        """Execute order through broker API"""
        try:
            # Check if we have Alpaca connected
            if hasattr(self.broker_api, 'execute_sell') and order.get('action') == 'SELL':
                # Execute through Alpaca
                symbol = order['symbol']
                quantity = order['quantity']
                price = order.get('details', {}).get('trigger_price', 0)
                reason = order.get('reason', 'AUTO_EXIT')
                
                result = self.broker_api.execute_sell(symbol, quantity, price, reason)
                
                if result.get('success'):
                    return {
                        'status': 'FILLED',
                        'fill_price': result.get('price', price),
                        'fill_quantity': quantity,
                        'timestamp': result.get('timestamp', datetime.now().isoformat()),
                        'order_id': result.get('order_id', f"ALPACA_{datetime.now().strftime('%Y%m%d%H%M%S')}"),
                        'platform': 'Alpaca'
                    }
                else:
                    return {
                        'status': 'FAILED',
                        'error': result.get('error', 'Unknown error'),
                        'timestamp': datetime.now().isoformat()
                    }
            else:
                # Fallback to simulation
                return {
                    'status': 'FILLED',
                    'fill_price': order.get('details', {}).get('trigger_price', 0),
                    'fill_quantity': order['quantity'],
                    'timestamp': datetime.now().isoformat(),
                    'order_id': f"SIM_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    'platform': 'Simulation'
                }
        except Exception as e:
            self.logger.error(f"Broker order execution failed: {e}")
            return {
                'status': 'FAILED',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _log_exit(self, position: Dict, exit_order: Dict):
        """Log exit to history"""
        try:
            exit_record = {
                'timestamp': datetime.now().isoformat(),
                'symbol': position['symbol'],
                'position_id': position.get('id'),
                'entry_price': position['entry_price'],
                'exit_price': exit_order['execution']['fill_price'],
                'quantity': position['quantity'],
                'pnl': exit_order.get('details', {}).get('pnl_pct', 0),
                'reason': exit_order['reason'],
                'days_held': position.get('days_held', 0)
            }
            
            self.exit_history.append(exit_record)
            
            # Save to file
            date_str = datetime.now().strftime('%Y-%m-%d')
            filename = f"{self.memory_path}/exits_{date_str}.json"
            
            exits = []
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    exits = json.load(f)
            
            exits.append(exit_record)
            
            with open(filename, 'w') as f:
                json.dump(exits, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error logging exit: {e}")
    
    async def _send_exit_notification(self, position: Dict, exit_order: Dict):
        """Send exit notification via Telegram"""
        try:
            if not self.telegram_bot:
                return

            reason = self.EXIT_REASONS.get(exit_order['reason'], exit_order['reason'])
            pnl_pct = exit_order.get('details', {}).get('pnl_pct', 0)

            # Base message
            message = f"""
🔔 AUTO EXIT EXECUTED

Symbol: {position['symbol']}
Reason: {reason}
Entry: ${position['entry_price']:.2f}
Exit: ${exit_order['execution']['fill_price']:.2f}
P&L: {pnl_pct:+.1%}
Days Held: {position.get('days_held', 0)}

Status: {exit_order['execution']['status']}
"""

            # Add simulation details if available
            if exit_order['reason'] == 'SIMULATION_EXIT':
                sim_details = exit_order.get('details', {}).get('simulation_details', {})
                if sim_details:
                    message += f"""
📊 SIMULATION ANALYSIS:
Win Rate: {sim_details.get('win_rate', 0):.1%}
Profit Potential: {sim_details.get('profit_potential', 0):.1%}
Optimal Exit Day: {sim_details.get('optimal_exit_day', 0)}
Volatility: {sim_details.get('volatility', 0):.1%}
Downside Risk: {sim_details.get('downside_risk', 0):.1%}

Exit Reasons:
"""
                    for reason_text in sim_details.get('exit_reasons', []):
                        message += f"  • {reason_text}\n"

            await self.telegram_bot.send_message(message)

        except Exception as e:
            self.logger.error(f"Error sending exit notification: {e}")
    
    def get_exit_statistics(self, period_days: int = 30) -> Dict:
        """Get exit statistics"""
        try:
            cutoff = datetime.now() - timedelta(days=period_days)
            recent_exits = [
                e for e in self.exit_history 
                if datetime.fromisoformat(e['timestamp']) > cutoff
            ]
            
            if not recent_exits:
                return {'total_exits': 0}
            
            # Count by reason
            by_reason = {}
            for exit in recent_exits:
                reason = exit['reason']
                by_reason[reason] = by_reason.get(reason, 0) + 1
            
            # Calculate success rates
            profitable_exits = sum(1 for e in recent_exits if e['pnl'] > 0)
            
            return {
                'total_exits': len(recent_exits),
                'period_days': period_days,
                'by_reason': by_reason,
                'profitable_exits': profitable_exits,
                'loss_exits': len(recent_exits) - profitable_exits,
                'win_rate': profitable_exits / len(recent_exits) if recent_exits else 0,
                'avg_hold_days': sum(e['days_held'] for e in recent_exits) / len(recent_exits)
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating exit stats: {e}")
            return {'error': str(e)}
    
    def print_exit_statistics(self, period_days: int = 30):
        """Print formatted exit statistics"""
        stats = self.get_exit_statistics(period_days)
        
        print("\n" + "="*60)
        print(f"AUTO EXIT STATISTICS - Last {period_days} Days")
        print("="*60)
        print(f"Total Exits: {stats.get('total_exits', 0)}")
        print(f"Profitable: {stats.get('profitable_exits', 0)}")
        print(f"Losses: {stats.get('loss_exits', 0)}")
        print(f"Win Rate: {stats.get('win_rate', 0):.1%}")
        print(f"Avg Hold: {stats.get('avg_hold_days', 0):.1f} days")
        
        if 'by_reason' in stats:
            print("\nEXITS BY REASON:")
            for reason, count in sorted(stats['by_reason'].items(), key=lambda x: x[1], reverse=True):
                reason_name = self.EXIT_REASONS.get(reason, reason)
                print(f"  {reason_name}: {count}")
        
        print("="*60 + "\n")
    
    def set_position_exit_rules(
        self,
        position_id: str,
        stop_loss_pct: float = None,
        profit_target_pct: float = None,
        max_hold_days: int = None,
        trailing_stop_pct: float = None
    ):
        """Set custom exit rules for specific position"""
        try:
            rules = {}
            
            if stop_loss_pct is not None:
                rules['stop_loss_pct'] = stop_loss_pct
            if profit_target_pct is not None:
                rules['profit_target_pct'] = profit_target_pct
            if max_hold_days is not None:
                rules['max_hold_days'] = max_hold_days
            if trailing_stop_pct is not None:
                rules['trailing_stop_pct'] = trailing_stop_pct
            
            if self.trade_db:
                self.trade_db.update_position_rules(position_id, rules)
            
            self.logger.info(f"Updated exit rules for position {position_id}")
            
        except Exception as e:
            self.logger.error(f"Error setting position rules: {e}")
