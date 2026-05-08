"""Data models for partnership and contract events"""
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Dict, Optional, Any
from enum import Enum
import uuid

class EventType(str, Enum):
    """Types of partnership/contract events"""
    GOV_CONTRACT = "government_contract"
    PARTNERSHIP = "strategic_partnership"
    JOINT_VENTURE = "joint_venture"
    DISTRIBUTION = "distribution_deal"
    LICENSING = "licensing_agreement"
    MOU = "memorandum_of_understanding"
    PILOT = "pilot_program"

@dataclass
class Counterparty:
    """Represents a company involved in a partnership/contract"""
    name: str
    ticker: Optional[str] = None
    cik: Optional[str] = None
    role: Optional[str] = None  # e.g., "awardee", "partner", "customer"
    amount: Optional[float] = None  # Their portion of the deal

@dataclass
class FinancialTerms:
    """Financial details of a partnership/contract"""
    amount: Optional[float] = None
    currency: str = "USD"
    amount_type: str = "total"  # total, annual, base, ceiling, etc.
    term_years: Optional[float] = None
    annual_value: Optional[float] = None
    options: Dict[str, Any] = field(default_factory=dict)  # Additional terms

@dataclass
class ContractDetails:
    """Specific details for government contracts"""
    contract_number: Optional[str] = None
    agency: Optional[str] = None
    naics: Optional[str] = None  # NAICS code
    psc: Optional[str] = None    # Product Service Code
    solicitation_id: Optional[str] = None
    set_aside: Optional[str] = None  # e.g., "SBA", "8(a)"

@dataclass
class PartnershipEvent:
    """A detected partnership or contract event"""
    # Required fields (no default values)
    primary_company: str  # The company we're tracking
    
    # Core identifiers (with defaults)
    event_id: str = field(default_factory=lambda: f"evt_{uuid.uuid4().hex[:8]}")
    event_type: EventType = EventType.PARTNERSHIP
    source: str = "unknown"
    source_id: Optional[str] = None  # Original ID from the source
    
    # Timestamps
    detected_at: datetime = field(default_factory=datetime.utcnow)
    announced_date: Optional[datetime] = None
    effective_date: Optional[datetime] = None
    
    # Collections with default factories
    counterparties: List[Counterparty] = field(default_factory=list)
    raw_data: Dict[str, Any] = field(default_factory=dict)
    
    # Optional fields with None as default
    title: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    contract: Optional[ContractDetails] = None
    
    # Fields with simple defaults
    confidence: float = 0.0
    impact_score: float = 0.0
    
    # Complex fields with default factories
    financials: FinancialTerms = field(default_factory=FinancialTerms)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        result = asdict(self)
        
        # Convert datetime to ISO format
        for dt_field in ['detected_at', 'announced_date', 'effective_date']:
            if dt_value := getattr(self, dt_field):
                result[dt_field] = dt_value.isoformat()
                
        # Convert enums to strings
        if isinstance(self.event_type, Enum):
            result['event_type'] = self.event_type.value
            
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PartnershipEvent':
        """Create from dictionary"""
        # Handle nested dataclasses
        if 'financials' in data and isinstance(data['financials'], dict):
            data['financials'] = FinancialTerms(**data['financials'])
            
        if 'contract' in data and isinstance(data['contract'], dict):
            data['contract'] = ContractDetails(**data['contract'])
            
        if 'counterparties' in data:
            data['counterparties'] = [
                Counterparty(**cp) if isinstance(cp, dict) else cp 
                for cp in data['counterparties']
            ]
            
        # Convert string event type to enum
        if 'event_type' in data and isinstance(data['event_type'], str):
            data['event_type'] = EventType(data['event_type'].lower())
            
        return cls(**data)

# Common patterns for detection
PATTERNS = {
    'GOV_CONTRACT': {
        'patterns': [
            r'(awarded|won|secured)\s+\$?([\d.,]+\s*(?:million|billion|M|B)?)',
            r'contract\s+(?:valued|worth)\s+\$?([\d.,]+\s*(?:million|billion|M|B)?)',
            r'\$([\d.]+[MB])\s+contract',
        ],
        'event_type': EventType.GOV_CONTRACT,
        'confidence_boost': 0.3
    },
    'STRATEGIC_PARTNERSHIP': {
        'patterns': [
            r'(?:partner|teaming|collaborat|alliance|joint venture|JV)\s+(?:with|between|among)',
            r'strategic (?:partnership|collaboration|alliance)',
            r'entered into (?:a|an)?\s*(?:partnership|collaboration|alliance)',
        ],
        'event_type': EventType.PARTNERSHIP,
        'confidence_boost': 0.2
    },
    'EXCLUSIVITY': {
        'patterns': [
            r'(exclusive|sole|preferred)\s+(?:partner|supplier|distributor|reseller)',
            r'(?:awarded|selected)\s+as(?:\s+the)?\s+(?:exclusive|sole|preferred)',
        ],
        'confidence_boost': 0.15
    }
}
