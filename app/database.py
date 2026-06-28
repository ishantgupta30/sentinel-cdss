from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy import Text, String, Integer, DateTime, Boolean, JSON, text
from datetime import datetime
from typing import Optional
from app.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

class AuditEntry(Base):
    __tablename__ = "audit_entries"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    patient_id: Mapped[str] = mapped_column(String(50), index=True)
    correlation_id: Mapped[str] = mapped_column(String(100))
    news2_score: Mapped[int] = mapped_column(Integer)
    risk_tier: Mapped[str] = mapped_column(String(20))
    recommended_ward: Mapped[str] = mapped_column(String(100))
    is_signed_off: Mapped[bool] = mapped_column(Boolean, default=False)
    lineage_hash: Mapped[str] = mapped_column(String(64))

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
