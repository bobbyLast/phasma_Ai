"""
Phasma AI - Meta-Brain Controller
Central intelligence system that coordinates all Phasma AI components.
Implements signal arbitration, capital allocation, risk governance, and transparency.
"""

import asyncio
import json
import logging
import os
import sys
from collections import defaultdict, deque
from datetime import datetime, timedelta

class PhasmaConfig:
    """System configuration management"""

    def __init__(self, config_path = None):
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                self.data = json.load(f)
        else:
            # Default configuration with nested structure
            self.data = {
                "bankroll": 2000,  # Level 2 account maximum
                "pop_threshold": 0.5,  # Lowered from 0.7 to allow more trades
                "risk_per_trade": 0.01,
                "max_drawdown": 0.1,
                "daily_loss_limit": 0.02,
                "max_concurrent_trades": 2,
                "webull_level2_enabled": True,
                "news_apis_enabled": True,
                "kalshi_enabled": True,
                "crypto_enabled": True,
                "telegram_enabled": True,
                "data_sources": [
                    "saurav_newsapi",
                    "thenews_api",
                    "marketaux",
                    "yahoo_rss",
                    "reuters_rss",
                    "x_search",
                    "etherscan"
                ],
                "assets": {
                    "sector_watchlist": {
                        "AI": {
                            "keywords": ["AI", "artificial intelligence", "machine learning", "neural", "chatbot", "automation", "tech", "software", "data", "algorithm"],
                            "focus": "AI/tech stocks moving on innovation and earnings",
                            "potential": "2-10x on hype cycles",
                            "feeds": ["yahoo_rss", "reuters_rss", "cnbc_rss", "x_search"]
                        },
                        "FOOD": {
                            "keywords": ["food", "beverage", "restaurant", "retail", "consumer", "brand", "snack", "grocery", "dining", "franchise"],
                            "focus": "Consumer staples and dining trends",
                            "potential": "1.5-3x on earnings",
                            "feeds": ["reuters_rss", "cnbc_rss", "x_search"]
                        }
                    }
                }
            }

    def get(self, key, default = None):
        """Get configuration value with support for nested keys"""
        keys = key.split('.') if '.' in key else [key]
        current = self.data

        try:
            for k in keys:
                current = current[k]
            return current
        except (KeyError, TypeError):
            return default

    def set(self, key, value):
        """Set configuration value with support for nested keys"""
        keys = key.split('.') if '.' in key else [key]

        # Navigate to the parent of the target key
        current = self.data
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]

        # Set the final value
        current[keys[-1]] = value

    def save(self, config_path):
        """Save configuration to file"""
        with open(config_path, 'w') as f:
            json.dump(self.data, f, indent=4)

class Signal:
    """Trading signal representation"""

    def __init__(self, symbol, action, confidence, position_size, rationale, source, timestamp = None, **kwargs):
        self.symbol = symbol
        self.action = action  # BUY_CALL, BUY_PUT, SELL_CALL, SELL_PUT
        self.confidence = confidence  # 0.0 to 1.0
        self.pop = confidence  # Probability of Profit
        self.position_size = position_size
        self.rationale = rationale
        self.source = source
        self.timestamp = timestamp or datetime.now()
        self.status = "pending"  # pending, approved, rejected, executed

        # Add any additional fields dynamically
        for key, value in kwargs.items():
            setattr(self, key, value)

    def to_dict(self):
        """Convert to dictionary with JSON-serializable datetime"""
        # Get all attributes except methods and private attributes
        result = {}
        for key in dir(self):
            if not key.startswith('_') and not callable(getattr(self, key)):
                value = getattr(self, key)
                # Convert datetime objects to ISO format strings
                if hasattr(value, 'isoformat'):
                    result[key] = value.isoformat()
                else:
                    result[key] = value

        return result

