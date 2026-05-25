/** @type {import('next').NextConfig} */
const nextConfig = {
    compress: true,
    poweredByHeader: false,
    reactStrictMode: true,
    async rewrites() {
        // En development, proxy al backend local
        // En production, proxy al backend en Render
        const backendUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        return [
            {
                source: "/api/:path*",
                destination: `${backendUrl}/api/:path*`,
            },
        ];
    },
};
export default nextConfig;
