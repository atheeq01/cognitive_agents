import React, { createContext, useContext, useEffect, useState } from 'react';
import { onAuthStateChanged, type User } from 'firebase/auth';
import { auth } from '../../lib/firebase';

interface AuthContextType {
  user: User | null;
  loading: boolean;
  loginWithMock: () => void;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  loading: true,
  loginWithMock: () => {},
});

const IS_MOCK_MODE =
  import.meta.env.DEV && import.meta.env.VITE_FIREBASE_API_KEY === undefined;

const MOCK_USER = {
  uid: 'mock-user-123',
  email: 'admin@omnimind.local',
  displayName: 'Admin',
} as User;

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // Allow the Login page to explicitly set the mock user in dev mode.
  // In real mode this is a no-op.
  const loginWithMock = () => {
    if (IS_MOCK_MODE) {
      setUser(MOCK_USER);
    }
  };

  useEffect(() => {
    if (IS_MOCK_MODE) {
      // Do NOT auto-login — wait for the user to click "Bypass Login" on the login page.
      // Just stop the loading spinner so the login page renders.
      setLoading(false);
      return;
    }

    const unsubscribe = onAuthStateChanged(auth, (firebaseUser) => {
      setUser(firebaseUser);
      setLoading(false);
    });

    return () => unsubscribe();
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, loginWithMock }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
