# Environment Configuration

> 📖 **中文文档**: [环境变量配置](./ENVIRONMENT_zh.md)

This guide explains how to properly configure the `.env` file for AlphaTransformer.

## Quick Setup

```bash
cd backend
cp .env.example .env
# Edit .env with your API keys
```

## Environment Variables

### AI Provider Configuration

**AI API Key Configuration**
```bash
# This key must match the AI provider configured in agent.yaml
# Default: DeepSeek (change agent.yaml to use other providers)
OPENAI_API_KEY=your-api-key-here
```

**Get API Keys:**
- **DeepSeek (Default)**: https://platform.deepseek.com/api-keys - Most cost-effective
- **OpenAI**: https://platform.openai.com/api-keys - For switching to GPT-4o
- **Anthropic**: https://console.anthropic.com/ - For switching to Claude

**Switch AI Provider:**
To use other models, modify `backend/config/agent.yaml`:
```yaml
agent:
  model_name: "deepseek-chat"  # Change to: gpt-4o, claude-3-5-sonnet, etc.
  base_url: "https://api.deepseek.com/v1"  # Update base_url accordingly
  api_key: "${OPENAI_API_KEY}"  # Use unified environment variable
```

### Trading Exchange Configuration

**Binance Futures**
```bash
BINANCE_API_KEY=your-binance-api-key-here
BINANCE_API_SECRET=your-binance-api-secret-here
```

**How to get Binance API credentials:**
1. Visit [Binance Registration](https://accounts.maxweb.red/register?ref=899414088) (Use referral for cashback)
2. Go to Binance Futures → User Center → API Management
3. Create new API key
4. **Important permissions:**
   - ✅ Enable Reading
   - ✅ Enable Futures  
   - ✅ Enable Universal Transfer (if using real trading)
   - ❌ Disable Spot & Margin Trading (for security)

**For Testing (Recommended):**
- Use [Binance Testnet](https://testnet.binancefuture.com/)
- No real money at risk
- Same API interface as production

### Database Configuration

**SQLite (Default)**
```bash
# DATABASE_URL=sqlite:///./alphatransformer.db
```
- No setup required
- Database file created automatically
- Perfect for development and single-user deployment

## Security Best Practices

### API Key Security
- **Never commit .env to git** (already in .gitignore)
- Use environment variables in production
- Rotate API keys regularly
- Use minimal required permissions

### Binance API Security
- Enable IP restrictions if possible
- Use testnet for development
- Start with small position sizes
- Monitor API key usage

## Example Complete .env File

```bash
# AI Provider API Key (must match the provider configured in agent.yaml)
# Default configuration uses DeepSeek
OPENAI_API_KEY=your-api-key-here

# Trading Exchange
BINANCE_API_KEY=abcdef123456...
BINANCE_API_SECRET=xyz789secretkey...

# Database (optional override)
# DATABASE_URL=sqlite:///./alphatransformer.db

# Logging (optional)
# LOG_LEVEL=INFO
```

## Validation

Test your configuration:
```bash
cd backend
uv run python -c "
from config.agent_config import load_config
config = load_config()
print('✅ Configuration loaded successfully')
print(f'Model: {config.agent.model_name}')
print(f'API Key configured: {bool(config.agent.api_key)}')
"
```

## Troubleshooting

**"Invalid API key" errors:**
- Check for extra spaces or quotes in .env
- Verify the API key is active
- Ensure correct provider endpoints

**"Permission denied" errors:**
- Check Binance API permissions
- Verify futures trading is enabled
- Try with testnet first

**Environment variables not loading:**
- Ensure .env is in backend/ directory
- Check file permissions
- Restart the application after changes