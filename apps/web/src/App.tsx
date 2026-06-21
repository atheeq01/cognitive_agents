import { RouterProvider } from 'react-router-dom';
import { AuthProvider } from './app/providers/AuthProvider';
import { QueryProvider } from './app/providers/QueryProvider';
import { router } from './app/router';
import { Toaster } from 'sonner';

function App() {
  return (
    <QueryProvider>
      <AuthProvider>
        <Toaster position="top-right" richColors />
        <RouterProvider router={router} />
      </AuthProvider>
    </QueryProvider>
  );
}

export default App;

