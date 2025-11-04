# AlphaTransformer

AI-powered autonomous trading system with intelligent agents, real-time market data processing, and minimalist interface.

## Quick Start

```bash
# Install dependencies
pip install -r backend/requirements.txt
cd frontend && npm install

# Start backend
cd backend && python main.py

# Start frontend (new terminal)
cd frontend && npm run dev
```

## Architecture

- **Backend**: FastAPI + PostgreSQL + Redis
- **Frontend**: Next.js + TypeScript + TailwindCSS
- **AI**: OpenAI API, Anthropic Claude
- **Market Data**: Binance Futures WebSocket
- **Trading**: Multi-exchange API integration

## Development

See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed system design.

## License

MIT License