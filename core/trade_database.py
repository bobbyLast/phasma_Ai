"""
Trade Database Module
Handles storage and retrieval of trade data
"""
import sqlite3
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json

class TradeDatabase:
    """
    Manages trade data storage and retrieval using SQLite
    """
    
    def __init__(self, db_path: str = 'data/trades/phasma_trades.db'):
        """
        Initialize the trade database
        
        Args:
            db_path: Path to the SQLite database file
        """
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_db()
        
    def close(self):
        """Close the database connection"""
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
            
    def __del__(self):
        """Ensure connection is closed when object is destroyed"""
        self.close()
    
    def _init_db(self):
        """Initialize the database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create trades table if it doesn't exist
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                strategy TEXT NOT NULL,
                action TEXT NOT NULL,  -- BUY/SELL
                entry_price REAL NOT NULL,
                exit_price REAL,
                quantity INTEGER NOT NULL,
                pnl REAL,
                entry_time TEXT NOT NULL,  -- ISO format datetime
                exit_time TEXT,
                status TEXT NOT NULL,  -- OPEN/CLOSED
                metadata TEXT,  -- JSON string for additional data
                created_at TEXT NOT NULL
            )
            ''')
            
            # Create index for faster lookups
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_entry_time ON trades(entry_time)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_strategy ON trades(strategy)')
            
            conn.commit()
    
    def save_trade(
        self,
        symbol: str,
        strategy: str,
        action: str,
        entry_price: float,
        quantity: int,
        metadata: Optional[Dict] = None,
        entry_time: Optional[datetime] = None
    ) -> int:
        """
        Save a new trade to the database
        
        Args:
            symbol: Trading symbol (e.g., 'AAPL')
            strategy: Strategy name (e.g., 'momentum', 'reversal')
            action: 'BUY' or 'SELL'
            entry_price: Entry price
            quantity: Number of shares/contracts
            metadata: Additional trade metadata (optional)
            entry_time: Trade entry time (defaults to now)
            
        Returns:
            int: The ID of the created trade
        """
        now = datetime.utcnow().isoformat()
        entry_time = entry_time.isoformat() if entry_time else now
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT INTO trades (
                symbol, strategy, action, entry_price, quantity,
                entry_time, status, metadata, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                symbol, strategy, action, entry_price, quantity,
                entry_time, 'OPEN',
                json.dumps(metadata) if metadata else None,
                now
            ))
            
            trade_id = cursor.lastrowid
            conn.commit()
            
            return trade_id
    
    def close_trade(
        self,
        trade_id: int,
        exit_price: float,
        exit_time: Optional[datetime] = None,
        metadata_update: Optional[Dict] = None
    ) -> bool:
        """
        Close an open trade
        
        Args:
            trade_id: ID of the trade to close
            exit_price: Exit price
            exit_time: Exit time (defaults to now)
            metadata_update: Additional metadata to merge with existing
            
        Returns:
            bool: True if successful, False if trade not found or already closed
        """
        exit_time = (exit_time or datetime.utcnow()).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get the trade to calculate PnL
            cursor.execute('SELECT entry_price, quantity, metadata FROM trades WHERE id = ?', (trade_id,))
            trade = cursor.fetchone()
            
            if not trade:
                return False
                
            entry_price, quantity, metadata_json = trade
            
            # Calculate PnL (simple version - can be customized per strategy)
            pnl = (exit_price - entry_price) * quantity
            
            # Update metadata if provided
            metadata = json.loads(metadata_json) if metadata_json else {}
            if metadata_update:
                metadata.update(metadata_update)
            
            # Update the trade
            cursor.execute('''
            UPDATE trades 
            SET exit_price = ?, 
                exit_time = ?,
                pnl = ?,
                status = 'CLOSED',
                metadata = ?
            WHERE id = ? AND status = 'OPEN'
            ''', (exit_price, exit_time, pnl, json.dumps(metadata) if metadata else None, trade_id))
            
            updated = cursor.rowcount > 0
            conn.commit()
            
            return updated
    
    def get_recent_trades(self, days_back: int = 30, strategy: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get recent trades
        
        Args:
            days_back: Number of days to look back
            strategy: Optional strategy filter
            
        Returns:
            List of trade dictionaries
        """
        cutoff = (datetime.utcnow() - timedelta(days=days_back)).isoformat()
        
        query = '''
        SELECT 
            id, symbol, strategy, action, 
            entry_price, exit_price, quantity, pnl,
            entry_time, exit_time, status, metadata
        FROM trades 
        WHERE entry_time >= ?
        '''
        
        params = [cutoff]
        
        if strategy:
            query += ' AND strategy = ?'
            params.append(strategy)
            
        query += ' ORDER BY entry_time DESC'
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            trades = []
            for row in rows:
                trade = dict(row)
                # Convert SQLite Row to dict and process metadata
                if 'metadata' in trade and trade['metadata']:
                    try:
                        trade['metadata'] = json.loads(trade['metadata'])
                    except (json.JSONDecodeError, TypeError):
                        trade['metadata'] = {}
                else:
                    trade['metadata'] = {}
                trades.append(trade)
                
            return trades
    
    def get_open_trades(self) -> List[Dict[str, Any]]:
        """Get all open trades"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT 
                id, symbol, strategy, action, 
                entry_price, quantity, entry_time, metadata
            FROM trades 
            WHERE status = 'OPEN'
            ORDER BY entry_time
            ''')
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_trade_stats(self, days_back: int = 30) -> Dict[str, Any]:
        """
        Get trade statistics
        
        Args:
            days_back: Number of days to analyze
            
        Returns:
            Dictionary with trade statistics
        """
        cutoff = (datetime.utcnow() - timedelta(days=days_back)).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Basic stats
            cursor.execute('''
            SELECT 
                COUNT(*) as total_trades,
                SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
                SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END) as losing_trades,
                AVG(pnl) as avg_pnl,
                SUM(pnl) as total_pnl,
                AVG(julianday(exit_time) - julianday(entry_time)) as avg_days_held,
                SUM(ABS(entry_price * quantity)) as total_capital_risked
            FROM trades 
            WHERE status = 'CLOSED' AND entry_time >= ?
            ''', (cutoff,))
            
            stats = dict(zip(
                ['total_trades', 'winning_trades', 'losing_trades', 
                 'avg_pnl', 'total_pnl', 'avg_days_held', 'total_capital_risked'],
                cursor.fetchone()
            ))
            
            # Handle None values
            for k, v in stats.items():
                if v is None:
                    stats[k] = 0
            
            # Calculate win rate
            stats['win_rate'] = (
                (stats['winning_trades'] / stats['total_trades'] * 100) 
                if stats['total_trades'] > 0 else 0
            )
            # Batch ROI based on approximate capital at risk
            total_capital_risked = stats.get('total_capital_risked', 0) or 0
            if total_capital_risked > 0:
                stats['roi_pct'] = (stats['total_pnl'] / total_capital_risked) * 100
            else:
                stats['roi_pct'] = 0
            
            # Strategy performance
            cursor.execute('''
            SELECT 
                strategy,
                COUNT(*) as count,
                SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as wins,
                AVG(pnl) as avg_pnl,
                SUM(pnl) as total_pnl
            FROM trades 
            WHERE status = 'CLOSED' AND entry_time >= ?
            GROUP BY strategy
            ORDER BY total_pnl DESC
            ''', (cutoff,))
            
            stats['by_strategy'] = []
            for row in cursor.fetchall():
                strat_stats = dict(zip(
                    ['strategy', 'count', 'wins', 'avg_pnl', 'total_pnl'],
                    row
                ))
                strat_stats['win_rate'] = (
                    (strat_stats['wins'] / strat_stats['count'] * 100) 
                    if strat_stats['count'] > 0 else 0
                )
                stats['by_strategy'].append(strat_stats)
            
            return stats
