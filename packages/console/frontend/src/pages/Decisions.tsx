import { useEffect, useState } from "react";

interface PendingDecision {
  task: {
    meta: {
      id: string;
      title: string;
      pipeline: Array<{ role: string; instruction: string }>;
      pipeline_cursor: number;
      current_role: string;
    };
    body: {
      description: string;
      acceptance_criteria: string;
    };
  };
  role: string;
  can_forward: boolean;
  next_role: string | null;
  outputs: Array<{
    step: number;
    role: string;
    file: string;
    content: string;
  }>;
}

export default function Decisions() {
  const [decisions, setDecisions] = useState<PendingDecision[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDecisions = async () => {
      try {
        const res = await fetch("/api/decisions/pending");
        if (res.ok) {
          setDecisions(await res.json());
        }
      } catch {
        // API not available
      } finally {
        setLoading(false);
      }
    };

    fetchDecisions();
    const interval = setInterval(fetchDecisions, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleAction = async (
    action: "forward" | "rework" | "complete",
    taskId: string,
    note?: string,
    comment?: string,
  ) => {
    const body: Record<string, string> = { task_id: taskId };
    if (comment) body.comment = comment;
    if (note) body.note = note;

    try {
      const res = await fetch(`/api/decisions/${action}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      if (res.ok) {
        setDecisions((prev) => prev.filter((d) => d.task.meta.id !== taskId));
      }
    } catch {
      // Handle error
    }
  };

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <h2 className="text-2xl font-bold text-gray-900">待决策</h2>
        <span className="text-sm text-gray-500">
          {decisions.length} 个待处理
        </span>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64 text-gray-500">
          加载中...
        </div>
      ) : decisions.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-64 text-gray-500">
          <p className="text-lg mb-2">🎉 没有待决策的任务</p>
          <p className="text-sm">所有任务都在正常进行中</p>
        </div>
      ) : (
        <div className="space-y-6">
          {decisions.map((d) => (
            <div
              key={d.task.meta.id}
              className="bg-white rounded-xl border border-red-100 p-6"
            >
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">
                    {d.task.meta.title}
                  </h3>
                  <p className="text-sm text-gray-500">
                    {d.task.meta.id} · {d.role} 已完成
                  </p>
                </div>
                <span className="px-3 py-1 bg-yellow-50 text-yellow-700 text-xs font-medium rounded-full">
                  等待决策
                </span>
              </div>

              {/* Pipeline progress */}
              <div className="flex items-center gap-2 mb-4 text-sm text-gray-500">
                {d.task.meta.pipeline.map((step, i) => (
                  <span key={i} className="flex items-center gap-1">
                    {i > 0 && <span className="text-gray-300">→</span>}
                    <span
                      className={
                        i <= d.task.meta.pipeline_cursor
                          ? "text-green-600 font-medium"
                          : "text-gray-400"
                      }
                    >
                      {step.role}
                    </span>
                  </span>
                ))}
              </div>

              {/* Latest output */}
              {d.outputs.length > 0 && (
                <div className="bg-red-50/50 rounded-lg p-4 mb-4">
                  <h4 className="text-sm font-medium text-gray-700 mb-2">
                    最新产出
                  </h4>
                  <pre className="text-sm text-gray-600 whitespace-pre-wrap max-h-48 overflow-auto">
                    {d.outputs[d.outputs.length - 1].content.slice(0, 500)}
                    {d.outputs[d.outputs.length - 1].content.length > 500 &&
                      "..."}
                  </pre>
                </div>
              )}

              {/* Actions */}
              <div className="flex items-center gap-3">
                {d.can_forward && d.next_role && (
                  <button
                    onClick={() =>
                      handleAction("forward", d.task.meta.id)
                    }
                    className="px-4 py-2 bg-red-700 text-white text-sm font-medium rounded-lg hover:bg-red-800 transition-colors"
                  >
                    Forward → {d.next_role}
                  </button>
                )}
                <button
                  onClick={() => {
                    const note = prompt("请输入 Rework 说明：");
                    if (note) {
                      handleAction("rework", d.task.meta.id, note);
                    }
                  }}
                  className="px-4 py-2 bg-yellow-50 text-yellow-700 text-sm font-medium rounded-lg hover:bg-yellow-100 transition-colors"
                >
                  Rework
                </button>
                <button
                  onClick={() => handleAction("complete", d.task.meta.id)}
                  className="px-4 py-2 bg-green-50 text-green-700 text-sm font-medium rounded-lg hover:bg-green-100 transition-colors"
                >
                  Complete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
