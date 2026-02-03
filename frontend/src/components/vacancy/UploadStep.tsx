import { useState, useRef, DragEvent, ChangeEvent } from 'react';
import { Upload, Type, AlertCircle, File, X, Info, ArrowRight, XCircle, Sparkles } from 'lucide-react';
import { createSession, uploadText, uploadFile, type ParseResponse } from '../../api';
import type { VacancyInput } from '../../types/vacancy';
import AnalyzingAnimation from './AnalyzingAnimation';

// Компонент Toggle Switch
interface ToggleSwitchProps {
  enabled: boolean;
  onChange: (enabled: boolean) => void;
  disabled?: boolean;
}

function ToggleSwitch({ enabled, onChange, disabled }: ToggleSwitchProps) {
  return (
    <button
      type="button"
      onClick={() => !disabled && onChange(!enabled)}
      disabled={disabled}
      className={`
        relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent
        transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-gray-900/20
        ${enabled ? 'bg-gray-900' : 'bg-gray-200'}
        ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
      `}
    >
      <span
        className={`
          pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0
          transition duration-200 ease-in-out
          ${enabled ? 'translate-x-5' : 'translate-x-0'}
        `}
      />
    </button>
  );
}

// Компонент модального окна для невалидного документа
interface ValidationErrorModalProps {
  isOpen: boolean;
  message: string;
  onClose: () => void;
}

function ValidationErrorModal({ isOpen, message, onClose }: ValidationErrorModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />
      
      {/* Modal */}
      <div className="relative bg-white rounded-2xl shadow-xl max-w-md w-full mx-4 p-6 animate-in fade-in zoom-in duration-200">
        <div className="flex flex-col items-center text-center">
          {/* Icon */}
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mb-4">
            <XCircle size={32} className="text-red-600" />
          </div>
          
          {/* Title */}
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            Невозможно создать вакансию
          </h3>
          
          {/* Message */}
          <p className="text-gray-600 mb-6">
            {message}
          </p>
          
          {/* Button */}
          <button
            onClick={onClose}
            className="w-full px-6 py-3 bg-gray-900 text-white rounded-xl font-medium hover:bg-gray-800 transition-colors"
          >
            Понятно
          </button>
        </div>
      </div>
    </div>
  );
}

type InputMode = 'file' | 'text';

interface UploadStepProps {
  onNext: (sessionId: string, parsedData: VacancyInput, completionPercent: number, wantsOverview: boolean) => void;
  setVacancyData: React.Dispatch<React.SetStateAction<VacancyInput>>;
}

const ALLOWED_TYPES = [
  'application/pdf',
  'application/msword',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'text/plain',
];

const ALLOWED_EXTENSIONS = ['.pdf', '.doc', '.docx', '.txt'];
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10 MB

