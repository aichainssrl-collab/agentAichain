from typing import List, Optional
from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from agent_aichain.models import Skill, AIModel, Agent
from agent_aichain.core.database import get_db
from agent_aichain.api.auth import get_current_user
from agent_aichain.models import User
from agent_aichain.api.schemas import SkillCreate, SkillUpdate, ModelCreate, ModelUpdate

router = APIRouter(prefix="/settings", tags=["settings"])


# Skills endpoints

@router.get("/skills", response_model=List[dict])
async def list_skills(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all skills"""
    result = await db.execute(select(Skill).order_by(Skill.name))
    skills = result.scalars().all()
    return [
        {
            "id": s.id,
            "name": s.name,
            "description": s.description,
            "category": s.category,
            "is_active": s.is_active,
            "created_at": s.created_at.isoformat() if s.created_at else None
        }
        for s in skills
    ]


@router.post("/skills", response_model=dict)
async def create_skill(
    data: SkillCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new skill"""
    # Check if exists
    result = await db.execute(select(Skill).where(Skill.name == data.name))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Skill with this name already exists")

    skill = Skill(
        name=data.name,
        description=data.description,
        category=data.category,
        is_active=data.is_active
    )
    db.add(skill)
    await db.commit()
    await db.refresh(skill)
    return {
        "id": skill.id,
        "name": skill.name,
        "description": skill.description,
        "category": skill.category,
        "is_active": skill.is_active,
        "created_at": skill.created_at.isoformat() if skill.created_at else None
    }


@router.get("/skills/{skill_id}", response_model=dict)
async def get_skill(
    skill_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific skill"""
    result = await db.execute(select(Skill).where(Skill.id == skill_id))
    skill = result.scalar_one_or_none()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return {
        "id": skill.id,
        "name": skill.name,
        "description": skill.description,
        "category": skill.category,
        "is_active": skill.is_active,
        "created_at": skill.created_at.isoformat() if skill.created_at else None,
        "updated_at": skill.updated_at.isoformat() if skill.updated_at else None
    }


@router.put("/skills/{skill_id}", response_model=dict)
async def update_skill(
    skill_id: int,
    data: SkillUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a skill"""
    result = await db.execute(select(Skill).where(Skill.id == skill_id))
    skill = result.scalar_one_or_none()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")

    if data.name is not None:
        existing = await db.execute(select(Skill).where(Skill.name == data.name, Skill.id != skill_id))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Skill with this name already exists")
        skill.name = data.name
    if data.description is not None:
        skill.description = data.description
    if data.category is not None:
        skill.category = data.category
    if data.is_active is not None:
        skill.is_active = data.is_active

    await db.commit()
    await db.refresh(skill)
    return {
        "id": skill.id,
        "name": skill.name,
        "description": skill.description,
        "category": skill.category,
        "is_active": skill.is_active,
        "created_at": skill.created_at.isoformat() if skill.created_at else None,
        "updated_at": skill.updated_at.isoformat() if skill.updated_at else None
    }


@router.delete("/skills/{skill_id}")
async def delete_skill(
    skill_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a skill"""
    result = await db.execute(select(Skill).where(Skill.id == skill_id))
    skill = result.scalar_one_or_none()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    await db.delete(skill)
    await db.commit()
    return {"message": "Skill deleted successfully"}


# AI Models endpoints

@router.get("/models", response_model=List[dict])
async def list_models(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all AI models"""
    result = await db.execute(select(AIModel).order_by(AIModel.name))
    models = result.scalars().all()
    return [
        {
            "id": m.id,
            "name": m.name,
            "provider": m.provider,
            "base_url": m.base_url,
            "api_key": m.api_key,
            "max_tokens": m.max_tokens,
            "max_context": m.max_context,
            "cost_per_1k_input": m.cost_per_1k_input,
            "cost_per_1k_output": m.cost_per_1k_output,
            "config": m.config,
            "is_active": m.is_active,
            "created_at": m.created_at.isoformat() if m.created_at else None
        }
        for m in models
    ]


@router.post("/models", response_model=dict)
async def create_model(
    data: ModelCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new AI model"""
    result = await db.execute(select(AIModel).where(AIModel.name == data.name))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Model with this name already exists")

    model = AIModel(
        name=data.name,
        provider=data.provider,
        base_url=data.base_url,
        api_key=data.api_key,
        max_tokens=data.max_tokens,
        max_context=data.max_context,
        cost_per_1k_input=data.cost_per_1k_input,
        cost_per_1k_output=data.cost_per_1k_output,
        config=data.config,
        is_active=data.is_active,
        tenant_id=current_user.tenant_id
    )
    db.add(model)
    await db.commit()
    await db.refresh(model)
    return {
        "id": model.id,
        "name": model.name,
        "provider": model.provider,
        "base_url": model.base_url,
        "api_key": model.api_key,  # Note: API key is sensitive, consider not returning it
        "max_tokens": model.max_tokens,
        "max_context": model.max_context,
        "cost_per_1k_input": model.cost_per_1k_input,
        "cost_per_1k_output": model.cost_per_1k_output,
        "config": model.config,
        "is_active": model.is_active,
        "created_at": model.created_at.isoformat() if model.created_at else None
    }


@router.get("/models/{model_id}", response_model=dict)
async def get_model(
    model_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific AI model"""
    result = await db.execute(select(AIModel).where(AIModel.id == model_id))
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return {
        "id": model.id,
        "name": model.name,
        "provider": model.provider,
        "base_url": model.base_url,
        "api_key": model.api_key,
        "max_tokens": model.max_tokens,
        "max_context": model.max_context,
        "cost_per_1k_input": model.cost_per_1k_input,
        "cost_per_1k_output": model.cost_per_1k_output,
        "config": model.config,
        "is_active": model.is_active,
        "created_at": model.created_at.isoformat() if model.created_at else None,
        "updated_at": model.updated_at.isoformat() if model.updated_at else None
    }


@router.put("/models/{model_id}", response_model=dict)
async def update_model(
    model_id: int,
    data: ModelUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update an AI model"""
    result = await db.execute(select(AIModel).where(AIModel.id == model_id))
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    if data.name is not None:
        existing = await db.execute(select(AIModel).where(AIModel.name == data.name, AIModel.id != model_id))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Model with this name already exists")
        model.name = data.name
    if data.provider is not None:
        model.provider = data.provider
    if data.base_url is not None:
        model.base_url = data.base_url
    if data.api_key is not None:
        model.api_key = data.api_key
    if data.max_tokens is not None:
        model.max_tokens = data.max_tokens
    if data.max_context is not None:
        model.max_context = data.max_context
    if data.cost_per_1k_input is not None:
        model.cost_per_1k_input = data.cost_per_1k_input
    if data.cost_per_1k_output is not None:
        model.cost_per_1k_output = data.cost_per_1k_output
    if data.config is not None:
        model.config = data.config
    if data.is_active is not None:
        model.is_active = data.is_active

    await db.commit()
    await db.refresh(model)
    return {
        "id": model.id,
        "name": model.name,
        "provider": model.provider,
        "base_url": model.base_url,
        "api_key": model.api_key,
        "max_tokens": model.max_tokens,
        "max_context": model.max_context,
        "cost_per_1k_input": model.cost_per_1k_input,
        "cost_per_1k_output": model.cost_per_1k_output,
        "config": model.config,
        "is_active": model.is_active,
        "created_at": model.created_at.isoformat() if model.created_at else None,
        "updated_at": model.updated_at.isoformat() if model.updated_at else None
    }


from sqlalchemy.exc import IntegrityError

@router.delete("/models/{model_id}")
async def delete_model(
    model_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete an AI model"""
    result = await db.execute(select(AIModel).where(AIModel.id == model_id))
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    try:
        await db.delete(model)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        # Find which agents are using this model
        agents_result = await db.execute(select(Agent).where(Agent.aimodel_id == model_id))
        agents_using_model = agents_result.scalars().all()
        agent_names = ", ".join([a.name for a in agents_using_model])
        
        raise HTTPException(
            status_code=400, 
            detail=f"Non è possibile eliminare questo modello perché è in uso dai seguenti agenti: {agent_names}. Modifica prima quegli agenti."
        )
        
    return {"message": "Model deleted successfully"}
