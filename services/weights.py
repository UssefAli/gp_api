from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import RecommendationWeights
# from app.db.recommendation_weights import RecommendationWeights


async def get_weights(session: AsyncSession) -> RecommendationWeights:
    result = await session.execute(
        select(RecommendationWeights).limit(1)
    )
    weights = result.scalar_one_or_none()

    if not weights:
        weights = RecommendationWeights()
        session.add(weights)
        await session.commit()
        await session.refresh(weights)

    return weights


async def update_weights(
    session: AsyncSession,
    delta: float,
    lr: float = 0.05,
):
    weights = await get_weights(session)

    weights = await get_weights(session)

    weights.rating_weight += lr * delta
    weights.distance_weight -= lr * delta

    # normalize
    total = weights.rating_weight + weights.distance_weight
    weights.rating_weight /= total
    weights.distance_weight /= total

    await session.commit()
