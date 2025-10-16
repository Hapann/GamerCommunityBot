# database/models.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from database.db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    tg_id = Column(Integer, unique=True, nullable=False)
    username = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    sent_news = relationship("SentNews", back_populates="user")


class Feed(Base):
    __tablename__ = "feeds"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    url = Column(Text, unique=True, nullable=False)
    type = Column(String, nullable=False)  # rss/api/parser


class News(Base):
    __tablename__ = "news"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    url = Column(Text, unique=True, nullable=False)
    source_id = Column(ForeignKey("feeds.id"))

    # 🕓 Дата публикации из RSS
    published_at = Column(DateTime, nullable=False)

    source = relationship("Feed")
    sent_to = relationship("SentNews", back_populates="news")


class SentNews(Base):
    __tablename__ = "sent_news"

    id = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey("users.id"))
    news_id = Column(ForeignKey("news.id"))
    sent_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("user_id", "news_id", name="unique_user_news"),
    )

    user = relationship("User", back_populates="sent_news")
    news = relationship("News", back_populates="sent_to")
