import { useState, useRef, useEffect, useCallback } from 'react';
import { Send, Bot, User, SkipForward, ArrowRight, CheckCircle, Loader2, AlertCircle } from 'lucide-react';
import { getNextQuestion, batchSubmitAnswers, type EnrichmentQuestion, type BatchAnswerItem } from '../../api';
import type { VacancyInput } from '../../types/vacancy';

interface ChatStepProps {
  sessionId: string;
  onNext: () => void;
  vacancyData: VacancyInput;
  setVacancyData: React.Dispatch<React.SetStateAction<VacancyInput>>;
  completionPercent: number;
  setCompletionPercent: React.Dispatch<React.SetStateAction<number>>;
}

interface Message {
  id: number;
  type: 'bot' | 'user' | 'system';
  content: string;
}

const COMPLETION_THRESHOLD = 85;

export default function ChatStep({
  sessionId,
  onNext,
  vacancyData,
  setVacancyData,
  completionPercent,
  setCompletionPercent,
}: ChatStepProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [currentQuestion, setCurrentQuestion] = useState<EnrichmentQuestion | null>(null);
  // Буфер вопросов - предзагруженные вопросы для мгновенного показа
  const [questionBuffer, setQuestionBuffer] = useState<EnrichmentQuestion[]>([]);
  // Накопленные ответы - отправляются пачкой когда буфер опустеет
  const [pendingAnswers, setPendingAnswers] = useState<BatchAnswerItem[]>([]);
  const [isLoadingQuestion, setIsLoadingQuestion] = useState(false);
  const [customInput, setCustomInput] = useState('');
  const [showCustomInput, setShowCustomInput] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isComplete, setIsComplete] = useState(false);
  const [answeredCount, setAnsweredCount] = useState(0);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const initialLoadDone = useRef(false);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const addMessage = (type: 'bot' | 'user' | 'system', content: string) => {
    setMessages((prev) => [...prev, { id: prev.length + 1, type, content }]);
  };

  // Загрузить начальные вопросы
  const loadInitialQuestions = useCallback(async () => {
    setIsLoadingQuestion(true);
    setError(null);

    try {
      const response = await getNextQuestion(sessionId);
      setCompletionPercent(response.completion_percent);

      if (response.is_complete || response.questions.length === 0) {
        setIsComplete(true);
        setCurrentQuestion(null);
        addMessage('bot', 'Отлично! Все основные поля заполнены. Вы можете перейти к редактированию вакансии.');
      } else {
        // Показываем первый вопрос, остальные в буфер
        const [first, ...rest] = response.questions;
        setCurrentQuestion(first);
        setQuestionBuffer(rest);
        addMessage('bot', first.question_text);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Ошибка загрузки вопросов';
      setError(errorMessage);
      addMessage('system', `Ошибка: ${errorMessage}`);
    } finally {
      setIsLoadingQuestion(false);
    }
  }, [sessionId, setCompletionPercent]);

  // Отправить накопленные ответы и получить новые вопросы
  const flushAnswersAndLoadMore = useCallback(async (answers: BatchAnswerItem[]) => {
    if (answers.length === 0) return;

    setIsLoadingQuestion(true);
    setError(null);

    try {
      const response = await batchSubmitAnswers(sessionId, answers);
      setCompletionPercent(response.completion_percent);

      // Уведомление о достижении порога
      if (response.completion_percent >= COMPLETION_THRESHOLD) {
        addMessage('bot', `Заполненность достигла ${response.completion_percent}%! Этого достаточно для качественного поиска.`);
      }

      if (response.is_complete || response.next_questions.length === 0) {
        setIsComplete(true);
        setCurrentQuestion(null);
        setQuestionBuffer([]);
        addMessage('bot', 'Отлично! Все основные поля заполнены. Вы можете перейти к редактированию вакансии.');
      } else {
        // Показываем первый вопрос, остальные в буфер
        const [first, ...rest] = response.next_questions;
        setCurrentQuestion(first);
        setQuestionBuffer(rest);
        addMessage('bot', first.question_text);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Ошибка отправки ответов';
      setError(errorMessage);
      addMessage('system', `Ошибка: ${errorMessage}`);
    } finally {
      setIsLoadingQuestion(false);
    }
  }, [sessionId, setCompletionPercent]);

  useEffect(() => {
    if (!initialLoadDone.current) {
      initialLoadDone.current = true;

      // Initial greeting message
      const greeting = `Отлично! Я проанализировал описание вакансии "${vacancyData.core?.jobTitle || 'Вакансия'}". Заполненность: ${completionPercent}%. Давайте уточним несколько деталей для улучшения качества поиска.`;
      setMessages([{ id: 1, type: 'bot', content: greeting }]);

      // Load initial questions
      loadInitialQuestions();
    }
  }, [vacancyData.core?.jobTitle, completionPercent, loadInitialQuestions]);

  const handleOptionSelect = async (option: string) => {
    if (!currentQuestion || isSubmitting) return;

    const fieldPath = currentQuestion.field_path;

    // Добавляем ответ в pending
    const newAnswer: BatchAnswerItem = {
      field_path: fieldPath,
      answer: option,
      skip: false,
    };
    const newPendingAnswers = [...pendingAnswers, newAnswer];
    setPendingAnswers(newPendingAnswers);

    // Обновляем UI
    setIsSubmitting(true);
    setCurrentQuestion(null);
    addMessage('user', option);
    setShowCustomInput(false);
    setCustomInput('');
    setAnsweredCount((prev) => prev + 1);

    // Проверяем буфер
    if (questionBuffer.length > 0) {
      // Есть вопросы в буфере - показываем следующий МГНОВЕННО (без API)
      const [next, ...rest] = questionBuffer;
      setCurrentQuestion(next);
      setQuestionBuffer(rest);
      addMessage('bot', next.question_text);
      setIsSubmitting(false);
    } else {
      // Буфер пуст - отправляем ВСЕ накопленные ответы и получаем новые вопросы
      await flushAnswersAndLoadMore(newPendingAnswers);
      setPendingAnswers([]); // Очищаем pending после отправки
      setIsSubmitting(false);
    }
  };

  const handleCustomSubmit = () => {
    if (customInput.trim()) {
      handleOptionSelect(customInput.trim());
    }
  };

  const handleSkip = async () => {
    if (!currentQuestion || isSubmitting) return;

    const fieldPath = currentQuestion.field_path;

    // Добавляем пропуск в pending
    const newAnswer: BatchAnswerItem = {
      field_path: fieldPath,
      answer: '',
      skip: true,
    };
    const newPendingAnswers = [...pendingAnswers, newAnswer];
    setPendingAnswers(newPendingAnswers);

    // Обновляем UI
    setIsSubmitting(true);
    setCurrentQuestion(null);
    addMessage('user', 'Пропущено');
    setShowCustomInput(false);
    setCustomInput('');
    setAnsweredCount((prev) => prev + 1);

    // Проверяем буфер
    if (questionBuffer.length > 0) {
      const [next, ...rest] = questionBuffer;
      setCurrentQuestion(next);
      setQuestionBuffer(rest);
      addMessage('bot', next.question_text);
      setIsSubmitting(false);
    } else {
      await flushAnswersAndLoadMore(newPendingAnswers);
      setPendingAnswers([]);
      setIsSubmitting(false);
    }
  };

  const handleFinishEnrichment = async () => {
    // Если есть несохранённые ответы - отправляем их перед выходом
    if (pendingAnswers.length > 0) {
      setIsSubmitting(true);
      try {
        const response = await batchSubmitAnswers(sessionId, pendingAnswers);
        setCompletionPercent(response.completion_percent);
        setPendingAnswers([]);
      } catch (err) {
        // Игнорируем ошибку при выходе
      }
      setIsSubmitting(false);
    }

    addMessage('bot', 'Переходим к редактированию вакансии.');
    setTimeout(() => {
      onNext();
    }, 300);
  };

  const isHighCompletion = completionPercent >= COMPLETION_THRESHOLD;

  return (
    <div className="max-w-3xl mx-auto">
      {/* Progress Bar */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700">Заполненность вакансии</span>
          <span className={`text-sm font-semibold ${isHighCompletion ? 'text-green-600' : 'text-gray-900'}`}>
            {completionPercent}%
          </span>
        </div>
        <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full sidebar-transition ${isHighCompletion ? 'bg-green-500' : 'bg-gray-900'}`}
            style={{ width: `${completionPercent}%` }}
          />
        </div>
        <div className="flex items-center justify-between mt-1">
          <p className="text-xs text-gray-500">
            Вопросов отвечено: {answeredCount}
            {questionBuffer.length > 0 && (
              <span className="text-gray-400 ml-2">
                (в очереди: {questionBuffer.length})
              </span>
            )}
            {pendingAnswers.length > 0 && (
              <span className="text-blue-500 ml-2">
                (не сохранено: {pendingAnswers.length})
              </span>
            )}
          </p>
          {isHighCompletion && (
            <p className="text-xs text-green-600 font-medium">
              Достаточно для качественного поиска
            </p>
          )}
        </div>
      </div>

      {/* Chat Container */}
      <div className="bg-white border border-gray-200 rounded-2xl overflow-hidden">
        {/* Messages */}
        <div className="h-96 overflow-y-auto p-4 space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex gap-3 ${message.type === 'user' ? 'flex-row-reverse' : ''}`}
            >
              {/* Avatar */}
              {message.type !== 'system' && (
                <div
                  className={`
                    w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0
                    ${message.type === 'bot' ? 'bg-gray-900' : 'bg-gray-200'}
                  `}
                >
                  {message.type === 'bot' ? (
                    <Bot size={16} strokeWidth={2} className="text-white" />
                  ) : (
                    <User size={16} strokeWidth={2} className="text-gray-600" />
                  )}
                </div>
              )}

              {/* Message Content */}
              <div
                className={`
                  max-w-[80%] px-4 py-3 rounded-2xl
                  ${message.type === 'bot'
                    ? 'bg-gray-100 text-gray-900 rounded-tl-md'
                    : message.type === 'user'
                      ? 'bg-gray-900 text-white rounded-tr-md'
                      : 'bg-amber-50 text-amber-800 border border-amber-200 mx-auto text-center text-sm'
                  }
                `}
              >
                <p className="text-sm">{message.content}</p>
              </div>
            </div>
          ))}

          {/* Loading indicator */}
          {isLoadingQuestion && (
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-full bg-gray-900 flex items-center justify-center flex-shrink-0">
                <Bot size={16} strokeWidth={2} className="text-white" />
              </div>
              <div className="bg-gray-100 px-4 py-3 rounded-2xl rounded-tl-md">
                <Loader2 size={18} className="animate-spin text-gray-500" />
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Error Display */}
        {error && (
          <div className="mx-4 mb-4 flex items-center gap-2 p-3 bg-red-50 border border-red-100 rounded-xl text-sm text-red-700">
            <AlertCircle size={18} strokeWidth={2} />
            {error}
          </div>
        )}

        {/* Input Area */}
        {!isComplete && currentQuestion && !isLoadingQuestion && (
          <div className="border-t border-gray-200 p-4 bg-gray-50/50">
            {/* Options */}
            <div className="space-y-2 mb-3">
              {currentQuestion.options.map((option, index) => (
                <button
                  key={index}
                  onClick={() => handleOptionSelect(option.value)}
                  disabled={isSubmitting}
                  className={`
                    w-full text-left px-4 py-3 bg-white border border-gray-200 rounded-xl
                    text-sm text-gray-900 hover:bg-gray-50 hover:border-gray-300
                    sidebar-transition flex items-start justify-between group
                    ${isSubmitting ? 'opacity-50 cursor-not-allowed' : ''}
                  `}
                >
                  <div className="flex-1">
                    <span className="font-medium">{option.value}</span>
                    {option.description && (
                      <p className="text-xs text-gray-500 mt-0.5">{option.description}</p>
                    )}
                  </div>
                  <span className="text-gray-400 group-hover:text-gray-600 sidebar-transition ml-2 flex-shrink-0">
                    {String.fromCharCode(65 + index)}
                  </span>
                </button>
              ))}
            </div>

            {/* Custom Input Toggle */}
            {currentQuestion.allow_custom && !showCustomInput ? (
              <div className="flex gap-2">
                <button
                  onClick={() => setShowCustomInput(true)}
                  disabled={isSubmitting}
                  className={`
                    flex-1 px-4 py-3 border border-dashed border-gray-300 rounded-xl
                    text-sm text-gray-500 hover:text-gray-900 hover:border-gray-400
                    hover:bg-gray-50 sidebar-transition
                    ${isSubmitting ? 'opacity-50 cursor-not-allowed' : ''}
                  `}
                >
                  Указать свой вариант...
                </button>
                <button
                  onClick={handleSkip}
                  disabled={isSubmitting}
                  className={`
                    flex items-center gap-2 px-4 py-3 text-sm text-gray-500
                    hover:text-gray-900 hover:bg-gray-100 rounded-xl sidebar-transition
                    ${isSubmitting ? 'opacity-50 cursor-not-allowed' : ''}
                  `}
                >
                  <SkipForward size={16} strokeWidth={2} />
                  Пропустить
                </button>
              </div>
            ) : showCustomInput ? (
              <div className="flex gap-2">
                <input
                  type="text"
                  value={customInput}
                  onChange={(e) => setCustomInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleCustomSubmit()}
                  placeholder="Введите свой вариант..."
                  disabled={isSubmitting}
                  className="flex-1 px-4 py-3 border border-gray-200 rounded-xl text-sm
                             focus:outline-none focus:ring-2 focus:ring-gray-900/10 focus:border-gray-300
                             disabled:opacity-50"
                  autoFocus
                />
                <button
                  onClick={handleCustomSubmit}
                  disabled={!customInput.trim() || isSubmitting}
                  className={`
                    px-4 py-3 rounded-xl sidebar-transition
                    ${customInput.trim() && !isSubmitting
                      ? 'bg-gray-900 text-white hover:bg-gray-800'
                      : 'bg-gray-200 text-gray-500 cursor-not-allowed'
                    }
                  `}
                >
                  {isSubmitting ? (
                    <Loader2 size={18} className="animate-spin" />
                  ) : (
                    <Send size={18} strokeWidth={2} />
                  )}
                </button>
                <button
                  onClick={() => {
                    setShowCustomInput(false);
                    setCustomInput('');
                  }}
                  disabled={isSubmitting}
                  className="px-4 py-3 text-gray-500 hover:text-gray-900 hover:bg-gray-100
                             rounded-xl sidebar-transition disabled:opacity-50"
                >
                  Отмена
                </button>
              </div>
            ) : (
              <button
                onClick={handleSkip}
                disabled={isSubmitting}
                className={`
                  flex items-center justify-center gap-2 w-full px-4 py-3 text-sm text-gray-500
                  hover:text-gray-900 hover:bg-gray-100 rounded-xl sidebar-transition
                  ${isSubmitting ? 'opacity-50 cursor-not-allowed' : ''}
                `}
              >
                <SkipForward size={16} strokeWidth={2} />
                Пропустить вопрос
              </button>
            )}

            {/* Finish Enrichment Button */}
            <div className="mt-4 pt-4 border-t border-gray-200">
              <button
                onClick={handleFinishEnrichment}
                disabled={isSubmitting}
                className={`
                  w-full flex items-center justify-center gap-2 px-4 py-3
                  rounded-xl font-medium text-sm sidebar-transition
                  ${isHighCompletion
                    ? 'bg-green-600 text-white hover:bg-green-700'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }
                  ${isSubmitting ? 'opacity-50 cursor-not-allowed' : ''}
                `}
              >
                <CheckCircle size={18} strokeWidth={2} />
                {isHighCompletion
                  ? 'Перейти к редактированию'
                  : 'Завершить и перейти к редактированию'
                }
                {pendingAnswers.length > 0 && (
                  <span className="text-xs opacity-75">
                    (сохранить {pendingAnswers.length} ответ{pendingAnswers.length > 1 ? 'а' : ''})
                  </span>
                )}
              </button>
            </div>
          </div>
        )}

        {/* Complete State */}
        {isComplete && (
          <div className="border-t border-gray-200 p-4 bg-gray-50/50">
            <button
              onClick={onNext}
              className="w-full flex items-center justify-center gap-2 px-6 py-3
                         bg-green-600 text-white rounded-xl font-medium text-sm
                         hover:bg-green-700 sidebar-transition"
            >
              Перейти к редактированию
              <ArrowRight size={18} strokeWidth={2} />
            </button>
          </div>
        )}

        {/* Loading State */}
        {isLoadingQuestion && !currentQuestion && messages.length <= 1 && (
          <div className="border-t border-gray-200 p-4 bg-gray-50/50">
            <div className="flex items-center justify-center gap-2 text-gray-500">
              <Loader2 size={18} className="animate-spin" />
              <span className="text-sm">Генерируем вопросы...</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
