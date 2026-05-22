"use client"

import { useState, type ReactNode } from "react"
import { createClient } from "@/lib/supabase/client"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { useTranslation } from "@/components/TranslationProvider"

export default function SignupPage() {
  const { t } = useTranslation()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState<ReactNode>(null)
  const [loading, setLoading] = useState(false)
  const router = useRouter()
  const supabase = createClient()

  async function handleSignup(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    
    const { data, error } = await supabase.auth.signUp({ email, password })
    
    if (error) {
      setError(error.message)
      setLoading(false)
      return
    }
    
    // Si el email ya existe, Supabase puede devolver data.session = null
    // (requiere confirmación) o directamente un error
    if (!data.session) {
      setError(
        <>
          {t("auth.signup.email_exists")}{" "}
          <a href="/login" className="underline font-medium hover:text-red-700">
            {t("auth.signup.email_exists.link")}
          </a>
        </>,
      )
      setLoading(false)
      return
    }
    
    router.push("/chat")
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl">{t("auth.signup.title")}</CardTitle>
          <CardDescription>{t("auth.signup.subtitle")}</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSignup} className="space-y-4">
            <Input
              type="email"
              placeholder={t("auth.signup.email")}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
            <Input
              type="password"
              placeholder={t("auth.signup.password")}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={6}
            />
            {error && (
              <p className="text-sm text-red-500">
                {typeof error === "string" && error.toLowerCase().includes("user already registered") ? (
                  <>
                    {t("auth.signup.email_exists")}{" "}
                    <a href="/login" className="underline font-medium hover:text-red-700">
                      {t("auth.signup.email_exists.link")}
                    </a>
                  </>
                ) : (
                  error
                )}
              </p>
            )}
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? t("auth.signup.loading") : t("auth.signup.button")}
            </Button>
          </form>

          <p className="mt-6 text-center text-sm text-muted-foreground">
            {t("auth.signup.has_account")}{" "}
            <a href="/login" className="underline hover:text-primary">{t("auth.signup.login_link")}</a>
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
