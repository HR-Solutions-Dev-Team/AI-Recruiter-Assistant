import { MapPin, Building2, Clock, Briefcase, DollarSign, CheckCircle2, Users, GraduationCap, Languages, Loader2, AlertCircle } from 'lucide-react';
import type { VacancyInput } from '../../types/vacancy';

interface PreviewStepProps {
  vacancyData: VacancyInput;
  onSave: () => void;
  isSaving?: boolean;
  saveError?: string | null;
}

export default function PreviewStep({ vacancyData, onSave, isSaving = false, saveError = null }: PreviewStepProps) {
  const formatSalary = () => {
    const salary = vacancyData.workConditions?.salary;
    if (!salary?.amountMin && !salary?.amountMax) return 'Не указана';

    const formatNum = (n: number) => n.toLocaleString('ru-RU');
    const currency = salary.currency || 'RUB';

    if (salary.amountMin && salary.amountMax) {
      return `${formatNum(salary.amountMin)} — ${formatNum(salary.amountMax)} ${currency}`;
    }
    if (salary.amountMin) return `от ${formatNum(salary.amountMin)} ${currency}`;
    return `до ${formatNum(salary.amountMax!)} ${currency}`;
  };

  const InfoBadge = ({ icon: Icon, label, value }: { icon: any; label: string; value: string }) => (
    <div className="flex items-center gap-2 px-3 py-2 bg-gray-50 rounded-lg">
      <Icon size={16} strokeWidth={2} className="text-gray-500" />
      <span className="text-sm text-gray-600">{label}:</span>
      <span className="text-sm font-medium text-gray-900">{value || 'Не указано'}</span>
    </div>
  );

  const ListSection = ({ title, items }: { title: string; items: string[] }) => {
    if (!items || items.length === 0) return null;
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

  // Извлечение данных из VacancyInput
  const title = vacancyData.core?.jobTitle || 'Название не указано';
  const department = vacancyData.classification?.businessFunction?.name || '';
  const location = vacancyData.workConditions?.location?.city
    ? `${vacancyData.workConditions.location.city}${vacancyData.workConditions.location.country ? `, ${vacancyData.workConditions.location.country}` : ''}`
    : '';
  const employmentType = vacancyData.workConditions?.employmentType?.name || '';
  const experienceLevel = vacancyData.core?.careerLevel?.code || '';
  const remoteType = vacancyData.workConditions?.location?.remote || '';

  const description = vacancyData.responsibilities?.scope || '';
  const responsibilities = vacancyData.responsibilities?.zones || [];

  const requiredSkills = vacancyData.requirements?.skills?.filter(s => s.isRequired).map(s => s.name) || [];
  const niceToHaveSkills = vacancyData.requirements?.skills?.filter(s => !s.isRequired).map(s => s.name) || [];

  // Сфера деятельности компании
  const activitySphere = vacancyData.company?.activitySphere;
  const activitySphereText = [
    activitySphere?.sphere?.name,
    activitySphere?.subSphere?.name,
    activitySphere?.specialization?.name
  ].filter(Boolean).join(' → ');

  const languages = vacancyData.requirements?.languages || [];
  const education = vacancyData.requirements?.education;

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
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-xl font-semibold text-gray-900">{title}</h1>
              {vacancyData.company?.name && (
                <p className="text-sm text-gray-500 mt-1">{vacancyData.company.name}</p>
              )}
            </div>
            {experienceLevel && (
              <span className="px-3 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded-full uppercase">
                {experienceLevel}
              </span>
            )}
          </div>

          {/* Meta Info */}
          <div className="flex flex-wrap gap-2 mt-4">
            {department && <InfoBadge icon={Building2} label="Функция" value={department} />}
            {location && <InfoBadge icon={MapPin} label="Локация" value={location} />}
            {remoteType && <InfoBadge icon={Clock} label="Формат" value={remoteType} />}
            {employmentType && <InfoBadge icon={Briefcase} label="Занятость" value={employmentType} />}
            <InfoBadge icon={DollarSign} label="Зарплата" value={formatSalary()} />
          </div>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Description */}
          {description && (
            <div>
              <h3 className="text-sm font-semibold text-gray-900 mb-2">О позиции</h3>
              <p className="text-sm text-gray-700 leading-relaxed">{description}</p>
            </div>
          )}

          {/* Responsibilities */}
          <ListSection title="Обязанности" items={responsibilities} />

          {/* Requirements */}
          <ListSection title="Требования (обязательные)" items={requiredSkills} />

          {/* Nice to Have */}
          <ListSection title="Будет плюсом" items={niceToHaveSkills} />

          {/* Languages */}
          {languages.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <Languages size={16} />
                Языки
              </h3>
              <div className="flex flex-wrap gap-2">
                {languages.map((lang, idx) => (
                  <span key={idx} className="px-3 py-1.5 bg-gray-100 rounded-lg text-sm">
                    {lang.name}
                    {lang.proficiency && <span className="text-gray-500 ml-1">({lang.proficiency})</span>}
                    {lang.isRequired && <span className="text-red-500 ml-1">*</span>}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Education */}
          {education?.level && (
            <div>
              <h3 className="text-sm font-semibold text-gray-900 mb-2 flex items-center gap-2">
                <GraduationCap size={16} />
                Образование
              </h3>
              <p className="text-sm text-gray-700">
                {education.level}
                {education.fields && education.fields.length > 0 && (
                  <span className="text-gray-500"> — {education.fields.join(', ')}</span>
                )}
              </p>
            </div>
          )}

          {/* Activity Sphere */}
          {activitySphereText && (
            <div>
              <h3 className="text-sm font-semibold text-gray-900 mb-2 flex items-center gap-2">
                <Building2 size={16} />
                Сфера деятельности
              </h3>
              <p className="text-sm text-gray-700">{activitySphereText}</p>
            </div>
          )}

          {/* Team Info */}
          {vacancyData.orgStructure && (
            <div>
              <h3 className="text-sm font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <Users size={16} />
                Команда
              </h3>
              <div className="space-y-1 text-sm text-gray-700">
                {vacancyData.orgStructure.reportsTo && (
                  <p>Подчинение: <span className="font-medium">{vacancyData.orgStructure.reportsTo}</span></p>
                )}
                {vacancyData.orgStructure.orgUnit && (
                  <p>Отдел: <span className="font-medium">{vacancyData.orgStructure.orgUnit}</span></p>
                )}
                {vacancyData.orgStructure.subordinatesCount !== undefined && vacancyData.orgStructure.subordinatesCount > 0 && (
                  <p>Подчинённых: <span className="font-medium">{vacancyData.orgStructure.subordinatesCount}</span></p>
                )}
              </div>
            </div>
          )}
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

      {/* Error Message */}
      {saveError && (
        <div className="mt-6 bg-red-50 border border-red-200 rounded-xl p-4 flex items-center gap-3">
          <AlertCircle size={20} className="text-red-500 flex-shrink-0" />
          <span className="text-red-700 text-sm">{saveError}</span>
        </div>
      )}

      {/* Actions */}
      <div className="mt-8 flex justify-end gap-3">
        <button
          onClick={onSave}
          disabled={isSaving}
          className="flex items-center gap-2 px-6 py-3 bg-gray-900 text-white
                     rounded-xl font-medium text-sm hover:bg-gray-800 transition-colors
                     disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isSaving ? (
            <>
              <Loader2 size={18} strokeWidth={2} className="animate-spin" />
              Сохранение...
            </>
          ) : (
            <>
              <CheckCircle2 size={18} strokeWidth={2} />
              Сохранить вакансию
            </>
          )}
        </button>
      </div>
    </div>
  );
}