class RiskManager:
    """Risk management and governance"""

    def __init__(self, config):
        self.config = config
        self.daily_pnl = 0.0
        self.total_drawdown = 0.0
        self.open_positions = {}
        self.trade_history = deque(maxlen=1000)
        self.start_time = datetime.now()

    def _get_starting_bankroll(self) -> float:
        """Starting bankroll from config (does not shrink).

        We treat this as total capital and subtract any capital committed
        to open positions to derive available bankroll for new trades.
        """
        try:
            return float(self.config.get("bankroll", 10000))
        except Exception:
            return 10000.0

    def _get_capital_in_use(self) -> float:
        """Sum of position_size across all open positions."""
        total = 0.0
        for pos in self.open_positions.values():
            try:
                sig = pos.get("signal", {}) or {}
                size = float(sig.get("position_size", 0.0))
                if size > 0:
                    total += size
            except Exception:
                continue
        return total

    def get_available_bankroll(self) -> float:
        """Bankroll available for new trades after accounting for open positions."""
        starting = self._get_starting_bankroll()
        used = self._get_capital_in_use()
        return max(0.0, starting - used)

    def check_risk_limits(self, signal):
        """Check if signal meets risk criteria"""
        bankroll = self.get_available_bankroll()

        # Check daily loss limit
        if self.daily_pnl < -self.config.get("daily_loss_limit", 0.02) * bankroll:
            return False, "Daily loss limit exceeded"

        # Check max drawdown
        if self.total_drawdown > self.config.get("max_drawdown", 0.1) * bankroll:
            return False, "Maximum drawdown exceeded"

        # Check concurrent trades
        if len(self.open_positions) >= self.config.get("max_concurrent_trades", 2):
            return False, "Maximum concurrent trades exceeded"

        # Check position size
        if signal.position_size > bankroll * self.config.get("risk_per_trade", 0.01):
            return False, "Position size too large"

        return True, "Risk check passed"

    def update_pnl(self, pnl_change):
        """Update daily P&L"""
        self.daily_pnl += pnl_change

        # Reset daily P&L if new day
        if datetime.now().date() != self.start_time.date():
            self.daily_pnl = pnl_change
            self.start_time = datetime.now()

    def add_position(self, symbol, position):
        """Add open position"""
        self.open_positions[symbol] = position

    def close_position(self, symbol):
        """Close position"""
        if symbol in self.open_positions:
            del self.open_positions[symbol]

