import { NavLink, Outlet } from "react-router-dom";
import { Users, AlertCircle, PlusCircle, Clock, SettingsIcon } from "lucide-react";

const navItems = [
  { to: "/team", label: "团队", icon: Users },
  { to: "/decisions", label: "待决策", icon: AlertCircle },
  { to: "/create-task", label: "创建任务", icon: PlusCircle },
  { to: "/history", label: "历史", icon: Clock },
  { to: "/settings", label: "设置", icon: SettingsIcon },
];

export default function Layout() {
  return (
    <div className="flex h-screen bg-red-50/40">
      {/* Sidebar */}
      <aside className="w-56 bg-white border-r border-red-100 flex flex-col">
        <div className="p-4 border-b border-red-100 flex items-center gap-3">
          <img src="/ClawOPC-logo.jpg" alt="ClawOPC" className="w-10 h-10 rounded-lg object-cover" />
          <h1 className="text-lg font-bold text-red-700 tracking-tight">ClawOPC</h1>
        </div>

        <nav className="flex-1 p-3 space-y-1">
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-red-700 text-white shadow-sm"
                    : "text-gray-600 hover:bg-red-50 hover:text-red-700"
                }`
              }
            >
              <Icon size={18} />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="p-4 border-t border-red-100">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-red-700 flex items-center justify-center text-white text-xs font-bold">
              B
            </div>
            <div>
              <p className="text-sm font-medium text-gray-900">Boss</p>
              <p className="text-xs text-red-400">在线</p>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}
