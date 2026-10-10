import { Link } from "react-router-dom";
import { appInfo } from "../appInfo";

export default function Home() {
  return (
    <div className="max-w-7xl mx-auto px-4 py-16">
      <h1 className="text-4xl font-bold text-slate-900">{appInfo.name}</h1>
      <p className="mt-3 text-lg text-slate-600 max-w-3xl">
        {appInfo.appType} — built with QuantBuild.
      </p>
      <div className="mt-6 flex gap-3">
        <Link to="/register" className="bg-brand-600 text-white rounded px-5 py-2 hover:bg-brand-700">
          Get started
        </Link>
        <Link to="/login" className="bg-white border border-slate-300 rounded px-5 py-2 hover:bg-slate-50">
          Log in
        </Link>
      </div>
      <h2 className="mt-14 mb-4 text-xl font-semibold text-slate-800">Features</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {appInfo.features.map((feat) => (
          <div key={feat} className="bg-white rounded-lg border border-slate-200 p-5 shadow-sm">
            <h3 className="font-semibold text-slate-800">{feat}</h3>
          </div>
        ))}
      </div>
    </div>
  );
}
