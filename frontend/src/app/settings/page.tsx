"use client"

import { useState, useEffect, useRef } from "react"
import { useRouter } from "next/navigation"
import { createClient } from "@/lib/supabase/client"
import { api } from "@/lib/api"
import { useAuthStore } from "@/stores/authStore"
import type { UserProfile } from "@/stores/authStore"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Label } from "@/components/ui/label"
import { Separator } from "@/components/ui/separator"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { useTheme } from "next-themes"
import { useTranslation } from "@/components/TranslationProvider"
import { Save, LogOut, User, Palette, Settings, AlertTriangle, Mail, Lock } from "lucide-react"

export default function SettingsPage() {
  const router = useRouter()
  const { t } = useTranslation()
  const { theme, setTheme } = useTheme()
  const { profile: storedProfile, setProfile: setStoredProfile } = useAuthStore()
  const [profile, setProfile] = useState<UserProfile | null>(storedProfile)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [fullName, setFullName] = useState(storedProfile?.full_name || "")
  const [language, setLanguage] = useState(storedProfile?.preferred_language || "es")
  const [saved, setSaved] = useState(false)
  const languageLoaded = useRef(false)

  // Email change state
  const [showEmailChange, setShowEmailChange] = useState(false)
  const [newEmail, setNewEmail] = useState("")
  const [emailChangeLoading, setEmailChangeLoading] = useState(false)
  const [emailChangeMessage, setEmailChangeMessage] = useState<string | null>(null)
  const [emailChangeError, setEmailChangeError] = useState<string | null>(null)

  // Password change state
  const [currentPassword, setCurrentPassword] = useState("")
  const [newPassword, setNewPassword] = useState("")
  const [confirmNewPassword, setConfirmNewPassword] = useState("")
  const [passwordChangeLoading, setPasswordChangeLoading] = useState(false)
  const [passwordChangeMessage, setPasswordChangeMessage] = useState<string | null>(null)
  const [passwordChangeError, setPasswordChangeError] = useState<string | null>(null)

  const supabaseClient = createClient()

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
        languageLoaded.current = true
      } catch { /* ignore */ }
      finally { setLoading(false) }
    }
    load()
  }, [router, storedProfile, setStoredProfile])

  async function handleSave() {
    setSaving(true)
    try {
      await api.profile.update({ full_name: fullName, preferred_language: language })
      setStoredProfile({ ...storedProfile, full_name: fullName, preferred_language: language } as UserProfile)
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } catch { /* ignore */ }
    finally { setSaving(false) }
  }

  function handleThemeChange(value: string | null) {
    if (!value) return
    setTheme(value)
    setStoredProfile({ ...storedProfile, preferred_theme: value } as UserProfile)
    api.profile.update({ preferred_theme: value }).catch(() => {})
  }

  function handleLanguageChange(value: string | null) {
    if (!value) return
    setLanguage(value)
    const updated = { ...storedProfile, preferred_language: value } as UserProfile
    setStoredProfile(updated)
    setProfile(updated)
    api.profile.update({ preferred_language: value }).catch(() => {})
  }

  async function handleEmailChange() {
    setEmailChangeError(null)
    setEmailChangeMessage(null)
    if (!newEmail || !newEmail.includes("@")) {
      setEmailChangeError(t("error.invalid_email"))
      return
    }
    setEmailChangeLoading(true)
    const { error } = await supabaseClient.auth.updateUser({ email: newEmail })
    if (error) {
      if (error.message.toLowerCase().includes("rate limit")) {
        setEmailChangeError(t("error.rate_limit.email"))
      } else {
        setEmailChangeError(error.message)
      }
    } else {
      setEmailChangeMessage(t("email.change.sent"))
      setShowEmailChange(false)
      setNewEmail("")
    }
    setEmailChangeLoading(false)
  }

  async function handlePasswordChange() {
    setPasswordChangeError(null)
    setPasswordChangeMessage(null)
    if (newPassword.length < 6) {
      setPasswordChangeError(t("error.password_min"))
      return
    }
    if (newPassword !== confirmNewPassword) {
      setPasswordChangeError(t("error.password_mismatch_new"))
      return
    }
    setPasswordChangeLoading(true)
    const { error } = await supabaseClient.auth.updateUser({ password: newPassword })
    if (error) {
      setPasswordChangeError(error.message)
    } else {
      setPasswordChangeMessage(t("password.reset.updated"))
      setCurrentPassword("")
      setNewPassword("")
      setConfirmNewPassword("")
    }
    setPasswordChangeLoading(false)
  }

  async function handleLogout() {
    const supabase = createClient()
    await supabase.auth.signOut()
    router.push("/login")
  }

  if (loading && !storedProfile) {
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
        <h1 className="text-lg font-semibold">{t("settings.title")}</h1>
      </header>
      <main className="max-w-2xl mx-auto p-6">
        <Tabs defaultValue="general">
          <TabsList className="mb-6">
            <TabsTrigger value="general"><Settings className="h-4 w-4 mr-2" />{t("settings.general")}</TabsTrigger>
            <TabsTrigger value="account"><User className="h-4 w-4 mr-2" />{t("settings.account")}</TabsTrigger>
            <TabsTrigger value="appearance"><Palette className="h-4 w-4 mr-2" />{t("settings.appearance")}</TabsTrigger>
          </TabsList>

          {/* General Tab */}
          <TabsContent value="general" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>{t("settings.general")}</CardTitle>
                <CardDescription>{t("settings.language.description")}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="flex items-center justify-between">
                  <div>
                    <Label className="text-sm font-medium">{t("settings.language")}</Label>
                    <p className="text-xs text-muted-foreground">{t("settings.language.description")}</p>
                  </div>
                  <Select value={language} onValueChange={handleLanguageChange}>
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

          {/* Account Tab */}
          <TabsContent value="account" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>{t("settings.profile")}</CardTitle>
                <CardDescription>{t("settings.profile.description")}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="email">{t("settings.email")}</Label>
                  <Input id="email" value={profile?.email || ""} disabled />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="name">{t("settings.name")}</Label>
                  <Input id="name" value={fullName} onChange={(e) => setFullName(e.target.value)} placeholder={t("settings.name.placeholder")} />
                </div>
                <Button onClick={handleSave} disabled={saving} className="gap-2">
                  <Save className="h-4 w-4" />
                  {saving ? t("settings.saving") : saved ? t("settings.saved") : t("settings.save")}
                </Button>
              </CardContent>
            </Card>

            {/* Email Change */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Mail className="h-5 w-5" />
                  {t("settings.change_email")}
                </CardTitle>
                <CardDescription>{t("email.change.description")}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>{t("settings.current_email")}</Label>
                  <Input value={profile?.email || ""} disabled />
                </div>
                {showEmailChange ? (
                  <>
                    <div className="space-y-2">
                      <Label htmlFor="new-email">{t("email.change.new")}</Label>
                      <Input
                        id="new-email"
                        type="email"
                        placeholder={t("settings.new_email.placeholder")}
                        value={newEmail}
                        onChange={(e) => setNewEmail(e.target.value)}
                      />
                    </div>
                    {emailChangeError && (
                      <p className="text-sm text-red-500">{emailChangeError}</p>
                    )}
                    {emailChangeMessage && (
                      <p className="text-sm text-green-600 font-medium">{emailChangeMessage}</p>
                    )}
                    <div className="flex gap-2">
                      <Button
                        onClick={handleEmailChange}
                        disabled={emailChangeLoading}
                      >
                        {emailChangeLoading ? t("common.sending") : t("email.change.save")}
                      </Button>
                      <Button
                        variant="outline"
                        onClick={() => {
                          setShowEmailChange(false)
                          setNewEmail("")
                          setEmailChangeError(null)
                          setEmailChangeMessage(null)
                        }}
                      >
                        {t("common.cancel")}
                      </Button>
                    </div>
                  </>
                ) : (
                  <Button
                    variant="outline"
                    onClick={() => {
                      setShowEmailChange(true)
                      setNewEmail(profile?.email || "")
                      setEmailChangeError(null)
                      setEmailChangeMessage(null)
                    }}
                  >
                    {t("settings.change_email")}
                  </Button>
                )}
              </CardContent>
            </Card>

            {/* Password Change */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Lock className="h-5 w-5" />
                  {t("settings.change_password")}
                </CardTitle>
                <CardDescription>{t("settings.password.description")}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="current-password">{t("settings.current_password")}</Label>
                  <Input
                    id="current-password"
                    type="password"
                    placeholder="••••••••"
                    value={currentPassword}
                    onChange={(e) => setCurrentPassword(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="new-password">{t("settings.new_password")}</Label>
                  <Input
                    id="new-password"
                    type="password"
                    placeholder={t("settings.new_password.placeholder")}
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    minLength={6}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="confirm-password">{t("settings.confirm_password")}</Label>
                  <Input
                    id="confirm-password"
                    type="password"
                    placeholder={t("settings.confirm_password.placeholder")}
                    value={confirmNewPassword}
                    onChange={(e) => setConfirmNewPassword(e.target.value)}
                    minLength={6}
                  />
                </div>
                {passwordChangeError && (
                  <p className="text-sm text-red-500">{passwordChangeError}</p>
                )}
                {passwordChangeMessage && (
                  <p className="text-sm text-green-600 font-medium">{passwordChangeMessage}</p>
                )}
                <Button
                  onClick={handlePasswordChange}
                  disabled={passwordChangeLoading}
                >
                  {passwordChangeLoading ? t("common.updating") : t("settings.change_password")}
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <CardTitle>{t("settings.api_keys")}</CardTitle>
                  <Badge variant="secondary">{t("settings.api_keys.soon")}</Badge>
                </div>
                <CardDescription>
                  {t("settings.api_keys.description")}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3 opacity-50 pointer-events-none">
                <div className="space-y-2">
                  <Label>{t("settings.api_keys.cmc")}</Label>
                  <Input placeholder={t("settings.api_keys.cmc_placeholder")} disabled />
                </div>
                <div className="space-y-2">
                  <Label>{t("settings.api_keys.fred")}</Label>
                  <Input placeholder={t("settings.api_keys.fred_placeholder")} disabled />
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Appearance Tab */}
          <TabsContent value="appearance" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>{t("settings.appearance")}</CardTitle>
                <CardDescription>{t("settings.appearance.description")}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="flex items-center justify-between">
                  <div>
                    <Label className="text-sm font-medium">{t("settings.theme")}</Label>
                    <p className="text-xs text-muted-foreground">{t("settings.theme.description")}</p>
                  </div>
                  <Select value={theme === "system" ? "medium" : theme} onValueChange={handleThemeChange}>
                    <SelectTrigger className="w-32">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="light">{t("theme.light")}</SelectItem>
                      <SelectItem value="dark">{t("theme.dark")}</SelectItem>
                      <SelectItem value="medium">{t("theme.medium")}</SelectItem>
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
              <CardTitle className="text-destructive">{t("settings.danger")}</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground mb-4">
              {t("settings.danger.description")}
            </p>
            <Button variant="destructive" onClick={handleLogout} className="gap-2">
              <LogOut className="h-4 w-4" />
              {t("settings.logout")}
            </Button>
          </CardContent>
        </Card>
      </main>
    </div>
  )
}
