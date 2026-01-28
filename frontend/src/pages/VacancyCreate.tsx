import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { X } from 'lucide-react';
import Breadcrumbs from '../components/Breadcrumbs';
import StepIndicator from '../components/vacancy/StepIndicator';
import UploadStep from '../components/vacancy/UploadStep';
import ChatStep from '../components/vacancy/ChatStep';
import EditStep from '../components/vacancy/EditStep';
import PreviewStep from '../components/vacancy/PreviewStep';

const STEPS = [
  { id: 1, title: 'Загрузка' },
  { id: 2, title: 'Уточнение' },
  { id: 3, title: 'Редактирование' },
  { id: 4, title: 'Предпросмотр' },
];

export interface VacancyData {
  title: string;
  department: string;
  location: string;
  employmentType: string;
  experienceLevel: string;
  salaryFrom: string;
  salaryTo: string;
  currency: string;
  description: string;
  responsibilities: string[];
  requirements: string[];
  niceToHave: string[];
  benefits: string[];
}

const initialVacancyData: VacancyData = {
  title: '',
  department: '',
  location: '',
  employmentType: '',
  experienceLevel: '',
  salaryFrom: '',
  salaryTo: '',
  currency: 'RUB',
  description: '',
  responsibilities: [],
  requirements: [],
  niceToHave: [],
  benefits: [],
};

export default function VacancyCreate() {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(1);
  const [vacancyData, setVacancyData] = useState<VacancyData>(initialVacancyData);
  const [showCancelModal, setShowCancelModal] = useState(false);

  const handleNextStep = () => {
    if (currentStep < 4) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handleCancel = () => {
    setShowCancelModal(true);
  };

  const confirmCancel = () => {
    navigate('/vacancy');
  };

  const handleSave = () => {
    // Симуляция сохранения
    navigate('/vacancy');
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
            onNext={handleNextStep}
            setVacancyData={setVacancyData}
          />
        )}
        {currentStep === 2 && (
          <ChatStep
            onNext={handleNextStep}
            vacancyData={vacancyData}
            setVacancyData={setVacancyData}
          />
        )}
        {currentStep === 3 && (
          <EditStep
            onNext={handleNextStep}
            vacancyData={vacancyData}
            setVacancyData={setVacancyData}
          />
        )}
        {currentStep === 4 && (
          <PreviewStep
            vacancyData={vacancyData}
            onSave={handleSave}
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
