"""SAM.gov API client for contract opportunities and awards"""
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
import logging
from .base_client import BaseAPIClient
from ..models import PartnershipEvent, EventType, Counterparty, FinancialTerms, ContractDetails

class SAMGovClient(BaseAPIClient):
    """Client for interacting with the SAM.gov API"""
    
    BASE_URL = "https://api.sam.gov/opportunities/v2"
    
    def __init__(self, api_key: str):
        """Initialize the SAM.gov client"""
        if not api_key:
            raise ValueError("API key is required for SAM.gov")
            
        super().__init__(self.BASE_URL, api_key=api_key, rate_limit=2)
        self.session.headers.update({
            'Accept': 'application/json',
        })
    
    def search_opportunities(self, keywords: List[str] = None,
                           naics_codes: List[str] = None,
                           psc_codes: List[str] = None,
                           posted_from: datetime = None,
                           posted_to: datetime = None,
                           opportunity_type: str = None,
                           set_aside: str = None,
                           limit: int = 50) -> List[Dict]:
        """
        Search for contract opportunities on SAM.gov
        
        Args:
            keywords: List of keywords to search for
            naics_codes: List of NAICS codes to filter by
            psc_codes: List of PSC codes to filter by
            posted_from: Only return opportunities posted after this date
            posted_to: Only return opportunities posted before this date
            opportunity_type: Type of opportunity (e.g., 's', 'o', 'k', 'r')
            set_aside: Set-aside code (e.g., 'SBA', '8A')
            limit: Maximum number of results to return (max 1000)
            
        Returns:
            List of opportunity dictionaries
        """
        params = {
            'api_key': self.api_key,
            'limit': min(limit, 1000),  # API max is 1000
            'offset': 0
        }
        
        # Add filters
        if keywords:
            params['q'] = ' '.join(keywords)
        if naics_codes:
            params['naics'] = ','.join(naics_codes)
        if psc_codes:
            params['psc'] = ','.join(psc_codes)
        if posted_from:
            params['postedFrom'] = posted_from.strftime('%m/%d/%Y')
        if posted_to:
            params['postedTo'] = posted_to.strftime('%m/%d/%Y')
        if opportunity_type:
            params['noticeType'] = opportunity_type
        if set_aside:
            params['setAside'] = set_aside
            
        # Make the request
        response = self.get("search", params=params)
        return response.get("opportunitiesData", []) if response else []
    
    def get_award_notices(self, date_from: datetime = None,
                         date_to: datetime = None,
                         limit: int = 100) -> List[Dict]:
        """
        Get award notices from SAM.gov
        
        Args:
            date_from: Only return awards after this date
            date_to: Only return awards before this date
            limit: Maximum number of results to return
            
        Returns:
            List of award notice dictionaries
        """
        params = {
            'api_key': self.api_key,
            'limit': min(limit, 1000),
            'offset': 0,
            'noticeType': 'a'
        }
        
        # Add date filters
        if date_from:
            params['publishedFrom'] = date_from.strftime('%m/%d/%Y')
        if date_to:
            params['publishedTo'] = date_to.strftime('%m/%d/%Y')
            
        # Make the request
        response = self.get("search", params=params)
        return response.get("opportunitiesData", []) if response else []
    
    def get_partnership_events(self, company_name: str = None,
                             lookback_days: int = 30) -> List[PartnershipEvent]:
        """
        Get partnership events from SAM.gov data
        
        Args:
            company_name: Name of the company to search for
            lookback_days: Number of days to look back
            
        Returns:
            List of PartnershipEvent objects
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=lookback_days)
        
        events = []
        
        # Search for awards to the company
        if company_name:
            awards = self.get_award_notices(date_from=start_date, date_to=end_date)
            
            for award in awards:
                try:
                    # Check if this award is relevant to our company
                    awardee = award.get('awardee', '').lower()
                    if company_name.lower() not in awardee:
                        continue
                        
                    # Extract contract details
                    amount = self._parse_amount(award.get('awardAmount', '0'))
                    if amount <= 0:
                        continue
                        
                    # Create contract details
                    contract_details = ContractDetails(
                        contract_number=award.get('awardID'),
                        agency=award.get('contractingOfficeAgencyID'),
                        naics=award.get('naics'),
                        psc=award.get('productServiceCode'),
                        solicitation_id=award.get('solicitationID'),
                        set_aside=award.get('typeOfSetAside')
                    )
                    
                    # Create financial terms
                    financials = FinancialTerms(
                        amount=amount,
                        currency="USD",
                        amount_type="awarded"
                    )
                    
                    # Create the event
                    event = PartnershipEvent(
                        event_type=EventType.GOV_CONTRACT,
                        source='sam_gov',
                        source_id=award.get('noticeID'),
                        announced_date=datetime.strptime(award.get('postedDate', ''), '%m/%d/%Y'),
                        primary_company=award.get('awardee', ''),
                        title=f"Award Notice: {award.get('title', '')}",
                        description=award.get('description', ''),
                        financials=financials,
                        contract=contract_details,
                        confidence=0.85,
                        impact_score=self._calculate_impact_score(amount)
                    )
                    
                    events.append(event)
                    
                except Exception as e:
                    self.logger.error(f"Error processing award {award.get('noticeID')}: {e}")
                    continue
                    
        return events
    
    def _parse_amount(self, amount_str: str) -> float:
        """Parse amount string into float"""
        if not amount_str:
            return 0.0
            
        try:
            # Remove non-numeric characters except decimal point
            clean = ''.join(c for c in amount_str if c.isdigit() or c in '.,')
            
            # Handle European format (1.234,56) vs US (1,234.56)
            if ',' in clean and '.' in clean:
                if clean.find(',') < clean.find('.'):  # 1,234.56 format
                    clean = clean.replace(',', '')
                else:  # 1.234,56 format
                    clean = clean.replace('.', '').replace(',', '.')
            
            return float(clean)
        except (ValueError, AttributeError):
            return 0.0
    
    def _calculate_impact_score(self, amount: float) -> float:
        """Calculate impact score based on contract amount"""
        if amount >= 100000000:  # $100M+
            return 9.0
        elif amount >= 50000000:  # $50M-$100M
            return 8.0 + (amount - 50000000) / 50000000
        elif amount >= 10000000:  # $10M-$50M
            return 7.0 + (amount - 10000000) / 40000000 * 1.0
        elif amount >= 1000000:  # $1M-$10M
            return 6.0 + (amount - 1000000) / 9000000 * 1.0
        else:  # Under $1M
            return 5.0 + amount / 1000000
