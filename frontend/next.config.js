// Polyfill 'self' for SSR compatibility
if (typeof global.self === 'undefined') {
  global.self = global;
}

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Use 'standalone' for Docker only, disable for Netlify
  // Automatically detect Docker environment
  ...(process.env.DOCKER_BUILD === 'true' && { output: 'standalone' }),
  reactStrictMode: true,

  // Disable SWC minification if NEXT_DISABLE_SWC is set
  swcMinify: process.env.NEXT_DISABLE_SWC !== 'true',

  // Enable type checking during build (but ignore in Docker to prevent build failures)
  typescript: {
    ignoreBuildErrors: process.env.DOCKER_BUILD === 'true',
  },

  // Enable ESLint during build (but ignore in Docker to prevent build failures)
  eslint: {
    ignoreDuringBuilds: process.env.DOCKER_BUILD === 'true',
  },

  // Enable App Router and experimental features
  experimental: {
    optimizePackageImports: ['lucide-react', '@radix-ui/react-icons'],
    // Temporarily disabled instrumentationHook to fix build issues
    // instrumentationHook: true,
  },

  // Optimize for development and production
  // Temporarily disabled all webpack customizations to fix build issues
  // webpack: (config, { dev, isServer }) => {
  //   return config;
  // },

  // Environment variables
  env: {
    NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL,
  },

  // Image optimization
  images: {
    domains: [
      'cdn.discordapp.com',
      'images.unsplash.com',
      'avatars.githubusercontent.com',
      'www.reddit.com',
    ],
    formats: ['image/avif', 'image/webp'],
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
  },

  // Compiler optimizations
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production',
  },

  // Enable font optimization
  optimizeFonts: true,

  // Security headers
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin',
          },
          {
            key: 'X-DNS-Prefetch-Control',
            value: 'on',
          },
          {
            key: 'Strict-Transport-Security',
            value: 'max-age=31536000; includeSubDomains',
          },
          {
            key: 'Permissions-Policy',
            value: 'camera=(), microphone=(), geolocation=()',
          },
          {
            key: 'Content-Security-Policy',
            value:
              process.env.NODE_ENV === 'development'
                ? "default-src 'self'; script-src 'self' 'unsafe-eval' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' http://localhost:* https:; manifest-src 'self';"
                : "default-src 'self'; script-src 'self' 'unsafe-eval' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' https:; manifest-src 'self';",
          },
        ],
      },
      // PWA manifest headers
      {
        source: '/manifest.json',
        headers: [
          {
            key: 'Content-Type',
            value: 'application/manifest+json',
          },
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable',
          },
        ],
      },
      // Service worker headers
      {
        source: '/sw.js',
        headers: [
          {
            key: 'Content-Type',
            value: 'application/javascript',
          },
          {
            key: 'Cache-Control',
            value: 'no-cache, no-store, must-revalidate',
          },
          {
            key: 'Service-Worker-Allowed',
            value: '/',
          },
        ],
      },
    ];
  },
};

module.exports = nextConfig;
