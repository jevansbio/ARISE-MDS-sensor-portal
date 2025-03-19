import { FormEvent, useContext } from 'react';
import AuthContext from '../../auth/AuthContext';

type AuthContextType = {
  loginUser: (e: FormEvent<HTMLFormElement>) => void;
};

function LoginPage() {
  const { loginUser } = useContext(AuthContext) as AuthContextType;

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