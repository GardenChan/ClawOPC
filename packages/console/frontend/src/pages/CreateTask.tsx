import { useState, useEffect } from "react";
import { PlusCircle, Trash2 } from "lucide-react";

interface PipelineStep {
  role: string;
  instruction: string;
}

interface RoleInfo {
  role: string;
  name: string;
  title: string;
}

export default function CreateTask() {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [background, setBackground] = useState("");
  const [criteria, setCriteria] = useState("");
  const [pipeline, setPipeline] = useState<PipelineStep[]>([
    { role: "", instruction: "" },
  ]);
  const [roles, setRoles] = useState<RoleInfo[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/roles/list")
      .then((res) => res.json())
      .then(setRoles)
      .catch(() => {});
  }, []);

  const addStep = () => {
    setPipeline([...pipeline, { role: "", instruction: "" }]);
  };

  const removeStep = (index: number) => {
    if (pipeline.length <= 1) return;
    setPipeline(pipeline.filter((_, i) => i !== index));
  };

  const updateStep = (index: number, field: keyof PipelineStep, value: string) => {
    const updated = [...pipeline];
    updated[index] = { ...updated[index], [field]: value };
    setPipeline(updated);
  };

  const handleSubmit = async () => {
    if (!title.trim() || !description.trim()) return;
    if (pipeline.some((s) => !s.role || !s.instruction.trim())) return;

    setSubmitting(true);
    setSuccess(null);

    try {
      const res = await fetch("/api/tasks/create", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title,
          description,
          background,
          acceptance_criteria: criteria,
          pipeline,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setSuccess(`✅ 任务已创建: ${data.id} → ${data.current_role}`);
        // Reset form
        setTitle("");
        setDescription("");
        setBackground("");
        setCriteria("");
        setPipeline([{ role: "", instruction: "" }]);
      }
    } catch {
      // Handle error
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="p-8 max-w-3xl">
      <h2 className="text-2xl font-bold text-gray-900 mb-8">创建任务</h2>

      {success && (
        <div className="bg-green-50 text-green-700 p-4 rounded-lg mb-6">
          {success}
        </div>
      )}

      <div className="space-y-6">
        {/* Title */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            任务标题 *
          </label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent"
            placeholder="例如：实现用户登录功能"
          />
        </div>

        {/* Description */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            任务描述 *
          </label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={4}
            className="w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent"
            placeholder="详细描述任务目标..."
          />
        </div>

        {/* Background */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            背景信息
          </label>
          <textarea
            value={background}
            onChange={(e) => setBackground(e.target.value)}
            rows={3}
            className="w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent"
            placeholder="技术栈、约束条件等..."
          />
        </div>

        {/* Acceptance Criteria */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            验收标准
          </label>
          <textarea
            value={criteria}
            onChange={(e) => setCriteria(e.target.value)}
            rows={3}
            className="w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent"
            placeholder="- [ ] 验收项 1&#10;- [ ] 验收项 2"
          />
        </div>

        {/* Pipeline */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            Pipeline
          </label>
          <div className="space-y-4">
            {pipeline.map((step, index) => (
              <div key={index} className="flex gap-3 items-start">
                <span className="text-sm text-gray-400 mt-3 w-8">
                  #{index + 1}
                </span>
                <div className="flex-1 space-y-2">
                  <select
                    value={step.role}
                    onChange={(e) => updateStep(index, "role", e.target.value)}
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-red-500"
                  >
                    <option value="">选择角色...</option>
                    {roles
                      .filter((r) => r.role !== "boss")
                      .map((r) => (
                        <option key={r.role} value={r.role}>
                          {r.name} ({r.title})
                        </option>
                      ))}
                  </select>
                  <textarea
                    value={step.instruction}
                    onChange={(e) =>
                      updateStep(index, "instruction", e.target.value)
                    }
                    rows={2}
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-red-500"
                    placeholder="给该角色的具体指令..."
                  />
                </div>
                {pipeline.length > 1 && (
                  <button
                    onClick={() => removeStep(index)}
                    className="mt-3 text-gray-400 hover:text-red-500 transition-colors"
                  >
                    <Trash2 size={16} />
                  </button>
                )}
              </div>
            ))}
          </div>

          <button
            onClick={addStep}
            className="mt-3 flex items-center gap-2 text-sm text-red-600 hover:text-red-700"
          >
            <PlusCircle size={16} />
            添加步骤
          </button>
        </div>

        {/* Submit */}
        <div className="flex gap-3 pt-4">
          <button
            onClick={handleSubmit}
            disabled={submitting}
            className="px-6 py-2.5 bg-red-700 text-white text-sm font-medium rounded-lg hover:bg-red-800 transition-colors disabled:opacity-50"
          >
            {submitting ? "创建中..." : "创建任务"}
          </button>
        </div>
      </div>
    </div>
  );
}
