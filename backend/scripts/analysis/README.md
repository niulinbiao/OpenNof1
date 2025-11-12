# Trading Analysis Tools

This directory contains tools for analyzing trading performance, debugging AI decisions, and monitoring system behavior.

## Tools Overview

### Performance Analysis
- **`trading_performance_analyzer.py`** - Comprehensive trading performance analysis
- **`decision_quality_analyzer.py`** - AI decision quality scoring and pattern analysis
- **`risk_metrics_calculator.py`** - Risk-adjusted performance metrics calculation

### AI Decision Analysis
- **`ai_reasoning_analyzer.py`** - Analyze AI decision-making patterns and reasoning quality
- **`prompt_performance_tester.py`** - Test and compare different prompt strategies
- **`decision_feedback_analyzer.py`** - Correlation between AI confidence and actual outcomes

### Market Pattern Analysis
- **`market_regime_detector.py`** - Identify market conditions and regime changes
- **`symbol_performance_analyzer.py`** - Symbol-specific trading performance analysis
- **`timing_pattern_analyzer.py`** - Analysis of trading timing and market hours impact

### System Monitoring
- **`order_execution_analyzer.py`** - Order execution quality and failure analysis
- **`system_health_monitor.py`** - Trading system health and performance monitoring
- **`real_time_dashboard.py`** - Real-time trading performance dashboard

## Usage

### Quick Performance Check
```bash
# Overall trading performance summary
python analysis/trading_performance_analyzer.py --summary

# AI decision quality analysis
python analysis/decision_quality_analyzer.py --recent-days 7

# Symbol-specific performance
python analysis/symbol_performance_analyzer.py --symbol BTCUSDT
```

### Detailed Analysis
```bash
# Full performance report with charts
python analysis/trading_performance_analyzer.py --full-report --export-charts

# AI reasoning pattern analysis
python analysis/ai_reasoning_analyzer.py --analyze-patterns --export-report

# Market regime analysis
python analysis/market_regime_detector.py --detect-current --historical-analysis
```

### Real-time Monitoring
```bash
# Start real-time dashboard
python analysis/real_time_dashboard.py --port 8080

# System health monitoring
python analysis/system_health_monitor.py --continuous
```

## Configuration

All analysis tools use the same database and configuration:
- **Database**: `../data/trading.db`
- **Config**: `../config/agent.yaml`
- **Logs**: `../logs/`

## Output Formats

- **Console**: Colored terminal output with tables and metrics
- **JSON**: Machine-readable format for integration
- **HTML**: Rich reports with charts and visualizations
- **CSV**: Raw data export for external analysis

## Dependencies

```bash
# Install additional analysis dependencies
pip install plotly dash pandas numpy scikit-learn matplotlib seaborn
```

## Contributing

When adding new analysis tools:

1. Follow the naming convention: `{category}_{tool_name}.py`
2. Include CLI argument support with `--help`
3. Add both summary and detailed modes
4. Support multiple output formats
5. Update this README with usage examples

## Future Enhancements

- [ ] Machine learning model performance tracking
- [ ] Automated anomaly detection alerts
- [ ] Integration with external monitoring systems
- [ ] Custom metric definitions and tracking
- [ ] A/B testing framework for trading strategies