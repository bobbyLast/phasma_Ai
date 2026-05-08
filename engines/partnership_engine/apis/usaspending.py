"""USAspending API client for government contract data"""
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import logging
from .base_client import BaseAPIClient
from ..models import PartnershipEvent, EventType, Counterparty, FinancialTerms, ContractDetails

class USASpendingClient(BaseAPIClient):
    """Client for interacting with the USAspending API"""
    
    BASE_URL = "https://api.usaspending.gov/api/v2"
    
    def __init__(self, api_key: str = None):
        """Initialize the USAspending client"""
        super().__init__(self.BASE_URL, api_key=api_key, rate_limit=5)
    
    def search_contracts(self, recipient_name: str = None, 
                        recipient_id: str = None,
                        naics_codes: List[str] = None,
                        psc_codes: List[str] = None,
                        date_signed_after: datetime = None,
                        date_signed_before: datetime = None,
                        min_amount: float = None,
                        max_amount: float = None,
                        limit: int = 100) -> List[Dict]:
        """
        Search for government contracts
        
        Args:
            recipient_name: Name of the recipient (company)
            recipient_id: Unique Entity ID (UEI) of the recipient
            naics_codes: List of NAICS codes to filter by
            psc_codes: List of PSC codes to filter by
            date_signed_after: Only return contracts signed after this date
            date_signed_before: Only return contracts signed before this date
            min_amount: Minimum contract amount
            max_amount: Maximum contract amount
            limit: Maximum number of results to return
            
        Returns:
            List of contract dictionaries
        """
        # Build filters
        filters = {
            "filters": {
                "time_period": [],
                "award_type_codes": ["A", "B", "C", "D"],  # Contracts only
            },
            "fields": [
                "award_id",
                "awarding_agency",
                "awarding_sub_agency",
                "recipient_name",
                "recipient_uei",
                "period_of_performance_start_date",
                "period_of_performance_current_end_date",
                "total_obligation",
                "base_and_all_options_value",
                "naics_code",
                "naics_description",
                "product_or_service_code",
                "product_or_service_description",
                "awarding_office_name",
                "description",
                "solicitation_identifier"
            ],
            "limit": min(limit, 100),  # API max is 100
            "page": 1,
            "sort": "-action_date"
        }
        
        # Add recipient filter
        if recipient_name:
            filters["filters"]["recipient_search_text"] = [recipient_name]
        if recipient_id:
            filters["filters"]["recipient_id"] = recipient_id
            
        # Add date filters
        if date_signed_after or date_signed_before:
            date_filter = {}
            if date_signed_after:
                date_filter["greater_than"] = date_signed_after.strftime("%Y-%m-%d")
            if date_signed_before:
                date_filter["less_than"] = date_signed_before.strftime("%Y-%m-%d")
            filters["filters"]["time_period"] = [{"date_type": "action_date", **date_filter}]
            
        # Add amount filters
        if min_amount is not None or max_amount is not None:
            amount_filter = {}
            if min_amount is not None:
                amount_filter["lower_bound"] = min_amount
            if max_amount is not None:
                amount_filter["upper_bound"] = max_amount
            filters["filters"]["award_amounts"] = [amount_filter]
            
        # Add NAICS/PSC filters
        if naics_codes:
            filters["filters"]["naics_codes"] = [{"requires": [["A", code]]} for code in naics_codes]
        if psc_codes:
            filters["filters"]["product_or_service_codes"] = psc_codes
            
        # Make the request
        response = self.post("search/spending_by_award/", data=filters)
        return response.get("results", []) if response else []
    
    def get_contract_events(self, recipient_name: str = None, 
                          recipient_id: str = None,
                          lookback_days: int = 30) -> List[PartnershipEvent]:
        """
        Get partnership events from contract awards
        
        Args:
            recipient_name: Name of the recipient (company)
            recipient_id: Unique Entity ID (UEI) of the recipient
            lookback_days: Number of days to look back
            
        Returns:
            List of PartnershipEvent objects
        """
        if not recipient_name and not recipient_id:
            raise ValueError("Either recipient_name or recipient_id must be provided")
            
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=lookback_days)
        
        # Search for contracts
        contracts = self.search_contracts(
            recipient_name=recipient_name,
            recipient_id=recipient_id,
            date_signed_after=start_date,
            date_signed_before=end_date,
            min_amount=100000  # $100K minimum
        )
        
        # Convert to PartnershipEvent objects
        events = []
        for contract in contracts:
            try:
                amount = float(contract.get('total_obligation', 0))
                if amount <= 0:
                    continue
                    
                # Create contract details
                contract_details = ContractDetails(
                    contract_number=contract.get('award_id'),
                    agency=contract.get('awarding_agency'),
                    naics=contract.get('naics_code'),
                    psc=contract.get('product_or_service_code'),
                    solicitation_id=contract.get('solicitation_identifier')
                )
                
                # Create financial terms
                financials = FinancialTerms(
                    amount=amount,
                    currency="USD",
                    amount_type="obligated",
                    annual_value=amount / 5  # Simple estimate
                )
                
                # Create the event
                event = PartnershipEvent(
                    event_type=EventType.GOV_CONTRACT,
                    source='usaspending',
                    source_id=contract.get('award_id'),
                    announced_date=datetime.strptime(contract.get('period_of_performance_start_date', ''), '%Y-%m-%d'),
                    primary_company=contract.get('recipient_name', ''),
                    title=f"Contract Award: {contract.get('awarding_agency', 'Unknown Agency')}",
                    description=contract.get('description', ''),
                    financials=financials,
                    contract=contract_details,
                    confidence=0.9 if amount > 1000000 else 0.7,
                    impact_score=self._calculate_impact_score(amount)
                )
                
                events.append(event)
                
            except Exception as e:
                self.logger.error(f"Error processing contract {contract.get('award_id')}: {e}")
                continue
                
        return events
    
    def _calculate_impact_score(self, amount: float) -> float:
        """Calculate impact score based on contract amount"""
        if amount >= 100000000:  # $100M+
            return 9.5
        elif amount >= 10000000:  # $10M-$100M
            return 8.0 + min((amount - 10000000) / 90000000, 1.0) * 1.5
        elif amount >= 1000000:  # $1M-$10M
            return 7.0 + min((amount - 1000000) / 9000000, 1.0) * 1.0
        else:  # Under $1M
            return 5.0 + min(amount / 1000000, 1.0) * 2.0
