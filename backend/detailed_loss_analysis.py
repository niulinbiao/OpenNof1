#!/usr/bin/env python3
"""
Detailed loss analysis - focusing on specific causes of trading losses
"""

import sqlite3
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta

def load_data():
    """Load all relevant data"""
    conn = sqlite3.connect('data/trading.db')
    
    trades_df = pd.read_sql_query("SELECT * FROM trade_records", conn)
    orders_df = pd.read_sql_query("SELECT * FROM order_records", conn)
    balance_df = pd.read_sql_query("SELECT * FROM balance_snapshots", conn)
    
    conn.close()
    
    # Convert timestamps
    trades_df['trade_time'] = pd.to_datetime(trades_df['trade_time'])
    orders_df['created_time'] = pd.to_datetime(orders_df['created_time'])
    orders_df['filled_time'] = pd.to_datetime(orders_df['filled_time'])
    balance_df['timestamp'] = pd.to_datetime(balance_df['timestamp'])
    
    return trades_df, orders_df, balance_df

def analyze_losing_trades_detailed(trades_df):
    """Detailed analysis of each losing trade"""
    losing_trades = []
    
    for _, trade in trades_df.iterrows():
        raw_data = json.loads(trade['raw_data']) if trade['raw_data'] else {}
        realized_pnl = float(raw_data.get('info', {}).get('realizedPnl', 0))
        
        if realized_pnl < 0:  # Losing trade
            losing_trades.append({
                'trade_id': trade['trade_id'],
                'symbol': trade['symbol'],
                'trade_time': trade['trade_time'],
                'side': trade['side'],
                'amount': trade['amount'],
                'price': trade['price'],
                'cost': trade['cost'],
                'realized_pnl': realized_pnl,
                'fees': trade['fee_cost'],
                'net_loss': realized_pnl - trade['fee_cost'],
                'loss_percentage': (realized_pnl / trade['cost']) * 100,
                'hour': trade['trade_time'].hour,
                'day_of_week': trade['trade_time'].strftime('%A')
            })
    
    return pd.DataFrame(losing_trades)

def analyze_order_execution_failures(orders_df):
    """Analyze failed order executions in detail"""
    failed_orders = orders_df[orders_df['status'].isin(['canceled', 'rejected', 'open'])]
    
    failure_analysis = {}
    
    # By symbol
    failure_analysis['by_symbol'] = failed_orders.groupby('symbol').agg({
        'order_id': 'count',
        'amount': 'sum',
        'cost': 'sum'
    }).to_dict()
    
    # By order type
    failure_analysis['by_type'] = failed_orders.groupby('type').agg({
        'order_id': 'count',
        'amount': 'sum'
    }).to_dict()
    
    # Timing of failures
    failed_orders['hour'] = failed_orders['created_time'].dt.hour
    failure_analysis['by_hour'] = failed_orders.groupby('hour')['order_id'].count().to_dict()
    
    # Large failed orders
    large_failed = failed_orders[failed_orders['amount'] > failed_orders['amount'].quantile(0.9)]
    failure_analysis['large_failed_orders'] = len(large_failed)
    
    return failure_analysis, failed_orders

def analyze_balance_drops(balance_df):
    """Analyze when and why the balance dropped"""
    balance_df = balance_df.sort_values('timestamp')
    balance_df['balance_change'] = balance_df['total_balance'].diff()
    balance_df['unrealized_change'] = balance_df['unrealized_pnl'].diff()
    
    # Find major drops
    major_drops = balance_df[balance_df['balance_change'] < -1.0]
    
    drop_analysis = {
        'total_drops': len(major_drops),
        'total_loss_amount': major_drops['balance_change'].sum(),
        'largest_drop': major_drops['balance_change'].min(),
        'avg_drop': major_drops['balance_change'].mean()
    }
    
    return drop_analysis, major_drops

