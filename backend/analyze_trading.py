#!/usr/bin/env python3
"""
Comprehensive trading analysis script
Analyzes all trading data from the trading.db database
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime
import json
from collections import defaultdict

def load_trading_data(db_path):
    """Load all trading data from database"""
    conn = sqlite3.connect(db_path)
    
    # Load all tables
    trades_df = pd.read_sql_query("SELECT * FROM trade_records", conn)
    orders_df = pd.read_sql_query("SELECT * FROM order_records", conn)
    balance_df = pd.read_sql_query("SELECT * FROM balance_snapshots", conn)
    analyses_df = pd.read_sql_query("SELECT * FROM trading_analyses", conn)
    
    conn.close()
    
    # Convert timestamps
    trades_df['trade_time'] = pd.to_datetime(trades_df['trade_time'])
    trades_df['created_at'] = pd.to_datetime(trades_df['created_at'])
    orders_df['created_time'] = pd.to_datetime(orders_df['created_time'])
    orders_df['filled_time'] = pd.to_datetime(orders_df['filled_time'])
    balance_df['timestamp'] = pd.to_datetime(balance_df['timestamp'])
    analyses_df['timestamp'] = pd.to_datetime(analyses_df['timestamp'])
    
    return trades_df, orders_df, balance_df, analyses_df

def calculate_trade_pnl(trades_df):
    """Calculate P&L for each completed trade"""
    trade_results = []
    
    # Group trades by symbol and analyze pairs
    for symbol in trades_df['symbol'].unique():
        symbol_trades = trades_df[trades_df['symbol'] == symbol].sort_values('trade_time')
        
        # Track positions
        position = 0
        avg_entry_price = 0
        entry_cost = 0
        
        for _, trade in symbol_trades.iterrows():
            if trade['side'] == 'buy':
                # Opening/adding to long position
                if position >= 0:
                    # Calculate new average entry price
                    total_cost = entry_cost + trade['cost']
                    total_amount = position + trade['amount']
                    avg_entry_price = total_cost / total_amount if total_amount > 0 else trade['price']
                    entry_cost = total_cost
                    position = total_amount
                else:
                    # Closing short position
                    close_amount = min(abs(position), trade['amount'])
                    pnl = close_amount * (avg_entry_price - trade['price']) - trade['fee_cost']
                    
                    trade_results.append({
                        'symbol': symbol,
                        'trade_id': trade['trade_id'],
                        'entry_time': None,  # We'll need to track this better
                        'exit_time': trade['trade_time'],
                        'side': 'SHORT',
                        'amount': close_amount,
                        'entry_price': avg_entry_price,
                        'exit_price': trade['price'],
                        'pnl': pnl,
                        'fees': trade['fee_cost'],
                        'duration_hours': None
                    })
                    
                    position += trade['amount']  # Remaining position after close
                    
            else:  # sell
                # Opening/adding to short position
                if position <= 0:
                    # Calculate new average entry price for short
                    if position == 0:
                        avg_entry_price = trade['price']
                        entry_cost = trade['cost']
                        position = -trade['amount']
                    else:
                        total_cost = entry_cost + trade['cost']
                        total_amount = abs(position) + trade['amount']
                        avg_entry_price = total_cost / total_amount if total_amount > 0 else trade['price']
                        entry_cost = total_cost
                        position = -total_amount
                else:
                    # Closing long position
                    close_amount = min(position, trade['amount'])
                    pnl = close_amount * (trade['price'] - avg_entry_price) - trade['fee_cost']
                    
                    trade_results.append({
                        'symbol': symbol,
                        'trade_id': trade['trade_id'],
                        'entry_time': None,
                        'exit_time': trade['trade_time'],
                        'side': 'LONG',
                        'amount': close_amount,
                        'entry_price': avg_entry_price,
                        'exit_price': trade['price'],
                        'pnl': pnl,
                        'fees': trade['fee_cost'],
                        'duration_hours': None
                    })
                    
                    position -= trade['amount']  # Remaining position after close
    
    return pd.DataFrame(trade_results)

def analyze_realized_pnl_from_trades(trades_df):
    """Analyze realized P&L from the raw trade data which includes realized_pnl"""
    pnl_trades = []
    
    for _, trade in trades_df.iterrows():
        raw_data = json.loads(trade['raw_data']) if trade['raw_data'] else {}
        realized_pnl = float(raw_data.get('info', {}).get('realizedPnl', 0))
        
        if realized_pnl != 0:  # Only trades that actually closed positions
            pnl_trades.append({
                'symbol': trade['symbol'],
                'trade_id': trade['trade_id'],
                'trade_time': trade['trade_time'],
                'side': trade['side'],
                'amount': trade['amount'],
                'price': trade['price'],
                'realized_pnl': realized_pnl,
                'fees': trade['fee_cost'],
                'net_pnl': realized_pnl - trade['fee_cost']
            })
    
    return pd.DataFrame(pnl_trades)

def analyze_balance_changes(balance_df):
    """Analyze account balance changes over time"""
    balance_df = balance_df.sort_values('timestamp')
    
    # Calculate changes
    balance_df['balance_change'] = balance_df['total_balance'].diff()
    balance_df['unrealized_change'] = balance_df['unrealized_pnl'].diff()
    
    # Find significant balance drops (losses)
    significant_drops = balance_df[balance_df['balance_change'] < -0.5]
    
    return balance_df, significant_drops

def analyze_trading_patterns(trades_df, pnl_df):
    """Analyze patterns in trading behavior and outcomes"""
    patterns = {}
    
    # By symbol
    patterns['by_symbol'] = {}
    for symbol in trades_df['symbol'].unique():
        symbol_trades = trades_df[trades_df['symbol'] == symbol]
        symbol_pnl = pnl_df[pnl_df['symbol'] == symbol] if len(pnl_df) > 0 else pd.DataFrame()
        
        patterns['by_symbol'][symbol] = {
            'total_trades': len(symbol_trades),
            'total_volume': symbol_trades['cost'].sum(),
            'total_fees': symbol_trades['fee_cost'].sum(),
            'realized_pnl': symbol_pnl['realized_pnl'].sum() if len(symbol_pnl) > 0 else 0,
            'net_pnl': symbol_pnl['net_pnl'].sum() if len(symbol_pnl) > 0 else 0,
            'winning_trades': len(symbol_pnl[symbol_pnl['realized_pnl'] > 0]) if len(symbol_pnl) > 0 else 0,
            'losing_trades': len(symbol_pnl[symbol_pnl['realized_pnl'] < 0]) if len(symbol_pnl) > 0 else 0
        }
    
    # By time periods
    trades_df['hour'] = trades_df['trade_time'].dt.hour
    trades_df['day_of_week'] = trades_df['trade_time'].dt.dayofweek
    
    patterns['by_hour'] = trades_df.groupby('hour').agg({
        'trade_id': 'count',
        'cost': 'sum',
        'fee_cost': 'sum'
    }).to_dict()
    
    patterns['by_day'] = trades_df.groupby('day_of_week').agg({
        'trade_id': 'count',
        'cost': 'sum',
        'fee_cost': 'sum'
    }).to_dict()
    
    return patterns

def analyze_order_execution(orders_df):
    """Analyze order execution efficiency and failures"""
    execution_analysis = {}
    
    # Order status breakdown
    execution_analysis['status_breakdown'] = orders_df['status'].value_counts().to_dict()
    
    # Fill rates
    filled_orders = orders_df[orders_df['status'] == 'closed']
    execution_analysis['avg_fill_rate'] = (filled_orders['filled'] / filled_orders['amount']).mean()
    
    # Failed orders
    failed_orders = orders_df[orders_df['status'].isin(['canceled', 'rejected'])]
    execution_analysis['failed_orders'] = len(failed_orders)
    execution_analysis['failure_rate'] = len(failed_orders) / len(orders_df)
    
    # Execution delays (for filled orders)
    filled_orders_with_times = filled_orders.dropna(subset=['filled_time'])
    if len(filled_orders_with_times) > 0:
        execution_delays = (filled_orders_with_times['filled_time'] - filled_orders_with_times['created_time']).dt.total_seconds()
        execution_analysis['avg_execution_time_seconds'] = execution_delays.mean()
        execution_analysis['max_execution_time_seconds'] = execution_delays.max()
    
    return execution_analysis

def analyze_fees_impact(trades_df, pnl_df):
    """Analyze the impact of trading fees on profitability"""
    fees_analysis = {}
    
    # Total fees paid
    fees_analysis['total_fees'] = trades_df['fee_cost'].sum()
    
    # Fees by symbol
    fees_analysis['fees_by_symbol'] = trades_df.groupby('symbol')['fee_cost'].sum().to_dict()
    
    # Fee rates
    fees_analysis['avg_fee_rate'] = (trades_df['fee_cost'] / trades_df['cost']).mean()
    
    # Impact on profitability
    if len(pnl_df) > 0:
        total_gross_pnl = pnl_df['realized_pnl'].sum()
        total_net_pnl = pnl_df['net_pnl'].sum()
        fees_analysis['gross_pnl'] = total_gross_pnl
        fees_analysis['net_pnl'] = total_net_pnl
        fees_analysis['fees_impact'] = total_gross_pnl - total_net_pnl
        fees_analysis['fees_as_percent_of_gross_pnl'] = (fees_analysis['fees_impact'] / abs(total_gross_pnl)) * 100 if total_gross_pnl != 0 else 0
    
    return fees_analysis

def main():
    """Main analysis function"""
    print("Loading trading data...")
    trades_df, orders_df, balance_df, analyses_df = load_trading_data('data/trading.db')
    
    print(f"Loaded {len(trades_df)} trades, {len(orders_df)} orders, {len(balance_df)} balance snapshots")
    
    # Calculate P&L from realized PnL in trades
    print("\nAnalyzing realized P&L...")
    pnl_df = analyze_realized_pnl_from_trades(trades_df)
    
    # Analyze balance changes
    print("Analyzing balance changes...")
    balance_df_analyzed, significant_drops = analyze_balance_changes(balance_df)
    
    # Analyze trading patterns
    print("Analyzing trading patterns...")
    patterns = analyze_trading_patterns(trades_df, pnl_df)
    
    # Analyze order execution
    print("Analyzing order execution...")
    execution_analysis = analyze_order_execution(orders_df)
    
    # Analyze fees impact
    print("Analyzing fees impact...")
    fees_analysis = analyze_fees_impact(trades_df, pnl_df)
    
    # Print comprehensive report
    print("\n" + "="*80)
    print("TRADING PERFORMANCE ANALYSIS REPORT")
    print("="*80)
    
    # Overall summary
    print("\nOVERALL SUMMARY:")
    print(f"Total Trades: {len(trades_df)}")
    print(f"Total Trading Volume: ${trades_df['cost'].sum():.2f}")
    print(f"Total Fees Paid: ${trades_df['fee_cost'].sum():.2f}")
    
    if len(pnl_df) > 0:
        print(f"Total Realized P&L: ${pnl_df['realized_pnl'].sum():.2f}")
        print(f"Net P&L (after fees): ${pnl_df['net_pnl'].sum():.2f}")
        print(f"Winning Trades: {len(pnl_df[pnl_df['realized_pnl'] > 0])}")
        print(f"Losing Trades: {len(pnl_df[pnl_df['realized_pnl'] < 0])}")
        if len(pnl_df) > 0:
            print(f"Win Rate: {(len(pnl_df[pnl_df['realized_pnl'] > 0]) / len(pnl_df) * 100):.1f}%")
    
    # Balance analysis
    print("\nBALANCE ANALYSIS:")
    print(f"Starting Balance: ${balance_df_analyzed.iloc[0]['total_balance']:.2f}")
    print(f"Ending Balance: ${balance_df_analyzed.iloc[-1]['total_balance']:.2f}")
    print(f"Total Balance Change: ${balance_df_analyzed.iloc[-1]['total_balance'] - balance_df_analyzed.iloc[0]['total_balance']:.2f}")
    print(f"Significant Balance Drops (>$0.50): {len(significant_drops)}")
    
    # Symbol-wise analysis
    print("\nSYMBOL-WISE ANALYSIS:")
    for symbol, stats in patterns['by_symbol'].items():
        print(f"\n{symbol}:")
        print(f"  Total Trades: {stats['total_trades']}")
        print(f"  Total Volume: ${stats['total_volume']:.2f}")
        print(f"  Total Fees: ${stats['total_fees']:.4f}")
        print(f"  Realized P&L: ${stats['realized_pnl']:.4f}")
        print(f"  Net P&L: ${stats['net_pnl']:.4f}")
        print(f"  Winning/Losing Trades: {stats['winning_trades']}/{stats['losing_trades']}")
    
    # Timing analysis
    print("\nTIMING ANALYSIS:")
    print("Most active trading hours:")
    hour_counts = patterns['by_hour']['trade_id']
    for hour in sorted(hour_counts.keys(), key=lambda x: hour_counts[x], reverse=True)[:5]:
        print(f"  Hour {hour}: {hour_counts[hour]} trades")
    
    # Order execution analysis
    print("\nORDER EXECUTION ANALYSIS:")
    print(f"Order Success Rate: {(1 - execution_analysis['failure_rate']) * 100:.1f}%")
    print(f"Failed Orders: {execution_analysis['failed_orders']}")
    print(f"Average Fill Rate: {execution_analysis['avg_fill_rate'] * 100:.1f}%")
    if 'avg_execution_time_seconds' in execution_analysis:
        print(f"Average Execution Time: {execution_analysis['avg_execution_time_seconds']:.2f} seconds")
    
    # Fees impact
    print("\nFEES IMPACT ANALYSIS:")
    print(f"Total Fees: ${fees_analysis['total_fees']:.4f}")
    print(f"Average Fee Rate: {fees_analysis['avg_fee_rate'] * 100:.3f}%")
    if 'fees_impact' in fees_analysis:
        print(f"Fees Impact on P&L: ${fees_analysis['fees_impact']:.4f}")
        print(f"Fees as % of Gross P&L: {fees_analysis['fees_as_percent_of_gross_pnl']:.1f}%")
    
    # Losing trades analysis
    if len(pnl_df) > 0:
        losing_trades = pnl_df[pnl_df['realized_pnl'] < 0]
        if len(losing_trades) > 0:
            print(f"\nLOSING TRADES ANALYSIS:")
            print(f"Number of Losing Trades: {len(losing_trades)}")
            print(f"Average Loss per Trade: ${losing_trades['realized_pnl'].mean():.4f}")
            print(f"Largest Loss: ${losing_trades['realized_pnl'].min():.4f}")
            print(f"Total Losses: ${losing_trades['realized_pnl'].sum():.4f}")
            
            # Losing trades by symbol
            print("\nLosses by Symbol:")
            for symbol in losing_trades['symbol'].unique():
                symbol_losses = losing_trades[losing_trades['symbol'] == symbol]
                print(f"  {symbol}: {len(symbol_losses)} trades, ${symbol_losses['realized_pnl'].sum():.4f} total loss")
    
    # Technical issues
    print(f"\nTECHNICAL ISSUES:")
    canceled_orders = orders_df[orders_df['status'] == 'canceled']
    print(f"Canceled Orders: {len(canceled_orders)}")
    if len(canceled_orders) > 0:
        print("Canceled orders by symbol:")
        for symbol in canceled_orders['symbol'].unique():
            count = len(canceled_orders[canceled_orders['symbol'] == symbol])
            print(f"  {symbol}: {count} canceled orders")
    
    # AI Analysis correlation
    print(f"\nAI ANALYSIS CORRELATION:")
    print(f"Total AI Analyses: {len(analyses_df)}")
    successful_analyses = analyses_df[analyses_df['error'].isnull()]
    failed_analyses = analyses_df[~analyses_df['error'].isnull()]
    print(f"Successful Analyses: {len(successful_analyses)}")
    print(f"Failed Analyses: {len(failed_analyses)}")
    if len(failed_analyses) > 0:
        print("Common failure reasons:")
        for error in failed_analyses['error'].unique()[:3]:
            count = len(failed_analyses[failed_analyses['error'] == error])
            print(f"  {error[:100]}... : {count} times")
    
    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)

if __name__ == "__main__":
    main()