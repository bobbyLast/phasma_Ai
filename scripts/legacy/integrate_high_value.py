"""
Integration Script for High-Value Components
This script will add useful engines to the main trading system
"""

import os
import shutil

def update_main_py():
    """Add imports and initialization for high-value components"""
    
    # Read current main.py
    with open('c:/Users/kyran/CascadeProjects/phasma_Ai/main.py', 'r') as f:
        content = f.read()
    
    # Check if already integrated
    if 'from engines.advanced_sentiment_engine import AdvancedSentimentEngine' in content:
        print("Components already integrated!")
        return
    
    # Add imports after existing imports
    import_section = """
# High-value analysis engines to integrate
from engines.advanced_sentiment_engine import AdvancedSentimentEngine
from engines.iv_crush_predictor import IVCrushPredictor
from engines.earnings_drift_engine import EarningsDriftEngine
from utils.sector_momentum_tracker import SectorMomentumTracker
from utils.dark_pool_detector import DarkPoolDetector
from utils.options_flow_analyzer import OptionsFlowAnalyzer
from utils.short_interest_tracker import ShortInterestTracker
from utils.correlation_analyzer import CorrelationAnalyzer
from engines.technical_analysis_engine import TechnicalAnalysisEngine
from engines.volatility_edge_engine import VolatilityEdgeEngine
"""
    
    # Find insertion point (after existing imports)
    insert_pos = content.find('from unified_trading_system import UnifiedTradingSystem')
    if insert_pos != -1:
        content = content[:insert_pos] + import_section + content[insert_pos:]
    
    # Add initialization in __init__
    init_section = """
        # Initialize high-value analysis engines
        self.advanced_sentiment = AdvancedSentimentEngine(self.config)
        self.iv_crush_predictor = IVCrushPredictor(self.config)
        self.earnings_drift = EarningsDriftEngine(self.config)
        self.sector_momentum = SectorMomentumTracker(self.config)
        self.dark_pool_detector = DarkPoolDetector(self.config)
        self.options_flow = OptionsFlowAnalyzer(self.config)
        self.short_tracker = ShortInterestTracker(self.config)
        self.correlation_tracker = CorrelationAnalyzer(self.config)
        self.technical_analysis = TechnicalAnalysisEngine(self.config)
        self.volatility_edge = VolatilityEdgeEngine(self.config)
        print("✅ High-Value Analysis Engines Initialized")
"""
    
    # Find insertion point in __init__
    insert_pos = content.find('self.convergence_engine = SignalConvergenceEngine()')
    if insert_pos != -1:
        # Find end of this line
        end_pos = content.find('\n', insert_pos) + 1
        content = content[:end_pos] + init_section + content[end_pos:]
    
    # Write updated content
    with open('c:/Users/kyran/CascadeProjects/phasma_Ai/main.py', 'w') as f:
        f.write(content)
    
    print("✅ Added imports and initialization to main.py")

