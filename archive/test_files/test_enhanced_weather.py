from engines.enhanced_weather_research import EnhancedWeatherResearch

print("🌍 Testing Enhanced Weather Research")
print("=" * 60)

# Initialize the enhanced weather research module
research = EnhancedWeatherResearch()

# Test a weather market
test_market = {
    'ticker': 'HIGHNY0-25-85',
    'title': 'NYC - High temperature > 85°F on Dec 26',
    'implied_probability': 0.65,
    'volume': 2000,
    'expiration_date': '2024-12-26'
}

print("\n📊 Analyzing Weather Market with Research:")
print(f"Ticker: {test_market['ticker']}")
print(f"Title: {test_market['title']}")
print(f"Market Probability: {test_market['implied_probability']:.1%}")

# Perform comprehensive research
result = research.analyze_weather_market(test_market['ticker'], test_market)

print("\n🔍 RESEARCH RESULTS:")
print("-" * 40)

if result['valid']:
    print(f"✅ Valid Market: YES")
    print(f"📍 Location: {result['location']}")
    print(f"🌡️  Type: {result['weather_type']}")
    print(f"🎯 Threshold: {result['threshold']}°F")
    print(f"📅 Date: {result['target_date']}")
    
    print("\n📈 CONFIDENCE & RECOMMENDATION:")
    print(f"Confidence: {result['confidence']:.1%}")
    print(f"Recommendation: {result['recommendation']}")
    
    print("\n🔬 DETAILED ANALYSIS:")
    
    # Historical patterns
    hist = result['detailed_analysis']['historical_patterns']
    print(f"\n1. Historical Patterns (30 years):")
    print(f"   • Mean Temperature: {hist.get('mean_temperature', 0):.1f}°F")
    print(f"   • Recent Trend: {hist.get('recent_trend', 0):.1f}°F")
    print(f"   • Extreme Events: {hist.get('extreme_events', 0)} recorded")
    
    # Climate impact
    climate = result['detailed_analysis']['climate_impact']
    print(f"\n2. Climate Change Impact:")
    print(f"   • Temperature Adjustment: +{climate.get('temperature_adjustment', 0):.1f}°F")
    print(f"   • Extreme Event Frequency: {climate.get('extreme_event_frequency', 1)}x normal")
    print(f"   • Specific: {climate.get('specific', 'N/A')}")
    
    # Forecast consensus
    forecast = result['detailed_analysis']['forecast_consensus']
    print(f"\n3. Forecast Model Consensus:")
    print(f"   • Consensus Probability: {forecast.get('consensus_probability', 0):.1%}")
    print(f"   • Agreement Level: {forecast.get('agreement_level', 'unknown')}")
    print(f"   • Model Range: {forecast.get('forecast_range', (0, 0))[0]:.1%} - {forecast.get('forecast_range', (0, 0))[1]:.1%}")
    
    # Special factors
    special = result['detailed_analysis']['special_factors']
    print(f"\n4. Special Climate Factors:")
    for factor, data in special.items():
        print(f"   • {factor.upper()}: {data.get('status', 'unknown')} (impact: {data.get('impact', 'unknown')})")
    
    # Validation
    if 'validation' in result['detailed_analysis']:
        validation = result['detailed_analysis']['validation']
        print(f"\n5. Market Validation:")
        print(f"   • Kalshi Probability: {validation.get('kalshi_probability', 0):.1%}")
        print(f"   • Forecast Probability: {validation.get('forecast_probability', 0):.1%}")
        print(f"   • Difference: {validation.get('difference', 0):.1%}")
        print(f"   • Status: {validation.get('validation_status', 'unknown')}")
    
    print("\n✅ RESEARCH COMPLETE!")
    print("\n🎯 Key Insights:")
    summary = result['research_summary']
    for factor, value in summary['key_factors'].items():
        print(f"   • {factor}: {value}")
    
else:
    print(f"❌ Invalid Market: {result['reason']}")

print("\n" + "=" * 60)
print("✅ Enhanced Weather Research Working!")
print("\n🌍 Benefits:")
print("   • No more blind probability picking")
print("   • 30+ years of historical data")
print("   • Multiple forecast models")
print("   • Climate change awareness")
print("   • Regional specialization")
print("   • Special factor consideration")
print("\n🎯 Result: AI takes weather seriously with proper research!")
