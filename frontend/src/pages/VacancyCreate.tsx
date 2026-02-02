import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { X, Loader2 } from 'lucide-react';
import Breadcrumbs from '../components/Breadcrumbs';
import StepIndicator from '../components/vacancy/StepIndicator';
import UploadStep from '../components/vacancy/UploadStep';
import ChatStep from '../components/vacancy/ChatStep';
import EditStep, { DEFAULT_WEIGHTS, type CriteriaWeights } from '../components/vacancy/EditStep';
import PreviewStep from '../components/vacancy/PreviewStep';
import { calculateWeights, saveVacancy } from '../api/vacancy';
import type { VacancyInput } from '../types/vacancy';

const STEPS = [
  { id: 1, title: 'Загрузка' },
  { id: 2, title: 'Уточнение' },
  { id: 3, title: 'Редактирование' },
  { id: 4, title: 'Предпросмотр' },
];

// Начальное состояние VacancyInput
const initialVacancyInput: VacancyInput = {
  core: {
    jobTitle: '',
  },
};

export default function VacancyCreate() {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(1);
  const [vacancyData, setVacancyData] = useState<VacancyInput>(initialVacancyInput);
  const [showCancelModal, setShowCancelModal] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [completionPercent, setCompletionPercent] = useState(0);
  
  // Веса критериев
  const [criteriaWeights, setCriteriaWeights] = useState<CriteriaWeights>(DEFAULT_WEIGHTS);
  const [isCalculatingWeights, setIsCalculatingWeights] = useState(false);
  const weightsCalculatedRef = useRef(false);
  
  // Сохранение
  const [isSaving, setIsSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  // Функция расчёта весов через API
  const fetchWeights = useCallback(async () => {
    if (!sessionId) return;
    
    setIsCalculatingWeights(true);
    try {
      const result = await calculateWeights(sessionId);
      setCriteriaWeights(result.weights as CriteriaWeights);
    } catch (error) {
      console.error('Failed to calculate weights:', error);
      // Оставляем дефолтные веса в случае ошибки
    } finally {
      setIsCalculatingWeights(false);
    }
  }, [sessionId]);

  // Автоматический расчёт весов при переходе на шаг 3 (EditStep)
  useEffect(() => {
    if (currentStep === 3 && sessionId && !weightsCalculatedRef.current) {
      weightsCalculatedRef.current = true;
      fetchWeights();
    }
  }, [currentStep, sessionId, fetchWeights]);

  // Обработчик пересчёта весов вручную
  const handleRecalculateWeights = useCallback(() => {
    fetchWeights();
  }, [fetchWeights]);

  const handleNextStep = () => {
    if (currentStep < 4) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handleUploadComplete = (
    newSessionId: string,
    parsedData: VacancyInput,
    newCompletionPercent: number
  ) => {
    setSessionId(newSessionId);
    setVacancyData(parsedData);
    setCompletionPercent(newCompletionPercent);
    setCurrentStep(2);
  };

  const handleCancel = () => {
    setShowCancelModal(true);
  };

  const confirmCancel = () => {
    navigate('/vacancy');
  };

  const handleSave = async () => {
    if (!sessionId) {
      setSaveError('Сессия не найдена');
      return;
    }
    
    setIsSaving(true);
    setSaveError(null);
    
    try {
      // Convert CriteriaWeights to Record<string, number>
      const weightsRecord: Record<string, number> = {
        core: criteriaWeights.core,
        company: criteriaWeights.company,
        workConditions: criteriaWeights.workConditions,
        requirements: criteriaWeights.requirements,
        responsibilities: criteriaWeights.responsibilities,
        hiringContext: criteriaWeights.hiringContext,
        successCriteria: criteriaWeights.successCriteria,
        differentiators: criteriaWeights.differentiators,
        dealbreakers: criteriaWeights.dealbreakers,
      };
      
      await saveVacancy(sessionId, weightsRecord);
      navigate('/vacancy');
    } catch (error) {
      console.error('Failed to save vacancy:', error);
      setSaveError(error instanceof Error ? error.message : 'Не удалось сохранить вакансию');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="p-8 min-h-screen bg-gray-50/30">
      <Breadcrumbs
        items={[
          { label: 'Главная', path: '/home' },
          { label: 'Вакансии', path: '/vacancy' },
          { label: 'Создание вакансии' },
        ]}
      />

      {/* Header */}
      <div className="mt-6 mb-8 flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Создание вакансии</h1>
          <p className="text-gray-500 mt-1 text-sm max-w-2xl">
            Загрузите описание вакансии или введите текст вручную. Система проанализирует данные
            и поможет структурировать информацию через уточняющие вопросы.
          </p>
        </div>
        <button
          onClick={handleCancel}
          className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-600
                     hover:text-gray-900 hover:bg-gray-100 rounded-lg sidebar-transition"
        >
          <X size={18} strokeWidth={2} />
          Отменить
        </button>
      </div>

      {/* Step Indicator */}
      <StepIndicator steps={STEPS} currentStep={currentStep} />

      {/* Step Content */}
      <div className="mt-8">
        {currentStep === 1 && (
          <UploadStep
            onNext={handleUploadComplete}
            setVacancyData={setVacancyData}
          />
        )}
        {currentStep === 2 && sessionId && (
          <ChatStep
            sessionId={sessionId}
            onNext={handleNextStep}
            vacancyData={vacancyData}
            setVacancyData={setVacancyData}
            completionPercent={completionPercent}
            setCompletionPercent={setCompletionPercent}
          />
        )}
        {currentStep === 3 && (
          <EditStep
            onNext={handleNextStep}
            vacancyData={vacancyData}
            setVacancyData={setVacancyData}
            completionPercent={completionPercent}
            setCompletionPercent={setCompletionPercent}
            criteriaWeights={criteriaWeights}
            setCriteriaWeights={setCriteriaWeights}
            isCalculatingWeights={isCalculatingWeights}
            onRecalculateWeights={handleRecalculateWeights}
          />
        )}
        {currentStep === 4 && (
          <PreviewStep
            vacancyData={vacancyData}
            onSave={handleSave}
            isSaving={isSaving}
            saveError={saveError}
          />
        )}
      </div>

      {/* Cancel Modal */}
      {showCancelModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl p-6 max-w-md w-full mx-4 shadow-xl">
            <h3 className="text-lg font-semibold text-gray-900">Отменить создание?</h3>
            <p className="text-gray-500 mt-2 text-sm">
              Все введённые данные будут потеряны. Вы уверены, что хотите отменить создание вакансии?
            </p>
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setShowCancelModal(false)}
                className="flex-1 px-4 py-2.5 text-sm font-medium text-gray-700 bg-gray-100
                           hover:bg-gray-200 rounded-xl sidebar-transition"
              >
                Продолжить редактирование
              </button>
              <button
                onClick={confirmCancel}
                className="flex-1 px-4 py-2.5 text-sm font-medium text-white bg-red-600
                           hover:bg-red-700 rounded-xl sidebar-transition"
              >
                Отменить
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
