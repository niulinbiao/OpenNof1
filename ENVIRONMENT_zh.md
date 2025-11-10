# 环境变量配置

> 📖 **English**: [Environment Configuration](./ENVIRONMENT.md)

本指南说明如何为 AlphaTransformer 正确配置 `.env` 文件。

## 快速设置

```bash
cd backend
cp .env.example .env
# 编辑 .env 文件添加你的 API keys
```

## 环境变量说明

### AI 提供商配置

**AI API Key 配置**
```bash
# 此 API Key 必须与 agent.yaml 中配置的 AI 提供商匹配
# 默认: DeepSeek (如需更换请同时修改 agent.yaml)
OPENAI_API_KEY=your-api-key-here
```

**获取 API Key:**
- **DeepSeek (默认)**: https://platform.deepseek.com/api-keys - 性价比最高
- **OpenAI**: https://platform.openai.com/api-keys - 如需切换到 GPT-4o
- **Anthropic**: https://console.anthropic.com/ - 如需切换到 Claude

**更换 AI Provider:**
如需更换其他模型，修改 `backend/config/agent.yaml`:
```yaml
agent:
  model_name: "deepseek-chat"  # 改为: gpt-4o, claude-3-5-sonnet 等
  base_url: "https://api.deepseek.com/v1"  # 对应修改 base_url  
  api_key: "${OPENAI_API_KEY}"  # 统一使用此环境变量
```

### 交易所配置

**Binance Futures**
```bash
BINANCE_API_KEY=your-binance-api-key-here
BINANCE_API_SECRET=your-binance-api-secret-here
```

**如何获取 Binance API 凭证:**
1. 访问 [Binance Futures](https://accounts.maxweb.red/register?ref=899414088) (使用邀请码享受返佣)
2. 用户中心 → API 管理 → 创建 API
3. **重要权限设置:**
   - ✅ 启用 读取权限
   - ✅ 启用 期货交易  
   - ✅ 启用 通用转账 (如使用实盘交易)
   - ❌ 禁用 现货和杠杆交易 (安全考虑)

**测试环境 (推荐):**
- 使用 [Binance Testnet](https://testnet.binancefuture.com/)
- 无真实资金风险
- 与生产环境相同的 API 接口

### 数据库配置

**SQLite (默认)**
```bash
# DATABASE_URL=sqlite:///./alphatransformer.db
```
- 无需设置
- 数据库文件自动创建
- 适用于开发和单用户部署

## 安全最佳实践

### API Key 安全
- **绝不将 .env 提交到 git** (已在 .gitignore 中)
- 生产环境使用环境变量
- 定期轮换 API keys
- 使用最小必需权限

### Binance API 安全
- 如可能请启用 IP 限制
- 开发时使用测试网
- 从小仓位开始
- 监控 API key 使用情况

## 完整 .env 文件示例

```bash
# AI 提供商 API Key (必须与 agent.yaml 中配置的提供商匹配)
# 默认配置使用 DeepSeek
OPENAI_API_KEY=your-api-key-here

# 交易所
BINANCE_API_KEY=abcdef123456...
BINANCE_API_SECRET=xyz789secretkey...

# 数据库 (可选覆盖)
# DATABASE_URL=sqlite:///./alphatransformer.db

# 日志 (可选)
# LOG_LEVEL=INFO
```

## 配置验证

测试你的配置:
```bash
cd backend
uv run python -c "
from config.agent_config import load_config
config = load_config()
print('✅ 配置加载成功')
print(f'模型: {config.agent.model_name}')
print(f'API Key 已配置: {bool(config.agent.api_key)}')
"
```

## 故障排除

**"Invalid API key" 错误:**
- 检查 .env 中是否有多余空格或引号
- 验证 API key 是否激活
- 确保使用正确的提供商端点

**"Permission denied" 错误:**
- 检查 Binance API 权限
- 验证期货交易是否已启用
- 先尝试测试网

**环境变量未加载:**
- 确保 .env 在 backend/ 目录中
- 检查文件权限
- 更改后重启应用程序

## AI 提供商对比

| 提供商 | 速度 | 成本 | 结构化输出 | 可靠性 |
|--------|------|------|-----------|---------|
| OpenAI gpt-4o | ⭐⭐⭐⭐ | ⭐⭐ | 原生 | ⭐⭐⭐⭐⭐ |
| DeepSeek | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | JSON 模式 | ⭐⭐⭐⭐ |
| Claude | ⭐⭐⭐ | ⭐⭐⭐ | JSON 模式 | ⭐⭐⭐⭐⭐ |

## 切换提供商

1. 更新 `backend/config/agent.yaml`
2. 在 `.env` 中设置对应的 API key
3. 重启交易代理

系统会自动检测提供商能力并相应调整解析方式。