import { useState } from "react";
import UploadResumeIcon from "../icons/UploadResumeIcon";
import UploadVacancyIcon from "../icons/UploadVacancyIcon";
import "../../styles/sidebar.css";

type SidebarItem = {
  id: "vacancy" | "resume";
  label: string;
  Icon: typeof UploadVacancyIcon;
};

const items: SidebarItem[] = [
  { id: "vacancy", label: "Загрузка вакансии", Icon: UploadVacancyIcon },
  { id: "resume", label: "Загрузка резюме", Icon: UploadResumeIcon },
];

export default function Sidebar() {
  const [activeId, setActiveId] = useState<SidebarItem["id"]>("vacancy");

  return (
    <aside className="sidebar">
      <div className="sidebar__logo" aria-label="HR">
        HR
      </div>
      <nav className="sidebar__nav" aria-label="Основные разделы">
        {items.map(({ id, label, Icon }) => {
          const isActive = id === activeId;
          return (
            <button
              key={id}
              type="button"
              className="sidebar__item"
              data-active={isActive}
              aria-pressed={isActive}
              onClick={() => setActiveId(id)}
            >
              <span className="sidebar__indicator" aria-hidden="true" />
              <Icon className="sidebar__icon" />
              <span className="sidebar__label">{label}</span>
            </button>
          );
        })}
      </nav>
    </aside>
  );
}
