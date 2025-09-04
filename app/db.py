# app/db.py
from __future__ import annotations
import os
from datetime import datetime
from sqlalchemy import String, DateTime, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker, Session

class Base(DeclarativeBase):
    pass

class TicketLog(Base):
    __tablename__ = "ticket_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    source_event: Mapped[str] = mapped_column(String(50), nullable=False)
    delivery_id: Mapped[str] = mapped_column(String(120), nullable=False)
    ticket_key: Mapped[str] = mapped_column(String(50), nullable=False)

def init_db(database_url: str | None):
    db_url = database_url or "sqlite:///app/dev.sqlite"
    if db_url.startswith("sqlite:///"):
        os.makedirs("app", exist_ok=True)

    engine = create_engine(db_url, echo=False, future=True)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    return engine, SessionLocal

def log_ticket_creation(session: Session, source_event: str, delivery_id: str, ticket_key: str) -> None:
    log = TicketLog(
        source_event=source_event,
        delivery_id=delivery_id,
        ticket_key=ticket_key
    )
    session.add(log)
    session.commit()

