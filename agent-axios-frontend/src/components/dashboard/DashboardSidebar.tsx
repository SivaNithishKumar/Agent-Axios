import { Home, Clock, Star, User, Plus, Shield, TrendingUp, FileText, Settings, FolderGit2 } from "lucide-react";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarTrigger,
  useSidebar,
} from "@/components/ui/sidebar";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useNavigate, useLocation } from "react-router-dom";

const chatHistory = [
  { id: 1, title: "React security audit", time: "2 hours ago", severity: "medium" },
  { id: 2, title: "Next.js CVE check", time: "Yesterday", severity: "low" },
  { id: 3, title: "Express.js analysis", time: "2 days ago", severity: "high" },
  { id: 4, title: "Vue.js dependencies", time: "3 days ago", severity: "medium" },
];

const favoriteRepos = [
  { id: 1, name: "my-app/frontend", stars: 142, lastScan: "2 days ago" },
  { id: 2, name: "company/backend", stars: 89, lastScan: "1 week ago" },
  { id: 3, name: "mobile-app", stars: 56, lastScan: "3 days ago" },
];

const navigationItems = [
  { id: 1, title: "Dashboard", icon: Home, path: "/dashboard" },
  { id: 2, title: "Repositories", icon: FolderGit2, path: "/repositories" },
  { id: 3, title: "Reports", icon: FileText, path: "/reports" },
  { id: 4, title: "Settings", icon: Settings, path: "/settings" },
];

export function DashboardSidebar() {
  const { open } = useSidebar();
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <Sidebar className="border-r border-sidebar-border bg-sidebar">
      <div className="h-16 px-4 border-b border-sidebar-border flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-3 min-w-0">
          <div className="w-8 h-8 bg-gradient-to-br from-primary to-accent rounded-lg flex items-center justify-center flex-shrink-0 shadow-sm">
            <Shield className="w-4 h-4 text-primary-foreground" />
          </div>
          {open && (
            <span className="font-semibold text-sidebar-foreground truncate">CVE Analyzer</span>
          )}
        </div>
        <SidebarTrigger className="flex-shrink-0" />
      </div>

      <SidebarContent className="flex flex-col h-[calc(100vh-4rem)]">
        {/* New Analysis Button */}
        <div className="p-3 flex-shrink-0">
          <Button 
            className="w-full bg-primary hover:bg-primary-hover text-primary-foreground shadow-sm transition-all justify-start"
            size={open ? "default" : "icon"}
          >
            <Plus className={`w-4 h-4 ${open ? "mr-2" : ""}`} />
            {open && "New Analysis"}
          </Button>
        </div>

        {/* Navigation Items */}
        <div className="px-3 pb-3 flex-shrink-0">
          <SidebarMenu>
            {navigationItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              return (
                <SidebarMenuItem key={item.id}>
                  <SidebarMenuButton 
                    onClick={() => navigate(item.path)}
                    className={`transition-colors ${
                      isActive 
                        ? "bg-sidebar-accent text-sidebar-foreground font-medium" 
                        : "hover:bg-sidebar-accent/50"
                    }`}
                  >
                    <Icon className={`w-4 h-4 ${open ? "mr-3" : ""} flex-shrink-0`} />
                    {open && <span className="truncate">{item.title}</span>}
                  </SidebarMenuButton>
                </SidebarMenuItem>
              );
            })}
          </SidebarMenu>
        </div>

        {/* Stats Section */}
        {open && (
          <div className="px-3 pb-3 flex-shrink-0">
            <div className="bg-gradient-to-br from-primary/10 to-accent/10 rounded-xl p-4 border border-primary/20">
              <div className="flex items-center gap-2 mb-3">
                <TrendingUp className="w-4 h-4 text-primary" />
                <span className="text-sm font-medium text-sidebar-foreground">This Month</span>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <div className="text-2xl font-bold text-sidebar-foreground">42</div>
                  <div className="text-xs text-muted-foreground">Analyses</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-sidebar-foreground">12</div>
                  <div className="text-xs text-muted-foreground">Repositories</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Scrollable Content */}
        <ScrollArea className="flex-1 px-3">
          <div className="space-y-4 pb-4">
            <SidebarGroup>
              <SidebarGroupLabel className="flex items-center gap-2 px-2">
                <Clock className="w-4 h-4 flex-shrink-0" />
                {open && <span>Recent Chats</span>}
              </SidebarGroupLabel>
              <SidebarGroupContent>
                <SidebarMenu>
                  {chatHistory.map((chat) => (
                    <SidebarMenuItem key={chat.id}>
                      <SidebarMenuButton className="hover:bg-sidebar-accent transition-colors h-auto py-2">
                        {open ? (
                          <div className="flex flex-col gap-1 flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <span className="text-sm font-medium truncate">{chat.title}</span>
                              <Badge 
                                variant={chat.severity === "high" ? "destructive" : chat.severity === "medium" ? "default" : "secondary"}
                                className="text-xs shrink-0"
                              >
                                {chat.severity}
                              </Badge>
                            </div>
                            <span className="text-xs text-muted-foreground">{chat.time}</span>
                          </div>
                        ) : (
                          <div className="w-2 h-2 rounded-full bg-primary" />
                        )}
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  ))}
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>

            <SidebarGroup>
              <SidebarGroupLabel className="flex items-center gap-2 px-2">
                <Star className="w-4 h-4 flex-shrink-0" />
                {open && <span>Favorites</span>}
              </SidebarGroupLabel>
              <SidebarGroupContent>
                <SidebarMenu>
                  {favoriteRepos.map((repo) => (
                    <SidebarMenuItem key={repo.id}>
                      <SidebarMenuButton className="hover:bg-sidebar-accent transition-colors h-auto py-2">
                        {open ? (
                          <div className="flex flex-col gap-1 flex-1 min-w-0">
                            <div className="flex items-center justify-between gap-2">
                              <span className="text-sm font-medium truncate">{repo.name}</span>
                              <span className="text-xs text-muted-foreground shrink-0">{repo.stars} ⭐</span>
                            </div>
                            <span className="text-xs text-muted-foreground">Last scan: {repo.lastScan}</span>
                          </div>
                        ) : (
                          <Star className="w-4 h-4 fill-primary text-primary" />
                        )}
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  ))}
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>
          </div>
        </ScrollArea>

        {/* User Profile */}
        <div className="p-3 border-t border-sidebar-border flex-shrink-0">
          <div className="bg-sidebar-accent rounded-lg p-3">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-primary/20 to-accent/20 rounded-full flex items-center justify-center flex-shrink-0">
                <User className="w-5 h-5 text-primary" />
              </div>
              {open && (
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-sidebar-foreground truncate">John Doe</div>
                  <div className="text-xs text-muted-foreground">Pro Plan</div>
                </div>
              )}
            </div>
          </div>
        </div>
      </SidebarContent>
    </Sidebar>
  );
}
