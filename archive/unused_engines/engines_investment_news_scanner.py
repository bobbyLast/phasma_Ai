#!/usr/bin/env python3
"""
Real Investment News Scanner - Detects actual corporate investment announcements
and generates ripple effect trading opportunities from real news articles.
"""

import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class InvestmentNewsScanner:
    """Scans news articles for real corporate investment announcements and generates trading opportunities."""
    
    def __init__(self):
        self.investment_keywords = [
            # Investment language
            'invest', 'investment', 'investing', 'commits', 'commits to', 'pledges', 'pledges to',
            'backs', 'funds', 'financing', 'capital', 'financing', 'funding round',
            
            # Acquisition language
            'acquires', 'acquire', 'acquisition', 'buys', 'buy', 'purchase', 'takes stake',
            'stake in', 'takes', 'merger', 'mergers', 'takeover', 'takeovers',
            
            # Money indicators
            'billion', 'million', '$', 'million', 'bn', 'm', 'billion', 'trillion',
            
            # Infrastructure/expansion
            'expansion', 'build', 'building', 'construction', 'facility', 'facilities',
            'headquarters', 'data center', 'factory', 'manufacturing', 'infrastructure',
            'plant', 'complex', 'campus', 'site', 'location',
            
            # Strategic moves
            'partnership', 'joint venture', 'collaboration', 'alliance', 'strategic',
            'launches', 'unveils', 'announces', 'reveals', 'introduces'
        ]
        
        self.tech_companies = {
            # Tech Giants
            'AMAZON': {'ticker': 'AMZN', 'sector': 'tech_ecommerce'},
            'MICROSOFT': {'ticker': 'MSFT', 'sector': 'tech_cloud'},
            'GOOGLE': {'ticker': 'GOOGL', 'sector': 'tech_ads'},
            'ALPHABET': {'ticker': 'GOOGL', 'sector': 'tech_ads'},
            'APPLE': {'ticker': 'AAPL', 'sector': 'tech_hardware'},
            'META': {'ticker': 'META', 'sector': 'tech_social'},
            'FACEBOOK': {'ticker': 'META', 'sector': 'tech_social'},
            'TESLA': {'ticker': 'TSLA', 'sector': 'tech_ev'},
            'NETFLIX': {'ticker': 'NFLX', 'sector': 'tech_streaming'},
            'INTEL': {'ticker': 'INTC', 'sector': 'tech_semiconductors'},
            
            # Additional Tech Companies
            'NVIDIA': {'ticker': 'NVDA', 'sector': 'tech_semiconductors'},
            'AMD': {'ticker': 'AMD', 'sector': 'tech_semiconductors'},
            'QUALCOMM': {'ticker': 'QCOM', 'sector': 'tech_semiconductors'},
            'ORACLE': {'ticker': 'ORCL', 'sector': 'tech_cloud'},
            'SALESFORCE': {'ticker': 'CRM', 'sector': 'tech_cloud'},
            'ADOBE': {'ticker': 'ADBE', 'sector': 'tech_software'},
            'AUTODESK': {'ticker': 'ADSK', 'sector': 'tech_software'},
            'IBM': {'ticker': 'IBM', 'sector': 'tech_enterprise'},
            'HP': {'ticker': 'HPQ', 'sector': 'tech_hardware'},
            'DELL': {'ticker': 'DELL', 'sector': 'tech_hardware'},
            'CISCO': {'ticker': 'CSCO', 'sector': 'tech_networking'},
            'BROADCOM': {'ticker': 'AVGO', 'sector': 'tech_semiconductors'},
            'TEXAS INSTRUMENTS': {'ticker': 'TXN', 'sector': 'tech_semiconductors'},
            
            # Energy & Industrial
            'EXXON': {'ticker': 'XOM', 'sector': 'energy_oil'},
            'CHEVRON': {'ticker': 'CVX', 'sector': 'energy_oil'},
            'BP': {'ticker': 'BP', 'sector': 'energy_oil'},
            'SHELL': {'ticker': 'SHEL', 'sector': 'energy_oil'},
            'GENERAL ELECTRIC': {'ticker': 'GE', 'sector': 'industrial'},
            'BOEING': {'ticker': 'BA', 'sector': 'industrial'},
            'LOCKHEED': {'ticker': 'LMT', 'sector': 'industrial'},
            'CAT': {'ticker': 'CAT', 'sector': 'industrial'},
            
            # Finance & Banking
            'JPMORGAN': {'ticker': 'JPM', 'sector': 'finance'},
            'BANK OF AMERICA': {'ticker': 'BAC', 'sector': 'finance'},
            'WELLS FARGO': {'ticker': 'WFC', 'sector': 'finance'},
            'GOLDMAN': {'ticker': 'GS', 'sector': 'finance'},
            'BLACKROCK': {'ticker': 'BLK', 'sector': 'finance'},
            
            # Consumer & Retail
            'WALMART': {'ticker': 'WMT', 'sector': 'retail'},
            'TARGET': {'ticker': 'TGT', 'sector': 'retail'},
            'HOME DEPOT': {'ticker': 'HD', 'sector': 'retail'},
            'LOWE': {'ticker': 'LOW', 'sector': 'retail'},
            'COCA COLA': {'ticker': 'KO', 'sector': 'consumer'},
            'PEPSI': {'ticker': 'PEP', 'sector': 'consumer'},
            'PROCTER': {'ticker': 'PG', 'sector': 'consumer'},
            
            # Healthcare
            'JOHNSON': {'ticker': 'JNJ', 'sector': 'healthcare'},
            'PFIZER': {'ticker': 'PFE', 'sector': 'healthcare'},
            'MODERNA': {'ticker': 'MRNA', 'sector': 'biotech'},
            'ABBVIE': {'ticker': 'ABBV', 'sector': 'healthcare'},
            'MERCK': {'ticker': 'MRK', 'sector': 'healthcare'}
        }
        
        self.regions = {
            'INDIA': {'etfs': ['INDA', 'INDY'], 'construction': ['LT', 'SBIN', 'HDFC'], 'local_tech': ['INFY', 'TCS', 'WIT']},
            'EUROPE': {'etfs': ['IEUR', 'EZU'], 'construction': ['SI', 'VOW', 'BAMXF'], 'local_tech': ['SAP', 'ASML', 'NOKIA']},
            'CHINA': {'etfs': ['MCHI', 'FXI'], 'construction': ['600519.SS', '000002.SZ', 'CICHY'], 'local_tech': ['BABA', 'JD', 'BIDU']},
            'JAPAN': {'etfs': ['EWJ', 'DXJ'], 'construction': ['7203.T', '6702.T', '8035.T'], 'local_tech': ['SONY', 'NTDOY', 'TYO']},
            'SOUTHEAST ASIA': {'etfs': ['ASEA', 'EEM'], 'construction': ['BBL', 'VALE', '3767.HK'], 'local_tech': ['0788.HK', 'Z74.SI', 'BREN.SI']},
            'LATIN AMERICA': {'etfs': ['ILF', 'EWZ'], 'construction': ['VALE', 'PBR', 'BSAC'], 'local_tech': ['MELI', 'DESP', 'BBA']},
            'AFRICA': {'etfs': ['AFK', 'EZA'], 'construction': ['BIL', 'SOL', 'NED'], 'local_tech': ['MTN', 'VOD', 'STAN']}
        }
        
        self.investment_threshold = 0.1  # $100M minimum to trigger analysis (catch more investments)
        
    def scan_article_for_investment(self, article: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Scan a news article for corporate investment announcements.
        
        Args:
            article: News article with title, content, source, date
            
        Returns:
            Investment analysis with ripple effect opportunities or None
        """
        title = article.get('title', '').upper()
        content = article.get('content', '').upper()
        text = f"{title} {content}"
        
        # Quick filter for investment-related content
        if not any(keyword in text for keyword in self.investment_keywords):
            return None
        
        # Extract investment details
        investment_analysis = self._extract_investment_details(text, article)
        
        if investment_analysis and investment_analysis['has_investment']:
            logger.info(f"💰 INVESTMENT DETECTED: {investment_analysis['investing_company']['ticker']} investing ${investment_analysis['investment_amount']}B in {investment_analysis['target_region']}")
            return investment_analysis
        
        return None
    
    def _extract_investment_details(self, text: str, article: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract investment details and strategic motivations from article text."""
        
        # Find investing company
        investing_company = None
        for company_name, company_data in self.tech_companies.items():
            if company_name in text:
                investing_company = company_data
                break
        
        if not investing_company:
            return None
        
        # Extract investment amount
        amount_patterns = [
            r'\$(\d+(?:\.\d+)?)\s*B',
            r'\$(\d+(?:\.\d+)?)\s*BILLION',
            r'(\d+(?:\.\d+)?)\s*BILLION\s*INVEST',
            r'(\d+(?:\.\d+)?)\s*BILLION\s*INVESTMENT',
            r'(\d+(?:\.\d+)?)\s*BILLION\s*COMMITMENT',
            r'(\d+(?:\.\d+)?)\s*BILLION\s*EXPANSION'
        ]
        
        investment_amount = 0
        for pattern in amount_patterns:
            match = re.search(pattern, text)
            if match:
                investment_amount = float(match.group(1))
                break
        
        if investment_amount < self.investment_threshold:
            return None
        
        # Detect target region
        target_region = None
        for region_name in self.regions.keys():
            if region_name in text:
                target_region = region_name
                break
        
        if not target_region:
            return None
        
        # DEEP STRATEGIC ANALYSIS - WHY THIS INVESTMENT?
        strategic_analysis = self._analyze_strategic_motivations(text, investing_company, target_region, investment_amount)
        
        # Generate ripple effect opportunities
        result = {
            'has_investment': True,
            'investing_company': investing_company,
            'investment_amount': investment_amount,
            'target_region': target_region,
            'source_article': {
                'title': article.get('title', ''),
                'source': article.get('source', ''),
                'date': article.get('date', ''),
                'url': article.get('url', '')
            },
            'ripple_effect_opportunities': [],
            'investment_thesis': '',
            'strategic_analysis': strategic_analysis,  # NEW: Deep WHY analysis
            'impact_strength': min(0.9, 0.5 + (investment_amount / 50)),
            'market_category': 'corporate_investment',
            'confidence_in_impact': 0.85,  # High confidence for real announcements
            'investment_timing_analysis': {
                'timing_recommendation': 'IMMEDIATE_ENTRY',
                'investment_thesis': f"Real {investment_amount}B investment by {investing_company['ticker']} in {target_region} creates immediate ripple effect opportunities"
            }
        }
        
        # Generate ripple effect opportunities
        region_data = self.regions[target_region]
        ripple_opportunities = []
        
        # 1. Construction/Infrastructure stocks
        construction_stocks = region_data['construction']
        ripple_opportunities.extend([
            {
                'ticker': ticker,
                'reason': f'Infrastructure construction for {investment_amount}B {target_region} investment',
                'timing': 'GOOD_TIMING',
                'category': 'construction_infrastructure',
                'expected_impact': 'HIGH' if investment_amount >= 20 else 'MEDIUM'
            } for ticker in construction_stocks[:3]
        ])
        
        # 2. Regional ETFs
        regional_etfs = region_data['etfs']
        ripple_opportunities.extend([
            {
                'ticker': etf,
                'reason': f'Regional ETF benefiting from {investment_amount}B investment inflow',
                'timing': 'GOOD_TIMING',
                'category': 'regional_etf',
                'expected_impact': 'MEDIUM'
            } for etf in regional_etfs[:2]
        ])
        
        # 3. Local tech partners
        local_tech = region_data['local_tech']
        ripple_opportunities.extend([
            {
                'ticker': ticker,
                'reason': f'Local tech partner/supplier for {investing_company["ticker"]} {target_region} expansion',
                'timing': 'SUPER_EARLY' if investment_amount >= 30 else 'GOOD_TIMING',
                'category': 'local_tech_partner',
                'expected_impact': 'HIGH' if investment_amount >= 25 else 'MEDIUM'
            } for ticker in local_tech[:3]
        ])
        
        # 4. Follow-the-leader opportunities
        other_tech = [data for name, data in self.tech_companies.items() if name != investing_company['ticker']]
        ripple_opportunities.extend([
            {
                'ticker': company['ticker'],
                'reason': f'Likely follow-on investment to {target_region} after {investing_company["ticker"]} lead',
                'timing': 'GOOD_TIMING',
                'category': 'follow_the_leader',
                'expected_impact': 'MEDIUM'
            } for company in other_tech[:3]
        ])
        
        result['ripple_effect_opportunities'] = ripple_opportunities
        result['affected_assets'] = [opp['ticker'] for opp in ripple_opportunities]
        result['bullish_assets'] = [opp['ticker'] for opp in ripple_opportunities]
        result['investment_thesis'] = f"Ride the coattails of real {investment_amount}B {target_region} investment through construction, regional ETFs, and follow-the-leader tech plays"
        
        return result
    
    def _analyze_strategic_motivations(self, text: str, investing_company: Dict[str, Any], 
                                     target_region: str, investment_amount: float) -> Dict[str, Any]:
        """Deep analysis of WHY this specific investment is being made.
        
        Args:
            text: Article content to analyze
            investing_company: Company making the investment
            target_region: Region receiving the investment
            investment_amount: Size of investment in billions
            
        Returns:
            Strategic analysis with motivations and comparative insights
        """
        
        # Knowledge base of regional advantages and strategic factors
        regional_advantages = {
            'INDIA': {
                'cost_advantages': ['40% lower engineering costs', '60% lower construction costs', '70% lower operational costs'],
                'market_opportunities': ['300M new internet users', 'fastest growing digital market', 'middle class expansion'],
                'regulatory_factors': ['data localization laws', 'government incentives', 'tax breaks for foreign investment'],
                'talent_factors': ['largest English-speaking tech workforce', 'STEM graduates', 'software engineering talent'],
                'competitive_factors': ['counter China dominance', 'diversify supply chain', 'local manufacturing requirements']
            },
            'EUROPE': {
                'cost_advantages': ['strong data privacy laws', 'stable regulatory environment', 'EU market access'],
                'market_opportunities': ['450M affluent consumers', 'GDPR compliance hub', 'AI research leadership'],
                'regulatory_factors': ['Digital Services Act', 'AI regulations requiring local presence', 'green technology incentives'],
                'talent_factors': ['world-class engineering schools', 'multilingual workforce', 'R&D expertise'],
                'competitive_factors': ['avoid US-China tensions', 'serve EU clients locally', 'regulatory compliance']
            },
            'CHINA': {
                'cost_advantages': ['massive scale economies', 'government subsidies', 'established supply chains'],
                'market_opportunities': ['1.4B consumers', 'digital payments dominance', 'smart city initiatives'],
                'regulatory_factors': ['government partnerships', 'special economic zones', 'infrastructure support'],
                'talent_factors': ['largest STEM workforce', 'manufacturing expertise', 'rapid innovation'],
                'competitive_factors': ['access domestic market', 'government requirements', 'local competitor landscape']
            }
        }
        
        # Industry-specific investment motivations
        industry_motivations = {
            'tech_cloud': {
                'drivers': ['data localization requirements', 'latency optimization', 'sovereign cloud demand', 'compliance needs'],
                'infrastructure_needs': ['data centers', 'fiber networks', 'power infrastructure', 'cooling systems']
            },
            'tech_ecommerce': {
                'drivers': ['last-mile delivery', 'warehousing', 'logistics networks', 'local manufacturing'],
                'infrastructure_needs': ['fulfillment centers', 'delivery networks', 'supply chain automation']
            },
            'tech_hardware': {
                'drivers': ['manufacturing capacity', 'supply chain diversification', 'cost optimization', 'component sourcing'],
                'infrastructure_needs': ['factories', 'assembly plants', 'component facilities']
            }
        }
        
        # Analyze text for specific motivations
        detected_motivations = []
        
        # Cost-related signals
        cost_keywords = ['CHEAPER', 'LOWER COST', 'COST-EFFECTIVE', 'SAVINGS', 'AFFORDABLE', 'BUDGET', 'ECONOMIC', 'LOWER COSTS']
        if any(keyword in text for keyword in cost_keywords):
            detected_motivations.append('COST_OPTIMIZATION')
        
        # Market opportunity signals
        market_keywords = ['MARKET GROWTH', 'EXPANDING MARKET', 'NEW CUSTOMERS', 'CONSUMER BASE', 'DEMAND', 'OPPORTUNITY', 'GROWING MARKET', 'MARKET OPPORTUNITY']
        if any(keyword in text for keyword in market_keywords):
            detected_motivations.append('MARKET_EXPANSION')
        
        # Regulatory compliance signals
        regulatory_keywords = ['COMPLIANCE', 'REGULATION', 'LAW', 'POLICY', 'GOVERNMENT', 'LOCALIZATION', 'DATA RESIDENCY', 'DATA LOCALIZATION', 'GDPR']
        if any(keyword in text for keyword in regulatory_keywords):
            detected_motivations.append('REGULATORY_COMPLIANCE')
        
        # Talent/Workforce signals
        talent_keywords = ['TALENT', 'ENGINEERS', 'WORKFORCE', 'SKILLS', 'EXPERTISE', 'GRADUATES', 'DEVELOPERS', 'TALENT POOL']
        if any(keyword in text for keyword in talent_keywords):
            detected_motivations.append('TALENT_ACQUISITION')
        
        # Competitive pressure signals
        competitive_keywords = ['COMPETITION', 'RIVAL', 'COMPETE', 'ADVANTAGE', 'MARKET SHARE', 'LEADERSHIP', 'COMPETITIVE', 'DOMINANCE']
        if any(keyword in text for keyword in competitive_keywords):
            detected_motivations.append('COMPETITIVE_POSITIONING')
        
        # Government partnership signals
        government_keywords = ['GOVERNMENT', 'PARTNERSHIP', 'INCENTIVE', 'SUBSIDY', 'TAX BREAK', 'POLICY SUPPORT', 'TAX INCENTIVES']
        if any(keyword in text for keyword in government_keywords):
            detected_motivations.append('GOVERNMENT_PARTNERSHIP')
        
        # Build strategic analysis
        region_data = regional_advantages.get(target_region, {})
        industry_data = industry_motivations.get(investing_company.get('sector', ''), {})
        
        # Primary strategic driver (most likely motivation)
        primary_driver = 'MARKET_EXPANSION'  # Default
        if 'REGULATORY_COMPLIANCE' in detected_motivations:
            primary_driver = 'REGULATORY_COMPLIANCE'
        elif 'COST_OPTIMIZATION' in detected_motivations:
            primary_driver = 'COST_OPTIMIZATION'
        elif 'COMPETITIVE_POSITIONING' in detected_motivations:
            primary_driver = 'COMPETITIVE_POSITIONING'
        
        # Comparative analysis - why this region vs alternatives
        comparative_insights = []
        if target_region == 'INDIA':
            comparative_insights.extend([
                "India offers 40-60% lower costs vs US/Europe for tech infrastructure",
                "Data localization laws require Indian data centers for Indian users",
                "300M+ new internet users represent massive untapped market",
                "Government 'Make in India' incentives provide tax benefits",
                "English-speaking workforce enables easier integration vs China"
            ])
        elif target_region == 'EUROPE':
            comparative_insights.extend([
                "GDPR and EU regulations require local data processing",
                "450M affluent consumers with high purchasing power",
                "Stable regulatory environment vs US-China tensions",
                "AI research leadership and technical talent pool",
                "Access to entire EU single market through local presence"
            ])
        elif target_region == 'CHINA':
            comparative_insights.extend([
                "Access to 1.4B consumer market requires local presence",
                "Government partnerships and subsidies reduce effective costs",
                "Established supply chain ecosystem for manufacturing",
                "Regulatory requirements favor local joint ventures",
                "Scale economies impossible to replicate elsewhere"
            ])
        
        # Investment validation signals
        validation_signals = []
        if investment_amount >= 20:
            validation_signals.append("Large investment ($20B+) indicates strong strategic commitment")
        if len(detected_motivations) >= 3:
            validation_signals.append("Multiple strategic drivers increase investment success probability")
        if primary_driver in ['REGULATORY_COMPLIANCE', 'MARKET_EXPANSION']:
            validation_signals.append("Non-discretionary drivers reduce investment risk")
        
        # Risk factors
        risk_factors = []
        if target_region in ['CHINA', 'INDIA']:
            risk_factors.append("Geopolitical tensions could impact investment timeline")
        if investment_amount >= 30:
            risk_factors.append("Large scale investments face execution challenges")
        if primary_driver == 'COST_OPTIMIZATION':
            risk_factors.append("Cost advantages may erode over time with competition")
        
        strategic_analysis = {
            'primary_strategic_driver': primary_driver,
            'detected_motivations': detected_motivations,
            'comparative_insights': comparative_insights,
            'regional_advantages': region_data,
            'industry_specific_drivers': industry_data.get('drivers', []),
            'validation_signals': validation_signals,
            'risk_factors': risk_factors,
            'strategic_confidence': min(0.95, 0.7 + (len(detected_motivations) * 0.1) + (len(validation_signals) * 0.05)),
            'investment_thesis': f"{investing_company['ticker']} investing ${investment_amount}B in {target_region} driven by {primary_driver.replace('_', ' ').title()} with {len(detected_motivations)} strategic factors"
        }
        
        return strategic_analysis
    
    def generate_trading_signals(self, investment_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate trading signals from investment analysis.
        
        Args:
            investment_analysis: Result from scan_article_for_investment
            
        Returns:
            List of trading signals with position sizing and timing
        """
        if not investment_analysis or not investment_analysis.get('has_investment'):
            return []
        
        ripple_opps = investment_analysis.get('ripple_effect_opportunities', [])
        signals = []
        
        for opp in ripple_opps:
            # Position size based on impact and category
            base_position = 1500
            
            if opp['expected_impact'] == 'HIGH':
                position_size = base_position * 1.5
            elif opp['expected_impact'] == 'MEDIUM':
                position_size = base_position
            else:
                position_size = base_position * 0.75
            
            # Adjust for timing
            if opp['timing'] == 'SUPER_EARLY':
                position_size *= 1.2  # Higher allocation for super early opportunities
            
            signal = {
                'symbol': opp['ticker'],
                'action': 'BUY_CALL',
                'confidence': investment_analysis['confidence_in_impact'],
                'position_size': int(position_size),
                'rationale': f"REAL INVESTMENT CATALYST: {opp['reason']}",
                'thesis': f"{opp['reason']} | {opp['category'].replace('_', ' ').title()}",
                'source': 'investment_news_scanner',
                'source_article': investment_analysis.get('source_article', {}),
                'timing_recommendation': opp['timing'],
                'expected_impact': opp['expected_impact'],
                'catalyst_type': investment_analysis['market_category'],
                'investment_details': {
                    'investing_company': investment_analysis['investing_company']['ticker'],
                    'amount': investment_analysis['investment_amount'],
                    'region': investment_analysis['target_region']
                },
                'days_to_expiry': 90,  # Medium-term investment plays
                'catalyst_score': investment_analysis['confidence_in_impact'] * investment_analysis['impact_strength']
            }
            
            signals.append(signal)
        
        return signals
    
    def scan_multiple_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Scan multiple articles for investment opportunities.
        
        Args:
            articles: List of news articles
            
        Returns:
            List of investment analyses found
        """
        investments_found = []
        
        for article in articles:
            investment = self.scan_article_for_investment(article)
            if investment:
                investments_found.append(investment)
        
        logger.info(f"📊 SCANNED {len(articles)} articles, found {len(investments_found)} investment opportunities")
        return investments_found

# Test function
def test_investment_scanner():
    """Test the investment news scanner with sample articles."""
    
    scanner = InvestmentNewsScanner()
    
    # Sample articles with rich strategic content for deep WHY analysis
    test_articles = [
        {
            'title': 'Amazon to invest $35 billion in India to create 1 million jobs by 2030',
            'content': 'Amazon announced today a massive $35 billion investment in India, citing cost-effective expansion opportunities and compliance with data localization laws. The investment includes data centers, warehouses, and logistics infrastructure to tap into India\'s growing market of 300 million new internet users. CEO Jeff Bezos emphasized that India offers 60% lower construction costs and a large English-speaking engineering talent pool compared to the US. The move is also seen as a competitive response to challenge Chinese dominance in the region. Government partnerships under the "Make in India" initiative provide significant tax incentives for foreign investment.',
            'source': 'TechCrunch',
            'date': '2023-12-01',
            'url': 'https://techcrunch.com/amazon-india-investment'
        },
        {
            'title': 'Microsoft commits $17.5 billion for India data center expansion',
            'content': 'Microsoft is investing $17.5 billion to expand its Azure cloud infrastructure in India, driven primarily by regulatory compliance requirements. India\'s data residency laws require that Indian user data be stored within the country, making local data centers essential for continued operations. The investment is also cost-effective, with operational costs 70% lower than in the United States. Microsoft CEO Satya Nadella highlighted the massive market opportunity with India\'s digital transformation creating unprecedented demand for cloud services. The expansion will tap into India\'s vast pool of software engineering talent while avoiding escalating US-China trade tensions.',
            'source': 'Reuters',
            'date': '2023-11-15',
            'url': 'https://reuters.com/microsoft-india-expansion'
        },
        {
            'title': 'Google announces $25 billion investment in European AI research centers',
            'content': 'Alphabet subsidiary Google will invest $25 billion to establish AI research centers across Europe, primarily to ensure compliance with GDPR and upcoming EU AI regulations. The investment in Germany, France, and the UK provides access to world-class technical talent and stable regulatory environment. Google executives emphasized that serving the 450 million affluent EU consumers requires local presence to meet data privacy requirements. The move also positions Google competitively against rivals while avoiding US-China geopolitical tensions. European governments are offering green technology incentives for AI infrastructure development.',
            'source': 'Bloomberg',
            'date': '2023-10-20',
            'url': 'https://bloomberg.com/google-europe-ai'
        }
    ]
    
    print("🏢 TESTING REAL INVESTMENT NEWS SCANNER")
    print("=" * 60)
    
    for i, article in enumerate(test_articles, 1):
        print(f"\n📰 ARTICLE {i}: {article['title'][:60]}...")
        
        investment = scanner.scan_article_for_investment(article)
        
        if investment:
            print(f"   ✅ INVESTMENT DETECTED!")
            print(f"      🏢 Company: {investment['investing_company']['ticker']}")
            print(f"      💰 Amount: ${investment['investment_amount']}B")
            print(f"      🌍 Region: {investment['target_region']}")
            print(f"      📈 Impact Strength: {investment['impact_strength']:.1%}")
            
            # Show strategic analysis
            strategic = investment.get('strategic_analysis', {})
            if strategic:
                print(f"      🧠 STRATEGIC ANALYSIS:")
                print(f"         🎯 Primary Driver: {strategic.get('primary_strategic_driver', 'Unknown').replace('_', ' ').title()}")
                print(f"         📋 Detected Motivations: {len(strategic.get('detected_motivations', []))}")
                print(f"         🔍 Comparative Insights: {len(strategic.get('comparative_insights', []))} factors")
                print(f"         ✅ Validation Signals: {len(strategic.get('validation_signals', []))}")
                print(f"         ⚠️  Risk Factors: {len(strategic.get('risk_factors', []))}")
                print(f"         📊 Strategic Confidence: {strategic.get('strategic_confidence', 0):.1%}")
                
                print(f"         💡 WHY THIS INVESTMENT:")
                for insight in strategic.get('comparative_insights', [])[:3]:
                    print(f"            • {insight}")
            
            # Generate trading signals
            signals = scanner.generate_trading_signals(investment)
            print(f"      📊 Trading Signals: {len(signals)}")
            
            print(f"   🎯 TOP OPPORTUNITIES:")
            for j, signal in enumerate(signals[:5], 1):
                print(f"      {j}. {signal['symbol']}: {signal['action']}")
                print(f"         💡 Thesis: {signal['thesis'][:50]}...")
                print(f"         📊 Position: ${signal['position_size']:,}")
                print(f"         ⏰ Timing: {signal['timing_recommendation']}")
                print(f"         🎯 Impact: {signal['expected_impact']}")
        else:
            print(f"   ❌ NO INVESTMENT DETECTED")
        
        print("-" * 50)
    
    print(f"\n🎉 INVESTMENT SCANNER TEST COMPLETE")
    return True

if __name__ == "__main__":
    test_investment_scanner()
