import { Home, Briefcase, ChevronLeft, ChevronRight } from 'lucide-react';
import { NavLink } from 'react-router-dom';

interface SidebarProps {
  isOpen: boolean;
  onToggle: () => void;
}

interface MenuSection {
  title: string;
  items: {
    path: string;
    label: string;
    icon: typeof Home;
  }[];
}

export default function Sidebar({ isOpen, onToggle }: SidebarProps) {
  const menuSections: MenuSection[] = [
    {
      title: 'ОСНОВНЫЕ',
      items: [
        { path: '/home', label: 'Главная', icon: Home },
      ],
    },
    {
      title: 'РАБОТОДАТЕЛЬ',
      items: [
        { path: '/vacancy', label: 'Вакансии', icon: Briefcase },
      ],
    },
  ];

  return (
    <aside
      className={`
        fixed left-0 top-0 h-full bg-gray-50 border-r border-gray-200
        sidebar-transition z-20 flex flex-col
        ${isOpen ? 'w-[260px]' : 'w-[72px]'}
      `}
    >
      {/* Toggle Button - круглая кнопка на границе */}
      <button
        onClick={onToggle}
        className="absolute -right-4 top-6 w-8 h-8 bg-white rounded-full shadow-md border border-gray-200 flex items-center justify-center hover:bg-gray-50 sidebar-transition z-30"
        aria-label={isOpen ? 'Свернуть меню' : 'Развернуть меню'}
      >
        {isOpen ? (
          <ChevronLeft size={16} className="text-gray-600" />
        ) : (
          <ChevronRight size={16} className="text-gray-600" />
        )}
      </button>

      {/* Logo / Brand */}
      <div className={`h-16 flex items-center border-b border-gray-200 ${isOpen ? 'px-6' : 'px-4 justify-center'}`}>
        {isOpen ? (
          <h1 className="text-lg font-bold text-gray-900 fade-transition">CRM HR AI</h1>
        ) : (
          <div className="tooltip-container">
            <span className="text-lg font-bold text-gray-900">C</span>
            <span className="tooltip">CRM HR AI</span>
          </div>
        )}
      </div>

      {/* Navigation Menu */}
      <nav className="flex-1 py-6 overflow-y-auto">
        {menuSections.map((section, sectionIndex) => (
          <div key={section.title} className={sectionIndex > 0 ? 'mt-6' : ''}>
            {/* Section Title / Divider */}
            {isOpen ? (
              <div className="px-6 mb-3">
                <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                  {section.title}
                </span>
              </div>
            ) : (
              <div className="mx-4 mb-3 border-t border-gray-200" />
            )}

            {/* Menu Items */}
            <ul className="space-y-1 px-3">
              {section.items.map((item) => (
                <li key={item.path}>
                  {isOpen ? (
                    <NavLink
                      to={item.path}
                      className={({ isActive }) =>
                        `flex items-center gap-3 px-4 py-3 rounded-xl sidebar-transition
                        ${isActive
                          ? 'bg-gray-200 text-gray-900'
                          : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                        }`
                      }
                    >
                      <item.icon size={20} strokeWidth={2} />
                      <span className="font-medium text-sm">{item.label}</span>
                    </NavLink>
                  ) : (
                    <div className="tooltip-container">
                      <NavLink
                        to={item.path}
                        className={({ isActive }) =>
                          `flex items-center justify-center p-3 rounded-xl sidebar-transition
                          ${isActive
                            ? 'bg-gray-200 text-gray-900'
                            : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                          }`
                        }
                      >
                        <item.icon size={20} strokeWidth={2} />
                      </NavLink>
                      <span className="tooltip">{item.label}</span>
                    </div>
                  )}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </nav>
    </aside>
  );
}
