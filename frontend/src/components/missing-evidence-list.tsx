import { AlertCircle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function MissingEvidenceList({
  items,
  title = "Missing Evidence",
}: {
  items: { name: string; reason: string }[];
  title?: string;
}) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-sm font-semibold">
          <AlertCircle className="h-4 w-4 text-[var(--color-severity-high)]" />
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {items.length === 0 ? (
          <p className="text-xs text-muted-foreground">No critical gaps detected.</p>
        ) : (
          <ul className="space-y-3">
            {items.map((it) => (
              <li
                key={it.name}
                className="flex items-start gap-3 rounded-md border border-dashed border-border bg-muted/40 p-3"
              >
                <div className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-[var(--color-severity-high)]" />
                <div className="min-w-0">
                  <p className="text-sm font-medium">{it.name}</p>
                  <p className="text-xs text-muted-foreground">{it.reason}</p>
                </div>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
