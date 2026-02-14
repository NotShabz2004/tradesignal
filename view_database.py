"""
Helper script to view TradeSignal database contents
Useful for taking screenshots of database schema and sample data
"""
import sqlite3
from database import Database

def print_schema():
    """Print database schema"""
    print("=" * 60)
    print("DATABASE SCHEMA")
    print("=" * 60)
    
    conn = sqlite3.connect("tradesignal.db")
    cursor = conn.cursor()
    
    tables = ["price_checks", "alerts", "decisions"]
    
    for table in tables:
        print(f"\n📊 Table: {table}")
        print("-" * 60)
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        print(f"{'Column':<20} {'Type':<15} {'Nullable':<10}")
        print("-" * 60)
        for col in columns:
            nullable = "YES" if col[3] == 0 else "NO"
            print(f"{col[1]:<20} {col[2]:<15} {nullable:<10}")
    
    conn.close()

def print_sample_data():
    """Print sample data from all tables"""
    db = Database("tradesignal.db")
    
    print("\n" + "=" * 60)
    print("SAMPLE DATA")
    print("=" * 60)
    
    # Price Checks
    conn = sqlite3.connect("tradesignal.db")
    cursor = conn.cursor()
    
    print("\n📈 Recent Price Checks (last 5):")
    print("-" * 60)
    cursor.execute("""
        SELECT timestamp, bitcoin_price, ethereum_price, solana_price,
               bitcoin_change, ethereum_change, solana_change
        FROM price_checks
        ORDER BY timestamp DESC
        LIMIT 5
    """)
    rows = cursor.fetchall()
    if rows:
        print(f"{'Timestamp':<20} {'BTC':<12} {'ETH':<12} {'SOL':<12} {'BTC%':<8} {'ETH%':<8} {'SOL%':<8}")
        print("-" * 60)
        for row in rows:
            print(f"{row[0][:19]:<20} ${row[1]:<11.2f} ${row[2]:<11.2f} ${row[3]:<11.2f} "
                  f"{row[4]:+7.2f}% {row[5]:+7.2f}% {row[6]:+7.2f}%")
    else:
        print("No price checks yet")
    
    # Alerts
    print("\n🚨 Recent Alerts (last 5):")
    print("-" * 60)
    cursor.execute("""
        SELECT id, timestamp, coin, price, change_percent, 
               ai_confidence, user_feedback
        FROM alerts
        ORDER BY timestamp DESC
        LIMIT 5
    """)
    rows = cursor.fetchall()
    if rows:
        print(f"{'ID':<4} {'Timestamp':<20} {'Coin':<10} {'Price':<12} "
              f"{'Change%':<10} {'Conf':<6} {'Feedback':<12}")
        print("-" * 60)
        for row in rows:
            feedback = row[6] or "None"
            print(f"{row[0]:<4} {row[1][:19]:<20} {row[2]:<10} ${row[3]:<11.2f} "
                  f"{row[4]:+9.2f}% {row[5]:<6} {feedback:<12}")
    else:
        print("No alerts sent yet")
    
    # Decisions
    print("\n🤖 Recent AI Decisions (last 5):")
    print("-" * 60)
    cursor.execute("""
        SELECT timestamp, coin, price_change, should_alert, confidence, reason
        FROM decisions
        ORDER BY timestamp DESC
        LIMIT 5
    """)
    rows = cursor.fetchall()
    if rows:
        print(f"{'Timestamp':<20} {'Coin':<10} {'Change%':<10} "
              f"{'Alert':<6} {'Conf':<6} {'Reason':<30}")
        print("-" * 60)
        for row in rows:
            alert = "Yes" if row[3] else "No"
            reason = (row[5] or "N/A")[:28]
            print(f"{row[0][:19]:<20} {row[1]:<10} {row[2]:+9.2f}% "
                  f"{alert:<6} {row[4]:<6} {reason:<30}")
    else:
        print("No AI decisions yet")
    
    # Statistics
    print("\n" + "=" * 60)
    print("STATISTICS")
    print("=" * 60)
    
    cursor.execute("SELECT COUNT(*) FROM price_checks")
    price_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM alerts")
    alert_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM decisions")
    decision_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM alerts WHERE user_feedback = 'helpful'")
    helpful_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM alerts WHERE user_feedback = 'not_helpful'")
    not_helpful_count = cursor.fetchone()[0]
    
    print(f"Total Price Checks: {price_count}")
    print(f"Total Alerts Sent: {alert_count}")
    print(f"Total AI Decisions: {decision_count}")
    print(f"User Feedback - Helpful: {helpful_count}, Not Helpful: {not_helpful_count}")
    
    conn.close()
    db.close()

if __name__ == "__main__":
    print("\n🔍 TradeSignal Database Viewer\n")
    
    try:
        print_schema()
        print_sample_data()
        print("\n" + "=" * 60)
        print("💡 Tip: Use this output to take screenshots for your README!")
        print("=" * 60 + "\n")
    except FileNotFoundError:
        print("❌ Error: tradesignal.db not found. Run monitor.py first to create the database.")
    except Exception as e:
        print(f"❌ Error: {e}")

