import { useEffect } from "react";
import { CheckCircle2, Loader2, Circle, Zap, Shield, Search, FileCode, Database, Brain, CheckCheck } from "lucide-react";
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
    { id: 'cloning', label: 'Cloning repository', range: [0, 10], icon: Database },
    { id: 'chunking', label: 'Parsing code files', range: [10, 20], icon: FileCode },
    { id: 'indexing', label: 'Indexing codebase', range: [20, 35], icon: Brain },
    { id: 'cve_search', label: 'Searching CVE database', range: [35, 45], icon: Search },
    { id: 'decomposition', label: 'Decomposing queries', range: [45, 50], icon: Zap },
    { id: 'code_search', label: 'Searching codebase', range: [50, 70], icon: Search },
    { id: 'matching', label: 'Matching CVEs to code', range: [70, 75], icon: Shield },
    { id: 'validating', label: 'Validating findings', range: [75, 95], icon: CheckCheck },
    { id: 'finalizing', label: 'Generating report', range: [95, 100], icon: FileCode },
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
    <div className="bg-gradient-to-br from-card via-card to-secondary/20 border-2 border-primary/20 rounded-2xl p-6 shadow-xl animate-scale-in relative overflow-hidden">
      {/* Animated background gradient */}
      <div className="absolute inset-0 bg-gradient-to-r from-primary/5 via-accent/5 to-primary/5 animate-shimmer opacity-50" />
      
      <div className="relative z-10">
        {/* Header */}
        <div className="flex items-center gap-3 mb-6">
          <div className={cn(
            "flex items-center justify-center w-10 h-10 rounded-xl transition-all duration-300",
            isCompleted 
              ? "bg-success/20 text-success ring-2 ring-success/30" 
              : "bg-primary/20 text-primary ring-2 ring-primary/30 animate-pulse-glow"
          )}>
            {isCompleted ? (
              <CheckCircle2 className="w-6 h-6" />
            ) : (
              <Loader2 className="w-6 h-6 animate-spin" />
            )}
          </div>
          <div className="flex-1">
            <h3 className="font-bold text-lg text-foreground">
              {isCompleted ? '✨ Analysis Complete' : '🚀 Analyzing Repository'}
            </h3>
            <p className="text-sm text-muted-foreground mt-0.5">
              {isCompleted ? 'All vulnerabilities have been identified' : 'Scanning for security vulnerabilities...'}
            </p>
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
              {Math.round(progress)}%
            </div>
          </div>
        </div>

        {/* Progress Steps */}
        <div className="space-y-3 mb-5">
          {steps.map((step, index) => {
            const stepStatus = getStepStatus(step.id, index);
            const StepIcon = step.icon;
            return (
              <div 
                key={step.id} 
                className={cn(
                  "flex items-center gap-3 p-3 rounded-xl transition-all duration-300",
                  stepStatus === "active" && "bg-primary/10 border border-primary/30 shadow-lg",
                  stepStatus === "complete" && "bg-success/5",
                )}
              >
                <div className={cn(
                  "flex items-center justify-center w-8 h-8 rounded-lg transition-all duration-300 flex-shrink-0",
                  stepStatus === "complete" && "bg-success/20 text-success",
                  stepStatus === "active" && "bg-primary/20 text-primary animate-pulse",
                  stepStatus === "pending" && "bg-muted/50 text-muted-foreground"
                )}>
                  {stepStatus === "complete" && <CheckCircle2 className="w-5 h-5" />}
                  {stepStatus === "active" && <StepIcon className="w-5 h-5" />}
                  {stepStatus === "pending" && <Circle className="w-5 h-5" />}
                </div>
                <span
                  className={cn(
                    "text-sm font-medium transition-colors duration-300",
                    stepStatus === "complete" && "text-muted-foreground line-through",
                    stepStatus === "active" && "text-foreground font-semibold",
                    stepStatus === "pending" && "text-muted-foreground"
                  )}
                >
                  {step.label}
                </span>
                {stepStatus === "active" && (
                  <div className="ml-auto flex gap-1">
                    <div className="w-1.5 h-1.5 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <div className="w-1.5 h-1.5 bg-primary rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <div className="w-1.5 h-1.5 bg-primary rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Progress Bar */}
        <div className="space-y-2">
          <div className="h-3 bg-secondary/50 rounded-full overflow-hidden shadow-inner">
            <div
              className={cn(
                "h-full rounded-full transition-all duration-500 ease-out relative",
                isCompleted 
                  ? "bg-gradient-to-r from-success to-success/80" 
                  : "bg-gradient-to-r from-primary via-accent to-primary bg-[length:200%_100%] animate-shimmer"
              )}
              style={{ width: `${progress}%` }}
            >
              <div className="absolute inset-0 bg-white/20 animate-pulse-soft" />
            </div>
          </div>
          {stage && (
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground font-medium">
                {getStageDescription(stage)}
              </span>
              <span className="text-foreground font-semibold px-2 py-0.5 bg-primary/10 rounded-full">
                {Math.round(progress)}%
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
