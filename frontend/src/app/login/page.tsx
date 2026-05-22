"use client"

import { useState, useEffect } from "react"
import { createClient } from "@/lib/supabase/client"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { useTranslation } from "@/components/TranslationProvider"

export default function LoginPage() {
  const { t } = useTranslation()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [forgotMode, setForgotMode] = useState(false)
  const [forgotEmail, setForgotEmail] = useState("")
  const [forgotLoading, setForgotLoading] = useState(false)
  const [forgotSent, setForgotSent] = useState(false)
  const [resendCooldown, setResendCooldown] = useState(0)
  const router = useRouter()
  const supabase = createClient()

  // Countdown for resend cooldown
  useEffect(() => {
    if (resendCooldown <= 0) return
    const timer = setTimeout(() => setResendCooldown(resendCooldown - 1), 1000)
    return () => clearTimeout(timer)
  }, [resendCooldown])

  async function handleEmailLogin(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    
    const { error } = await supabase.auth.signInWithPassword({ email, password })
    
    if (error) {
      setError(error.message)
      setLoading(false)
      return
    }
    
    router.push("/chat")
  }

  async function handleForgotPassword(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setForgotLoading(true)
    
    const targetEmail = forgotEmail || email
    // El redirectTo DEBE ser una URL sin query params para que Supabase
    // la reconozca en la lista de Redirect URLs permitidas.
    const { error } = await supabase.auth.resetPasswordForEmail(targetEmail, {
      redirectTo: `${window.location.origin}/auth/callback`,
    })
    
    if (error) {
      if (error.message.toLowerCase().includes("rate limit")) {
        setError(t("error.rate_limit.password"))
      } else {
        setError(error.message)
      }
      setForgotLoading(false)
      return
    }
    
    setForgotSent(true)
    setForgotLoading(false)
    setResendCooldown(30)
  }

  const providerNames: Record<string, string> = {
    google: "Google",
    github: "GitHub",
  }

  async function handleOAuth(provider: "google" | "github") {
    setError(null)
    const { error } = await supabase.auth.signInWithOAuth({
      provider,
      options: {
        redirectTo: `${window.location.origin}/auth/callback`,
      },
    })
    if (error) {
      setError(t("error.oauth_failed").replace("{provider}", providerNames[provider]))
    }
  }

  if (forgotMode) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <CardTitle className="text-2xl">{t("password.reset.title")}</CardTitle>
            <CardDescription>{t("password.reset.description")}</CardDescription>
          </CardHeader>
          <CardContent>
            {forgotSent ? (
              <div className="space-y-4 text-center">
                <p className="text-sm text-green-600 font-medium">
                  {t("password.reset.success")}
                </p>
                {resendCooldown > 0 ? (
                  <p className="text-xs text-muted-foreground">
                    {t("password.reset.resend_in").replace("{seconds}", String(resendCooldown))}
                  </p>
                ) : (
                  <p className="text-xs text-muted-foreground">
                    {t("password.reset.not_received")}{" "}
                    <button
                      type="button"
                      onClick={handleForgotPassword}
                      className="underline hover:text-primary"
                    >
                      {t("password.reset.resend")}
                    </button>
                  </p>
                )}
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={() => {
                    setForgotMode(false)
                    setForgotSent(false)
                    setError(null)
                  }}
                >
                  {t("password.reset.back")}
                </Button>
              </div>
            ) : (
              <form onSubmit={handleForgotPassword} className="space-y-4">
                <Input
                  type="email"
                  placeholder={t("auth.login.email")}
                  value={forgotEmail || email}
                  onChange={(e) => setForgotEmail(e.target.value)}
                  required
                />
                {error && <p className="text-sm text-red-500">{error}</p>}
                <Button type="submit" className="w-full" disabled={forgotLoading}>
                  {forgotLoading ? t("common.sending") : t("password.reset.button")}
                </Button>
                <button
                  type="button"
                  onClick={() => {
                    setForgotMode(false)
                    setForgotSent(false)
                    setError(null)
                  }}
                  className="w-full text-center text-sm text-muted-foreground underline hover:text-primary"
                >
                  {t("password.reset.back")}
                </button>
              </form>
            )}
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl">{t("app.title")}</CardTitle>
          <CardDescription>{t("auth.login.subtitle")}</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleEmailLogin} className="space-y-4">
            <Input
              type="email"
              placeholder={t("auth.login.email")}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
            <Input
              type="password"
              placeholder={t("auth.login.password")}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
            <div className="flex items-center justify-end">
              <button
                type="button"
                onClick={() => setForgotMode(true)}
                className="text-sm text-muted-foreground underline hover:text-primary"
              >
                {t("auth.login.forgot")}
              </button>
            </div>
            {error && <p className="text-sm text-red-500">{error}</p>}
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? t("auth.login.loading") : t("auth.login.button")}
            </Button>
          </form>

          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center"><span className="w-full border-t" /></div>
            <div className="relative flex justify-center text-xs uppercase"><span className="bg-background px-2 text-muted-foreground">{t("auth.login.or_continue_with")}</span></div>
          </div>

          {/*
            OAuth providers (Google/GitHub) require configuration in your Supabase project:
              1. Go to Supabase Dashboard → Authentication → Providers
              2. Enable Google and/or GitHub
              3. Set the redirect URL to: http://localhost:3000/auth/callback
              4. Add your OAuth client ID and secret from the provider's dev console
          */}
          <div className="space-y-3">
            <Button variant="outline" className="w-full" onClick={() => handleOAuth("google")}>
              Google
            </Button>
            <Button variant="outline" className="w-full" onClick={() => handleOAuth("github")}>
              GitHub
            </Button>
          </div>

          <p className="mt-6 text-center text-sm text-muted-foreground">
            {t("auth.login.no_account")}{" "}
            <a href="/signup" className="underline hover:text-primary">{t("auth.login.signup_link")}</a>
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
