import { useState } from 'react';
import { Pencil, X, Check, Plus, Trash2, ArrowRight, GripVertical } from 'lucide-react';
import type { VacancyData } from '../../pages/VacancyCreate';

interface EditStepProps {
  onNext: () => void;
  vacancyData: VacancyData;
  setVacancyData: React.Dispatch<React.SetStateAction<VacancyData>>;
}

type EditingField = string | null;

interface FieldConfig {
  key: keyof VacancyData;
  label: string;
  type: 'text' | 'textarea' | 'select' | 'list' | 'salary';
  options?: string[];
  placeholder?: string;
}

const FIELD_CONFIGS: FieldConfig[] = [
  { key: 'title', label: 'Название позиции', type: 'text', placeholder: 'Например: Senior Frontend Developer' },
  { key: 'department', label: 'Отдел', type: 'text', placeholder: 'Например: Engineering' },
  { key: 'location', label: 'Локация', type: 'text', placeholder: 'Например: Москва' },
  {
    key: 'employmentType',
    label: 'Формат работы',
    type: 'select',
    options: ['Полная занятость (офис)', 'Полная занятость (удалённо)', 'Гибрид', 'Частичная занятость'],
  },
  {
    key: 'experienceLevel',
    label: 'Уровень опыта',
    type: 'select',
    options: ['Junior', 'Middle', 'Senior', 'Lead', 'Principal'],
  },
  { key: 'salaryFrom', label: 'Заработная плата', type: 'salary' },
  { key: 'description', label: 'Описание', type: 'textarea', placeholder: 'Краткое описание позиции...' },
  { key: 'responsibilities', label: 'Обязанности', type: 'list' },
  { key: 'requirements', label: 'Требования', type: 'list' },
  { key: 'niceToHave', label: 'Будет плюсом', type: 'list' },
  { key: 'benefits', label: 'Что мы предлагаем', type: 'list' },
];

