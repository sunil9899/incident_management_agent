from app.tools.incident_tools import (
    get_recent_errors,
    check_service_health,
    check_database_health,
    check_redis_health
)


INCIDENT_TOOLS = [
    get_recent_errors,
    check_service_health,
    check_database_health,
    check_redis_health
]
