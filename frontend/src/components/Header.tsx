"use client"

import Link from "next/link"
import { useRouter } from "next/navigation"
import { createClient } from "@/lib/supabase/client"
import { useAuthStore } from "@/stores/authStore"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { ThemeToggle } from "./ThemeToggle"
import { useTranslation } from "@/components/TranslationProvider"
import { Menu, Settings } from "lucide-react"

interface HeaderProps {
  onToggleHistory?: () => void
}

export function Header({ onToggleHistory }: HeaderProps) {
  const router = useRouter()
  const { user } = useAuthStore()
  const { t } = useTranslation()

  async function handleLogout() {
    const supabase = createClient()
    await supabase.auth.signOut()
    router.push("/login")
  }

  return (
    <header className="flex items-center justify-between px-4 h-14 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <h1 className="text-sm font-medium text-muted-foreground">
        {t("app.title")}
      </h1>
      <div className="flex items-center gap-1">
        {/* Mobile: sidebar toggle */}
        {onToggleHistory && (
          <Button variant="ghost" size="icon" className="lg:hidden" onClick={onToggleHistory}>
            <Menu className="h-5 w-5" />
          </Button>
        )}
        <Link href="/settings">
          <Button variant="ghost" size="icon">
            <Settings className="h-4 w-4" />
          </Button>
        </Link>
        <ThemeToggle />
        <DropdownMenu>
          <DropdownMenuTrigger
            render={
              <Button variant="ghost" size="sm" className="h-8 w-8 rounded-full">
                {user?.email?.[0]?.toUpperCase() || "U"}
              </Button>
            }
          />
          <DropdownMenuContent align="end">
            <DropdownMenuItem className="text-xs text-muted-foreground" disabled>
              {user?.email}
            </DropdownMenuItem>
            <DropdownMenuItem onClick={handleLogout}>
              {t("settings.logout")}
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  )
}
