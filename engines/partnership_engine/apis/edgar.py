"""SEC EDGAR API client for partnership and contract data"""
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import re
from .base_client import BaseAPIClient
from ..models import PartnershipEvent, EventType, Counterparty, FinancialTerms, ContractDetails

class EdgarClient(BaseAPIClient):
    """Client for interacting with the SEC EDGAR API"""
    
    BASE_URL = "https://data.sec.gov/submissions"
    
    def __init__(self, user_agent: str = "PhasmaAI (your-email@example.com)"):
        """Initialize the EDGAR client"""
        super().__init__(self.BASE_URL, rate_limit=10)
        self.session.headers['User-Agent'] = user_agent
    
    def get_company_filings(self, cik: str, form_types: List[str] = None, 
                          start_date: datetime = None, 
                          end_date: datetime = None) -> List[Dict]:
        """
        Get filings for a company by CIK
        
        Args:
            cik: Company CIK (with or without leading zeros)
            form_types: List of form types to filter by (e.g., ['8-K', '10-K'])
            start_date: Only return filings after this date
            end_date: Only return filings before this date
            
        Returns:
            List of filing dictionaries
        """
        # Normalize CIK (10 digits, leading zeros)
        cik = str(cik).zfill(10)
        
        # Get company filings
        company_json = self.get(f"CIK{cik}.json")
        if not company_json or 'filings' not in company_json:
            return []
            
        # Filter and process filings
        filings = company_json['filings'].get('recent', {})
        if not filings:
            return []
            
        # Convert to list of dicts with proper field names
        result = []
        for i in range(len(filings.get('accessionNumber', []))):
            filing = {
                'accession_number': filings['accessionNumber'][i],
                'filing_date': filings['filingDate'][i],
                'report_date': filings['reportDate'][i],
                'form': filings['form'][i],
                'primary_document': filings['primaryDocument'][i],
                'items': filings.get('items', [''])[i],
                'size': int(filings.get('size', ['0'])[i]),
                'url': f"https://www.sec.gov/Archives/edgar/data/{cik}/{filings['accessionNumber'][i].replace('-', '')}/{filings['primaryDocument'][i]}"
            }
            
            # Apply filters
            if form_types and filing['form'] not in form_types:
                continue
                
            filing_date = datetime.strptime(filing['filing_date'], '%Y-%m-%d')
            if start_date and filing_date < start_date:
                continue
            if end_date and filing_date > end_date:
                continue
                
            result.append(filing)
            
        return result
    
    def extract_partnership_events(self, filing: Dict) -> List[PartnershipEvent]:
        """
        Extract partnership/contract events from an EDGAR filing
        
        Args:
            filing: Filing dictionary from get_company_filings()
            
        Returns:
            List of PartnershipEvent objects
        """
        events = []
        
        # 8-K Item 1.01: Entry into a Material Definitive Agreement
        if filing['form'] == '8-K' and '1.01' in filing['items']:
            # In a real implementation, we would:
            # 1. Download the filing text
            # 2. Parse it to extract relevant sections
            # 3. Create PartnershipEvent objects
            # For now, we'll return a placeholder event
            
            event = PartnershipEvent(
                event_type=EventType.PARTNERSHIP,
                source='edgar',
                source_id=f"edgar_{filing['accession_number']}",
                announced_date=datetime.strptime(filing['filing_date'], '%Y-%m-%d'),
                primary_company="",  # Would be filled in by the caller
                title=f"8-K Filing: {filing['primary_document']}",
                url=filing['url'],
                confidence=0.8,
                impact_score=7.5
            )
            events.append(event)
            
        # 10-K Item 1: Business (for long-term contracts)
        elif filing['form'] == '10-K':
            # Similar parsing logic would go here
            pass
            
        return events
    
    def search_partnerships(self, cik: str, lookback_days: int = 30) -> List[PartnershipEvent]:
        """
        Search for partnership/contract events for a company
        
        Args:
            cik: Company CIK
            lookback_days: Number of days to look back
            
        Returns:
            List of PartnershipEvent objects
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=lookback_days)
        
        # Get relevant filings
        filings = self.get_company_filings(
            cik=cik,
            form_types=['8-K', '10-K', '10-Q', 'S-4'],
            start_date=start_date,
            end_date=end_date
        )
        
        # Extract events from filings
        events = []
        for filing in filings:
            try:
                events.extend(self.extract_partnership_events(filing))
            except Exception as e:
                self.logger.error(f"Error processing filing {filing.get('accession_number')}: {e}")
                continue
                
        return events
