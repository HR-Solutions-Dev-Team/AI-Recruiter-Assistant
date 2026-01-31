import { useState, useMemo, useCallback } from 'react';
import { ChevronDown, ChevronRight, ArrowRight, Plus, Trash2, Check, Sparkles, Scale, Loader2, RotateCcw } from 'lucide-react';
import type {
  VacancyInput, Skill, Language,
  OnboardingMilestone, ShortTermKPI, AchievementMarker, AbsoluteRequirement
} from '../../types/vacancy';

export type SectionKey =
  | 'core'
  | 'company'
  | 'workConditions'
  | 'requirements'
  | 'responsibilities'
  // Executive Search
  | 'hiringContext'
  | 'successCriteria'
  | 'differentiators'
  | 'dealbreakers';

export type CriteriaWeights = Record<SectionKey, number>;

interface EditStepProps {
  onNext: () => void;
  vacancyData: VacancyInput;
  setVacancyData: React.Dispatch<React.SetStateAction<VacancyInput>>;
  completionPercent: number;
  setCompletionPercent: React.Dispatch<React.SetStateAction<number>>;
  // Веса критериев
  criteriaWeights: CriteriaWeights;
  setCriteriaWeights: React.Dispatch<React.SetStateAction<CriteriaWeights>>;
  isCalculatingWeights: boolean;
  onRecalculateWeights: () => void;
}

interface SectionConfig {
  key: SectionKey;
  title: string;
  description: string;
  baseWeight: number;
  isExecutiveSearch?: boolean;
}

// Базовые веса секций (будут корректироваться динамически)
const SECTIONS: SectionConfig[] = [
  // Базовые блоки (80% ключевой информации)
  { key: 'core', title: 'Позиция', description: 'Должность, уровень, отрасль', baseWeight: 20 },
  { key: 'company', title: 'Компания', description: 'Название, тип, сфера', baseWeight: 10 },
  { key: 'workConditions', title: 'Условия', description: 'Формат, зарплата, локация', baseWeight: 15 },
  { key: 'requirements', title: 'Требования', description: 'Опыт, навыки, языки', baseWeight: 20 },
  { key: 'responsibilities', title: 'Обязанности', description: 'Задачи, зоны ответственности', baseWeight: 10 },
  // Executive Search блоки
  { key: 'hiringContext', title: 'Контекст найма', description: 'Зачем нужен, какую проблему решает', baseWeight: 10, isExecutiveSearch: true },
  { key: 'successCriteria', title: 'Критерии успеха', description: 'KPI, milestones, ожидания', baseWeight: 5, isExecutiveSearch: true },
  { key: 'differentiators', title: 'Идеальный кандидат', description: 'Что отличает лучших', baseWeight: 5, isExecutiveSearch: true },
  { key: 'dealbreakers', title: 'Критические требования', description: 'Без чего точно нет', baseWeight: 5, isExecutiveSearch: true },
];

// Опции для select полей с русскими названиями
const CAREER_LEVELS: { value: string; label: string }[] = [
  { value: 'intern', label: 'Стажёр' },
  { value: 'junior', label: 'Младший специалист (Junior)' },
  { value: 'middle', label: 'Специалист (Middle)' },
  { value: 'senior', label: 'Старший специалист (Senior)' },
  { value: 'lead', label: 'Ведущий специалист (Lead)' },
  { value: 'head', label: 'Руководитель направления' },
  { value: 'director', label: 'Директор' },
  { value: 'c-level', label: 'Топ-менеджмент (C-level)' },
];

const COMPANY_TYPES: { value: string; label: string }[] = [
  { value: 'startup', label: 'Стартап' },
  { value: 'sme', label: 'Малый и средний бизнес' },
  { value: 'enterprise', label: 'Крупная компания' },
  { value: 'corporation', label: 'Корпорация' },
  { value: 'government', label: 'Государственная организация' },
  { value: 'ngo', label: 'Некоммерческая организация' },
  { value: 'consulting', label: 'Консалтинг' },
];

const COMPANY_SIZES = ['1-10', '11-50', '51-200', '201-500', '501-1000', '1001-5000', '5000+'];

const EMPLOYMENT_TYPES: { value: string; label: string }[] = [
  { value: 'full-time', label: 'Полная занятость' },
  { value: 'part-time', label: 'Частичная занятость' },
  { value: 'contract', label: 'Контракт/Проект' },
  { value: 'freelance', label: 'Фриланс' },
  { value: 'internship', label: 'Стажировка' },
  { value: 'temporary', label: 'Временная работа' },
];

const SCHEDULE_TYPES: { value: string; label: string }[] = [
  { value: '5/2', label: '5/2 (пн-пт)' },
  { value: '2/2', label: '2/2 (сменный)' },
  { value: 'flexible', label: 'Гибкий график' },
  { value: 'shift', label: 'Сменный график' },
  { value: 'remote-async', label: 'Удалённо (асинхронно)' },
  { value: 'hybrid', label: 'Гибридный' },
];

const REMOTE_TYPES: { value: string; label: string }[] = [
  { value: 'office', label: 'В офисе' },
  { value: 'remote', label: 'Удалённо' },
  { value: 'hybrid', label: 'Гибрид (офис + удалёнка)' },
  { value: 'relocate', label: 'С релокацией' },
];

const CURRENCIES = ['RUB', 'USD', 'EUR', 'GBP', 'KZT', 'BYN'];

const EDUCATION_LEVELS: { value: string; label: string }[] = [
  { value: 'any', label: 'Любое' },
  { value: 'secondary', label: 'Среднее' },
  { value: 'bachelor', label: 'Бакалавриат' },
  { value: 'master', label: 'Магистратура' },
  { value: 'phd', label: 'Аспирантура / PhD' },
  { value: 'mba', label: 'MBA' },
];

const SKILL_CATEGORIES: { value: string; label: string }[] = [
  { value: 'hard', label: 'Технические' },
  { value: 'soft', label: 'Гибкие навыки' },
  { value: 'management', label: 'Управленческие' },
  { value: 'digital_tool', label: 'Цифровые инструменты' },
];

const SKILL_LEVELS: { value: string; label: string }[] = [
  { value: 'basic', label: 'Базовый' },
  { value: 'intermediate', label: 'Средний' },
  { value: 'advanced', label: 'Продвинутый' },
  { value: 'expert', label: 'Эксперт' },
];

const LANGUAGE_PROFICIENCIES: { value: string; label: string }[] = [
  { value: 'A1', label: 'A1 (начальный)' },
  { value: 'A2', label: 'A2 (элементарный)' },
  { value: 'B1', label: 'B1 (средний)' },
  { value: 'B2', label: 'B2 (выше среднего)' },
  { value: 'C1', label: 'C1 (продвинутый)' },
  { value: 'C2', label: 'C2 (владение в совершенстве)' },
  { value: 'native', label: 'Родной' },
];

