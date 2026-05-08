#!/usr/bin/env python3
"""
Test script to demonstrate P/E Ratio Analyzer capabilities
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.pe_ratio_analyzer import PERatioAnalyzer

def test_pe_analyzer():
    """Test the P/E analyzer with various stocks"""
    
    print("="*80)
    print("P/E RATIO ANALYZER DEMONSTRATION")
    print("="*80)
    print("\nThis shows the AI now truly understands P/E ratios beyond just fetching numbers!")
    
    # Initialize analyzer
    analyzer = PERatioAnalyzer()
    
    # Test stocks from different sectors
    test_stocks = [
        ("AAPL", "Technology - Mature growth"),
        ("MSFT", "Software - Cloud leader"),
        ("NVDA", "Semiconductors - High growth"),
        ("JPM", "Financial Services - Bank"),
        ("JNJ", "Healthcare - Stable"),
        ("XOM", "Energy - Oil major"),
        ("TSLA", "Automotive - Growth story"),
        ("AMZN", "E-commerce/Cloud"),
        ("PG", "Consumer Staples"),
        ("PLUG", "Energy - Hydrogen (no P/E)")
    ]
    
    print("\n" + "="*80)
    print("COMPREHENSIVE P/E ANALYSIS RESULTS")
    print("="*80)
    
    for ticker, description in test_stocks:
        print(f"\n{'='*60}")
        print(f"{ticker} - {description}")
        print(f"{'='*60}")
        
        # Get full analysis
        analysis = analyzer.analyze_pe_ratio(ticker)
        
        if analysis.get("error"):
            print(f"❌ {analysis['error']}")
            continue
        
        # Display key metrics
        print(f"\n📊 CURRENT METRICS:")
        print(f"   P/E Ratio: {analysis['current_pe']:.1f}")
        if analysis.get('forward_pe'):
            print(f"   Forward P/E: {analysis['forward_pe']:.1f}")
        print(f"   Sector: {analysis['sector']}")
        print(f"   Market Cap: ${analysis['market_cap']/1e9:.1f}B")
        
        # Industry comparison
        print(f"\n🏭 INDUSTRY COMPARISON:")
        print(f"   Industry Avg P/E: {analysis['industry_pe']:.1f}")
        print(f"   vs Industry: {analysis['pe_vs_industry']:.1f}x ({analysis['industry_analysis']['classification']})")
        
        # PEG analysis
        if analysis.get("peg_ratio"):
            print(f"\n📈 GROWTH ANALYSIS (PEG):")
            print(f"   PEG Ratio: {analysis['peg_ratio']:.2f}")
            print(f"   Interpretation: {analysis['peg_interpretation']}")
            if analysis.get('eps_growth'):
                print(f"   EPS Growth: {analysis['eps_growth']*100:.1f}%")
        
        # Historical context
        if analysis.get('historical_avg'):
            print(f"\n📊 HISTORICAL CONTEXT:")
            print(f"   5-Year Avg P/E: {analysis['historical_avg']:.1f}")
            print(f"   Current Percentile: {analysis['pe_percentile']*100:.0f}%")
            print(f"   Trend: {analysis['trend']} ({analysis['trend_strength']}/5)")
        
        # Valuation assessment
        print(f"\n💰 VALUATION ASSESSMENT:")
        print(f"   Level: {analysis['valuation_level']}")
        print(f"   Score: {analysis['valuation_score']}/10")
        
        # Fair value
        fair_value = analysis['fair_value_range']
        print(f"\n🎯 FAIR VALUE ESTIMATE:")
        print(f"   Fair P/E Range: {fair_value['low']}-{fair_value['high']}")
        print(f"   Current vs Fair: {fair_value['current_vs_fair']:.1f}x")
        
        # Summary
        if fair_value['current_vs_fair'] < 0.8:
            summary = "SIGNIFICANTLY UNDervalued"
        elif fair_value['current_vs_fair'] < 1.0:
            summary = "Modestly Undervalued"
        elif fair_value['current_vs_fair'] < 1.2:
            summary = "Near Fair Value"
        else:
            summary = "OVERVALUED"
        
        print(f"\n🎯 SUMMARY: {summary}")
    
    # Demonstrate screening capability
    print("\n" + "="*80)
    print("P/E SCREENING DEMONSTRATION")
    print("="*80)
    
    # Screen for low P/E stocks
    all_tickers = [t[0] for t in test_stocks]
    low_pe_stocks = analyzer.screen_by_pe(all_tickers, max_pe=20)
    
    print(f"\n🔍 Stocks with P/E < 20:")
    for stock in low_pe_stocks[:5]:
        print(f"   {stock['ticker']}: P/E {stock['pe']:.1f}, Score {stock['score']}/10")
    
    # Screen for attractive PEG ratios
    attractive_peg = []
    for ticker in all_tickers:
        analysis = analyzer.analyze_pe_ratio(ticker)
        if analysis.get("peg_ratio") and analysis["peg_ratio"] < 1.5:
            attractive_peg.append({
                "ticker": ticker,
                "peg": analysis["peg_ratio"],
                "pe": analysis["current_pe"]
            })
    
    print(f"\n🔍 Stocks with PEG < 1.5:")
    for stock in sorted(attractive_peg, key=lambda x: x["peg"])[:5]:
        print(f"   {stock['ticker']}: PEG {stock['peg']:.2f}, P/E {stock['pe']:.1f}")
    
    print("\n" + "="*80)
    print("✅ P/E ANALYSIS COMPLETE")
    print("="*80)
    print("\n🧠 The AI now demonstrates TRUE P/E understanding:")
    print("   ✓ Compares to industry averages")
    print("   ✓ Calculates and interprets PEG ratios")
    print("   ✓ Analyzes historical P/E trends")
    print("   ✓ Provides fair value estimates")
    print("   ✓ Scores valuation from 0-10")
    print("   ✓ Screens stocks based on P/E criteria")
    print("\n💡 This goes far beyond just fetching P/E numbers!")

if __name__ == "__main__":
    test_pe_analyzer()
