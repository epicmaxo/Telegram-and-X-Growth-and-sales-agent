from __future__ import annotations

import os
from typing import Any

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, JSON
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.sql import func

Base = declarative_base()


class UserRecord(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(255), unique=True, nullable=False, default="admin")
    telegram_session_string = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), default=func.now())


class ConversationRecord(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True)
    conversation_id = Column(String(255), unique=True, nullable=False)
    person_name = Column(String(255), nullable=True)
    chat_id = Column(String(255), nullable=True)
    stage = Column(String(255), nullable=True)
    state = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), default=func.now())


class DatabaseService:
    def __init__(self, database_url: str | None = None) -> None:
        self.database_url = database_url or os.getenv("DATABASE_URL", "sqlite:///./mentrast.db")
        
        # Supabase/SQLAlchemy compatibility: Use psycopg3 driver
        if self.database_url.startswith("postgresql://"):
            self.database_url = self.database_url.replace("postgresql://", "postgresql+psycopg://", 1)
            
        # Supabase uses a connection pooler, so pool_pre_ping is critical to avoid dropouts
        self.engine = create_engine(self.database_url, pool_pre_ping=True)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def create_conversation(self, conversation_id: str, chat_id: str | None = None, state: dict[str, Any] | None = None) -> ConversationRecord:
        with self.SessionLocal() as session:
            record = ConversationRecord(conversation_id=conversation_id, chat_id=chat_id, state=state or {})
            session.add(record)
            session.commit()
            session.refresh(record)
            return record

    def get_conversation(self, conversation_id: str) -> ConversationRecord | None:
        with self.SessionLocal() as session:
            return session.query(ConversationRecord).filter(ConversationRecord.conversation_id == conversation_id).first()

    def get_admin_user(self) -> UserRecord:
        with self.SessionLocal() as session:
            user = session.query(UserRecord).filter(UserRecord.username == "admin").first()
            if not user:
                user = UserRecord(username="admin")
                session.add(user)
                session.commit()
                session.refresh(user)
            return user

    def update_telegram_session(self, session_string: str) -> None:
        with self.SessionLocal() as session:
            user = session.query(UserRecord).filter(UserRecord.username == "admin").first()
            if not user:
                user = UserRecord(username="admin")
                session.add(user)
            user.telegram_session_string = session_string
            session.commit()
