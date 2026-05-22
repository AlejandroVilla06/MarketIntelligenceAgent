export interface WidgetData {
	type: string
	data: Record<string, unknown>
}

export interface TextSegment {
	kind: "text"
	content: string
}

export interface WidgetSegment {
	kind: "widget"
	widgetData: WidgetData
}

export type MessageSegment = TextSegment | WidgetSegment

/**
 * Parse a message string into segments of text and widgets.
 *
 * Widget markers follow the format:
 *   [WIDGET:<type>]{json}[\/WIDGET]
 */
export function parseMessage(content: string): MessageSegment[] {
	const segments: MessageSegment[] = []
	const regex = /\[WIDGET:(\w+)\](.*?)\[\/WIDGET\]/gs
	let lastIndex = 0
	let match: RegExpExecArray | null

	while ((match = regex.exec(content)) !== null) {
		// Text before this widget
		if (match.index > lastIndex) {
			segments.push({
				kind: "text",
				content: content.slice(lastIndex, match.index),
			})
		}

		// Parse the widget
		try {
			const widgetData: WidgetData = {
				type: match[1],
				data: JSON.parse(match[2]),
			}
			segments.push({ kind: "widget", widgetData })
		} catch {
			// If JSON parsing fails, treat as text
			segments.push({
				kind: "text",
				content: match[0],
			})
		}

		lastIndex = match.index + match[0].length
	}

	// Remaining text after last widget
	if (lastIndex < content.length) {
		segments.push({
			kind: "text",
			content: content.slice(lastIndex),
		})
	}

	return segments
}
