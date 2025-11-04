# Quick Start Guide

## Prerequisites

- Python 3.11+
- OpenAI API key (for agent decisions)
- Binance Futures API credentials

## Installation

### 1. Clone Repository
```bash
git clone <repository-url>
cd AlphaTransformer
```

### 2. Install Dependencies
```bash
cd backend
uv sync
```

### 3. Setup Environment Variables
```bash
# Create .env file
cp .env.example .env

# Edit .env with your credentials
OPENAI_API_KEY=your_openai_api_key
BINANCE_API_KEY=your_binance_api_key
BINANCE_API_SECRET=your_binance_api_secret
```

**注意**: 系统会自动读取.env文件中的环境变量并替换配置文件中的${VAR_NAME}占位符。

### 4. Configure Agent
Edit `backend/config/agent.yaml` to customize:
- Trading symbols
- Risk parameters
- Decision intervals
- LLM model settings

Example:
```yaml
agent:
  model_name: "gpt-4"
  decision_interval: 180
  symbols:
    - BTCUSDT
    - ETHUSDT

default_risk:
  max_position_size_percent: 0.1
  max_daily_loss_percent: 0.05
```

## Running the System

### 1. Initialize Database
```bash
# SQLite database will be created automatically on first run
# No additional setup required
```

### 2. Run Migrations
```bash
# Create database tables
python -m alembic upgrade head
```

### 3. Start the Trading Agent
```bash
cd backend
uv run python main.py
```

The agent will:
1. Connect to market data feeds
2. Start making trading decisions every 60 seconds
3. Execute trades through Binance Futures
4. Log all decisions and executions

### 4. Start API Server
```bash
# In another terminal
cd backend
uv run python api/main.py
```

## Monitoring

### Web Dashboard
Access the dashboard at: `http://localhost:8000`

Features:
- Real-time position monitoring
- Decision history and reasoning
- Performance metrics
- Account snapshots

### API Endpoints
```bash
# Get agent status
curl http://localhost:8000/api/v1/agent/status

# Get decision history
curl http://localhost:8000/api/v1/decisions?limit=10

# Get trade history
curl http://localhost:8000/api/v1/executions

# Stop agent
curl -X POST http://localhost:8000/api/v1/agent/stop
```

## Configuration

### Agent Prompt Customization
Modify the `system_prompt` in `config/agent.yaml` to change the agent's behavior:

```yaml
agent:
  system_prompt: |
    You are a conservative crypto trader focused on capital preservation.
    Only take high-probability trades with risk/reward ratio > 3:1.
    Always respect position size limits and stop-loss rules.
```

### Risk Management
Adjust risk parameters in the configuration:

```yaml
default_risk:
  max_position_size_percent: 0.05  # 5% per position
  max_daily_loss_percent: 0.03      # 3% daily max loss
  stop_loss_percent: 0.015          # 1.5% stop loss
```

### Trading Symbols
Add or remove symbols from the trading list:

```yaml
agent:
  symbols:
    - BTCUSDT
    - ETHUSDT
    - SOLUSDT
    - ADAUSDT
```

## Safety Features

### Paper Trading Mode
For testing, enable paper trading in the configuration:

```yaml
exchange:
  testnet: true  # Use Binance testnet
```

### Risk Controls
The system includes multiple safety layers:
- Position size limits
- Daily loss limits
- Stop-loss enforcement
- Emergency stop mechanisms

### Monitoring Alerts
Configure alerts for important events:

```yaml
logging:
  level: "INFO"
  save_decisions: true
  save_executions: true
```

## Troubleshooting

### Common Issues

**Agent not making decisions:**
- Check API credentials in .env file
- Verify OpenAI API key is valid
- Check market data connection

**Orders failing:**
- Verify Binance API permissions
- Check account balance
- Review risk limit settings

**Database connection errors:**
- Check DATABASE_URL in .env
- Ensure the database file path is writable
- Run database initialization if first time setup

### Debug Mode
Enable debug logging for detailed troubleshooting:

```yaml
logging:
  level: "DEBUG"
```

## Next Steps

1. **Test with Paper Trading**: Always start with testnet to validate your configuration
2. **Monitor Performance**: Review decision quality and execution results
3. **Adjust Parameters**: Fine-tune risk parameters based on performance
4. **Scale Gradually**: Start with small position sizes

## Support

- Review logs in `logs/` directory
- Check API documentation at `http://localhost:8000/docs`
- Monitor real-time data in the dashboard

## Important Notes

⚠️ **Risk Warning**: This is an automated trading system. Start with small amounts and paper trading mode.

⚠️ **Market Risk**: Cryptocurrency markets are highly volatile. Only trade what you can afford to lose.

⚠️ **API Limits**: Monitor your API usage to avoid rate limiting issues.