from langchain.tools import tool
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from redis.asyncio import Redis
import httpx

from app.core.config import get_settings


mock_errors = {
    "payment-api": [
        "Database connection timeout",
        "Payment API returned HTTP 503",
        "Connection pool exhausted",
    ],
    "user-api": [
        "Redis connection timeout",
        "User API returned HTTP 500",
    ]
}


@tool
def get_recent_errors(service_name: str) -> list[str]:
    """
    Fetch recent application errors for a given service.

    Args:
        service_name: Name of the application service.
    """
    error = mock_errors.get(service_name.lower(), [])
    return error


@tool
async def check_database_health() -> dict:
    """To check the PostGresql connection"""
    settings = get_settings()
    engine = create_async_engine(
        url=settings.database_url,
        pool_pre_ping=True
    )
    try:
        async with engine.connect() as connection:
            await connection.execute(text("select 1"))
        return {
            "status": "healthy",
            "database": "postgresql",
            "message": "database connection successful."
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "postgresql",
            "message": str(e)
        }
    finally:
        await engine.dispose()


@tool
async def check_redis_health() -> dict:
    """To check the redis connection"""
    settings = get_settings()
    redis_client = Redis.from_url(
        url=settings.REDIS_URL,
        socket_connect_timeout=5,
        socket_timeout=5,
        decode_responses=True
    )
    try:
        response = redis_client.ping()
        if response:
            return {
                "status": "healthy",
                "service": "redis",
                "message": "Redis connection successful."
            }
        return {
            "status": "unhealthy",
            "service": "redis",
            "message": "Redis ping returned an unexpected response."
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "redis",
            "message": str(e)
        }
    finally:
        await redis_client.aclose()


@tool
async def check_service_health(service_url: str) -> dict:
    """
    Check the availability of an external microservice using its health endpoint.

    Args:
        service_url: Base URL of the service to investigate.
    """
    health_url = f'{service_url.rstrip("/")}/helath'
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(health_url)
        return {
            "status": "healthy" if response.is_success else "unhealthy",
            "service_url": health_url,
            "http_status": response.status_code,
            "message": (
                "Service is responding"
                if response.is_success
                else "Service returned unsuccessful HTTP status"
            )
        }
    except httpx.TimeoutException:
        return {
            "status": "unhealthy",
            "service_url": health_url,
            "message": "Service health-check timed out"
        }
    except httpx.RequestError as e:
        return {
            "status": "unhealthy",
            "service_url": health_url,
            "message": f"Service connection failed: {e}"
        }