class PhasmaMetaBrain:
    """Meta-Brain: Central intelligence coordinating all Phasma AI components"""

    def __init__(self, config_path = None):
        self.config = PhasmaConfig(config_path)
        self.risk_manager = RiskManager(self.config)
        self.signals = defaultdict(list)
        self.active_engines = {}
        self.performance_history = deque(maxlen=1000)
        self.is_running = False
        self.logger = self._setup_logging()

        # Initialize components
        self._initialize_engines()

        # Use ASCII-only message to avoid encoding issues
        self.logger.info("[START] Phasma Meta-Brain initialized")

    def _setup_logging(self):
        """Setup logging system with ASCII-only output"""
        logger = logging.getLogger("PhasmaMetaBrain")
        logger.setLevel(logging.INFO)

        # Prevent messages from also being handled by the root logger (avoids duplicates)
        logger.propagate = False

        # Remove any existing handlers
        if logger.hasHandlers():
            logger.handlers.clear()

        # Create a custom formatter that handles Unicode characters
        class ASCIIFormatter(logging.Formatter):
            def format(self, record):
                # First, let the parent class do its formatting
                result = super().format(record)
                
                # Replace common Unicode characters with ASCII equivalents
                replacements = {
                    '🚀': '[START]',
                    '✅': '[OK]',
                    '❌': '[ERROR]',
                    '⚡': '[!]',
                    '🧠': '[AI]',
                    '📊': '[CHART]',
                    '📈': '[UP]',
                    '📉': '[DOWN]',
                    'ℹ️': '[INFO]',
                    '⚠️': '[WARN]',
                    '❓': '[?]',
                    '🔍': '[SEARCH]',
                    '🔒': '[LOCK]',
                    '🔓': '[UNLOCK]',
                    '📝': '[NOTE]',
                    '🔔': '[ALERT]',
                    '━': '=',
                    '•': '*',
                    '✓': '[OK]',
                    '🔍': '[SEARCH]'
                }
                
                # Replace known Unicode characters
                for uni, ascii_equiv in replacements.items():
                    result = result.replace(uni, ascii_equiv)
                
                # Replace any remaining non-ASCII characters with '?'
                result = result.encode('ascii', 'replace').decode('ascii')
                return result
        
        # Set up the handler and formatter
        console_handler = logging.StreamHandler()
        formatter = ASCIIFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)
        logger.addHandler(console_handler)
        return logger

    def _initialize_engines(self):
        """Initialize all trading engines"""
        # This will be populated as we implement each engine
        self.engines = {
            'news': None,      # News and sentiment analysis
            'options': None,   # Options trading engine
            'kalshi': None,    # Kalshi event prediction
            'crypto': None,    # Crypto analysis
            'risk': self.risk_manager  # Risk management (already initialized)
        }

        self.logger.info(f"Initialized {len(self.engines)} engine slots")

    def register_engine(self, engine_name, engine_instance):
        """Register a trading engine"""
        self.engines[engine_name] = engine_instance
        self.active_engines[engine_name] = True
        self.logger.info(f"Registered engine: {engine_name}")

    async def collect_signals(self):
        """Collect signals from all active engines"""
        all_signals = []

        for engine_name, engine in self.engines.items():
            if engine and self.active_engines.get(engine_name, False):
                try:
                    # Each engine should implement a get_signals() method
                    if hasattr(engine, 'get_signals'):
                        engine_signals = await engine.get_signals()
                        all_signals.extend(engine_signals)
                        self.logger.info(f"Collected {len(engine_signals)} signals from {engine_name}")
                except Exception as e:
                    self.logger.error(f"Error collecting signals from {engine_name}: {e}")

        return all_signals

    def arbitrate_signals(self, signals, pop_threshold=None):
        """Arbitrate conflicting signals using confidence weighting"""
        if not signals:
            return []

        # Group signals by symbol
        symbol_signals = defaultdict(list)
        for signal in signals:
            symbol_signals[signal.symbol].append(signal)

        arbitrated_signals = []

        for symbol, symbol_signal_list in symbol_signals.items():
            if len(symbol_signal_list) == 1:
                # No conflict, use the signal as-is
                arbitrated_signals.append(symbol_signal_list[0])
            else:
                # Multiple signals, need arbitration
                best_signal = self._resolve_conflict(symbol_signal_list, pop_threshold)
                if best_signal:
                    arbitrated_signals.append(best_signal)

        return arbitrated_signals

    def _resolve_conflict(self, signals, pop_threshold=None):
        """Resolve conflicting signals using confidence weighting"""
        if not signals:
            return None

        # Use provided threshold; if config is "auto"/missing, fall back to a low default (30%)
        cfg_threshold = self.config.get("pop_threshold", None)
        if cfg_threshold == "auto" or cfg_threshold is None:
            cfg_threshold = 0.3

        threshold = pop_threshold if pop_threshold is not None else cfg_threshold

        # Calculate weighted scores
        best_signal = None
        best_score = 0

        for signal in signals:
            # Base score from confidence
            score = signal.confidence

            # Boost for high-POP signals
            if signal.pop >= threshold:
                score += 0.1

            # Boost for reliable sources (this would be learned over time)
            reliable_sources = ["news_api", "options_engine", "kalshi"]
            if signal.source in reliable_sources:
                score += 0.05

            # Apply risk adjustment
            risk_ok, risk_reason = self.risk_manager.check_risk_limits(signal)
            if not risk_ok:
                score = 0  # Reject signal if risk limits exceeded

            if score > best_score:
                best_score = score
                best_signal = signal

        if best_signal and best_score > threshold:
            best_signal.status = "approved"
            self.logger.info(f"Arbitrated {best_signal.symbol}: {best_signal.action} "
                           f"(Score: {best_score:.2f}, Source: {best_signal.source})")
            return best_signal

        return None

    def allocate_capital(self, signal):
        """Allocate capital based on confidence and risk"""
        bankroll = self.config.get("bankroll", 10000)

        # Base allocation from risk per trade
        base_allocation = bankroll * self.config.get("risk_per_trade", 0.01)

        # Adjust based on confidence
        confidence_multiplier = signal.confidence
        adjusted_allocation = base_allocation * confidence_multiplier

        # Apply risk limits
        max_allocation = bankroll * self.config.get("risk_per_trade", 0.01)
        final_allocation = min(adjusted_allocation, max_allocation)

        return final_allocation

    def update_performance(self, signal, outcome):
        """Update performance tracking and learning"""
        performance_record = {
            "symbol": signal.symbol,
            "signal": signal.to_dict(),
            "outcome": outcome,
            "timestamp": datetime.now().isoformat()
        }

        self.performance_history.append(performance_record)

        # Update risk manager
        pnl_change = outcome.get("pnl", 0)
        self.risk_manager.update_pnl(pnl_change)

        # Log performance
        self.logger.info(f"Performance update: {signal.symbol} {signal.action} "
                        f"P&L: ${pnl_change:.2f}")

    async def run_cycle(self):
        """Run one complete trading cycle"""
        self.logger.info("Starting Phasma trading cycle")

        # 1. Collect signals from all engines
        signals = await self.collect_signals()

        # 2. Arbitrate conflicting signals
        arbitrated_signals = self.arbitrate_signals(signals)

        # 3. Apply risk management and capital allocation
        approved_signals = []
        for signal in arbitrated_signals:
            # Check risk limits
            risk_ok, risk_reason = self.risk_manager.check_risk_limits(signal)
            if risk_ok:
                # Allocate capital
                signal.position_size = self.allocate_capital(signal)
                signal.status = "approved"
                approved_signals.append(signal)

                # Add to risk manager's open positions
                self.risk_manager.add_position(signal.symbol, {
                    "signal": signal.to_dict(),
                    "entry_time": datetime.now()
                })
            else:
                signal.status = "rejected"
                self.logger.warning(f"Signal rejected: {risk_reason}")

        # 4. Log results
        self.logger.info(f"Cycle complete: {len(approved_signals)} signals approved, "
                        f"{len(signals) - len(approved_signals)} rejected")

        return approved_signals

    def get_status(self):
        """Get current system status"""
        starting_bankroll = self.config.get("bankroll", 10000)
        capital_in_use = 0.0
        for pos in self.risk_manager.open_positions.values():
            try:
                sig = pos.get("signal", {}) or {}
                size = float(sig.get("position_size", 0.0))
                if size > 0:
                    capital_in_use += size
            except Exception:
                continue
        available_bankroll = max(0.0, float(starting_bankroll) - capital_in_use)

        return {
            "is_running": self.is_running,
            "bankroll": available_bankroll,
            "daily_pnl": self.risk_manager.daily_pnl,
            "open_positions": len(self.risk_manager.open_positions),
            "total_signals": len(self.signals),
            "active_engines": list(self.active_engines.keys()),
            "performance_records": len(self.performance_history),
            "uptime": str(datetime.now() - self.risk_manager.start_time)
        }

    def save_state(self, state_path):
        """Save current state to file"""
        def _json_safe(obj):
            """Convert nested structures to JSON-serializable types"""
            # Primitive types
            if isinstance(obj, (str, int, float, bool)) or obj is None:
                return obj

            # Handle common numeric-like objects (e.g. numpy/pandas scalars)
            try:
                import numpy as np  # type: ignore
                if isinstance(obj, (np.integer, np.floating)):
                    return obj.item()
            except Exception:
                pass

            # Dicts/lists/tuples
            if isinstance(obj, dict):
                return { _json_safe(k): _json_safe(v) for k, v in obj.items() }
            if isinstance(obj, list):
                return [ _json_safe(v) for v in obj ]
            if isinstance(obj, tuple):
                return [ _json_safe(v) for v in obj ]

            # Datetime with isoformat
            if hasattr(obj, 'isoformat'):
                try:
                    return obj.isoformat()
                except Exception:
                    return str(obj)

            # Fallback
            return str(obj)

        state = {
            "config": self.config.data,
            "performance_history": list(self.performance_history),
            "signals": {k: [s.to_dict() for s in v] for k, v in self.signals.items()},
            "risk_state": {
                "daily_pnl": self.risk_manager.daily_pnl,
                # Do not assume entry_time is a datetime; it may already be an ISO string
                "open_positions": {
                    k: {
                        "signal": (v or {}).get("signal"),
                        "entry_time": (v or {}).get("entry_time"),
                    }
                    for k, v in self.risk_manager.open_positions.items()
                },
                "start_time": self.risk_manager.start_time
            },
            "timestamp": datetime.now().isoformat()
        }

        safe_state = _json_safe(state)
        with open(state_path, 'w') as f:
            json.dump(safe_state, f, indent=2)

        self.logger.info(f"State saved to {state_path}")

    def load_state(self, state_path):
        """Load state from file"""
        if os.path.exists(state_path):
            with open(state_path, 'r') as f:
                state = json.load(f)

            # Restore configuration
            self.config.data.update(state.get("config", {}))

            # Restore performance history
            self.performance_history.extend(state.get("performance_history", []))

            # Restore signals
            for symbol, signal_list in state.get("signals", {}).items():
                signals_for_symbol = []
                for signal_data in signal_list:
                    # Handle timestamp conversion safely
                    timestamp_str = signal_data.get("timestamp")
                    if timestamp_str:
                        try:
                            timestamp = datetime.fromisoformat(timestamp_str)
                        except ValueError:
                            timestamp = datetime.now()
                    else:
                        timestamp = datetime.now()

                    # Create Signal with all the saved fields
                    signal = Signal(
                        symbol=signal_data.get("symbol", ""),
                        action=signal_data.get("action", ""),
                        confidence=signal_data.get("confidence", 0.0),
                        position_size=signal_data.get("position_size", 0.0),
                        rationale=signal_data.get("rationale", ""),
                        source=signal_data.get("source", ""),
                        timestamp=timestamp,
                        **{k: v for k, v in signal_data.items()
                           if k not in ["symbol", "action", "confidence", "position_size", "rationale", "source", "timestamp"]}
                    )
                    signals_for_symbol.append(signal)
                self.signals[symbol] = signals_for_symbol

            # Restore risk state
            risk_state = state.get("risk_state", {})
            self.risk_manager.daily_pnl = risk_state.get("daily_pnl", 0.0)
            self.risk_manager.open_positions = risk_state.get("open_positions", {})

            # Handle start_time conversion
            start_time_str = risk_state.get("start_time")
            if start_time_str:
                try:
                    self.risk_manager.start_time = datetime.fromisoformat(start_time_str)
                except ValueError:
                    self.risk_manager.start_time = datetime.now()
            else:
                self.risk_manager.start_time = datetime.now()

            self.logger.info(f"State loaded from {state_path}")

