"""
Thematic Analysis Engine - Macro Trend Detection and Stock Mapping

Identifies macro themes from news and maps them to relevant stocks.
Generates AI-driven reasoning for why these themes represent trading opportunities.

Key Features:
- Scans news for recurring themes and trends
- Maps themes to relevant stock tickers
- Generates AI reasoning for thematic trades
- Scores thematic confidence based on news momentum
"""

import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import yfinance as yf
import json
import requests

from utils.confidence_utils import normalize_confidence_to_pct


class ThematicTheme:
    """Represents a thematic investment opportunity"""
    
    def __init__(self, name: str, keywords: List[str], description: str):
        self.name = name
        self.keywords = keywords
        self.description = description
        self.news_mentions = []
        self.related_stocks = []
        self.confidence_score = 0.0
        self.momentum_score = 0.0
        self.ai_reasoning = ""
        self.last_updated = datetime.now()


class ThematicAnalyzer:
    """Analyzes news to identify investment themes"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.themes = self._initialize_themes()
        self.news_history = []
        self.theme_momentum = defaultdict(list)

    # region agent log
    def _debug_log(self, run_id: str, hypothesis_id: str, location: str, message: str, data: Dict):
        """Temporary debug instrumentation for session 28cc99."""
        try:
            payload = {
                "sessionId": "28cc99",
                "runId": run_id,
                "hypothesisId": hypothesis_id,
                "location": location,
                "message": message,
                "data": data,
                "pid": __import__("os").getpid(),
                "timestamp": int(datetime.now().timestamp() * 1000),
            }
            with open("debug-28cc99.log", "a", encoding="utf-8") as f:
                f.write(json.dumps(payload, default=str) + "\n")
        except Exception:
            pass
    # endregion
        
    def _initialize_themes(self) -> List[ThematicTheme]:
        """Initialize predefined investment themes"""
        themes = [
            ThematicTheme(
                name="Energy Crisis",
                keywords=[
                    "energy", "power", "electricity", "oil", "gas", "nuclear", "renewable", "solar", "wind",
                    "energy shortage", "power grid", "electricity demand", "energy production",
                    "blackout", "power outage", "energy infrastructure", "natural gas", "energy transition"
                ],
                description="US energy consumption outpacing production capacity"
            ),
            ThematicTheme(
                name="AI Infrastructure",
                keywords=[
                    "AI", "artificial intelligence", "chip", "semiconductor", "data center", "cloud", "GPU", "computing",
                    "data centers", "AI computing", "chip demand", "semiconductor shortage",
                    "cloud computing", "AI infrastructure", "GPU demand", "neural networks",
                    "machine learning", "AI chips", "nvidia", "amd"
                ],
                description="Growing demand for AI computing infrastructure"
            ),
            ThematicTheme(
                name="Supply Chain Restructuring",
                keywords=[
                    "supply chain", "manufacturing", "factory", "production", "industrial", "reshoring", "onshoring",
                    "supply chain", "manufacturing", "onshoring", "reshoring", "factory",
                    "production capacity", "industrial", "manufacturing boom", "made in america"
                ],
                description="Shift in global supply chains towards domestic production"
            ),
            ThematicTheme(
                name="Digital Transformation",
                keywords=[
                    "digital", "software", "technology", "cloud", "cybersecurity", "remote", "online",
                    "digitalization", "cloud adoption", "cybersecurity", "remote work",
                    "digital economy", "software demand", "technology adoption", "saas"
                ],
                description="Accelerated digital transformation across industries"
            )
        ]
        return themes
    
    def analyze_news_themes(self, news_items: List[Dict]) -> List[ThematicTheme]:
        """Analyze news articles to identify active themes"""
        print("[THEMATIC ANALYSIS] Scanning news for macro themes...")
        print(f"[THEMATIC ANALYSIS] Processing {len(news_items)} news items...")
        
        # Reset theme mentions
        for theme in self.themes:
            theme.news_mentions = []
        
        # Scan each news item for theme matches
        for i, item in enumerate(news_items):
            text = f"{item.get('title', '')} {item.get('summary', '')}".lower()
            
            for theme in self.themes:
                matches = self._find_theme_matches(text, theme)
                if matches:
                    theme.news_mentions.append({
                        'title': item.get('title', ''),
                        'url': item.get('url', ''),
                        'date': item.get('published', ''),
                        'matches': matches,
                        'sentiment': item.get('sentiment', 0)
                    })
                    print(f"[THEMATIC ANALYSIS] Found {theme.name} in: {item.get('title', '')[:50]}...")
        
        # Calculate theme scores and identify active themes
        active_themes = []
        for theme in self.themes:
            if len(theme.news_mentions) >= 1:  # Need minimum mentions (lowered from 3)
                theme.confidence_score = self._calculate_confidence_score(theme)
                theme.momentum_score = self._calculate_momentum_score(theme)
                
                if theme.confidence_score > 0.2:  # Lowered confidence threshold from 0.3
                    theme.ai_reasoning = self._generate_ai_reasoning(theme)
                    active_themes.append(theme)
        
        # Sort by confidence score
        active_themes.sort(key=lambda x: x.confidence_score, reverse=True)
        
        print(f"[THEMATIC ANALYSIS] Found {len(active_themes)} active themes")
        for theme in active_themes[:3]:
            conf_pct = normalize_confidence_to_pct(theme.confidence_score)
            print(
                f"   TARGET {theme.name}: {conf_pct:.1f}% confidence "
                f"({len(theme.news_mentions)} mentions)"
            )
        
        return active_themes
    
    def _find_theme_matches(self, text: str, theme: ThematicTheme) -> List[str]:
        """Find keyword matches in text for a theme"""
        matches = []
        for keyword in theme.keywords:
            if keyword in text:
                matches.append(keyword)
        return matches
    
    def _calculate_confidence_score(self, theme: ThematicTheme) -> float:
        """Calculate confidence score based on news mentions and sentiment"""
        if not theme.news_mentions:
            return 0.0
        
        # Base score from number of mentions
        mention_score = min(len(theme.news_mentions) / 10.0, 1.0)
        
        # Sentiment adjustment
        avg_sentiment = sum(m.get('sentiment', 0) for m in theme.news_mentions) / len(theme.news_mentions)
        sentiment_adjustment = (avg_sentiment + 1) / 2  # Convert from [-1,1] to [0,1]
        
        # Recency bonus
        recent_mentions = sum(1 for m in theme.news_mentions 
                            if self._is_recent(m.get('date', '')))
        recency_bonus = recent_mentions / len(theme.news_mentions)
        
        confidence = (mention_score * 0.4 + sentiment_adjustment * 0.3 + recency_bonus * 0.3)
        return confidence
    
    def _calculate_momentum_score(self, theme: ThematicTheme) -> float:
        """Calculate momentum based on frequency of mentions over time"""
        if len(theme.news_mentions) < 2:
            return 0.0
        
        # Simple momentum: more recent mentions = higher momentum
        recent_weight = sum(0.5 ** i for i in range(min(5, len(theme.news_mentions))))
        momentum = recent_weight / 5.0  # Normalize to 0-1
        return momentum
    
    def _is_recent(self, date_str: str, days: int = 7) -> bool:
        """Check if a date is within recent days"""
        try:
            if not date_str:
                return False
            # Parse date string (format varies by source)
            date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return datetime.now() - date <= timedelta(days=days)
        except:
            return False
    
    def _generate_ai_reasoning(self, theme: ThematicTheme) -> str:
        """Generate AI reasoning for why this theme is a trading opportunity"""
        reasoning = f"AI Analysis: {theme.name}\n\n"
        
        reasoning += f"**Thesis:** {theme.description}\n\n"
        
        reasoning += f"**Evidence:**\n"
        reasoning += f"• {len(theme.news_mentions)} recent news articles discussing this theme\n"
        
        # Find most cited keywords
        all_keywords = []
        for mention in theme.news_mentions:
            all_keywords.extend(mention.get('matches', []))
        keyword_counts = Counter(all_keywords)
        
        if keyword_counts:
            top_keywords = keyword_counts.most_common(3)
            reasoning += f"• Key indicators: {', '.join([f'{kw} ({count})' for kw, count in top_keywords])}\n"
        
        # Sentiment analysis
        avg_sentiment = sum(m.get('sentiment', 0) for m in theme.news_mentions) / len(theme.news_mentions)
        sentiment_desc = "Positive" if avg_sentiment > 0.1 else "Negative" if avg_sentiment < -0.1 else "Neutral"
        reasoning += f"• Market sentiment: {sentiment_desc} ({avg_sentiment:.1f})\n\n"
        
        reasoning += f"**Opportunity:** This theme represents a structural shift in the market "
        reasoning += f"with {'strong' if theme.momentum_score > 0.5 else 'moderate'} momentum. "
        reasoning += f"Companies positioned to benefit from this trend may see sustained growth.\n"
        
        return reasoning
    
    def map_themes_to_stocks(self, themes: List[ThematicTheme]) -> List[Dict]:
        """Map active themes to relevant stock tickers"""
        print("[THEMATIC ANALYSIS] Mapping themes to relevant stocks...")
        
        theme_stocks = {
            "Energy Crisis": [
                {"ticker": "FLNC", "name": "Fluence Energy", "reason": "Energy storage solutions for grid stability"},
                {"ticker": "ET", "name": "Energy Transfer", "reason": "Natural gas infrastructure and transport"},
                {"ticker": "CEG", "name": "Constellation Energy", "reason": "Nuclear power generation"},
                {"ticker": "NRG", "name": "NRG Energy", "reason": "Power generation and retail"},
                {"ticker": "VST", "name": "Vistra Corp", "reason": "Electricity generation and trading"}
            ],
            "AI Infrastructure": [
                {"ticker": "NVDA", "name": "NVIDIA", "reason": "AI chips and GPUs"},
                {"ticker": "AMD", "name": "AMD", "reason": "AI accelerators and data center CPUs"},
                {"ticker": "SMCI", "name": "Super Micro Computer", "reason": "AI server infrastructure"},
                {"ticker": "PLTR", "name": "Palantir", "reason": "AI data analytics platforms"},
                {"ticker": "CRM", "name": "Salesforce", "reason": "AI-powered business software"}
            ],
            "Supply Chain Restructuring": [
                {"ticker": "CAT", "name": "Caterpillar", "reason": "Industrial equipment for manufacturing"},
                {"ticker": "GE", "name": "General Electric", "reason": "Manufacturing technology"},
                {"ticker": "DE", "name": "Deere & Co", "reason": "Industrial automation"},
                {"ticker": "UMC", "name": "United Microelectronics", "reason": "Semiconductor manufacturing"},
                {"ticker": "KLAC", "name": "KLA Corporation", "reason": "Semiconductor equipment"}
            ],
            "Digital Transformation": [
                {"ticker": "MSFT", "name": "Microsoft", "reason": "Cloud computing and software"},
                {"ticker": "AMZN", "name": "Amazon", "reason": "Cloud services and digital infrastructure"},
                {"ticker": "CRM", "name": "Salesforce", "reason": "Business digitalization"},
                {"ticker": "ADBE", "name": "Adobe", "reason": "Digital document solutions"},
                {"ticker": "INTU", "reason": "Financial software and automation"}
            ]
        }
        
        mapped_opportunities = []
        
        for theme in themes:
            if theme.name in theme_stocks:
                print(f"\n   ANALYZING {theme.name} - Analyzing stocks...")
                
                for stock_info in theme_stocks[theme.name]:
                    ticker = stock_info["ticker"]
                    
                    # Get stock data
                    try:
                        current_price = self._fetch_stock_price(ticker)
                        if current_price is None:
                            print(f"      SKIP {ticker}: No verified live price")
                            continue
                        
                        from utils.price_filter_config import within_price_cap
                        if within_price_cap(current_price, self.config):
                            opportunity = {
                                'theme': theme.name,
                                'ticker': ticker,
                                'name': stock_info.get("name", ticker),
                                'price': current_price,
                                'reason': stock_info["reason"],
                                'theme_confidence': theme.confidence_score,
                                'ai_reasoning': theme.ai_reasoning,
                                'combined_score': self._calculate_combined_score(theme, current_price)
                            }
                            mapped_opportunities.append(opportunity)
                            print(f"      PASS {ticker}: ${current_price:.2f} - {stock_info['reason']}")
                        else:
                            print(f"      FAIL {ticker}: ${current_price:.2f} - Above max price cap")
                            
                    except Exception as e:
                        print(f"      ERROR {ticker}: Error fetching data - {str(e)}")
        
        # region agent log
        self._debug_log(
            "pre-fix",
            "H13",
            "brain/thematic_analysis_engine.py:map_themes_to_stocks",
            "thematic stock mapping result",
            {
                "themes": [theme.name for theme in themes],
                "mapped_opportunities": len(mapped_opportunities),
                "mapped_symbols": [item.get("ticker") for item in mapped_opportunities],
            },
        )
        # endregion
        
        # Sort by combined score
        mapped_opportunities.sort(key=lambda x: x['combined_score'], reverse=True)
        
        print(f"\n[THEMATIC ANALYSIS] Found {len(mapped_opportunities)} thematic stock opportunities")
        
        return mapped_opportunities

    def _fetch_stock_price(self, ticker: str) -> Optional[float]:
        """Fetch a live price with fallbacks for empty yfinance history."""
        try:
            history = yf.Ticker(ticker).history(period="5d")
            if len(history) > 0:
                closes = history['Close'].dropna()
                if len(closes) > 0:
                    return float(closes.iloc[-1])
        except Exception:
            pass

        try:
            response = requests.get(
                f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}",
                params={"range": "5d", "interval": "1d"},
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=8,
            )
            if response.status_code == 200:
                result = (response.json().get("chart", {}).get("result") or [None])[0]
                quote = ((result or {}).get("indicators", {}).get("quote") or [{}])[0]
                closes = [value for value in quote.get("close", []) if value is not None]
                if closes:
                    return float(closes[-1])
        except Exception:
            pass

        try:
            import csv
            import io
            response = requests.get(
                f"https://stooq.com/q/l/?s={ticker.lower()}.us&f=sd2t2ohlcv&h&e=csv",
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=8,
            )
            rows = list(csv.DictReader(io.StringIO(response.text)))
            if rows and rows[0].get("Close") not in (None, "N/D"):
                return float(rows[0]["Close"])
        except Exception:
            pass

        return None
    
    def _calculate_combined_score(self, theme: ThematicTheme, stock_price: float) -> float:
        """Calculate combined score for theme + stock"""
        # Base score from theme confidence
        base_score = theme.confidence_score
        
        from utils.price_filter_config import resolve_price_filter
        _, cap = resolve_price_filter(self.config)
        ref = cap if cap else 10000.0
        price_factor = max(0, 1 - (stock_price / ref))
        
        # Momentum boost
        momentum_boost = theme.momentum_score * 0.2
        
        combined = base_score * 0.7 + price_factor * 0.1 + momentum_boost
        return min(combined, 1.0)
