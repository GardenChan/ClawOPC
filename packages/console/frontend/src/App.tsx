import { Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/Layout";
import TeamOverview from "./pages/TeamOverview";
import Decisions from "./pages/Decisions";
import CreateTask from "./pages/CreateTask";
import TaskHistory from "./pages/TaskHistory";
import Settings from "./pages/Settings";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Navigate to="/team" replace />} />
        <Route path="team" element={<TeamOverview />} />
        <Route path="decisions" element={<Decisions />} />
        <Route path="create-task" element={<CreateTask />} />
        <Route path="history" element={<TaskHistory />} />
        <Route path="settings" element={<Settings />} />
      </Route>
    </Routes>
  );
}
