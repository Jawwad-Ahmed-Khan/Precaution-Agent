import asyncpg
from asyncpg.pool import Pool
from app.core.config import settings
from app.core.logger import setup_logger

logger = setup_logger(__name__)

# Module-level variable to hold the pool instance
_collection_pool: Pool | None = None


async def _init_collection_connection(conn):
    """Initializes each connection in the pool."""
    await conn.execute("SET timezone = 'Asia/Karachi'")


async def create_collection_pool() -> None:
    """
    Creates the Collection Database pool.
    Tests the connection with SELECT 1 and logs success.
    """
    global _collection_pool
    if _collection_pool is not None:
        return

    try:
        _collection_pool = await asyncpg.create_pool(
            host=settings.collection_db_host,
            port=settings.collection_db_port,
            user=settings.collection_db_user,
            password=settings.collection_db_password,
            database=settings.collection_db_name,
            min_size=0,
            max_size=settings.collection_db_pool_max,
            init=_init_collection_connection,
            command_timeout=120,
            statement_cache_size=0,  # Required for Supabase transaction pooler
            max_inactive_connection_lifetime=30.0,  # Release idle connections after 30s
        )

        # Test the connection immediately
        async with _collection_pool.acquire() as conn:
            await conn.execute("SELECT 1")

        logger.info("Successfully created Collection Database pool (Read-Only).")
    except Exception as e:
        logger.error(f"Failed to create Collection Database pool: {str(e)}")
        raise


async def close_collection_pool() -> None:
    """Closes the Collection Database pool."""
    global _collection_pool
    if _collection_pool:
        await _collection_pool.close()
        _collection_pool = None
        logger.info("Closed Collection Database pool.")


def get_collection_pool() -> Pool:
    """
    Returns the Collection Database pool.
    Raises RuntimeError if the pool is not initialized.
    """
    if _collection_pool is None:
        raise RuntimeError("Collection Database pool is not initialized. Call create_collection_pool() first.")
    return _collection_pool


async def acquire_healthy_collection_connection(pool: Pool):
    """
    Acquires a healthy connection from the collection pool.
    Retries up to 3 times on stale connections.
    """
    for attempt in range(3):
        try:
            conn = await pool.acquire()
            await conn.execute("SELECT 1")
            return conn
        except Exception as e:
            if conn:
                try:
                    await pool.release(conn)
                except Exception:
                    pass
            if attempt < 2:
                logger.warning(f"Stale collection connection (attempt {attempt + 1}): {e}. Retrying...")
                continue
            raise
