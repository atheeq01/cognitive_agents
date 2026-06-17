import { RouterProvider } from 'react-router-dom';
import { AuthProvider } from './app/providers/AuthProvider';
import { ProjectProvider } from './app/providers/ProjectProvider';
import { QueryProvider } from './app/providers/QueryProvider';
import { router } from './app/router';
import { Toaster } from 'sonner';

function App() {
  return (
    <QueryProvider>
      <AuthProvider>
        <ProjectProvider>
          <Toaster position="top-right" richColors />
          <RouterProvider router={router} />
        </ProjectProvider>
      </AuthProvider>
    </QueryProvider>
  );
}

export default App;

