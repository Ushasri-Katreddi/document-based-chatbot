import asyncio

from dotenv import dotenv_values
from sqlalchemy.ext.asyncio import create_async_engine


async def main():
    settings = dotenv_values(".env")
    database_url = settings["DATABASE_URL"]

    engine = create_async_engine(database_url)

    try:
        async with engine.connect() as connection:
            result = await connection.exec_driver_sql(
                "SELECT current_database(), current_user"
            )
            print("Connection successful:", result.fetchone())
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())