"""
Multi-Timeframe Technical Analysis Tool for AI Agent
Uses TA-Lib for professional technical indicators across multiple timeframes
"""
import logging
import numpy as np
import talib
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from market.data_cache import kline_cache
from utils.logger import logger
from utils.timezone_utils import now_utc


def _generate_overall_signals(multi_timeframe_analysis: Dict[str, Dict]) -> Dict[str, Any]:
    """生成跨时间框架的综合信号"""
    overall_signals = {}
    
    # EMA 趋势分析
    ema20_above_ema50_count = 0
    total_timeframes = 0
    
    for timeframe, data in multi_timeframe_analysis.items():
        if "error" in data:
            continue
            
        if data.get("ema20") and data.get("ema50"):
            total_timeframes += 1
            if data["ema20"] > data["ema50"]:
                ema20_above_ema50_count += 1
    
    # 趋势一致性
    if total_timeframes > 0:
        trend_consistency = ema20_above_ema50_count / total_timeframes
        overall_signals["trend_direction"] = "上涨" if trend_consistency > 0.6 else "下跌" if trend_consistency < 0.4 else "震荡"
        overall_signals["trend_consistency"] = float(trend_consistency)
    
    # RSI 综合分析
    rsi7_values = []
    rsi14_values = []
    for timeframe, data in multi_timeframe_analysis.items():
        if data.get("rsi7") is not None:
            rsi7_values.append(data["rsi7"])
        if data.get("rsi14") is not None:
            rsi14_values.append(data["rsi14"])
    
    if rsi7_values:
        overall_signals["avg_rsi7"] = float(np.mean(rsi7_values))
        overall_signals["rsi7_signal"] = "超买" if overall_signals["avg_rsi7"] > 70 else "超卖" if overall_signals["avg_rsi7"] < 30 else "中性"
    
    if rsi14_values:
        overall_signals["avg_rsi14"] = float(np.mean(rsi14_values))
        overall_signals["rsi14_signal"] = "超买" if overall_signals["avg_rsi14"] > 70 else "超卖" if overall_signals["avg_rsi14"] < 30 else "中性"
    
    # MACD 跨时间框架分析
    macd_histograms = []
    for timeframe, data in multi_timeframe_analysis.items():
        if data.get("macd_histogram") is not None:
            macd_histograms.append(data["macd_histogram"])
    
    if macd_histograms:
        overall_signals["macd_consensus"] = "看涨" if np.mean(macd_histograms) > 0 else "看跌"
    
    # ADX 趋势强度综合分析
    adx_values = []
    for timeframe, data in multi_timeframe_analysis.items():
        if data.get("adx") is not None:
            adx_values.append(data["adx"])
    
    if adx_values:
        avg_adx = np.mean(adx_values)
        overall_signals["avg_adx"] = float(avg_adx)
        overall_signals["market_regime"] = "强趋势市场" if avg_adx > 25 else "震荡市场" if avg_adx < 20 else "中等趋势市场"
    
    # 布林带综合分析
    bb_positions = []
    for timeframe, data in multi_timeframe_analysis.items():
        if data.get("bb_position") is not None:
            bb_positions.append(data["bb_position"])
    
    if bb_positions:
        avg_bb_position = np.mean(bb_positions)
        overall_signals["avg_bb_position"] = float(avg_bb_position)
        overall_signals["bb_signal"] = "超买" if avg_bb_position > 0.8 else "超卖" if avg_bb_position < 0.2 else "正常"
    
    # OBV 成交量趋势综合分析
    obv_trends = []
    for timeframe, data in multi_timeframe_analysis.items():
        if data.get("obv_trend") is not None:
            obv_trends.append(data["obv_trend"])
    
    if obv_trends:
        bullish_count = sum(1 for trend in obv_trends if trend == "看涨")
        bearish_count = sum(1 for trend in obv_trends if trend == "看跌")
        overall_signals["obv_consensus"] = "看涨" if bullish_count > bearish_count else "看跌" if bearish_count > bullish_count else "中性"
    
    return overall_signals


