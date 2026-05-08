#!/usr/bin/env python3
"""
Test script to demonstrate Undervalued Stock Detector capabilities
Finds stocks that could go from $30 to $400+ if everything goes right
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.undervalued_stock_detector import UndervaluedStockDetector

def test_hidden_gems():
    """Test the hidden gem detector with potential 10x stocks"""
    
    print("="*80)
    print("HIDDEN GEM DETECTOR - FINDING 10X POTENTIAL STOCKS")
    print("="*80)
    print("\n🔍 This AI system identifies deeply undervalued stocks that could")
    print("   go from $30 to $400+ if everything goes right!")
    print("   It analyzes business models, TAM penetration, catalysts, and more.\n")
    
    # Initialize detector
    detector = UndervaluedStockDetector()
    
    # Test stocks - mix of potential hidden gems
    test_stocks = [
        ("PLUG", "Hydrogen fuel cell pioneer"),
        ("NKLA", "Electric truck innovator"),
        ("RIVN", "EV startup with Amazon backing"),
        ("LCID", "Luxury EV manufacturer"),
        ("CHPT", "EV charging infrastructure"),
        ("GOEV", "Commercial electric vehicles"),
        ("FSR", "Electric vehicle technology"),
        ("SOFI", "Fintech disruptor"),
        ("UPST", "AI lending platform"),
        ("COIN", "Crypto exchange"),
        ("HOOD", "Commission-free trading"),
        ("AFRM", "Buy now, pay later"),
        ("ROKU", "Streaming platform"),
        ("ZM", "Video communications"),
        ("DOCU", "Digital document management")
    ]
    
    print("ANALYZING STOCKS FOR 10X POTENTIAL...\n")
    
    hidden_gems = []
    
    for ticker, description in test_stocks:
        print(f"{'='*60}")
        print(f"Analyzing: {ticker} - {description}")
        print(f"{'='*60}")
        
        # Get full analysis
        analysis = detector.analyze_undervaluation(ticker)
        
        if analysis.get("error"):
            print(f"❌ {analysis['error']}")
            continue
        
        # Key metrics
        price = analysis["current_price"]
        market_cap = analysis["market_cap"]
        potential = analysis["potential_score"]
        
        print(f"\n💎 CURRENT STATUS:")
        print(f"   Price: ${price:.2f}")
        print(f"   Market Cap: ${market_cap:.1f}B")
        print(f"   Potential Score: {potential['total_score']}/10")
        print(f"   Category: {potential['category']}")
        
        # Business analysis
        business = analysis["business_model"]
        if business.get("disruption_category"):
            print(f"\n🚀 DISRUPTION POTENTIAL:")
            print(f"   Sector: {business['disruption_category']}")
            print(f"   Disruption Score: {business['disruption_score']}/10")
            print(f"   Moat Strength: {business['moat_score']}/10")
        
        # Valuation
        valuation = analysis["valuation"]
        print(f"\n💰 VALUATION METRICS:")
        if valuation.get("pe_ratio"):
            print(f"   P/E Ratio: {valuation['pe_ratio']:.1f}")
        if valuation.get("ps_ratio"):
            print(f"   P/S Ratio: {valuation['ps_ratio']:.1f}")
        print(f"   Undervaluation Score: {valuation['undervaluation_score']}/10")
        
        # Growth runway
        growth = analysis["growth"]
        print(f"\n📈 GROWTH RUNWAY:")
        print(f"   Market Penetration: {growth['current_penetration']:.2f}%")
        print(f"   Growth Runway Score: {growth['runway_score']}/10")
        
        # Catalysts
        catalysts = analysis["catalysts"]
        if catalysts["identified_catalysts"]:
            print(f"\n⚡ EARLY CATALYSTS:")
            print(f"   Signals: {', '.join(catalysts['identified_catalysts'])}")
            print(f"   Catalyst Score: {catalysts['catalyst_score']}/10")
        
        # Future potential
        scenarios = analysis["future_scenarios"]
        print(f"\n🔮 FUTURE SCENARIOS:")
        print(f"   Base Case Return: {scenarios['base_case']['return']*100:.0f}%")
        print(f"   Best Case Return: {scenarios['best_case']['return']*100:.0f}%")
        print(f"   Expected Return: {scenarios['expected_return']*100:.0f}%")
        
        # Calculate potential future price
        best_case_price = scenarios["best_case"]["price"]
        upside = scenarios["upside_potential"]
        
        print(f"\n💎 POTENTIAL OUTCOME:")
        print(f"   Current Price: ${price:.2f}")
        print(f"   Best Case Target: ${best_case_price:.2f}")
        print(f"   Upside Potential: {upside*100:.0f}x")
        
        # Check if it's a hidden gem
        if potential["total_score"] >= 7.0:
            hidden_gems.append({
                "ticker": ticker,
                "price": price,
                "potential_score": potential["total_score"],
                "category": potential["category"],
                "upside": upside,
                "best_case_price": best_case_price
            })
            print(f"\n✨ HIDDEN GEM DETECTED! ✨")
            print(f"   This stock has {potential['category']}")
        elif potential["total_score"] >= 5.5:
            print(f"\n👀 WORTH WATCHING")
            print(f"   Moderate potential - keep on radar")
        else:
            print(f"\n⚠️ LIMITED POTENTIAL")
            print(f"   Doesn't meet hidden gem criteria")
    
    # Summary of hidden gems found
    print("\n" + "="*80)
    print("HIDDEN GEMS SUMMARY")
    print("="*80)
    
    if hidden_gems:
        print(f"\n🎯 Found {len(hidden_gems)} hidden gems with 10x+ potential:\n")
        
        # Sort by potential score
        hidden_gems.sort(key=lambda x: x["potential_score"], reverse=True)
        
        for i, gem in enumerate(hidden_gems, 1):
            print(f"{i}. {gem['ticker']}")
            print(f"   Current: ${gem['price']:.2f} → Target: ${gem['best_case_price']:.2f}")
            print(f"   Potential: {gem['upside']:.1f}x | Score: {gem['potential_score']}/10")
            print(f"   Category: {gem['category']}\n")
        
        # Top pick
        top_gem = hidden_gems[0]
        print(f"🏆 TOP PICK: {top_gem['ticker']}")
        print(f"   Highest potential score: {top_gem['potential_score']}/10")
        print(f"   Could turn ${top_gem['price']:.2f} into ${top_gem['best_case_price']:.2f}")
        
    else:
        print("\n😔 No hidden gems found in this batch.")
        print("   Try analyzing smaller, undiscovered stocks")
    
    print("\n" + "="*80)
    print("✅ HIDDEN GEM ANALYSIS COMPLETE")
    print("="*80)
    print("\n🧠 The AI now identifies stocks that could go from $30 to $400+!")
    print("   It looks for:")
    print("   ✓ Disruptive technology in early stages")
    print("   ✓ Massive market opportunity (<1% penetrated)")
    print("   ✓ Strong competitive moats")
    print("   ✓ Near-term catalysts")
    print("   ✓ Deep undervaluation vs potential")
    print("\n💡 These are the stocks Wall Street hasn't discovered yet!")

if __name__ == "__main__":
    test_hidden_gems()
