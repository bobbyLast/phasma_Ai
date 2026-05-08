"""API clients for partnership and contract data sources"""

# Import all API clients for easier access
from .edgar import EdgarClient
from .usaspending import USASpendingClient
from .sam_gov import SAMGovClient

__all__ = ['EdgarClient', 'USASpendingClient', 'SAMGovClient']
