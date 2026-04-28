import psycopg2
from backend.config import settings

def check_extension():
    db_url = settings.database_url.replace("postgresql+asyncpg://", "")
    auth, rest = db_url.split("@")
    user, password = auth.split(":")
    host_port, db_name = rest.split("/")
    host = host_port.split(":")[0]
    port = host_port.split(":")[1] if ":" in host_port else "5432"
    
    try:
        conn = psycopg2.connect(
            dbname=db_name,
            user=user,
            password=password,
            host=host,
            port=port
        )
        cur = conn.cursor()
        cur.execute("SELECT * FROM pg_available_extensions WHERE name = 'vector'")
        extension = cur.fetchone()
        if extension:
            print(f"Extension 'vector' is available. Version: {extension[2]}")
        else:
            print("Extension 'vector' is NOT available in pg_available_extensions.")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_extension()