def add_to_trading_loop():
    """Add advanced analysis to the main trading loop"""
    
    with open('c:/Users/kyran/CascadeProjects/phasma_Ai/main.py', 'r') as f:
        content = f.read()
    
    # Add advanced analysis section
    analysis_code = """
        # 2.5. Advanced Analysis - Generate additional signals
        advanced_signals = []
        
        try:
            # Sentiment Analysis
            if news_items:
                sentiment_analysis = self.advanced_sentiment.analyze_batch(news_items)
                if sentiment_analysis:
                    advanced_signals.extend(sentiment_analysis)
                    print(f"   ✅ Sentiment Analysis: {len(sentiment_analysis)} signals")
            
            # IV Crush Prediction (if options enabled)
            if self.options_enabled:
                iv_signals = self.iv_crush_predictor.predict_crush_opportunities()
                if iv_signals:
                    advanced_signals.extend(iv_signals)
                    print(f"   ✅ IV Crush Prediction: {len(iv_signals)} opportunities")
            
            # Earnings Drift
            earnings_signals = self.earnings_drift.scan_for_drift_opportunities()
            if earnings_signals:
                advanced_signals.extend(earnings_signals)
                print(f"   ✅ Earnings Drift: {len(earnings_signals)} opportunities")
            
            # Sector Momentum
            sector_signals = self.sector_momentum.get_sector_rotation_signals()
            if sector_signals:
                advanced_signals.extend(sector_signals)
                print(f"   ✅ Sector Momentum: {len(sector_signals)} signals")
            
            # Dark Pool & Options Flow
            flow_signals = []
            dark_pool_signals = self.dark_pool_detector.detect_unusual_activity()
            if dark_pool_signals:
                flow_signals.extend(dark_pool_signals)
            
            options_flow_signals = self.options_flow.scan_for_unusual_flow()
            if options_flow_signals:
                flow_signals.extend(options_flow_signals)
            
            if flow_signals:
                advanced_signals.extend(flow_signals)
                print(f"   ✅ Flow Analysis: {len(flow_signals)} unusual activities")
            
            # Short Squeeze Detection
            short_signals = self.short_tracker.scan_squeeze_candidates()
            if short_signals:
                advanced_signals.extend(short_signals)
                print(f"   ✅ Short Squeeze: {len(short_signals)} candidates")
            
            # Correlation Analysis
            correlation_signals = self.correlation_tracker.find_correlation_opportunities()
            if correlation_signals:
                advanced_signals.extend(correlation_signals)
                print(f"   ✅ Correlation Analysis: {len(correlation_signals)} opportunities")
            
            # Technical Analysis
            tech_signals = self.technical_analysis.scan_technical_signals()
            if tech_signals:
                advanced_signals.extend(tech_signals)
                print(f"   ✅ Technical Analysis: {len(tech_signals)} signals")
            
            # Volatility Edge
            vol_signals = self.volatility_edge.scan_volatility_edges()
            if vol_signals:
                advanced_signals.extend(vol_signals)
                print(f"   ✅ Volatility Edge: {len(vol_signals)} signals")
            
        except Exception as e:
            print(f"   ⚠️ Advanced analysis error: {e}")
        
        # Add advanced signals to opportunities
        all_opportunities.extend(advanced_signals)
"""
    
    # Find insertion point (after Kalshi scanning)
    insert_pos = content.find('all_opportunities.extend(kalshi_opportunities)')
    if insert_pos != -1:
        # Find end of this line
        end_pos = content.find('\n', insert_pos) + 1
        content = content[:end_pos] + analysis_code + content[end_pos:]
    
    # Write updated content
    with open('c:/Users/kyran/CascadeProjects/phasma_Ai/main.py', 'w') as f:
        f.write(content)
    
    print("✅ Added advanced analysis to trading loop")

def update_config():
    """Add configuration for advanced features"""
    
    with open('c:/Users/kyran/CascadeProjects/phasma_Ai/config.json', 'r') as f:
        config = f.read()
    
    # Add advanced features config
    import json
    config_dict = json.loads(config)
    
    if 'advanced_features' not in config_dict:
        config_dict['advanced_features'] = {
            "sentiment_analysis": True,
            "iv_crush_prediction": True,
            "earnings_drift": True,
            "sector_momentum": True,
            "dark_pool_detection": True,
            "options_flow": True,
            "short_interest": True,
            "correlation_analysis": True,
            "technical_analysis": True,
            "volatility_edge": True
        }
        
        with open('c:/Users/kyran/CascadeProjects/phasma_Ai/config.json', 'w') as f:
            json.dump(config_dict, f, indent=2)
        
        print("✅ Added advanced features to config")

def main():
    """Run the integration"""
    print("🚀 Starting High-Value Components Integration...")
    print()
    
    print("1. Updating main.py with imports and initialization...")
    update_main_py()
    
    print("\n2. Adding advanced analysis to trading loop...")
    add_to_trading_loop()
    
    print("\n3. Updating configuration...")
    update_config()
    
    print("\n✅ Integration complete!")
    print("\nNext steps:")
    print("1. Test the system with: python main.py")
    print("2. Monitor logs for new signal types")
    print("3. Adjust thresholds in config as needed")

if __name__ == "__main__":
    main()
