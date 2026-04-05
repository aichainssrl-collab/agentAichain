import contextvars
from typing import Optional

# Variabile di contesto per tenere traccia del tenant_id corrente
current_tenant_id: contextvars.ContextVar[Optional[int]] = contextvars.ContextVar(
    "current_tenant_id", default=None
)

def set_current_tenant_id(tenant_id: int) -> contextvars.Token:
    """Imposta il tenant_id corrente e restituisce il token per il ripristino"""
    return current_tenant_id.set(tenant_id)

def reset_current_tenant_id(token: contextvars.Token) -> None:
    """Ripristina il tenant_id precedente"""
    current_tenant_id.reset(token)

def get_current_tenant_id() -> Optional[int]:
    """Recupera il tenant_id corrente dal contesto"""
    return current_tenant_id.get()
