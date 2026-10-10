import { useAuth } from "../auth/AuthContext";

export default function Profile() {
  const { user } = useAuth();
  if (!user) return null;
  return (
    <div className="max-w-xl mx-auto mt-12 bg-white border border-slate-200 rounded-lg p-8 shadow-sm">
      <h1 className="text-2xl font-bold text-slate-900 mb-6">Profile</h1>
      <dl className="space-y-3 text-sm">
        <div><dt className="text-slate-500">Name</dt><dd className="font-medium">{user.full_name}</dd></div>
        <div><dt className="text-slate-500">Email</dt><dd className="font-medium">{user.email}</dd></div>
        <div><dt className="text-slate-500">Role</dt><dd className="font-medium capitalize">{user.role}</dd></div>
      </dl>
    </div>
  );
}
