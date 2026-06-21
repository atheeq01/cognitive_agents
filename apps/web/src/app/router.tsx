/* eslint-disable react-refresh/only-export-components */
import { createBrowserRouter, Outlet } from 'react-router-dom';
import React, { Suspense } from 'react';
import { ProjectSwitcher } from '../features/project-switcher/ProjectSwitcher';
import { CommandPalette } from '../features/project-switcher/CommandPalette';
import { PendingInvitationsDropdown } from '../features/members/PendingInvitationsDropdown';
import { Login } from '../features/auth/Login';
import { AuthenticatedRoute } from '../features/auth/AuthenticatedRoute';

import { UploadQueueWidget } from '../features/upload/UploadQueueWidget';
import { NavLink, useNavigate } from 'react-router-dom';
import { Moon, Sun, LogOut, Home, MessageSquare, FileText, PieChart, Users, Settings } from 'lucide-react';
import { useAuth } from '../app/providers/AuthProvider';
import { auth } from '../lib/firebase';

// Lazy loading features for code splitting
const AdminDashboard = React.lazy(() => import('../features/admin-dashboard/AdminDashboard'));
const ChatPage = React.lazy(() => import('../features/chat/ChatPage').then(m => ({ default: m.ChatPage })));
const MemberManagementPage = React.lazy(() => import('../features/members/MemberManagementPage'));
const AcceptInvitationPage = React.lazy(() => import('../features/members/AcceptInvitationPage'));
const ProjectReportPage = React.lazy(() => import('../pages/ProjectReportPage').then(m => ({ default: m.ProjectReportPage })));
import { HomePage } from '../features/home/HomePage';
import { ProjectProvider, useProject } from './providers/ProjectProvider';

const NavItem = ({ to, icon: Icon, children, exact }: { to: string, icon: any, children: React.ReactNode, exact?: boolean }) => (
  <NavLink
    to={to}
    end={exact}
    className={({ isActive }) => `flex items-center gap-3 px-3 py-2 rounded-xl text-sm font-medium transition-all duration-200 ${
      isActive 
        ? 'bg-card text-foreground shadow-sm' 
        : 'text-muted-foreground hover:bg-accent/50 hover:text-foreground'
    }`}
  >
    <Icon className="w-5 h-5" />
    {children}
  </NavLink>
);

