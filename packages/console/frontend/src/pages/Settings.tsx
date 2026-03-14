import { useEffect, useState } from "react";

interface PositionInfo {
  role: string;
  status: string;
  agent_id: string | null;
  occupied_at: string | null;
}

interface RoleInfo {
  role: string;
  name: string;
  title: string;
}

export default function Settings() {
  const [positions, setPositions] = useState<PositionInfo[]>([]);
  const [roles, setRoles] = useState<RoleInfo[]>([]);

  useEffect(() => {
    fetchPositions();
    fetchRoles();
  }, []);

  const fetchPositions = () => {
    fetch("/api/positions/list")
      .then((res) => res.json())
      .then(setPositions)
      .catch(() => {});
  };

  const fetchRoles = () => {
    fetch("/api/roles/list")
      .then((res) => res.json())
      .then(setRoles)
      .catch(() => {});
  };

  const handlePublish = async (role: string) => {
    try {
      const res = await fetch("/api/positions/publish", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ role }),
      });
      if (res.ok) fetchPositions();
    } catch {
      // Handle error
    }
  };

  const handleOnboard = async (role: string) => {
    try {
      const res = await fetch("/api/positions/onboard", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ role }),
      });
      if (res.ok) fetchPositions();
    } catch {
      // Handle error
    }
  };

  const publishedRoles = new Set(positions.map((p) => p.role));
  const unpublishedRoles = roles.filter(
    (r) => !publishedRoles.has(r.role) && r.role !== "boss"
  );

  return (
    <div className="p-8 max-w-3xl">
      <h2 className="text-2xl font-bold text-gray-900 mb-8">设置</h2>

      {/* Positions */}
      <section className="mb-8">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">岗位管理</h3>

        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          {positions.length === 0 ? (
            <div className="p-6 text-center text-gray-500">
              暂无岗位。请先运行 <code className="text-sm bg-gray-100 px-2 py-0.5 rounded">clawopc init</code> 初始化系统。
            </div>
          ) : (
            <div className="divide-y divide-gray-50">
              {positions.map((pos) => (
                <div
                  key={pos.role}
                  className="flex items-center justify-between px-5 py-4"
                >
                  <div>
                    <p className="font-medium text-gray-900 capitalize">
                      {pos.role}
                    </p>
                    <p className="text-sm text-gray-500">
                      {pos.status === "occupied" ? (
                        <span className="text-green-600">
                          ● 在岗 {pos.agent_id && `(${pos.agent_id})`}
                        </span>
                      ) : (
                        <span className="text-gray-400">○ 空缺</span>
                      )}
                    </p>
                  </div>

                  <div>
                    {pos.status === "vacant" && (
                      <button
                        onClick={() => handleOnboard(pos.role)}
                        className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
                      >
                        入职
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* Unpublished Roles */}
      {unpublishedRoles.length > 0 && (
        <section className="mb-8">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            可发布的角色
          </h3>
          <div className="bg-white rounded-xl border border-gray-200 divide-y divide-gray-50">
            {unpublishedRoles.map((role) => (
              <div
                key={role.role}
                className="flex items-center justify-between px-5 py-4"
              >
                <div>
                  <p className="font-medium text-gray-900">{role.name}</p>
                  <p className="text-sm text-gray-500">{role.title}</p>
                </div>
                <button
                  onClick={() => handlePublish(role.role)}
                  className="px-4 py-2 bg-red-700 text-white text-sm font-medium rounded-lg hover:bg-red-800 transition-colors"
                >
                  发布岗位
                </button>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* System Info */}
      <section>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">系统信息</h3>
        <div className="bg-white rounded-xl border border-gray-200 p-5 space-y-3">
          <div className="flex justify-between text-sm">
            <span className="text-gray-500">版本</span>
            <span className="text-gray-900 font-mono">0.1.0</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-500">轮询间隔</span>
            <span className="text-gray-900">5 秒</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-500">日志保留</span>
            <span className="text-gray-900">6 个月</span>
          </div>
        </div>
      </section>
    </div>
  );
}
