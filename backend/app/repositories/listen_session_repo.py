from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.listen_session import ListenSession


class ListenSessionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert(self, entity: ListenSession) -> None:
        """Insert or update a listen session by its unique session_token.

        The client sends cumulative session state, so an existing row is
        fully overwritten with the latest values.
        """
        stmt = insert(ListenSession).values(
            track_id=entity.track_id,
            session_token=entity.session_token,
            visitor_id=entity.visitor_id,
            track_duration_seconds=entity.track_duration_seconds,
            listened_seconds=entity.listened_seconds,
            last_position_seconds=entity.last_position_seconds,
            completion_ratio=entity.completion_ratio,
            seek_count=entity.seek_count,
            is_completed=entity.is_completed,
            referrer=entity.referrer,
            language=entity.language,
            device_type=entity.device_type,
        )
        excluded = stmt.excluded
        stmt = stmt.on_conflict_do_update(
            index_elements=[ListenSession.session_token],
            set_={
                "track_id": excluded.track_id,
                "visitor_id": excluded.visitor_id,
                "track_duration_seconds": excluded.track_duration_seconds,
                "listened_seconds": excluded.listened_seconds,
                "last_position_seconds": excluded.last_position_seconds,
                "completion_ratio": excluded.completion_ratio,
                "seek_count": excluded.seek_count,
                "is_completed": excluded.is_completed,
                "referrer": excluded.referrer,
                "language": excluded.language,
                "device_type": excluded.device_type,
                "updated_at": func.now(),
            },
        )
        await self.session.execute(stmt)
        await self.session.commit()
