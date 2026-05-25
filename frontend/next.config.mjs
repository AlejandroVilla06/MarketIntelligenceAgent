/** @type {import('next').NextConfig} */
const nextConfig = {
	compress: true,
	poweredByHeader: false,
	reactStrictMode: true,
	async rewrites() {
		return [
			{
				source: "/api/:path*",
				destination: "http://localhost:8000/api/:path*",
			},
		];
	},
};
export default nextConfig;
