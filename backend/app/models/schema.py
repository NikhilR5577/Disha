from sqlalchemy import Column, String, Integer, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .database import Base

class NodeDB(Base):
    __tablename__ = "nodes"

    id = Column(String, primary_key=True, index=True)
    x = Column(Float)
    y = Column(Float)
    floor = Column(Integer)
    is_room = Column(Boolean)
    name = Column(String, index=True, nullable=True)
    name_hi = Column(String, index=True, nullable=True)
    keywords = Column(String, nullable=True)

    edges_out = relationship("EdgeDB", foreign_keys="[EdgeDB.from_id]", back_populates="from_node")
    edges_in = relationship("EdgeDB", foreign_keys="[EdgeDB.to_id]", back_populates="to_node")


class EdgeDB(Base):
    __tablename__ = "edges"

    id = Column(Integer, primary_key=True, index=True)
    from_id = Column(String, ForeignKey("nodes.id"))
    to_id = Column(String, ForeignKey("nodes.id"))
    distance = Column(Float)

    from_node = relationship("NodeDB", foreign_keys=[from_id], back_populates="edges_out")
    to_node = relationship("NodeDB", foreign_keys=[to_id], back_populates="edges_in")

import datetime
from sqlalchemy import DateTime

class AnalyticsEventDB(Base):
    __tablename__ = 'analytics_events'
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String, index=True)
    session_id = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
