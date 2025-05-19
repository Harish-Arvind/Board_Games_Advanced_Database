import os

def escape_string(value):
    """Escape single quotes for SQL strings."""
    return "'" + str(value).replace("'", "''") + "'"

def submit_user_rating(mysql, user_id, game_id, stars, comment):
    cur = mysql.connection.cursor()
    try:
        # Build path to SQL file
        base_dir = os.path.dirname(__file__)  # webserver/
        sql_path = os.path.join(base_dir, '..', 'Database', 'submit_rating_transaction.sql')

        with open(sql_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()

        # Inject values safely
        replacements = {
            '{user_id}': str(user_id),
            '{game_id}': str(game_id),
            '{stars}': str(stars),
            '{comment}': escape_string(comment)
        }

        for placeholder, val in replacements.items():
            sql_content = sql_content.replace(placeholder, val)

        statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]

        for stmt in statements:
            cur.execute(stmt)

        mysql.connection.commit()

    except Exception as e:
        mysql.connection.rollback()
        print(f"❌ Error during transaction: {e}")
        raise e
    finally:
        cur.close()


