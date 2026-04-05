from fastapi import APIRouter, Depends
from agent_aichain.core.security import get_current_user
from agent_aichain.models.user import User
from agent_aichain.services.graph_service import GraphService

router = APIRouter(prefix="/graph", tags=["graph"])

@router.get("/tenant", response_model=dict)
async def get_tenant_graph(current_user: User = Depends(get_current_user)):
    """Get the full graph for the current tenant for Wow effect visualization"""
    graph_data = await GraphService.get_tenant_graph(tenant_id=current_user.tenant_id)
    return graph_data
