import asyncio
import aiohttp

async def main():
    async with aiohttp.ClientSession() as s:
        async with s.post('http://localhost:8000/auth/login', json={'username': 'cyber_sec', 'password': 'CyberSecure456!'}) as r:
            data = await r.json()
            if 'access_token' not in data:
                print("Login failed:", data)
                return
            token = data['access_token']

        async with s.get('http://localhost:8000/security/stats', headers={'Authorization': f'Bearer {token}'}) as me:
            print("Stats status:", me.status)
            print("Stats response:", await me.text())

        async with s.get('http://localhost:8000/security/events', headers={'Authorization': f'Bearer {token}'}) as me:
            print("Events status:", me.status)
            print("Events response:", await me.text())

if __name__ == "__main__":
    asyncio.run(main())
