"""
测试持仓匹配逻辑
"""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
script_dir = Path(__file__).parent
backend_dir = script_dir.parent
sys.path.insert(0, str(backend_dir))

env_file = backend_dir / ".env"
if env_file.exists():
    load_dotenv(env_file)

from trading import get_trader


async def test_position_matching():
    """测试持仓匹配逻辑"""
    
    try:
        trader = get_trader()
        
        # 1. 获取持仓
        positions = await trader.get_positions()
        print(f"持仓数量: {len(positions)}")
        
        # 2. 测试符号匹配
        test_symbols = ['SOLUSDT', 'ETHUSDT', 'BTCUSDT']
        
        for symbol in test_symbols:
            print(f"\n🔍 测试符号: {symbol}")
            
            # 寻找匹配的持仓
            matching_position = None
            for pos in positions:
                # 标准化符号比较
                pos_symbol_normalized = pos.symbol.replace('/', '').replace(':USDT', '')
                symbol_normalized = symbol.replace('/', '').replace(':USDT', '')
                
                print(f"  比较: '{pos_symbol_normalized}' vs '{symbol_normalized}'")
                
                if pos_symbol_normalized == symbol_normalized:
                    matching_position = pos
                    break
            
            if matching_position:
                print(f"  ✅ 找到匹配持仓:")
                print(f"    原始符号: {matching_position.symbol}")
                print(f"    方向: {matching_position.side}")
                print(f"    大小: {matching_position.size}")
                print(f"    盈亏: ${matching_position.unrealized_pnl:.2f}")
            else:
                print(f"  ❌ 未找到匹配持仓")
        
        # 3. 测试平仓功能
        print(f"\n🔧 测试 SOLUSDT 平仓功能...")
        try:
            await trader.close_long("SOLUSDT", 0)  # 尝试全部平仓
            print("✅ SOLUSDT 平多仓成功")
        except Exception as e:
            print(f"❌ SOLUSDT 平多仓失败: {e}")
        
        # 4. 检查平仓后的持仓
        print(f"\n🔍 检查平仓后的持仓...")
        final_positions = await trader.get_positions()
        print(f"最终持仓数量: {len(final_positions)}")
        
        for pos in final_positions:
            print(f"  {pos.symbol} {pos.side} 大小:{pos.size} 盈亏:${pos.unrealized_pnl:.2f}")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_position_matching())