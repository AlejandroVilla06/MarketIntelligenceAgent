"use client"

import { useTheme } from "next-themes"
import { Button } from "@/components/ui/button"
import { Sun, Moon, Contrast } from "lucide-react"
import { api } from "@/lib/api"
import { useEffect, useState } from "react"
import { useTranslation } from "@/components/TranslationProvider"

export function ThemeToggle() {
  const { theme, setTheme } = useTheme()
  const [mounted, setMounted] = useState(false)
  const { t } = useTranslation()
  useEffect(() => setMounted(true), [])

  function handleToggle() {
    const next = { dark: "light", light: "medium", medium: "dark" } as const
    const newTheme = next[theme as keyof typeof next] ?? "medium"
    setTheme(newTheme)
    api.profile.update({ preferred_theme: newTheme }).catch(() => {})
  }

  if (!mounted) {
    return (
      <Button variant="ghost" size="icon" disabled>
        <Sun className="h-4 w-4" />
        <span className="sr-only">{t("theme.toggle")}</span>
      </Button>
    )
  }

  return (
    <Button variant="ghost" size="icon" onClick={handleToggle}>
      {theme === "dark" && <Moon className="h-4 w-4" />}
      {theme === "light" && <Sun className="h-4 w-4" />}
      {theme === "medium" && <Contrast className="h-4 w-4" />}
      <span className="sr-only">{t("theme.toggle")}</span>
    </Button>
  )
}
