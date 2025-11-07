import { CheckCircle2, Loader2, Circle } from "lucide-react";
import { cn } from "@/lib/utils";

const steps = [
  { id: 1, label: "Cloning repository", status: "complete" },
  { id: 2, label: "Scanning dependencies", status: "active" },
  { id: 3, label: "Analyzing vulnerabilities", status: "pending" },
  { id: 4, label: "Generating report", status: "pending" },
];

export function AnalysisProgress() {
  return (
    <div className="bg-card border border-border rounded-2xl p-6 shadow-[var(--shadow-soft)] animate-fade-in">
      <div className="flex items-center gap-2 mb-4">
        <Loader2 className="w-5 h-5 text-primary animate-spin" />
        <h3 className="font-semibold text-foreground">Analyzing Repository</h3>
      </div>

      <div className="space-y-3">
        {steps.map((step, index) => (
          <div key={step.id} className="flex items-center gap-3">
            {step.status === "complete" && (
              <CheckCircle2 className="w-5 h-5 text-success flex-shrink-0" />
            )}
            {step.status === "active" && (
              <Loader2 className="w-5 h-5 text-primary flex-shrink-0 animate-spin" />
            )}
            {step.status === "pending" && (
              <Circle className="w-5 h-5 text-muted-foreground flex-shrink-0" />
            )}
            <span
              className={cn(
                "text-sm",
                step.status === "complete" && "text-muted-foreground",
                step.status === "active" && "text-foreground font-medium",
                step.status === "pending" && "text-muted-foreground"
              )}
            >
              {step.label}
            </span>
          </div>
        ))}
      </div>

      <div className="mt-4 pt-4 border-t border-border">
        <div className="flex justify-between text-sm text-muted-foreground">
          <span>Progress</span>
          <span>50%</span>
        </div>
        <div className="mt-2 h-2 bg-secondary rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-primary to-accent transition-all duration-500"
            style={{ width: "50%" }}
          />
        </div>
      </div>
    </div>
  );
}
