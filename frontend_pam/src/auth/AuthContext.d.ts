// AuthContext.d.ts
declare module './AuthContext' {
    import { ReactNode } from 'react';
    
    // Named export
    export const AuthProvider: (props: { children?: ReactNode }) => JSX.Element;
    
    // Default export
    const AuthContext: any;
    export default AuthContext;
  }
  
  // Force TS to treat this as a module
  export {};
  