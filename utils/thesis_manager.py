"""
Thesis Manager - Long-term Trade Reasoning System
Implements the Master Decision Loop, Confidence Decay Curve, and Future Optionality Scoring
"""

import sqlite3
import os
from utils.alert_learning_loop import get_alert_learning_loop
from utils.pe_ratio_analyzer import PERatioAnalyzer
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import yfinance as yf

try:
    from utils.market_data_cache import MarketDataCache
except ImportError:
    MarketDataCache = None


class ThesisManager:
    """Manages long-term trade theses with confidence tracking and survival analysis"""
    
    def __init__(self, db_path: str = "insider_accumulation.db", cache=None):
        self.db_path = db_path
        self.cache = cache  # MarketDataCache instance
        self._init_database()
        self.pe_analyzer = PERatioAnalyzer()
    
    def _init_database(self):
        """Initialize database tables for thesis tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Thesis positions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS thesis_positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT UNIQUE NOT NULL,
                thesis_type TEXT NOT NULL,  -- Infrastructure, Growth, Optionality, Speculation
                ecosystem_role TEXT NOT NULL,  -- Shovel, Toll Booth, Lottery Ticket
                initial_confidence INTEGER NOT NULL,  -- 0-100
                current_confidence INTEGER NOT NULL,  -- 0-100
                initial_thesis TEXT NOT NULL,  -- Detailed reasoning
                success_conditions TEXT NOT NULL,  -- What must happen
                entry_price REAL,
                entry_date TEXT,
                max_position_size REAL,  -- % of portfolio
                last_review TEXT,
                status TEXT DEFAULT 'active'  -- active, downgraded, exited
            )
        """)
        
        # Confidence events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS confidence_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                event_date TEXT NOT NULL,
                event_type TEXT NOT NULL,  -- positive, negative, decay
                confidence_change INTEGER NOT NULL,
                reason TEXT NOT NULL,
                confidence_before INTEGER NOT NULL,
                confidence_after INTEGER NOT NULL,
                FOREIGN KEY (ticker) REFERENCES thesis_positions(ticker)
            )
        """)
        
        # Optionality scoring table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS optionality_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT UNIQUE NOT NULL,
                macro_inevitability INTEGER,  -- 0-10
                survival_probability INTEGER,  -- 0-10
                optional_upside INTEGER,  -- 0-10
                dilution_risk INTEGER,  -- 0-10 (inverse)
                replaceability_risk INTEGER,  -- 0-10 (inverse)
                total_score INTEGER,
                last_updated TEXT,
                FOREIGN KEY (ticker) REFERENCES thesis_positions(ticker)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def create_thesis(self, ticker: str, insider_signals: List[Dict] = None) -> Dict:
        """Create a new thesis based on insider signals and fundamental analysis"""
        print(f"\n[THESIS] Creating thesis for {ticker}")
        print("=" * 60)
        
        # Fetch ticker info once (with cache if available)
        if self.cache and MarketDataCache:
            info = self.cache.fetch_ticker_info(ticker)
        else:
            info = yf.Ticker(ticker).info
        
        # Get P/E analysis
        pe_analysis = self.pe_analyzer.analyze_pe_ratio(ticker)
        print(f"\n[P/E] Analysis: {pe_analysis.get('valuation_level', 'Unknown')} (Score: {pe_analysis.get('score', 0)}/10)")
        
        if pe_analysis.get("error"):
            print(f"[P/E] Note: {pe_analysis['error']}")
        else:
            print(f"[P/E] Current: {pe_analysis.get('current_pe', 'N/A'):.1f} vs Industry: {pe_analysis.get('industry_pe', 'N/A'):.1f}")
            if pe_analysis.get("peg_ratio"):
                print(f"[P/E] PEG: {pe_analysis['peg_ratio']:.2f} ({pe_analysis.get('peg_interpretation', 'N/A')})")
        
        # Step 0: Classify the game
        game_type = self._classify_asset_game(ticker, info)
        print(f"\nStep 0 - Game Classification: {game_type}")
        
        # Step 1: Macro Force Test
        macro_pass, macro_reason = self._macro_force_test(ticker, info)
        print(f"\nStep 1 - Macro Force Test: {'PASS' if macro_pass else 'FAIL'}")
        print(f"Reason: {macro_reason}")
        
        if not macro_pass:
            ecosystem_role = self._ecosystem_role_test(ticker, info)
            return {
                "action": "trade_only",
                "reasoning": f"Fails macro force test: {macro_reason}",
                "classification": game_type,
                "ecosystem_role": ecosystem_role
            }
        
        # Step 2: Role in Ecosystem
        ecosystem_role = self._ecosystem_role_test(ticker, info)
        print(f"\nStep 2 - Ecosystem Role: {ecosystem_role}")
        
        # Step 3: Survival Filter
        survival_pass, survival_score = self._survival_filter(ticker, info)
        print(f"\nStep 3 - Survival Test: {'PASS' if survival_pass else 'FAIL'} ({survival_score}/10)")
        
        if not survival_pass:
            return {
                "action": "reject",
                "reasoning": f"Survival risk too high: {survival_score}/10",
                "classification": game_type,
                "ecosystem_role": ecosystem_role
            }
        
        # Step 4: Price as Risk Absorber
        price_buffer = self._price_risk_buffer(ticker, info)
        print(f"\nStep 4 - Price Buffer: {price_buffer}")
        
        # Step 5: Success Definition
        success_conditions = self._define_success_conditions(ticker, info)
        print(f"\nStep 5 - Success Conditions: {success_conditions}")
        
        # Step 6: Regret-Based Sizing
        max_size = self._calculate_regret_based_size(game_type, survival_score)
        print(f"\nStep 6 - Max Position Size: {max_size}% of portfolio")
        
        # Step 7: Time ≠ Blind Faith
        review_schedule = self._set_review_schedule(game_type)
        print(f"\nStep 7 - Review Schedule: Every {review_schedule} months")
        
        return {
            "action": "establish_thesis" if game_type in ["Optionality / Venture", "Growth / Execution"] else "monitor",
            "classification": game_type,
            "ecosystem_role": ecosystem_role,
            "survival_score": survival_score,
            "max_position_size": max_size,
            "success_conditions": success_conditions,
            "review_schedule": review_schedule,
            "reasoning": f"Passes macro force test as {ecosystem_role} with survival score {survival_score}/10"
        }
    
    def _classify_asset_game(self, ticker: str, info: Optional[Dict] = None) -> str:
        """Classify what game we're playing with this asset"""
        try:
            # Use cached info if provided, otherwise fetch
            if info is None:
                if self.cache and MarketDataCache:
                    info = self.cache.fetch_ticker_info(ticker)
                else:
                    info = yf.Ticker(ticker).info
            market_cap = info.get("marketCap", 0)
            pe_ratio = info.get("trailingPE", 0)
            revenue_growth = info.get("revenueGrowth", 0)
            sector = info.get("sector", "")
            
            # Infrastructure/Cash-flow
            if market_cap > 10_000_000_000 and pe_ratio and pe_ratio > 0:
                if sector in ["Utilities", "Energy", "Financial Services"]:
                    return "Infrastructure / Cash-flow"
                return "Growth / Execution"
            
            # Growth/Execution
            elif market_cap > 2_000_000_000 and revenue_growth and revenue_growth > 0.1:
                return "Growth / Execution"
            
            # Optionality/Venture
            elif market_cap < 2_000_000_000 and (not pe_ratio or pe_ratio < 0):
                if sector in ["Technology", "Biotechnology", "Energy"]:
                    return "Optionality / Venture"
            
            # Sector-based classification
            if sector in ["Utilities", "Energy", "Financial Services"]:
                return "Infrastructure / Cash-flow"
            elif sector in ["Technology", "Healthcare", "Consumer Discretionary"]:
                return "Growth / Execution"
            elif sector in ["Biotechnology", "Clean Energy"]:
                return "Optionality / Venture"
            
            # Default to speculation
            return "Speculation / Trade"
            
        except Exception as e:
            print(f"[THESIS] Error classifying {ticker}: {e}")
            # Default to speculation on error - never Unknown
            return "Speculation / Trade"
    
    def _macro_force_test(self, ticker: str, info: Optional[Dict] = None) -> Tuple[bool, str]:
        """Test if the world is structurally forced to move in this direction"""
        try:
            # Use cached info if provided, otherwise fetch
            if info is None:
                if self.cache and MarketDataCache:
                    info = self.cache.fetch_ticker_info(ticker)
                else:
                    info = yf.Ticker(ticker).info
            sector = info.get("sector", "")
            industry = info.get("industry", "")
            
            # Macro forces that are unavoidable over 10 years
            unstoppable_forces = {
                "Technology": ["Semiconductors", "Software", "Cloud Computing", "AI"],
                "Healthcare": ["Biotechnology", "Medical Devices", "Pharmaceuticals"],
                "Energy": ["Renewable Energy", "Electrical Equipment", "Oil & Gas"],
                "Financial": ["Financial Services", "Insurance", "Asset Management"],
                "Industrial": ["Aerospace & Defense", "Industrial Machinery", "Construction"],
                "Utilities": ["Utilities", "Renewable Energy"]
            }
            
            for macro_sector, industries in unstoppable_forces.items():
                if sector in macro_sector or any(ind in industry for ind in industries):
                    return True, f"{sector} - {industry} addresses structural demand over 10 years"
            
            # Check if it's a narrative without real constraint
            narrative_industries = ["Specialty Retail", "Leisure", "Media", "Consumer Discretionary"]
            if industry in narrative_industries:
                return False, f"{industry} is driven by sentiment, not structural necessity"
            
            return False, f"Unclear macro necessity for {sector} - {industry}"
            
        except Exception as e:
            print(f"[THESIS] Error in macro force test for {ticker}: {e}")
            return False, "Unable to assess macro forces"
    
    def _ecosystem_role_test(self, ticker: str, info: Optional[Dict] = None) -> str:
        """Determine if this is a shovel seller, toll booth, or lottery ticket"""
        try:
            # Use cached info if provided, otherwise fetch
            if info is None:
                if self.cache and MarketDataCache:
                    info = self.cache.fetch_ticker_info(ticker)
                else:
                    info = yf.Ticker(ticker).info
            sector = info.get("sector", "")
            industry = info.get("industry", "")
            business_summary = info.get("longBusinessSummary", "").lower()
            
            # Shovel sellers - pickaxes in a gold rush
            shovel_keywords = ["equipment", "infrastructure", "semiconductor", "cloud", "platform", "tools", "component", "chip", "hardware"]
            if any(keyword in business_summary for keyword in shovel_keywords):
                return "Shovel Seller"
            
            # Toll booths - recurring revenue, network effects
            toll_keywords = ["subscription", "recurring", "network", "platform", "exchange", "marketplace", "utility", "regulated"]
            if any(keyword in business_summary for keyword in toll_keywords):
                return "Toll Booth"
            
            # Sector-based fallbacks
            if sector in ["Technology", "Semiconductors", "Industrial", "Energy", "Utilities"]:
                return "Shovel Seller"
            elif sector in ["Financial Services", "Real Estate", "Utilities"]:
                return "Toll Booth"
            
            # Everything else is a lottery ticket on specific outcomes
            return "Lottery Ticket"
            
        except Exception as e:
            print(f"[THESIS] Error determining ecosystem role for {ticker}: {e}")
            # Default to Lottery Ticket on error - never Unknown
            return "Lottery Ticket"
    
    def _survival_filter(self, ticker: str, info: Optional[Dict] = None) -> Tuple[bool, int]:
        """Test if company can survive bad years without wiping equity holders"""
        try:
            # Use cached info if provided, otherwise fetch
            if info is None:
                if self.cache and MarketDataCache:
                    info = self.cache.fetch_ticker_info(ticker)
                else:
                    info = yf.Ticker(ticker).info
            market_cap = info.get("marketCap", 0)
            debt_to_equity = info.get("debtToEquity", 0)
            current_ratio = info.get("currentRatio", 0)
            profit_margins = info.get("profitMargins", 0)
            operating_margins = info.get("operatingMargins", 0)
            
            score = 5  # Base score
            reasons = []
            
            # Cash burn / profitability
            if profit_margins and profit_margins > 0:
                score += 2
                reasons.append("Profitable")
            elif operating_margins and operating_margins > -0.1:
                score += 1
                reasons.append("Manageable burn")
            else:
                score -= 2
                reasons.append("High burn")
            
            # Balance sheet strength
            if debt_to_equity and debt_to_equity < 0.5:
                score += 1
                reasons.append("Low debt")
            elif debt_to_equity and debt_to_equity > 2:
                score -= 2
                reasons.append("High debt")
            
            # Liquidity
            if current_ratio and current_ratio > 1.5:
                score += 1
                reasons.append("Strong liquidity")
            elif current_ratio and current_ratio < 1:
                score -= 1
                reasons.append("Weak liquidity")
            
            # Market cap (bigger companies more likely to survive)
            if market_cap > 5_000_000_000:
                score += 1
                reasons.append("Large cap")
            elif market_cap < 500_000_000:
                score -= 1
                reasons.append("Micro cap")
            
            score = max(0, min(10, score))
            survival_pass = score >= 4
            
            print(f"[THESIS] Survival Analysis: {score}/10 - {', '.join(reasons)}")
            
            return survival_pass, score
            
        except Exception as e:
            print(f"[THESIS] Error in survival filter for {ticker}: {e}")
            return False, 0
    
    def _price_risk_buffer(self, ticker: str, info: Optional[Dict] = None) -> str:
        """Assess if price provides room for error"""
        try:
            # Use cached info if provided, otherwise fetch
            if info is None:
                if self.cache and MarketDataCache:
                    info = self.cache.fetch_ticker_info(ticker)
                else:
                    info = yf.Ticker(ticker).info
            current_price = info.get("currentPrice", 0)
            fifty_two_week_low = info.get("fiftyTwoWeekLow", 0)
            fifty_two_week_high = info.get("fiftyTwoWeekHigh", 0)
            
            if not all([current_price, fifty_two_week_low, fifty_two_week_high]):
                return "Unable to assess price buffer"
            
            # Calculate position in 52-week range
            range_position = (current_price - fifty_two_week_low) / (fifty_two_week_high - fifty_two_week_low)
            
            if range_position < 0.25:
                return "Excellent buffer - near lows"
            elif range_position < 0.5:
                return "Good buffer - below midpoint"
            elif range_position < 0.75:
                return "Limited buffer - above midpoint"
            else:
                return "No buffer - near highs"
                
        except Exception as e:
            print(f"[THESIS] Error assessing price buffer for {ticker}: {e}")
            return "Unable to assess price buffer"
    
    def _define_success_conditions(self, ticker: str, info: Optional[Dict] = None) -> str:
        """Define what must happen for this to work (no price targets)"""
        try:
            # Use cached info if provided, otherwise fetch
            if info is None:
                if self.cache and MarketDataCache:
                    info = self.cache.fetch_ticker_info(ticker)
                else:
                    info = yf.Ticker(ticker).info
            sector = info.get("sector", "")
            industry = info.get("industry", "")
            
            conditions = []
            
            if "Technology" in sector:
                conditions.extend([
                    "Product-market fit achieved",
                    "Revenue growth accelerates",
                    "Gross margins improve"
                ])
            elif "Biotechnology" in sector:
                conditions.extend([
                    "Clinical trials progress",
                    "Regulatory approval path clear",
                    "Partnership or acquisition interest"
                ])
            elif "Energy" in sector:
                conditions.extend([
                    "Technology costs decline",
                    "Infrastructure adoption begins",
                    "Policy support continues"
                ])
            else:
                conditions.extend([
                    "Market share increases",
                    "Profitability path emerges",
                    "Competitive moat strengthens"
                ])
            
            # Add survival conditions
            conditions.extend([
                "Cash burn manageable",
                "No destructive dilution",
                "Management executes"
            ])
            
            return "; ".join(conditions)
            
        except Exception as e:
            print(f"[THESIS] Error defining success conditions for {ticker}: {e}")
            return "Business execution + survival + market adoption"
    
    def _calculate_regret_based_size(self, game_type: str, survival_score: int) -> float:
        """Calculate position size based on regret tolerance"""
        base_sizes = {
            "Infrastructure / Cash-flow": 5.0,
            "Growth / Execution": 3.0,
            "Optionality / Venture": 1.0,
            "Speculation / Trade": 0.5
        }
        
        base_size = base_sizes.get(game_type, 0.5)
        
        # Adjust based on survival score
        if survival_score >= 7:
            multiplier = 1.5
        elif survival_score >= 5:
            multiplier = 1.0
        else:
            multiplier = 0.5
        
        final_size = base_size * multiplier
        
        # Hard cap for optionality
        if game_type == "Optionality / Venture":
            final_size = min(final_size, 1.0)
        
        return round(final_size, 1)
    
    def _set_review_schedule(self, game_type: str) -> int:
        """Set review frequency in months"""
        schedules = {
            "Infrastructure / Cash-flow": 24,
            "Growth / Execution": 18,
            "Optionality / Venture": 12,
            "Speculation / Trade": 6
        }
        
        return schedules.get(game_type, 12)
    
    def establish_thesis(self, ticker: str, decision_result: Dict):
        """Establish a new thesis position in the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Calculate initial confidence
            initial_confidence = self._calculate_initial_confidence(decision_result)
            
            # Insert thesis position
            cursor.execute("""
                INSERT OR REPLACE INTO thesis_positions 
                (ticker, thesis_type, ecosystem_role, initial_confidence, current_confidence,
                 initial_thesis, success_conditions, entry_price, entry_date, max_position_size,
                 last_review, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ticker,
                decision_result["classification"],
                decision_result["ecosystem_role"],
                initial_confidence,
                initial_confidence,
                decision_result["reasoning"],
                decision_result["success_conditions"],
                None,  # Entry price to be set when position is taken
                datetime.now().isoformat(),
                decision_result["max_position_size"],
                datetime.now().isoformat(),
                "active"
            ))
            
            conn.commit()
            conn.close()
            
            # Calculate and store optionality score (separate connection)
            self._update_optionality_score(ticker)
            
            print(f"\n[THESIS] Established thesis for {ticker}")
            print(f"   Type: {decision_result['classification']}")
            print(f"   Initial Confidence: {initial_confidence}/100")
            print(f"   Max Position: {decision_result['max_position_size']}%")
        except Exception as e:
            print(f"[THESIS] Error establishing thesis for {ticker}: {e}")
            if 'conn' in locals():
                conn.close()
    
    def _calculate_initial_confidence(self, decision_result: Dict) -> int:
        """Calculate initial thesis confidence"""
        base_confidence = 50
        
        # Adjust based on classification
        type_adjustments = {
            "Infrastructure / Cash-flow": 20,
            "Growth / Execution": 10,
            "Optionality / Venture": -10,
            "Speculation / Trade": -20
        }
        
        base_confidence += type_adjustments.get(decision_result["classification"], 0)
        
        # Adjust based on survival score
        survival_score = decision_result.get("survival_score", 5)
        base_confidence += (survival_score - 5) * 5
        
        return max(20, min(80, base_confidence))
    
    def _update_optionality_score(self, ticker: str):
        """Calculate and update the 5-factor optionality scoring"""
        scores = self._calculate_optionality_factors(ticker)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        total_score = sum([
            scores["macro_inevitability"],
            scores["survival_probability"],
            scores["optional_upside"],
            scores["dilution_risk"],
            scores["replaceability_risk"]
        ])
        
        cursor.execute("""
            INSERT OR REPLACE INTO optionality_scores
            (ticker, macro_inevitability, survival_probability, optional_upside,
             dilution_risk, replaceability_risk, total_score, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ticker,
            scores["macro_inevitability"],
            scores["survival_probability"],
            scores["optional_upside"],
            scores["dilution_risk"],
            scores["replaceability_risk"],
            total_score,
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        print(f"\n[THESIS] Optionality Score for {ticker}: {total_score}/50")
        print(f"   Macro: {scores['macro_inevitability']}/10")
        print(f"   Survival: {scores['survival_probability']}/10")
        print(f"   Upside: {scores['optional_upside']}/10")
        print(f"   Dilution Risk: {scores['dilution_risk']}/10")
        print(f"   Replaceability: {scores['replaceability_risk']}/10")
    
    def _calculate_optionality_factors(self, ticker: str, info: Optional[Dict] = None) -> Dict[str, int]:
        """Calculate the 5 factors for optionality scoring"""
        try:
            # Use cached info if provided, otherwise fetch
            if info is None:
                if self.cache and MarketDataCache:
                    info = self.cache.fetch_ticker_info(ticker)
                else:
                    info = yf.Ticker(ticker).info
            
            # Macro Inevitability (0-10)
            macro_pass, _ = self._macro_force_test(ticker, info)
            macro_inevitability = 8 if macro_pass else 3
            
            # Survival Probability (0-10)
            _, survival_score = self._survival_filter(ticker, info)
            survival_probability = survival_score
            
            # Optional Upside (0-10)
            market_cap = info.get("marketCap", 0)
            if market_cap < 500_000_000:
                optional_upside = 9  # Micro-cap has room to grow
            elif market_cap < 2_000_000_000:
                optional_upside = 7  # Small-cap
            elif market_cap < 10_000_000_000:
                optional_upside = 5  # Mid-cap
            else:
                optional_upside = 3  # Large-cap
            
            # Dilution Risk (0-10, inverse scoring - lower is worse)
            pe_ratio = info.get("trailingPE", 0)
            if pe_ratio and pe_ratio > 0:
                dilution_risk = 8  # Profitable companies dilute less
            elif market_cap > 1_000_000_000:
                dilution_risk = 5  # Can raise capital easily
            else:
                dilution_risk = 3  # High dilution risk
            
            # Replaceability Risk (0-10, inverse scoring)
            sector = info.get("sector", "")
            moat_strength = {
                "Technology": 6,
                "Healthcare": 7,
                "Financial": 8,
                "Energy": 5,
                "Utilities": 9,
                "Consumer": 4
            }
            replaceability_risk = moat_strength.get(sector, 5)
            
            return {
                "macro_inevitability": macro_inevitability,
                "survival_probability": survival_probability,
                "optional_upside": optional_upside,
                "dilution_risk": dilution_risk,
                "replaceability_risk": replaceability_risk
            }
            
        except Exception as e:
            print(f"[THESIS] Error calculating optionality factors for {ticker}: {e}")
            return {
                "macro_inevitability": 5,
                "survival_probability": 5,
                "optional_upside": 5,
                "dilution_risk": 5,
                "replaceability_risk": 5
            }
    
    def apply_confidence_decay(self):
        """Apply time-based confidence decay to all active theses"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all active theses
        cursor.execute("""
            SELECT ticker, current_confidence, last_review, thesis_type
            FROM thesis_positions
            WHERE status = 'active'
        """)
        
        theses = cursor.fetchall()
        
        for ticker, confidence, last_review, thesis_type in theses:
            # Calculate months since last review
            last_review_date = datetime.fromisoformat(last_review)
            months_since = (datetime.now() - last_review_date).days / 30
            
            # Apply decay every 18 months
            if months_since >= 18:
                decay_amount = int(months_since / 18) * 5
                new_confidence = max(0, confidence - decay_amount)
                
                # Update confidence
                cursor.execute("""
                    UPDATE thesis_positions
                    SET current_confidence = ?, last_review = ?
                    WHERE ticker = ?
                """, (new_confidence, datetime.now().isoformat(), ticker))
                
                # Record decay event
                cursor.execute("""
                    INSERT INTO confidence_events
                    (ticker, event_date, event_type, confidence_change, reason,
                     confidence_before, confidence_after)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    ticker,
                    datetime.now().isoformat(),
                    "decay",
                    -decay_amount,
                    f"Time-based decay: {months_since:.0f} months without progress",
                    confidence,
                    new_confidence
                ))
                
                print(f"[THESIS] Applied {decay_amount} point decay to {ticker}: {confidence} → {new_confidence}")
                
                # Check for downgrade triggers
                self._check_downgrade_triggers(cursor, ticker, new_confidence)
        
        conn.commit()
        conn.close()
    
    def _check_downgrade_triggers(self, cursor, ticker: str, confidence: int):
        """Check if thesis should be downgraded or exited"""
        if confidence < 20:
            # Thesis invalidated - exit
            cursor.execute("""
                UPDATE thesis_positions
                SET status = 'exited'
                WHERE ticker = ?
            """, (ticker,))
            print(f"[THESIS] THESIS INVALIDATED: {ticker} - confidence below 20")
            
        elif confidence < 35:
            # Exit optionality
            cursor.execute("""
                UPDATE thesis_positions
                SET status = 'downgraded'
                WHERE ticker = ?
            """, (ticker,))
            print(f"[THESIS] EXIT OPTIONALITY: {ticker} - confidence below 35")
    
    def record_confidence_event(self, ticker: str, event_type: str, change: int, reason: str):
        """Record a confidence-changing event"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get current confidence
        cursor.execute("""
            SELECT current_confidence FROM thesis_positions WHERE ticker = ?
        """, (ticker,))
        
        result = cursor.fetchone()
        if not result:
            print(f"[THESIS] No thesis found for {ticker}")
            conn.close()
            return
        
        old_confidence = result[0]
        new_confidence = max(0, min(100, old_confidence + change))
        
        # Update confidence
        cursor.execute("""
            UPDATE thesis_positions
            SET current_confidence = ?, last_review = ?
            WHERE ticker = ?
        """, (new_confidence, datetime.now().isoformat(), ticker))
        
        # Record event
        cursor.execute("""
            INSERT INTO confidence_events
            (ticker, event_date, event_type, confidence_change, reason,
             confidence_before, confidence_after)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            ticker,
            datetime.now().isoformat(),
            event_type,
            change,
            reason,
            old_confidence,
            new_confidence
        ))
        
        conn.commit()
        conn.close()
        
        print(f"[THESIS] Confidence update for {ticker}: {old_confidence} → {new_confidence} ({reason})")
        
        # Check for downgrade triggers
        if new_confidence < 35:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            self._check_downgrade_triggers(cursor, ticker, new_confidence)
            conn.commit()
            conn.close()
    
    def get_active_theses(self) -> List[Dict]:
        """Get all active thesis positions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT tp.*, os.total_score as optionality_score
            FROM thesis_positions tp
            LEFT JOIN optionality_scores os ON tp.ticker = os.ticker
            WHERE tp.status = 'active'
            ORDER BY tp.current_confidence DESC
        """)
        
        columns = [desc[0] for desc in cursor.description]
        theses = []
        
        for row in cursor.fetchall():
            thesis = dict(zip(columns, row))
            theses.append(thesis)
        
        conn.close()
        return theses
    
    def generate_thesis_report(self, ticker: str) -> str:
        """Generate a comprehensive thesis report"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get thesis details
        cursor.execute("""
            SELECT tp.*, os.total_score as optionality_score
            FROM thesis_positions tp
            LEFT JOIN optionality_scores os ON tp.ticker = os.ticker
            WHERE tp.ticker = ?
        """, (ticker,))
        
        thesis_data = cursor.fetchone()
        if not thesis_data:
            return f"No thesis found for {ticker}"
        
        columns = [desc[0] for desc in cursor.description]
        thesis = dict(zip(columns, thesis_data))
        
        # Get recent events
        cursor.execute("""
            SELECT * FROM confidence_events
            WHERE ticker = ?
            ORDER BY event_date DESC
            LIMIT 5
        """, (ticker,))
        
        events = []
        for row in cursor.fetchall():
            event_columns = [desc[0] for desc in cursor.description]
            events.append(dict(zip(event_columns, row)))
        
        conn.close()
        
        # Generate report
        report = f"\n{'='*60}\n"
        report += f"THESIS REPORT: {ticker}\n"
        report += f"{'='*60}\n\n"
        
        report += f"Classification: {thesis['thesis_type']}\n"
        report += f"Ecosystem Role: {thesis['ecosystem_role']}\n"
        report += f"Status: {thesis['status'].upper()}\n"
        report += f"Initial Confidence: {thesis['initial_confidence']}/100\n"
        report += f"Current Confidence: {thesis['current_confidence']}/100\n"
        report += f"Optionality Score: {thesis.get('optionality_score', 'N/A')}/50\n"
        report += f"Max Position Size: {thesis['max_position_size']}%\n\n"
        
        report += f"Initial Thesis:\n{thesis['initial_thesis']}\n\n"
        
        report += f"Success Conditions:\n{thesis['success_conditions']}\n\n"
        
        if events:
            report += f"Recent Events:\n"
            for event in events:
                direction = "↑" if event['confidence_change'] > 0 else "↓"
                report += f"  {event['event_date'][:10]} {direction} {abs(event['confidence_change'])} - {event['reason']}\n"
        
        # Confidence zone analysis
        confidence = thesis['current_confidence']
        if confidence >= 70:
            zone = "CONVICTION ZONE"
            action = "Eligible for increased size"
        elif confidence >= 50:
            zone = "HOLD & MONITOR"
            action = "No action required"
        elif confidence >= 35:
            zone = "SKEPTICAL HOLD"
            action = "Must see progress next cycle"
        else:
            zone = "EXIT OPTIONALITY"
            action = "Consider reducing exposure"
        
        report += f"\nConfidence Zone: {zone}\n"
        report += f"Recommended Action: {action}\n"
        
        return report
    
    def _get_connection(self):
        """Get a database connection"""
        return sqlite3.connect(self.db_path)
    
    def _get_current_time(self):
        """Get current time as ISO string"""
        return datetime.now().isoformat()
