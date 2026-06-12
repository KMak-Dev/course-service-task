import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import provider as provider_crud
from app.database.session import get_db, get_tenant_db
from app.schemas.provider import (
    CreateProvider,
    ProviderResponse,
    UpdateProvider,
)

router = APIRouter(prefix="/providers", tags=["providers"])


@router.get("", response_model=list[ProviderResponse])
async def list_providers(
    db: AsyncSession = Depends(get_db),
) -> list[ProviderResponse]:
    providers = await provider_crud.list_providers(db)
    return [
        ProviderResponse.model_validate(provider) for provider in providers
    ]


@router.post(
    "",
    response_model=ProviderResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_provider(
    body: CreateProvider,
    db: AsyncSession = Depends(get_db),
) -> ProviderResponse:
    provider = await provider_crud.create_provider(db, body)
    await db.commit()
    return ProviderResponse.model_validate(provider)


@router.get("/{provider_id}", response_model=ProviderResponse)
async def get_provider(
    provider_id: uuid.UUID,
    db: AsyncSession = Depends(get_tenant_db),
) -> ProviderResponse:
    provider = await provider_crud.get_provider_by_id(db, provider_id)
    if provider is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider not found",
        )
    return ProviderResponse.model_validate(provider)


@router.patch("/{provider_id}", response_model=ProviderResponse)
async def update_provider(
    provider_id: uuid.UUID,
    body: UpdateProvider,
    db: AsyncSession = Depends(get_tenant_db),
) -> ProviderResponse:
    provider = await provider_crud.get_provider_by_id(db, provider_id)
    if provider is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider not found",
        )

    provider = await provider_crud.update_provider(db, provider, body)
    await db.commit()
    return ProviderResponse.model_validate(provider)


@router.delete("/{provider_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_provider(
    provider_id: uuid.UUID,
    db: AsyncSession = Depends(get_tenant_db),
) -> Response:
    provider = await provider_crud.get_provider_by_id(db, provider_id)
    if provider is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider not found",
        )

    await provider_crud.delete_provider(db, provider)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
