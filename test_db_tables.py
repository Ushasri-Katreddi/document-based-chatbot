import asyncio

from dotenv import dotenv_values
from sqlalchemy.ext.asyncio import create_async_engine


async def main():
    database_url = dotenv_values(".env")["DATABASE_URL"]
    engine = create_async_engine(database_url)

    try:
        async with engine.connect() as connection:
            result = await connection.exec_driver_sql(
                "SELECT tablename FROM pg_tables "
                "WHERE schemaname = 'public' "
                "ORDER BY tablename"
            )
            print("Tables:", [row[0] for row in result.fetchall()])
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())