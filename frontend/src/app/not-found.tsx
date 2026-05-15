import Link from "next/link"

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <div className="text-center max-w-md">
        <h1 className="text-6xl font-bold text-primary mb-4">404</h1>
        <h2 className="text-xl font-semibold mb-2">Página no encontrada</h2>
        <p className="text-muted-foreground mb-6">
          La página que buscás no existe o fue movida.
        </p>
        <Link
          href="/chat"
          className="inline-flex items-center justify-center rounded-lg bg-primary text-primary-foreground px-5 py-2 text-sm font-medium hover:bg-primary/90 transition-colors"
        >
          Volver al chat
        </Link>
      </div>
    </div>
  )
}
