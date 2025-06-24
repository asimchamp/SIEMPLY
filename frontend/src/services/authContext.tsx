import React, { createContext, useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import api from './api';

// Define types
interface User {
  id: number;
  username: string;
  email: string;
  role: string;
  full_name?: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  checkAuth: () => Promise<boolean>;
}

// Create the auth context
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Custom hook to use the auth context
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Auth provider component
export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const navigate = useNavigate();

  // Check if user is authenticated on initial load
  useEffect(() => {
    const checkUserAuth = async () => {
      try {
        await checkAuth();
      } catch (error) {
        console.error('Authentication check failed:', error);
      } finally {
        setLoading(false);
      }
    };

    checkUserAuth();
  }, []);

  // Add authorization header to all requests if token exists
  useEffect(() => {
    const token = localStorage.getItem('siemply_token');
    if (token) {
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    }
  }, [isAuthenticated]);

  // Check if the user is authenticated by validating their token
  const checkAuth = async (): Promise<boolean> => {
    const token = localStorage.getItem('siemply_token');
    
    if (!token) {
      setIsAuthenticated(false);
      setUser(null);
      return false;
    }

    try {
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      const response = await api.get('/auth/users/me');
      
      setUser(response.data);
      setIsAuthenticated(true);
      return true;
    } catch (error) {
      console.error('Token validation failed:', error);
      // Clear invalid token
      localStorage.removeItem('siemply_token');
      delete api.defaults.headers.common['Authorization'];
      setUser(null);
      setIsAuthenticated(false);
      return false;
    }
  };

  // Login function
  const login = async (username: string, password: string): Promise<void> => {
    setLoading(true);
    
    try {
      // Create form data (required for OAuth2 password flow)
      const formData = new FormData();
      formData.append('username', username);
      formData.append('password', password);

      // Call the token endpoint
      const response = await api.post('/auth/token', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      });

      // Store token in localStorage
      localStorage.setItem('siemply_token', response.data.access_token);
      
      // Set authorization header for future API calls
      api.defaults.headers.common['Authorization'] = `Bearer ${response.data.access_token}`;
      
      // Get user details
      await checkAuth();
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  // Logout function
  const logout = () => {
    // Remove token from localStorage
    localStorage.removeItem('siemply_token');
    
    // Remove authorization header
    delete api.defaults.headers.common['Authorization'];
    
    // Reset state
    setUser(null);
    setIsAuthenticated(false);
    
    // Redirect to login page
    navigate('/login');
  };

  const value = {
    user,
    loading,
    isAuthenticated,
    login,
    logout,
    checkAuth,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// Private route component to protect routes that require authentication
export const RequireAuth: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      navigate('/login');
    }
  }, [isAuthenticated, loading, navigate]);

  if (loading) {
    return <div>Loading...</div>;
  }

  return isAuthenticated ? <>{children}</> : null;
};

// Admin route component to protect routes that require admin access
export const RequireAdmin: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, loading, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!loading) {
      if (!isAuthenticated) {
        navigate('/login');
      } else if (user && user.role !== 'admin') {
        navigate('/dashboard');
      }
    }
  }, [user, isAuthenticated, loading, navigate]);

  if (loading) {
    return <div>Loading...</div>;
  }

  return isAuthenticated && user?.role === 'admin' ? <>{children}</> : null;
}; 