import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, FileText, Clock, CheckCircle2, Loader2, AlertCircle } from 'lucide-react';
import Breadcrumbs from '../components/Breadcrumbs';
import { getVacancies, type VacancyListItem } from '../api/vacancy';

export default function Vacancy() {
  const navigate = useNavigate();
  const [vacancies, setVacancies] = useState<VacancyListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadVacancies();
  }, []);

  const loadVacancies = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await getVacancies(0, 100);
      setVacancies(response.items);
    } catch (err) {
      console.error('Failed to load vacancies:', err);
      setError('Не удалось загрузить вакансии');
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    if (status === 'active') {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-1 bg-green-100 text-green-800 text-xs font-medium rounded-md">
          <CheckCircle2 size={12} strokeWidth={2} />
          Активна
        </span>
      );
    }
    if (status === 'closed') {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-1 bg-gray-100 text-gray-600 text-xs font-medium rounded-md">
          Закрыта
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

  const formatSalary = (vacancy: VacancyListItem) => {
    if (!vacancy.salary_min && !vacancy.salary_max) return null;
    
    const currency = vacancy.salary_currency || 'RUB';
    const currencySymbol = currency === 'RUB' ? '₽' : currency === 'USD' ? '$' : currency === 'EUR' ? '€' : currency;
    
    if (vacancy.salary_min && vacancy.salary_max) {
      return `${vacancy.salary_min.toLocaleString()} – ${vacancy.salary_max.toLocaleString()} ${currencySymbol}`;
    }
    if (vacancy.salary_min) {
      return `от ${vacancy.salary_min.toLocaleString()} ${currencySymbol}`;
    }
    if (vacancy.salary_max) {
      return `до ${vacancy.salary_max.toLocaleString()} ${currencySymbol}`;
    }
    return null;
  };

  const formatDate = (dateStr: string) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString('ru-RU', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    });
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

      {/* Loading state */}
      {isLoading && (
        <div className="mt-8 flex items-center justify-center py-12">
          <Loader2 size={32} className="animate-spin text-gray-400" />
        </div>
      )}

      {/* Error state */}
      {error && !isLoading && (
        <div className="mt-8 bg-red-50 border border-red-200 rounded-xl p-4 flex items-center gap-3">
          <AlertCircle size={20} className="text-red-500" />
          <span className="text-red-700">{error}</span>
          <button
            onClick={loadVacancies}
            className="ml-auto text-sm font-medium text-red-600 hover:text-red-800"
          >
            Повторить
          </button>
        </div>
      )}

      {/* Vacancies List */}
      {!isLoading && !error && (
        <div className="mt-8 space-y-3">
          {vacancies.map((vacancy) => (
            <div
              key={vacancy.id}
              onClick={() => navigate(`/vacancy/${vacancy.id}`)}
              className="bg-white border border-gray-200 rounded-xl p-4 hover:border-gray-300
                         sidebar-transition cursor-pointer"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
                    <FileText size={20} strokeWidth={2} className="text-gray-500" />
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900">{vacancy.job_title}</h3>
                    <p className="text-sm text-gray-500">
                      {vacancy.company_name || 'Компания не указана'}
                      {vacancy.location_city && ` • ${vacancy.location_city}`}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  {formatSalary(vacancy) && (
                    <span className="text-sm text-gray-600 font-medium">
                      {formatSalary(vacancy)}
                    </span>
                  )}
                  <span className="text-sm text-gray-400">
                    {formatDate(vacancy.created_at)}
                  </span>
                  {getStatusBadge(vacancy.status)}
                </div>
              </div>
            </div>
          ))}

          {/* Empty state */}
          {vacancies.length === 0 && (
            <div className="text-center py-12">
              <FileText size={48} className="mx-auto text-gray-300 mb-4" />
              <p className="text-gray-500">Нет вакансий</p>
              <p className="text-gray-400 text-sm mt-1">
                Нажмите «Создать вакансию», чтобы добавить первую позицию
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
