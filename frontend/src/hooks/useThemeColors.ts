"use client"

import { useEffect, useState } from "react"

export function useThemeColors() {
  const [colors, setColors] = useState({
    primary: "#6366f1",
    muted: "#94a3b8",
    background: "#ffffff",
  })

  useEffect(() => {
    const getVar = (name: string, fallback: string) => {
      try {
        const val = getComputedStyle(document.documentElement)
          .getPropertyValue(name).trim()
        return val || fallback
      } catch {
        return fallback
      }
    }

    setColors({
      primary: getVar("--primary", "#6366f1"),
      muted: getVar("--muted-foreground", "#94a3b8"),
      background: getVar("--background", "#ffffff"),
    })
  }, [])

  return colors
}