export default function EditStep({ onNext, vacancyData, setVacancyData }: EditStepProps) {
  const [editingField, setEditingField] = useState<EditingField>(null);
  const [tempValue, setTempValue] = useState<string | string[]>('');
  const [newListItem, setNewListItem] = useState('');

  const startEditing = (field: FieldConfig) => {
    setEditingField(field.key);
    setTempValue(vacancyData[field.key] as string | string[]);
  };

  const cancelEditing = () => {
    setEditingField(null);
    setTempValue('');
    setNewListItem('');
  };

  const saveField = (key: keyof VacancyData) => {
    setVacancyData((prev) => ({
      ...prev,
      [key]: tempValue,
    }));
    setEditingField(null);
    setTempValue('');
  };

  const addListItem = (key: keyof VacancyData) => {
    if (newListItem.trim()) {
      const currentList = tempValue as string[];
      setTempValue([...currentList, newListItem.trim()]);
      setNewListItem('');
    }
  };

  const removeListItem = (index: number) => {
    const currentList = tempValue as string[];
    setTempValue(currentList.filter((_, i) => i !== index));
  };

  const updateListItem = (index: number, value: string) => {
    const currentList = [...(tempValue as string[])];
    currentList[index] = value;
    setTempValue(currentList);
  };

  const renderFieldValue = (field: FieldConfig) => {
    const value = vacancyData[field.key];

    if (field.type === 'list') {
      const items = value as string[];
      if (items.length === 0) {
        return <span className="text-gray-400 italic">Не указано</span>;
      }
      return (
        <ul className="list-disc list-inside space-y-1">
          {items.map((item, index) => (
            <li key={index} className="text-gray-700 text-sm">{item}</li>
          ))}
        </ul>
      );
    }

    if (field.type === 'salary') {
      const from = vacancyData.salaryFrom;
      const to = vacancyData.salaryTo;
      if (!from && !to) {
        return <span className="text-gray-400 italic">Не указано</span>;
      }
      return (
        <span className="text-gray-700">
          {from && to ? `${Number(from).toLocaleString()} — ${Number(to).toLocaleString()} ${vacancyData.currency}` :
            from ? `от ${Number(from).toLocaleString()} ${vacancyData.currency}` :
            `до ${Number(to).toLocaleString()} ${vacancyData.currency}`}
        </span>
      );
    }

    if (!value || (typeof value === 'string' && !value.trim())) {
      return <span className="text-gray-400 italic">Не указано</span>;
    }

    return <span className="text-gray-700">{value as string}</span>;
  };

  const renderEditor = (field: FieldConfig) => {
    if (field.type === 'text') {
      return (
        <input
          type="text"
          value={tempValue as string}
          onChange={(e) => setTempValue(e.target.value)}
          placeholder={field.placeholder}
          className="w-full px-4 py-2.5 border border-gray-300 rounded-xl text-sm
                     focus:outline-none focus:ring-2 focus:ring-gray-900/10 focus:border-gray-400"
          autoFocus
        />
      );
    }

    if (field.type === 'textarea') {
      return (
        <textarea
          value={tempValue as string}
          onChange={(e) => setTempValue(e.target.value)}
          placeholder={field.placeholder}
          rows={4}
          className="w-full px-4 py-2.5 border border-gray-300 rounded-xl text-sm resize-none
                     focus:outline-none focus:ring-2 focus:ring-gray-900/10 focus:border-gray-400"
          autoFocus
        />
      );
    }

    if (field.type === 'select') {
      return (
        <select
          value={tempValue as string}
          onChange={(e) => setTempValue(e.target.value)}
          className="w-full px-4 py-2.5 border border-gray-300 rounded-xl text-sm
                     focus:outline-none focus:ring-2 focus:ring-gray-900/10 focus:border-gray-400
                     bg-white"
        >
          <option value="">Выберите...</option>
          {field.options?.map((option) => (
            <option key={option} value={option}>{option}</option>
          ))}
        </select>
      );
    }

    if (field.type === 'salary') {
      const [from, to] = typeof tempValue === 'string'
        ? [vacancyData.salaryFrom, vacancyData.salaryTo]
        : [tempValue[0] || '', tempValue[1] || ''];

      return (
        <div className="space-y-3">
          <div className="flex gap-3">
            <div className="flex-1">
              <label className="text-xs text-gray-500 mb-1 block">От</label>
              <input
                type="number"
                value={from}
                onChange={(e) => {
                  setVacancyData(prev => ({ ...prev, salaryFrom: e.target.value }));
                }}
                placeholder="100000"
                className="w-full px-4 py-2.5 border border-gray-300 rounded-xl text-sm
                           focus:outline-none focus:ring-2 focus:ring-gray-900/10 focus:border-gray-400"
              />
            </div>
            <div className="flex-1">
              <label className="text-xs text-gray-500 mb-1 block">До</label>
              <input
                type="number"
                value={to}
                onChange={(e) => {
                  setVacancyData(prev => ({ ...prev, salaryTo: e.target.value }));
                }}
                placeholder="200000"
                className="w-full px-4 py-2.5 border border-gray-300 rounded-xl text-sm
                           focus:outline-none focus:ring-2 focus:ring-gray-900/10 focus:border-gray-400"
              />
            </div>
            <div className="w-24">
              <label className="text-xs text-gray-500 mb-1 block">Валюта</label>
              <select
                value={vacancyData.currency}
                onChange={(e) => setVacancyData(prev => ({ ...prev, currency: e.target.value }))}
                className="w-full px-3 py-2.5 border border-gray-300 rounded-xl text-sm
                           focus:outline-none focus:ring-2 focus:ring-gray-900/10 focus:border-gray-400 bg-white"
              >
                <option value="RUB">RUB</option>
                <option value="USD">USD</option>
                <option value="EUR">EUR</option>
              </select>
            </div>
          </div>
        </div>
      );
    }

    if (field.type === 'list') {
      const items = tempValue as string[];
      return (
        <div className="space-y-2">
          {items.map((item, index) => (
            <div key={index} className="flex items-center gap-2">
              <GripVertical size={16} className="text-gray-400 flex-shrink-0" />
              <input
                type="text"
                value={item}
                onChange={(e) => updateListItem(index, e.target.value)}
                className="flex-1 px-4 py-2 border border-gray-200 rounded-lg text-sm
                           focus:outline-none focus:ring-2 focus:ring-gray-900/10 focus:border-gray-300"
              />
              <button
                onClick={() => removeListItem(index)}
                className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg
                           sidebar-transition"
              >
                <Trash2 size={16} strokeWidth={2} />
              </button>
            </div>
          ))}
          <div className="flex items-center gap-2 mt-3">
            <input
              type="text"
              value={newListItem}
              onChange={(e) => setNewListItem(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && addListItem(field.key)}
              placeholder="Добавить пункт..."
              className="flex-1 px-4 py-2 border border-dashed border-gray-300 rounded-lg text-sm
                         focus:outline-none focus:ring-2 focus:ring-gray-900/10 focus:border-gray-400"
            />
            <button
              onClick={() => addListItem(field.key)}
              disabled={!newListItem.trim()}
              className={`
                p-2 rounded-lg sidebar-transition
                ${newListItem.trim()
                  ? 'text-gray-900 hover:bg-gray-100'
                  : 'text-gray-300 cursor-not-allowed'
                }
              `}
            >
              <Plus size={18} strokeWidth={2} />
            </button>
          </div>
        </div>
      );
    }

    return null;
  };

  return (
    <div className="max-w-3xl mx-auto">
      {/* Info */}
      <p className="text-sm text-gray-500 mb-6">
        Нажмите на поле, чтобы отредактировать его. После проверки всех данных нажмите «Продолжить».
      </p>

      {/* Fields */}
      <div className="bg-white border border-gray-200 rounded-2xl divide-y divide-gray-100">
        {FIELD_CONFIGS.map((field) => (
          <div key={field.key} className="p-4">
            {editingField === field.key ? (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <label className="text-sm font-medium text-gray-900">{field.label}</label>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={cancelEditing}
                      className="p-1.5 text-gray-500 hover:text-gray-900 hover:bg-gray-100
                                 rounded-lg sidebar-transition"
                    >
                      <X size={16} strokeWidth={2} />
                    </button>
                    {field.type !== 'salary' && (
                      <button
                        onClick={() => saveField(field.key)}
                        className="p-1.5 text-white bg-gray-900 hover:bg-gray-800
                                   rounded-lg sidebar-transition"
                      >
                        <Check size={16} strokeWidth={2} />
                      </button>
                    )}
                  </div>
                </div>
                {renderEditor(field)}
                {field.type === 'salary' && (
                  <div className="flex justify-end">
                    <button
                      onClick={cancelEditing}
                      className="px-4 py-2 text-sm font-medium text-white bg-gray-900
                                 hover:bg-gray-800 rounded-lg sidebar-transition"
                    >
                      Готово
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <button
                onClick={() => startEditing(field)}
                className="w-full text-left group"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <label className="text-sm font-medium text-gray-500 group-hover:text-gray-700
                                      sidebar-transition">
                      {field.label}
                    </label>
                    <div className="mt-1">{renderFieldValue(field)}</div>
                  </div>
                  <div className="p-1.5 text-gray-400 group-hover:text-gray-600 group-hover:bg-gray-100
                                  rounded-lg sidebar-transition ml-4 flex-shrink-0">
                    <Pencil size={16} strokeWidth={2} />
                  </div>
                </div>
              </button>
            )}
          </div>
        ))}
      </div>

      {/* Action Button */}
      <div className="mt-8 flex justify-end">
        <button
          onClick={onNext}
          className="flex items-center gap-2 px-6 py-3 bg-gray-900 text-white
                     rounded-xl font-medium text-sm hover:bg-gray-800 sidebar-transition"
        >
          Продолжить
          <ArrowRight size={18} strokeWidth={2} />
        </button>
      </div>
    </div>
  );
}