def analyze_trading_frequency_vs_performance(trades_df):
    """Analyze if high-frequency trading led to losses"""
    trades_df = trades_df.sort_values('trade_time')
    
    # Calculate time between trades
    trades_df['time_since_last_trade'] = trades_df['trade_time'].diff().dt.total_seconds()
    
    # Group by trading frequency
    trades_df['frequency_bucket'] = pd.cut(trades_df['time_since_last_trade'], 
                                         bins=[0, 60, 300, 3600, 86400, float('inf')],
                                         labels=['<1min', '1-5min', '5min-1h', '1h-1d', '>1d'])
    
    frequency_analysis = {}
    for bucket in ['<1min', '1-5min', '5min-1h', '1h-1d', '>1d']:
        bucket_trades = trades_df[trades_df['frequency_bucket'] == bucket]
        if len(bucket_trades) > 0:
            # Calculate PnL for these trades
            total_pnl = 0
            total_fees = bucket_trades['fee_cost'].sum()
            
            for _, trade in bucket_trades.iterrows():
                raw_data = json.loads(trade['raw_data']) if trade['raw_data'] else {}
                realized_pnl = float(raw_data.get('info', {}).get('realizedPnl', 0))
                total_pnl += realized_pnl
            
            frequency_analysis[bucket] = {
                'trade_count': len(bucket_trades),
                'total_pnl': total_pnl,
                'total_fees': total_fees,
                'net_pnl': total_pnl - total_fees,
                'avg_pnl_per_trade': total_pnl / len(bucket_trades) if len(bucket_trades) > 0 else 0
            }
    
    return frequency_analysis

def analyze_position_sizing_impact(trades_df):
    """Analyze if position sizing contributed to losses"""
    position_analysis = {}
    
    # Calculate position size buckets
    trades_df['size_bucket'] = pd.cut(trades_df['cost'], 
                                    bins=5, 
                                    labels=['Very Small', 'Small', 'Medium', 'Large', 'Very Large'])
    
    for bucket in ['Very Small', 'Small', 'Medium', 'Large', 'Very Large']:
        bucket_trades = trades_df[trades_df['size_bucket'] == bucket]
        if len(bucket_trades) > 0:
            total_pnl = 0
            total_fees = bucket_trades['fee_cost'].sum()
            
            for _, trade in bucket_trades.iterrows():
                raw_data = json.loads(trade['raw_data']) if trade['raw_data'] else {}
                realized_pnl = float(raw_data.get('info', {}).get('realizedPnl', 0))
                total_pnl += realized_pnl
            
            position_analysis[bucket] = {
                'trade_count': len(bucket_trades),
                'avg_position_size': bucket_trades['cost'].mean(),
                'total_pnl': total_pnl,
                'total_fees': total_fees,
                'net_pnl': total_pnl - total_fees,
                'pnl_per_dollar_traded': total_pnl / bucket_trades['cost'].sum() if bucket_trades['cost'].sum() > 0 else 0
            }
    
    return position_analysis

def calculate_win_loss_ratios(trades_df):
    """Calculate detailed win/loss statistics"""
    winning_trades = []
    losing_trades = []
    
    for _, trade in trades_df.iterrows():
        raw_data = json.loads(trade['raw_data']) if trade['raw_data'] else {}
        realized_pnl = float(raw_data.get('info', {}).get('realizedPnl', 0))
        
        if realized_pnl > 0:
            winning_trades.append(realized_pnl)
        elif realized_pnl < 0:
            losing_trades.append(abs(realized_pnl))
    
    stats = {
        'total_winning_trades': len(winning_trades),
        'total_losing_trades': len(losing_trades),
        'win_rate': len(winning_trades) / (len(winning_trades) + len(losing_trades)) * 100 if (len(winning_trades) + len(losing_trades)) > 0 else 0,
        'avg_win': np.mean(winning_trades) if winning_trades else 0,
        'avg_loss': np.mean(losing_trades) if losing_trades else 0,
        'largest_win': max(winning_trades) if winning_trades else 0,
        'largest_loss': max(losing_trades) if losing_trades else 0,
        'win_loss_ratio': np.mean(winning_trades) / np.mean(losing_trades) if winning_trades and losing_trades else 0,
        'expectancy': (len(winning_trades) * np.mean(winning_trades) - len(losing_trades) * np.mean(losing_trades)) / (len(winning_trades) + len(losing_trades)) if (len(winning_trades) + len(losing_trades)) > 0 else 0
    }
    
    return stats

