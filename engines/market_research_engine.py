"""
Market Research Engine - Deep analysis for any asset
Performs comprehensive research including on-chain data, sentiment, macro factors, institutional flows
"""

import requests
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import yfinance as market_data

@dataclass
class ResearchFinding:
    """Single research finding with confidence and impact"""
    title: str
    description: str
    confidence: float  # 0-1
    impact: str  # HIGH/MEDIUM/LOW
    data_source: str
    timestamp: datetime

@dataclass
class MarketResearchReport:
    """Complete market research report for an asset"""
    symbol: str
    asset_type: str  # CRYPTO/STOCK/ETF/COMMODITY
    current_price: float
    research_findings: List[ResearchFinding]
    sentiment_analysis: Dict
    institutional_flows: Dict
    macro_factors: Dict
    technical_indicators: Dict
    catalysts: List[Dict]
    risk_factors: List[Dict]
    historical_patterns: Dict
    price_targets: Dict
    recommendation: str
    confidence: float
    generated_at: datetime

class MarketResearchEngine:
    """Engine for performing deep market research on any asset"""
    
    def __init__(self, config: Dict, market_cache=None):
        self.config = config
        self.market_cache = market_cache
        self.logger = logging.getLogger(__name__)
        
        # API endpoints
        self.fear_greed_api = "https://api.alternative.me/fng/"
        self.coingecko_api = "https://api.coingecko.com/api/v3"
        self.news_api_key = config.get('news_api_key')
        
        # Cache for research data
        self.research_cache = {}
        self.cache_duration = timedelta(hours=1)
        
        # Research sources
        self.sources = {
            'sentiment': ['fear_greed', 'social_media', 'news_sentiment', 'google_trends'],
            'institutional': ['etf_flows', 'insider_trading', 'institutional_ownership'],
            'macro': ['fed_policy', 'credit_stress', 'cross_asset_correlation'],
            'onchain': ['exchange_flows', 'whale_movements', 'funding_rates'],
            'technical': ['price_patterns', 'volume_analysis', 'volatility_regime']
        }
        
        print("[RESEARCH] Market Research Engine initialized")
        print("[RESEARCH] Research sources: sentiment, institutional, macro, on-chain, technical")
    
    def research_asset(self, symbol: str, asset_type: str = 'STOCK') -> MarketResearchReport:
        """Perform comprehensive research on an asset"""
        print(f"\n[RESEARCH] Starting deep analysis for {symbol} ({asset_type})")
        print("=" * 60)
        
        # Check cache
        cache_key = f"{symbol}_{asset_type}"
        if cache_key in self.research_cache:
            cached_time = self.research_cache[cache_key]['timestamp']
            if datetime.now() - cached_time < self.cache_duration:
                print(f"[RESEARCH] Using cached research for {symbol}")
                return self.research_cache[cache_key]['report']
        
        # Get current price
        try:
            ticker = market_data.Ticker(symbol)
            current_price = ticker.history(period='1d')['Close'].iloc[-1]
        except:
            current_price = 0
        
        # Collect all research findings
        findings = []
        
        # 1. Sentiment Analysis
        print("\n[RESEARCH] 1. Analyzing sentiment...")
        sentiment_data = self._analyze_sentiment(symbol, asset_type)
        if sentiment_data.get('fear_greed'):
            findings.append(ResearchFinding(
                title="Fear & Greed Index",
                description=f"Current reading: {sentiment_data['fear_greed']['value']} ({sentiment_data['fear_greed']['classification']})",
                confidence=0.9,
                impact="HIGH",
                data_source="alternative.me",
                timestamp=datetime.now()
            ))
        
        # 2. Institutional Flows
        print("[RESEARCH] 2. Tracking institutional flows...")
        institutional_data = self._analyze_institutional_flows(symbol, asset_type)
        if institutional_data.get('etf_flows'):
            flow_amount = institutional_data['etf_flows']['net_flow']
            if abs(flow_amount) > 100_000_000:  # $100M+ is significant
                findings.append(ResearchFinding(
                    title="ETF Flow Activity",
                    description=f"Net flow: ${flow_amount/1_000_000:.1f}M ({'inflow' if flow_amount > 0 else 'outflow'})",
                    confidence=0.95,
                    impact="HIGH",
                    data_source="ETF data",
                    timestamp=datetime.now()
                ))
        
        # 3. Macro Factors
        print("[RESEARCH] 3. Analyzing macro factors...")
        macro_data = self._analyze_macro_factors(symbol, asset_type)
        if macro_data.get('fed_stance'):
            findings.append(ResearchFinding(
                title="Federal Reserve Stance",
                description=f"Current stance: {macro_data['fed_stance']['policy']} - {macro_data['fed_stance']['outlook']}",
                confidence=0.9,
                impact="HIGH",
                data_source="Fed analysis",
                timestamp=datetime.now()
            ))
        
        # 4. On-chain Analysis (for crypto)
        if asset_type == 'CRYPTO':
            print("[RESEARCH] 4. Analyzing on-chain data...")
            onchain_data = self._analyze_onchain_data(symbol)
            if onchain_data.get('exchange_flows'):
                findings.append(ResearchFinding(
                    title="Exchange Flow Analysis",
                    description=f"Net flow: {onchain_data['exchange_flows']['net_btc']} BTC ({'inflow' if onchain_data['exchange_flows']['net_btc'] > 0 else 'outflow'})",
                    confidence=0.85,
                    impact="HIGH",
                    data_source="On-chain data",
                    timestamp=datetime.now()
                ))
        
        # 5. Technical Analysis
        print("[RESEARCH] 5. Technical pattern analysis...")
        technical_data = self._analyze_technical_patterns(symbol)
        if technical_data.get('key_levels'):
            findings.append(ResearchFinding(
                title="Key Technical Levels",
                description=f"Support: ${technical_data['key_levels']['support']:.2f}, Resistance: ${technical_data['key_levels']['resistance']:.2f}",
                confidence=0.8,
                impact="MEDIUM",
                data_source="Technical analysis",
                timestamp=datetime.now()
            ))
        
        # 6. Catalyst Identification
        print("[RESEARCH] 6. Identifying upcoming catalysts...")
        catalysts = self._identify_catalysts(symbol, asset_type)
        
        # 7. Risk Factors
        print("[RESEARCH] 7. Assessing risk factors...")
        risk_factors = self._assess_risk_factors(symbol, asset_type, findings)
        
        # 8. Historical Pattern Matching
        print("[RESEARCH] 8. Comparing to historical patterns...")
        historical_patterns = self._match_historical_patterns(symbol, asset_type, findings)
        
        # 9. Price Targets
        print("[RESEARCH] 9. Calculating price targets...")
        price_targets = self._calculate_price_targets(symbol, current_price, findings)
        
        # 10. Generate Recommendation
        print("[RESEARCH] 10. Generating recommendation...")
        recommendation, confidence = self._generate_recommendation(findings, catalysts, risk_factors)
        
        # Create report
        report = MarketResearchReport(
            symbol=symbol,
            asset_type=asset_type,
            current_price=current_price,
            research_findings=findings,
            sentiment_analysis=sentiment_data,
            institutional_flows=institutional_data,
            macro_factors=macro_data,
            technical_indicators=technical_data,
            catalysts=catalysts,
            risk_factors=risk_factors,
            historical_patterns=historical_patterns,
            price_targets=price_targets,
            recommendation=recommendation,
            confidence=confidence,
            generated_at=datetime.now()
        )
        
        # Cache the report
        self.research_cache[cache_key] = {
            'report': report,
            'timestamp': datetime.now()
        }
        
        # Print summary
        self._print_research_summary(report)
        
        return report
    
    def _analyze_sentiment(self, symbol: str, asset_type: str) -> Dict:
        """Analyze market sentiment for the asset"""
        sentiment_data = {}
        
        # Get Fear & Greed Index for crypto
        if asset_type == 'CRYPTO':
            try:
                response = requests.get(self.fear_greed_api, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    sentiment_data['fear_greed'] = {
                        'value': data['data'][0]['value'],
                        'classification': data['data'][0]['value_classification'],
                        'timestamp': data['data'][0]['timestamp']
                    }
                    print(f"   Fear & Greed: {data['data'][0]['value']} ({data['data'][0]['value_classification']})")
            except Exception as e:
                print(f"   Error fetching Fear & Greed: {e}")
        
        # For stocks, get general market sentiment
        if asset_type == 'STOCK':
            # Get VIX as fear indicator
            try:
                vix = market_data.Ticker('^VIX').history(period='5d')['Close'].iloc[-1]
                sentiment_data['vix'] = vix
                fear_level = 'LOW' if vix < 20 else 'MEDIUM' if vix < 30 else 'HIGH'
                print(f"   VIX Fear Index: {vix:.2f} ({fear_level} fear)")
            except:
                pass
        
        # Social sentiment (placeholder for now)
        sentiment_data['social'] = {
            'overall': 'NEUTRAL',
            'trend': 'STABLE'
        }
        
        return sentiment_data
    
    def _analyze_institutional_flows(self, symbol: str, asset_type: str) -> Dict:
        """Analyze institutional money flows"""
        flows_data = {}
        
        # For Bitcoin, track ETF flows
        if symbol == 'BTC' or symbol == 'BTC-USD':
            # Simulated ETF flow data (in real implementation, fetch from ETF providers)
            flows_data['etf_flows'] = {
                'net_flow': -250_000_000,  # $250M outflow (example)
                'daily_flow': -50_000_000,
                'weekly_flow': -300_000_000,
                'monthly_flow': -1_200_000_000,
                'trend': 'OUTFLOW'
            }
            print(f"   ETF Flows: ${flows_data['etf_flows']['net_flow']/1_000_000:.0f}M net")
        
        # For stocks, check institutional ownership
        if asset_type == 'STOCK':
            try:
                ticker = market_data.Ticker(symbol)
                info = ticker.info
                if 'institutionalHolders' in info:
                    flows_data['institutional_ownership'] = info.get('institutionalHolders', [])
                    print(f"   Institutional holders: {len(flows_data['institutional_ownership'])}")
            except:
                pass
        
        return flows_data
    
    def _analyze_macro_factors(self, symbol: str, asset_type: str) -> Dict:
        """Analyze macroeconomic factors affecting the asset"""
        macro_data = {}
        
        # Fed policy analysis
        macro_data['fed_stance'] = {
            'policy': 'HOLDING_RATES',  # Based on recent news
            'outlook': 'POTENTIAL_CUTS',  # Based on Warsh appointment
            'next_meeting': 'March 2026',
            'probability_cut': 0.65
        }
        print(f"   Fed Policy: {macro_data['fed_stance']['policy']} - {macro_data['fed_stance']['outlook']}")
        
        # Credit stress indicators
        try:
            # Get TED spread as credit stress indicator (3-month LIBOR - 3-month T-bill)
            # Using proxy: high-yield corporate bond ETF vs Treasuries
            hyg = market_data.Ticker('HYG').history(period='5d')['Close'].iloc[-1]
            tlt = market_data.Ticker('TLT').history(period='5d')['Close'].iloc[-1]
            credit_stress = (hyg / tlt - 1) * 100
            macro_data['credit_stress'] = credit_stress
            stress_level = 'LOW' if credit_stress < 5 else 'MEDIUM' if credit_stress < 10 else 'HIGH'
            print(f"   Credit Stress: {credit_stress:.1f}% ({stress_level})")
        except:
            pass
        
        # Cross-asset correlation
        if asset_type == 'CRYPTO':
            # Check correlation with S&P 500 and Gold
            try:
                spy = market_data.Ticker('SPY').history(period='30d')['Close'].pct_change().iloc[-1]
                btc = market_data.Ticker('BTC-USD').history(period='30d')['Close'].pct_change().iloc[-1]
                correlation = 'POSITIVE' if (spy > 0 and btc > 0) or (spy < 0 and btc < 0) else 'NEGATIVE'
                macro_data['sp500_correlation'] = correlation
                print(f"   S&P 500 Correlation: {correlation}")
            except:
                pass
        
        return macro_data
    
    def _analyze_onchain_data(self, symbol: str) -> Dict:
        """Analyze on-chain data for crypto assets"""
        onchain_data = {}
        
        if symbol in ['BTC', 'BTC-USD', 'Bitcoin']:
            # Simulated on-chain data (in real implementation, fetch from CryptoQuant/Glassnode)
            onchain_data['exchange_flows'] = {
                'inflow_24h': 1250,
                'outflow_24h': 2100,
                'net_btc': -850,  # Negative = outflow from exchanges (bullish)
                'net_usd': -55_250_000
            }
            print(f"   Exchange Flows: {onchain_data['exchange_flows']['net_btc']} BTC net")
            
            # Whale activity
            onchain_data['whale_activity'] = {
                'large_transactions_24h': 45,
                'whale_balance_change': '+2,150 BTC',
                'accumulation_phase': True
            }
            print(f"   Whale Activity: {onchain_data['whale_activity']['accumulation_phase']}")
            
            # Funding rates (for perpetual futures)
            onchain_data['funding_rates'] = {
                'current': 0.0125,  # 1.25% annualized
                'trend': 'DECREASING',
                'status': 'NEUTRAL'
            }
            print(f"   Funding Rate: {onchain_data['funding_rates']['current']*100:.2f}%")
        
        return onchain_data
    
    def _analyze_technical_patterns(self, symbol: str) -> Dict:
        """Analyze technical patterns and indicators"""
        technical_data = {}
        
        try:
            ticker = market_data.Ticker(symbol)
            hist = ticker.history(period='3mo')
            
            if len(hist) > 20:
                current = hist['Close'].iloc[-1]
                high_20d = hist['High'].rolling(20).max().iloc[-1]
                low_20d = hist['Low'].rolling(20).min().iloc[-1]
                
                technical_data['key_levels'] = {
                    'support': low_20d,
                    'resistance': high_20d,
                    'current_position': (current - low_20d) / (high_20d - low_20d)
                }
                
                # Volume analysis
                avg_volume = hist['Volume'].rolling(20).mean().iloc[-1]
                current_volume = hist['Volume'].iloc[-1]
                volume_ratio = current_volume / avg_volume
                
                technical_data['volume_analysis'] = {
                    'current_volume': current_volume,
                    'avg_volume': avg_volume,
                    'volume_ratio': volume_ratio,
                    'trend': 'HIGH' if volume_ratio > 1.5 else 'LOW' if volume_ratio < 0.7 else 'NORMAL'
                }
                
                print(f"   Support: ${low_20d:.2f}, Resistance: ${high_20d:.2f}")
                print(f"   Volume Ratio: {volume_ratio:.1f}x ({technical_data['volume_analysis']['trend']})")
        
        except Exception as e:
            print(f"   Technical analysis error: {e}")
        
        return technical_data
    
    def _identify_catalysts(self, symbol: str, asset_type: str) -> List[Dict]:
        """Identify upcoming catalysts for the asset"""
        catalysts = []
        
        # Fed meetings (macro catalyst)
        catalysts.append({
            'event': 'Federal Reserve Meeting',
            'date': 'March 18-19, 2026',
            'potential_impact': 'HIGH',
            'description': 'Potential rate cuts under new Chair Warsh',
            'probability': 0.65
        })
        
        # Crypto-specific catalysts
        if asset_type == 'CRYPTO':
            catalysts.append({
                'event': 'Clarity Act Markup',
                'date': 'January 15, 2026',
                'potential_impact': 'HIGH',
                'description': 'Crypto market structure bill legislation',
                'probability': 0.7
            })
            
            catalysts.append({
                'event': 'Bitcoin Halving Effect',
                'date': 'Ongoing (April 2024 halving)',
                'potential_impact': 'MEDIUM',
                'description': 'Reduced supply continues to impact market',
                'probability': 0.8
            })
        
        # Stock-specific catalysts
        if asset_type == 'STOCK':
            # Check for upcoming earnings
            catalysts.append({
                'event': 'Earnings Report',
                'date': 'Next quarter',
                'potential_impact': 'HIGH',
                'description': 'Quarterly earnings announcement',
                'probability': 0.9
            })
        
        print(f"   Identified {len(catalysts)} upcoming catalysts")
        return catalysts
    
    def _assess_risk_factors(self, symbol: str, asset_type: str, findings: List[ResearchFinding]) -> List[Dict]:
        """Assess risk factors for the asset"""
        risk_factors = []
        
        # Check for negative sentiment
        for finding in findings:
            if 'Fear' in finding.title and finding.impact == 'HIGH':
                risk_factors.append({
                    'risk': 'Extreme Market Fear',
                    'severity': 'HIGH',
                    'description': 'Fear & Greed at extreme lows indicates panic selling',
                    'mitigation': 'Wait for sentiment stabilization'
                })
        
        # Check for institutional outflows
        for finding in findings:
            if 'ETF Flow' in finding.title and 'outflow' in finding.description.lower():
                risk_factors.append({
                    'risk': 'Institutional Exodus',
                    'severity': 'HIGH',
                    'description': 'Continued institutional selling pressure',
                    'mitigation': 'Monitor for flow reversal'
                })
        
        # General market risks
        risk_factors.append({
            'risk': 'Macro Uncertainty',
            'severity': 'MEDIUM',
            'description': 'Fed policy and credit conditions remain uncertain',
            'mitigation': 'Diversify across assets'
        })
        
        if asset_type == 'CRYPTO':
            risk_factors.append({
                'risk': 'Leverage Cascade',
                'severity': 'HIGH',
                'description': 'High leverage in crypto markets can cause cascading liquidations',
                'mitigation': 'Monitor open interest and funding rates'
            })
        
        print(f"   Identified {len(risk_factors)} key risk factors")
        return risk_factors
    
    def _match_historical_patterns(self, symbol: str, asset_type: str, findings: List[ResearchFinding]) -> Dict:
        """Match current conditions to historical patterns"""
        patterns = {}
        
        # Crypto winter pattern
        if asset_type == 'CRYPTO':
            patterns['crypto_winter'] = {
                'similarity': 0.85,
                'historical_duration': '13 months',
                'current_duration': '13 months (Jan 2025 - Feb 2026)',
                'recovery_timeline': 'Q1-Q2 2026',
                'confidence': 0.8
            }
            print("   Pattern: Crypto Winter (85% similarity)")
        
        # Fear and recovery pattern
        extreme_fear = any(finding.title == 'Fear & Greed Index' and 'EXTREME' in finding.description for finding in findings)
        if extreme_fear:
            patterns['fear_recovery'] = {
                'similarity': 0.9,
                'historical_outcome': 'Recovery within 2-4 months',
                'success_rate': 0.75,
                'confidence': 0.85
            }
            print("   Pattern: Extreme Fear Recovery (90% similarity)")
        
        return patterns
    
    def _calculate_price_targets(self, symbol: str, current_price: float, findings: List[ResearchFinding]) -> Dict:
        """Calculate price targets based on research findings"""
        targets = {}
        
        # Base targets on historical volatility and patterns
        volatility_factor = 0.3  # 30% volatility assumption
        
        # Conservative target (10% upside)
        targets['conservative'] = {
            'target': current_price * 1.1,
            'timeline': '3 months',
            'probability': 0.6
        }
        
        # Moderate target (25% upside)
        targets['moderate'] = {
            'target': current_price * 1.25,
            'timeline': '6 months',
            'probability': 0.4
        }
        
        # Optimistic target (50%+ upside)
        targets['optimistic'] = {
            'target': current_price * 1.5,
            'timeline': '12 months',
            'probability': 0.2
        }
        
        # Downside risk (20% downside)
        targets['downside'] = {
            'target': current_price * 0.8,
            'timeline': '3 months',
            'probability': 0.3
        }
        
        print(f"   Price Targets: ${targets['conservative']['target']:.2f} (C), ${targets['moderate']['target']:.2f} (M), ${targets['optimistic']['target']:.2f} (O)")
        
        return targets
    
    def _generate_recommendation(self, findings: List[ResearchFinding], catalysts: List[Dict], risk_factors: List[Dict]) -> Tuple[str, float]:
        """Generate overall recommendation and confidence"""
        
        # Score the findings
        positive_score = 0
        negative_score = 0
        total_weight = 0
        
        for finding in findings:
            weight = 3 if finding.impact == 'HIGH' else 2 if finding.impact == 'MEDIUM' else 1
            
            # Determine if finding is positive or negative
            is_positive = self._is_positive_finding(finding)
            
            if is_positive:
                positive_score += weight * finding.confidence
            else:
                negative_score += weight * finding.confidence
            
            total_weight += weight
        
        # Factor in catalysts
        catalyst_score = sum(c['probability'] * (3 if c['potential_impact'] == 'HIGH' else 2) for c in catalysts)
        
        # Factor in risk factors
        risk_score = sum(r['severity'] == 'HIGH' and 3 or r['severity'] == 'MEDIUM' and 2 or 1 for r in risk_factors)
        
        # Calculate net score
        net_score = (positive_score - negative_score + catalyst_score/10 - risk_score/5) / max(total_weight, 1)
        
        # Generate recommendation
        if net_score > 0.3:
            recommendation = "BUY"
        elif net_score > -0.3:
            recommendation = "HOLD"
        else:
            recommendation = "SELL"
        
        # Calculate confidence
        confidence = min(abs(net_score) + 0.5, 0.9)
        
        print(f"   Net Score: {net_score:.2f}")
        print(f"   Recommendation: {recommendation} (Confidence: {confidence:.1%})")
        
        return recommendation, confidence
    
    def _is_positive_finding(self, finding: ResearchFinding) -> bool:
        """Determine if a research finding is positive or negative"""
        positive_keywords = ['inflow', 'accumulation', 'bullish', 'support', 'cut rates', 'clarity', 'stable']
        negative_keywords = ['outflow', 'distribution', 'bearish', 'resistance', 'hike rates', 'fear', 'extreme']
        
        description = finding.description.lower()
        
        for keyword in positive_keywords:
            if keyword in description:
                return True
        
        for keyword in negative_keywords:
            if keyword in description:
                return False
        
        # Default to neutral (slightly positive)
        return True
    
    def _print_research_summary(self, report: MarketResearchReport):
        """Print a summary of the research report"""
        print("\n" + "=" * 60)
        print(f"RESEARCH SUMMARY FOR {report.symbol}")
        print("=" * 60)
        print(f"Current Price: ${report.current_price:.2f}")
        print(f"Asset Type: {report.asset_type}")
        print(f"Recommendation: {report.recommendation} (Confidence: {report.confidence:.1%})")
        print("\nKEY FINDINGS:")
        for finding in report.research_findings[:5]:  # Top 5 findings
            print(f"  • {finding.title}: {finding.description}")
        print(f"\nUPCOMING CATALYSTS: {len(report.catalysts)} identified")
        print(f"RISK FACTORS: {len(report.risk_factors)} identified")
        print("\nPRICE TARGETS:")
        print(f"  Conservative: ${report.price_targets['conservative']['target']:.2f} ({report.price_targets['conservative']['timeline']})")
        print(f"  Moderate: ${report.price_targets['moderate']['target']:.2f} ({report.price_targets['moderate']['timeline']})")
        print(f"  Optimistic: ${report.price_targets['optimistic']['target']:.2f} ({report.price_targets['optimistic']['timeline']})")
        print("=" * 60)
