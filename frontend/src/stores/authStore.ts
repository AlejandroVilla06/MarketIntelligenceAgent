import { create } from "zustand"
import { persist } from "zustand/middleware"
import type { User } from "@supabase/supabase-js"
import { api } from "@/lib/api"

export interface UserProfile {
  full_name?: string
  preferred_theme?: string
  preferred_language?: string
  email?: string
}

interface AuthState {
  user: User | null
  loading: boolean
  profile: UserProfile | null
  setUser: (user: User | null) => void
  setLoading: (loading: boolean) => void
  setProfile: (profile: UserProfile | null) => void
  syncProfile: () => Promise<void>
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      loading: true,
      profile: null,

      setUser: (user) => set({ user, loading: false }),

      setLoading: (loading) => set({ loading }),

      setProfile: (profile) => set({ profile }),

      syncProfile: async () => {
        try {
          const profile = await api.profile.get()
          set({ profile })
        } catch {
          // Silently fail — Settings page handles its own error states
        }
      },
    }),
    {
      name: "auth-storage",
      partialize: (state) => ({
        profile: state.profile,
        user: state.user,
      }),
    },
  ),
)
