"use client"

import { useRouter } from "next/navigation"

export default function ChatError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  const router = useRouter()

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <div className="text-center max-w-md">
        <div className="w-16 h-16 rounded-full bg-destructive/10 flex items-center justify-center mx-auto mb-6">
          <span className="text-3xl">💬</span>
        </div>
        <h2 className="text-xl font-semibold mb-2">Error en el chat</h2>
        <p className="text-muted-foreground mb-6">
          No se pudieron cargar los mensajes. Esto puede deberse a un problema de conexión.
        </p>
        <div className="flex gap-3 justify-center">
          <button
            onClick={reset}
            className="inline-flex items-center justify-center rounded-lg bg-primary text-primary-foreground px-5 py-2 text-sm font-medium hover:bg-primary/90 transition-colors"
          >
            Reintentar
          </button>
          <button
            onClick={() => router.push("/chat")}
            className="inline-flex items-center justify-center rounded-lg border border-border bg-background px-5 py-2 text-sm font-medium hover:bg-muted transition-colors"
          >
            Nueva conversación
          </button>
        </div>
      </div>
    </div>
  )
}
