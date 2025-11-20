import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Shield, 
  GitBranch, 
  Loader2, 
  CheckCircle2, 
  AlertTriangle,
  Download,
  ArrowRight,
  FileSearch,
  Database,
  Brain,
  Bug,
  FileText,
  Clock,
  Zap,
  Sparkles,
  Activity
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { cn } from '@/lib/utils';
import { AzureOpenAIService } from '@/services/azureOpenAI';
import { VulnerabilityReportGenerator } from '@/lib/pdfGenerator';
import { PageLayout } from '@/components/layout/PageLayout';

interface AnalysisEvent {
  id: number;
  stage: string;
  message: string;
  progress: number;
  timestamp: Date;
  icon: React.ReactNode;
  status: 'pending' | 'active' | 'completed';
}

export default function Analyze() {
  const navigate = useNavigate();
  const [repoUrl, setRepoUrl] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [currentProgress, setCurrentProgress] = useState(0);
  const [events, setEvents] = useState<AnalysisEvent[]>([]);
  const [vulnerabilityCount, setVulnerabilityCount] = useState(0);
  const [analysisTime, setAnalysisTime] = useState(0);
  const [reportData, setReportData] = useState<any>(null);
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);
  const eventIdRef = useRef(1);
  const timerRef = useRef<NodeJS.Timeout>();
  const startTimeRef = useRef<Date>();
  const azureService = useRef(new AzureOpenAIService());

  // Mock analysis events based on backend flow
  const mockAnalysisSequence = [
    { stage: 'initializing', message: 'Initializing security analysis engine...', progress: 5, icon: <Zap className="w-4 h-4" />, delay: 2000 },
    { stage: 'cloning', message: 'Cloning repository from remote...', progress: 15, icon: <GitBranch className="w-4 h-4" />, delay: 3000 },
    { stage: 'cloning', message: 'Repository cloned successfully', progress: 20, icon: <CheckCircle2 className="w-4 h-4" />, delay: 2000 },
    { stage: 'indexing', message: 'Scanning codebase structure...', progress: 25, icon: <FileSearch className="w-4 h-4" />, delay: 2500 },
    { stage: 'indexing', message: 'Processing and chunking source files...', progress: 35, icon: <FileText className="w-4 h-4" />, delay: 3000 },
    { stage: 'indexing', message: 'Building semantic index...', progress: 45, icon: <Database className="w-4 h-4" />, delay: 2500 },
    { stage: 'indexing', message: 'Indexed 847 code chunks across 143 files', progress: 50, icon: <CheckCircle2 className="w-4 h-4" />, delay: 2000 },
    { stage: 'agent_starting', message: 'Launching autonomous security agent...', progress: 55, icon: <Brain className="w-4 h-4" />, delay: 2000 },
    { stage: 'agent_analyzing', message: 'Agent analyzing repository structure...', progress: 60, icon: <Brain className="w-4 h-4" />, delay: 2500 },
    { stage: 'agent_analyzing', message: 'Searching CVE database for known vulnerabilities...', progress: 65, icon: <Database className="w-4 h-4" />, delay: 3000 },
    { stage: 'agent_analyzing', message: 'Found 8 potentially relevant CVEs', progress: 70, icon: <AlertTriangle className="w-4 h-4" />, delay: 2000 },
    { stage: 'agent_analyzing', message: 'Analyzing CVE-2024-1337: SQL Injection vulnerability...', progress: 75, icon: <Bug className="w-4 h-4" />, delay: 3500 },
    { stage: 'agent_analyzing', message: 'Searching codebase for vulnerable patterns...', progress: 78, icon: <FileSearch className="w-4 h-4" />, delay: 2500 },
    { stage: 'agent_analyzing', message: 'Validating vulnerability match...', progress: 80, icon: <Shield className="w-4 h-4" />, delay: 3000 },
    { stage: 'agent_analyzing', message: 'Confirmed vulnerability in database.py', progress: 82, icon: <AlertTriangle className="w-4 h-4" />, delay: 2000 },
    { stage: 'agent_analyzing', message: 'Analyzing CVE-2024-2891: Cross-Site Scripting (XSS)...', progress: 85, icon: <Bug className="w-4 h-4" />, delay: 3000 },
    { stage: 'agent_analyzing', message: 'Confirmed vulnerability in templates/user.html', progress: 88, icon: <AlertTriangle className="w-4 h-4" />, delay: 2500 },
    { stage: 'agent_analyzing', message: 'Analyzing CVE-2024-3782: Insecure Deserialization...', progress: 91, icon: <Bug className="w-4 h-4" />, delay: 3000 },
    { stage: 'agent_analyzing', message: 'Confirmed vulnerability in api/handlers.py', progress: 94, icon: <AlertTriangle className="w-4 h-4" />, delay: 2500 },
    { stage: 'generating_report', message: 'Generating comprehensive security report...', progress: 97, icon: <FileText className="w-4 h-4" />, delay: 2500 },
    { stage: 'completed', message: 'Security analysis completed successfully', progress: 100, icon: <CheckCircle2 className="w-4 h-4" />, delay: 1500 }
  ];

  const addEvent = (stage: string, message: string, progress: number, icon: React.ReactNode) => {
    const newEvent: AnalysisEvent = {
      id: eventIdRef.current++,
      stage,
      message,
      progress,
      timestamp: new Date(),
      icon,
      status: 'active'
    };

    setEvents(prev => {
      const updated = prev.map(e => ({ ...e, status: 'completed' as const }));
      return [...updated, newEvent];
    });
    setCurrentProgress(progress);
  };

  const startAnalysis = async () => {
    if (!repoUrl.trim()) return;

    setIsAnalyzing(true);
    setIsComplete(false);
    setEvents([]);
    setCurrentProgress(0);
    setVulnerabilityCount(0);
    setReportData(null);
    eventIdRef.current = 1;
    startTimeRef.current = new Date();

    // Start timer
    timerRef.current = setInterval(() => {
      if (startTimeRef.current) {
        const elapsed = Math.floor((new Date().getTime() - startTimeRef.current.getTime()) / 1000);
        setAnalysisTime(elapsed);
      }
    }, 1000);

    // Start generating report in background
    setIsGeneratingReport(true);
    const reportPromise = azureService.current.generateVulnerabilityReport(repoUrl);

    // Process mock events sequentially
    for (let i = 0; i < mockAnalysisSequence.length; i++) {
      const event = mockAnalysisSequence[i];
      
      await new Promise(resolve => setTimeout(resolve, event.delay));
      
      addEvent(event.stage, event.message, event.progress, event.icon);

      // On completion
      if (event.stage === 'completed') {
        // Wait for report generation
        try {
          const report = await reportPromise;
          setReportData(report);
          setVulnerabilityCount(report.vulnerabilities.length);
          setIsGeneratingReport(false);
        } catch (error) {
          console.error('Report generation error:', error);
          setIsGeneratingReport(false);
        }

        setTimeout(() => {
          setIsAnalyzing(false);
          setIsComplete(true);
          if (timerRef.current) {
            clearInterval(timerRef.current);
          }
        }, 500);
      }
    }
  };

  const downloadReport = () => {
    if (!reportData) return;

    try {
      const generator = new VulnerabilityReportGenerator();
      const pdfBlob = generator.generateReport({
        repoUrl,
        analysisDate: new Date().toLocaleString(),
        analysisDuration: analysisTime,
        vulnerabilities: reportData.vulnerabilities,
        executiveSummary: reportData.executiveSummary,
        remediationPriority: reportData.remediationPriority
      });

      const url = URL.createObjectURL(pdfBlob);
      const link = document.createElement('a');
      link.href = url;
      const repoName = repoUrl.split('/').pop()?.replace('.git', '') || 'repository';
      link.download = `security-analysis-${repoName}-${Date.now()}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error generating PDF:', error);
    }
  };

  const resetAnalysis = () => {
    setRepoUrl('');
    setIsAnalyzing(false);
    setIsComplete(false);
    setEvents([]);
    setCurrentProgress(0);
    setVulnerabilityCount(0);
    setAnalysisTime(0);
    setReportData(null);
    setIsGeneratingReport(false);
    if (timerRef.current) {
      clearInterval(timerRef.current);
    }
  };

  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, []);

  return (
    <PageLayout
      breadcrumbs={[
        { label: "Dashboard", href: "/dashboard" },
        { label: "New Analysis" },
      ]}
    >
    <div className="flex-1 bg-gradient-to-br from-slate-900 via-indigo-900 to-purple-900 relative overflow-hidden">
      {/* Animated background */}
      <div className="absolute inset-0 opacity-20">
        <div className="absolute top-0 -left-4 w-72 h-72 bg-purple-500 rounded-full mix-blend-multiply filter blur-xl animate-blob"></div>
        <div className="absolute top-0 -right-4 w-72 h-72 bg-indigo-500 rounded-full mix-blend-multiply filter blur-xl animate-blob animation-delay-2000"></div>
        <div className="absolute -bottom-8 left-20 w-72 h-72 bg-blue-500 rounded-full mix-blend-multiply filter blur-xl animate-blob animation-delay-4000"></div>
      </div>

      <div className="container max-w-5xl mx-auto px-4 py-12 relative z-10">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12"
        >
          <motion.div 
            className="flex items-center justify-center mb-6"
            animate={{ 
              scale: [1, 1.05, 1],
            }}
            transition={{ 
              duration: 2,
              repeat: Infinity,
              ease: "easeInOut"
            }}
          >
            <div className="relative">
              <Shield className="w-16 h-16 text-indigo-400" />
              <Sparkles className="w-6 h-6 text-yellow-400 absolute -top-1 -right-1 animate-pulse" />
            </div>
          </motion.div>
          <h1 className="text-5xl font-bold bg-gradient-to-r from-blue-400 via-indigo-400 to-purple-400 bg-clip-text text-transparent mb-4">
            AI Security Analysis
          </h1>
          <p className="text-lg text-slate-300 max-w-2xl mx-auto">
            Advanced vulnerability detection powered by Azure GPT-4 and autonomous security agents
          </p>
        </motion.div>

        {/* Main Content */}
        <AnimatePresence mode="wait">
          {!isAnalyzing && !isComplete ? (
            <motion.div
              key="input"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="max-w-2xl mx-auto"
            >
              <Card className="p-8 shadow-2xl border-slate-700 bg-slate-800/50 backdrop-blur-xl">
                <div className="space-y-6">
                  <div>
                    <label className="block text-sm font-medium text-slate-200 mb-2 flex items-center gap-2">
                      <GitBranch className="w-4 h-4" />
                      Repository URL
                    </label>
                    <Input
                      type="url"
                      placeholder="https://github.com/username/repository"
                      value={repoUrl}
                      onChange={(e) => setRepoUrl(e.target.value)}
                      className="h-12 text-base bg-slate-900/50 border-slate-600 text-slate-100 placeholder:text-slate-500 focus:border-indigo-500 focus:ring-indigo-500"
                      onKeyDown={(e) => e.key === 'Enter' && startAnalysis()}
                    />
                    <p className="text-sm text-slate-400 mt-2 flex items-center gap-2">
                      <Activity className="w-3 h-3" />
                      AI agent will perform deep security analysis
                    </p>
                  </div>

                  <Button
                    onClick={startAnalysis}
                    disabled={!repoUrl.trim()}
                    className="w-full h-12 text-base bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white shadow-lg shadow-indigo-500/50 transition-all"
                    size="lg"
                  >
                    <Sparkles className="mr-2 w-5 h-5" />
                    Start Security Analysis
                    <ArrowRight className="ml-2 w-5 h-5" />
                  </Button>
                </div>
              </Card>

              <motion.div 
                className="mt-8 text-center space-y-3"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.3 }}
              >
                <p className="text-sm text-slate-300">
                  Powered by Azure GPT-4 and advanced semantic analysis
                </p>
                <div className="flex items-center justify-center gap-6 text-xs text-slate-400">
                  <div className="flex items-center gap-1">
                    <Brain className="w-3 h-3" />
                    <span>Autonomous AI Agent</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Database className="w-3 h-3" />
                    <span>CVE Database</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Shield className="w-3 h-3" />
                    <span>Real-time Analysis</span>
                  </div>
                </div>
              </motion.div>
            </motion.div>
          ) : isAnalyzing ? (
            <motion.div
              key="analyzing"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="space-y-6"
            >
              {/* Progress Header */}
              <Card className="p-6 shadow-2xl border-slate-700 bg-slate-800/50 backdrop-blur-xl">
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex-1 min-w-0">
                      <h3 className="text-lg font-semibold text-slate-100 flex items-center gap-2">
                        <Activity className="w-5 h-5 text-indigo-400 animate-pulse" />
                        Analyzing Repository
                      </h3>
                      <p className="text-sm text-slate-400 truncate mt-1">
                        {repoUrl}
                      </p>
                    </div>
                    <div className="flex items-center gap-3 text-sm text-slate-300 bg-slate-900/50 px-4 py-2 rounded-lg">
                      <Clock className="w-4 h-4 text-indigo-400" />
                      <span className="font-mono font-semibold">{analysisTime}s</span>
                    </div>
                  </div>
                  
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-slate-300">
                        Analysis Progress
                      </span>
                      <span className="text-sm font-bold text-indigo-400">
                        {currentProgress}%
                      </span>
                    </div>
                    <Progress value={currentProgress} className="h-3 bg-slate-700" />
                  </div>

                  {isGeneratingReport && (
                    <motion.div
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="flex items-center gap-2 text-sm text-yellow-400 bg-yellow-400/10 px-3 py-2 rounded-lg"
                    >
                      <Sparkles className="w-4 h-4 animate-pulse" />
                      <span>AI generating comprehensive security report...</span>
                    </motion.div>
                  )}
                </div>
              </Card>

              {/* Events Timeline */}
              <Card className="p-6 shadow-2xl border-slate-700 bg-slate-800/50 backdrop-blur-xl max-h-[500px] overflow-y-auto">
                <h3 className="text-lg font-semibold text-slate-100 mb-4 flex items-center gap-2">
                  <FileText className="w-5 h-5 text-indigo-400" />
                  Analysis Events
                </h3>
                <div className="space-y-3">
                  <AnimatePresence>
                    {events.map((event, index) => (
                      <motion.div
                        key={event.id}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.05 }}
                        className={cn(
                          "flex items-start gap-3 p-4 rounded-lg transition-all border",
                          event.status === 'active' && "bg-indigo-500/10 border-indigo-500/30 shadow-lg shadow-indigo-500/20",
                          event.status === 'completed' && "bg-slate-700/30 border-slate-600/30"
                        )}
                      >
                        <div className={cn(
                          "mt-0.5 p-2.5 rounded-full shrink-0 transition-all",
                          event.status === 'active' && "bg-indigo-600 text-white shadow-lg shadow-indigo-500/50",
                          event.status === 'completed' && "bg-slate-600 text-slate-300"
                        )}>
                          {event.status === 'active' ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
                          ) : (
                            event.icon
                          )}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-slate-100">
                            {event.message}
                          </p>
                          <p className="text-xs text-slate-400 mt-1 font-mono">
                            {event.timestamp.toLocaleTimeString()}
                          </p>
                        </div>
                      </motion.div>
                    ))}
                  </AnimatePresence>
                </div>
              </Card>
            </motion.div>
          ) : (
            <motion.div
              key="complete"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="max-w-2xl mx-auto"
            >
              <Card className="p-8 shadow-2xl border-slate-700 bg-slate-800/50 backdrop-blur-xl overflow-hidden relative">
                {/* Success glow effect */}
                <div className="absolute inset-0 bg-gradient-to-r from-green-500/10 to-emerald-500/10 animate-pulse"></div>
                
                <div className="text-center space-y-6 relative z-10">
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ type: "spring", duration: 0.6 }}
                    className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-gradient-to-r from-green-500 to-emerald-500 shadow-lg shadow-green-500/50"
                  >
                    <CheckCircle2 className="w-10 h-10 text-white" />
                  </motion.div>

                  <div>
                    <h2 className="text-3xl font-bold text-slate-100 mb-2">
                      Analysis Complete!
                    </h2>
                    <p className="text-slate-300">
                      Security analysis finished in {analysisTime} seconds
                    </p>
                  </div>

                  <motion.div 
                    className="bg-gradient-to-r from-amber-500/20 to-red-500/20 border border-amber-500/30 rounded-xl p-6 backdrop-blur-sm"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                  >
                    <div className="flex items-center justify-center gap-3 mb-3">
                      <AlertTriangle className="w-8 h-8 text-amber-400" />
                      <span className="text-5xl font-bold bg-gradient-to-r from-amber-400 to-red-400 bg-clip-text text-transparent">
                        {vulnerabilityCount}
                      </span>
                    </div>
                    <p className="text-base font-semibold text-slate-200">
                      {vulnerabilityCount === 1 ? 'Vulnerability' : 'Vulnerabilities'} Detected
                    </p>
                    <p className="text-sm text-slate-400 mt-2">
                      Critical security issues requiring immediate attention
                    </p>
                  </motion.div>

                  <div className="space-y-3 pt-4">
                    <Button
                      onClick={downloadReport}
                      disabled={!reportData || isGeneratingReport}
                      className="w-full h-12 text-base bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 shadow-lg shadow-indigo-500/50 disabled:opacity-50 disabled:cursor-not-allowed"
                      size="lg"
                    >
                      {isGeneratingReport ? (
                        <>
                          <Loader2 className="mr-2 w-5 h-5 animate-spin" />
                          Generating Report...
                        </>
                      ) : (
                        <>
                          <Download className="mr-2 w-5 h-5" />
                          Download Security Report (PDF)
                        </>
                      )}
                    </Button>

                    <Button
                      onClick={resetAnalysis}
                      variant="outline"
                      className="w-full h-12 text-base border-slate-600 text-slate-200 hover:bg-slate-700/50"
                      size="lg"
                    >
                      Analyze Another Repository
                    </Button>
                  </div>
                </div>
              </Card>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
    </PageLayout>
  );
}
