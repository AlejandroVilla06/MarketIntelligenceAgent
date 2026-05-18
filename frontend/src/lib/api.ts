// API proxy via Next.js rewrites (next.config.mjs)
// En development, /api/* se redirige a http://localhost:8000/api/*
const API_URL = "";
const REQUEST_TIMEOUT_MS = 30000;
const MAX_RETRIES = 2;

class ApiError extends Error {
	constructor(
		public status: number,
		message: string,
	) {
		super(message);
		this.name = "ApiError";
	}
}

let _supabaseClient: any = null;

async function getAccessToken(): Promise<string | null> {
	if (!_supabaseClient) {
		const { createClient } = await import("@/lib/supabase/client");
		_supabaseClient = createClient();
	}
	const { data } = await _supabaseClient.auth.getSession();
	return data.session?.access_token ?? null;
}

async function refreshAndRetry(
	path: string,
	options: RequestInit,
	retries: number,
): Promise<Response> {
	// Refresh the session
	if (!_supabaseClient) {
		const { createClient } = await import("@/lib/supabase/client");
		_supabaseClient = createClient();
	}
	await _supabaseClient.auth.refreshSession();

	// Get new token and retry
	const { data } = await _supabaseClient.auth.getSession();
	const newToken = data.session?.access_token;
	if (!newToken) throw new ApiError(401, "Session expired");

	return fetchWithTimeout(
		path,
		{
			...options,
			headers: {
				...(options.headers as Record<string, string>),
				Authorization: `Bearer ${newToken}`,
			},
		},
		retries - 1,
	);
}

async function fetchWithTimeout(
	path: string,
	options: RequestInit = {},
	retries: number = MAX_RETRIES,
): Promise<Response> {
	const controller = new AbortController();
	const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

	try {
		const response = await fetch(path, {
			...options,
			signal: controller.signal,
		});
		return response;
	} catch (err) {
		// On network error or timeout, retry if we have retries left
		if (
			retries > 0 &&
			(err instanceof TypeError || // Failed to fetch
				err instanceof DOMException) // AbortError (timeout)
		) {
			console.warn(
				`Request failed, retrying (${MAX_RETRIES - retries + 1}/${MAX_RETRIES}):`,
				path,
			);
			return fetchWithTimeout(path, options, retries - 1);
		}
		throw err;
	} finally {
		clearTimeout(timeoutId);
	}
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
	const token = await getAccessToken();
	const headers: Record<string, string> = {
		"Content-Type": "application/json",
		...(options.headers as Record<string, string>),
	};
	if (token) {
		headers["Authorization"] = `Bearer ${token}`;
	}

	const url = `${API_URL}${path}`;
	const response = await fetchWithTimeout(url, { ...options, headers });

	if (!response.ok) {
		if (response.status === 401 && token) {
			// Token expired — refresh and retry once
			const retryResponse = await refreshAndRetry(url, options, MAX_RETRIES);
			if (retryResponse.ok) {
				return retryResponse.json();
			}
		}
		throw new ApiError(response.status, await response.text());
	}

	return response.json();
}

export async function streamChat(
	query: string,
	conversationId: string | undefined,
	onToken: (token: string) => void,
	onDone: () => void,
	onError: (error: string) => void,
): Promise<void> {
	const token = await getAccessToken();
	if (!token) {
		onError("Sesión expirada. Iniciá sesión nuevamente.");
		return;
	}

	const params = new URLSearchParams({ query: query.substring(0, 500) });
	if (conversationId) params.set("conversation_id", conversationId);

	try {
		const response = await fetchWithTimeout(
			`${API_URL}/api/chat/stream?${params}`,
			{ headers: { Authorization: `Bearer ${token}` } },
		);

		if (!response.ok) {
			if (response.status === 401) {
				const supabaseClient =
					_supabaseClient ||
					(await import("@/lib/supabase/client")).createClient();
				await supabaseClient.auth.refreshSession();
				onError("Sesión expirada. Recargá la página.");
				return;
			}
			onError(`Error del servidor (${response.status})`);
			return;
		}

		const reader = response.body?.getReader();
		if (!reader) {
			onError("No se pudo leer la respuesta");
			return;
		}

		const decoder = new TextDecoder();
		let buffer = "";

		while (true) {
			const { done, value } = await reader.read();
			if (done) break;

			buffer += decoder.decode(value, { stream: true });
			const lines = buffer.split("\n");
			buffer = lines.pop() || "";

			for (const line of lines) {
				if (line.startsWith("data: ")) {
					try {
						const data = JSON.parse(line.slice(6));
						if (data.token) onToken(data.token);
						if (data.done) onDone();
						if (data.error) onError(data.error);
					} catch {
						/* ignore parse errors */
					}
				}
			}
		}
	} catch (err) {
		if (err instanceof DOMException && err.name === "AbortError") {
			onError("La conexión tardó demasiado. Intentá de nuevo.");
		} else {
			onError(err instanceof Error ? err.message : "Error de conexión");
		}
	}
}

export const api = {
	chat: {
		send: (query: string, conversationId?: string) =>
			request<{ response: string; conversation_id: string }>("/api/chat", {
				method: "POST",
				body: JSON.stringify({ query, conversation_id: conversationId }),
			}),
		stream: streamChat,
	},
	conversations: {
		list: (offset = 0, limit = 20) =>
			request<any[]>(`/api/conversations?offset=${offset}&limit=${limit}`),
		get: (id: string) => request<any>(`/api/conversations/${id}`),
		create: () =>
			request<{ id: string }>("/api/conversations", { method: "POST" }),
		delete: (id: string) =>
			request<any>(`/api/conversations/${id}`, { method: "DELETE" }),
	},
	profile: {
		get: () => request<any>("/api/auth/me"),
		update: (data: any) =>
			request<any>("/api/auth/me", {
				method: "PUT",
				body: JSON.stringify(data),
			}),
	},
};
