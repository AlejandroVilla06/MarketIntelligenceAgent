"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { createClient } from "@/lib/supabase/client"
import { api } from "@/lib/api"
import { useAuthStore } from "@/stores/authStore"
import type { UserProfile } from "@/stores/authStore"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Switch } from "@/components/ui/switch"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Label } from "@/components/ui/label"
import { Separator } from "@/components/ui/separator"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { useTheme } from "next-themes"
import { Save, LogOut, User, Palette, AlertTriangle } from "lucide-react"

export default function SettingsPage() {
  const router = useRouter()
  const { theme, setTheme } = useTheme()
  const { profile: storedProfile, setProfile: setStoredProfile } = useAuthStore()
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [fullName, setFullName] = useState("")
  const [language, setLanguage] = useState("es")
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    async function load() {
      try {
        const supabase = createClient()
        const { data: { user } } = await supabase.auth.getUser()
        if (!user) { router.push("/login"); return }

        // Use stored profile if available, otherwise fetch fresh
        let me: UserProfile
        if (storedProfile) {
          me = storedProfile
        } else {
          me = await api.profile.get()
          setStoredProfile(me)
        }
        setProfile(me)
        setFullName(me.full_name || "")
        setLanguage(me.preferred_language || "es")
      } catch { /* ignore */ }
      finally { setLoading(false) }
    }
    load()
  }, [router, storedProfile, setStoredProfile])

  async function handleSave() {
    setSaving(true)
    try {
      await api.profile.update({ full_name: fullName, preferred_language: language })
      setStoredProfile({ ...storedProfile, full_name: fullName, preferred_language: language })
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } catch { /* ignore */ }
    finally { setSaving(false) }
  }

  function handleThemeChange() {
    const newTheme = theme === "dark" ? "light" : "dark"
    setTheme(newTheme)
    setStoredProfile({ ...storedProfile, preferred_theme: newTheme })
    api.profile.update({ preferred_theme: newTheme }).catch(() => {})
  }

  async function handleLogout() {
    const supabase = createClient()
    await supabase.auth.signOut()
    router.push("/login")
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-background p-8 max-w-2xl mx-auto space-y-4">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-64 w-full rounded-lg" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b px-6 h-14 flex items-center">
        <h1 className="text-lg font-semibold">Configuración</h1>
      </header>
      <main className="max-w-2xl mx-auto p-6">
        <Tabs defaultValue="account">
          <TabsList className="mb-6">
            <TabsTrigger value="account"><User className="h-4 w-4 mr-2" />Cuenta</TabsTrigger>
            <TabsTrigger value="appearance"><Palette className="h-4 w-4 mr-2" />Apariencia</TabsTrigger>
          </TabsList>

          {/* Account Tab */}
          <TabsContent value="account" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Perfil</CardTitle>
                <CardDescription>Tu información personal</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
                  <Input id="email" value={profile?.email || ""} disabled />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="name">Nombre completo</Label>
                  <Input id="name" value={fullName} onChange={(e) => setFullName(e.target.value)} placeholder="Tu nombre" />
                </div>
                <Button onClick={handleSave} disabled={saving} className="gap-2">
                  <Save className="h-4 w-4" />
                  {saving ? "Guardando..." : saved ? "Guardado ✓" : "Guardar cambios"}
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <CardTitle>API Keys (MCP)</CardTitle>
                  <Badge variant="secondary">Próximamente</Badge>
                </div>
                <CardDescription>
                  Configurá tus propias API keys para CoinMarketCap y FRED
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3 opacity-50 pointer-events-none">
                <div className="space-y-2">
                  <Label>CoinMarketCap API Key</Label>
                  <Input placeholder="Tu API key de CoinMarketCap" disabled />
                </div>
                <div className="space-y-2">
                  <Label>FRED API Key</Label>
                  <Input placeholder="Tu API key de FRED" disabled />
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Appearance Tab */}
          <TabsContent value="appearance" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Apariencia</CardTitle>
                <CardDescription>Personalizá tu experiencia visual</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="flex items-center justify-between">
                  <div>
                    <Label className="text-sm font-medium">Tema oscuro</Label>
                    <p className="text-xs text-muted-foreground">Alternar entre tema claro y oscuro</p>
                  </div>
                  <Switch checked={theme === "dark"} onCheckedChange={handleThemeChange} />
                </div>
                <Separator />
                <div className="flex items-center justify-between">
                  <div>
                    <Label className="text-sm font-medium">Idioma</Label>
                    <p className="text-xs text-muted-foreground">Idioma de la interfaz</p>
                  </div>
                  <Select value={language} onValueChange={(value) => { if (value !== null) setLanguage(value); }}>
                    <SelectTrigger className="w-32">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="es">Español</SelectItem>
                      <SelectItem value="en">English</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Danger Zone */}
        <Card className="mt-6 border-destructive/50">
          <CardHeader>
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-destructive" />
              <CardTitle className="text-destructive">Zona de Peligro</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground mb-4">
              Al cerrar sesión, tus conversaciones seguirán almacenadas en la nube.
            </p>
            <Button variant="destructive" onClick={handleLogout} className="gap-2">
              <LogOut className="h-4 w-4" />
              Cerrar sesión
            </Button>
          </CardContent>
        </Card>
      </main>
    </div>
  )
}
