import os
import mysql.connector
from mysql.connector.cursor import MySQLCursor
import sqlparse
import time
from app import app  # our Flask app
import re

# === MySQL credentials ===
MYSQL_HOST = "localhost"
MYSQL_USER = "Admin"
MYSQL_PASSWORD = "Admin"
MYSQL_DB = "Bored_Games"

# === SQL file paths ===
BASE_SQL_DIR = os.path.abspath(os.path.join(os.getcwd(), '../Database'))
CREATION_SQL = os.path.join(BASE_SQL_DIR, 'Creation.sql')
INSERT_SQL = os.path.join(BASE_SQL_DIR, 'Insertion.sql') #Change accroding to normal insertion or blob insertion
VIEWS_TRIGGERS_SQL = os.path.join(BASE_SQL_DIR, 'Views_Triggers_functions.sql')

def execute_sql_file(cursor, connection, path):
    print(f"▶ Running SQL: {os.path.basename(path)}")
    with open(path, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    # Disable foreign key checks during inserts
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
    connection.commit()

    statements = sqlparse.split(sql_content)  # safer splitting

    for statement in statements:
        stmt = statement.strip()
        if stmt:
            try:
                cursor.execute(stmt)
            except Exception as e:
                print(f"⚠️ Error executing:\n{stmt}\n→ {e}")

    cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
    connection.commit()

def setup_database():
    print("📡 Connecting to MySQL...")
    connection = mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB
    )
    cursor = connection.cursor()
    execute_sql_file(cursor, connection, CREATION_SQL)
    connection.commit()
    cursor.close()
    connection.close()

    # Second: Reconnect to the specific database
    print("🔁 Reconnecting to MySQL (with database)...")
    connection = mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB
    )
    cursor = connection.cursor()
    execute_sql_file(cursor, connection, VIEWS_TRIGGERS_SQL)
    execute_sql_file(cursor, connection, INSERT_SQL)
    
    connection.commit()
    cursor.close()
    connection.close()

    print("✅ Database setup complete.")

def launch_flask():
    print("🚀 Starting Flask app...")
    app.run(debug=True)

if __name__ == "__main__":
    setup_database()
    time.sleep(2)
    launch_flask()
