"""Entity resolution for company names and tickers"""
from typing import Dict, List, Optional, Tuple
import pandas as pd
from rapidfuzz import fuzz
import logging
from .config import PartnershipConfig

class EntityResolver:
    """Resolves company names to tickers and other identifiers"""
    
    def __init__(self, db_connection=None):
        self.logger = logging.getLogger(__name__)
        self.db_connection = db_connection
        self.ticker_map = self._load_ticker_map()
        
    def _load_ticker_map(self) -> pd.DataFrame:
        """Load ticker-company mapping with aliases"""
        try:
            # Try to load from database if connection exists
            if self.db_connection:
                query = """
                    SELECT ticker, company_name, aliases, cik, cusip, sector, industry 
                    FROM company_reference
                """
                return pd.read_sql(query, self.db_connection)
                
            # Fallback to CSV if no DB connection
            # TODO: Add path to your reference data
            return pd.read_csv('data/company_reference.csv')
            
        except Exception as e:
            self.logger.error(f"Failed to load ticker map: {e}")
            return pd.DataFrame(columns=['ticker', 'company_name', 'aliases', 'cik', 'cusip'])
    
    def resolve(self, name: str, threshold: float = None) -> List[Dict]:
        """
        Fuzzy match company name to ticker and identifiers
        
        Args:
            name: Company name to resolve
            threshold: Minimum match score (0-1)
            
        Returns:
            List of matches with scores and metadata
        """
        if not name or not isinstance(name, str):
            return []
            
        threshold = threshold or PartnershipConfig.FUZZY_MATCH_THRESHOLD
        matches = []
        
        # Clean the input name
        clean_name = self._clean_company_name(name)
        
        for _, row in self.ticker_map.iterrows():
            # Check company name
            company_name = str(row['company_name']).lower()
            score = fuzz.token_sort_ratio(clean_name.lower(), company_name) / 100
            
            # Check aliases if any
            alias_scores = [score]
            if pd.notna(row.get('aliases')):
                aliases = str(row['aliases']).split('|')
                alias_scores.extend([
                    fuzz.token_sort_ratio(clean_name.lower(), a.strip().lower()) / 100 
                    for a in aliases if a.strip()
                ])
            
            best_score = max(alias_scores)
            if best_score >= threshold:
                matches.append({
                    'ticker': row['ticker'],
                    'company_name': row['company_name'],
                    'score': best_score,
                    'cik': row.get('cik'),
                    'cusip': row.get('cusip'),
                    'sector': row.get('sector'),
                    'industry': row.get('industry'),
                    'match_type': 'company_name' if best_score == score else 'alias'
                })
        
        return sorted(matches, key=lambda x: x['score'], reverse=True)
    
    def resolve_cik(self, cik: str) -> Optional[Dict]:
        """Resolve CIK to company info"""
        if not cik:
            return None
            
        matches = self.ticker_map[self.ticker_map['cik'] == cik]
        if not matches.empty:
            return matches.iloc[0].to_dict()
        return None
    
    def _clean_company_name(self, name: str) -> str:
        """Clean company name for matching"""
        if not name:
            return ""
            
        # Remove common suffixes and clean up
        suffixes = [
            'inc', 'llc', 'ltd', 'corp', 'corporation', 'limited', 'holding',
            'holdings', 'group', 'technologies', 'incorporated', 'plc', 'co',
            'company', '& co', '& company', '& sons', '& partners', 'the '
        ]
        
        clean = name.lower().strip()
        for suffix in suffixes:
            clean = re.sub(rf'\s+{re.escape(suffix)}\.?$', '', clean)
            clean = re.sub(rf'\s+{re.escape(suffix)}\s+', ' ', clean)
            
        return clean.strip()

# Singleton instance for easy import
resolver = EntityResolver()
