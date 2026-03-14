import { useEffect, useState } from "react";

interface AgentCard {
  role: string;
  name: string;
  title: string;
  state: string;
  position_status: string;
  current_task_id: string | null;
  has_avatar: boolean;
  latest_log: {
    timestamp: string;
    event: string;
    detail: string;
  } | null;
}

const stateConfig: Record<string, { icon: string; label: string; color: string }> = {
  working: { icon: "🔵", label: "工作中", color: "text-blue-600" },
  idle: { icon: "⚪", label: "待机中", color: "text-gray-500" },
  awaiting_decision: { icon: "🟡", label: "等待决策", color: "text-yellow-600" },
  offline: { icon: "🔴", label: "离线", color: "text-red-500" },
};

export default function TeamOverview() {
  const [agents, setAgents] = useState<AgentCard[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchTeam = async () => {
      try {
        const res = await fetch("/api/team/overview");
        if (res.ok) {
          setAgents(await res.json());
        }
      } catch {
        // API not available yet
      } finally {
        setLoading(false);
      }
    };

    fetchTeam();
    const interval = setInterval(fetchTeam, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <h2 className="text-2xl font-bold text-gray-900">团队总览</h2>
        <span className="text-sm text-gray-500">每 5 秒刷新</span>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64 text-gray-500">
          加载中...
        </div>
      ) : agents.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-64 text-gray-500">
          <p className="text-lg mb-2">暂无团队成员</p>
          <p className="text-sm">在「设置」中发布岗位并入职虚拟员工</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
          {agents.map((agent) => {
            const state = stateConfig[agent.state] || stateConfig.offline;
            return (
              <div
                key={agent.role}
                className="bg-white rounded-xl border border-red-100 p-5 hover:shadow-md hover:shadow-red-100/50 transition-shadow cursor-pointer"
              >
                {/* Avatar placeholder */}
                <div className="w-16 h-16 rounded-full bg-red-50 text-red-700 flex items-center justify-center text-2xl mb-4 font-bold">
                  {agent.name.charAt(0).toUpperCase()}
                </div>

                <h3 className="font-semibold text-gray-900">{agent.name}</h3>
                <p className="text-sm text-gray-500 mb-3">{agent.title}</p>

                <div className={`flex items-center gap-2 text-sm ${state.color}`}>
                  <span>{state.icon}</span>
                  <span>{state.label}</span>
                </div>

                {agent.current_task_id && (
                  <p className="text-xs text-gray-400 mt-2">
                    {agent.current_task_id}
                  </p>
                )}

                {agent.latest_log && (
                  <p className="text-xs text-gray-400 mt-1 truncate">
                    {agent.latest_log.detail}
                  </p>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