const BUSINESS_SEGMENTS: { value: string; label: string }[] = [
  { value: 'B2B', label: 'B2B (бизнес для бизнеса)' },
  { value: 'B2C', label: 'B2C (бизнес для потребителя)' },
  { value: 'B2B2C', label: 'B2B2C (смешанный)' },
  { value: 'B2G', label: 'B2G (бизнес для государства)' },
  { value: 'C2C', label: 'C2C (между потребителями)' },
  { value: 'D2C', label: 'D2C (напрямую потребителю)' },
];

// === EXECUTIVE SEARCH OPTIONS ===

const TRIGGER_EVENT_TYPES: { value: string; label: string }[] = [
  { value: 'growth', label: 'Рост бизнеса' },
  { value: 'replacement', label: 'Замена сотрудника' },
  { value: 'new_direction', label: 'Новое направление' },
  { value: 'crisis', label: 'Антикризисное управление' },
  { value: 'transformation', label: 'Трансформация' },
  { value: 'm_and_a', label: 'Слияние/поглощение' },
  { value: 'restructuring', label: 'Реструктуризация' },
];

const MILESTONE_TIMEFRAMES: { value: string; label: string }[] = [
  { value: '30_days', label: '30 дней' },
  { value: '60_days', label: '60 дней' },
  { value: '90_days', label: '90 дней' },
];

const ACHIEVEMENT_IMPORTANCE: { value: string; label: string }[] = [
  { value: 'must_have', label: 'Обязательно' },
  { value: 'strong_plus', label: 'Сильный плюс' },
  { value: 'nice_to_have', label: 'Желательно' },
];

const COMPETITOR_POLICIES: { value: string; label: string }[] = [
  { value: 'actively_hire', label: 'Активно нанимаем' },
  { value: 'neutral', label: 'Нейтрально' },
  { value: 'avoid', label: 'Избегаем' },
  { value: 'strict_avoid', label: 'Строго нет' },
];

const COMPANY_STAGES: { value: string; label: string }[] = [
  { value: 'startup_early', label: 'Ранний стартап' },
  { value: 'startup_growth', label: 'Растущий стартап' },
  { value: 'scaleup', label: 'Скейлап' },
  { value: 'enterprise', label: 'Зрелая компания' },
  { value: 'turnaround', label: 'Turnaround' },
  { value: 'm_and_a', label: 'M&A' },
];

// Дефолтные веса (баллы 0-10, используются до расчёта через LLM)
export const DEFAULT_WEIGHTS: CriteriaWeights = {
  core: 6,
  company: 5,
  workConditions: 5,
  requirements: 6,
  responsibilities: 5,
  hiringContext: 5,
  successCriteria: 5,
  differentiators: 5,
  dealbreakers: 5,
};

// Функция расчёта процентов из баллов
// Если балл = 0, считаем как 1 для расчёта
// Если все баллы = 0, равное распределение по ~11%
export const calculatePercentFromScores = (weights: CriteriaWeights): Record<SectionKey, number> => {
  const keys = Object.keys(weights) as SectionKey[];
  
  // Преобразуем 0 в 1 для расчёта
  const effectiveWeights = keys.map(k => weights[k] === 0 ? 1 : weights[k]);
  const total = effectiveWeights.reduce((a, b) => a + b, 0);
  
  // Если всё по 1 (все были 0), то равное распределение
  if (total === keys.length) {
    const equalPercent = Math.floor(100 / keys.length);
    const result: Record<string, number> = {};
    keys.forEach((k, i) => {
      // Последняя категория получает остаток
      result[k] = i === keys.length - 1 ? 100 - equalPercent * (keys.length - 1) : equalPercent;
    });
    return result as Record<SectionKey, number>;
  }
  
  // Обычный расчёт процентов
  const percents: Record<string, number> = {};
  let sum = 0;
  keys.forEach((k, i) => {
    const effectiveWeight = weights[k] === 0 ? 1 : weights[k];
    if (i === keys.length - 1) {
      // Последняя категория получает остаток для точности 100%
      percents[k] = 100 - sum;
    } else {
      const percent = Math.round((effectiveWeight / total) * 100);
      percents[k] = percent;
      sum += percent;
    }
  });
  
  return percents as Record<SectionKey, number>;
};

