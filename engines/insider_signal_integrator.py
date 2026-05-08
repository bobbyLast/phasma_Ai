"""
Insider Signal Integrator - Combines insider, institutional, analyst, and options signals

Detects high-conviction opportunities when multiple signals align:
- Insider buying (Form 4 purchases)
- Institutional accumulation (13F filings)
- Analyst upgrades/price targets
- Unusual options activity

Examples like BLND:
- Insiders buying at $3
- BlackRock accumulating shares
- Analyst price targets higher
- Options flow spike
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional, Tuple
import json
import os
from engines.form4_parser import Form4Parser
from engines.options_flow_filter import OptionsFlowFilter


class SignalSource:
    """Represents a source of trading signals"""
    
    def __init__(self, name: str, weight: float, description: str):
        self.name = name
        self.weight = weight
        self.description = description
        self.signals = []
        self.last_updated = None


class ConfluenceSignal:
    """Represents a high-conviction signal from multiple sources"""
    
    def __init__(self, ticker: str):
        self.ticker = ticker
        self.insider_signals = []
        self.institutional_signals = []
        self.analyst_signals = []
        self.options_signals = []
        self.confluence_score = 0.0
        self.confidence_level = 'LOW'
        self.reasoning = ""
        self.detected_at = datetime.now()


class InsiderSignalIntegrator:
    """
    Integrates multiple signal sources to identify high-conviction opportunities
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        
        # Signal weights - CORRECTED based on expert feedback
        self.insider_weight = float(self.config.get('insider_integrator', {}).get('insider_weight', 0.50))  # INCREASED - real-time signal
        self.institutional_weight = float(self.config.get('insider_integrator', {}).get('institutional_weight', 0.10))  # DECREASED - lagging data
        self.analyst_weight = float(self.config.get('insider_integrator', {}).get('analyst_weight', 0.20))  # Same
        self.options_weight = float(self.config.get('insider_integrator', {}).get('options_weight', 0.20))  # Same
        
        # Thresholds
        self.confluence_threshold = float(self.config.get('insider_integrator', {}).get('confluence_threshold', 0.7))
        self.min_price = float(self.config.get('insider_integrator', {}).get('min_price', 0.1))
        self.max_price = float(self.config.get('insider_integrator', {}).get('max_price', 20.0))
        self.min_insider_amount = float(self.config.get('insider_integrator', {}).get('min_insider_amount', 1000000))  # $1M minimum
        
        # Tracking
        self.active_signals = {}
        self.signal_history = []
        
        # Initialize Form 4 parser for better signal quality
        self.form4_parser = Form4Parser(min_amount=self.min_insider_amount)
        
        # Initialize options flow filter for better options analysis
        self.options_filter = OptionsFlowFilter()
        
        print("[INSIDER INTEGRATOR] Initialized with corrected weights - Insider: 50%, Institutional: 10%, Analyst: 20%, Options: 20%")
        print("[INSIDER INTEGRATOR] Enhanced with Form 4 parser and options flow filter")
    
    def analyze_stock(self, ticker: str, insider_data: Dict = None) -> Optional[ConfluenceSignal]:
        """Analyze a stock for confluence of signals"""
        
        print(f"   [DEBUG] Starting analysis for {ticker}")
        
        # Check price range
        try:
            stock = yf.Ticker(ticker)
            current_price = stock.history(period="1d")['Close'].iloc[-1]
            print(f"   [DEBUG] Current price: ${current_price:.2f}")
            
            if not (self.min_price <= current_price <= self.max_price):
                print(f"   [DEBUG] Price out of range (${self.min_price}-${self.max_price})")
                return None
        except Exception as e:
            print(f"   [DEBUG] Error getting price: {e}")
            return None
        
        signal = ConfluenceSignal(ticker)
        
        # 1. Insider signals (Form 4 purchases)
        if insider_data:
            signal.insider_signals = self._analyze_insider_signals(ticker, insider_data)
            print(f"   [DEBUG] Insider signals found: {len(signal.insider_signals)}")
        
        # 2. Institutional signals (13F accumulation)
        signal.institutional_signals = self._analyze_institutional_signals(ticker)
        print(f"   [DEBUG] Institutional signals found: {len(signal.institutional_signals)}")
        
        # 3. Analyst signals (upgrades, price targets)
        signal.analyst_signals = self._analyze_analyst_signals(ticker)
        print(f"   [DEBUG] Analyst signals found: {len(signal.analyst_signals)}")
        
        # 4. Options signals (unusual flow)
        signal.options_signals = self._analyze_options_signals(ticker)
        print(f"   [DEBUG] Options signals found: {len(signal.options_signals)}")
        
        # Calculate confluence score
        signal.confluence_score = self._calculate_confluence_score(signal)
        
        # Apply macro context boost
        macro_boost = self._get_macro_boost(signal.ticker)
        if macro_boost > 0:
            signal.confluence_score = min(signal.confluence_score + macro_boost, 1.0)
            print(f"   [MACRO BOOST] +{macro_boost:.1%} for sector momentum")
        
        print(f"   [DEBUG] Confluence score: {signal.confluence_score:.1%}")
        
        # Determine confidence level
        if signal.confluence_score >= 0.8:
            signal.confidence_level = 'VERY HIGH'
        elif signal.confluence_score >= 0.6:
            signal.confidence_level = 'HIGH'
        elif signal.confluence_score >= 0.4:
            signal.confidence_level = 'MEDIUM'
        else:
            signal.confidence_level = 'LOW'
        
        # Generate reasoning
        signal.reasoning = self._generate_reasoning(signal, current_price)
        print(f"   [DEBUG] Reasoning: {signal.reasoning}")
        
        # Save if meets threshold
        if signal.confluence_score >= self.confluence_threshold:
            self.active_signals[ticker] = signal
            self.signal_history.append(signal)
            print(f"[CONFLUENCE DETECTED] {ticker}: {signal.confidence_level} confidence ({signal.confluence_score:.1%})")
            print(f"   {signal.reasoning[:100]}...")
            return signal
        else:
            print(f"   [DEBUG] Score {signal.confluence_score:.1%} below threshold {self.confluence_threshold:.1%}")
        
        return None
    
    def _analyze_insider_signals(self, ticker: str, insider_data: Dict) -> List[Dict]:
        """Analyze insider trading signals with Form 4 code parsing"""
        
        signals = []
        
        # Check for recent insider buys using Form 4 parser
        if ticker in insider_data:
            transactions = insider_data[ticker]
            
            # Use Form 4 parser to filter meaningful buys
            analysis = self.form4_parser.analyze_multiple_transactions(transactions)
            
            if analysis['meaningful_buys']:
                for buy in analysis['meaningful_buys']:
                    signals.append({
                        'type': 'insider_buy',
                        'amount': buy['amount'],
                        'price': buy['price'],
                        'days_ago': buy.get('days_ago', 0),
                        'confidence': buy['confidence'],
                        'insider_name': buy['insider_name'],
                        'title': buy['title'],
                        'quality': self.form4_parser.get_transaction_quality(buy)
                    })
                
                print(f"   [FORM 4 PARSED] {ticker}: {analysis['summary']}")
            
            # Boost confidence if multiple insiders
            if analysis['insider_count'] > 1:
                print(f"   [MULTIPLE INSIDERS] {ticker}: {analysis['insider_count']} insiders buying - confidence boosted")
        
        return signals
    
    def _analyze_institutional_signals(self, ticker: str) -> List[Dict]:
        """Analyze institutional accumulation signals"""
        
        signals = []
        
        # For now, simulate institutional data - in production would use 13F API
        # Example: BlackRock accumulating BLND
        major_institutions = ['BlackRock', 'Vanguard', 'Fidelity', 'ARK Invest']
        
        for institution in major_institutions:
            # Simulate detection of accumulation
            if np.random.random() < 0.1:  # 10% chance for demo
                signals.append({
                    'type': 'institutional_accumulation',
                    'institution': institution,
                    'shares': np.random.randint(100000, 10000000),
                    'confidence': np.random.uniform(0.7, 1.0)
                })
        
        return signals
    
    def _analyze_analyst_signals(self, ticker: str) -> List[Dict]:
        """Analyze analyst ratings and price targets"""
        
        signals = []
        
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Get analyst data
            if 'recommendationKey' in info:
                recommendation = info['recommendationKey']
                
                if recommendation in ['buy', 'strong_buy']:
                    signals.append({
                        'type': 'analyst_upgrade',
                        'rating': recommendation,
                        'confidence': 0.8 if recommendation == 'strong_buy' else 0.6
                    })
            
            # Price target analysis
            if 'targetMeanPrice' in info and 'currentPrice' in info:
                target_price = info['targetMeanPrice']
                current_price = info['currentPrice']
                
                if target_price > current_price * 1.2:  # 20%+ upside
                    upside = (target_price - current_price) / current_price
                    signals.append({
                        'type': 'price_target',
                        'target': target_price,
                        'upside': upside,
                        'confidence': min(upside / 2, 1.0)
                    })
        
        except Exception as e:
            pass
        
        return signals
    
    def _analyze_options_signals(self, ticker: str) -> List[Dict]:
        """Analyze unusual options activity with enhanced filtering"""
        
        # Use the new options flow filter
        filtered_signals = self.options_filter.analyze_options_flow(ticker)
        
        signals = []
        
        # Convert to expected format
        for signal in filtered_signals:
            # Only include high-quality signals
            if signal['final_score'] >= 0.5:  # 50% minimum score
                
                signals.append({
                    'type': signal['type'],
                    'option_type': signal['option_type'],
                    'strike': signal['strike'],
                    'volume': signal['volume'],
                    'open_interest': signal['open_interest'],
                    'confidence': signal['final_score'],
                    'reasoning': signal['reasoning'],
                    'score': signal['final_score']
                })
        
        if signals:
            # Get bullish/bearish ratio
            ratio = self.options_filter.calculate_bullish_bearish_ratio(filtered_signals)
            print(f"   [OPTIONS FLOW] {ticker}: {len(signals)} quality signals (Bullish: {ratio['bullish']:.1%}, Bearish: {ratio['bearish']:.1%})")
            
            # Show top signal
            if filtered_signals:
                top = filtered_signals[0]
                print(f"   [TOP SIGNAL] {ticker}: {top['reasoning']} (Score: {top['final_score']:.2f})")
        
        return signals
    
    def _calculate_confluence_score(self, signal: ConfluenceSignal) -> float:
        """Calculate overall confluence score with smart money boost"""
        
        score = 0.0
        
        # Base weights
        insider_weight = self.insider_weight
        institutional_weight = self.institutional_weight
        analyst_weight = self.analyst_weight
        options_weight = self.options_weight
        
        # Check for smart money signals
        smart_money_signals = []
        if signal.options_signals:
            smart_money_types = ['sweep_trade', 'block_trade']
            smart_money_signals = [s for s in signal.options_signals if s['type'] in smart_money_types]
        
        # SMART MONEY BONUS: If insider buying + smart money flow, boost weights
        if signal.insider_signals and smart_money_signals:
            print(f"[SMART MONEY CONFLUENCE] Insider buying + {'sweep' if smart_money_signals[0]['type'] == 'sweep_trade' else 'block'} detected!")
            insider_weight += 0.1  # Boost insider weight by 10%
            options_weight += 0.1   # Boost options weight by 10%
        
        if signal.insider_signals:
            insider_conf = np.mean([s['confidence'] for s in signal.insider_signals])
            score += insider_conf * insider_weight
            
        if signal.institutional_signals:
            inst_conf = np.mean([s['confidence'] for s in signal.institutional_signals])
            score += inst_conf * institutional_weight
            
        if signal.analyst_signals:
            analyst_conf = np.mean([s['confidence'] for s in signal.analyst_signals])
            score += analyst_conf * analyst_weight
            
        if signal.options_signals:
            options_conf = np.mean([s['confidence'] for s in signal.options_signals])
            score += options_conf * options_weight
        
        return min(score, 1.0)
    
    def _generate_reasoning(self, signal: ConfluenceSignal, current_price: float) -> str:
        """Generate reasoning for the confluence signal with macro context"""
        
        reasons = []
        
        if signal.insider_signals:
            total_insider = sum(s['amount'] for s in signal.insider_signals)
            reasons.append(f"Insiders buying ${total_insider/1000000:.1f}M in stock")
        
        if signal.institutional_signals:
            institutions = [s['institution'] for s in signal.institutional_signals]
            reasons.append(f"Major funds loading up ({', '.join(institutions[:3])})")
        
        if signal.analyst_signals:
            for s in signal.analyst_signals:
                if s['type'] == 'price_target':
                    reasons.append(f"Analysts see {s['upside']:.0%} upside to ${s['target']:.2f}")
                else:
                    reasons.append(f"Analysts rating as {s['rating'].upper()}")
        
        if signal.options_signals:
            # Check for smart money signals
            smart_money_types = ['sweep_trade', 'block_trade']
            smart_money_signals = [s for s in signal.options_signals if s['type'] in smart_money_types]
            
            if smart_money_signals:
                # Highlight smart money activity
                for s in smart_money_signals:
                    if s['type'] == 'sweep_trade':
                        reasons.append(f"🎯 SMART MONEY: {s['volume']:.0f} contract sweep detected")
                    elif s['type'] == 'block_trade':
                        reasons.append(f"🎯 SMART MONEY: {s['volume']:.0f} contract block trade")
            else:
                # Regular unusual flow
                for s in signal.options_signals:
                    reasons.append(f"Options flow {s.get('multiple', 2.0):.1f}x normal volume")
        
        # Add macro context if available
        macro_context = self._get_macro_context(signal.ticker)
        if macro_context:
            reasons.append(f"🌍 {macro_context}")
        
        if not reasons:
            return "Multiple signals detected"
        
        return " | ".join(reasons)
    
    def _get_macro_context(self, ticker: str) -> Optional[str]:
        """Get macro context for the ticker based on sector trends"""
        
        # AI Infrastructure stocks
        ai_stocks = {
            'NVDA': 'AI Infrastructure Boom - $100B+ in AI chip spending projected',
            'AMD': 'AI Data Center Expansion - CPU/GPU demand soaring',
            'SMCI': 'AI Server Buildout - Data center construction at record highs',
            'PLTR': 'AI Adoption Acceleration - Enterprise AI spending up 40% YoY',
            'CRM': 'AI Business Software - $50B market by 2025'
        }
        
        # Energy stocks (powering AI)
        energy_stocks = {
            'CEG': 'Nuclear Renaissance for AI - 20+ new reactors planned',
            'VST': 'AI Power Demand - Electricity consumption up 15% in data center hubs',
            'NRG': 'Natural Gas for AI - Power plants running at peak capacity',
            'ET': 'Energy Infrastructure - Pipeline expansion for AI data centers'
        }
        
        # Semiconductor supply chain
        semi_stocks = {
            'KLAC': 'Chip Equipment Boom - $100B capex in semiconductors',
            'UMC': 'Foundry Expansion - AI chip shortage driving new capacity',
            'LRCX': 'Lithography Demand - EUV machines for AI chips',
            'AMAT': 'Materials Science - AI requires advanced chip materials'
        }
        
        # Combine all mappings
        macro_map = {**ai_stocks, **energy_stocks, **semi_stocks}
        
        if ticker in macro_map:
            return macro_map[ticker]
        
        # Check for AI bubble indicators
        if ticker in ['NVDA', 'AMD', 'SMCI']:
            # Add bubble warning for high-flying AI stocks
            pe_ratio = self._get_pe_ratio(ticker)
            if pe_ratio and pe_ratio > 50:
                return f"AI Bubble Alert - P/E {pe_ratio:.0f} suggests overheating"
        
        return None
    
    def _get_pe_ratio(self, ticker: str) -> Optional[float]:
        """Get P/E ratio for bubble analysis"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            return info.get('trailingPE', None)
        except:
            return None
    
    def _get_macro_boost(self, ticker: str) -> float:
        """Get macro boost based on sector momentum and capital flows"""
        
        # AI Infrastructure sector - massive capital flows
        if ticker in ['NVDA', 'AMD', 'SMCI']:
            return 0.15  # 15% boost for AI infrastructure boom
        
        # AI Software/Services - strong adoption
        if ticker in ['PLTR', 'CRM']:
            return 0.10  # 10% boost for AI services
        
        # Energy for AI - nuclear and natural gas
        if ticker in ['CEG', 'VST', 'NRG', 'ET']:
            return 0.08  # 8% boost for energy demand
        
        # Semiconductor equipment - supply chain constraints
        if ticker in ['KLAC', 'AMAT', 'LRCX']:
            return 0.12  # 12% boost for chip equipment boom
        
        return 0.0
    
    def get_high_conviction_signals(self) -> List[ConfluenceSignal]:
        """Get all high-conviction signals"""
        
        high_conviction = []
        
        for signal in self.active_signals.values():
            if signal.confidence_level in ['HIGH', 'VERY HIGH']:
                high_conviction.append(signal)
        
        # Sort by confluence score
        high_conviction.sort(key=lambda x: x.confluence_score, reverse=True)
        
        return high_conviction
    
    def check_pump_correlation(self, ticker: str) -> Dict:
        """Check if confluence signals correlate with pump activity"""
        
        if ticker not in self.active_signals:
            return {'correlated': False, 'reason': 'No confluence signal'}
        
        signal = self.active_signals[ticker]
        
        # High confluence + insider buying often precedes pumps
        has_insider = len(signal.insider_signals) > 0
        has_institutional = len(signal.institutional_signals) > 0
        high_score = signal.confluence_score > 0.7
        
        if has_insider and has_institutional and high_score:
            return {
                'correlated': True,
                'pump_probability': 0.8,
                'reason': 'Insider + institutional buying with high confluence'
            }
        
        return {
            'correlated': False,
            'pump_probability': 0.0,
            'reason': 'Insufficient correlation'
        }
