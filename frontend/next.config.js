/** @type {import('next').NextConfig} */
const blockedApiPaths = [
  '/api/agent/analyze',
  '/api/agent/start',
  '/api/agent/stop',
  '/api/trading/history/reset',
  '/api/trading/history/sync',
]

const nextConfig = {
  reactStrictMode: true,
  webpack: (config) => {
    config.watchOptions = {
      poll: 1000,
      aggregateTimeout: 300,
      ignored: [
        '**/node_modules/**',
        '**/.next/**',
        '**/.git/**',
        '**/dist/**',
        '**/build/**',
      ],
    }
    return config
  },
  async rewrites() {
    const origin = process.env.BACKEND_ORIGIN || 'http://localhost:8000'
    return {
      beforeFiles: blockedApiPaths.map((source) => ({
        source,
        destination: '/api/frontend-blocked',
      })),
      afterFiles: [
        {
          source: '/api/:path*',
          destination: `${origin}/api/v1/:path*`,
        },
      ],
      fallback: [],
    }
  },
}

module.exports = nextConfig
