import { createBrowserRouter, Outlet } from 'react-router-dom';
import React, { Suspense } from 'react';
import { ProjectSwitcher } from '../features/project-switcher/ProjectSwitcher';
import { CommandPalette } from '../features/project-switcher/CommandPalette';
import { Login } from '../features/auth/Login';
import { AuthenticatedRoute } from '../features/auth/AuthenticatedRoute';

import { UploadQueueWidget } from '../features/upload/UploadQueueWidget';
import { NavLink } from 'react-router-dom';

// Lazy loading features for code splitting
const AdminDashboard = React.lazy(() => import('../features/admin-dashboard/AdminDashboard'));
const ChatPage = React.lazy(() => import('../features/chat/ChatPage').then(m => ({ default: m.ChatPage })));
// Other lazy components can be added here

const AppLayout = () => {
  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col relative">
      <CommandPalette />
      <UploadQueueWidget />
      <header className="border-b px-4 py-3 flex justify-between items-center bg-card">
        <div className="flex items-center gap-6">
          <h1 className="text-xl font-bold tracking-tight">OmniMind v2</h1>
          <nav className="hidden md:flex gap-4 ml-4">
            <NavLink to="/" className={({isActive}) => `text-sm font-medium transition-colors ${isActive ? 'text-primary' : 'text-muted-foreground hover:text-foreground'}`}>
              Dashboard
            </NavLink>
            <NavLink to="/chat" className={({isActive}) => `text-sm font-medium transition-colors ${isActive ? 'text-primary' : 'text-muted-foreground hover:text-foreground'}`}>
              Chat
            </NavLink>
          </nav>
        </div>
        <div className="flex items-center gap-4">
           <ProjectSwitcher />
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
    path: '/',
    element: (
      <AuthenticatedRoute>
        <AppLayout />
      </AuthenticatedRoute>
    ),
    children: [
      {
        path: '',
        element: <div>Welcome to OmniMind v2! Press Cmd+K to navigate.</div>,
      },
      {
        path: 'admin/*',
        element: <AdminDashboard />,
      },
      {
        path: 'chat',
        element: <ChatPage />,
      },
    ],
  },
]);
