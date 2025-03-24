import { FormEvent, useContext, useEffect } from 'react';
import { useNavigate } from "@tanstack/react-router";
import AuthContext from '../../auth/AuthContext';

type AuthContextType = {
  loginUser: (e: FormEvent<HTMLFormElement>) => void;
  user: any;
};

function LoginPage() {
  const { loginUser, user } = useContext(AuthContext) as AuthContextType;
  const navigate = useNavigate();

  // Redirect if user is already logged in
  useEffect(() => {
    if (user) {
      navigate({ to: "/" });
    }
  }, [user, navigate]);

  return (
    <div>
      <form onSubmit={loginUser}>
        <input type="text" name="username" placeholder="Enter username" />
        <input type="password" name="password" placeholder="Enter password" />
        <input type="submit" />
      </form>
    </div>
  );
}

export default LoginPage;