# Main test function
async def main():
    """Test Meta-Brain system"""
    print("🚀 Starting Phasma Meta-Brain Test")

    # Initialize system
    meta_brain = PhasmaMetaBrain("config.json")

    # Test signal arbitration
    test_signals = [
        Signal("AMD", "BUY_CALL", 0.8, 100, "OpenAI deal catalyst", "news_api"),
        Signal("AMD", "BUY_PUT", 0.6, 80, "Market volatility", "options_engine"),
        Signal("COCH", "BUY_CALL", 0.75, 50, "Overnight surge potential", "news_scanner")
    ]

    # Add test signals
    for signal in test_signals:
        meta_brain.signals[signal.symbol].append(signal)

    # Run arbitration
    arbitrated = meta_brain.arbitrate_signals(test_signals)

    print(f"\n📊 Arbitration Results:")
    print(f"Input signals: {len(test_signals)}")
    print(f"Approved signals: {len(arbitrated)}")

    for signal in arbitrated:
        print(f"- {signal.symbol} {signal.action}: {signal.confidence:.1%} "
              f"(${signal.position_size:.0f}) - {signal.source}")

    # Show system status
    status = meta_brain.get_status()
    print(f"\n📈 System Status: {status}")

    print("\n✅ Phasma Meta-Brain test complete!")

if __name__ == "__main__":
    asyncio.run(main())