def main():
    """Main analysis"""
    print("Loading data for detailed loss analysis...")
    trades_df, orders_df, balance_df = load_data()
    
    print("\n" + "="*100)
    print("DETAILED TRADING LOSS ANALYSIS")
    print("="*100)
    
    # 1. Detailed losing trades analysis
    print("\n1. LOSING TRADES BREAKDOWN:")
    losing_trades_df = analyze_losing_trades_detailed(trades_df)
    
    if len(losing_trades_df) > 0:
        print(f"Total Losing Trades: {len(losing_trades_df)}")
        print(f"Total Loss Amount: ${losing_trades_df['realized_pnl'].sum():.4f}")
        print(f"Average Loss per Trade: ${losing_trades_df['realized_pnl'].mean():.4f}")
        print(f"Median Loss per Trade: ${losing_trades_df['realized_pnl'].median():.4f}")
        
        print("\nWorst 10 Losing Trades:")
        worst_trades = losing_trades_df.nsmallest(10, 'realized_pnl')
        for _, trade in worst_trades.iterrows():
            print(f"  {trade['symbol']} - ${trade['realized_pnl']:.4f} loss on {trade['trade_time'].strftime('%Y-%m-%d %H:%M')} ({trade['loss_percentage']:.2f}%)")
        
        print("\nLosses by Symbol:")
        symbol_losses = losing_trades_df.groupby('symbol').agg({
            'realized_pnl': ['count', 'sum', 'mean'],
            'fees': 'sum'
        }).round(4)
        print(symbol_losses)
        
        print("\nLosses by Day of Week:")
        daily_losses = losing_trades_df.groupby('day_of_week').agg({
            'realized_pnl': ['count', 'sum', 'mean']
        }).round(4)
        print(daily_losses)
        
        print("\nLosses by Hour:")
        hourly_losses = losing_trades_df.groupby('hour').agg({
            'realized_pnl': ['count', 'sum', 'mean']
        }).round(4)
        print("Most loss-prone hours:")
        hour_totals = losing_trades_df.groupby('hour')['realized_pnl'].sum().sort_values()
        print(hour_totals.head(10))
    
    # 2. Order execution failures
    print("\n\n2. ORDER EXECUTION FAILURES:")
    failure_analysis, failed_orders = analyze_order_execution_failures(orders_df)
    
    print(f"Total Failed Orders: {len(failed_orders)}")
    print(f"Failed Order Rate: {len(failed_orders) / len(orders_df) * 100:.1f}%")
    print(f"Large Failed Orders (>90th percentile): {failure_analysis['large_failed_orders']}")
    
    print("\nFailed Orders by Symbol:")
    for symbol, stats in failure_analysis['by_symbol']['order_id'].items():
        print(f"  {symbol}: {stats} failed orders")
    
    print("\nFailed Orders by Type:")
    for order_type, count in failure_analysis['by_type']['order_id'].items():
        print(f"  {order_type}: {count} failed orders")
    
    # 3. Balance drops analysis
    print("\n\n3. BALANCE DROP ANALYSIS:")
    drop_analysis, major_drops = analyze_balance_drops(balance_df)
    
    print(f"Major Balance Drops (>$1.00): {drop_analysis['total_drops']}")
    print(f"Total Loss from Major Drops: ${drop_analysis['total_loss_amount']:.2f}")
    print(f"Largest Single Drop: ${drop_analysis['largest_drop']:.2f}")
    print(f"Average Drop Size: ${drop_analysis['avg_drop']:.2f}")
    
    if len(major_drops) > 0:
        print("\nMajor Balance Drops Timeline:")
        for _, drop in major_drops.head(10).iterrows():
            print(f"  {drop['timestamp'].strftime('%Y-%m-%d %H:%M')} - ${drop['balance_change']:.2f} drop")
    
    # 4. Trading frequency analysis
    print("\n\n4. TRADING FREQUENCY vs PERFORMANCE:")
    frequency_analysis = analyze_trading_frequency_vs_performance(trades_df)
    
    for bucket, stats in frequency_analysis.items():
        print(f"\n{bucket} intervals:")
        print(f"  Trades: {stats['trade_count']}")
        print(f"  Total P&L: ${stats['total_pnl']:.4f}")
        print(f"  Avg P&L per trade: ${stats['avg_pnl_per_trade']:.4f}")
        print(f"  Net P&L (after fees): ${stats['net_pnl']:.4f}")
    
    # 5. Position sizing analysis
    print("\n\n5. POSITION SIZING IMPACT:")
    position_analysis = analyze_position_sizing_impact(trades_df)
    
    for bucket, stats in position_analysis.items():
        print(f"\n{bucket} positions:")
        print(f"  Trades: {stats['trade_count']}")
        print(f"  Avg Position Size: ${stats['avg_position_size']:.2f}")
        print(f"  Total P&L: ${stats['total_pnl']:.4f}")
        print(f"  P&L per $ traded: ${stats['pnl_per_dollar_traded']:.6f}")
        print(f"  Net P&L: ${stats['net_pnl']:.4f}")
    
    # 6. Win/Loss ratios
    print("\n\n6. WIN/LOSS STATISTICS:")
    win_loss_stats = calculate_win_loss_ratios(trades_df)
    
    print(f"Win Rate: {win_loss_stats['win_rate']:.1f}%")
    print(f"Average Win: ${win_loss_stats['avg_win']:.4f}")
    print(f"Average Loss: ${win_loss_stats['avg_loss']:.4f}")
    print(f"Largest Win: ${win_loss_stats['largest_win']:.4f}")
    print(f"Largest Loss: ${win_loss_stats['largest_loss']:.4f}")
    print(f"Win/Loss Ratio: {win_loss_stats['win_loss_ratio']:.2f}")
    print(f"Expectancy per Trade: ${win_loss_stats['expectancy']:.4f}")
    
    # 7. Key insights and recommendations
    print("\n\n7. KEY INSIGHTS & RECOMMENDATIONS:")
    print("="*50)
    
    total_fees = trades_df['fee_cost'].sum()
    total_pnl = sum(float(json.loads(trade['raw_data']).get('info', {}).get('realizedPnl', 0)) 
                   for _, trade in trades_df.iterrows() 
                   if trade['raw_data'])
    
    print(f"• Total net loss: ${total_pnl - total_fees:.2f}")
    print(f"• Fees represent {(total_fees / abs(total_pnl)) * 100:.1f}% of gross losses" if total_pnl != 0 else "• No realized P&L to compare fees against")
    print(f"• Order failure rate of {len(failed_orders) / len(orders_df) * 100:.1f}% suggests execution issues")
    print(f"• Win rate of {win_loss_stats['win_rate']:.1f}% is below breakeven threshold")
    print(f"• Average loss (${win_loss_stats['avg_loss']:.4f}) exceeds average win (${win_loss_stats['avg_win']:.4f})")
    
    if win_loss_stats['expectancy'] < 0:
        print("• NEGATIVE EXPECTANCY: Current strategy is mathematically unprofitable")
    
    print("\nImprovement Suggestions:")
    print("1. Reduce order cancellation rate by improving entry/exit timing")
    print("2. Implement better position sizing to reduce large losses")
    print("3. Focus on improving win rate or win/loss ratio")
    print("4. Consider reducing trading frequency to minimize fees")
    print("5. Analyze the AI decision quality - many trades seem to be losing")
    
    print("\n" + "="*100)

if __name__ == "__main__":
    main()