import asyncpg
from asyncpg.pool import Pool
from app.core.config import settings
from app.core.logger import setup_logger

logger = setup_logger(__name__)

# Module-level variable to hold the pool instance
_main_pool: Pool | None = None


async def _init_main_connection(conn):
    """Initializes each connection in the pool."""
    await conn.execute("SET timezone = 'Asia/Karachi'")


async def create_main_pool() -> None:
    """
    Creates the Main Operational Database pool.
    Tests the connection with SELECT 1 and logs success.
    """
    global _main_pool
    if _main_pool is not None:
        return

    try:
        _main_pool = await asyncpg.create_pool(
            host=settings.main_db_host,
            port=settings.main_db_port,
            user=settings.main_db_user,
            password=settings.main_db_password,
            database=settings.main_db_name,
            min_size=0,
            max_size=settings.main_db_pool_max,
            init=_init_main_connection,
            command_timeout=120,
            statement_cache_size=0,  # Required for Supabase transaction pooler
            max_inactive_connection_lifetime=30.0,  # Release idle connections after 30s
        )

        # Test the connection immediately
        async with _main_pool.acquire() as conn:
            await conn.execute("SELECT 1")

        logger.info("Successfully created Main Operational Database pool (Read+Write).")
    except Exception as e:
        logger.error(f"Failed to create Main Operational Database pool: {str(e)}")
        raise


async def close_main_pool() -> None:
    """Closes the Main Operational Database pool."""
    global _main_pool
    if _main_pool:
        await _main_pool.close()
        _main_pool = None
        logger.info("Closed Main Operational Database pool.")


def get_main_pool() -> Pool:
    """
    Returns the Main Operational Database pool.
    Raises RuntimeError if the pool is not initialized.
    """
    if _main_pool is None:
        raise RuntimeError("Main Database pool is not initialized. Call create_main_pool() first.")
    return _main_pool


async def acquire_healthy_connection(pool: Pool):
    """
    Acquires a connection from the pool, testing its health.
    If the connection is stale (closed by PgBouncer), expires it and gets a fresh one.
    Retries up to 3 times.
    """
    for attempt in range(3):
        try:
            conn = await pool.acquire()
            # Test the connection is alive
            await conn.execute("SELECT 1")
            return conn
        except Exception as e:
            if conn:
                try:
                    await pool.release(conn)
                except Exception:
                    pass
            if attempt < 2:
                logger.warning(f"Stale connection detected (attempt {attempt + 1}): {e}. Retrying...")
                continue
            raise