export default function EditStep({
  onNext,
  vacancyData,
  setVacancyData,
  completionPercent,
  setCompletionPercent,
  criteriaWeights,
  setCriteriaWeights,
  isCalculatingWeights,
  onRecalculateWeights,
}: EditStepProps) {
  const [openSection, setOpenSection] = useState<SectionKey | null>('core');
  const [showWeightsPanel, setShowWeightsPanel] = useState(true);

  // Проценты, рассчитанные из баллов
  const weightPercents = useMemo(() => calculatePercentFromScores(criteriaWeights), [criteriaWeights]);

  // Обработчик изменения балла категории (0-10)
  const handleWeightChange = useCallback((key: SectionKey, newValue: number) => {
    setCriteriaWeights(prev => ({
      ...prev,
      [key]: Math.max(0, Math.min(10, newValue)),
    }));
  }, [setCriteriaWeights]);

  const toggleSection = (key: SectionKey) => {
    setOpenSection(openSection === key ? null : key);
  };

  // Универсальный обновлятор вложенных полей
  const updateField = <T extends keyof VacancyInput>(
    section: T,
    field: string,
    value: unknown
  ) => {
    setVacancyData(prev => ({
      ...prev,
      [section]: {
        ...(prev[section] as object || {}),
        [field]: value,
      },
    }));
  };

  // Обновление вложенных объектов (уровень 3)
  const updateNestedField = <T extends keyof VacancyInput>(
    section: T,
    parent: string,
    field: string,
    value: unknown
  ) => {
    setVacancyData(prev => {
      const sectionData = (prev[section] as Record<string, unknown>) || {};
      const parentData = (sectionData[parent] as Record<string, unknown>) || {};
      return {
        ...prev,
        [section]: {
          ...sectionData,
          [parent]: {
            ...parentData,
            [field]: value,
          },
        },
      };
    });
  };

  // Подсчёт заполненности секции
  const getSectionCompletion = (key: SectionKey): number => {
    const section = vacancyData[key];
    if (!section) return 0;

    const values = Object.values(section);
    const filled = values.filter(v => {
      if (v === null || v === undefined) return false;
      if (typeof v === 'string') return v.trim() !== '';
      if (Array.isArray(v)) return v.length > 0;
      if (typeof v === 'object') return Object.values(v).some(x => x !== null && x !== undefined);
      return true;
    });

    return Math.round((filled.length / Math.max(values.length, 1)) * 100);
  };

  // Рендер текстового поля
  const renderTextField = (
    label: string,
    value: string | undefined,
    onChange: (val: string) => void,
    placeholder?: string
  ) => (
    <div className="mb-4">
      <label className="block text-sm font-medium text-gray-700 mb-1.5">{label}</label>
      <input
        type="text"
        value={value || ''}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm
                   focus:outline-none focus:ring-2 focus:ring-gray-900/10 focus:border-gray-300"
      />
    </div>
  );

  // Рендер числового поля
  const renderNumberField = (
    label: string,
    value: number | undefined,
    onChange: (val: number | undefined) => void,
    placeholder?: string
  ) => (
    <div className="mb-4">
      <label className="block text-sm font-medium text-gray-700 mb-1.5">{label}</label>
      <input
        type="number"
        value={value ?? ''}
        onChange={(e) => onChange(e.target.value ? Number(e.target.value) : undefined)}
        placeholder={placeholder}
        className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm
                   focus:outline-none focus:ring-2 focus:ring-gray-900/10 focus:border-gray-300"
      />
    </div>
  );

  // Рендер select поля (поддерживает как простые строки, так и {value, label})
  const renderSelectField = (
    label: string,
    value: string | undefined,
    options: string[] | { value: string; label: string }[],
    onChange: (val: string) => void,
    placeholder = 'Выберите...'
  ) => {
    const isLabeledOptions = options.length > 0 && typeof options[0] === 'object';

    return (
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-1.5">{label}</label>
        <select
          value={value || ''}
          onChange={(e) => onChange(e.target.value)}
          className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm bg-white
                     focus:outline-none focus:ring-2 focus:ring-gray-900/10 focus:border-gray-300"
        >
          <option value="">{placeholder}</option>
          {isLabeledOptions
            ? (options as { value: string; label: string }[]).map(opt => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))
            : (options as string[]).map(opt => (
                <option key={opt} value={opt}>{opt}</option>
              ))
          }
        </select>
      </div>
    );
  };

  // Рендер списка строк
  const renderStringList = (
    label: string,
    items: string[] | undefined,
    onChange: (items: string[]) => void
  ) => {
    const list = items || [];
    return (
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-1.5">{label}</label>
        <div className="space-y-2">
          {list.map((item, idx) => (
            <div key={idx} className="flex gap-2">
              <input
                type="text"
                value={item}
                onChange={(e) => {
                  const newList = [...list];
                  newList[idx] = e.target.value;
                  onChange(newList);
                }}
                className="flex-1 px-4 py-2 border border-gray-200 rounded-lg text-sm
                           focus:outline-none focus:ring-2 focus:ring-gray-900/10"
              />
              <button
                onClick={() => onChange(list.filter((_, i) => i !== idx))}
                className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg"
              >
                <Trash2 size={16} />
              </button>
            </div>
          ))}
          <button
            onClick={() => onChange([...list, ''])}
            className="flex items-center gap-2 px-4 py-2 text-sm text-gray-600
                       border border-dashed border-gray-300 rounded-lg hover:bg-gray-50 w-full"
          >
            <Plus size={16} /> Добавить
          </button>
        </div>
      </div>
    );
  };

  // Рендер checkbox
  const renderCheckbox = (
    label: string,
    checked: boolean | undefined,
    onChange: (val: boolean) => void
  ) => (
    <label className="flex items-center gap-3 mb-3 cursor-pointer">
      <div className={`w-5 h-5 rounded border-2 flex items-center justify-center
                       ${checked ? 'bg-gray-900 border-gray-900' : 'border-gray-300'}`}>
        {checked && <Check size={14} className="text-white" />}
      </div>
      <input
        type="checkbox"
        checked={checked || false}
        onChange={(e) => onChange(e.target.checked)}
        className="hidden"
      />
      <span className="text-sm text-gray-700">{label}</span>
    </label>
  );

  // === СЕКЦИИ ===

  const renderCoreSection = () => (
    <div className="space-y-4">
      {renderTextField('Название должности *', vacancyData.core?.jobTitle,
        (v) => updateField('core', 'jobTitle', v), 'Например: Ведущий разработчик')}

      {renderStringList('Альтернативные названия', vacancyData.core?.synonyms,
        (v) => updateField('core', 'synonyms', v))}

      <div className="bg-gray-50 rounded-xl p-4 mt-4">
        <h4 className="text-sm font-medium text-gray-900 mb-3">Уровень позиции</h4>
        {renderSelectField('Грейд', vacancyData.core?.careerLevel?.code, CAREER_LEVELS,
          (v) => updateNestedField('core', 'careerLevel', 'code', v))}
        <div className="grid grid-cols-2 gap-4">
          {renderNumberField('Опыт от (лет)', vacancyData.core?.careerLevel?.experienceYearsMin,
            (v) => updateNestedField('core', 'careerLevel', 'experienceYearsMin', v), '1')}
          {renderNumberField('Опыт до (лет)', vacancyData.core?.careerLevel?.experienceYearsMax,
            (v) => updateNestedField('core', 'careerLevel', 'experienceYearsMax', v), '5')}
        </div>
      </div>

      <div className="bg-gray-50 rounded-xl p-4">
        <h4 className="text-sm font-medium text-gray-900 mb-3">Отрасль</h4>
        {renderTextField('Отрасль', vacancyData.core?.industry?.name,
          (v) => updateNestedField('core', 'industry', 'name', v), 'ИТ, Финтех, Электронная коммерция')}
        {renderTextField('Подотрасль', vacancyData.core?.industry?.subIndustry,
          (v) => updateNestedField('core', 'industry', 'subIndustry', v), 'Разработка ПО, Банкинг')}
      </div>
    </div>
  );

  const renderCompanySection = () => (
    <div className="space-y-4">
      {renderTextField('Название компании', vacancyData.company?.name,
        (v) => updateField('company', 'name', v), 'ООО «Компания»')}

      <div className="grid grid-cols-2 gap-4">
        {renderSelectField('Тип компании', vacancyData.company?.type, COMPANY_TYPES,
          (v) => updateField('company', 'type', v))}
        {renderSelectField('Размер (сотрудников)', vacancyData.company?.size, COMPANY_SIZES,
          (v) => updateField('company', 'size', v))}
      </div>

      <div className="bg-gray-50 rounded-xl p-4">
        <h4 className="text-sm font-medium text-gray-900 mb-3">Сфера деятельности</h4>
        <p className="text-xs text-gray-500 mb-3">
          Укажите сферу деятельности компании для поиска узкоспециализированных кандидатов
        </p>
        {renderTextField('Сфера', vacancyData.company?.activitySphere?.sphere?.name,
          (v) => updateNestedField('company', 'activitySphere', 'sphere', { name: v }),
          'Информационные технологии, Общественное питание, Медицина...')}
        {renderTextField('Подсфера', vacancyData.company?.activitySphere?.subSphere?.name,
          (v) => updateNestedField('company', 'activitySphere', 'subSphere', { name: v }),
          'Финансовые технологии, Рестораны, Стоматология...')}
        {renderTextField('Специализация', vacancyData.company?.activitySphere?.specialization?.name,
          (v) => updateNestedField('company', 'activitySphere', 'specialization', { name: v }),
          'Платёжные системы, Кафе, Ортодонтия...')}
      </div>
    </div>
  );

  // === EXECUTIVE SEARCH SECTIONS ===

  const renderHiringContextSection = () => (
    <div className="space-y-4">
      {renderSelectField('Причина открытия вакансии', vacancyData.hiringContext?.triggerEvent?.type,
        TRIGGER_EVENT_TYPES,
        (v) => updateNestedField('hiringContext', 'triggerEvent', 'type', v))}

      {renderTextArea('Какую бизнес-проблему должен решить?', vacancyData.hiringContext?.businessProblem,
        (v) => updateField('hiringContext', 'businessProblem', v),
        'Опишите конкретную проблему, которую решит этот человек')}

      {renderTextArea('Ожидаемый результат от найма', vacancyData.hiringContext?.expectedImpact,
        (v) => updateField('hiringContext', 'expectedImpact', v),
        'Что изменится через 6-12 месяцев после выхода на работу?')}

      {renderTextField('Почему срочно?', vacancyData.hiringContext?.urgencyReason,
        (v) => updateField('hiringContext', 'urgencyReason', v), 'Причина срочности найма')}

      {renderTextArea('Ожидания стейкхолдеров', vacancyData.hiringContext?.stakeholderExpectations,
        (v) => updateField('hiringContext', 'stakeholderExpectations', v),
        'Чего ждут ключевые лица от этого найма?')}
    </div>
  );

  const renderSuccessCriteriaSection = () => (
    <div className="space-y-4">
      <div className="bg-gray-50 rounded-xl p-4">
        <h4 className="text-sm font-medium text-gray-900 mb-3">Milestones первых 90 дней</h4>
        {renderMilestonesList()}
      </div>

      <div className="bg-gray-50 rounded-xl p-4">
        <h4 className="text-sm font-medium text-gray-900 mb-3">KPI на 6 месяцев</h4>
        {renderKPIsList()}
      </div>

      {renderStringList('Стратегические цели (1+ год)', vacancyData.successCriteria?.longTermGoals,
        (v) => updateField('successCriteria', 'longTermGoals', v))}

      {renderTextArea('Качественные ожидания', vacancyData.successCriteria?.qualitativeExpectations,
        (v) => updateField('successCriteria', 'qualitativeExpectations', v),
        'Что сложно измерить, но важно для успеха?')}
    </div>
  );

  const renderDifferentiatorsSection = () => (
    <div className="space-y-4">
      {renderStringList('Знание доменов/областей', vacancyData.differentiators?.domainKnowledge,
        (v) => updateField('differentiators', 'domainKnowledge', v))}

      <div className="bg-gray-50 rounded-xl p-4">
        <h4 className="text-sm font-medium text-gray-900 mb-3">Опыт с масштабом</h4>
        {renderTextField('Размер команды (мин.)', vacancyData.differentiators?.scaleExperience?.teamSize?.description,
          (v) => {
            const current = vacancyData.differentiators?.scaleExperience || {};
            updateNestedField('differentiators', 'scaleExperience', 'teamSize', { ...current.teamSize, description: v });
          }, '10+ человек, 50+ человек')}
        {renderTextField('Бюджет в управлении', vacancyData.differentiators?.scaleExperience?.budget?.min,
          (v) => {
            const current = vacancyData.differentiators?.scaleExperience || {};
            updateNestedField('differentiators', 'scaleExperience', 'budget', { ...current.budget, min: v });
          }, '$1M+, 100M руб+')}
      </div>

      <div className="bg-gray-50 rounded-xl p-4">
        <h4 className="text-sm font-medium text-gray-900 mb-3">Ключевые достижения</h4>
        {renderAchievementsList()}
      </div>

      {renderTextField('Ценность нетворка', vacancyData.differentiators?.networkValue,
        (v) => updateField('differentiators', 'networkValue', v),
        'Какие связи важны? Клиенты, партнёры, эксперты...')}

      {renderStringList('Предпочтительные компании в бэкграунде', vacancyData.differentiators?.companyBackground?.preferred,
        (v) => updateNestedField('differentiators', 'companyBackground', 'preferred', v))}
    </div>
  );

  const renderDealbrakersSection = () => (
    <div className="space-y-4">
      <div className="bg-gray-50 rounded-xl p-4">
        <h4 className="text-sm font-medium text-gray-900 mb-3">Абсолютные требования</h4>
        {renderAbsoluteRequirementsList()}
      </div>

      <div className="bg-gray-50 rounded-xl p-4">
        <h4 className="text-sm font-medium text-gray-900 mb-3">Минимальный опыт</h4>
        <div className="grid grid-cols-3 gap-4">
          {renderNumberField('Всего лет', vacancyData.dealbreakers?.experienceMinimums?.totalYears,
            (v) => updateNestedField('dealbreakers', 'experienceMinimums', 'totalYears', v), '5')}
          {renderNumberField('В домене', vacancyData.dealbreakers?.experienceMinimums?.domainYears,
            (v) => updateNestedField('dealbreakers', 'experienceMinimums', 'domainYears', v), '3')}
          {renderNumberField('Руководство', vacancyData.dealbreakers?.experienceMinimums?.leadershipYears,
            (v) => updateNestedField('dealbreakers', 'experienceMinimums', 'leadershipYears', v), '2')}
        </div>
      </div>

      {renderStringList('Red flags (что точно НЕ подходит)', vacancyData.dealbreakers?.redFlags,
        (v) => updateField('dealbreakers', 'redFlags', v))}

      <div className="bg-gray-50 rounded-xl p-4">
        <h4 className="text-sm font-medium text-gray-900 mb-3">Политика по конкурентам</h4>
        {renderSelectField('Отношение к кандидатам из конкурентов', vacancyData.dealbreakers?.competitorPolicy?.policy,
          COMPETITOR_POLICIES,
          (v) => updateNestedField('dealbreakers', 'competitorPolicy', 'policy', v))}
        {renderStringList('Компании-конкуренты', vacancyData.dealbreakers?.competitorPolicy?.companies,
          (v) => updateNestedField('dealbreakers', 'competitorPolicy', 'companies', v))}
      </div>

      {renderStringList('Требования, которые не обсуждаются', vacancyData.dealbreakers?.nonNegotiables,
        (v) => updateField('dealbreakers', 'nonNegotiables', v))}
    </div>
  );

  // === СПИСКИ ДЛЯ EXECUTIVE SEARCH ===

  const renderMilestonesList = () => {
    const milestones = vacancyData.successCriteria?.onboardingMilestones || [];
    return (
      <div className="space-y-3">
        {milestones.map((item, idx) => (
          <div key={idx} className="bg-white rounded-lg p-3 border border-gray-200">
            <div className="flex justify-between items-start mb-2">
              <input
                type="text"
                value={item.milestone || ''}
                onChange={(e) => {
                  const newList = [...milestones];
                  newList[idx] = { ...item, milestone: e.target.value };
                  updateField('successCriteria', 'onboardingMilestones', newList);
                }}
                placeholder="Что должно быть достигнуто"
                className="flex-1 px-3 py-1.5 border border-gray-200 rounded-lg text-sm mr-2"
              />
              <button
                onClick={() => updateField('successCriteria', 'onboardingMilestones', milestones.filter((_, i) => i !== idx))}
                className="p-1.5 text-gray-400 hover:text-red-600"
              >
                <Trash2 size={14} />
              </button>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <select
                value={item.timeframe || ''}
                onChange={(e) => {
                  const newList = [...milestones];
                  newList[idx] = { ...item, timeframe: e.target.value as OnboardingMilestone['timeframe'] };
                  updateField('successCriteria', 'onboardingMilestones', newList);
                }}
                className="px-2 py-1.5 border border-gray-200 rounded-lg text-xs bg-white"
              >
                <option value="">Срок</option>
                {MILESTONE_TIMEFRAMES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
              </select>
              <input
                type="text"
                value={item.measureOfSuccess || ''}
                onChange={(e) => {
                  const newList = [...milestones];
                  newList[idx] = { ...item, measureOfSuccess: e.target.value };
                  updateField('successCriteria', 'onboardingMilestones', newList);
                }}
                placeholder="Как измерить успех"
                className="px-2 py-1.5 border border-gray-200 rounded-lg text-xs"
              />
            </div>
          </div>
        ))}
        <button
          onClick={() => updateField('successCriteria', 'onboardingMilestones', [...milestones, { milestone: '', timeframe: '30_days' }])}
          className="flex items-center gap-2 px-4 py-2 text-sm text-gray-600 border border-dashed border-gray-300 rounded-lg hover:bg-gray-50 w-full"
        >
          <Plus size={16} /> Добавить milestone
        </button>
      </div>
    );
  };

  const renderKPIsList = () => {
    const kpis = vacancyData.successCriteria?.shortTermKPIs || [];
    return (
      <div className="space-y-3">
        {kpis.map((item, idx) => (
          <div key={idx} className="bg-white rounded-lg p-3 border border-gray-200">
            <div className="flex justify-between items-start mb-2">
              <input
                type="text"
                value={item.metric || ''}
                onChange={(e) => {
                  const newList = [...kpis];
                  newList[idx] = { ...item, metric: e.target.value };
                  updateField('successCriteria', 'shortTermKPIs', newList);
                }}
                placeholder="Метрика (NPS, Revenue, Retention...)"
                className="flex-1 px-3 py-1.5 border border-gray-200 rounded-lg text-sm mr-2"
              />
              <button
                onClick={() => updateField('successCriteria', 'shortTermKPIs', kpis.filter((_, i) => i !== idx))}
                className="p-1.5 text-gray-400 hover:text-red-600"
              >
                <Trash2 size={14} />
              </button>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <input
                type="text"
                value={item.currentValue || ''}
                onChange={(e) => {
                  const newList = [...kpis];
                  newList[idx] = { ...item, currentValue: e.target.value };
                  updateField('successCriteria', 'shortTermKPIs', newList);
                }}
                placeholder="Текущее значение"
                className="px-2 py-1.5 border border-gray-200 rounded-lg text-xs"
              />
              <input
                type="text"
                value={item.targetValue || ''}
                onChange={(e) => {
                  const newList = [...kpis];
                  newList[idx] = { ...item, targetValue: e.target.value };
                  updateField('successCriteria', 'shortTermKPIs', newList);
                }}
                placeholder="Целевое значение"
                className="px-2 py-1.5 border border-gray-200 rounded-lg text-xs"
              />
            </div>
          </div>
        ))}
        <button
          onClick={() => updateField('successCriteria', 'shortTermKPIs', [...kpis, { metric: '' }])}
          className="flex items-center gap-2 px-4 py-2 text-sm text-gray-600 border border-dashed border-gray-300 rounded-lg hover:bg-gray-50 w-full"
        >
          <Plus size={16} /> Добавить KPI
        </button>
      </div>
    );
  };

  const renderAchievementsList = () => {
    const achievements = vacancyData.differentiators?.achievementMarkers || [];
    return (
      <div className="space-y-3">
        {achievements.map((item, idx) => (
          <div key={idx} className="flex gap-2 items-center">
            <input
              type="text"
              value={item.achievement || ''}
              onChange={(e) => {
                const newList = [...achievements];
                newList[idx] = { ...item, achievement: e.target.value };
                updateField('differentiators', 'achievementMarkers', newList);
              }}
              placeholder="Построил команду с 0, вывел продукт на рынок..."
              className="flex-1 px-3 py-2 border border-gray-200 rounded-lg text-sm"
            />
            <select
              value={item.importance || ''}
              onChange={(e) => {
                const newList = [...achievements];
                newList[idx] = { ...item, importance: e.target.value as AchievementMarker['importance'] };
                updateField('differentiators', 'achievementMarkers', newList);
              }}
              className="px-3 py-2 border border-gray-200 rounded-lg text-sm bg-white"
            >
              <option value="">Важность</option>
              {ACHIEVEMENT_IMPORTANCE.map(i => <option key={i.value} value={i.value}>{i.label}</option>)}
            </select>
            <button
              onClick={() => updateField('differentiators', 'achievementMarkers', achievements.filter((_, i) => i !== idx))}
              className="p-2 text-gray-400 hover:text-red-600"
            >
              <Trash2 size={16} />
            </button>
          </div>
        ))}
        <button
          onClick={() => updateField('differentiators', 'achievementMarkers', [...achievements, { achievement: '' }])}
          className="flex items-center gap-2 px-4 py-2 text-sm text-gray-600 border border-dashed border-gray-300 rounded-lg hover:bg-gray-50 w-full"
        >
          <Plus size={16} /> Добавить достижение
        </button>
      </div>
    );
  };

  const renderAbsoluteRequirementsList = () => {
    const requirements = vacancyData.dealbreakers?.absoluteRequirements || [];
    return (
      <div className="space-y-3">
        {requirements.map((item, idx) => (
          <div key={idx} className="bg-white rounded-lg p-3 border border-gray-200">
            <div className="flex justify-between items-start mb-2">
              <input
                type="text"
                value={item.requirement || ''}
                onChange={(e) => {
                  const newList = [...requirements];
                  newList[idx] = { ...item, requirement: e.target.value };
                  updateField('dealbreakers', 'absoluteRequirements', newList);
                }}
                placeholder="Требование без исключений"
                className="flex-1 px-3 py-1.5 border border-gray-200 rounded-lg text-sm mr-2"
              />
              <button
                onClick={() => updateField('dealbreakers', 'absoluteRequirements', requirements.filter((_, i) => i !== idx))}
                className="p-1.5 text-gray-400 hover:text-red-600"
              >
                <Trash2 size={14} />
              </button>
            </div>
            <input
              type="text"
              value={item.reason || ''}
              onChange={(e) => {
                const newList = [...requirements];
                newList[idx] = { ...item, reason: e.target.value };
                updateField('dealbreakers', 'absoluteRequirements', newList);
              }}
              placeholder="Почему это критично?"
              className="w-full px-2 py-1.5 border border-gray-200 rounded-lg text-xs"
            />
          </div>
        ))}
        <button
          onClick={() => updateField('dealbreakers', 'absoluteRequirements', [...requirements, { requirement: '' }])}
          className="flex items-center gap-2 px-4 py-2 text-sm text-gray-600 border border-dashed border-gray-300 rounded-lg hover:bg-gray-50 w-full"
        >
          <Plus size={16} /> Добавить требование
        </button>
      </div>
    );
  };

  // Рендер textarea
  const renderTextArea = (
    label: string,
    value: string | undefined,
    onChange: (val: string) => void,
    placeholder?: string
  ) => (
    <div className="mb-4">
      <label className="block text-sm font-medium text-gray-700 mb-1.5">{label}</label>
      <textarea
        value={value || ''}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        rows={3}
        className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm
                   focus:outline-none focus:ring-2 focus:ring-gray-900/10 focus:border-gray-300 resize-none"
      />
    </div>
  );

  const renderWorkConditionsSection = () => (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        {renderSelectField('Тип занятости', vacancyData.workConditions?.employmentType?.name, EMPLOYMENT_TYPES,
          (v) => updateNestedField('workConditions', 'employmentType', 'name', v))}
        {renderSelectField('График', vacancyData.workConditions?.schedule?.name, SCHEDULE_TYPES,
          (v) => updateNestedField('workConditions', 'schedule', 'name', v))}
      </div>

      {renderTextField('Часы работы', vacancyData.workConditions?.workHours,
        (v) => updateField('workConditions', 'workHours', v), '10:00-19:00 по Москве')}

      <div className="bg-gray-50 rounded-xl p-4">
        <h4 className="text-sm font-medium text-gray-900 mb-3">Зарплата</h4>
        <div className="grid grid-cols-3 gap-4">
          {renderNumberField('От', vacancyData.workConditions?.salary?.amountMin,
            (v) => updateNestedField('workConditions', 'salary', 'amountMin', v), '150000')}
          {renderNumberField('До', vacancyData.workConditions?.salary?.amountMax,
            (v) => updateNestedField('workConditions', 'salary', 'amountMax', v), '300000')}
          {renderSelectField('Валюта', vacancyData.workConditions?.salary?.currency, CURRENCIES,
            (v) => updateNestedField('workConditions', 'salary', 'currency', v))}
        </div>
        {renderTextField('Комментарий', vacancyData.workConditions?.salary?.comment,
          (v) => updateNestedField('workConditions', 'salary', 'comment', v), 'до вычета налогов, + премии')}
      </div>

      <div className="bg-gray-50 rounded-xl p-4">
        <h4 className="text-sm font-medium text-gray-900 mb-3">Локация</h4>
        <div className="grid grid-cols-2 gap-4">
          {renderTextField('Город', vacancyData.workConditions?.location?.city,
            (v) => updateNestedField('workConditions', 'location', 'city', v), 'Москва')}
          {renderTextField('Страна', vacancyData.workConditions?.location?.country,
            (v) => updateNestedField('workConditions', 'location', 'country', v), 'Россия')}
        </div>
        {renderSelectField('Формат работы', vacancyData.workConditions?.location?.remote, REMOTE_TYPES,
          (v) => updateNestedField('workConditions', 'location', 'remote', v))}
        <div className="mt-3">
          {renderCheckbox('Помощь с релокацией', vacancyData.workConditions?.location?.relocationSupport,
            (v) => updateNestedField('workConditions', 'location', 'relocationSupport', v))}
          {renderCheckbox('Визовая поддержка', vacancyData.workConditions?.location?.visaSupport,
            (v) => updateNestedField('workConditions', 'location', 'visaSupport', v))}
        </div>
      </div>
    </div>
  );

  const renderRequirementsSection = () => (
    <div className="space-y-4">
      <div className="bg-gray-50 rounded-xl p-4">
        <h4 className="text-sm font-medium text-gray-900 mb-3">Образование</h4>
        {renderSelectField('Уровень', vacancyData.requirements?.education?.level, EDUCATION_LEVELS,
          (v) => updateNestedField('requirements', 'education', 'level', v))}
        {renderStringList('Направления подготовки', vacancyData.requirements?.education?.fields,
          (v) => updateNestedField('requirements', 'education', 'fields', v))}
      </div>

      <div className="bg-gray-50 rounded-xl p-4">
        <h4 className="text-sm font-medium text-gray-900 mb-3">Опыт работы</h4>
        <div className="grid grid-cols-2 gap-4">
          {renderNumberField('Лет от', vacancyData.requirements?.experience?.yearsMin,
            (v) => updateNestedField('requirements', 'experience', 'yearsMin', v), '1')}
          {renderNumberField('Лет до', vacancyData.requirements?.experience?.yearsMax,
            (v) => updateNestedField('requirements', 'experience', 'yearsMax', v), '5')}
        </div>
        {renderStringList('Отрасли опыта', vacancyData.requirements?.experience?.domains,
          (v) => updateNestedField('requirements', 'experience', 'domains', v))}
        {renderStringList('Обязательный опыт', vacancyData.requirements?.experience?.mustHave,
          (v) => updateNestedField('requirements', 'experience', 'mustHave', v))}
        {renderStringList('Желательный опыт', vacancyData.requirements?.experience?.niceToHave,
          (v) => updateNestedField('requirements', 'experience', 'niceToHave', v))}
      </div>

      <div className="bg-gray-50 rounded-xl p-4">
        <h4 className="text-sm font-medium text-gray-900 mb-3">Навыки</h4>
        {renderSkillsList()}
      </div>

      <div className="bg-gray-50 rounded-xl p-4">
        <h4 className="text-sm font-medium text-gray-900 mb-3">Языки</h4>
        {renderLanguagesList()}
      </div>
    </div>
  );

  const renderSkillsList = () => {
    const skills = vacancyData.requirements?.skills || [];
    return (
      <div className="space-y-3">
        {skills.map((skill, idx) => (
          <div key={idx} className="bg-white rounded-lg p-3 border border-gray-200">
            <div className="flex justify-between items-start mb-2">
              <input
                type="text"
                value={skill.name}
                onChange={(e) => {
                  const newSkills = [...skills];
                  newSkills[idx] = { ...skill, name: e.target.value };
                  updateField('requirements', 'skills', newSkills);
                }}
                placeholder="Например: React, Python, Управление командой"
                className="flex-1 px-3 py-1.5 border border-gray-200 rounded-lg text-sm mr-2"
              />
              <button
                onClick={() => updateField('requirements', 'skills', skills.filter((_, i) => i !== idx))}
                className="p-1.5 text-gray-400 hover:text-red-600"
              >
                <Trash2 size={14} />
              </button>
            </div>
            <div className="grid grid-cols-3 gap-2">
              <select
                value={skill.category}
                onChange={(e) => {
                  const newSkills = [...skills];
                  newSkills[idx] = { ...skill, category: e.target.value as Skill['category'] };
                  updateField('requirements', 'skills', newSkills);
                }}
                className="px-2 py-1.5 border border-gray-200 rounded-lg text-xs bg-white"
              >
                {SKILL_CATEGORIES.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
              </select>
              <select
                value={skill.level || ''}
                onChange={(e) => {
                  const newSkills = [...skills];
                  newSkills[idx] = { ...skill, level: e.target.value as Skill['level'] };
                  updateField('requirements', 'skills', newSkills);
                }}
                className="px-2 py-1.5 border border-gray-200 rounded-lg text-xs bg-white"
              >
                <option value="">Уровень</option>
                {SKILL_LEVELS.map(l => <option key={l.value} value={l.value}>{l.label}</option>)}
              </select>
              <label className="flex items-center gap-2 text-xs">
                <input
                  type="checkbox"
                  checked={skill.isRequired || false}
                  onChange={(e) => {
                    const newSkills = [...skills];
                    newSkills[idx] = { ...skill, isRequired: e.target.checked };
                    updateField('requirements', 'skills', newSkills);
                  }}
                />
                Обязательный
              </label>
            </div>
          </div>
        ))}
        <button
          onClick={() => updateField('requirements', 'skills', [...skills, { name: '', category: 'hard', isRequired: true }])}
          className="flex items-center gap-2 px-4 py-2 text-sm text-gray-600
                     border border-dashed border-gray-300 rounded-lg hover:bg-gray-50 w-full"
        >
          <Plus size={16} /> Добавить навык
        </button>
      </div>
    );
  };

  const renderLanguagesList = () => {
    const languages = vacancyData.requirements?.languages || [];
    return (
      <div className="space-y-3">
        {languages.map((lang, idx) => (
          <div key={idx} className="flex gap-2 items-center">
            <input
              type="text"
              value={lang.name}
              onChange={(e) => {
                const newLangs = [...languages];
                newLangs[idx] = { ...lang, name: e.target.value };
                updateField('requirements', 'languages', newLangs);
              }}
              placeholder="Русский, Английский..."
              className="flex-1 px-3 py-2 border border-gray-200 rounded-lg text-sm"
            />
            <select
              value={lang.proficiency || ''}
              onChange={(e) => {
                const newLangs = [...languages];
                newLangs[idx] = { ...lang, proficiency: e.target.value as Language['proficiency'] };
                updateField('requirements', 'languages', newLangs);
              }}
              className="px-3 py-2 border border-gray-200 rounded-lg text-sm bg-white"
            >
              <option value="">Уровень</option>
              {LANGUAGE_PROFICIENCIES.map(p => <option key={p.value} value={p.value}>{p.label}</option>)}
            </select>
            <label className="flex items-center gap-2 text-sm whitespace-nowrap">
              <input
                type="checkbox"
                checked={lang.isRequired || false}
                onChange={(e) => {
                  const newLangs = [...languages];
                  newLangs[idx] = { ...lang, isRequired: e.target.checked };
                  updateField('requirements', 'languages', newLangs);
                }}
              />
              Обяз.
            </label>
            <button
              onClick={() => updateField('requirements', 'languages', languages.filter((_, i) => i !== idx))}
              className="p-2 text-gray-400 hover:text-red-600"
            >
              <Trash2 size={16} />
            </button>
          </div>
        ))}
        <button
          onClick={() => updateField('requirements', 'languages', [...languages, { name: '', isRequired: false }])}
          className="flex items-center gap-2 px-4 py-2 text-sm text-gray-600
                     border border-dashed border-gray-300 rounded-lg hover:bg-gray-50 w-full"
        >
          <Plus size={16} /> Добавить язык
        </button>
      </div>
    );
  };

  const renderResponsibilitiesSection = () => (
    <div className="space-y-4">
      {renderTextArea('Общее описание роли', vacancyData.responsibilities?.scope,
        (v) => updateField('responsibilities', 'scope', v), 'Кратко опишите ключевую миссию роли')}

      {renderStringList('Ключевые зоны ответственности', vacancyData.responsibilities?.zones,
        (v) => updateField('responsibilities', 'zones', v))}

      {renderTextField('Кому подчиняется', vacancyData.orgStructure?.reportsTo,
        (v) => updateField('orgStructure', 'reportsTo', v), 'CTO, VP Engineering, Руководитель отдела')}

      {renderNumberField('Количество подчинённых', vacancyData.orgStructure?.subordinatesCount,
        (v) => updateField('orgStructure', 'subordinatesCount', v), '0')}

      {renderStringList('Процессы в управлении', vacancyData.responsibilities?.processOwnership,
        (v) => updateField('responsibilities', 'processOwnership', v))}
    </div>
  );

  const renderSectionContent = (key: SectionKey) => {
    switch (key) {
      case 'core': return renderCoreSection();
      case 'company': return renderCompanySection();
      case 'workConditions': return renderWorkConditionsSection();
      case 'requirements': return renderRequirementsSection();
      case 'responsibilities': return renderResponsibilitiesSection();
      // Executive Search
      case 'hiringContext': return renderHiringContextSection();
      case 'successCriteria': return renderSuccessCriteriaSection();
      case 'differentiators': return renderDifferentiatorsSection();
      case 'dealbreakers': return renderDealbrakersSection();
      default: return null;
    }
  };

  // Разделяем секции на базовые и Executive Search
  const baseSections = SECTIONS.filter(s => !s.isExecutiveSearch);
  const execSections = SECTIONS.filter(s => s.isExecutiveSearch);

  const renderSectionItem = (section: SectionConfig) => {
    const isOpen = openSection === section.key;
    const sectionCompletion = getSectionCompletion(section.key);
    const weightPercent = weightPercents[section.key];

    return (
      <div
        key={section.key}
        className={`bg-white border rounded-xl overflow-hidden ${
          section.isExecutiveSearch ? 'border-amber-200' : 'border-gray-200'
        }`}
      >
        <button
          onClick={() => toggleSection(section.key)}
          className={`w-full px-4 py-4 flex items-center justify-between transition-colors ${
            section.isExecutiveSearch ? 'hover:bg-amber-50' : 'hover:bg-gray-50'
          }`}
        >
          <div className="flex items-center gap-3">
            {isOpen ? (
              <ChevronDown size={20} className="text-gray-400" />
            ) : (
              <ChevronRight size={20} className="text-gray-400" />
            )}
            <div className="text-left">
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-medium text-gray-900">{section.title}</h3>
                {section.isExecutiveSearch && (
                  <span className="px-1.5 py-0.5 text-[10px] font-medium bg-amber-100 text-amber-700 rounded">
                    Executive
                  </span>
                )}
              </div>
              <p className="text-xs text-gray-500">{section.description}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="text-right mr-2">
              <span className="text-[10px] text-gray-400">вес</span>
              <span className="block text-xs font-medium text-gray-600">{weightPercent}%</span>
            </div>
            <div className="w-16 h-1.5 bg-gray-200 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full ${section.isExecutiveSearch ? 'bg-amber-500' : 'bg-green-500'}`}
                style={{ width: `${sectionCompletion}%` }}
              />
            </div>
            <span className="text-xs text-gray-500 w-8">{sectionCompletion}%</span>
          </div>
        </button>

        {isOpen && (
          <div className={`px-4 pb-4 pt-2 border-t ${section.isExecutiveSearch ? 'border-amber-100 bg-amber-50/30' : 'border-gray-100'}`}>
            {renderSectionContent(section.key)}
          </div>
        )}
      </div>
    );
  };

  // Рендер кастомного слайдера для одной категории весов (0-10)
  const renderWeightSlider = (key: SectionKey, title: string, isExecutive: boolean = false) => {
    const score = criteriaWeights[key];
    const fillColor = isExecutive ? 'bg-amber-500' : 'bg-gray-900';
    const fillPercent = (score / 10) * 100;
    
    return (
      <div key={key} className="flex items-center gap-3 py-2">
        <div className="w-36 flex items-center gap-2">
          <span className={`text-sm ${isExecutive ? 'text-amber-700' : 'text-gray-700'}`}>
            {title}
          </span>
          {isExecutive && (
            <span className="px-1 py-0.5 text-[8px] font-medium bg-amber-100 text-amber-600 rounded">
              ES
            </span>
          )}
        </div>
        
        {/* Кастомный слайдер с рисками */}
        <div className="flex-1 relative">
          {/* Серая линия с рисками */}
          <div className="relative h-6 flex items-center">
            {/* Основная линия (серая) */}
            <div className="absolute inset-x-0 top-1/2 -translate-y-1/2 h-1.5 bg-gray-200 rounded-full" />
            
            {/* Цветное заполнение */}
            <div 
              className={`absolute left-0 top-1/2 -translate-y-1/2 h-1.5 ${fillColor} rounded-full transition-all duration-150`}
              style={{ width: `${fillPercent}%` }}
            />
            
            {/* Риски (0-10) */}
            <div className="absolute inset-x-0 top-1/2 -translate-y-1/2 flex justify-between px-0">
              {Array.from({ length: 11 }, (_, i) => (
                <div
                  key={i}
                  className={`w-0.5 ${i === 0 || i === 10 ? 'h-3' : 'h-2'} ${
                    i <= score ? (isExecutive ? 'bg-amber-400' : 'bg-gray-600') : 'bg-gray-300'
                  } rounded-full`}
                />
              ))}
            </div>
            
            {/* Невидимый input для управления */}
            <input
              type="range"
              min={0}
              max={10}
              step={1}
              value={score}
              onChange={(e) => handleWeightChange(key, parseInt(e.target.value))}
              disabled={isCalculatingWeights}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed"
            />
            
            {/* Ползунок (точка) */}
            <div 
              className={`absolute top-1/2 -translate-y-1/2 w-4 h-4 ${fillColor} rounded-full shadow-md
                         border-2 border-white transition-all duration-150
                         ${isCalculatingWeights ? 'opacity-50' : ''}`}
              style={{ left: `calc(${fillPercent}% - 8px)` }}
            />
          </div>
        </div>
        
        {/* Балл справа */}
        <div className="w-8 text-right">
          <span className={`text-sm font-bold ${isExecutive ? 'text-amber-700' : 'text-gray-900'}`}>
            {score}
          </span>
        </div>
      </div>
    );
  };

  // Сумма всех баллов (для отображения)
  const totalScores = Object.values(criteriaWeights).reduce((a, b) => a + b, 0);

  return (
    <div className="max-w-3xl mx-auto">
      {/* Progress Bar */}
      <div className="mb-6 bg-white border border-gray-200 rounded-xl p-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700">Заполненность вакансии</span>
          <span className="text-sm font-semibold text-gray-900">{completionPercent}%</span>
        </div>
        <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
          <div
            className="h-full bg-gray-900 rounded-full transition-all duration-300"
            style={{ width: `${completionPercent}%` }}
          />
        </div>
      </div>

      {/* Weights Panel */}
      <div className="mb-6 bg-white border border-gray-200 rounded-xl overflow-hidden">
        <button
          onClick={() => setShowWeightsPanel(!showWeightsPanel)}
          className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50 transition-colors"
        >
          <div className="flex items-center gap-3">
            <Scale size={20} className="text-gray-500" />
            <div className="text-left">
              <h3 className="text-sm font-medium text-gray-900">Приоритеты критериев отбора</h3>
              <p className="text-xs text-gray-500">
                {isCalculatingWeights 
                  ? 'Рассчитываем приоритеты...' 
                  : 'Оцените важность каждой категории от 0 до 10'}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {isCalculatingWeights && (
              <Loader2 size={18} className="animate-spin text-gray-400" />
            )}
            <span className="text-sm font-medium text-gray-600">
              {totalScores} баллов
            </span>
            {showWeightsPanel ? (
              <ChevronDown size={20} className="text-gray-400" />
            ) : (
              <ChevronRight size={20} className="text-gray-400" />
            )}
          </div>
        </button>

        {showWeightsPanel && (
          <div className="px-4 pb-4 pt-2 border-t border-gray-100">
            {/* Базовые категории */}
            <div className="mb-3">
              {renderWeightSlider('core', 'Позиция')}
              {renderWeightSlider('company', 'Компания')}
              {renderWeightSlider('workConditions', 'Условия')}
              {renderWeightSlider('requirements', 'Требования')}
              {renderWeightSlider('responsibilities', 'Обязанности')}
            </div>

            {/* Разделитель Executive Search */}
            <div className="flex items-center gap-2 my-3">
              <div className="flex-1 h-px bg-amber-200" />
              <span className="text-[10px] font-medium text-amber-600 uppercase">Executive Search</span>
              <div className="flex-1 h-px bg-amber-200" />
            </div>

            {/* Executive Search категории */}
            <div className="mb-3">
              {renderWeightSlider('hiringContext', 'Контекст найма', true)}
              {renderWeightSlider('successCriteria', 'Критерии успеха', true)}
              {renderWeightSlider('differentiators', 'Идеальный кандидат', true)}
              {renderWeightSlider('dealbreakers', 'Критические треб.', true)}
            </div>

            {/* Кнопка пересчёта */}
            <div className="flex justify-end pt-2 border-t border-gray-100">
              <button
                onClick={onRecalculateWeights}
                disabled={isCalculatingWeights}
                className="flex items-center gap-2 px-3 py-1.5 text-xs font-medium text-gray-600
                           hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors
                           disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isCalculatingWeights ? (
                  <Loader2 size={14} className="animate-spin" />
                ) : (
                  <RotateCcw size={14} />
                )}
                Пересчитать через AI
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Base Sections */}
      <div className="space-y-3">
        {baseSections.map(renderSectionItem)}
      </div>

      {/* Executive Search Divider */}
      <div className="my-6 flex items-center gap-3">
        <div className="flex-1 h-px bg-amber-200" />
        <div className="flex items-center gap-2 px-3 py-1.5 bg-amber-50 rounded-full">
          <Sparkles size={14} className="text-amber-600" />
          <span className="text-xs font-medium text-amber-700">Executive Search</span>
        </div>
        <div className="flex-1 h-px bg-amber-200" />
      </div>

      {/* Executive Search Sections */}
      <div className="space-y-3">
        {execSections.map(renderSectionItem)}
      </div>

      {/* Action Button */}
      <div className="mt-8 flex justify-end">
        <button
          onClick={onNext}
          className="flex items-center gap-2 px-6 py-3 bg-gray-900 text-white
                     rounded-xl font-medium text-sm hover:bg-gray-800 transition-colors"
        >
          Продолжить
          <ArrowRight size={18} strokeWidth={2} />
        </button>
      </div>
    </div>
  );
}
