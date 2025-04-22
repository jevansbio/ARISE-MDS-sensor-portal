// AuthContext.d.ts
declare module './AuthContext' {
    import { ReactNode } from 'react';
    
    interface AuthContextType {
        authTokens: {
            access: string;
            refresh: string;
        } | null;
        user: {
            username: string;
            email: string;
            // Add other user properties as needed
        } | null;
        loginUser: (e: FormEvent<HTMLFormElement>) => Promise<void>;
        logoutUser: () => void;
        refreshToken: () => Promise<void>;
    }
    
    // Named export
    export const AuthProvider: (props: { children?: ReactNode }) => JSX.Element;
    
    // Default export
    const AuthContext: React.Context<AuthContextType>;
    export default AuthContext;
}
  
// Force TS to treat this as a module
export {};
  