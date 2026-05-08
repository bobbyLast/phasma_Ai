"""
Moonshot Keywords Database
Hidden gem keywords that signal massive potential moves (50-1000%+)
These are rarely used terms that can indicate transformational catalysts
"""

from typing import Dict, List, Any

class MoonshotKeywords:
    """Database of hidden moonshot catalyst keywords"""
    
    # ========== CORPORATE ACTIONS & LEGAL CATALYSTS ==========
    LEGAL_CATALYSTS = {
        'patent granted': {
            'meaning': 'Company gets exclusive rights to technology',
            'potential_move': '+50-200%',
            'sectors': ['biotech', 'tech', 'pharma'],
            'priority': 'HIGH',
            'examples': ['CRSP', 'EDIT', 'NTLA']
        },
        'orphan drug designation': {
            'meaning': 'FDA special status for rare disease treatments',
            'potential_move': '+100-400%',
            'sectors': ['biotech', 'pharma'],
            'priority': 'VERY_HIGH',
            'examples': ['RARE', 'PCYC', 'BIIB']
        },
        'breakthrough therapy': {
            'meaning': 'FDA fast-tracks promising drug',
            'potential_move': '+80-300%',
            'sectors': ['biotech', 'pharma'],
            'priority': 'VERY_HIGH',
            'examples': ['KPTI', 'SRPT']
        },
        'fast track designation': {
            'meaning': 'FDA expedites drug review process',
            'potential_move': '+60-250%',
            'sectors': ['biotech', 'pharma'],
            'priority': 'HIGH'
        },
        'short squeeze': {
            'meaning': 'High short interest + catalyst forces covering',
            'potential_move': '+200-1000%',
            'sectors': ['all'],
            'priority': 'VERY_HIGH',
            'risk': 'EXTREME',
            'examples': ['GME', 'AMC', 'BBBY']
        },
        'gamma squeeze': {
            'meaning': 'Options market makers forced to buy shares',
            'potential_move': '+100-500%',
            'sectors': ['all'],
            'priority': 'HIGH',
            'risk': 'EXTREME'
        }
    }
    
    # ========== SUPPLY CHAIN & PRODUCTION ==========
    SUPPLY_CATALYSTS = {
        'mine commissioning': {
            'meaning': 'Mining operation becomes operational',
            'potential_move': '+100-500%',
            'sectors': ['mining', 'metals', 'lithium'],
            'priority': 'HIGH'
        },
        'first production': {
            'meaning': 'Company produces first commercial product',
            'potential_move': '+80-300%',
            'sectors': ['mining', 'ev', 'manufacturing'],
            'priority': 'HIGH'
        },
        'supply disruption': {
            'meaning': 'Major supplier has production issues',
            'potential_move': '+50-200% for competitors',
            'sectors': ['all'],
            'priority': 'MEDIUM',
            'note': 'Benefits competitors'
        },
        'reserve upgrade': {
            'meaning': 'Company significantly increases estimated resources',
            'potential_move': '+100-300%',
            'sectors': ['mining', 'oil', 'gas'],
            'priority': 'HIGH'
        },
        'feasibility study positive': {
            'meaning': 'Project deemed economically viable',
            'potential_move': '+80-250%',
            'sectors': ['mining', 'energy'],
            'priority': 'HIGH'
        }
    }
    
    # ========== CRYPTO-SPECIFIC CATALYSTS ==========
    CRYPTO_CATALYSTS = {
        'mainnet launch': {
            'meaning': 'Blockchain network goes live',
            'potential_move': '+100-1000%',
            'sectors': ['crypto'],
            'priority': 'VERY_HIGH',
            'examples': ['ETH 2015', 'ADA 2017', 'DOT 2020']
        },
        'hard fork': {
            'meaning': 'Major protocol change requiring update',
            'potential_move': '+50-200% or -50%',
            'sectors': ['crypto'],
            'priority': 'HIGH',
            'risk': 'HIGH'
        },
        'token burn': {
            'meaning': 'Permanent removal of tokens from supply',
            'potential_move': '+50-300%',
            'sectors': ['crypto'],
            'priority': 'HIGH'
        },
        'halving': {
            'meaning': 'Mining reward reduction (Bitcoin)',
            'potential_move': '+100-400%',
            'sectors': ['crypto', 'mining'],
            'priority': 'VERY_HIGH',
            'examples': ['BTC halving cycles']
        },
        'cross-chain integration': {
            'meaning': 'Project integrates with major blockchain',
            'potential_move': '+200-1000%',
            'sectors': ['crypto'],
            'priority': 'VERY_HIGH'
        },
        'liquidity mining launch': {
            'meaning': 'New yield farming opportunities',
            'potential_move': '+100-400%',
            'sectors': ['crypto', 'defi'],
            'priority': 'HIGH',
            'risk': 'HIGH',
            'note': 'Often short-lived'
        }
    }
    
    # ========== GOVERNMENT & REGULATORY ==========
    GOVERNMENT_CATALYSTS = {
        'national security designation': {
            'meaning': 'Company deemed critical to national security',
            'potential_move': '+100-400%',
            'sectors': ['defense', 'cyber', 'mining'],
            'priority': 'VERY_HIGH'
        },
        'defense production act': {
            'meaning': 'Government mandates production',
            'potential_move': '+200-800%',
            'sectors': ['manufacturing', 'defense', 'pharma'],
            'priority': 'VERY_HIGH',
            'examples': ['Vaccine manufacturers 2020']
        },
        'critical minerals list': {
            'meaning': 'Government identifies strategic minerals',
            'potential_move': '+100-300%',
            'sectors': ['mining', 'metals'],
            'priority': 'HIGH'
        },
        'regulatory clarity': {
            'meaning': 'Clear rules established for industry',
            'potential_move': '+50-200%',
            'sectors': ['crypto', 'fintech'],
            'priority': 'HIGH'
        },
        'etf approval': {
            'meaning': 'SEC approves exchange-traded fund',
            'potential_move': '+100-500%',
            'sectors': ['crypto', 'commodities'],
            'priority': 'VERY_HIGH',
            'examples': ['Bitcoin ETF']
        },
        'approves etf': {
            'meaning': 'SEC approves exchange-traded fund',
            'potential_move': '+100-500%',
            'sectors': ['crypto', 'commodities'],
            'priority': 'VERY_HIGH',
            'examples': ['Bitcoin ETF']
        }
    }
    
    # ========== FINANCIAL ENGINEERING ==========
    FINANCIAL_CATALYSTS = {
        'spinoff': {
            'meaning': 'Company separates into independent entities',
            'potential_move': '+50-200% for spinoff',
            'sectors': ['all'],
            'priority': 'HIGH',
            'examples': ['PYPL from EBAY']
        },
        'strategic alternatives': {
            'meaning': 'Code for potential sale/merger',
            'potential_move': '+30-150%',
            'sectors': ['all'],
            'priority': 'HIGH',
            'note': 'CEO letter phrase'
        },
        'substantial undervaluation': {
            'meaning': 'May signal buyback or activist interest',
            'potential_move': '+40-200%',
            'sectors': ['all'],
            'priority': 'MEDIUM'
        },
        'transformative acquisition': {
            'meaning': 'Major M&A that changes business model',
            'potential_move': '+50-300%',
            'sectors': ['all'],
            'priority': 'HIGH'
        },
        'stock buyback': {
            'meaning': 'Company repurchasing own shares',
            'potential_move': '+20-100%',
            'sectors': ['all'],
            'priority': 'MEDIUM'
        }
    }
    
    # ========== SCIENTIFIC BREAKTHROUGHS ==========
    SCIENTIFIC_CATALYSTS = {
        'peer review publication': {
            'meaning': 'Research published in prestigious journal',
            'potential_move': '+100-400%',
            'sectors': ['biotech', 'pharma', 'tech'],
            'priority': 'VERY_HIGH',
            'journals': ['Nature', 'Science', 'The Lancet']
        },
        'clinical trial success': {
            'meaning': 'Trial meets primary endpoint',
            'potential_move': '+150-800%',
            'sectors': ['biotech', 'pharma'],
            'priority': 'VERY_HIGH'
        },
        'phase 3 results': {
            'meaning': 'Final stage trial results',
            'potential_move': '+200-1000%',
            'sectors': ['biotech', 'pharma'],
            'priority': 'VERY_HIGH',
            'risk': 'EXTREME'
        },
        'efficacy rate': {
            'meaning': 'Drug/treatment effectiveness percentage',
            'potential_move': '+200-1000% if >90%',
            'sectors': ['biotech', 'pharma'],
            'priority': 'VERY_HIGH',
            'threshold': '>90% efficacy'
        },
        'breakthrough discovery': {
            'meaning': 'Novel scientific finding',
            'potential_move': '+100-500%',
            'sectors': ['biotech', 'tech', 'energy'],
            'priority': 'HIGH'
        }
    }
    
    # ========== ENERGY & COMMODITY SPECIFIC ==========
    ENERGY_CATALYSTS = {
        'power purchase agreement': {
            'meaning': 'Long-term energy sales contract signed',
            'potential_move': '+50-200%',
            'sectors': ['energy', 'renewable'],
            'priority': 'HIGH'
        },
        'offtake agreement': {
            'meaning': 'Buyer commits to purchase future production',
            'potential_move': '+80-300%',
            'sectors': ['mining', 'energy'],
            'priority': 'HIGH'
        },
        'drilling results': {
            'meaning': 'Positive exploration findings',
            'potential_move': '+100-400%',
            'sectors': ['mining', 'oil', 'gas'],
            'priority': 'HIGH'
        },
        'resource estimate': {
            'meaning': 'Official calculation of mineral reserves',
            'potential_move': '+80-250%',
            'sectors': ['mining'],
            'priority': 'HIGH'
        }
    }
    
    # ========== TECHNICAL PATTERNS (HIDDEN) ==========
    TECHNICAL_PATTERNS = {
        'inverse head and shoulders': {
            'meaning': 'Bullish reversal pattern',
            'potential_move': '+30-150%',
            'sectors': ['all'],
            'priority': 'MEDIUM'
        },
        'cup and handle': {
            'meaning': 'Bullish continuation pattern',
            'potential_move': '+40-200%',
            'sectors': ['all'],
            'priority': 'MEDIUM'
        },
        'falling wedge': {
            'meaning': 'Bullish reversal pattern',
            'potential_move': '+30-120%',
            'sectors': ['all'],
            'priority': 'MEDIUM'
        },
        'bull flag': {
            'meaning': 'Bullish continuation pattern',
            'potential_move': '+20-100%',
            'sectors': ['all'],
            'priority': 'LOW'
        }
    }
    
    @classmethod
    def get_all_keywords(cls) -> List[str]:
        """Get flat list of all moonshot keywords"""
        all_keywords = []
        for category in [
            cls.LEGAL_CATALYSTS,
            cls.SUPPLY_CATALYSTS,
            cls.CRYPTO_CATALYSTS,
            cls.GOVERNMENT_CATALYSTS,
            cls.FINANCIAL_CATALYSTS,
            cls.SCIENTIFIC_CATALYSTS,
            cls.ENERGY_CATALYSTS,
            cls.TECHNICAL_PATTERNS
        ]:
            all_keywords.extend(category.keys())
        return all_keywords
    
    @classmethod
    def get_keyword_info(cls, keyword: str) -> Dict[str, Any]:
        """Get detailed information about a specific keyword"""
        keyword_lower = keyword.lower()
        
        # Search all categories
        for category in [
            cls.LEGAL_CATALYSTS,
            cls.SUPPLY_CATALYSTS,
            cls.CRYPTO_CATALYSTS,
            cls.GOVERNMENT_CATALYSTS,
            cls.FINANCIAL_CATALYSTS,
            cls.SCIENTIFIC_CATALYSTS,
            cls.ENERGY_CATALYSTS,
            cls.TECHNICAL_PATTERNS
        ]:
            if keyword_lower in category:
                return category[keyword_lower]
        
        return None
    
    @classmethod
    def get_high_priority_keywords(cls) -> List[str]:
        """Get only VERY_HIGH priority moonshot keywords"""
        high_priority = []
        
        for category in [
            cls.LEGAL_CATALYSTS,
            cls.SUPPLY_CATALYSTS,
            cls.CRYPTO_CATALYSTS,
            cls.GOVERNMENT_CATALYSTS,
            cls.FINANCIAL_CATALYSTS,
            cls.SCIENTIFIC_CATALYSTS,
            cls.ENERGY_CATALYSTS
        ]:
            for keyword, info in category.items():
                if info.get('priority') == 'VERY_HIGH':
                    high_priority.append(keyword)
        
        return high_priority
    
    @classmethod
    def calculate_moonshot_score(cls, text: str) -> Dict[str, Any]:
        """
        Calculate moonshot potential based on keyword presence
        
        Returns:
            {
                'score': 0-100,
                'keywords_found': [],
                'highest_priority': 'VERY_HIGH/HIGH/MEDIUM/LOW',
                'potential_move': '50-200%',
                'risk_level': 'EXTREME/HIGH/MEDIUM/LOW'
            }
        """
        text_lower = text.lower()
        keywords_found = []
        highest_priority = 'LOW'
        max_potential = 0
        risk_level = 'LOW'
        
        # Check all categories
        for category in [
            cls.LEGAL_CATALYSTS,
            cls.SUPPLY_CATALYSTS,
            cls.CRYPTO_CATALYSTS,
            cls.GOVERNMENT_CATALYSTS,
            cls.FINANCIAL_CATALYSTS,
            cls.SCIENTIFIC_CATALYSTS,
            cls.ENERGY_CATALYSTS,
            cls.TECHNICAL_PATTERNS
        ]:
            for keyword, info in category.items():
                if keyword in text_lower:
                    keywords_found.append({
                        'keyword': keyword,
                        'info': info
                    })
                    
                    # Update highest priority
                    priority = info.get('priority', 'LOW')
                    if priority == 'VERY_HIGH':
                        highest_priority = 'VERY_HIGH'
                    elif priority == 'HIGH' and highest_priority != 'VERY_HIGH':
                        highest_priority = 'HIGH'
                    elif priority == 'MEDIUM' and highest_priority not in ['VERY_HIGH', 'HIGH']:
                        highest_priority = 'MEDIUM'
                    
                    # Extract max potential move
                    potential_str = info.get('potential_move', '+0%')
                    try:
                        # Extract max percentage (e.g., "+100-400%" -> 400)
                        max_pct = int(potential_str.split('-')[-1].replace('%', '').replace('+', ''))
                        max_potential = max(max_potential, max_pct)
                    except:
                        pass
                    
                    # Update risk level
                    keyword_risk = info.get('risk', 'LOW')
                    if keyword_risk == 'EXTREME':
                        risk_level = 'EXTREME'
                    elif keyword_risk == 'HIGH' and risk_level != 'EXTREME':
                        risk_level = 'HIGH'
        
        # Calculate score (0-100)
        priority_scores = {
            'VERY_HIGH': 100,
            'HIGH': 75,
            'MEDIUM': 50,
            'LOW': 25
        }
        
        base_score = priority_scores.get(highest_priority, 0)
        keyword_bonus = min(len(keywords_found) * 10, 30)  # Max +30 for multiple keywords
        
        final_score = min(base_score + keyword_bonus, 100)
        
        return {
            'score': final_score,
            'keywords_found': keywords_found,
            'highest_priority': highest_priority,
            'potential_move': f'+{max_potential}%' if max_potential > 0 else 'Unknown',
            'risk_level': risk_level,
            'is_moonshot': final_score >= 75
        }


# Quick access lists for integration
MOONSHOT_KEYWORDS_LIST = MoonshotKeywords.get_all_keywords()
HIGH_PRIORITY_MOONSHOTS = MoonshotKeywords.get_high_priority_keywords()

# For easy import
__all__ = ['MoonshotKeywords', 'MOONSHOT_KEYWORDS_LIST', 'HIGH_PRIORITY_MOONSHOTS']
