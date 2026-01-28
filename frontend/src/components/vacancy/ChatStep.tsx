import { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, SkipForward, ArrowRight } from 'lucide-react';
import type { VacancyData } from '../../pages/VacancyCreate';

interface ChatStepProps {
  onNext: () => void;
  vacancyData: VacancyData;
  setVacancyData: React.Dispatch<React.SetStateAction<VacancyData>>;
}

interface Question {
  id: number;
  text: string;
  field: string;
  options: string[];
  answered: boolean;
  selectedOption?: string;
  customAnswer?: string;
}

interface Message {
  id: number;
  type: 'bot' | 'user';
  content: string;
  question?: Question;
}

const QUESTIONS: Omit<Question, 'answered'>[] = [
  {
    id: 1,
    text: 'Какой формат занятости предполагается для этой позиции?',
    field: 'employmentType',
    options: ['Полная занятость (офис)', 'Полная занятость (удалённо)', 'Гибрид'],
  },
  {
    id: 2,
    text: 'Какой уровень опыта требуется от кандидата?',
    field: 'experienceLevel',
    options: ['Junior (1-2 года)', 'Middle (2-4 года)', 'Senior (4+ лет)'],
  },
  {
    id: 3,
    text: 'В каком отделе будет работать сотрудник?',
    field: 'department',
    options: ['Разработка (Engineering)', 'Продукт (Product)', 'Дизайн (Design)'],
  },
  {
    id: 4,
    text: 'Какие дополнительные навыки будут преимуществом?',
    field: 'niceToHave',
    options: ['Опыт работы с Next.js', 'Знание Node.js', 'Опыт с микросервисами'],
  },
  {
    id: 5,
    text: 'Какие бенефиты предлагает компания?',
    field: 'benefits',
    options: ['ДМС со стоматологией', 'Гибкий график', 'Компенсация обучения'],
  },
];

