import React, { useState, useEffect } from "react";
import SafetyAPI, { setAccessToken } from "../api";
import { AuthContext } from "./AuthHooks";

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [isAuthenticated, setIsAuthenticated] = useState(null); // null = checking
    const [loading, setLoading] = useState(true);

    // Check auth status on mount (silent refresh via cookie)
    useEffect(() => {
        const initAuth = async () => {
            try {
                // Try to restore session via refresh cookie
                // This is REQUIRED because access token is memory-only and cleared on reload
                await SafetyAPI.refreshToken();
                // Access token is automatically set in api.js by our new refreshToken wrapper

                // Verify token / Get User
                const userData = await SafetyAPI.getMe();
                setUser(userData);
                setIsAuthenticated(true);
            } catch (err) {
                // No valid refresh cookie or 7-day expiry hit
                console.debug("Session restoration failed (Normal if new user):", err);
                setIsAuthenticated(false);
                setUser(null);
                setAccessToken(null);
            } finally {
                setLoading(false);
            }
        };

        initAuth();
    }, []);

    const login = async (email, password) => {
        try {
            const data = await SafetyAPI.login(email, password);
            setAccessToken(data.access_token);

            // Fetch user profile immediately
            const userData = await SafetyAPI.getMe();
            setUser(userData);
            setIsAuthenticated(true);
            return data;
        } catch (error) {
            setIsAuthenticated(false);
            throw error;
        }
    };

    const signup = async (email, password, role) => {
        const data = await SafetyAPI.signup(email, password, role);
        return data; // Signup usually doesn't auto-login in this flow, or it does? Standard is redirect to login.
    };

    const logout = async () => {
        try {
            await SafetyAPI.logout();
        } catch (err) {
            console.warn("Logout API call failed", err);
        }
        setAccessToken(null);
        setUser(null);
        setIsAuthenticated(false);
        // Let Router handle redirect via ProtectedRoute
    };

    return (
        <AuthContext.Provider value={{ user, isAuthenticated, loading, login, signup, logout }}>
            {children}
        </AuthContext.Provider>
    );
};
