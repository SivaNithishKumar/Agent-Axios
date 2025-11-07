import { useState } from "react";
import { DashboardSidebar } from "@/components/dashboard/DashboardSidebar";
import { DashboardHeader } from "@/components/dashboard/DashboardHeader";
import { SidebarProvider } from "@/components/ui/sidebar";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { 
  FileText, 
  Download, 
  Calendar, 
  AlertCircle, 
  CheckCircle, 
  XCircle,
  Search,
  Filter,
  TrendingUp
} from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const reports = [
  {
    id: 1,
    repository: "user/react-app",
    date: "2024-11-08",
    vulnerabilities: {
      critical: 2,
      high: 5,
      medium: 8,
      low: 3
    },
    status: "critical",
    totalIssues: 18,
  },
  {
    id: 2,
    repository: "company/backend-api",
    date: "2024-11-07",
    vulnerabilities: {
      critical: 0,
      high: 2,
      medium: 4,
      low: 6
    },
    status: "warning",
    totalIssues: 12,
  },
  {
    id: 3,
    repository: "team/mobile-app",
    date: "2024-11-06",
    vulnerabilities: {
      critical: 0,
      high: 0,
      medium: 1,
      low: 2
    },
    status: "safe",
    totalIssues: 3,
  },
  {
    id: 4,
    repository: "opensource/library",
    date: "2024-11-05",
    vulnerabilities: {
      critical: 1,
      high: 3,
      medium: 5,
      low: 4
    },
    status: "critical",
    totalIssues: 13,
  },
];

