import { createContext, useContext } from 'react';

// Create context here to avoid Fast Refresh errors
export const AuthContext = createContext();

// Hook for consuming auth context
export const useAuth = () => useContext(AuthContext);
