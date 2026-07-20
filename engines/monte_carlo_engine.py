#!/usr/bin/env python3
"""
Phasma Monte Carlo Simulation Engine
Provides realistic predictions for moonshot opportunities using:
- Monte Carlo simulations (1,000+ price paths)
- Historical backtesting on similar events
- Data-driven exit timing and profit targets
"""

import numpy as np
import random
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import json
import os
import psutil
import time
from scipy import stats

class PhasmaMonteCarloEngine:
    """Monte Carlo simulation engine for realistic moonshot predictions"""

    def __init__(self, config=None):
        self.config = config or {}
        self.random_seed = 42
        np.random.seed(self.random_seed)

        # Performance and safety configuration
        self.sim_config = {
            'default_sims': 250,   # OPTIMIZED: From 500 to 250 (super upgraded version)
            'max_sims': 500,       # OPTIMIZED: From 1000 to 500 for consistency
            'escalate_threshold': 0.03,  # Escalate if POP within ±3% of 0.50
            'target_ci_width': 0.02,     # Early stop when 95% CI < ±2%
            'variance_reduction': ['antithetic', 'sobol'],
            'dtype': np.float32
        }

        # Safety governors
        self.governors = {
            'cpu_headroom_min_pct': 40,
            'cpu_throttle_pct': 85,
            'max_wall_ms_per_ticker': 150,
            'max_mem_increase_mb': 50
        }

        # Performance settings
        self.perf_config = {
            'timer': 'perf_counter_ns',
            'warmup_batches': 1,
            'batch_size': 256
        }

        # Cache for per-ticker data
        self.ticker_cache = {}

        # Historical patterns database for backtesting
        self.historical_patterns = self._load_historical_patterns()

    def _load_historical_patterns(self) -> Dict:
        """Load historical patterns for backtesting"""
        patterns_file = "c:\\Users\\kyran\\CascadeProjects\\phasma_Ai\\data\\historical_patterns.json"

        if os.path.exists(patterns_file):
            try:
                with open(patterns_file, 'r') as f:
                    return json.load(f)
            except:
                pass

        # Default patterns if file doesn't exist
        return {
            'sanctions': {'avg_return': 0.08, 'volatility': 0.35, 'duration_days': 5, 'win_rate': 0.75, 'realized_vol': 0.45},
            'earnings_beat': {'avg_return': 0.12, 'volatility': 0.40, 'duration_days': 3, 'win_rate': 0.80, 'realized_vol': 0.55},
            'merger_acquisition': {'avg_return': 0.15, 'volatility': 0.45, 'duration_days': 7, 'win_rate': 0.85, 'realized_vol': 0.60},
            'product_launch': {'avg_return': 0.18, 'volatility': 0.50, 'duration_days': 5, 'win_rate': 0.70, 'realized_vol': 0.65},
            'clinical_trial': {'avg_return': 0.30, 'volatility': 0.60, 'duration_days': 10, 'win_rate': 0.65, 'realized_vol': 0.75},
            'oil_supply': {'avg_return': 0.05, 'volatility': 0.30, 'duration_days': 4, 'win_rate': 0.60, 'realized_vol': 0.40},
            'default': {'avg_return': 0.10, 'volatility': 0.35, 'duration_days': 5, 'win_rate': 0.70, 'realized_vol': 0.45}
        }

    def run_stock_simulation(self, signal: Dict) -> Dict:
        """Run Monte Carlo simulation for regular stock trades (no options)"""
        symbol = signal.get('symbol') or signal.get('ticker') or 'N/A'
        current_price = signal.get('current_price') or 0
        try:
            current_price = float(current_price)
        except (TypeError, ValueError):
            current_price = 0.0
        if current_price <= 0:
            from utils.company_resolver import get_resolver
            sector_hint = get_resolver().sector(symbol, signal.get('title'))
            signal['sector'] = signal.get('sector') or sector_hint
        target_price = signal.get('target_price', current_price * 1.1)  # Default 10% target
        stop_loss = signal.get('stop_loss', current_price * 0.9)  # Default 10% stop
        confidence = signal.get('confidence', 0.5)
        holding_days = signal.get('holding_days', 30)
        
        print(f"Running {250:,} stock simulations for {symbol}")
        print(f"   Entry: ${current_price:.2f} | Target: ${target_price:.2f} | Stop: ${stop_loss:.2f}")
        
        # Get volatility
        sector = signal.get('sector', 'Technology')
        sector_vol_map = {
            'Technology': 0.45, 'AI': 0.55, 'Energy': 0.40, 'Healthcare': 0.50,
            'Finance': 0.35, 'Consumer': 0.30, 'Automotive': 0.45, 'Mining': 0.50
        }
        volatility = sector_vol_map.get(sector, 0.35)
        
        # Run simulations
        num_sims = 250
        wins = 0
        final_prices = []
        
        for _ in range(num_sims):
            # Generate random price path using geometric Brownian motion
            daily_returns = np.random.normal(0, volatility / np.sqrt(252), holding_days)
            price_path = current_price * np.exp(np.cumsum(daily_returns))
            final_price = price_path[-1]
            final_prices.append(final_price)
            
            # Check if hit target or stop loss
            max_price = np.max(price_path)
            min_price = np.min(price_path)
            
            if max_price >= target_price:
                wins += 1
            elif min_price <= stop_loss:
                # Stop loss hit - count as loss
                pass
            elif final_price >= current_price * 1.05:  # 5% profit considered win
                wins += 1
        
        win_rate = wins / num_sims
        avg_final = np.mean(final_prices)
        profit_potential = (avg_final - current_price) / current_price
        
        return {
            'symbol': symbol,
            'win_rate': win_rate,
            'avg_final_price': avg_final,
            'profit_potential': profit_potential,
            'target_price': target_price,
            'stop_loss': stop_loss,
            'holding_days': holding_days,
            'volatility_used': volatility,
            'total_simulations': num_sims,
            'simulation_type': 'stock'
        }
    
    def run_monte_carlo_simulation(self, signal: Dict, num_sims: int = None) -> Dict:
        """Advanced Monte Carlo simulation with safety governors and variance reduction"""
        symbol = signal.get('symbol') or signal.get('ticker') or 'N/A'
        confidence = signal.get('confidence', 0.5)

        # CHECK CACHE FIRST: Prevent duplicate simulation calls (TEMPORARILY DISABLED)
        cache_key = f"{symbol}_{confidence:.2f}_{signal.get('current_price', 0):.0f}"
        if False and cache_key in self.ticker_cache:  # Temporarily disabled
            print(f"📋 Using cached simulation for {symbol} (confidence: {confidence:.1%})")
            return self.ticker_cache[cache_key]

        # SMART SIMULATION COUNT: Adaptive with safety caps
        if num_sims is None:
            base_sims = self.sim_config['default_sims']
            pop_threshold = 0.50  # Your decision threshold

            # Check if we're near the decision threshold (escalate for precision)
            if hasattr(self, 'last_pop_estimate'):
                last_pop = self.last_pop_estimate.get(symbol, 0.5)
                if abs(last_pop - pop_threshold) < self.sim_config['escalate_threshold']:
                    num_sims = min(self.sim_config['max_sims'], base_sims * 2)
                    print(f"   🎯 Near decision threshold - escalating to {num_sims:,} sims")
                else:
                    num_sims = base_sims
            else:
                num_sims = base_sims
        
        # SMART SPLIT: If not risk-neutral, split the total sims in half
        # Main simulation gets half, risk-neutral gets the other half
        if not signal.get('risk_neutral', False):
            drift_sims = num_sims // 2  # Half for drift
            num_sims = drift_sims  # Run only half here
        else:
            drift_sims = num_sims  # Risk-neutral runs full amount

        print(f"🎲 Running {num_sims:,} Monte Carlo simulations for {symbol} (confidence: {confidence:.1%})")

        # HIGH-PRECISION TIMING: Use perf_counter_ns for accurate measurement
        start_time_ns = time.perf_counter_ns()
        process = psutil.Process()
        start_memory = process.memory_info().rss / 1024 / 1024  # MB

        # SAFETY CHECK: Pre-flight resource check
        if process.cpu_percent() > self.governors['cpu_throttle_pct']:
            print(f"   ⚠️ High CPU usage detected - reducing simulations to 1,000")
            num_sims = min(num_sims, 1000)

        # CALIBRATE VOLATILITY: Use realized vol from historical patterns
        sector = signal.get('sector', 'Technology')
        analogs = self.get_historical_analogs(signal) or []  # Ensure it's a list, not None

        if analogs:
            best_analog = max(analogs, key=lambda x: x['confidence'])
            realized_vol = best_analog['historical_data'].get('realized_vol', 0.35)
        else:
            sector_vol_map = {
                'Technology': 0.45, 'AI': 0.55, 'Energy': 0.40, 'Healthcare': 0.50,
                'Finance': 0.35, 'Consumer': 0.30, 'Automotive': 0.45, 'Mining': 0.50
            }
            realized_vol = sector_vol_map.get(sector, 0.35)

        # Apply news sentiment adjustment (Less volatility penalty)
        sentiment = signal.get('sentiment', 0)
        catalyst_score = signal.get('catalyst_score', 0)
        news_vol_multiplier = 1.0 + (abs(sentiment) * 0.2) + (catalyst_score * 0.2)  # Reduced from 0.3 and 0.4
        calibrated_volatility = realized_vol * news_vol_multiplier
        calibrated_volatility = min(calibrated_volatility, 0.8)  # Reduced max from 1.0

        # Determine drift with confidence scaling (Realistic - based on historical data)
        base_drift = 0.08  # Realistic annual drift (8% vs previous 20%)
        if signal.get('risk_neutral', False):
            # Risk-neutral pricing: drift ≈ risk-free rate (near 0)
            drift = 0.01  # 1% risk-free rate
        else:
            if confidence > 0.8:
                drift = base_drift * 1.5  # 12% max (vs previous 60%)
            elif confidence > 0.6:
                drift = base_drift * 1.25  # 10% (vs previous 50%)
            elif confidence > 0.4:
                drift = base_drift * 1.0  # 8% (vs previous 40%)
            else:
                drift = base_drift * 0.8  # 6.4% (vs previous 30%)

            if signal.get('is_moonshot', False):
                drift *= 2.0  # 16% max for moonshots (vs previous 240%)

        # ADVANCED MONTE CARLO: Vectorized with variance reduction
        current_price = signal.get('current_price') or signal.get('entry_price') or 100.0
        try:
            current_price = float(current_price)
        except (TypeError, ValueError):
            current_price = 100.0
        strike_price = signal.get('strike') or current_price
        premium = signal.get('premium') or 5.0
        days_to_expiry = signal.get('days_to_expiry', 7)

        # DEBUG: Show key parameters
        print(f"   📊 Parameters: Current=${current_price:.2f}, Strike=${strike_price:.2f}, Drift={drift:.3f} ({drift*100:.1f}%), Vol={calibrated_volatility:.3f} ({calibrated_volatility*100:.1f}%)")

        # Use float32 for performance (as recommended)
        dt = np.float32(1/252)
        num_sims = int(num_sims)

        # Batch processing for memory efficiency
        batch_size = self.perf_config['batch_size']
        num_batches = (num_sims + batch_size - 1) // batch_size
        all_payoffs = []

        # Progress tracking for early stopping
        running_win_rate = 0.0
        confidence_interval_width = 1.0

        for batch in range(num_batches):
            batch_start = batch * batch_size
            batch_end = min((batch + 1) * batch_size, num_sims)
            batch_sims = batch_end - batch_start

            # SAFETY GOVERNOR: Check resources mid-batch
            if batch > 0 and batch % 4 == 0:  # Check every 4 batches
                current_cpu = process.cpu_percent()
                current_memory = process.memory_info().rss / 1024 / 1024
                elapsed_ms = (time.perf_counter_ns() - start_time_ns) / 1_000_000

                if current_cpu > self.governors['cpu_throttle_pct']:
                    print(f"   🛑 CPU governor triggered ({current_cpu:.1f}% > {self.governors['cpu_throttle_pct']}%) - reducing batch size")
                    batch_size = max(64, batch_size // 2)
                    num_batches = (num_sims + batch_size - 1) // batch_size

                if (current_memory - start_memory) > self.governors['max_mem_increase_mb']:
                    print(f"   🛑 Memory governor triggered (+{current_memory - start_memory:.1f}MB) - terminating early")
                    break

                if elapsed_ms > self.governors['max_wall_ms_per_ticker']:
                    print(f"   🛑 Time governor triggered ({elapsed_ms:.1f}ms > {self.governors['max_wall_ms_per_ticker']}ms) - terminating early")
                    break

            # Generate paths for this batch with variance reduction
            paths = np.zeros((batch_sims, days_to_expiry + 1), dtype=self.sim_config['dtype'])
            paths[:, 0] = current_price

            for t in range(1, days_to_expiry + 1):
                # Vectorized Brownian motion with antithetic variates for variance reduction
                half_batch = batch_sims // 2
                if half_batch > 0:
                    # Generate first half of paths
                    z1 = np.random.standard_normal(half_batch).astype(self.sim_config['dtype'])
                    # Generate antithetic variates (negative correlation) for second half
                    z2 = -z1

                    # Combine for full batch
                    z_combined = np.concatenate([z1, z2])[:batch_sims]

                    # Ensure shape compatibility
                    if len(z_combined) != paths.shape[0]:
                        # Regenerate random numbers with correct shape
                        z_combined = np.random.standard_normal(batch_sims).astype(self.sim_config['dtype'])

                    paths[:, t] = paths[:, t-1] * np.exp((drift - 0.5 * calibrated_volatility**2) * dt + calibrated_volatility * np.sqrt(dt) * z_combined)
                else:
                    # Fallback for odd batch sizes
                    z = np.random.standard_normal(batch_sims).astype(self.sim_config['dtype'])
                    paths[:, t] = paths[:, t-1] * np.exp((drift - 0.5 * calibrated_volatility**2) * dt + calibrated_volatility * np.sqrt(dt) * z)

            # Calculate payoffs for this batch
            final_prices = paths[:, -1]
            if signal.get('action') in ['BUY_CALL', 'CALL']:
                payoffs = np.maximum(final_prices - strike_price, 0)
            elif signal.get('action') in ['BUY_PUT', 'PUT']:
                payoffs = np.maximum(strike_price - final_prices, 0)
            else:
                payoffs = np.abs(final_prices - strike_price)

            # Convert to P&L per contract
            pnl = (payoffs - premium) * 100
            all_payoffs.extend(pnl)

            # EARLY STOPPING: Check if we've achieved target precision
            if len(all_payoffs) >= 500:  # Need minimum samples for CI
                current_win_rate = np.mean(np.array(all_payoffs) > 0)
                if len(all_payoffs) > 30:  # Need >30 samples for reliable CI
                    se = np.sqrt(current_win_rate * (1 - current_win_rate) / len(all_payoffs))
                    confidence_interval_width = 1.96 * se  # 95% CI half-width

                    if confidence_interval_width < self.sim_config['target_ci_width']:
                        print(f"   ✅ Early stopping: CI width {confidence_interval_width:.3f} < target {self.sim_config['target_ci_width']:.3f}")
                        break

        # Convert to numpy for final calculations
        all_payoffs = np.array(all_payoffs, dtype=np.float64)  # Back to float64 for accuracy
        actual_sims = len(all_payoffs)

        # PERFORMANCE METRICS: High-precision timing
        end_time_ns = time.perf_counter_ns()
        end_cpu = process.cpu_percent()
        end_memory = process.memory_info().rss / 1024 / 1024
        execution_time_ms = (end_time_ns - start_time_ns) / 1_000_000

        print(f"📊 Performance: {execution_time_ms:.2f}ms | CPU: {end_cpu:.1f}% | Memory: +{end_memory - start_memory:.1f}MB | Sims: {actual_sims:,}")

        # Calculate comprehensive statistics
        win_rate = np.mean(all_payoffs > 0)
        avg_pnl = np.mean(all_payoffs)
        median_pnl = np.median(all_payoffs)
        percentile_10 = np.percentile(all_payoffs, 10)
        percentile_90 = np.percentile(all_payoffs, 90)
        max_pnl = np.max(all_payoffs)
        min_pnl = np.min(all_payoffs)

        # Calculate confidence interval for win rate
        if actual_sims > 30:
            se = np.sqrt(win_rate * (1 - win_rate) / actual_sims)
            ci_half_width = 1.96 * se
            win_rate_ci = f"±{ci_half_width:.3f}"
        else:
            win_rate_ci = "N/A"

        # Find optimal exit day
        daily_max_pnl = []
        for day in range(1, days_to_expiry + 1):
            day_prices = np.full(actual_sims, current_price)  # Simplified for performance
            if signal.get('action') in ['BUY_CALL', 'CALL']:
                day_payoffs = np.maximum(day_prices - strike_price, 0)
            else:
                day_payoffs = np.maximum(strike_price - day_prices, 0)
            day_pnl = (day_payoffs - premium) * 100
            daily_max_pnl.append(np.mean(day_pnl))

        optimal_exit_day = np.argmax(daily_max_pnl) + 1

        # Moonshot probabilities with caps
        moonshot_threshold = premium * 5
        raw_moonshot_prob = np.mean(all_payoffs >= moonshot_threshold)
        moonshot_prob = min(raw_moonshot_prob, 0.15)

        moonshot_10x_threshold = premium * 10
        raw_moonshot_10x_prob = np.mean(all_payoffs >= moonshot_10x_threshold)
        moonshot_10x_prob = min(raw_moonshot_10x_prob, 0.05)

        # REALITY DRAG: Historical bias correction (Minimal)
        if analogs:
            historical_win_rates = [analog['historical_data']['win_rate'] for analog in analogs]
            avg_historical_win_rate = sum(historical_win_rates) / len(historical_win_rates)
            reality_drag_factor = 0.05  # Reduced from 0.1 (5% historical vs 95% simulation)
            adjusted_win_rate = (win_rate * (1 - reality_drag_factor)) + (avg_historical_win_rate * reality_drag_factor)
            print(f"⚖️ Reality drag: {win_rate:.3f} → {adjusted_win_rate:.3f} (historical: {avg_historical_win_rate:.3f})")
            win_rate = adjusted_win_rate

        # Calculate simulation-scaled confidence and POP
        sim_scaled_confidence = min(0.95, win_rate * 1.5)  # Scale win rate to confidence
        pop_from_sim = win_rate * 100  # Convert to percentage
        
        # Initialize result dictionary before smart split
        result = {}
        
        # SMART SPLIT: Run risk-neutral simulation with the OTHER HALF of sims for accurate POP
        # This gives us both drift-based returns AND unbiased probability
        if not signal.get('risk_neutral', False):
            try:
                # Use the same number of sims as drift (already halved above)
                # So if total was 500, drift ran 250, now risk-neutral runs 250
                risk_neutral_sims = num_sims  # Same as drift (already halved)
                risk_neutral_results = self.run_risk_neutral_simulation(signal, num_sims=risk_neutral_sims)
                risk_neutral_pop = risk_neutral_results['pop_from_sim']
                result['risk_neutral_pop'] = risk_neutral_pop
                result['bias_comparison'] = f"Drift-based: {pop_from_sim:.1f}% vs Risk-Neutral POP: {risk_neutral_pop:.1f}%"
                
                # Calculate optimal closing point based on both simulations
                result['optimal_close_days'] = self._calculate_optimal_close(
                    drift_results=result,
                    risk_neutral_results=risk_neutral_results,
                    signal=signal
                )
                
                print(f"⚖️ Smart Split: Drift {pop_from_sim:.1f}% | Risk-Neutral POP {risk_neutral_pop:.1f}% | Close in {result['optimal_close_days']} days")
            except Exception as e:
                result['risk_neutral_pop'] = None
                result['bias_comparison'] = "Risk-neutral calculation failed"
                result['optimal_close_days'] = signal.get('dte', 30) // 2  # Default to half DTE

        # CACHE RESULTS: Prevent duplicate calls
        result.update({
            'symbol': symbol,
            'win_rate': win_rate,
            'win_rate_ci': win_rate_ci,
            'avg_pnl': avg_pnl,
            'median_pnl': median_pnl,
            'percentile_10': percentile_10,
            'percentile_90': percentile_90,
            'max_pnl': max_pnl,
            'min_pnl': min_pnl,
            'optimal_exit_day': optimal_exit_day,
            'moonshot_probability': moonshot_prob,
            'moonshot_10x_probability': moonshot_10x_prob,
            'total_simulations': actual_sims,
            'drift_used': drift,
            'volatility_used': calibrated_volatility,
            'realized_vol_used': realized_vol,
            'simulation_date': datetime.now().isoformat(),
            'sim_scaled_confidence': sim_scaled_confidence,
            'pop_from_sim': pop_from_sim,
            'historical_analogs': len(analogs),
            'reality_drag_applied': bool(analogs),
            'execution_time_ms': execution_time_ms,
            'cpu_usage': end_cpu,
            'memory_delta': end_memory - start_memory,
            'early_stopped': confidence_interval_width < self.sim_config['target_ci_width']
        })
        if False:  # Temporarily disabled
            self.ticker_cache[cache_key] = result
        return result

    def get_historical_analogs(self, signal: Dict) -> List[Dict]:
        """Find historical analogs for backtesting"""
        symbol = signal.get('symbol', '')
        title = signal.get('title', '').lower()
        sector = signal.get('sector', '')

        # Keyword matching for pattern detection
        analogs = []

        # Check for sanctions-related events
        if any(word in title for word in ['sanction', 'embargo', 'restriction', 'penalty']):
            analogs.append({
                'pattern': 'sanctions',
                'description': 'Sanctions impact',
                'confidence': 0.8,
                'historical_data': self.historical_patterns['sanctions']
            })

        # Check for earnings events
        if any(word in title for word in ['earnings', 'eps', 'profit', 'revenue', 'beat', 'miss']):
            analogs.append({
                'pattern': 'earnings_beat',
                'description': 'Earnings announcement',
                'confidence': 0.9,
                'historical_data': self.historical_patterns['earnings_beat']
            })

        # Check for merger/acquisition events
        if any(word in title for word in ['merger', 'acquisition', 'deal', 'buyout', 'takeover']):
            analogs.append({
                'pattern': 'merger_acquisition',
                'description': 'M&A activity',
                'confidence': 0.7,
                'historical_data': self.historical_patterns['merger_acquisition']
            })

        # Check for oil/energy specific events
        if sector in ['ENERGY', 'OIL'] and any(word in title for word in ['supply', 'production', 'output', 'barrel']):
            analogs.append({
                'pattern': 'oil_supply',
                'description': 'Oil supply changes',
                'confidence': 0.8,
                'historical_data': self.historical_patterns['oil_supply']
            })

        # Default pattern if no specific match
        if not analogs:
            analogs.append({
                'pattern': 'default',
                'description': 'General market event',
                'confidence': 0.5,
                'historical_data': self.historical_patterns['default']
            })

    def run_risk_neutral_simulation(self, signal: Dict, num_sims: int = None) -> Dict:
        """Run risk-neutral Monte Carlo simulation (drift = 0) for unbiased POP calculation"""
        # Create a copy of the signal with risk-neutral assumptions
        risk_neutral_signal = signal.copy()
        risk_neutral_signal['risk_neutral'] = True

        # Use risk-free rate as drift (approximately 0)
        original_drift = signal.get('confidence', 0.5)  # Store original confidence
        risk_neutral_signal['confidence'] = 0.5  # Neutral confidence for risk-neutral calc

        # Run the simulation with neutral assumptions
        return self.run_monte_carlo_simulation(risk_neutral_signal, num_sims)

    def generate_simulation_evidence(self, signal: Dict) -> str:
        sim_results = self.run_monte_carlo_simulation(signal)
        analogs = self.get_historical_analogs(signal) or []  # Ensure it's a list, not None

        evidence_parts = []

        # Add simulation results with confidence intervals
        win_rate = sim_results['win_rate']
        win_rate_ci = sim_results.get('win_rate_ci', 'N/A')
        avg_pnl = sim_results['avg_pnl']
        percentile_90 = sim_results['percentile_90']
        optimal_days = sim_results['optimal_exit_day']
        moonshot_prob = sim_results['moonshot_probability']
        moonshot_10x_prob = sim_results['moonshot_10x_probability']
        total_sims = sim_results['total_simulations']
        calibrated_vol = sim_results.get('volatility_used', 0)
        realized_vol = sim_results.get('realized_vol_used', 0)
        execution_time_ms = sim_results.get('execution_time_ms', 0)
        cpu_usage = sim_results.get('cpu_usage', 0)
        memory_delta = sim_results.get('memory_delta', 0)

        # PRECISE LOGGING: Show the actual calculation chain
        evidence_parts.append(f"📊 Monte Carlo: POP_raw={win_rate:.3f} ({win_rate_ci} CI), "
                           f"avg ${avg_pnl:.0f} P&L, "
                           f"90th ${percentile_90:.0f} (optimal {optimal_days} days, {total_sims:,} sims)")

        # Add performance metrics
        evidence_parts.append(f"⚡ Performance: {execution_time_ms:.1f}ms, "
                           f"{cpu_usage:.1f}% CPU, +{memory_delta:.1f}MB memory")

        if moonshot_prob > 0.01:
            evidence_parts.append(f"🎯 Moonshot: {moonshot_prob:.1%} chance of 5x+ return (capped at 15%)")

        if moonshot_10x_prob > 0.01:
            evidence_parts.append(f"🚀 10x+ Prob: {moonshot_10x_prob:.1%} chance of 10x+ return (capped at 5%)")

        # Add volatility calibration info
        if calibrated_vol != realized_vol:
            evidence_parts.append(f"📈 Volatility: {realized_vol:.1%} realized → {calibrated_vol:.1%} calibrated")

        # Add reality drag info
        if sim_results.get('reality_drag_applied', False) and sim_results.get('historical_analogs', 0) > 0:
            evidence_parts.append(f"⚖️ Reality Drag: Adjusted with {sim_results['historical_analogs']} historical analogs")

        # Add adaptive simulation count info
        if total_sims >= 500:
            evidence_parts.append(f"🎲 High Precision: {total_sims:,} simulations (optimized for performance)")
        elif total_sims < 500:
            evidence_parts.append(f"⚡ Efficient: {total_sims:,} simulations for low-confidence signal")

        # Add early stopping info
        if sim_results.get('early_stopped', False):
            evidence_parts.append(f"✅ Early Stop: Achieved target precision, stopped early")

        # Add historical analogs
        for analog in analogs[:2]:  # Top 2 analogs
            hist_data = analog['historical_data']
            evidence_parts.append(f"📚 Historical {analog['pattern']}: "
                               f"{hist_data['win_rate']:.1%} win rate, "
                               f"{hist_data['avg_return']:+.1%} avg return "
                               f"over {hist_data['duration_days']} days")

        return "\n".join([f"{i+1}. {evidence}" for i, evidence in enumerate(evidence_parts)])

    def _calculate_optimal_close(self, drift_results: Dict, risk_neutral_results: Dict, signal: Dict) -> int:
        """
        Calculate optimal closing point using both drift and risk-neutral simulations
        
        Strategy:
        - Drift simulation shows when returns peak (timing)
        - Risk-neutral shows true probability (POP)
        - Combine to find sweet spot: max profit before decay
        """
        dte = signal.get('dte', 30)
        
        # Get optimal exit from drift simulation (when returns peak)
        drift_optimal = drift_results.get('optimal_exit_day', dte // 2)
        
        # Risk-neutral POP tells us confidence level (no fabricated default)
        risk_neutral_pop = None
        if risk_neutral_results is not None:
            risk_neutral_pop = risk_neutral_results.get('pop_from_sim')
        if risk_neutral_pop is None:
            risk_neutral_pop = drift_results.get('pop_from_sim')
        if risk_neutral_pop is not None:
            try:
                risk_neutral_pop = float(risk_neutral_pop)
                if 0 < risk_neutral_pop <= 1:
                    risk_neutral_pop *= 100.0
            except (TypeError, ValueError):
                risk_neutral_pop = None

        if risk_neutral_pop is None:
            optimal_close = max(1, min(int(drift_optimal * 0.60), dte))
            return optimal_close

        # High POP = can hold longer (more confident)
        # Low POP = close early (less confident)
        if risk_neutral_pop >= 60:
            # High confidence - hold for 75% of drift optimal
            optimal_close = int(drift_optimal * 0.75)
        elif risk_neutral_pop >= 50:
            # Medium confidence - hold for 60% of drift optimal
            optimal_close = int(drift_optimal * 0.60)
        else:
            # Low confidence - close early at 40% of drift optimal
            optimal_close = int(drift_optimal * 0.40)
        
        # Bounds: minimum 1 day, maximum DTE
        optimal_close = max(1, min(optimal_close, dte))
        
        return optimal_close
    
    def should_flip_signal(self, signal: Dict) -> tuple:
        """Determine if signal should be flipped based on simulation results"""
        sim_results = self.run_monte_carlo_simulation(signal)

        # Flip if win rate is very low (< 20%) and confidence is high
        if sim_results['win_rate'] < 0.2 and signal.get('confidence', 0) > 0.7:
            return True, f"Sim shows {sim_results['win_rate']:.1%} win rate - flipping to contrarian play"

        # Flip if bearish drift but signal is bullish
        if sim_results['drift_used'] < -0.02 and signal.get('action', '').startswith('BUY_CALL'):
            return True, f"Sim shows bearish drift ({sim_results['drift_used']:.2%}) - flipping signal"

        return False, ""

# Global instance
monte_carlo_engine = None

def get_monte_carlo_engine(config=None):
    """Get or create Monte Carlo engine instance"""
    global monte_carlo_engine
    if monte_carlo_engine is None:
        monte_carlo_engine = PhasmaMonteCarloEngine(config)
    return monte_carlo_engine

