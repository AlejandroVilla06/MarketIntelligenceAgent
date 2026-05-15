"use client"

import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Send } from "lucide-react"

interface ChatInputProps {
  onSend: (message: string) => void
  disabled?: boolean
}

export function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [input, setInput] = useState("")
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto"
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`
    }
  }, [input])

  function handleSubmit() {
    if (!input.trim() || disabled) return
    onSend(input.trim())
    setInput("")
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <div className="border-t bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="max-w-4xl mx-auto p-4">
        <div className="flex items-end gap-2 bg-muted/50 rounded-2xl border px-4 py-3 focus-within:border-primary/50 transition-colors">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Preguntá sobre acciones, noticias o análisis..."
            rows={1}
            disabled={disabled}
            className="flex-1 bg-transparent outline-none resize-none text-sm placeholder:text-muted-foreground max-h-[200px]"
          />
          <Button
            size="icon"
            onClick={handleSubmit}
            disabled={!input.trim() || disabled}
            className="flex-shrink-0 h-8 w-8 rounded-full"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
        <p className="text-xs text-center text-muted-foreground mt-2">
          Market Intelligence Agent puede cometer errores. Verificá la información importante.
        </p>
      </div>
    </div>
  )
}
