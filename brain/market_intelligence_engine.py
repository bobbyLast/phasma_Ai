"""
Market Intelligence Engine - Universal contextual analysis for all trading decisions
Provides deep investigation of market movements, fundamental analysis, and predictive intelligence
"""

import yfinance as market_data
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import numpy as np
import requests
import json

class MarketIntelligenceEngine:
    """
    Universal market intelligence engine that provides deep contextual analysis
    for both bullish and bearish trading opportunities
    """
    
    def __init__(self, config=None):
        """Initialize market intelligence engine"""
        self.config = config or {}
        
        # Initialize caches and settings
        self.analysis_cache = {}
        self.cache_expiry = 1800  # 30 minutes cache
        
        # News API for market context analysis
        self.news_api_url = "https://saurav.tech/NewsAPI/top-headlines/category/business/us.json"
        
        # Sector mappings for analysis
        self.sector_etfs = {
            'AI_TECH': ['QQQ', 'XLK', 'SOXX', 'BOTZ', 'NVDA', 'AMD'],
            'CRYPTO': ['BTC-USD', 'ETH-USD', 'MARA', 'RIOT', 'COIN'],
            'AR_TECH': ['ARKK', 'ARKF', 'ARKG', 'ARKW'],
            'BIOTECH': ['XBI', 'IBB', 'ARKG'],
            'EV': ['TSLA', 'RIVN', 'LCID', 'NIO'],
            'FINTECH': ['PYPL', 'SQ', 'COIN', 'ARKF'],
            'SEMICONDUCTOR': ['SOXX', 'SMH', 'NVDA', 'AMD', 'INTC'],
            'ENERGY': ['XLE', 'CVX', 'XOM', 'COP'],
            'FINANCIAL': ['XLF', 'JPM', 'BAC', 'WFC'],
            'CONSUMER': ['XLY', 'AMZN', 'TSLA', 'HD'],
            'HEALTHCARE': ['XLV', 'JNJ', 'PFE', 'UNH']
        }
        
        print("[MARKET INTEL] Market Intelligence Engine initialized successfully")
    
    def analyze_symbol_intelligence(self, symbol: str, signal_type: str = 'BULLISH') -> Dict:
        """
        Comprehensive intelligence analysis for any symbol
        """
        print(f"[MARKET INTEL] 🧠 Analyzing {symbol} for {signal_type} opportunity...")
        
        # Check cache first
        cache_key = f"{symbol}_{signal_type}"
        if cache_key in self.analysis_cache:
            cached_time = datetime.fromisoformat(self.analysis_cache[cache_key].get('timestamp', '1970-01-01'))
            if (datetime.now() - cached_time).seconds < self.cache_expiry:
                print(f"[MARKET INTEL] Using cached analysis for {symbol}")
                return self.analysis_cache[cache_key]
        
        intelligence = {
            'symbol': symbol,
            'signal_type': signal_type,
            'analysis_timestamp': datetime.now().isoformat(),
            'sector_context': {},
            'news_triggers': [],
            'fundamental_analysis': {},
            'momentum_analysis': {},
            'market_psychology': {},
            'predictive_intelligence': {},
            'risk_factors': [],
            'opportunity_strength': 0
        }
        
        # 1. Determine sector context
        sector_context = self._analyze_sector_context(symbol)
        intelligence['sector_context'] = sector_context
        
        # 2. News analysis - What's driving this movement?
        news_triggers = self._analyze_news_catalysts(symbol, signal_type)
        intelligence['news_triggers'] = news_triggers
        
        # 3. Fundamental analysis - Understand real value
        fundamental_analysis = self._analyze_fundamentals(symbol)
        intelligence['fundamental_analysis'] = fundamental_analysis
        
        # 4. Momentum and technical analysis
        momentum_analysis = self._analyze_momentum_patterns(symbol, signal_type)
        intelligence['momentum_analysis'] = momentum_analysis
        
        # 5. Market psychology and sentiment
        psychology = self._analyze_market_psychology(symbol, signal_type)
        intelligence['market_psychology'] = psychology
        
        # 6. Predictive intelligence
        predictive_intel = self._generate_predictive_intelligence(intelligence)
        intelligence['predictive_intelligence'] = predictive_intel
        
        # 7. Risk factors
        risk_factors = self._identify_risk_factors(intelligence)
        intelligence['risk_factors'] = risk_factors
        
        # 8. Overall opportunity strength
        opportunity_strength = self._calculate_opportunity_strength(intelligence)
        intelligence['opportunity_strength'] = opportunity_strength
        
        # Cache the analysis
        self.analysis_cache[cache_key] = intelligence
        
        print(f"[MARKET INTEL] ✅ Analysis complete for {symbol} | Strength: {opportunity_strength:.1f}/100")
        
        return intelligence
    
    def _analyze_sector_context(self, symbol: str) -> Dict:
        """Analyze sector context and positioning"""
        sector_context = {
            'primary_sector': None,
            'sector_performance': {},
            'sector_ranking': {},
            'correlation_analysis': {}
        }
        
        try:
            # Determine which sector this symbol belongs to
            for sector_name, symbols in self.sector_etfs.items():
                if symbol in symbols:
                    sector_context['primary_sector'] = sector_name
                    break
            
            if sector_context['primary_sector']:
                # Analyze sector performance
                sector_symbols = self.sector_etfs[sector_context['primary_sector']]
                sector_performance = {}
                
                for sector_symbol in sector_symbols[:5]:  # Top 5 symbols
                    try:
                        ticker = market_data.Ticker(sector_symbol)
                        hist = ticker.history(period="5d")
                        if len(hist) >= 2:
                            performance = (hist['Close'].iloc[-1] / hist['Close'].iloc[0] - 1) * 100
                            sector_performance[sector_symbol] = performance
                    except:
                        continue
                
                # Rank symbol within sector
                if symbol in sector_performance:
                    sorted_performance = sorted(sector_performance.items(), key=lambda x: x[1])
                    rank = [s[0] for s in sorted_performance].index(symbol) + 1
                    total = len(sorted_performance)
                    sector_context['sector_ranking'] = {
                        'rank': rank,
                        'total': total,
                        'percentile': (total - rank) / total * 100
                    }
                
                sector_context['sector_performance'] = sector_performance
                
        except Exception as e:
            print(f"[MARKET INTEL] Error analyzing sector context for {symbol}: {e}")
        
        return sector_context
    
    def _analyze_news_catalysts(self, symbol: str, signal_type: str) -> List[Dict]:
        """Analyze news catalysts driving the signal"""
        catalysts = []
        
        try:
            response = requests.get(self.news_api_url, timeout=10)
            if response.status_code == 200:
                articles = response.json().get('articles', [])
                
                # Symbol-specific keywords
                symbol_keywords = {
                    'NVDA': ['NVIDIA', 'chip', 'AI', 'GPU', 'semiconductor'],
                    'TSLA': ['Tesla', 'EV', 'electric vehicle', 'Musk', 'battery'],
                    'BTC-USD': ['bitcoin', 'crypto', 'BTC', 'blockchain', 'mining'],
                    'ARKK': ['ARKK', 'Cathie Wood', 'innovation', 'disruptive'],
                    'SPY': ['S&P', 'market', 'stocks', 'index', 'trading'],
                    'QQQ': ['NASDAQ', 'tech', 'growth', 'technology']
                }
                
                keywords = symbol_keywords.get(symbol, [symbol.lower()])
                
                # Signal-specific keywords
                if signal_type == 'BULLISH':
                    signal_keywords = ['rally', 'surge', 'jump', 'gain', 'bull', 'breakthrough', 'beat', 'strong']
                else:
                    signal_keywords = ['crash', 'drop', 'fall', 'decline', 'bear', 'concern', 'warning', 'bubble']
                
                for article in articles[:15]:
                    title = article.get('title', '').lower()
                    description = article.get('description', '').lower()
                    
                    # Check for symbol and signal keywords
                    symbol_match = any(keyword in title or keyword in description for keyword in keywords)
                    signal_match = any(keyword in title or keyword in description for keyword in signal_keywords)
                    
                    if symbol_match and signal_match:
                        catalysts.append({
                            'title': article.get('title', ''),
                            'description': article.get('description', ''),
                            'relevance': 'HIGH' if symbol in title else 'MEDIUM',
                            'sentiment': signal_type,
                            'publishedAt': article.get('publishedAt', '')
                        })
                
        except Exception as e:
            print(f"[MARKET INTEL] Error analyzing news for {symbol}: {e}")
        
        return catalysts[:3]  # Top 3 catalysts
    
    def _analyze_fundamentals(self, symbol: str) -> Dict:
        """Analyze fundamental metrics and valuation"""
        fundamentals = {
            'valuation_metrics': {},
            'financial_health': {},
            'growth_indicators': {},
            'valuation_assessment': 'NEUTRAL'
        }
        
        try:
            ticker = market_data.Ticker(symbol)
            info = ticker.info
            
            # Valuation metrics
            pe_ratio = info.get('trailingPE', 0)
            pb_ratio = info.get('priceToBook', 0)
            ps_ratio = info.get('priceToSales', 0)
            market_cap = info.get('marketCap', 0)
            
            fundamentals['valuation_metrics'] = {
                'pe_ratio': pe_ratio,
                'pb_ratio': pb_ratio,
                'ps_ratio': ps_ratio,
                'market_cap': market_cap
            }
            
            # Valuation assessment
            if pe_ratio > 0:
                if pe_ratio < 15:
                    valuation = 'UNDERVERLUED'
                elif pe_ratio > 50:
                    valuation = 'OVERVALUED'
                else:
                    valuation = 'FAIR'
                fundamentals['valuation_assessment'] = valuation
            
            # Financial health indicators
            debt_to_equity = info.get('debtToEquity', 0)
            roe = info.get('returnOnEquity', 0)
            profit_margin = info.get('profitMargins', 0)
            
            fundamentals['financial_health'] = {
                'debt_to_equity': debt_to_equity,
                'return_on_equity': roe,
                'profit_margin': profit_margin
            }
            
            # Growth indicators
            revenue_growth = info.get('revenueGrowth', 0)
            earnings_growth = info.get('earningsGrowth', 0)
            
            fundamentals['growth_indicators'] = {
                'revenue_growth': revenue_growth,
                'earnings_growth': earnings_growth
            }
            
        except Exception as e:
            print(f"[MARKET INTEL] Error analyzing fundamentals for {symbol}: {e}")
        
        return fundamentals
    
    def _analyze_momentum_patterns(self, symbol: str, signal_type: str) -> Dict:
        """Analyze momentum patterns and technical indicators"""
        momentum = {
            'price_momentum': {},
            'volume_analysis': {},
            'trend_strength': 0,
            'momentum_assessment': 'NEUTRAL'
        }
        
        try:
            ticker = market_data.Ticker(symbol)
            hist = ticker.history(period="3mo")
            
            if len(hist) > 20:
                # Price momentum analysis
                current_price = hist['Close'].iloc[-1]
                
                # Various timeframes
                momentum_5d = (current_price / hist['Close'].iloc[-5] - 1) * 100
                momentum_10d = (current_price / hist['Close'].iloc[-10] - 1) * 100
                momentum_30d = (current_price / hist['Close'].iloc[-30] - 1) * 100
                
                momentum['price_momentum'] = {
                    'momentum_5d': momentum_5d,
                    'momentum_10d': momentum_10d,
                    'momentum_30d': momentum_30d
                }
                
                # Volume analysis
                if 'Volume' in hist.columns:
                    recent_volume = hist['Volume'].iloc[-5:].mean()
                    avg_volume = hist['Volume'].iloc[:-5].mean()
                    volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 1
                    
                    momentum['volume_analysis'] = {
                        'volume_ratio': volume_ratio,
                        'volume_trend': 'INCREASING' if volume_ratio > 1.2 else 'NORMAL'
                    }
                
                # Trend strength calculation
                trend_strength = 0
                if signal_type == 'BULLISH':
                    if momentum_5d > 2 and momentum_10d > 5 and momentum_30d > 10:
                        trend_strength = min(100, momentum_30d / 2)
                else:  # BEARISH
                    if momentum_5d < -2 and momentum_10d < -5 and momentum_30d < -10:
                        trend_strength = min(100, abs(momentum_30d) / 2)
                
                momentum['trend_strength'] = trend_strength
                
                # Momentum assessment
                if trend_strength > 70:
                    momentum['momentum_assessment'] = 'STRONG'
                elif trend_strength > 40:
                    momentum['momentum_assessment'] = 'MODERATE'
                elif trend_strength > 20:
                    momentum['momentum_assessment'] = 'WEAK'
                else:
                    momentum['momentum_assessment'] = 'NEUTRAL'
            
        except Exception as e:
            print(f"[MARKET INTEL] Error analyzing momentum for {symbol}: {e}")
        
        return momentum
    
    def _analyze_market_psychology(self, symbol: str, signal_type: str) -> Dict:
        """Analyze market psychology and sentiment factors"""
        psychology = {
            'sentiment_indicators': {},
            'psychology_factors': [],
            'crowd_behavior': 'NEUTRAL'
        }
        
        try:
            # Analyze recent price action for psychology clues
            ticker = market_data.Ticker(symbol)
            hist = ticker.history(period="1mo")
            
            if len(hist) > 10:
                # Volatility analysis (fear/greed indicator)
                daily_returns = hist['Close'].pct_change().dropna()
                volatility = daily_returns.std() * np.sqrt(252)  # Annualized volatility
                
                psychology['sentiment_indicators'] = {
                    'volatility': volatility,
                    'volatility_level': 'HIGH' if volatility > 0.4 else 'NORMAL'
                }
                
                # Price patterns
                recent_high = hist['High'].iloc[-10:].max()
                recent_low = hist['Low'].iloc[-10:].min()
                current_price = hist['Close'].iloc[-1]
                
                # Position within range
                if recent_high > recent_low:
                    position_in_range = (current_price - recent_low) / (recent_high - recent_low)
                    
                    if position_in_range > 0.8:
                        psychology['psychology_factors'].append('Near recent highs - potential resistance')
                    elif position_in_range < 0.2:
                        psychology['psychology_factors'].append('Near recent lows - potential support')
                
                # Gap analysis (psychology indicator)
                gaps = []
                for i in range(1, len(hist)):
                    if hist['Low'].iloc[i] > hist['High'].iloc[i-1]:
                        gaps.append('GAP_UP')
                    elif hist['High'].iloc[i] < hist['Low'].iloc[i-1]:
                        gaps.append('GAP_DOWN')
                
                if gaps:
                    gap_frequency = len(gaps) / len(hist)
                    if gap_frequency > 0.1:
                        psychology['psychology_factors'].append('High gap activity - emotional trading')
                
                # Overall crowd behavior assessment
                if volatility > 0.5 and len(gaps) > 2:
                    psychology['crowd_behavior'] = 'PANIC' if signal_type == 'BEARISH' else 'EUPHORIA'
                elif volatility > 0.3:
                    psychology['crowd_behavior'] = 'ANXIOUS' if signal_type == 'BEARISH' else 'OPTIMISTIC'
                else:
                    psychology['crowd_behavior'] = 'CALM'
            
        except Exception as e:
            print(f"[MARKET INTEL] Error analyzing psychology for {symbol}: {e}")
        
        return psychology
    
    def _generate_predictive_intelligence(self, intelligence: Dict) -> Dict:
        """Generate predictive intelligence and outcome probabilities"""
        prediction = {
            'success_probability': 0.5,
            'time_horizon': '30 days',
            'confidence_level': 'MEDIUM',
            'key_factors': [],
            'risk_adjusted_return': 0
        }
        
        try:
            symbol = intelligence['symbol']
            signal_type = intelligence['signal_type']
            
            # Base probability from momentum
            momentum_strength = intelligence.get('momentum_analysis', {}).get('trend_strength', 0)
            base_prob = 0.5 + (momentum_strength / 200)  # Convert strength to probability adjustment
            
            # News catalyst adjustment
            news_triggers = intelligence.get('news_triggers', [])
            high_impact_news = [n for n in news_triggers if n.get('relevance') == 'HIGH']
            if high_impact_news:
                base_prob += 0.15
            
            # Fundamental adjustment
            valuation = intelligence.get('fundamental_analysis', {}).get('valuation_assessment', 'NEUTRAL')
            if signal_type == 'BULLISH' and valuation == 'UNDERVERLUED':
                base_prob += 0.10
            elif signal_type == 'BEARISH' and valuation == 'OVERVALUED':
                base_prob += 0.10
            
            # Psychology adjustment
            crowd_behavior = intelligence.get('market_psychology', {}).get('crowd_behavior', 'NEUTRAL')
            if (signal_type == 'BULLISH' and crowd_behavior in ['EUPHORIA', 'OPTIMISTIC']) or \
               (signal_type == 'BEARISH' and crowd_behavior in ['PANIC', 'ANXIOUS']):
                base_prob += 0.05
            
            # Ensure probability stays in valid range
            success_probability = max(0.1, min(0.9, base_prob))
            
            # Confidence level
            if len(high_impact_news) > 0 and momentum_strength > 50:
                confidence = 'HIGH'
            elif momentum_strength > 30 or len(news_triggers) > 0:
                confidence = 'MEDIUM'
            else:
                confidence = 'LOW'
            
            # Key factors
            key_factors = []
            if momentum_strength > 40:
                key_factors.append(f"Strong {signal_type.lower()} momentum ({momentum_strength:.0f}/100)")
            if high_impact_news:
                key_factors.append("High-impact news catalysts")
            if valuation in ['UNDERVERLUED', 'OVERVALUED']:
                key_factors.append(f"Favorable valuation ({valuation})")
            
            # Risk-adjusted return estimate
            if signal_type == 'BULLISH':
                risk_adjusted_return = success_probability * 0.25  # Expected 25% return if successful
            else:
                risk_adjusted_return = success_probability * 0.20  # Expected 20% return if successful
            
            prediction = {
                'success_probability': success_probability,
                'time_horizon': '30 days',
                'confidence_level': confidence,
                'key_factors': key_factors,
                'risk_adjusted_return': risk_adjusted_return
            }
            
        except Exception as e:
            print(f"[MARKET INTEL] Error generating prediction for {symbol}: {e}")
        
        return prediction
    
    def _identify_risk_factors(self, intelligence: Dict) -> List[Dict]:
        """Identify specific risk factors for the trade"""
        risk_factors = []
        
        try:
            symbol = intelligence['symbol']
            signal_type = intelligence['signal_type']
            
            # High volatility risk
            volatility = intelligence.get('market_psychology', {}).get('sentiment_indicators', {}).get('volatility', 0)
            if volatility > 0.5:
                risk_factors.append({
                    'type': 'HIGH_VOLATILITY',
                    'severity': 'HIGH',
                    'description': f'High volatility ({volatility:.1%}) increases risk of adverse moves'
                })
            
            # Contrarian signal risk
            crowd_behavior = intelligence.get('market_psychology', {}).get('crowd_behavior', 'NEUTRAL')
            if (signal_type == 'BULLISH' and crowd_behavior in ['PANIC', 'ANXIOUS']) or \
               (signal_type == 'BEARISH' and crowd_behavior in ['EUPHORIA', 'OPTIMISTIC']):
                risk_factors.append({
                    'type': 'CONTRARIAN_SIGNAL',
                    'severity': 'MEDIUM',
                    'description': 'Trading against crowd psychology increases risk'
                })
            
            # Valuation risk
            valuation = intelligence.get('fundamental_analysis', {}).get('valuation_assessment', 'NEUTRAL')
            if (signal_type == 'BULLISH' and valuation == 'OVERVALUED') or \
               (signal_type == 'BEARISH' and valuation == 'UNDERVERLUED'):
                risk_factors.append({
                    'type': 'VALUATION_RISK',
                    'severity': 'MEDIUM',
                    'description': f'Valuation ({valuation}) contradicts signal direction'
                })
            
            # Weak momentum risk
            momentum_strength = intelligence.get('momentum_analysis', {}).get('trend_strength', 0)
            if momentum_strength < 20:
                risk_factors.append({
                    'type': 'WEAK_MOMENTUM',
                    'severity': 'MEDIUM',
                    'description': 'Weak momentum increases probability of signal failure'
                })
            
        except Exception as e:
            print(f"[MARKET INTEL] Error identifying risk factors for {symbol}: {e}")
        
        return risk_factors
    
    def _calculate_opportunity_strength(self, intelligence: Dict) -> float:
        """Calculate overall opportunity strength score (0-100)"""
        try:
            score = 50  # Base score
            
            # Momentum contribution (30% weight)
            momentum_strength = intelligence.get('momentum_analysis', {}).get('trend_strength', 0)
            score += (momentum_strength - 50) * 0.3
            
            # News catalysts contribution (25% weight)
            news_triggers = intelligence.get('news_triggers', [])
            high_impact_news = [n for n in news_triggers if n.get('relevance') == 'HIGH']
            news_score = min(50, len(high_impact_news) * 20 + len(news_triggers) * 10)
            score += (news_score - 25) * 0.25
            
            # Fundamentals contribution (20% weight)
            valuation = intelligence.get('fundamental_analysis', {}).get('valuation_assessment', 'NEUTRAL')
            signal_type = intelligence['signal_type']
            if (signal_type == 'BULLISH' and valuation == 'UNDERVERLUED') or \
               (signal_type == 'BEARISH' and valuation == 'OVERVALUED'):
                score += 10 * 0.2
            elif valuation == 'FAIR':
                score += 5 * 0.2
            else:
                score -= 5 * 0.2
            
            # Psychology contribution (15% weight)
            crowd_behavior = intelligence.get('market_psychology', {}).get('crowd_behavior', 'NEUTRAL')
            if (signal_type == 'BULLISH' and crowd_behavior in ['EUPHORIA', 'OPTIMISTIC']) or \
               (signal_type == 'BEARISH' and crowd_behavior in ['PANIC', 'ANXIOUS']):
                score += 10 * 0.15
            elif crowd_behavior == 'CALM':
                score += 5 * 0.15
            else:
                score -= 5 * 0.15
            
            # Risk adjustment (10% weight)
            risk_factors = intelligence.get('risk_factors', [])
            high_risk_factors = [r for r in risk_factors if r.get('severity') == 'HIGH']
            if high_risk_factors:
                score -= len(high_risk_factors) * 5 * 0.1
            
            # Ensure score stays in valid range
            final_score = max(10, min(100, score))
            
            return final_score
            
        except Exception as e:
            print(f"[MARKET INTEL] Error calculating opportunity strength: {e}")
            return 50  # Default to neutral
    
    def format_intelligence_summary(self, intelligence: Dict) -> str:
        """
        Format intelligence analysis for display in trading alerts
        """
        symbol = intelligence['symbol']
        signal_type = intelligence['signal_type']
        strength = intelligence['opportunity_strength']
        
        summary = f"🧠 **MARKET INTELLIGENCE: {symbol}**\n"
        summary += f"📊 Signal: {signal_type} | Strength: {strength:.0f}/100\n\n"
        
        # Sector context
        sector_context = intelligence.get('sector_context', {})
        if sector_context.get('primary_sector'):
            sector = sector_context['primary_sector']
            ranking = sector_context.get('sector_ranking', {})
            if ranking:
                summary += f"🏭 **SECTOR CONTEXT:** {sector} | Rank: {ranking['rank']}/{ranking['total']} (Top {ranking['percentile']:.0f}%)\n"
        
        # News catalysts
        news_triggers = intelligence.get('news_triggers', [])
        if news_triggers:
            top_news = news_triggers[0]
            summary += f"📰 **NEWS CATALYST:** {top_news.get('title', 'Market-moving news detected')}\n"
        
        # Fundamental analysis
        fundamentals = intelligence.get('fundamental_analysis', {})
        valuation = fundamentals.get('valuation_assessment', 'NEUTRAL')
        pe_ratio = fundamentals.get('valuation_metrics', {}).get('pe_ratio', 0)
        if pe_ratio > 0:
            summary += f"💰 **FUNDAMENTALS:** Valuation: {valuation} | P/E: {pe_ratio:.1f}\n"
        
        # Momentum
        momentum = intelligence.get('momentum_analysis', {})
        momentum_assessment = momentum.get('momentum_assessment', 'NEUTRAL')
        trend_strength = momentum.get('trend_strength', 0)
        summary += f"📈 **MOMENTUM:** {momentum_assessment} | Strength: {trend_strength:.0f}/100\n"
        
        # Predictive intelligence
        prediction = intelligence.get('predictive_intelligence', {})
        success_prob = prediction.get('success_probability', 0.5) * 100
        confidence = prediction.get('confidence_level', 'MEDIUM')
        summary += f"🎯 **PREDICTION:** {success_prob:.0f}% success probability | Confidence: {confidence}\n"
        
        # Risk factors
        risk_factors = intelligence.get('risk_factors', [])
        if risk_factors:
            high_risks = [r for r in risk_factors if r.get('severity') == 'HIGH']
            if high_risks:
                summary += f"⚠️ **RISKS:** {len(high_risks)} high-risk factors identified\n"
        
        return summary
