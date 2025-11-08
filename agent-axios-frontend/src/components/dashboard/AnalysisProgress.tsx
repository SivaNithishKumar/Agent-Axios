import { useEffect } from "react";
import { CheckCircle2, Loader2, Circle } from "lucide-react";
import { cn } from "@/lib/utils";
import { getStageDescription } from "@/services/api";

interface AnalysisProgressProps {
  progress: number;
  stage: string;
  status: string;
}

export function AnalysisProgress({ progress, stage, status }: AnalysisProgressProps) {
  useEffect(() => {
    console.log('📊 AnalysisProgress props changed:', { progress, stage, status });
  }, [progress, stage, status]);

  const steps = [
    { id: 'cloning', label: 'Cloning repository', range: [0, 20] },
    { id: 'chunking', label: 'Parsing code files', range: [20, 35] },
    { id: 'embedding', label: 'Generating embeddings', range: [35, 55] },
    { id: 'searching', label: 'Searching CVE database', range: [55, 75] },
    { id: 'validating', label: 'Validating findings', range: [75, 95] },
    { id: 'finalizing', label: 'Generating report', range: [95, 100] },
  ];

  const getStepStatus = (stepId: string, stepIndex: number) => {
    // Use progress percentage to determine step status more reliably
    const [rangeStart, rangeEnd] = steps[stepIndex].range;
    
    if (progress >= 100) {
      return 'complete'; // All complete when analysis is done
    } else if (progress > rangeEnd) {
      return 'complete';
    } else if (progress >= rangeStart && progress <= rangeEnd) {
      return 'active';
    } else {
      return 'pending';
    }
  };

  const isCompleted = progress >= 100 || stage === 'completed';

  return (
    <div className="bg-card border border-border rounded-2xl p-6 shadow-[var(--shadow-soft)] animate-fade-in">
      <div className="flex items-center gap-2 mb-4">
        {isCompleted ? (
          <CheckCircle2 className="w-5 h-5 text-success" />
        ) : (
          <Loader2 className="w-5 h-5 text-primary animate-spin" />
        )}
        <h3 className="font-semibold text-foreground">
          {isCompleted ? 'Analysis Complete' : 'Analyzing Repository'}
        </h3>
      </div>

      <div className="space-y-3">
        {steps.map((step, index) => {
          const stepStatus = getStepStatus(step.id, index);
          return (
            <div key={step.id} className="flex items-center gap-3">
              {stepStatus === "complete" && (
                <CheckCircle2 className="w-5 h-5 text-success flex-shrink-0" />
              )}
              {stepStatus === "active" && (
                <Loader2 className="w-5 h-5 text-primary flex-shrink-0 animate-spin" />
              )}
              {stepStatus === "pending" && (
                <Circle className="w-5 h-5 text-muted-foreground flex-shrink-0" />
              )}
              <span
                className={cn(
                  "text-sm",
                  stepStatus === "complete" && "text-muted-foreground",
                  stepStatus === "active" && "text-foreground font-medium",
                  stepStatus === "pending" && "text-muted-foreground"
                )}
              >
                {step.label}
              </span>
            </div>
          );
        })}
      </div>

      <div className="mt-4 pt-4 border-t border-border">
        <div className="flex justify-between text-sm text-muted-foreground">
          <span>Progress</span>
          <span>{Math.round(progress)}%</span>
        </div>
        <div className="mt-2 h-2 bg-secondary rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-primary to-accent transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>
        {stage && (
          <p className="text-xs text-muted-foreground mt-2">
            {getStageDescription(stage)}
          </p>
        )}
      </div>
    </div>
  );
}
