"""
提示词管理服务 - 三层优先级：数据库 > 配置文件 > 代码默认
"""
import logging
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.database import get_session_maker
from database.models import SystemConfig
from config.settings import config

logger = logging.getLogger("AlphaTransformer")

# 代码默认的交易策略
DEFAULT_TRADING_STRATEGY = """

策略前提／风控设定:
- 单一币种一次建仓最大不超过 可用余额 的 20%。  
- 止损／止盈设定: 以小时级 NATR 为单位 (例如用当前 NATR * k)，盈亏比设为 2:1。  
- 不要随意建仓 —— 只有当所有关键指标一致指向同一方向时 (趋势、波动性、量／成交、动能 等) 才考虑建仓。  
- 不要随意主动平仓 —— 已设置止损／止盈后，除非出现强烈趋势反转信号，否则维持持仓。  

入场逻辑 (开多／开空):
- 计算近期 NATR (例如过去 14 根小时线)，并根据当前价格波动与 NATR 判断市场是否处于“合适波动／趋势启动”阶段。  
- 如果 NATR 显著上升 (例如突破其近期均值)，说明波动性放大 → 市场可能进入大幅波动阶段，适合趋势交易或突破交易。  
- 同时确认趋势方向 (可以用趋势指标，比如均线、动量、ADX／DI／MACD 等) 和成交量／动能辅助信号 —— 只有当趋势与波动性和动量共同指向同一方向时，才考虑建仓。  

止损／止盈逻辑:
- 止损设置为入场价 ± (NATR * k1)，止盈设置为入场价 + (方向 × NATR * k2)，且 k2 ≈ 2 * k1 以符合盈亏比 2:1。  
- 随着价格移动，可以考虑将止损跟踪 (trailing stop) —— 例如用波动性停止 (类似于 “Volatility Stop / Chandelier Exit” 思路，用 NATR 或 ATR 动态调整止损), 以保护盈利。  

平仓／加仓规则:
- 不主动平仓，除非有强烈趋势反转信号 (例如趋势指标反转 + 波动性下降 + 动量逆转／成交量萎缩)。  
- 若价格朝有利方向运行，可考虑分批加仓 (不过总仓位仍 ≤ 可用余额 20%)。  
- 加仓／加仓前也必须满足所有指标一致 (趋势 + 波动 + 动量 + 成交量 等) 。  

风险控制／资金管理:
- 总仓位风险分散 —— 不把所有资金压在一个币种或一个方向上。  
- 使用 NATR 作为 “波动性滤波器 (volatility filter)” —— 若 NATR 太低 (行情太平)，避免入场；若 NATR 太高 (过度波动或躁动)，适当缩减仓位或等待稳定。  
- 保持冷静 / 避免情绪交易 (遵守规则，不被 FOMO 诱惑) 。  

记录／复盘:
- 每次入场／出场都记录 NATR 值、入场价、止损价、止盈价、成交量、趋势／动量指标值。  
- 定期统计胜率、盈亏比、最大回撤、每笔交易波动性 (NATR 倍数) 等，以评估策略表现、优化参数。  


"""

# 缓存配置
_strategy_cache: Optional[str] = None
_cache_valid = False

async def get_trading_strategy() -> str:
    """
    获取交易策略配置，按优先级：数据库 > 配置文件 > 代码默认
    """
    global _strategy_cache, _cache_valid
    
    # 先检查缓存
    if _cache_valid and _strategy_cache is not None:
        return _strategy_cache
    
    try:
        # 1. 优先级最高：检查数据库
        async with get_session_maker()() as session:
            result = await session.execute(
                select(SystemConfig).where(SystemConfig.key == "trading_strategy")
            )
            config_row = result.scalar_one_or_none()
            
            if config_row and config_row.value.strip():
                logger.info("使用数据库中的交易策略配置")
                _strategy_cache = config_row.value.strip()
                _cache_valid = True
                return _strategy_cache
    
    except Exception as e:
        logger.warning(f"读取数据库交易策略失败: {e}")
    
    # 2. 次优先级：检查配置文件
    try:
        config_strategy = getattr(config.agent, 'trading_strategy', None)
        if config_strategy and config_strategy.strip():
            logger.info("使用配置文件中的交易策略配置")
            _strategy_cache = config_strategy.strip()
            _cache_valid = True
            return _strategy_cache
    except Exception as e:
        logger.warning(f"读取配置文件交易策略失败: {e}")
    
    # 3. 最低优先级：使用代码默认
    logger.info("使用代码默认的交易策略配置")
    _strategy_cache = DEFAULT_TRADING_STRATEGY
    _cache_valid = True
    return _strategy_cache

async def set_trading_strategy(strategy: str) -> bool:
    """
    设置用户自定义的交易策略（存储到数据库）
    """
    global _strategy_cache, _cache_valid
    
    try:
        if not strategy or not strategy.strip():
            raise ValueError("交易策略内容不能为空")
        
        strategy = strategy.strip()
        
        async with get_session_maker()() as session:
            # 查找现有配置
            result = await session.execute(
                select(SystemConfig).where(SystemConfig.key == "trading_strategy")
            )
            config_row = result.scalar_one_or_none()
            
            if config_row:
                # 更新现有配置
                config_row.value = strategy
                logger.info("更新数据库中的交易策略配置")
            else:
                # 创建新配置
                new_config = SystemConfig(
                    key="trading_strategy",
                    value=strategy,
                    description="用户自定义的交易策略配置"
                )
                session.add(new_config)
                logger.info("创建新的交易策略配置")
            
            await session.commit()
            
            # 清除缓存，强制下次重新读取
            _strategy_cache = None
            _cache_valid = False
            
            return True
            
    except Exception as e:
        logger.error(f"设置交易策略失败: {e}")
        return False

def clear_strategy_cache():
    """清除策略缓存（用于测试或强制刷新）"""
    global _strategy_cache, _cache_valid
    _strategy_cache = None
    _cache_valid = False
    logger.info("交易策略缓存已清除")