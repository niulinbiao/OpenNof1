#!/bin/bash

# AlphaTransformer API 测试脚本
# 使用方法: ./test_api.sh [端口号，默认8000]

PORT=${1:-8000}
BASE_URL="http://127.0.0.1:$PORT"

echo "🚀 AlphaTransformer API 测试"
echo "测试地址: $BASE_URL"
echo "================================"

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 测试函数
test_endpoint() {
    local endpoint=$1
    local description=$2
    local method=${3:-GET}
    
    echo -n "测试 $description ... "
    
    response=$(curl -s -w "%{http_code}" -o /tmp/api_response.json \
        -X "$method" "$BASE_URL$endpoint" \
        -H "Accept: application/json")
    
    if [ "$response" = "200" ]; then
        echo -e "${GREEN}✅ 成功${NC}"
        if [ -f /tmp/api_response.json ]; then
            echo "   响应: $(cat /tmp/api_response.json | jq -r '.message // .status // .symbol // "OK"')"
        fi
    else
        echo -e "${RED}❌ 失败 ($response)${NC}"
        if [ -f /tmp/api_response.json ]; then
            echo "   错误: $(cat /tmp/api_response.json)"
        fi
    fi
    echo
}

# 检查jq是否安装
if ! command -v jq &> /dev/null; then
    echo -e "${YELLOW}⚠️  jq未安装，JSON格式化将被跳过${NC}"
    echo
fi

# 开始测试
echo "🔍 基础接口测试"
echo

test_endpoint "/" "根接口"
test_endpoint "/api/v1/health" "健康检查"
test_endpoint "/api/v1/config" "系统配置"
test_endpoint "/api/v1/config/validate" "配置验证"
test_endpoint "/api/v1/symbols" "交易对列表"

echo "📊 数据接口测试"
echo

test_endpoint "/api/v1/klines/BTCUSDT/1m?limit=5" "BTCUSDT 1分钟K线"
test_endpoint "/api/v1/klines/ETHUSDT/5m?limit=5" "ETHUSDT 5分钟K线"
test_endpoint "/api/v1/snapshot/BTCUSDT" "BTCUSDT快照"
test_endpoint "/api/v1/cache/info" "缓存信息"

echo "🔌 连接状态测试"
echo

test_endpoint "/api/v1/connection/status" "WebSocket连接状态"

echo "📚 API文档"
echo "访问: $BASE_URL/docs"

echo "================================"
echo "测试完成！"

# 清理临时文件
rm -f /tmp/api_response.json