"""
Form 4 Parser - Parse Form 4 filings with transaction code analysis

Filters meaningful insider buys from noise by analyzing SEC transaction codes.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import re
import numpy as np


class Form4Parser:
    """Parse Form 4 filings with transaction code analysis"""
    
    # SEC transaction codes and their meanings
    TRANSACTION_CODES = {
        'P': 'Open market purchase',      # HIGH CONFIDENCE - Real buying
        'S': 'Open market sale',         # AVOID - Insider selling
        'M': 'Exercise/Conversion',      # EXCLUDE - Not cash purchase
        'G': 'Gift/Acquisition',         # NEUTRAL - May not be conviction
        'A': 'Grant/Award',              # EXCLUDE - Compensation
        'F': 'Payment of exercise price', # EXCLUDE - Exercise related
        'D': 'Disposition',              # AVOID - Getting rid of shares
        'C': 'Conversion',               # EXCLUDE - Converting options
        'E': 'Expiration of short position', # EXCLUDE - Options related
        'H': 'Conversion of derivative', # EXCLUDE - Derivative conversion
        'I': 'Disposition of derivative to issuer', # EXCLUDE
        'J': 'Other acquisition or disposition', # MANUAL REVIEW
        'K': 'Equity swap for derivative', # EXCLUDE
        'L': 'Small acquisition',        # MANUAL REVIEW - Check size
        'M': 'Exercise or conversion',   # EXCLUDE - Already listed
        'N': 'Equity swap for derivative', # EXCLUDE
        'O': 'Other',                   # MANUAL REVIEW
        'P': 'Open market purchase',      # HIGH CONFIDENCE - Already listed
        'Q': 'Discretionary transaction', # MANUAL REVIEW
        'R': 'Derivative transaction',   # EXCLUDE
        'S': 'Open market sale',         # AVOID - Already listed
        'U': 'Disposition of derivative', # EXCLUDE
        'V': 'Transaction by trustee',   # MANUAL REVIEW
        'W': 'Acquisition or disposition by will', # NEUTRAL
        'X': 'Intra-firm transaction',   # EXCLUDE - Internal transfer
        'Y': 'Intra-firm transaction',   # EXCLUDE - Internal transfer
        'Z': 'Intra-firm transaction',   # EXCLUDE - Internal transfer
    }
    
    def __init__(self, min_amount: float = 500000):
        """
        Initialize Form 4 parser
        
        Args:
            min_amount: Minimum transaction amount in dollars
        """
        self.min_amount = min_amount
        self.footnote_patterns = [
            r'10b5-1',
            r'rule\s*10b5',
            r'pre-arranged',
            r'scheduled',
            r'trading\s*plan'
        ]
    
    def parse_transaction(self, transaction: Dict) -> Optional[Dict]:
        """
        Extract meaningful insider buys from transaction data
        
        Args:
            transaction: Raw transaction data from Form 4
            
        Returns:
            Parsed signal if meaningful, None otherwise
        """
        # Extract transaction code
        code = transaction.get('transaction_code', '').upper()
        amount = transaction.get('amount', 0)
        
        # Only count open market purchases (Code P)
        if code != 'P':
            return None
            
        # Must meet minimum amount
        if amount < self.min_amount:
            return None
            
        # Exclude 10b5-1 planned trades
        if self.is_10b5_1_plan(transaction):
            return None
            
        # Calculate confidence based on amount
        confidence = min(amount / 5000000, 1.0)  # $5M = 100% confidence
        
        return {
            'type': 'meaningful_buy',
            'amount': amount,
            'confidence': confidence,
            'transaction_code': code,
            'insider_name': transaction.get('insider_name', ''),
            'title': transaction.get('title', ''),
            'date': transaction.get('date'),
            'price': transaction.get('price', 0)
        }
    
    def is_10b5_1_plan(self, transaction: Dict) -> bool:
        """
        Check if transaction is part of a 10b5-1 trading plan
        
        Args:
            transaction: Transaction data
            
        Returns:
            True if this appears to be a planned trade
        """
        # Check footnotes for 10b5-1 indicators
        footnote = transaction.get('footnote', '').lower()
        
        for pattern in self.footnote_patterns:
            if re.search(pattern, footnote):
                return True
        
        # Check remarks field
        remarks = transaction.get('remarks', '').lower()
        for pattern in self.footnote_patterns:
            if re.search(pattern, remarks):
                return True
        
        return False
    
    def analyze_multiple_transactions(self, transactions: List[Dict]) -> Dict:
        """
        Analyze multiple transactions from the same filing
        
        Args:
            transactions: List of transactions
            
        Returns:
            Analysis summary
        """
        meaningful_buys = []
        total_amount = 0
        
        for transaction in transactions:
            parsed = self.parse_transaction(transaction)
            if parsed:
                meaningful_buys.append(parsed)
                total_amount += parsed['amount']
        
        # Boost confidence if multiple insiders buying
        insider_count = len(set(b['insider_name'] for b in meaningful_buys))
        base_confidence = np.mean([b['confidence'] for b in meaningful_buys]) if meaningful_buys else 0
        
        if insider_count > 1:
            base_confidence = min(base_confidence * 1.2, 1.0)  # 20% boost
        
        return {
            'meaningful_buys': meaningful_buys,
            'total_amount': total_amount,
            'insider_count': insider_count,
            'confidence': base_confidence,
            'summary': f"{insider_count} insiders bought ${total_amount/1000000:.1f}M total"
        }
    
    def get_transaction_quality(self, transaction: Dict) -> str:
        """
        Get quality rating for a transaction
        
        Args:
            transaction: Transaction data
            
        Returns:
            Quality rating (HIGH, MEDIUM, LOW)
        """
        parsed = self.parse_transaction(transaction)
        
        if not parsed:
            return 'LOW'
        
        amount = parsed['amount']
        
        if amount >= 2000000:  # $2M+
            return 'HIGH'
        elif amount >= 1000000:  # $1M+
            return 'MEDIUM'
        else:
            return 'LOW'


# Example usage
if __name__ == "__main__":
    parser = Form4Parser(min_amount=500000)
    
    # Example transaction
    transaction = {
        'transaction_code': 'P',
        'amount': 2000000,
        'insider_name': 'John Doe',
        'title': 'CEO',
        'date': '2024-01-15',
        'price': 5.00,
        'footnote': 'Ordinary transaction'
    }
    
    result = parser.parse_transaction(transaction)
    print(f"Parsed transaction: {result}")
