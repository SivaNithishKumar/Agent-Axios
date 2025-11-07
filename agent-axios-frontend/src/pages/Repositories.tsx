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
  FolderGit2, 
  Star, 
  GitBranch, 
  Clock, 
  Plus,
  Search,
  MoreVertical,
  Trash2,
  RefreshCw,
  ExternalLink,
  AlertTriangle
} from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";

const repositories = [
  {
    id: 1,
    name: "my-app/frontend",
    url: "github.com/my-app/frontend",
    language: "TypeScript",
    lastScan: "2 hours ago",
    nextScan: "In 22 hours",
    vulnerabilities: 5,
    starred: true,
    status: "healthy",
    branches: 12,
  },
  {
    id: 2,
    name: "company/backend-api",
    url: "github.com/company/backend-api",
    language: "Python",
    lastScan: "1 day ago",
    nextScan: "In 6 hours",
    vulnerabilities: 12,
    starred: false,
    status: "warning",
    branches: 8,
  },
  {
    id: 3,
    name: "team/mobile-app",
    url: "github.com/team/mobile-app",
    language: "React Native",
    lastScan: "3 days ago",
    nextScan: "Overdue",
    vulnerabilities: 3,
    starred: true,
    status: "healthy",
    branches: 15,
  },
  {
    id: 4,
    name: "opensource/library",
    url: "github.com/opensource/library",
    language: "JavaScript",
    lastScan: "5 days ago",
    nextScan: "Overdue",
    vulnerabilities: 18,
    starred: false,
    status: "critical",
    branches: 6,
  },
];

