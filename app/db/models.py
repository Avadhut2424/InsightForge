from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from app.db.session import Base

class KBChunk(Base):
    __tablename__ = 'kb_chunks'

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    # Using 384 dimension for BAAI/bge-small-en-v1.5
    embedding = Column(Vector(384), nullable=False)
    source_name = Column(Text, nullable=False)
    document_title = Column(Text)
    chunk_index = Column(Integer, nullable=False)
    metadata_ = Column("metadata", JSONB, default={})
    created_at = Column(DateTime, default=datetime.utcnow)

    # ivfflat index, can be reindexed later when data is populated
    __table_args__ = (
        Index('ix_kb_chunks_embedding', 'embedding', postgresql_using='ivfflat', postgresql_with={'lists': 100}),
    )

class ResearchRun(Base):
    __tablename__ = 'research_runs'

    id = Column(Integer, primary_key=True, index=True)
    status = Column(String, index=True, nullable=False)
    query = Column(Text, nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    metadata_ = Column("metadata", JSONB, default={})

    steps = relationship("AgentStep", back_populates="run")
    tool_calls = relationship("ToolCall", back_populates="run")
    revisions = relationship("Revision", back_populates="run")

class AgentStep(Base):
    __tablename__ = 'agent_steps'

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey('research_runs.id'), nullable=False, index=True)
    agent_name = Column(String, nullable=False)
    step_index = Column(Integer, nullable=False)
    status = Column(String, nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    input_summary = Column(JSONB)
    output_summary = Column(JSONB)

    run = relationship("ResearchRun", back_populates="steps")
    tool_calls = relationship("ToolCall", back_populates="step")

class ToolCall(Base):
    __tablename__ = 'tool_calls'

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey('research_runs.id'), nullable=False, index=True)
    step_id = Column(Integer, ForeignKey('agent_steps.id'), nullable=True, index=True)
    tool_name = Column(String, nullable=False)
    input_payload = Column(JSONB)
    output_payload = Column(JSONB)
    status = Column(String, nullable=False)
    called_at = Column(DateTime, default=datetime.utcnow)
    duration_ms = Column(Integer)

    run = relationship("ResearchRun", back_populates="tool_calls")
    step = relationship("AgentStep", back_populates="tool_calls")

class Revision(Base):
    __tablename__ = 'revisions'

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey('research_runs.id'), nullable=False, index=True)
    revision_number = Column(Integer, nullable=False)
    reason = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    run = relationship("ResearchRun", back_populates="revisions")
