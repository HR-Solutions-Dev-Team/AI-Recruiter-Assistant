import { useNavigate } from 'react-router-dom';
import { Plus, FileText, Clock, CheckCircle2 } from 'lucide-react';
import Breadcrumbs from '../components/Breadcrumbs';

// Демо данные для списка вакансий
const DEMO_VACANCIES = [
  {
    id: 1,
    title: 'Senior Frontend Developer',
    department: 'Engineering',
    location: 'Москва',
    status: 'active',
    candidates: 12,
    createdAt: '2024-01-15',
  },
  {
    id: 2,
    title: 'Product Manager',
    department: 'Product',
    location: 'Удалённо',
    status: 'draft',
    candidates: 0,
    createdAt: '2024-01-20',
  },
];

export default function Vacancy() {
  const navigate = useNavigate();

  const getStatusBadge = (status: string) => {
    if (status === 'active') {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-1 bg-green-100 text-green-800 text-xs font-medium rounded-md">
          <CheckCircle2 size={12} strokeWidth={2} />
          Активна
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2 py-1 bg-amber-100 text-amber-800 text-xs font-medium rounded-md">
        <Clock size={12} strokeWidth={2} />
        Черновик
      </span>
    );
  };

  return (
    <div className="p-8">
      <Breadcrumbs
        items={[
          { label: 'Главная', path: '/home' },
          { label: 'Вакансии' },
        ]}
      />

      <div className="mt-6 flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Вакансии</h1>
          <p className="text-gray-500 mt-2">Управление вакансиями компании</p>
        </div>
        <button
          onClick={() => navigate('/vacancy/create')}
          className="flex items-center gap-2 px-4 py-2.5 bg-gray-900 text-white
                     rounded-xl font-medium text-sm hover:bg-gray-800 sidebar-transition"
        >
          <Plus size={18} strokeWidth={2} />
          Создать вакансию
        </button>
      </div>

      {/* Vacancies List */}
      <div className="mt-8 space-y-3">
        {DEMO_VACANCIES.map((vacancy) => (
          <div
            key={vacancy.id}
            className="bg-white border border-gray-200 rounded-xl p-4 hover:border-gray-300
                       sidebar-transition cursor-pointer"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
                  <FileText size={20} strokeWidth={2} className="text-gray-500" />
                </div>
                <div>
                  <h3 className="font-medium text-gray-900">{vacancy.title}</h3>
                  <p className="text-sm text-gray-500">
                    {vacancy.department} • {vacancy.location}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <span className="text-sm text-gray-500">
                  {vacancy.candidates} кандидатов
                </span>
                {getStatusBadge(vacancy.status)}
              </div>
            </div>
          </div>
        ))}

        {/* Empty state hint */}
        <div className="text-center py-8 text-gray-400 text-sm">
          Нажмите «Создать вакансию», чтобы добавить новую позицию
        </div>
      </div>
    </div>
  );
}