export default function ChatStep({ onNext, vacancyData, setVacancyData }: ChatStepProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [customInput, setCustomInput] = useState('');
  const [showCustomInput, setShowCustomInput] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const totalQuestions = QUESTIONS.length;
  const answeredQuestions = currentQuestionIndex;
  const progress = Math.round((answeredQuestions / totalQuestions) * 100);

  const isComplete = currentQuestionIndex >= totalQuestions;

  useEffect(() => {
    // Инициализация первого сообщения и вопроса
    if (messages.length === 0) {
      const initialMessages: Message[] = [
        {
          id: 1,
          type: 'bot',
          content: `Отлично! Я проанализировал описание вакансии "${vacancyData.title || 'Senior Frontend Developer'}". Теперь мне нужно уточнить несколько деталей для формирования полного описания. Выберите подходящий вариант или укажите свой.`,
        },
        {
          id: 2,
          type: 'bot',
          content: QUESTIONS[0].text,
          question: { ...QUESTIONS[0], answered: false },
        },
      ];
      setMessages(initialMessages);
    }
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleOptionSelect = (option: string) => {
    // Добавляем ответ пользователя
    const userMessage: Message = {
      id: messages.length + 1,
      type: 'user',
      content: option,
    };

    setMessages((prev) => [...prev, userMessage]);
    setShowCustomInput(false);
    setCustomInput('');

    // Переходим к следующему вопросу или завершаем
    const nextIndex = currentQuestionIndex + 1;
    setCurrentQuestionIndex(nextIndex);

    if (nextIndex < totalQuestions) {
      const nextQuestion = QUESTIONS[nextIndex];
      const botMessage: Message = {
        id: messages.length + 2,
        type: 'bot',
        content: nextQuestion.text,
        question: { ...nextQuestion, answered: false },
      };
      setMessages((prev) => [...prev, botMessage]);
    } else {
      const completeMessage: Message = {
        id: messages.length + 2,
        type: 'bot',
        content: 'Спасибо! Я собрал всю необходимую информацию. Теперь вы можете перейти к редактированию и проверить все поля вакансии.',
      };
      setMessages((prev) => [...prev, completeMessage]);
    }
  };

  const handleCustomSubmit = () => {
    if (customInput.trim()) {
      handleOptionSelect(customInput.trim());
    }
  };

  const handleSkip = () => {
    handleOptionSelect('Пропущено');
  };

  const currentQuestion = currentQuestionIndex < totalQuestions ? QUESTIONS[currentQuestionIndex] : null;

  return (
    <div className="max-w-3xl mx-auto">
      {/* Progress Bar */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700">Прогресс уточнения</span>
          <span className="text-sm font-semibold text-gray-900">{progress}%</span>
        </div>
        <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
          <div
            className="h-full bg-gray-900 rounded-full sidebar-transition"
            style={{ width: `${progress}%` }}
          />
        </div>
        <p className="text-xs text-gray-500 mt-1">
          Вопрос {Math.min(currentQuestionIndex + 1, totalQuestions)} из {totalQuestions}
        </p>
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

              {/* Message Content */}
              <div
                className={`
                  max-w-[80%] px-4 py-3 rounded-2xl
                  ${message.type === 'bot'
                    ? 'bg-gray-100 text-gray-900 rounded-tl-md'
                    : 'bg-gray-900 text-white rounded-tr-md'
                  }
                `}
              >
                <p className="text-sm">{message.content}</p>
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        {!isComplete && currentQuestion && (
          <div className="border-t border-gray-200 p-4 bg-gray-50/50">
            {/* Options */}
            <div className="space-y-2 mb-3">
              {currentQuestion.options.map((option, index) => (
                <button
                  key={index}
                  onClick={() => handleOptionSelect(option)}
                  className="w-full text-left px-4 py-3 bg-white border border-gray-200 rounded-xl
                             text-sm text-gray-900 hover:bg-gray-50 hover:border-gray-300
                             sidebar-transition flex items-center justify-between group"
                >
                  <span>{option}</span>
                  <span className="text-gray-400 group-hover:text-gray-600 sidebar-transition">
                    {String.fromCharCode(65 + index)}
                  </span>
                </button>
              ))}
            </div>

            {/* Custom Input Toggle */}
            {!showCustomInput ? (
              <div className="flex gap-2">
                <button
                  onClick={() => setShowCustomInput(true)}
                  className="flex-1 px-4 py-3 border border-dashed border-gray-300 rounded-xl
                             text-sm text-gray-500 hover:text-gray-900 hover:border-gray-400
                             hover:bg-gray-50 sidebar-transition"
                >
                  Указать свой вариант...
                </button>
                <button
                  onClick={handleSkip}
                  className="flex items-center gap-2 px-4 py-3 text-sm text-gray-500
                             hover:text-gray-900 hover:bg-gray-100 rounded-xl sidebar-transition"
                >
                  <SkipForward size={16} strokeWidth={2} />
                  Пропустить
                </button>
              </div>
            ) : (
              <div className="flex gap-2">
                <input
                  type="text"
                  value={customInput}
                  onChange={(e) => setCustomInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleCustomSubmit()}
                  placeholder="Введите свой вариант..."
                  className="flex-1 px-4 py-3 border border-gray-200 rounded-xl text-sm
                             focus:outline-none focus:ring-2 focus:ring-gray-900/10 focus:border-gray-300"
                  autoFocus
                />
                <button
                  onClick={handleCustomSubmit}
                  disabled={!customInput.trim()}
                  className={`
                    px-4 py-3 rounded-xl sidebar-transition
                    ${customInput.trim()
                      ? 'bg-gray-900 text-white hover:bg-gray-800'
                      : 'bg-gray-200 text-gray-500 cursor-not-allowed'
                    }
                  `}
                >
                  <Send size={18} strokeWidth={2} />
                </button>
                <button
                  onClick={() => {
                    setShowCustomInput(false);
                    setCustomInput('');
                  }}
                  className="px-4 py-3 text-gray-500 hover:text-gray-900 hover:bg-gray-100
                             rounded-xl sidebar-transition"
                >
                  Отмена
                </button>
              </div>
            )}
          </div>
        )}

        {/* Complete State */}
        {isComplete && (
          <div className="border-t border-gray-200 p-4 bg-gray-50/50">
            <button
              onClick={onNext}
              className="w-full flex items-center justify-center gap-2 px-6 py-3
                         bg-gray-900 text-white rounded-xl font-medium text-sm
                         hover:bg-gray-800 sidebar-transition"
            >
              Перейти к редактированию
              <ArrowRight size={18} strokeWidth={2} />
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
