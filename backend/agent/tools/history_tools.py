"""
历史交易表现分析工具 - 为AI Agent提供历史决策和表现数据
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from database.database import get_session_maker
from database.models import TradingAnalysis, BalanceSnapshot
from utils.logger import logger


def get_trading_history_tool(query: str = "") -> Dict[str, Any]:
    """
    获取历史交易决策和表现数据
    
    Args:
        query: 查询字符串，格式为 "symbol=SYMBOL&days=DAYS" 或空字符串使用默认值
               例如: "symbol=ETHUSDT&days=7" 或 "days=14" 或 ""
    
    Returns:
        Dict包含历史决策统计、胜率、平均盈亏等信息
    """
    try:
        # 解析查询参数
        symbol = None
        days = 7
        
        if query:
            # 简单解析 key=value 格式
            parts = query.split("&")
            for part in parts:
                if "=" in part:
                    key, value = part.split("=", 1)
                    key = key.strip().lower()
                    value = value.strip()
                    if key == "symbol" and value:
                        symbol = value.upper()
                    elif key == "days" and value.isdigit():
                        days = int(value)
        
        logger.info(f"获取历史交易数据: symbol={symbol}, days={days}")
        
        async def fetch_history():
            async with get_session_maker()() as session:
                # 计算查询时间范围
                start_time = datetime.now() - timedelta(days=days)
                
                # 查询交易分析记录
                query = select(TradingAnalysis).where(
                    TradingAnalysis.timestamp >= start_time
                ).order_by(TradingAnalysis.timestamp.desc())
                
                result = await session.execute(query)
                analyses = result.scalars().all()
                
                # 统计信息
                stats = {
                    "total_analyses": len(analyses),
                    "period_days": days,
                    "symbol": symbol or "ALL",
                    "start_time": start_time.isoformat(),
                    "end_time": datetime.now().isoformat(),
                }
                
                # 按标的统计决策
                symbol_stats = {}
                action_counts = {"OPEN_LONG": 0, "OPEN_SHORT": 0, "CLOSE_LONG": 0, "CLOSE_SHORT": 0, "HOLD": 0}
                
                for analysis in analyses:
                    if not analysis.symbol_decisions:
                        continue
                    
                    for sym, decision in analysis.symbol_decisions.items():
                        # 如果指定了symbol，只统计该标的
                        if symbol and sym != symbol:
                            continue
                        
                        if sym not in symbol_stats:
                            symbol_stats[sym] = {
                                "total_decisions": 0,
                                "actions": {"OPEN_LONG": 0, "OPEN_SHORT": 0, "CLOSE_LONG": 0, "CLOSE_SHORT": 0, "HOLD": 0},
                                "recent_decisions": []
                            }
                        
                        action = decision.get("action", "HOLD")
                        symbol_stats[sym]["total_decisions"] += 1
                        symbol_stats[sym]["actions"][action] = symbol_stats[sym]["actions"].get(action, 0) + 1
                        action_counts[action] = action_counts.get(action, 0) + 1
                        
                        # 保存最近10个决策
                        if len(symbol_stats[sym]["recent_decisions"]) < 10:
                            symbol_stats[sym]["recent_decisions"].append({
                                "timestamp": analysis.timestamp.isoformat(),
                                "action": action,
                                "reasoning": decision.get("reasoning", "")[:200],  # 限制长度
                                "execution_status": decision.get("execution_status", "unknown")
                            })
                
                # 查询账户快照计算盈亏
                balance_query = select(BalanceSnapshot).where(
                    BalanceSnapshot.timestamp >= start_time
                ).order_by(BalanceSnapshot.timestamp)
                
                balance_result = await session.execute(balance_query)
                snapshots = balance_result.scalars().all()
                
                balance_changes = []
                if len(snapshots) >= 2:
                    initial_balance = snapshots[0].total_balance
                    final_balance = snapshots[-1].total_balance
                    total_change = final_balance - initial_balance
                    total_change_pct = (total_change / initial_balance * 100) if initial_balance > 0 else 0
                    
                    balance_changes = {
                        "initial_balance": float(initial_balance),
                        "final_balance": float(final_balance),
                        "total_change": float(total_change),
                        "total_change_pct": float(total_change_pct),
                        "snapshot_count": len(snapshots)
                    }
                
                return {
                    "stats": stats,
                    "action_counts": action_counts,
                    "symbol_stats": symbol_stats,
                    "balance_changes": balance_changes,
                    "summary": _generate_summary(stats, action_counts, symbol_stats, balance_changes)
                }
        
        # 同步执行异步查询
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(lambda: asyncio.run(fetch_history()))
                    return future.result()
            else:
                return loop.run_until_complete(fetch_history())
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(fetch_history())
            finally:
                loop.close()
        
    except Exception as e:
        logger.error(f"获取历史交易数据失败: {e}")
        return {
            "error": f"获取历史数据失败: {str(e)}",
            "stats": {},
            "action_counts": {},
            "symbol_stats": {},
            "balance_changes": {},
            "summary": "无法获取历史数据"
        }


def _generate_summary(stats: Dict, action_counts: Dict, symbol_stats: Dict, balance_changes: Dict) -> str:
    """生成历史表现摘要"""
    summary_parts = []
    
    summary_parts.append(f"过去{stats['period_days']}天共进行了{stats['total_analyses']}次分析")
    
    # 决策分布
    total_actions = sum(action_counts.values())
    if total_actions > 0:
        hold_pct = (action_counts.get("HOLD", 0) / total_actions * 100)
        open_pct = ((action_counts.get("OPEN_LONG", 0) + action_counts.get("OPEN_SHORT", 0)) / total_actions * 100)
        summary_parts.append(f"决策分布: HOLD {hold_pct:.1f}%, 开仓 {open_pct:.1f}%")
    
    # 账户变化
    if balance_changes:
        change_pct = balance_changes.get("total_change_pct", 0)
        change_str = f"盈利 {change_pct:.2f}%" if change_pct > 0 else f"亏损 {abs(change_pct):.2f}%"
        summary_parts.append(f"账户变化: {change_str}")
    
    # 各标的活跃度
    if symbol_stats:
        active_symbols = [sym for sym, data in symbol_stats.items() if data["total_decisions"] > 0]
        if active_symbols:
            summary_parts.append(f"活跃标的: {', '.join(active_symbols)}")
    
    return " | ".join(summary_parts)


# 创建 LangChain 工具实例
def create_trading_history_tool():
    """创建历史交易分析工具供 LangChain 使用"""
    from langchain_core.tools import Tool
    
    tool = Tool(
        name="trading_history_tool",
        description="获取历史交易决策和表现数据，包括最近N天的决策统计、胜率、账户盈亏变化等，帮助AI了解历史表现并改进决策策略。调用格式：'symbol=SYMBOL&days=DAYS' 或 'days=DAYS' 或 ''（使用默认值）。例如：'symbol=ETHUSDT&days=7' 或 'days=14'",
        func=get_trading_history_tool
    )
    
    return tool
