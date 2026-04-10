import structlog
from typing import Any, Dict, Optional
from enum import Enum
from datetime import datetime, timezone

logger = structlog.get_logger("audit")

class AuditAction(str, Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    READ = "READ"
    EXECUTE = "EXECUTE"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"

def log_audit_event(
    action: AuditAction,
    resource_type: str,
    resource_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
    user_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log an audit event with structured data.
    """
    event_data = {
        "event_type": "audit",
        "action": action.value,
        "resource_type": resource_type,
        "resource_id": str(resource_id) if resource_id else None,
        "tenant_id": str(tenant_id) if tenant_id else None,
        "user_id": str(user_id) if user_id else None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "details": details or {}
    }
    
    # Remove None values for cleaner logs
    event_data = {k: v for k, v in event_data.items() if v is not None}
    
    logger.info("Audit event", **event_data)