const Reports = () => {
  const [searchQuery, setSearchQuery] = useState("");
  const [filterStatus, setFilterStatus] = useState("all");

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "critical":
        return <Badge variant="destructive" className="gap-1"><XCircle className="w-3 h-3" />Critical</Badge>;
      case "warning":
        return <Badge variant="default" className="gap-1 bg-warning text-warning-foreground"><AlertCircle className="w-3 h-3" />Warning</Badge>;
      case "safe":
        return <Badge variant="secondary" className="gap-1 bg-success/10 text-success border-success/20"><CheckCircle className="w-3 h-3" />Safe</Badge>;
      default:
        return null;
    }
  };

  const filteredReports = reports.filter(report => {
    const matchesSearch = report.repository.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesFilter = filterStatus === "all" || report.status === filterStatus;
    return matchesSearch && matchesFilter;
  });

  return (
    <SidebarProvider>
      <div className="min-h-screen flex w-full bg-background">
        <DashboardSidebar />
        
        <div className="flex-1 flex flex-col min-w-0">
          <DashboardHeader />
          
          <div className="flex-1 overflow-hidden">
            <ScrollArea className="h-full">
              <div className="p-4 lg:p-8 max-w-7xl mx-auto">
                {/* Page Header */}
                <div className="mb-8">
                  <h1 className="text-3xl font-bold text-foreground mb-2">Security Reports</h1>
                  <p className="text-muted-foreground">View and manage your vulnerability analysis reports</p>
                </div>

                {/* Stats Cards */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm font-medium text-muted-foreground">Total Reports</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-3xl font-bold text-foreground">{reports.length}</div>
                      <p className="text-xs text-muted-foreground mt-1">All time</p>
                    </CardContent>
                  </Card>
                  
                  <Card className="border-destructive/20">
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm font-medium text-muted-foreground">Critical Issues</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-3xl font-bold text-destructive">
                        {reports.reduce((sum, r) => sum + r.vulnerabilities.critical, 0)}
                      </div>
                      <p className="text-xs text-muted-foreground mt-1">Require immediate action</p>
                    </CardContent>
                  </Card>
                  
                  <Card className="border-warning/20">
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm font-medium text-muted-foreground">High Priority</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-3xl font-bold text-warning">
                        {reports.reduce((sum, r) => sum + r.vulnerabilities.high, 0)}
                      </div>
                      <p className="text-xs text-muted-foreground mt-1">Should be addressed soon</p>
                    </CardContent>
                  </Card>
                  
                  <Card className="border-success/20">
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm font-medium text-muted-foreground">Safe Repos</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-3xl font-bold text-success">
                        {reports.filter(r => r.status === "safe").length}
                      </div>
                      <p className="text-xs text-muted-foreground mt-1">No critical issues</p>
                    </CardContent>
                  </Card>
                </div>

                {/* Filters */}
                <div className="flex flex-col sm:flex-row gap-4 mb-6">
                  <div className="flex-1 relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                    <Input
                      placeholder="Search repositories..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="pl-10"
                    />
                  </div>
                  <Select value={filterStatus} onValueChange={setFilterStatus}>
                    <SelectTrigger className="w-full sm:w-[180px]">
                      <Filter className="w-4 h-4 mr-2" />
                      <SelectValue placeholder="Filter by status" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Status</SelectItem>
                      <SelectItem value="critical">Critical</SelectItem>
                      <SelectItem value="warning">Warning</SelectItem>
                      <SelectItem value="safe">Safe</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* Reports List */}
                <div className="space-y-4">
                  {filteredReports.map((report) => (
                    <Card key={report.id} className="hover:border-primary/50 transition-all hover:shadow-sm">
                      <CardHeader>
                        <div className="flex items-start justify-between gap-4">
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-3 mb-2">
                              <div className="w-10 h-10 bg-gradient-to-br from-primary/10 to-accent/10 rounded-lg flex items-center justify-center flex-shrink-0">
                                <FileText className="w-5 h-5 text-primary" />
                              </div>
                              <div className="flex-1 min-w-0">
                                <CardTitle className="text-lg truncate">{report.repository}</CardTitle>
                                <CardDescription className="flex items-center gap-2 mt-1">
                                  <Calendar className="w-3 h-3" />
                                  {new Date(report.date).toLocaleDateString('en-US', { 
                                    year: 'numeric', 
                                    month: 'long', 
                                    day: 'numeric' 
                                  })}
                                </CardDescription>
                              </div>
                            </div>
                          </div>
                          <div className="flex items-center gap-2 flex-shrink-0">
                            {getStatusBadge(report.status)}
                          </div>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-4">
                          {/* Vulnerability Breakdown */}
                          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                            <div className="p-3 bg-destructive/10 rounded-lg border border-destructive/20">
                              <div className="text-xs text-muted-foreground mb-1">Critical</div>
                              <div className="text-2xl font-bold text-destructive">{report.vulnerabilities.critical}</div>
                            </div>
                            <div className="p-3 bg-warning/10 rounded-lg border border-warning/20">
                              <div className="text-xs text-muted-foreground mb-1">High</div>
                              <div className="text-2xl font-bold text-warning">{report.vulnerabilities.high}</div>
                            </div>
                            <div className="p-3 bg-primary/10 rounded-lg border border-primary/20">
                              <div className="text-xs text-muted-foreground mb-1">Medium</div>
                              <div className="text-2xl font-bold text-primary">{report.vulnerabilities.medium}</div>
                            </div>
                            <div className="p-3 bg-secondary rounded-lg border border-border">
                              <div className="text-xs text-muted-foreground mb-1">Low</div>
                              <div className="text-2xl font-bold text-foreground">{report.vulnerabilities.low}</div>
                            </div>
                          </div>

                          {/* Actions */}
                          <div className="flex gap-2">
                            <Button variant="default" size="sm" className="flex-1 sm:flex-none">
                              <FileText className="w-4 h-4 mr-2" />
                              View Details
                            </Button>
                            <Button variant="outline" size="sm">
                              <Download className="w-4 h-4 mr-2" />
                              Export PDF
                            </Button>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}

                  {filteredReports.length === 0 && (
                    <Card className="p-12">
                      <div className="text-center">
                        <FileText className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                        <h3 className="text-lg font-semibold text-foreground mb-2">No reports found</h3>
                        <p className="text-muted-foreground">Try adjusting your search or filter criteria</p>
                      </div>
                    </Card>
                  )}
                </div>
              </div>
            </ScrollArea>
          </div>
        </div>
      </div>
    </SidebarProvider>
  );
};

export default Reports;
