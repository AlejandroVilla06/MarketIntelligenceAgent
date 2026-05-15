"use client"

import { useTheme } from "next-themes"
import { Button } from "@/components/ui/button"
import { Sun, Moon } from "lucide-react"
import { api } from "@/lib/api"

export function ThemeToggle() {
  const { theme, setTheme } = useTheme()

  function handleToggle() {
    const newTheme = theme === "dark" ? "light" : "dark"
    setTheme(newTheme)
    // Sync to Supabase (fire and forget)
    api.profile.update({ preferred_theme: newTheme }).catch(() => {})
  }

  return (
    <Button variant="ghost" size="icon" onClick={handleToggle}>
      <Sun className="h-4 w-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
      <Moon className="absolute h-4 w-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
      <span className="sr-only">Toggle theme</span>
    </Button>
  )
}
