"""Integration module for the partnership engine"""
import asyncio
import logging
from typing import List, Dict, Optional, Set
from datetime import datetime, timedelta
import json
import os

from .models import PartnershipEvent, EventType
from .apis import EdgarClient, USASpendingClient, SAMGovClient
from .entity_resolver import EntityResolver
from .config import PartnershipConfig

class PartnershipEngine:
    """Main integration class for the partnership engine"""
    
    def __init__(self, db_connection=None):
        """Initialize the partnership engine"""
        self.logger = logging.getLogger(__name__)
        self.db_connection = db_connection
        
        # Initialize API clients
        self.edgar_client = EdgarClient()
        self.usaspending_client = USASpendingClient()
        # Initialize SAMGovClient with API key from config if available
        sam_api_key = os.getenv('SAM_GOV_API_KEY', '')
        self.sam_gov_client = SAMGovClient(sam_api_key) if sam_api_key else None
        
        # Initialize entity resolver
        self.entity_resolver = EntityResolver(db_connection)
        
        # State for deduplication
        self.processed_event_ids: Set[str] = set()
        self.seen_hashes: Set[int] = set()
        
        # Load state if it exists
        self._load_state()
    
    def _load_state(self):
        """Load processed event IDs from disk"""
        try:
            if os.path.exists('partnership_engine_state.json'):
                with open('partnership_engine_state.json', 'r') as f:
                    state = json.load(f)
                    self.processed_event_ids = set(state.get('processed_event_ids', []))
                    self.seen_hashes = set(state.get('seen_hashes', []))
        except Exception as e:
            self.logger.error(f"Failed to load state: {e}")
    
    def _save_state(self):
        """Save processed event IDs to disk"""
        try:
            state = {
                'processed_event_ids': list(self.processed_event_ids),
                'seen_hashes': list(self.seen_hashes),
                'last_updated': datetime.utcnow().isoformat()
            }
            with open('partnership_engine_state.json', 'w') as f:
                json.dump(state, f)
        except Exception as e:
            self.logger.error(f"Failed to save state: {e}")
    
    def _is_duplicate(self, event: PartnershipEvent) -> bool:
        """Check if we've seen this event before"""
        # Create a unique hash based on the event's identifying characteristics
        event_hash = hash((
            event.event_type,
            event.primary_company,
            tuple(sorted(cp.name for cp in event.counterparties)),
            event.announced_date.isoformat() if event.announced_date else '',
            event.financials.amount if event.financials.amount else 0
        ))
        
        if event_hash in self.seen_hashes:
            return True
            
        self.seen_hashes.add(event_hash)
        return False
    
    def _calculate_impact_score(self, event: PartnershipEvent) -> float:
        """Calculate an impact score for the event"""
        score = 0.0
        
        # Base score based on event type
        if event.event_type == EventType.GOV_CONTRACT:
            score += 6.0
        elif event.event_type == EventType.PARTNERSHIP:
            score += 4.0
        else:
            score += 3.0
        
        # Boost for financial impact
        if event.financials and event.financials.amount:
            if event.financials.amount >= 1_000_000_000:  # $1B+
                score += 3.0
            elif event.financials.amount >= 100_000_000:  # $100M+
                score += 2.0
            elif event.financials.amount >= 10_000_000:  # $10M+
                score += 1.0
        
        # Boost for exclusivity
        if event.contract and hasattr(event.contract, 'is_exclusive') and event.contract.is_exclusive:
            score += 2.0
        
        # Cap the score at 10
        return min(score, 10.0)
    
    async def _process_events(self, events: List[PartnershipEvent]) -> List[PartnershipEvent]:
        """Process and filter events"""
        processed = []
        
        for event in events:
            # Skip duplicates
            if self._is_duplicate(event):
                continue
            
            # Calculate impact score
            event.impact_score = self._calculate_impact_score(event)
            
            # Only include events above the minimum impact threshold
            if event.impact_score >= PartnershipConfig.MIN_IMPACT_SCORE:
                processed.append(event)
                self.processed_event_ids.add(event.event_id)
        
        return processed
    
    async def _scan_edgar(self, ticker: str) -> List[PartnershipEvent]:
        """Scan SEC EDGAR for partnership events"""
        self.logger.info(f"Scanning EDGAR for {ticker}...")
        try:
            # Get recent filings
            filings = await self.edgar_client.get_company_filings(ticker)
            
            # Filter for relevant forms (8-K, 10-K, 10-Q, etc.)
            relevant_forms = ['8-K', '10-K', '10-Q', '6-K']
            filings = [f for f in filings if f.get('form') in relevant_forms]
            
            # Process filings to extract events
            events = []
            for filing in filings:
                try:
                    # Extract text and look for partnership/contract patterns
                    filing_text = await self.edgar_client.get_filing_text(filing['accession_number'])
                    
                    # Here you would add logic to parse the filing text and extract events
                    # This is a simplified example
                    if 'strategic partnership' in filing_text.lower():
                        event = PartnershipEvent(
                            event_type=EventType.PARTNERSHIP,
                            source="EDGAR",
                            source_id=f"edgar_{filing['accession_number']}",
                            primary_company=ticker,
                            announced_date=datetime.strptime(filing['filing_date'], '%Y-%m-%d'),
                            description=f"Strategic partnership mentioned in {filing['form']} filing",
                            url=f"https://www.sec.gov/Archives/edgar/data/{filing['cik']}/{filing['accession_number'].replace('-', '')}/{filing['primary_document']}",
                            confidence=0.8
                        )
                        events.append(event)
                        
                except Exception as e:
                    self.logger.error(f"Error processing EDGAR filing {filing.get('accession_number')}: {e}")
            
            return events
            
        except Exception as e:
            self.logger.error(f"Error scanning EDGAR for {ticker}: {e}")
            return []
    
    async def _scan_usaspending(self, ticker: str) -> List[PartnershipEvent]:
        """Scan USAspending for government contracts"""
        self.logger.info(f"Scanning USAspending for {ticker}...")
        try:
            # Get recent awards
            awards = await self.usaspending_client.get_contract_awards(ticker)
            
            # Convert to PartnershipEvent objects
            events = []
            for award in awards:
                try:
                    event = PartnershipEvent(
                        event_type=EventType.GOV_CONTRACT,
                        source="USAspending",
                        source_id=award.get('award_id', ''),
                        primary_company=ticker,
                        announced_date=datetime.strptime(award['signed_date'], '%Y-%m-%d'),
                        title=f"Government Contract: {award.get('description', '')}",
                        description=award.get('description', ''),
                        financials={
                            'amount': float(award.get('total_obligation', 0)),
                            'currency': 'USD',
                            'term_years': (datetime.strptime(award['end_date'], '%Y-%m-%d').year - 
                                          datetime.strptime(award['start_date'], '%Y-%m-%d').year) if 'start_date' in award and 'end_date' in award else None
                        },
                        contract={
                            'contract_number': award.get('award_id'),
                            'agency': award.get('awarding_agency', {}).get('name'),
                            'naics': award.get('naics')
                        },
                        confidence=0.9
                    )
                    events.append(event)
                except Exception as e:
                    self.logger.error(f"Error processing USAspending award {award.get('award_id')}: {e}")
            
            return events
            
        except Exception as e:
            self.logger.error(f"Error scanning USAspending for {ticker}: {e}")
            return []
    
    async def scan_ticker(self, ticker: str) -> List[PartnershipEvent]:
        """Scan all sources for a given ticker"""
        # Run all scans in parallel
        results = await asyncio.gather(
            self._scan_edgar(ticker),
            self._scan_usaspending(ticker),
            # Add other scanners here
            return_exceptions=True
        )
        
        # Flatten results and filter out exceptions
        all_events = []
        for result in results:
            if isinstance(result, list):
                all_events.extend(result)
            elif isinstance(result, Exception):
                self.logger.error(f"Error in scanner: {result}")
        
        # Process and deduplicate events
        processed_events = await self._process_events(all_events)
        
        # Save state
        self._save_state()
        
        return processed_events
    
    def format_alert(self, event: PartnershipEvent) -> str:
        """Format an event as an alert message"""
        # Format the amount if present
        amount_str = ""
        if event.financials and event.financials.amount:
            if event.financials.amount >= 1_000_000_000:
                amount_str = f"${event.financials.amount/1_000_000_000:.2f}B"
            elif event.financials.amount >= 1_000_000:
                amount_str = f"${event.financials.amount/1_000_000:.2f}M"
            else:
                amount_str = f"${event.financials.amount:,.2f}"
        
        # Format counterparties
        counterparties = ", ".join([cp.name for cp in event.counterparties])
        
        # Build the message
        lines = [
            f"🚨 *{event.primary_company} - {event.event_type.value.upper()} DETECTED* 🚨",
            f"*Event Type:* {event.event_type.value.replace('_', ' ').title()}",
            f"*Partners:* {counterparties}",
        ]
        
        if amount_str:
            lines.append(f"*Amount:* {amount_str}")
        
        if event.contract and event.contract.agency:
            lines.append(f"*Agency:* {event.contract.agency}")
        
        if event.announced_date:
            lines.append(f"*Date:* {event.announced_date.strftime('%Y-%m-%d')}")
        
        if event.url:
            lines.append(f"*Source:* [Link]({event.url})")
        
        if hasattr(event, 'impact_score'):
            lines.append(f"*Impact Score:* {event.impact_score:.1f}/10.0")
        
        return "\n".join(lines)


async def monitor_tickers(tickers: List[str], interval_minutes: int = 60):
    """Continuously monitor the given tickers for partnership events"""
    engine = PartnershipEngine()
    
    while True:
        try:
            for ticker in tickers:
                events = await engine.scan_ticker(ticker)
                
                # Process and alert on new events
                for event in events:
                    alert = engine.format_alert(event)
                    print(f"\n{'='*80}\n{alert}\n{'='*80}\n")
                    
                    # Here you would integrate with your alerting system
                    # For example, send to Telegram, Discord, etc.
                    # await send_alert(alert)
            
            # Wait for the next interval
            await asyncio.sleep(interval_minutes * 60)
            
        except Exception as e:
            logging.error(f"Error in monitoring loop: {e}")
            await asyncio.sleep(60)  # Wait a minute before retrying


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m partnership_engine.integration <ticker1> [ticker2 ...]")
        sys.exit(1)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Start monitoring the provided tickers
    asyncio.run(monitor_tickers(sys.argv[1:]))
