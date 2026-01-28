import { useState, useRef, DragEvent, ChangeEvent } from 'react';
import { Upload, FileText, Type, AlertCircle, File, X, Info, ArrowRight } from 'lucide-react';
import type { VacancyData } from '../../pages/VacancyCreate';

type InputMode = 'file' | 'text';

interface UploadStepProps {
  onNext: () => void;
  setVacancyData: React.Dispatch<React.SetStateAction<VacancyData>>;
}

const ALLOWED_TYPES = [
  'application/pdf',
  'application/msword',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'text/plain',
];

const ALLOWED_EXTENSIONS = ['.pdf', '.doc', '.docx', '.txt'];
const MAX_FILE_SIZE = 2 * 1024 * 1024; // 2 MB

export default function UploadStep({ onNext, setVacancyData }: UploadStepProps) {
  const [mode, setMode] = useState<InputMode>('file');
  const [isDragging, setIsDragging] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [text, setText] = useState('');
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateFile = (file: File): string | null => {
    if (!ALLOWED_TYPES.includes(file.type)) {
      return 'Неподдерживаемый формат файла. Используйте PDF, Word или TXT.';
    }
    if (file.size > MAX_FILE_SIZE) {
      return 'Файл слишком большой. Максимальный размер — 2 МБ.';
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

  const getFileIcon = (fileName: string) => {
    const ext = fileName.split('.').pop()?.toLowerCase();
    return <File size={20} strokeWidth={2} className="text-gray-500" />;
  };

  const canProceed = mode === 'file' ? file !== null : text.trim().length > 50;

  const handleNext = () => {
    // Симуляция данных после обработки
    setVacancyData({
      title: 'Senior Frontend Developer',
      department: 'Engineering',
      location: 'Москва',
      employmentType: 'full-time',
      experienceLevel: 'senior',
      salaryFrom: '250000',
      salaryTo: '400000',
      currency: 'RUB',
      description: 'Мы ищем опытного Frontend разработчика для работы над высоконагруженными проектами.',
      responsibilities: [
        'Разработка и поддержка пользовательских интерфейсов',
        'Код-ревью и менторинг младших разработчиков',
        'Участие в архитектурных решениях',
      ],
      requirements: [
        'Опыт работы с React от 4 лет',
        'Глубокое знание TypeScript',
        'Опыт работы с REST API и GraphQL',
      ],
      niceToHave: [
        'Опыт работы с Next.js',
        'Знание принципов CI/CD',
      ],
      benefits: [
        'Гибкий график работы',
        'ДМС со стоматологией',
        'Компенсация обучения',
      ],
    });
    onNext();
  };

  return (
    <div className="max-w-3xl mx-auto">
      {/* Info Banner */}
      <div className="mb-6 p-4 bg-blue-50 border border-blue-100 rounded-xl flex gap-3">
        <Info size={20} strokeWidth={2} className="text-blue-600 flex-shrink-0 mt-0.5" />
        <div className="text-sm text-blue-800">
          <p className="font-medium">Как это работает?</p>
          <p className="mt-1 text-blue-700">
            Загрузите файл с описанием вакансии или введите текст вручную. Система проанализирует
            содержимое и предложит уточняющие вопросы в формате теста для заполнения всех
            необходимых полей вакансии.
          </p>
        </div>
      </div>

      {/* Mode Switcher */}
      <div className="bg-gray-100 p-1 rounded-xl inline-flex mb-6">
        <button
          onClick={() => {
            setMode('file');
            setError(null);
          }}
          className={`
            flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium sidebar-transition
            ${mode === 'file'
              ? 'bg-white text-gray-900 shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
            }
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
          className={`
            flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium sidebar-transition
            ${mode === 'text'
              ? 'bg-white text-gray-900 shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
            }
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
              onClick={() => fileInputRef.current?.click()}
              className={`
                border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer
                sidebar-transition
                ${isDragging
                  ? 'border-gray-900 bg-gray-50'
                  : 'border-gray-300 hover:border-gray-400 hover:bg-gray-50/50'
                }
              `}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept={ALLOWED_EXTENSIONS.join(',')}
                onChange={handleFileSelect}
                className="hidden"
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
                  PDF, Word, TXT • Максимум 2 МБ
                </p>
              </div>
            </div>
          ) : (
            <div className="border border-gray-200 rounded-2xl p-4 bg-white">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-gray-100 rounded-xl flex items-center justify-center">
                    {getFileIcon(file.name)}
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-900">{file.name}</p>
                    <p className="text-xs text-gray-500">{formatFileSize(file.size)}</p>
                  </div>
                </div>
                <button
                  onClick={handleRemoveFile}
                  className="p-2 hover:bg-gray-100 rounded-lg sidebar-transition"
                >
                  <X size={18} strokeWidth={2} className="text-gray-500" />
                </button>
              </div>
            </div>
          )}

          {error && (
            <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-100 rounded-xl text-sm text-red-700">
              <AlertCircle size={18} strokeWidth={2} />
              {error}
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
              placeholder="Вставьте или введите описание вакансии...

Например:
Требуется Senior Frontend разработчик с опытом работы от 4 лет.
Обязанности: разработка UI компонентов, код-ревью, менторинг.
Требования: React, TypeScript, опыт с REST API..."
              className="w-full h-64 p-4 border border-gray-200 rounded-2xl resize-none
                         text-gray-900 placeholder:text-gray-400
                         focus:outline-none focus:ring-2 focus:ring-gray-900/10 focus:border-gray-300
                         sidebar-transition"
            />
            <div className="absolute bottom-3 right-3 text-xs text-gray-400">
              {text.length} символов
            </div>
          </div>
          {text.length > 0 && text.length < 50 && (
            <p className="text-sm text-amber-600 flex items-center gap-2">
              <AlertCircle size={16} strokeWidth={2} />
              Введите минимум 50 символов для анализа
            </p>
          )}
        </div>
      )}

      {/* Action Button */}
      <div className="mt-8 flex justify-end">
        <button
          onClick={handleNext}
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
          Продолжить
          <ArrowRight size={18} strokeWidth={2} />
        </button>
      </div>
    </div>
  );
}
