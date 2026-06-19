/* eslint-disable react-refresh/only-export-components */
import { createBrowserRouter, Outlet } from 'react-router-dom';
import React, { Suspense } from 'react';
import { ProjectSwitcher } from '../features/project-switcher/ProjectSwitcher';
import { CommandPalette } from '../features/project-switcher/CommandPalette';
import { Login } from '../features/auth/Login';
import { AuthenticatedRoute } from '../features/auth/AuthenticatedRoute';

import { UploadQueueWidget } from '../features/upload/UploadQueueWidget';
import { NavLink, useNavigate } from 'react-router-dom';
import { Moon, Sun, LogOut } from 'lucide-react';
import { auth } from '../lib/firebase';

// Lazy loading features for code splitting
const AdminDashboard = React.lazy(() => import('../features/admin-dashboard/AdminDashboard'));
const ChatPage = React.lazy(() => import('../features/chat/ChatPage').then(m => ({ default: m.ChatPage })));
const MemberManagementPage = React.lazy(() => import('../features/members/MemberManagementPage'));
const AcceptInvitationPage = React.lazy(() => import('../features/members/AcceptInvitationPage'));
const ProjectReportPage = React.lazy(() => import('../pages/ProjectReportPage').then(m => ({ default: m.ProjectReportPage })));
import { HomePage } from '../features/home/HomePage';
// Other lazy components can be added here

const AppLayout = () => {
  const [isDark, setIsDark] = React.useState(false);
  const navigate = useNavigate();

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
    <div className="min-h-screen bg-background text-foreground flex flex-col relative transition-colors duration-200">
      <CommandPalette />
      <UploadQueueWidget />
      <header className="border-b px-4 py-3 flex justify-between items-center bg-card">
        <div className="flex items-center gap-6">
          <h1 className="text-xl font-bold tracking-tight">OmniMind v2</h1>
          <nav className="hidden md:flex gap-4 ml-4">
            <NavLink to="/" end className={({isActive}) => `text-sm font-medium transition-colors ${isActive ? 'text-primary' : 'text-muted-foreground hover:text-foreground'}`}>
              Home
            </NavLink>
            <NavLink to="/admin" className={({isActive}) => `text-sm font-medium transition-colors ${isActive ? 'text-primary' : 'text-muted-foreground hover:text-foreground'}`}>
              Dashboard
            </NavLink>
            <NavLink to="/chat" className={({isActive}) => `text-sm font-medium transition-colors ${isActive ? 'text-primary' : 'text-muted-foreground hover:text-foreground'}`}>
              Chat
            </NavLink>
            <NavLink to="/members" className={({isActive}) => `text-sm font-medium transition-colors ${isActive ? 'text-primary' : 'text-muted-foreground hover:text-foreground'}`}>
              Members
            </NavLink>
          </nav>
        </div>
        <div className="flex items-center gap-3">
          <button 
            onClick={toggleTheme}
            className="p-2 rounded-md hover:bg-accent text-muted-foreground hover:text-foreground transition-colors"
            title="Toggle theme"
          >
            {isDark ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
          </button>
          <ProjectSwitcher />
          <button 
            onClick={handleSignOut}
            className="p-2 rounded-md hover:bg-destructive/10 text-muted-foreground hover:text-destructive transition-colors"
            title="Sign out"
          >
            <LogOut className="w-5 h-5" />
          </button>
        </div>
      </header>
      <main className="flex-1 p-4">
        <Suspense fallback={<div>Loading...</div>}>
          <Outlet />
        </Suspense>
      </main>
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
    element: (
      <AuthenticatedRoute>
        <AppLayout />
      </AuthenticatedRoute>
    ),
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
]);
