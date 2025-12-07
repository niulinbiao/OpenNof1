"""
时区工具 - 统一处理时区转换
所有时间统一使用UTC存储，显示时转换为北京时间（UTC+8）
"""
from datetime import datetime, timezone, timedelta
from typing import Optional

# 北京时间时区（UTC+8）
BEIJING_TZ = timezone(timedelta(hours=8))


def now_utc() -> datetime:
    """获取当前UTC时间"""
    return datetime.now(timezone.utc)


def now_beijing() -> datetime:
    """获取当前北京时间"""
    return datetime.now(BEIJING_TZ)


def to_beijing(utc_time: datetime) -> datetime:
    """将UTC时间转换为北京时间"""
    if utc_time.tzinfo is None:
        # 如果没有时区信息，假设是UTC
        utc_time = utc_time.replace(tzinfo=timezone.utc)
    elif utc_time.tzinfo != timezone.utc:
        # 如果不是UTC，先转换为UTC
        utc_time = utc_time.astimezone(timezone.utc)
    return utc_time.astimezone(BEIJING_TZ)


def to_utc(beijing_time: datetime) -> datetime:
    """将北京时间转换为UTC时间"""
    if beijing_time.tzinfo is None:
        # 如果没有时区信息，假设是北京时间
        beijing_time = beijing_time.replace(tzinfo=BEIJING_TZ)
    elif beijing_time.tzinfo != BEIJING_TZ:
        # 如果不是北京时间，先转换为北京时间
        beijing_time = beijing_time.astimezone(BEIJING_TZ)
    return beijing_time.astimezone(timezone.utc)


def format_beijing_time(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """格式化时间为北京时间字符串"""
    if dt.tzinfo is None:
        # 如果没有时区信息，假设是UTC
        dt = dt.replace(tzinfo=timezone.utc)
    beijing_dt = to_beijing(dt)
    return beijing_dt.strftime(format_str)


def parse_utc_time(time_str: str) -> datetime:
    """解析时间字符串为UTC时间（如果字符串没有时区信息，假设是UTC）"""
    try:
        dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        # 如果解析失败，尝试其他格式
        try:
            dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
            return dt.replace(tzinfo=timezone.utc)
        except Exception:
            raise ValueError(f"无法解析时间字符串: {time_str}")
