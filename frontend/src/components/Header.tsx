"use client"

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
import { Menu } from "lucide-react"

interface HeaderProps {
  onToggleHistory?: () => void
}

export function Header({ onToggleHistory }: HeaderProps) {
  const router = useRouter()
  const { user } = useAuthStore()

  async function handleLogout() {
    const supabase = createClient()
    await supabase.auth.signOut()
    router.push("/login")
  }

  return (
    <header className="flex items-center justify-between px-4 h-14 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <h1 className="text-sm font-medium text-muted-foreground">
        Market Intelligence Agent
      </h1>
      <div className="flex items-center gap-1">
        {/* Mobile: sidebar toggle */}
        {onToggleHistory && (
          <Button variant="ghost" size="icon" className="lg:hidden" onClick={onToggleHistory}>
            <Menu className="h-5 w-5" />
          </Button>
        )}
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
              Cerrar sesión
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  )
}
