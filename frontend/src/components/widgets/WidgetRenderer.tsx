"use client";

import { CryptoPriceCard } from "./CryptoPriceCard";
import { MacroIndicator } from "./MacroIndicator";
import { DataTable } from "./DataTable";
import { CalcResult } from "./CalcResult";
import { TimeSeriesChart } from "./TimeSeriesChart";
import type { WidgetData } from "@/lib/widgetParser";

interface WidgetRendererProps {
	widget: WidgetData;
}

function RawDataFallback({ data }: { data: unknown }) {
	return (
		<pre className="text-xs text-muted-foreground bg-muted rounded-md p-2 overflow-x-auto whitespace-pre-wrap font-mono">
			{JSON.stringify(data, null, 2)}
		</pre>
	);
}

export function WidgetRenderer({ widget }: WidgetRendererProps) {
	switch (widget.type) {
		case "crypto":
			return <CryptoPriceCard data={widget.data} />;
		case "macro":
			return <MacroIndicator data={widget.data} />;
		case "table":
			return <DataTable data={widget.data} />;
		case "calc":
			return <CalcResult data={widget.data} />;
		case "chart":
			return (
				<TimeSeriesChart
					data={widget.data.data || []}
					xKey={widget.data.xKey || "date"}
					yKey={widget.data.yKey || "value"}
					title={widget.data.title}
					type={widget.data.type || "line"}
					color={widget.data.color}
				/>
			);
		case "text":
			return (
				<div className="text-sm text-muted-foreground">
					{widget.data.text ||
						widget.data.content ||
						JSON.stringify(widget.data)}
				</div>
			);
		default:
			// Unknown widget type — render raw data as JSON so nothing is lost
			return <RawDataFallback data={widget.data} />;
	}
}