const Repositories = () => {
  const [searchQuery, setSearchQuery] = useState("");
  const [repos, setRepos] = useState(repositories);
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [newRepoUrl, setNewRepoUrl] = useState("");

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "healthy":
        return <Badge variant="secondary" className="bg-success/10 text-success border-success/20">Healthy</Badge>;
      case "warning":
        return <Badge variant="default" className="bg-warning/90 text-warning-foreground">Warning</Badge>;
      case "critical":
        return <Badge variant="destructive">Critical</Badge>;
      default:
        return null;
    }
  };

  const toggleStar = (id: number) => {
    setRepos(repos.map(repo => 
      repo.id === id ? { ...repo, starred: !repo.starred } : repo
    ));
  };

  const filteredRepos = repos.filter(repo =>
    repo.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    repo.language.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleAddRepo = () => {
    if (newRepoUrl.trim()) {
      // In a real app, this would make an API call
      console.log("Adding repository:", newRepoUrl);
      setNewRepoUrl("");
      setIsAddDialogOpen(false);
    }
  };

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
                <div className="flex items-start justify-between mb-8 gap-4">
                  <div>
                    <h1 className="text-3xl font-bold text-foreground mb-2">Repositories</h1>
                    <p className="text-muted-foreground">Manage and monitor your tracked repositories</p>
                  </div>
                  <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
                    <DialogTrigger asChild>
                      <Button className="gap-2 flex-shrink-0">
                        <Plus className="w-4 h-4" />
                        Add Repository
                      </Button>
                    </DialogTrigger>
                    <DialogContent>
                      <DialogHeader>
                        <DialogTitle>Add New Repository</DialogTitle>
                        <DialogDescription>
                          Enter the GitHub repository URL you want to monitor for vulnerabilities
                        </DialogDescription>
                      </DialogHeader>
                      <div className="space-y-4 pt-4">
                        <div className="space-y-2">
                          <Label htmlFor="repo-url">Repository URL</Label>
                          <Input
                            id="repo-url"
                            placeholder="https://github.com/username/repository"
                            value={newRepoUrl}
                            onChange={(e) => setNewRepoUrl(e.target.value)}
                          />
                        </div>
                        <div className="flex gap-2 justify-end">
                          <Button variant="outline" onClick={() => setIsAddDialogOpen(false)}>
                            Cancel
                          </Button>
                          <Button onClick={handleAddRepo}>
                            Add Repository
                          </Button>
                        </div>
                      </div>
                    </DialogContent>
                  </Dialog>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm font-medium text-muted-foreground">Total Repositories</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-3xl font-bold text-foreground">{repos.length}</div>
                    </CardContent>
                  </Card>
                  
                  <Card>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm font-medium text-muted-foreground">Starred</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-3xl font-bold text-foreground">
                        {repos.filter(r => r.starred).length}
                      </div>
                    </CardContent>
                  </Card>
                  
                  <Card className="border-warning/20">
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm font-medium text-muted-foreground">Need Attention</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-3xl font-bold text-warning">
                        {repos.filter(r => r.status !== "healthy").length}
                      </div>
                    </CardContent>
                  </Card>
                  
                  <Card className="border-destructive/20">
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm font-medium text-muted-foreground">Total Vulnerabilities</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="text-3xl font-bold text-destructive">
                        {repos.reduce((sum, r) => sum + r.vulnerabilities, 0)}
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* Search */}
                <div className="mb-6">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                    <Input
                      placeholder="Search repositories..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="pl-10"
                    />
                  </div>
                </div>

                {/* Repository Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  {filteredRepos.map((repo) => (
                    <Card key={repo.id} className="hover:border-primary/50 transition-all hover:shadow-sm">
                      <CardHeader>
                        <div className="flex items-start justify-between gap-4">
                          <div className="flex items-start gap-3 flex-1 min-w-0">
                            <div className="w-12 h-12 bg-gradient-to-br from-primary/10 to-accent/10 rounded-lg flex items-center justify-center flex-shrink-0">
                              <FolderGit2 className="w-6 h-6 text-primary" />
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 mb-1">
                                <CardTitle className="text-lg truncate">{repo.name}</CardTitle>
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  className="h-6 w-6 flex-shrink-0"
                                  onClick={() => toggleStar(repo.id)}
                                >
                                  <Star className={`w-4 h-4 ${repo.starred ? 'fill-primary text-primary' : ''}`} />
                                </Button>
                              </div>
                              <CardDescription className="truncate">{repo.url}</CardDescription>
                            </div>
                          </div>
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="icon" className="flex-shrink-0">
                                <MoreVertical className="w-4 h-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem>
                                <RefreshCw className="w-4 h-4 mr-2" />
                                Scan Now
                              </DropdownMenuItem>
                              <DropdownMenuItem>
                                <ExternalLink className="w-4 h-4 mr-2" />
                                Open in GitHub
                              </DropdownMenuItem>
                              <DropdownMenuSeparator />
                              <DropdownMenuItem className="text-destructive">
                                <Trash2 className="w-4 h-4 mr-2" />
                                Remove
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </div>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        {/* Status & Vulnerabilities */}
                        <div className="flex items-center justify-between gap-4">
                          {getStatusBadge(repo.status)}
                          {repo.vulnerabilities > 0 && (
                            <div className="flex items-center gap-2 text-sm">
                              <AlertTriangle className="w-4 h-4 text-destructive" />
                              <span className="font-medium">{repo.vulnerabilities} vulnerabilities</span>
                            </div>
                          )}
                        </div>

                        {/* Metadata */}
                        <div className="grid grid-cols-2 gap-3 text-sm">
                          <div className="flex items-center gap-2 text-muted-foreground">
                            <GitBranch className="w-4 h-4" />
                            <span>{repo.branches} branches</span>
                          </div>
                          <div className="flex items-center gap-2 text-muted-foreground">
                            <Clock className="w-4 h-4" />
                            <span>{repo.lastScan}</span>
                          </div>
                        </div>

                        {/* Language Badge */}
                        <div>
                          <Badge variant="outline">{repo.language}</Badge>
                        </div>

                        {/* Next Scan */}
                        <div className="pt-3 border-t border-border">
                          <div className="text-xs text-muted-foreground mb-1">Next scheduled scan</div>
                          <div className={`text-sm font-medium ${repo.nextScan === "Overdue" ? "text-destructive" : "text-foreground"}`}>
                            {repo.nextScan}
                          </div>
                        </div>

                        {/* Actions */}
                        <div className="flex gap-2 pt-2">
                          <Button variant="default" size="sm" className="flex-1">
                            View Details
                          </Button>
                          <Button variant="outline" size="sm">
                            <RefreshCw className="w-4 h-4" />
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>

                {filteredRepos.length === 0 && (
                  <Card className="p-12">
                    <div className="text-center">
                      <FolderGit2 className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                      <h3 className="text-lg font-semibold text-foreground mb-2">No repositories found</h3>
                      <p className="text-muted-foreground mb-4">Try adjusting your search query</p>
                      <Button onClick={() => setIsAddDialogOpen(true)}>
                        <Plus className="w-4 h-4 mr-2" />
                        Add Your First Repository
                      </Button>
                    </div>
                  </Card>
                )}
              </div>
            </ScrollArea>
          </div>
        </div>
      </div>
    </SidebarProvider>
  );
};

export default Repositories;
