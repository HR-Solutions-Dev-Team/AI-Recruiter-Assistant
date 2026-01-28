import { MapPin, Building2, Clock, Briefcase, DollarSign, CheckCircle2 } from 'lucide-react';
import type { VacancyData } from '../../pages/VacancyCreate';

interface PreviewStepProps {
  vacancyData: VacancyData;
  onSave: () => void;
}

export default function PreviewStep({ vacancyData, onSave }: PreviewStepProps) {
  const formatSalary = () => {
    const { salaryFrom, salaryTo, currency } = vacancyData;
    if (!salaryFrom && !salaryTo) return 'Не указана';

    const formatNum = (n: string) => Number(n).toLocaleString('ru-RU');

    if (salaryFrom && salaryTo) {
      return `${formatNum(salaryFrom)} — ${formatNum(salaryTo)} ${currency}`;
    }
    if (salaryFrom) return `от ${formatNum(salaryFrom)} ${currency}`;
    return `до ${formatNum(salaryTo)} ${currency}`;
  };

  const InfoBadge = ({ icon: Icon, label, value }: { icon: any; label: string; value: string }) => (
    <div className="flex items-center gap-2 px-3 py-2 bg-gray-50 rounded-lg">
      <Icon size={16} strokeWidth={2} className="text-gray-500" />
      <span className="text-sm text-gray-600">{label}:</span>
      <span className="text-sm font-medium text-gray-900">{value || 'Не указано'}</span>
    </div>
  );

  const ListSection = ({ title, items }: { title: string; items: string[] }) => {
    if (items.length === 0) return null;
    return (
      <div>
        <h3 className="text-sm font-semibold text-gray-900 mb-3">{title}</h3>
        <ul className="space-y-2">
          {items.map((item, index) => (
            <li key={index} className="flex items-start gap-2 text-sm text-gray-700">
              <CheckCircle2 size={16} strokeWidth={2} className="text-gray-400 mt-0.5 flex-shrink-0" />
              {item}
            </li>
          ))}
        </ul>
      </div>
    );
  };

  return (
    <div className="max-w-3xl mx-auto">
      {/* Info */}
      <p className="text-sm text-gray-500 mb-6">
        Проверьте, как будет выглядеть вакансия. Если всё верно, нажмите «Сохранить вакансию».
      </p>

      {/* Preview Card */}
      <div className="bg-white border border-gray-200 rounded-2xl overflow-hidden">
        {/* Header */}
        <div className="p-6 border-b border-gray-100">
          <h1 className="text-xl font-semibold text-gray-900">
            {vacancyData.title || 'Название не указано'}
          </h1>

          {/* Meta Info */}
          <div className="flex flex-wrap gap-2 mt-4">
            <InfoBadge icon={Building2} label="Отдел" value={vacancyData.department} />
            <InfoBadge icon={MapPin} label="Локация" value={vacancyData.location} />
            <InfoBadge icon={Clock} label="Формат" value={vacancyData.employmentType} />
            <InfoBadge icon={Briefcase} label="Уровень" value={vacancyData.experienceLevel} />
            <InfoBadge icon={DollarSign} label="Зарплата" value={formatSalary()} />
          </div>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Description */}
          {vacancyData.description && (
            <div>
              <h3 className="text-sm font-semibold text-gray-900 mb-2">О позиции</h3>
              <p className="text-sm text-gray-700 leading-relaxed">{vacancyData.description}</p>
            </div>
          )}

          {/* Responsibilities */}
          <ListSection title="Обязанности" items={vacancyData.responsibilities} />

          {/* Requirements */}
          <ListSection title="Требования" items={vacancyData.requirements} />

          {/* Nice to Have */}
          <ListSection title="Будет плюсом" items={vacancyData.niceToHave} />

          {/* Benefits */}
          <ListSection title="Что мы предлагаем" items={vacancyData.benefits} />
        </div>

        {/* Footer */}
        <div className="px-6 py-4 bg-gray-50 border-t border-gray-100">
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-500">
              Вакансия будет опубликована как черновик
            </span>
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center px-2 py-1 bg-amber-100 text-amber-800 text-xs font-medium rounded-md">
                Черновик
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="mt-8 flex justify-end gap-3">
        <button
          onClick={onSave}
          className="flex items-center gap-2 px-6 py-3 bg-gray-900 text-white
                     rounded-xl font-medium text-sm hover:bg-gray-800 sidebar-transition"
        >
          <CheckCircle2 size={18} strokeWidth={2} />
          Сохранить вакансию
        </button>
      </div>
    </div>
  );
}
