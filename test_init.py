import asyncio
import os
import sys

# Set up path to find backend
sys.path.insert(0, os.path.abspath('.'))

from backend.database.connection import init_db

async def main():
    try:
        print("Running init_db...")
        await init_db()
        print("Success!")
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
