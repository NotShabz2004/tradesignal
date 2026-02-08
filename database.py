"""
Database operations for TradeSignal
Handles SQLite database for storing price checks, alerts, and feedback
"""
import sqlite3
import logging
from datetime import datetime
from typing import Optional, List, Dict, Tuple

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_file: str):
        """Initialize database connection and create tables if needed"""
        self.db_file = db_file
        self.conn = None
        self._connect()
        self._create_tables()
    
    def _connect(self):
        """Create database connection"""
        try:
            self.conn = sqlite3.connect(self.db_file, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries
            logger.info(f"Connected to database: {self.db_file}")
        except sqlite3.Error as e:
            logger.error(f"Error connecting to database: {e}")
            raise
    
    def _create_tables(self):
        """Create all required tables if they don't exist"""
        cursor = self.conn.cursor()
        
        # Price checks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS price_checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                bitcoin_price REAL NOT NULL,
                ethereum_price REAL NOT NULL,
                solana_price REAL NOT NULL,
                bitcoin_change REAL,
                ethereum_change REAL,
                solana_change REAL
            )
        """)
        
        # Alerts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                coin TEXT NOT NULL,
                price REAL NOT NULL,
                change_percent REAL NOT NULL,
                ai_reason TEXT,
                ai_confidence INTEGER,
                user_feedback TEXT,
                feedback_timestamp TEXT
            )
        """)
        
        # Decisions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                coin TEXT NOT NULL,
                price_change REAL NOT NULL,
                should_alert INTEGER NOT NULL,
                reason TEXT,
                confidence INTEGER
            )
        """)
        
        self.conn.commit()
        logger.info("Database tables created/verified")
    
    def save_price_check(self, prices: Dict[str, float], changes: Dict[str, float]):
        """Save a price check to the database"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO price_checks 
                (timestamp, bitcoin_price, ethereum_price, solana_price,
                 bitcoin_change, ethereum_change, solana_change)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.utcnow().isoformat(),
                prices.get("bitcoin", 0),
                prices.get("ethereum", 0),
                prices.get("solana", 0),
                changes.get("bitcoin", 0),
                changes.get("ethereum", 0),
                changes.get("solana", 0)
            ))
            self.conn.commit()
            logger.debug(f"Saved price check: {prices}")
            return cursor.lastrowid
        except sqlite3.Error as e:
            logger.error(f"Error saving price check: {e}")
            self.conn.rollback()
            raise
    
    def get_last_price_check(self) -> Optional[Dict]:
        """Get the most recent price check"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT * FROM price_checks
                ORDER BY timestamp DESC
                LIMIT 1
            """)
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        except sqlite3.Error as e:
            logger.error(f"Error getting last price check: {e}")
            return None
    
    def save_decision(self, coin: str, price_change: float, should_alert: bool,
                     reason: str, confidence: int):
        """Save an AI decision to the database"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO decisions 
                (timestamp, coin, price_change, should_alert, reason, confidence)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                datetime.utcnow().isoformat(),
                coin,
                price_change,
                1 if should_alert else 0,
                reason,
                confidence
            ))
            self.conn.commit()
            logger.debug(f"Saved decision: {coin}, alert={should_alert}")
            return cursor.lastrowid
        except sqlite3.Error as e:
            logger.error(f"Error saving decision: {e}")
            self.conn.rollback()
            raise
    
    def save_alert(self, coin: str, price: float, change_percent: float,
                  ai_reason: str, ai_confidence: int) -> int:
        """Save an alert to the database"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO alerts 
                (timestamp, coin, price, change_percent, ai_reason, ai_confidence)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                datetime.utcnow().isoformat(),
                coin,
                price,
                change_percent,
                ai_reason,
                ai_confidence
            ))
            self.conn.commit()
            alert_id = cursor.lastrowid
            logger.info(f"Saved alert #{alert_id}: {coin} at ${price}")
            return alert_id
        except sqlite3.Error as e:
            logger.error(f"Error saving alert: {e}")
            self.conn.rollback()
            raise
    
    def update_alert_feedback(self, alert_id: int, feedback: str):
        """Update alert with user feedback"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                UPDATE alerts
                SET user_feedback = ?, feedback_timestamp = ?
                WHERE id = ?
            """, (
                feedback,
                datetime.utcnow().isoformat(),
                alert_id
            ))
            self.conn.commit()
            logger.info(f"Updated alert #{alert_id} with feedback: {feedback}")
        except sqlite3.Error as e:
            logger.error(f"Error updating alert feedback: {e}")
            self.conn.rollback()
            raise
    
    def get_recent_feedback(self, limit: int = 10) -> List[Dict]:
        """Get recent user feedback for AI context"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT coin, change_percent, user_feedback, ai_confidence
                FROM alerts
                WHERE user_feedback IS NOT NULL
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Error getting recent feedback: {e}")
            return []
    
    def get_feedback_stats(self) -> Dict[str, int]:
        """Get statistics about user feedback"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN user_feedback = 'helpful' THEN 1 ELSE 0 END) as helpful,
                    SUM(CASE WHEN user_feedback = 'not_helpful' THEN 1 ELSE 0 END) as not_helpful
                FROM alerts
                WHERE user_feedback IS NOT NULL
            """)
            row = cursor.fetchone()
            if row:
                return {
                    "total": row["total"] or 0,
                    "helpful": row["helpful"] or 0,
                    "not_helpful": row["not_helpful"] or 0
                }
            return {"total": 0, "helpful": 0, "not_helpful": 0}
        except sqlite3.Error as e:
            logger.error(f"Error getting feedback stats: {e}")
            return {"total": 0, "helpful": 0, "not_helpful": 0}
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

