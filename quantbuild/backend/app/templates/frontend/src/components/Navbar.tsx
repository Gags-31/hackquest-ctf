import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { entityConfigs } from "../entityConfig";
import { appInfo } from "../appInfo";

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <nav className="bg-white border-b border-slate-200 sticky top-0 z-10">
      <div className="max-w-7xl mx-auto px-4 flex items-center justify-between h-14">
        <Link to="/" className="font-bold text-brand-600 text-lg">
          {appInfo.name}
        </Link>
        {user && (
          <div className="hidden md:flex gap-4">
            <Link className="text-sm text-slate-600 hover:text-brand-600" to="/dashboard">
              Dashboard
            </Link>
            {entityConfigs.map((cfg) => (
              <Link
                key={cfg.resource}
                className="text-sm text-slate-600 hover:text-brand-600"
                to={"/" + cfg.resource}
              >
                {cfg.label}
              </Link>
            ))}
            {["admin", "administrator"].includes((user.role || "").toLowerCase()) && (
              <Link className="text-sm text-slate-600 hover:text-brand-600" to="/admin">
                Admin
              </Link>
            )}
          </div>
        )}
        <div className="flex items-center gap-3">
          {user ? (
            <>
              <Link to="/profile" className="text-sm text-slate-600 hover:text-brand-600">
                {user.full_name}
              </Link>
              <button
                onClick={handleLogout}
                className="text-sm bg-slate-100 hover:bg-slate-200 rounded px-3 py-1"
              >
                Log out
              </button>
            </>
          ) : (
            <>
              <Link className="text-sm text-slate-600 hover:text-brand-600" to="/login">
                Log in
              </Link>
              <Link
                className="text-sm bg-brand-600 text-white rounded px-3 py-1 hover:bg-brand-700"
                to="/register"
              >
                Sign up
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}
