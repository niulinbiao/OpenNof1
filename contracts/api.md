# API Contracts

## Trading Agent API

### Agent Control

#### Start Agent
```http
POST /api/v1/agent/start
```

#### Stop Agent
```http
POST /api/v1/agent/stop
```

#### Get Agent Status
```http
GET /api/v1/agent/status

Response:
{
  "status": "running",
  "last_decision_time": "2024-01-15T10:01:00Z",
  "current_positions": 2,
  "total_trades_today": 5,
  "daily_pnl": 125.50,
  "error_message": null
}
```

### Decisions

#### Get Decision History
```http
GET /api/v1/decisions?limit=100&offset=0

Response:
{
  "decisions": [
    {
      "id": "uuid",
      "timestamp": "2024-01-15T10:01:00Z",
      "reasoning": "BTC showing strong upward momentum...",
      "confidence": 0.85,
      "action": "buy",
      "action_parameters": {
        "symbol": "BTCUSDT",
        "quantity": 0.1
      },
      "risk_parameters": {
        "max_position_size": 0.1,
        "max_daily_loss": 0.05
      },
      "market_data": {
        "BTCUSDT": {
          "price": 45000,
          "change_24h": 2.5,
          "volume": 1000000
        }
      },
      "positions_snapshot": {
        "BTCUSDT": {"size": 0.0, "side": "flat"}
      }
    }
  ],
  "total": 1420,
  "limit": 100,
  "offset": 0
}
```

### Trade Executions

#### Get Trade History
```http
GET /api/v1/executions?status=filled&symbol=BTCUSDT

Response:
{
  "executions": [
    {
      "id": "uuid",
      "decision_id": "uuid",
      "symbol": "BTCUSDT",
      "side": "buy",
      "order_type": "market",
      "quantity": 0.1,
      "executed_price": 45000.5,
      "executed_quantity": 0.1,
      "exchange_fee": 0.045,
      "status": "filled",
      "created_at": "2024-01-15T10:01:30Z",
      "filled_at": "2024-01-15T10:01:32Z"
    }
  ]
}
```

### Real-time Data

#### Get Current Positions
```http
GET /api/v1/positions

Response:
{
  "positions": [
    {
      "symbol": "BTCUSDT",
      "side": "long",
      "size": 0.1,
      "entry_price": 45000.5,
      "current_price": 45200.0,
      "unrealized_pnl": 19.95
    }
  ],
  "last_updated": "2024-01-15T10:02:00Z"
}
```

#### Get Agent Status
```http
GET /api/v1/agents/{agent_id}/status

Response:
{
  "agent_id": "uuid",
  "status": "running",
  "last_decision_time": "2024-01-15T10:01:00Z",
  "current_positions": 2,
  "total_trades_today": 5,
  "daily_pnl": 125.50,
  "error_message": null
}
```

### Dashboard Data

#### Get Dashboard Overview
```http
GET /api/v1/dashboard

Response:
{
  "account_balance": 10000.0,
  "total_pnl": 525.75,
  "daily_pnl": 125.50,
  "win_rate": 0.65,
  "total_trades": 142,
  "current_positions": [
    {
      "symbol": "BTCUSDT",
      "side": "long", 
      "size": 0.1,
      "unrealized_pnl": 19.95
    }
  ],
  "recent_decisions": [
    {
      "timestamp": "2024-01-15T10:01:00Z",
      "action": "buy",
      "symbol": "BTCUSDT",
      "confidence": 0.85,
      "reasoning": "Strong momentum..."
    }
  ]
}
```

## WebSocket Events

### Real-time Updates
```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/ws/dashboard');

// Messages received:
{
  "type": "decision_made",
  "data": {
    "agent_id": "uuid",
    "timestamp": "2024-01-15T10:01:00Z",
    "action": "buy",
    "symbol": "BTCUSDT",
    "confidence": 0.85
  }
}

{
  "type": "trade_executed", 
  "data": {
    "execution_id": "uuid",
    "symbol": "BTCUSDT",
    "side": "buy",
    "quantity": 0.1,
    "executed_price": 45000.5
  }
}

{
  "type": "position_updated",
  "data": {
    "symbol": "BTCUSDT",
    "size": 0.1,
    "unrealized_pnl": 19.95
  }
}
```

## Error Responses

All endpoints return consistent error format:
```json
{
  "error": {
    "code": "INSUFFICIENT_BALANCE",
    "message": "Insufficient balance for this trade",
    "details": {
      "required": 500.0,
      "available": 450.0
    }
  }
}
```

## Status Codes

- `200 OK` - Successful request
- `201 Created` - Resource created successfully  
- `400 Bad Request` - Invalid parameters
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `409 Conflict` - Resource conflict
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error