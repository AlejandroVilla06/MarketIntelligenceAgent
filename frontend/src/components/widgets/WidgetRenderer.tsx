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
	const data = widget.data as any;
	switch (widget.type) {
		case "crypto":
			return <CryptoPriceCard data={data} />;
		case "macro":
			return <MacroIndicator data={data} />;
		case "table":
			return <DataTable data={data} />;
		case "calc":
			return <CalcResult data={data} />;
		case "chart":
			return (
				<TimeSeriesChart
					data={data.data || []}
					xKey={data.xKey || "date"}
					yKey={data.yKey || "value"}
					title={data.title}
					type={data.type || "line"}
					color={data.color}
				/>
			);
		case "text":
			return (
				<div className="text-sm text-muted-foreground">
					{data.text ||
						data.content ||
						JSON.stringify(data)}
				</div>
			);
		default:
			// Unknown widget type — render raw data as JSON so nothing is lost
			return <RawDataFallback data={data} />;
	}
}
