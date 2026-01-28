import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from '../components/Sidebar';

export default function MainLayout() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  return (
    <div className="min-h-screen bg-white">
      {/* Sidebar */}
      <Sidebar
        isOpen={isSidebarOpen}
        onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
      />

      {/* Main Content Area */}
      <main
        className={`
          sidebar-transition min-h-screen bg-white
          ${isSidebarOpen ? 'ml-[260px]' : 'ml-[72px]'}
        `}
      >
        <Outlet />
      </main>
    </div>
  );
}
