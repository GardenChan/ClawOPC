import { useEffect, useState } from "react";

interface TaskSummary {
  id: string;
  title: string;
  status: string;
  current_role: string;
  pipeline_cursor: number;
  pipeline_total: number;
  created_at: string;
  completed_at: string | null;
  location: string;
}

const statusConfig: Record<string, { label: string; color: string }> = {
  pending: { label: "等待处理", color: "bg-gray-100 text-gray-700" },
  processing: { label: "进行中", color: "bg-red-50 text-red-700" },
  awaiting_boss: { label: "待决策", color: "bg-yellow-50 text-yellow-700" },
  complete: { label: "已完成", color: "bg-green-50 text-green-700" },
};

export default function TaskHistory() {
  const [tasks, setTasks] = useState<TaskSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/tasks/list")
      .then((res) => res.json())
      .then(setTasks)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="p-8">
      <h2 className="text-2xl font-bold text-gray-900 mb-8">任务历史</h2>

      {loading ? (
        <div className="flex items-center justify-center h-64 text-gray-500">
          加载中...
        </div>
      ) : tasks.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-64 text-gray-500">
          <p className="text-lg mb-2">暂无任务</p>
          <p className="text-sm">去「创建任务」页面创建第一个任务吧</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-100">
                <th className="px-5 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  任务 ID
                </th>
                <th className="px-5 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  标题
                </th>
                <th className="px-5 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  状态
                </th>
                <th className="px-5 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  当前角色
                </th>
                <th className="px-5 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  进度
                </th>
                <th className="px-5 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  创建时间
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {tasks.map((task) => {
                const status = statusConfig[task.status] || statusConfig.pending;
                return (
                  <tr
                    key={task.id}
                    className="hover:bg-gray-50 cursor-pointer transition-colors"
                  >
                    <td className="px-5 py-3 text-sm text-gray-500 font-mono">
                      {task.id}
                    </td>
                    <td className="px-5 py-3 text-sm font-medium text-gray-900">
                      {task.title}
                    </td>
                    <td className="px-5 py-3">
                      <span
                        className={`px-2.5 py-1 text-xs font-medium rounded-full ${status.color}`}
                      >
                        {status.label}
                      </span>
                    </td>
                    <td className="px-5 py-3 text-sm text-gray-600">
                      {task.current_role}
                    </td>
                    <td className="px-5 py-3 text-sm text-gray-500">
                      {task.pipeline_cursor + 1} / {task.pipeline_total}
                    </td>
                    <td className="px-5 py-3 text-sm text-gray-500">
                      {new Date(task.created_at).toLocaleString("zh-CN")}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
