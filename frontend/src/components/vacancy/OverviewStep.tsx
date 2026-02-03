import { useState, useEffect } from 'react';
import { 
  ArrowRight, 
  Briefcase, 
  Building2, 
  TrendingUp, 
  ClipboardList,
  ExternalLink,
  Loader2,
  AlertCircle,
  RefreshCw
} from 'lucide-react';
import { generateOverview, type OverviewData } from '../../api';

interface OverviewStepProps {
  sessionId: string;
  jobTitle: string;
  companyName?: string;
  onNext: () => void;
}

interface OverviewCardProps {
  icon: React.ReactNode;
  title: string;
  content: string | string[];
  className?: string;
}

function OverviewCard({ icon, title, content, className = '' }: OverviewCardProps) {
  const isArray = Array.isArray(content);
  
  return (
    <div className={`bg-white rounded-2xl border border-gray-200 p-5 ${className}`}>
      <div className="flex items-center gap-3 mb-3">
        <div className="w-10 h-10 bg-gray-100 rounded-xl flex items-center justify-center">
          {icon}
        </div>
        <h3 className="font-semibold text-gray-900">{title}</h3>
      </div>
      {isArray ? (
        <ul className="space-y-2">
          {(content as string[]).map((item, index) => (
            <li key={index} className="flex items-start gap-2 text-sm text-gray-600">
              <span className="text-gray-400 mt-1">•</span>
              <span>{item}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-gray-600 leading-relaxed">{content}</p>
      )}
    </div>
  );
}

function LoadingState() {
  return (
    <div className="max-w-4xl mx-auto">
      <div className="text-center py-16">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-purple-100 rounded-2xl mb-6">
          <Loader2 size={32} className="text-purple-600 animate-spin" />
        </div>
        <h2 className="text-xl font-semibold text-gray-900 mb-2">
          Собираем информацию...
        </h2>
        <p className="text-gray-500 max-w-md mx-auto">
          ИИ анализирует вакансию и ищет актуальную информацию о компании и отрасли. 
          Это займёт несколько секунд.
        </p>
        
        {/* Animated dots */}
        <div className="flex justify-center gap-2 mt-8">
          <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
          <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
          <div className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
        </div>
      </div>
    </div>
  );
}

interface ErrorStateProps {
  message: string;
  onRetry: () => void;
  onSkip: () => void;
}

function ErrorState({ message, onRetry, onSkip }: ErrorStateProps) {
  return (
    <div className="max-w-4xl mx-auto">
      <div className="text-center py-16">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-red-100 rounded-2xl mb-6">
          <AlertCircle size={32} className="text-red-600" />
        </div>
        <h2 className="text-xl font-semibold text-gray-900 mb-2">
          Не удалось загрузить обзор
        </h2>
        <p className="text-gray-500 max-w-md mx-auto mb-8">
          {message}
        </p>
        <div className="flex justify-center gap-3">
          <button
            onClick={onRetry}
            className="flex items-center gap-2 px-5 py-2.5 bg-gray-100 text-gray-700 rounded-xl 
                       font-medium text-sm hover:bg-gray-200 transition-colors"
          >
            <RefreshCw size={18} />
            Попробовать снова
          </button>
          <button
            onClick={onSkip}
            className="flex items-center gap-2 px-5 py-2.5 bg-gray-900 text-white rounded-xl 
                       font-medium text-sm hover:bg-gray-800 transition-colors"
          >
            Пропустить
            <ArrowRight size={18} />
          </button>
        </div>
      </div>
    </div>
  );
}

export default function OverviewStep({ sessionId, jobTitle, companyName, onNext }: OverviewStepProps) {
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [overviewData, setOverviewData] = useState<OverviewData | null>(null);
  const [sources, setSources] = useState<string[] | null>(null);

  const fetchOverview = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await generateOverview(sessionId);
      setOverviewData(response.data);
      setSources(response.sources);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Произошла ошибка при загрузке обзора');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchOverview();
  }, [sessionId]);

  if (isLoading) {
    return <LoadingState />;
  }

  if (error) {
    return (
      <ErrorState 
        message={error} 
        onRetry={fetchOverview}
        onSkip={onNext}
      />
    );
  }

  if (!overviewData) {
    return (
      <ErrorState 
        message="Не удалось получить данные обзора" 
        onRetry={fetchOverview}
        onSkip={onNext}
      />
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <h2 className="text-xl font-semibold text-gray-900">
            {jobTitle}
          </h2>
          {companyName && (
            <>
              <span className="text-gray-300">•</span>
              <span className="text-gray-600">{companyName}</span>
            </>
          )}
        </div>
        <p className="text-gray-500 text-sm">
          Краткий обзор роли, компании и отрасли для лучшего понимания контекста вакансии
        </p>
      </div>

      {/* Overview Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        {/* Role Description */}
        <OverviewCard
          icon={<Briefcase size={20} className="text-gray-600" />}
          title="О профессии"
          content={overviewData.role_description}
        />

        {/* Company Overview (if available) */}
        {overviewData.company_overview && (
          <OverviewCard
            icon={<Building2 size={20} className="text-gray-600" />}
            title="О компании"
            content={overviewData.company_overview}
          />
        )}

        {/* Industry Context */}
        <OverviewCard
          icon={<TrendingUp size={20} className="text-gray-600" />}
          title="Контекст отрасли"
          content={overviewData.industry_context}
          className={!overviewData.company_overview ? 'md:col-span-1' : ''}
        />

        {/* Business Processes */}
        <OverviewCard
          icon={<ClipboardList size={20} className="text-gray-600" />}
          title="Типичные бизнес-процессы"
          content={overviewData.business_processes}
          className={overviewData.company_overview ? 'md:col-span-2' : ''}
        />
      </div>

      {/* Sources (if available) */}
      {sources && sources.length > 0 && (
        <div className="mb-6 p-4 bg-gray-50 rounded-xl">
          <p className="text-xs text-gray-500 mb-2 font-medium">Источники информации:</p>
          <div className="flex flex-wrap gap-2">
            {sources.map((source, index) => (
              <a
                key={index}
                href={source}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 px-2 py-1 bg-white border border-gray-200 
                           rounded-lg text-xs text-gray-600 hover:border-gray-300 hover:text-gray-900 
                           transition-colors"
              >
                <ExternalLink size={12} />
                {new URL(source).hostname}
              </a>
            ))}
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex justify-end gap-3">
        <button
          onClick={onNext}
          className="flex items-center gap-2 px-6 py-3 bg-gray-900 text-white rounded-xl 
                     font-medium text-sm hover:bg-gray-800 transition-colors"
        >
          Продолжить
          <ArrowRight size={18} />
        </button>
      </div>
    </div>
  );
}
