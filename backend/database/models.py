"""
Database models for trading system - Simplified design
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, JSON, text
from sqlalchemy.sql import func
import uuid

from database.database import Base


class TradingAnalysis(Base):
    """一次完整的AI分析决策记录"""
    __tablename__ = "trading_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(String(36), nullable=False, default=lambda: str(uuid.uuid4()), unique=True, index=True)
    timestamp = Column(DateTime, nullable=False, default=func.now(), index=True)
    
    # AI分析结果
    overall_summary = Column(Text, nullable=True)  # AI的整体市场分析
    symbol_decisions = Column(JSON, nullable=False)  # 所有交易对的决策和执行结果
    duration_ms = Column(Float, nullable=True)  # 分析和执行总耗时
    
    # 元数据
    model_name = Column(String(50), nullable=False)  # AI模型名称
    error = Column(Text, nullable=True)  # 错误信息（如果有）
    created_at = Column(DateTime, nullable=False, default=func.now())
    
    def __repr__(self):
        return (f"TradingAnalysis(id={self.id}, analysis_id={self.analysis_id}, "
                f"symbols={len(self.symbol_decisions or {})})")