def tech_analysis_tool(symbol: str) -> Dict[str, Any]:
    """
    Multi-timeframe technical analysis tool for AI agent using TA-Lib
    
    Args:
        symbol: Trading symbol (e.g., "BTCUSDT")
    
    Returns:
        Dict containing multi-timeframe technical analysis
    """
    try:
        from config.settings import config
        
        logger.info(f"获取 {symbol} 多时间框架技术分析数据")
        
        def get_klines_sync(timeframe):
            """同步方式获取指定时间框架的K线数据"""
            import asyncio
            loop = None
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # 如果事件循环正在运行，我们需要在新的循环中运行
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(lambda: asyncio.run(kline_cache.get_klines(symbol, timeframe, limit=200)))
                        return future.result()
                else:
                    return loop.run_until_complete(kline_cache.get_klines(symbol, timeframe, limit=200))
            except RuntimeError:
                # 创建新的事件循环
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(kline_cache.get_klines(symbol, timeframe, limit=200))
                    return result
                finally:
                    loop.close()
        
        # 分析多个时间框架
        multi_timeframe_analysis = {}
        
        for timeframe in config.agent.timeframes:
            klines = get_klines_sync(timeframe)
            logger.info(f"获取到 {symbol} {timeframe} {len(klines)} 根K线数据")
            
            # 分析单个时间框架
            if not klines:
                logger.warning(f"{symbol} {timeframe} 缓存中无数据")
                multi_timeframe_analysis[timeframe] = {
                    "error": "缓存中无数据",
                    "data_points": 0
                }
                continue
            
            # 提取价格数据为numpy数组
            closes = np.array([float(kline.close_price) for kline in klines], dtype=np.float64)
            highs = np.array([float(kline.high_price) for kline in klines], dtype=np.float64)
            lows = np.array([float(kline.low_price) for kline in klines], dtype=np.float64)
            volumes = np.array([float(kline.volume) for kline in klines], dtype=np.float64)
            
            current_price = closes[-1]
            price_change = closes[-1] - closes[-2] if len(closes) >= 2 else 0
            price_change_percent = (price_change / closes[-2] * 100) if len(closes) >= 2 and closes[-2] > 0 else 0
            
            # 使用 TA-Lib 计算核心技术指标
            timeframe_result = {
                "current_price": current_price,
                "price_change": price_change,
                "price_change_percent": price_change_percent,
                "data_points": len(klines),
                "latest_timestamp": klines[-1].timestamp.isoformat() if klines[-1].timestamp else None,
            }
            
            # EMA (20, 50)
            timeframe_result["ema20"] = talib.EMA(closes, timeperiod=20)[-1] if len(closes) >= 20 else None
            timeframe_result["ema50"] = talib.EMA(closes, timeperiod=50)[-1] if len(closes) >= 50 else None
            
            # MACD
            macd, macd_signal, macd_hist = talib.MACD(closes, fastperiod=12, slowperiod=26, signalperiod=9)
            timeframe_result["macd_line"] = macd[-1] if not np.isnan(macd[-1]) else None
            timeframe_result["signal_line"] = macd_signal[-1] if not np.isnan(macd_signal[-1]) else None
            timeframe_result["macd_histogram"] = macd_hist[-1] if not np.isnan(macd_hist[-1]) else None
            
            # RSI (7, 14)
            rsi7 = talib.RSI(closes, timeperiod=7)
            rsi14 = talib.RSI(closes, timeperiod=14)
            timeframe_result["rsi7"] = rsi7[-1] if not np.isnan(rsi7[-1]) else None
            timeframe_result["rsi14"] = rsi14[-1] if not np.isnan(rsi14[-1]) else None
            
            # NATR (Normalized Average True Range) - 标准化平均真实范围
            natr = talib.NATR(highs, lows, closes, timeperiod=14)
            timeframe_result["natr"] = natr[-1] if not np.isnan(natr[-1]) else None
            
            # 布林带 (Bollinger Bands) - 波动率和超买超卖指标
            if len(closes) >= 20:
                bb_upper, bb_middle, bb_lower = talib.BBANDS(closes, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)
                timeframe_result["bb_upper"] = bb_upper[-1] if not np.isnan(bb_upper[-1]) else None
                timeframe_result["bb_middle"] = bb_middle[-1] if not np.isnan(bb_middle[-1]) else None
                timeframe_result["bb_lower"] = bb_lower[-1] if not np.isnan(bb_lower[-1]) else None
                # 计算价格在布林带中的位置 (0-1之间，0.5表示中轨)
                if bb_upper[-1] and bb_lower[-1] and bb_upper[-1] != bb_lower[-1]:
                    bb_position = (current_price - bb_lower[-1]) / (bb_upper[-1] - bb_lower[-1])
                    timeframe_result["bb_position"] = float(bb_position)
                    timeframe_result["bb_signal"] = "超买" if bb_position > 0.8 else "超卖" if bb_position < 0.2 else "正常"
            
            # ADX (Average Directional Index) - 趋势强度指标
            if len(closes) >= 14:
                adx = talib.ADX(highs, lows, closes, timeperiod=14)
                timeframe_result["adx"] = adx[-1] if not np.isnan(adx[-1]) else None
                # ADX > 25 表示强趋势，< 20 表示震荡
                if adx[-1] and not np.isnan(adx[-1]):
                    timeframe_result["trend_strength"] = "强趋势" if adx[-1] > 25 else "弱趋势" if adx[-1] < 20 else "中等趋势"
            
            # OBV (On Balance Volume) - 成交量平衡指标
            if len(closes) > 0:
                obv = talib.OBV(closes, volumes)
                timeframe_result["obv"] = obv[-1] if not np.isnan(obv[-1]) else None
                # 计算OBV趋势（最近5个周期的斜率）
                if len(obv) >= 5:
                    obv_slope = (obv[-1] - obv[-5]) / 5 if obv[-5] != 0 else 0
                    timeframe_result["obv_trend"] = "看涨" if obv_slope > 0 else "看跌" if obv_slope < 0 else "中性"
            
            # VWAP (Volume Weighted Average Price) - 成交量加权平均价
            if len(closes) > 0:
                # 计算VWAP（简化版，使用最近50根K线）
                lookback = min(50, len(closes))
                vwap_data = closes[-lookback:]
                volume_data = volumes[-lookback:]
                if np.sum(volume_data) > 0:
                    vwap = np.sum(vwap_data * volume_data) / np.sum(volume_data)
                    timeframe_result["vwap"] = float(vwap)
                    # 价格相对VWAP的位置
                    vwap_ratio = (current_price - vwap) / vwap * 100 if vwap > 0 else 0
                    timeframe_result["vwap_ratio"] = float(vwap_ratio)
                    timeframe_result["vwap_signal"] = "高于VWAP" if vwap_ratio > 0 else "低于VWAP"
            
            # 支撑阻力位识别（使用最近的高点和低点）
            if len(highs) >= 20 and len(lows) >= 20:
                # 最近20根K线的最高价和最低价作为支撑阻力位
                recent_highs = highs[-20:]
                recent_lows = lows[-20:]
                resistance_level = float(np.max(recent_highs))
                support_level = float(np.min(recent_lows))
                timeframe_result["resistance_level"] = resistance_level
                timeframe_result["support_level"] = support_level
                # 计算当前价格距离支撑阻力位的距离百分比
                if resistance_level > support_level:
                    price_range = resistance_level - support_level
                    distance_to_resistance = (resistance_level - current_price) / price_range * 100
                    distance_to_support = (current_price - support_level) / price_range * 100
                    timeframe_result["distance_to_resistance_pct"] = float(distance_to_resistance)
                    timeframe_result["distance_to_support_pct"] = float(distance_to_support)
            
            multi_timeframe_analysis[timeframe] = timeframe_result
        
        # 生成跨时间框架的综合分析（使用UTC时间）
        result = {
            "symbol": symbol,
            "timeframes": multi_timeframe_analysis,
            "overall_signals": _generate_overall_signals(multi_timeframe_analysis),
            "analysis_timestamp": now_utc().isoformat()
        }
        
        
        logger.info(f"{symbol} 多时间框架技术分析完成")
        return result
        
    except Exception as e:
        logger.error(f"多时间框架技术分析失败 {symbol}: {e}")
        return {
            "symbol": symbol,
            "error": f"技术分析失败: {str(e)}",
            "timeframes": {},
            "overall_signals": {},
            "analysis_timestamp": now_utc().isoformat()
        }


# 创建 LangChain 工具实例
def create_tech_analysis_tool():
    """创建技术分析工具供 LangChain 使用"""
    from langchain_core.tools import Tool
    
    tool = Tool(
        name="tech_analysis_tool",
        description="获取交易标的的多时间框架技术分析数据，包括EMA20、EMA50、MACD、RSI7、RSI14、NATR（波动率）、布林带（BB）、ADX（趋势强度）、OBV（成交量平衡）、VWAP（成交量加权平均价）、支撑阻力位等核心技术指标，并提供跨时间框架的综合分析",
        func=tech_analysis_tool
    )
    
    return tool