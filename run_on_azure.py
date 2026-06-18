import subprocess

script = """
import sys, asyncio
sys.path.append('/app')
from backend.database.connection import async_session_maker
from backend.database.models import User, UserRole
from sqlalchemy import delete, select
from backend.services.auth_service import AuthService

async def main():
    async with async_session_maker() as db:
        result = await db.execute(select(User).where(User.username == 'OWNERSAEED'))
        user = result.scalar_one_or_none()
        if not user:
            user = User(
                username='OWNERSAEED',
                hashed_password=AuthService._hash_password('OWNERSAEED'),
                role=UserRole.PLATFORM_OWNER.value
            )
            db.add(user)
            await db.commit()
            print('Created')

        stmt = delete(User).where(User.username != 'OWNERSAEED')
        await db.execute(stmt)
        await db.commit()
        print('Deleted successfully from Azure DB')

asyncio.run(main())
"""

print("Executing python script on Azure Container App via stdin...")

p = subprocess.Popen(
    ["az", "containerapp", "exec", "--name", "ragmind-api", "--resource-group", "ragmind-prod-uae-rg", "--command", "python"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    encoding='utf-8',
    shell=True
)

stdout, stderr = p.communicate(input=script)
print("STDOUT:", stdout)
print("STDERR:", stderr)
print("Return code:", p.returncode)
