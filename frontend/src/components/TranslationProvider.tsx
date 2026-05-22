"use client"

import { createContext, useContext, useMemo } from "react"
import { useAuthStore } from "@/stores/authStore"
import { translations, type SupportedLocale } from "@/lib/i18n"

export type TranslateFn = (key: string, fallback?: string) => string

const TranslationContext = createContext<{ t: TranslateFn; locale: SupportedLocale }>({
  t: (k) => k,
  locale: "es",
})

export function useTranslation() {
  return useContext(TranslationContext)
}

export function TranslationProvider({ children }: { children: React.ReactNode }) {
  const preferredLanguage = useAuthStore((s) => s.profile?.preferred_language)
  const locale = (preferredLanguage || "es") as SupportedLocale

  const value = useMemo(
    () => ({
      locale,
      t: ((key: string, fallback?: string) => {
        return translations[locale]?.[key] || fallback || key
      }) as TranslateFn,
    }),
    [locale],
  )

  return (
    <TranslationContext.Provider value={value}>
      {children}
    </TranslationContext.Provider>
  )
}