const AppLayout = () => {
  const [isDark, setIsDark] = React.useState(false);
  const navigate = useNavigate();
  const { activeProject } = useProject();
  const { user } = useAuth();
  const projectId = activeProject?.project_id || '';

  React.useEffect(() => {
    setIsDark(document.documentElement.classList.contains('dark'));
  }, []);

  const handleSignOut = async () => {
    await auth.signOut();
    navigate('/login');
  };

  const toggleTheme = () => {
    document.documentElement.classList.toggle('dark');
    setIsDark(!isDark);
  };

  return (
    <div className="h-screen w-full bg-muted/30 text-foreground flex overflow-hidden transition-colors duration-200">
      <CommandPalette />
      <UploadQueueWidget />
      
      {/* Sidebar */}
      <aside className="w-64 flex flex-col justify-between py-6 px-4">
        <div className="space-y-8">
          <div className="px-3 flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center text-primary-foreground font-bold text-lg">
              O
            </div>
            <h1 className="text-xl font-bold tracking-tight">OmniMind v2</h1>
          </div>

          <div className="space-y-6">
            <nav className="space-y-1">
              <NavItem to={`/projects/${projectId}`} exact icon={Home}>Home</NavItem>
            </nav>

            <div>
              <h4 className="px-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">Workspace</h4>
              <nav className="space-y-1">
                <NavItem to={`/projects/${projectId}/admin`} icon={FileText}>Documents</NavItem>
                <NavItem to={`/projects/${projectId}/report`} icon={PieChart}>Project Report</NavItem>
              </nav>
            </div>

            <div>
              <h4 className="px-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">Agent</h4>
              <nav className="space-y-1">
                <NavItem to={`/projects/${projectId}/chat`} icon={MessageSquare}>Knowledge Chat</NavItem>
              </nav>
            </div>

            <div>
              <h4 className="px-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">Team</h4>
              <nav className="space-y-1">
                <NavItem to={`/projects/${projectId}/members`} icon={Users}>Team Access</NavItem>
              </nav>
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <div className="px-3 flex items-center justify-between">
            <PendingInvitationsDropdown />
            <ProjectSwitcher />
          </div>

          <div className="space-y-1 pt-4 border-t">
            <button
              onClick={toggleTheme}
              className="w-full flex items-center gap-3 px-3 py-2 rounded-xl text-sm font-medium text-muted-foreground hover:bg-accent/50 hover:text-foreground transition-all duration-200"
            >
              {isDark ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
              {isDark ? 'Light Mode' : 'Dark Mode'}
            </button>
            
            <div className="w-full flex items-center justify-between px-3 py-2 mt-2">
              <div className="flex items-center gap-2 overflow-hidden">
                <div className="w-8 h-8 rounded-full bg-accent flex items-center justify-center flex-shrink-0">
                  {user?.displayName?.charAt(0) || user?.email?.charAt(0) || 'U'}
                </div>
                <div className="truncate text-sm font-medium">
                  {user?.displayName || user?.email?.split('@')[0] || 'User'}
                </div>
              </div>
              <button 
                onClick={handleSignOut}
                className="p-1.5 rounded-md hover:bg-destructive/10 text-muted-foreground hover:text-destructive transition-colors"
                title="Log out"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 p-4 lg:p-6 lg:pl-0 overflow-hidden h-full">
        <div className="bg-card h-full w-full rounded-[2rem] shadow-sm border border-border/50 overflow-y-auto relative">
          <Suspense fallback={<div className="p-8 flex justify-center"><div className="animate-pulse">Loading...</div></div>}>
            <Outlet />
          </Suspense>
        </div>
      </main>
    </div>
  );
};

import { Navigate } from 'react-router-dom';

const RootRedirector = () => {
  const { projects, isLoading, createProject, isCreating } = useProject();
  const [name, setName] = React.useState('');
  
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="animate-pulse text-muted-foreground">Loading...</div>
      </div>
    );
  }

  if (projects.length === 0) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background p-4">
        <div className="bg-card border rounded-xl shadow-2xl p-8 w-full max-w-md text-center">
          <h2 className="text-2xl font-bold mb-2">Welcome to OmniMind</h2>
          <p className="text-muted-foreground mb-6">Create your first project to get started.</p>
          <form onSubmit={async (e) => {
            e.preventDefault();
            if (name.trim()) await createProject(name.trim());
          }} className="space-y-4 text-left">
            <div>
              <label className="block text-sm font-medium mb-1">Project Name</label>
              <input
                autoFocus
                required
                className="w-full px-3 py-2 border rounded-md bg-input text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                placeholder="e.g. Legal Review 2025"
                value={name}
                onChange={e => setName(e.target.value)}
              />
            </div>
            <button
              type="submit"
              disabled={isCreating || !name.trim()}
              className="w-full py-2 px-4 rounded-md bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
            >
              {isCreating ? 'Creating...' : 'Create Project'}
            </button>
          </form>
        </div>
      </div>
    );
  }

  return null; // ProjectProvider's useEffect handles redirecting to the first project
};

const GlobalError = () => {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-background text-foreground p-4">
      <h1 className="text-4xl font-bold mb-4">404 - Not Found</h1>
      <p className="text-muted-foreground mb-8">The page you're looking for doesn't exist or you don't have access.</p>
      <a href="/" className="px-6 py-2 rounded-md bg-primary text-primary-foreground hover:bg-primary/90 transition-colors">
        Go Home
      </a>
    </div>
  );
};

export const router = createBrowserRouter([
  {
    path: '/login',
    element: <Login />,
  },
  {
    path: '/accept-invite/:token',
    element: (
      <Suspense fallback={<div>Loading...</div>}>
        <AcceptInvitationPage />
      </Suspense>
    ),
  },
  {
    path: '/',
    errorElement: <GlobalError />,
    element: (
      <AuthenticatedRoute>
        <ProjectProvider>
          <Outlet />
        </ProjectProvider>
      </AuthenticatedRoute>
    ),
    children: [
      {
        path: '',
        element: <RootRedirector />,
      },
      {
        path: 'projects/:projectId',
        element: <AppLayout />,
        children: [
          {
            path: '',
            element: <HomePage />,
          },
          {
            path: 'admin/*',
            element: <AdminDashboard />,
          },
          {
            path: 'report',
            element: <ProjectReportPage />,
          },
          {
            path: 'chat',
            element: <ChatPage />,
          },
          {
            path: 'members',
            element: <MemberManagementPage />,
          },
        ],
      },
      {
        path: '*',
        element: <Navigate to="/" replace />
      }
    ],
  },
]);