export default function UploadStep({ onNext, setVacancyData }: UploadStepProps) {
  const [mode, setMode] = useState<InputMode>('file');
  const [isDragging, setIsDragging] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [text, setText] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  // Состояние для обзора вакансии
  const [wantsOverview, setWantsOverview] = useState(true);
  
  // Состояние для модального окна валидации
  const [showValidationModal, setShowValidationModal] = useState(false);
  const [validationError, setValidationError] = useState<string>('');

  const validateFile = (file: File): string | null => {
    if (!ALLOWED_TYPES.includes(file.type) && !file.name.match(/\.(pdf|docx?|txt)$/i)) {
      return 'Неподдерживаемый формат файла. Используйте PDF, Word или TXT.';
    }
    if (file.size > MAX_FILE_SIZE) {
      return 'Файл слишком большой. Максимальный размер — 10 МБ.';
    }
    return null;
  };

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    setError(null);

    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      const validationError = validateFile(droppedFile);
      if (validationError) {
        setError(validationError);
        return;
      }
      setFile(droppedFile);
    }
  };

  const handleFileSelect = (e: ChangeEvent<HTMLInputElement>) => {
    setError(null);
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      const validationError = validateFile(selectedFile);
      if (validationError) {
        setError(validationError);
        return;
      }
      setFile(selectedFile);
    }
  };

  const handleRemoveFile = () => {
    setFile(null);
    setError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const canProceed = mode === 'file' ? file !== null : text.trim().length > 0;

  const handleSubmit = async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Создаём сессию
      const session = await createSession();

      // Загружаем и парсим
      let result: ParseResponse;
      if (mode === 'file' && file) {
        result = await uploadFile(session.session_id, file);
      } else {
        result = await uploadText(session.session_id, text);
      }

      // Проверяем валидность документа
      if (!result.is_valid || !result.parsed_data) {
        setIsLoading(false);
        setValidationError(
          result.validation_error || 
          'По предоставленным данным нельзя сформировать вакансию. Попробуйте загрузить еще раз или изменить запрос.'
        );
        setShowValidationModal(true);
        return;
      }

      // Сохраняем parsed_data напрямую как VacancyInput
      setVacancyData(result.parsed_data);

      // Переходим к следующему шагу (Overview или ChatStep)
      onNext(result.session_id, result.parsed_data, result.completion_percent, wantsOverview);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Произошла ошибка при обработке');
      setIsLoading(false);
    }
  };

  const handleCloseValidationModal = () => {
    setShowValidationModal(false);
    setValidationError('');
    // Очищаем поля ввода
    setFile(null);
    setText('');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Показываем анимацию во время анализа
  if (isLoading) {
    return (
      <div className="max-w-3xl mx-auto">
        <AnalyzingAnimation
          message={mode === 'file' ? 'Анализируем файл...' : 'Анализируем текст...'}
        />
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto">
      {/* Info Banner */}
      <div className="mb-6 p-4 bg-blue-50 border border-blue-100 rounded-xl flex gap-3">
        <Info size={20} strokeWidth={2} className="text-blue-600 flex-shrink-0 mt-0.5" />
        <div className="text-sm text-blue-800">
          <p className="font-medium">Как это работает?</p>
          <p className="mt-1 text-blue-700">
            Загрузите файл с описанием вакансии или введите текст вручную. Система проанализирует
            содержимое с помощью ИИ и извлечёт структурированные данные для заполнения вакансии.
          </p>
        </div>
      </div>

      {/* Overview Toggle */}
      <div className="mb-6 p-4 bg-gradient-to-r from-purple-50 to-indigo-50 border border-purple-100 rounded-xl">
        <div className="flex items-start justify-between gap-4">
          <div className="flex gap-3">
            <div className="w-10 h-10 bg-purple-100 rounded-xl flex items-center justify-center flex-shrink-0">
              <Sparkles size={20} strokeWidth={2} className="text-purple-600" />
            </div>
            <div>
              <p className="font-medium text-gray-900">Обзор роли и компании</p>
              <p className="text-sm text-gray-600 mt-1">
                ИИ подготовит краткую справку о профессии, компании и отрасли. 
                Поможет лучше понять контекст вакансии перед уточнением деталей.
              </p>
            </div>
          </div>
          <ToggleSwitch
            enabled={wantsOverview}
            onChange={setWantsOverview}
            disabled={isLoading}
          />
        </div>
      </div>

      {/* Mode Switcher */}
      <div className="bg-gray-100 p-1 rounded-xl inline-flex mb-6">
        <button
          onClick={() => {
            setMode('file');
            setError(null);
          }}
          disabled={isLoading}
          className={`
            flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium sidebar-transition
            ${mode === 'file'
              ? 'bg-white text-gray-900 shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
            }
            ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}
          `}
        >
          <Upload size={18} strokeWidth={2} />
          Загрузить файл
        </button>
        <button
          onClick={() => {
            setMode('text');
            setError(null);
          }}
          disabled={isLoading}
          className={`
            flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium sidebar-transition
            ${mode === 'text'
              ? 'bg-white text-gray-900 shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
            }
            ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}
          `}
        >
          <Type size={18} strokeWidth={2} />
          Ввести текст
        </button>
      </div>

      {/* File Upload Mode */}
      {mode === 'file' && (
        <div className="space-y-4">
          {!file ? (
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => !isLoading && fileInputRef.current?.click()}
              className={`
                border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer
                sidebar-transition
                ${isDragging
                  ? 'border-gray-900 bg-gray-50'
                  : 'border-gray-300 hover:border-gray-400 hover:bg-gray-50/50'
                }
                ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}
              `}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept={ALLOWED_EXTENSIONS.join(',')}
                onChange={handleFileSelect}
                className="hidden"
                disabled={isLoading}
              />
              <div className="flex flex-col items-center">
                <div
                  className={`
                    w-16 h-16 rounded-2xl flex items-center justify-center mb-4
                    sidebar-transition
                    ${isDragging ? 'bg-gray-900' : 'bg-gray-100'}
                  `}
                >
                  <Upload
                    size={28}
                    strokeWidth={2}
                    className={isDragging ? 'text-white' : 'text-gray-500'}
                  />
                </div>
                <p className="text-gray-900 font-medium">
                  {isDragging ? 'Отпустите файл здесь' : 'Перетащите файл сюда'}
                </p>
                <p className="text-gray-500 text-sm mt-1">
                  или <span className="text-gray-900 underline">выберите на компьютере</span>
                </p>
                <p className="text-gray-400 text-xs mt-4">
                  PDF, Word, TXT • Максимум 10 МБ
                </p>
              </div>
            </div>
          ) : (
            <div className="border border-gray-200 rounded-2xl p-4 bg-white">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-gray-100 rounded-xl flex items-center justify-center">
                    <File size={20} strokeWidth={2} className="text-gray-500" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-900">{file.name}</p>
                    <p className="text-xs text-gray-500">{formatFileSize(file.size)}</p>
                  </div>
                </div>
                <button
                  onClick={handleRemoveFile}
                  disabled={isLoading}
                  className="p-2 hover:bg-gray-100 rounded-lg sidebar-transition disabled:opacity-50"
                >
                  <X size={18} strokeWidth={2} className="text-gray-500" />
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Text Input Mode */}
      {mode === 'text' && (
        <div className="space-y-4">
          <div className="relative">
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              disabled={isLoading}
              placeholder="Вставьте или введите описание вакансии...

Например:
Требуется Senior Frontend разработчик с опытом работы от 4 лет.
Обязанности: разработка UI компонентов, код-ревью, менторинг.
Требования: React, TypeScript, опыт с REST API..."
              className="w-full h-64 p-4 border border-gray-200 rounded-2xl resize-none
                         text-gray-900 placeholder:text-gray-400
                         focus:outline-none focus:ring-2 focus:ring-gray-900/10 focus:border-gray-300
                         sidebar-transition disabled:opacity-50 disabled:cursor-not-allowed"
            />
            <div className="absolute bottom-3 right-3 text-xs text-gray-400">
              {text.length} символов
            </div>
          </div>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="mt-4 flex items-center gap-2 p-3 bg-red-50 border border-red-100 rounded-xl text-sm text-red-700">
          <AlertCircle size={18} strokeWidth={2} />
          {error}
        </div>
      )}

      {/* Action Buttons */}
      <div className="mt-8 flex justify-end gap-3">
        <button
          onClick={handleSubmit}
          disabled={!canProceed}
          className={`
            flex items-center gap-2 px-6 py-3 rounded-xl font-medium text-sm
            sidebar-transition
            ${canProceed
              ? 'bg-gray-900 text-white hover:bg-gray-800'
              : 'bg-gray-200 text-gray-500 cursor-not-allowed'
            }
          `}
        >
          Анализировать
          <ArrowRight size={18} strokeWidth={2} />
        </button>
      </div>

      {/* Модальное окно ошибки валидации */}
      <ValidationErrorModal
        isOpen={showValidationModal}
        message={validationError}
        onClose={handleCloseValidationModal}
      />
    </div>
  );
}
