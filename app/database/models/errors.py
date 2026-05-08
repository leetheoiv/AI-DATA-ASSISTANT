from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class ErrorLog(Base):
    __tablename__ = "error_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String)
    agent_name = Column(String)

    # This is where we store those last two lines of the error
    error_snippet = Column(Text)
    created_at = Column(DateTime, default=datetime.timestamp)