"use client"

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  return (
    <html>
      <body className="min-h-screen flex items-center justify-center bg-background p-4">
        <div className="text-center max-w-md">
          <div className="w-16 h-16 rounded-full bg-destructive/10 flex items-center justify-center mx-auto mb-6">
            <span className="text-3xl">⚠️</span>
          </div>
          <h1 className="text-2xl font-semibold mb-2">Algo salió mal</h1>
          <p className="text-muted-foreground mb-6">
            Ocurrió un error inesperado. No te preocupes, tus datos están seguros.
          </p>
          <button
            onClick={reset}
            className="inline-flex items-center justify-center rounded-lg bg-primary text-primary-foreground px-6 py-2.5 text-sm font-medium hover:bg-primary/90 transition-colors"
          >
            Reintentar
          </button>
        </div>
      </body>
    </html>
  )
}
