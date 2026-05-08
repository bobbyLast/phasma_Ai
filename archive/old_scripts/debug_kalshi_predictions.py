#!/usr/bin/env python3
"""
Debug why Kalshi analysis isn't generating trading signals from real markets
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from engines.kalshi_engine import KalshiPredictionEngine

def debug_predictions():
    """Debug the prediction and analysis pipeline with real market data"""
    
    print("🔍 DEBUGGING KALSHI PREDICTION PIPELINE")
    print("=" * 50)
    
    config = {'kalshi': {'api_key': None}}
    engine = KalshiPredictionEngine(config)
    
    try:
        # Get real markets from the working series
        print("📡 Fetching real markets from KXGDP and KXHIGHNY...")
        
        # Test KXGDP markets (GDP-related)
        gdp_url = "markets?series_ticker=KXGDP&status=open"
        gdp_response = engine._get(gdp_url)
        gdp_markets = gdp_response.get('markets', []) if gdp_response else []
        
        # Test KXHIGHNY markets (temperature-related)
        high_url = "markets?series_ticker=KXHIGHNY&status=open"
        high_response = engine._get(high_url)
        high_markets = high_response.get('markets', []) if high_response else []
        
        print(f"✅ Found {len(gdp_markets)} GDP markets and {len(high_markets)} temperature markets")
        
        # Test a few markets in detail
        test_markets = gdp_markets[:2] + high_markets[:2]
        
        for i, market in enumerate(test_markets):
            print(f"\n🔍 TESTING MARKET {i+1}:")
            print(f"   Ticker: {market.get('ticker')}")
            print(f"   Title: {market.get('title')}")
            print(f"   Series: {market.get('series_ticker')}")
            print(f"   Yes Ask: {market.get('yes_ask')}¢")
            print(f"   Volume: {market.get('volume')}")
            print(f"   Status: {market.get('status')}")
            
            # Test Phasma prediction
            print(f"   🧠 GENERATING PHASMA PREDICTION...")
            try:
                prediction = engine.generate_phasma_prediction(market)
                print(f"      Prediction: {prediction}")
                print(f"      Type: {type(prediction)}")
            except Exception as e:
                print(f"      ❌ Prediction failed: {e}")
                prediction = None
            
            # Test market analysis
            print(f"   📊 RUNNING MARKET ANALYSIS...")
            try:
                analysis = engine.analyze_market_opportunity(market, prediction)
                print(f"      Signal: {analysis.get('signal')}")
                print(f"      Confidence: {analysis.get('confidence', 0):.1%}")
                print(f"      Rationale: {analysis.get('rationale', 'No rationale')[:100]}...")
                print(f"      Market Probability: {analysis.get('market_probability', 0):.1%}")
                
                # Check qualification
                signal = analysis.get('signal')
                confidence = analysis.get('confidence', 0)
                
                if signal and confidence >= 0.6:
                    print(f"      ✅ QUALIFIED OPPORTUNITY!")
                else:
                    print(f"      ❌ Not qualified - Signal: {signal}, Confidence: {confidence:.1%}")
                    
            except Exception as e:
                print(f"      ❌ Analysis failed: {e}")
        
        # Test with lower confidence threshold
        print(f"\n🎯 TESTING WITH LOWER CONFIDENCE THRESHOLD (40%)...")
        
        for market in test_markets:
            try:
                prediction = engine.generate_phasma_prediction(market)
                analysis = engine.analyze_market_opportunity(market, prediction)
                
                signal = analysis.get('signal')
                confidence = analysis.get('confidence', 0)
                
                if signal and confidence >= 0.4:
                    print(f"   ✅ FOUND OPPORTUNITY AT 40%: {market.get('ticker')} - {signal} ({confidence:.1%})")
                    
            except Exception as e:
                continue
        
        return True
        
    except Exception as e:
        print(f"❌ Debug error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_predictions()
    
    print("\n" + "=" * 50)
    print("🎯 DEBUG COMPLETE")
    print("=" * 50)
