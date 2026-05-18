"use client";

import { useEffect, useState } from "react";
import { ThemeProvider } from "next-themes";
import { Skeleton } from "@/components/ui/skeleton";

export function Providers({ children }: { children: React.ReactNode }) {
	const [theme, setTheme] = useState<string | null>(null);

	useEffect(() => {
		let cancelled = false;
		const controller = new AbortController();
		const timeout = setTimeout(() => {
			if (!cancelled) setTheme("dark");
		}, 3000);

		async function loadTheme() {
			try {
				const { createClient } = await import("@/lib/supabase/client");
				const supabase = createClient();
				const {
					data: { session },
				} = await supabase.auth.getSession();

				if (session?.access_token) {
					const resp = await fetch(`/api/auth/me`, {
						headers: { Authorization: `Bearer ${session.access_token}` },
						signal: controller.signal,
					});
					if (resp.ok) {
						const profile = await resp.json();
						if (!cancelled) setTheme(profile.preferred_theme || "dark");
						clearTimeout(timeout);
						return;
					}
				}
			} catch {}
			if (!cancelled) setTheme("dark");
			clearTimeout(timeout);
		}

		loadTheme();
		return () => {
			cancelled = true;
			controller.abort();
			clearTimeout(timeout);
		};
	}, []);

	if (!theme) {
		return (
			<div className="min-h-screen bg-background p-8 space-y-4">
				<Skeleton className="h-8 w-48" />
				<Skeleton className="h-4 w-96" />
				<Skeleton className="h-64 w-full max-w-3xl rounded-lg" />
				<div className="space-y-2">
					<Skeleton className="h-12 w-full max-w-3xl" />
					<Skeleton className="h-12 w-full max-w-3xl" />
				</div>
			</div>
		);
	}

	return (
		<ThemeProvider attribute="class" defaultTheme={theme} enableSystem={false}>
			{children}
		</ThemeProvider>
	);
}
