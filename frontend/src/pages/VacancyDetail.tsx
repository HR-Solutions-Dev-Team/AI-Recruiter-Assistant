import { useState, useEffect, useRef, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { 
  Users, 
  FileText, 
  ChevronDown, 
  ChevronUp, 
  Upload, 
  MapPin, 
  Building2, 
  Wallet, 
  Calendar,
  Clock,
  Briefcase,
  Target,
  ShieldAlert,
  Award,
  Network,
  MessageCircleQuestion,
  TrendingUp,
  AlertCircle,
  CheckCircle2,
  Loader2,
  RefreshCw
} from 'lucide-react';
import Breadcrumbs from '../components/Breadcrumbs';
import { getVacancy } from '../api/vacancy';
import { uploadResume, getVacancyCandidates, CandidateMatch } from '../api/resume';

export default function VacancyDetail() {
  const { id } = useParams();
  const [activeTab, setActiveTab] = useState<'vacancy' | 'candidates'>('vacancy');
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [vacancy, setVacancy] = useState<any | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  
  // Candidates state
  const [candidates, setCandidates] = useState<CandidateMatch[]>([]);
  const [candidatesLoading, setCandidatesLoading] = useState(false);
  const [candidatesError, setCandidatesError] = useState<string | null>(null);
  
  // Upload state
  const [isUploading, setIsUploading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  // Expanded candidate cards
  const [expandedCandidates, setExpandedCandidates] = useState<Set<number>>(new Set());
  
  // Accordion states
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    description: true,
    company: false,
    orgStructure: false,
    requirements: true,
    responsibilities: true,
    conditions: true,
    hiringContext: false,
    successCriteria: false,
    selectionCriteria: false,
  });

  const toggleSection = (section: string) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const toggleCandidateExpanded = (resumeId: number) => {
    setExpandedCandidates(prev => {
      const newSet = new Set(prev);
      if (newSet.has(resumeId)) {
        newSet.delete(resumeId);
      } else {
        newSet.add(resumeId);
      }
      return newSet;
    });
  };

  const loadCandidates = useCallback(async () => {
    if (!id) return;
    setCandidatesLoading(true);
    setCandidatesError(null);
    try {
      const response = await getVacancyCandidates(parseInt(id), 0, 100);
      setCandidates(response.candidates);
    } catch (error) {
      console.error('Failed to load candidates', error);
      setCandidatesError('Не удалось загрузить кандидатов');
    } finally {
      setCandidatesLoading(false);
    }
  }, [id]);

  useEffect(() => {
    const loadVacancy = async () => {
      if (!id) return;
      try {
        const data = await getVacancy(parseInt(id));
        setVacancy(data);
      } catch (error) {
        console.error('Failed to load vacancy', error);
      } finally {
        setIsLoading(false);
      }
    };
    loadVacancy();
  }, [id]);

  // Load candidates when switching to candidates tab
  useEffect(() => {
    if (activeTab === 'candidates' && candidates.length === 0 && !candidatesLoading) {
      loadCandidates();
    }
  }, [activeTab, candidates.length, candidatesLoading, loadCandidates]);

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    setUploadMessage(null);
    setUploadError(null);

    try {
      const result = await uploadResume(file);
      setUploadMessage(`Резюме "${result.candidateName || 'Кандидат'}" загружено. Выполняется анализ...`);
      
      // Reload candidates after a delay (give time for background processing)
      setTimeout(() => {
        loadCandidates();
        setUploadMessage(null);
      }, 3000);
    } catch (error) {
      console.error('Failed to upload resume', error);
      setUploadError('Не удалось загрузить резюме. Попробуйте ещё раз.');
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleDropZoneClick = () => {
    fileInputRef.current?.click();
  };

  const handleDrop = (event: React.DragEvent) => {
    event.preventDefault();
    const file = event.dataTransfer.files?.[0];
    if (file && fileInputRef.current) {
      const dataTransfer = new DataTransfer();
      dataTransfer.items.add(file);
      fileInputRef.current.files = dataTransfer.files;
      fileInputRef.current.dispatchEvent(new Event('change', { bubbles: true }));
    }
  };

  const handleDragOver = (event: React.DragEvent) => {
    event.preventDefault();
  };

  const getScoreColor = (score: number) => {
    if (score >= 70) return 'text-green-600 bg-green-50 border-green-200';
    if (score >= 50) return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    return 'text-red-600 bg-red-50 border-red-200';
  };

  const getScoreLabel = (score: number) => {
    if (score >= 70) return 'Высокое соответствие';
    if (score >= 50) return 'Среднее соответствие';
    return 'Низкое соответствие';
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
      </div>
    );
  }

  if (!vacancy) return <div>Вакансия не найдена</div>;

  // Helpers to safely extract data
  const jobTitle = vacancy.core?.jobTitle || 'Без названия';
  const companyName = vacancy.company?.name || 'Компания не указана';
  const locationCity = vacancy.workConditions?.location?.city || 'Локация не указана';
  const salaryData = vacancy.workConditions?.salary;
  const salaryText = salaryData && (salaryData.amountMin || salaryData.amountMax)
    ? `${salaryData.amountMin ? `от ${salaryData.amountMin}` : ''} ${salaryData.amountMax ? `до ${salaryData.amountMax}` : ''} ${salaryData.currency || ''}`
    : 'Зарплата не указана';
  
  const status = vacancy.status || 'draft';
  const createdAt = vacancy.createdAt;
  
  const descriptionText = vacancy.fullText?.text || 'Описание отсутствует';
  
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const renderCompanyDetails = () => {
    const comp = vacancy.company;
    if (!comp) return <div className="text-gray-500">Информация о компании не указана</div>;

    return (
      <div className="space-y-3 text-gray-600">
        {comp.industry?.name && <div><strong>Отрасль:</strong> {comp.industry.name}</div>}
        {comp.type && <div><strong>Тип:</strong> {comp.type}</div>}
        {comp.size && <div><strong>Размер:</strong> {comp.size}</div>}
        {comp.publicLinks && comp.publicLinks.length > 0 && (
          <div>
            <strong>Ссылки:</strong>
            <ul className="list-disc list-inside ml-2">
              {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
              {comp.publicLinks.map((link: any, i: number) => (
                <li key={i}><a href={link.url} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline">{link.type}: {link.url}</a></li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  };

  const renderOrgStructure = () => {
    const org = vacancy.orgStructure;
    if (!org) return <div className="text-gray-500">Оргструктура не указана</div>;

    return (
      <div className="space-y-3 text-gray-600">
        {org.reportsTo && <div><strong>Подчиняется:</strong> {org.reportsTo}</div>}
        {org.subordinatesCount !== undefined && <div><strong>Подчиненных:</strong> {org.subordinatesCount}</div>}
        {org.teamRoles && org.teamRoles.length > 0 && (
          <div>
            <strong>Роли в команде:</strong>
            <ul className="list-disc list-inside ml-2">
              {org.teamRoles.map((role: string, i: number) => <li key={i}>{role}</li>)}
            </ul>
          </div>
        )}
      </div>
    );
  };

  const renderRequirements = () => {
    const reqs = vacancy.requirements;
    const skills = reqs?.skills || [];
    const exp = reqs?.experience;
    const edu = reqs?.education;
    const langs = reqs?.languages;

    if (!reqs && !skills.length) return <div className="text-gray-500">Требования не указаны</div>;

    return (
      <div className="space-y-4 text-gray-600">
        {exp && (
          <div>
            <strong>Опыт:</strong> {exp.yearsMin ? `от ${exp.yearsMin} лет` : ''} {exp.yearsMax ? `до ${exp.yearsMax} лет` : ''}
            {exp.mustHave && exp.mustHave.length > 0 && (
              <ul className="list-disc list-inside mt-1 ml-2">
                {exp.mustHave.map((item: string, i: number) => <li key={i}>{item}</li>)}
              </ul>
            )}
          </div>
        )}
        
        {skills.length > 0 && (
          <div>
            <strong>Навыки:</strong>
            <div className="flex flex-wrap gap-2 mt-2">
              {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
              {skills.map((skill: any, idx: number) => (
                <span key={idx} className="bg-gray-100 text-gray-700 px-2 py-1 rounded text-sm border border-gray-200">
                  {skill.name} {skill.level ? `(${skill.level})` : ''}
                </span>
              ))}
            </div>
          </div>
        )}

        {edu && (
          <div>
             <strong>Образование:</strong> {edu.level || 'Любое'}
             {edu.fields && edu.fields.length > 0 && ` (${edu.fields.join(', ')})`}
          </div>
        )}

        {langs && langs.length > 0 && (
          <div>
            <strong>Языки:</strong>
            <ul className="list-disc list-inside ml-2">
              {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
              {langs.map((l: any, i: number) => (
                <li key={i}>{l.name} - {l.proficiency}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  };

  const renderResponsibilities = () => {
    const resp = vacancy.responsibilities;
    if (!resp) return <div className="text-gray-500">Обязанности не указаны</div>;

    return (
      <div className="space-y-4 text-gray-600">
        {resp.scope && <div className="whitespace-pre-wrap mb-2"><strong>Область ответственности:</strong> {resp.scope}</div>}
        {resp.zones && resp.zones.length > 0 && (
          <div>
            <strong>Основные задачи:</strong>
            <ul className="list-disc list-inside space-y-1 ml-2 mt-1">
              {resp.zones.map((zone: string, i: number) => (
                <li key={i}>{zone}</li>
              ))}
            </ul>
          </div>
        )}
        {resp.criticalTasks && resp.criticalTasks.length > 0 && (
          <div className="mt-2">
            <strong>Критические задачи (первые 90 дней):</strong>
            <ul className="list-disc list-inside ml-2 mt-1">
               {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
               {resp.criticalTasks.map((t: any, i: number) => (
                 <li key={i}>{t.task} (срок: {t.deadline})</li>
               ))}
            </ul>
          </div>
        )}
      </div>
    );
  };

  const renderConditions = () => {
    const cond = vacancy.workConditions;
    if (!cond) return <div className="text-gray-500">Условия не указаны</div>;

    return (
      <div className="space-y-3 text-gray-600">
        {cond.employmentType?.name && (
          <div><strong>Тип занятости:</strong> {cond.employmentType.name}</div>
        )}
        {cond.schedule?.name && (
          <div><strong>График:</strong> {cond.schedule.name}</div>
        )}
        {cond.workHours && (
           <div><strong>Часы работы:</strong> {cond.workHours}</div>
        )}
        {cond.location && (
          <div>
            <strong>Локация:</strong> {cond.location.city} 
            {cond.location.remote && ` (${cond.location.remote})`}
            {cond.location.relocationSupport && ' (Помощь с переездом)'}
          </div>
        )}
         {cond.salary?.comment && (
           <div className="text-sm italic mt-1">{cond.salary.comment}</div>
         )}
      </div>
    );
  };

  const renderHiringContext = () => {
    const context = vacancy.hiringContext;
    if (!context) return <div className="text-gray-500">Контекст найма не указан</div>;

    return (
      <div className="space-y-3 text-gray-600">
        {context.triggerEvent?.description && <div><strong>Причина открытия:</strong> {context.triggerEvent.description}</div>}
        {context.businessProblem && <div><strong>Бизнес-проблема:</strong> {context.businessProblem}</div>}
        {context.expectedImpact && <div><strong>Ожидаемый результат:</strong> {context.expectedImpact}</div>}
        {context.urgencyReason && <div><strong>Срочность:</strong> {context.urgencyReason}</div>}
      </div>
    );
  };

  const renderSuccessCriteria = () => {
    const criteria = vacancy.successCriteria;
    if (!criteria) return <div className="text-gray-500">Критерии успеха не указаны</div>;

    return (
      <div className="space-y-4 text-gray-600">
        {criteria.shortTermKPIs && criteria.shortTermKPIs.length > 0 && (
          <div>
            <strong>KPI (6 мес):</strong>
            <ul className="list-disc list-inside ml-2">
              {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
              {criteria.shortTermKPIs.map((kpi: any, i: number) => (
                <li key={i}>{kpi.metric}: {kpi.targetValue}</li>
              ))}
            </ul>
          </div>
        )}
        {criteria.onboardingMilestones && criteria.onboardingMilestones.length > 0 && (
          <div>
            <strong>Milestones (Onboarding):</strong>
            <ul className="list-disc list-inside ml-2">
              {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
              {criteria.onboardingMilestones.map((m: any, i: number) => (
                <li key={i}>{m.milestone} ({m.timeframe})</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  };

  const renderSelectionCriteria = () => {
    const diffs = vacancy.differentiators;
    const deals = vacancy.dealbreakers;

    if (!diffs && !deals) return <div className="text-gray-500">Критерии отбора не указаны</div>;

    return (
      <div className="space-y-4 text-gray-600">
        {diffs && (
          <div className="bg-blue-50 p-3 rounded-lg border border-blue-100">
            <h4 className="font-semibold text-blue-800 mb-2">Преимущества (Differentiators)</h4>
            {diffs.industryExpertise?.industries && (
              <div>Отрасли: {diffs.industryExpertise.industries.join(', ')}</div>
            )}
            {diffs.culturalFit?.workStyle && (
              <div>Стиль работы: {diffs.culturalFit.workStyle.join(', ')}</div>
            )}
          </div>
        )}
        
        {deals && (
          <div className="bg-red-50 p-3 rounded-lg border border-red-100">
            <h4 className="font-semibold text-red-800 mb-2">Стоп-факторы (Dealbreakers)</h4>
             {deals.absoluteRequirements && (
               <ul className="list-disc list-inside text-red-700">
                 {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
                 {deals.absoluteRequirements.map((r: any, i: number) => (
                   <li key={i}>{r.requirement}</li>
                 ))}
               </ul>
             )}
             {deals.redFlags && (
               <div className="mt-2 text-red-600 text-sm">
                 Red Flags: {deals.redFlags.join(', ')}
               </div>
             )}
          </div>
        )}
      </div>
    );
  };

  const renderCandidateCard = (candidate: CandidateMatch) => {
    const isExpanded = expandedCandidates.has(candidate.resumeId);
    const candidateName = [candidate.firstName, candidate.lastName].filter(Boolean).join(' ') || 'Без имени';
    
    return (
      <div key={candidate.resumeId} className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden transition-all hover:shadow-md">
        {/* Header */}
        <div 
          className="p-4 cursor-pointer"
          onClick={() => toggleCandidateExpanded(candidate.resumeId)}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-gradient-to-br from-blue-100 to-blue-200 rounded-full flex items-center justify-center text-blue-600 font-semibold text-lg">
                {candidateName.charAt(0).toUpperCase()}
              </div>
              <div>
                <div className="font-semibold text-gray-900">{candidateName}</div>
                <div className="text-sm text-gray-500">{candidate.desiredPosition || 'Должность не указана'}</div>
                {candidate.city && (
                  <div className="text-xs text-gray-400 flex items-center gap-1 mt-0.5">
                    <MapPin size={12} />
                    {candidate.city}
                  </div>
                )}
              </div>
            </div>
            <div className="flex items-center gap-4">
              {/* Score badge */}
              <div className={`px-4 py-2 rounded-xl border font-semibold ${getScoreColor(candidate.matchScore)}`}>
                <div className="text-2xl">{Math.round(candidate.matchScore)}%</div>
                <div className="text-xs font-normal">{getScoreLabel(candidate.matchScore)}</div>
              </div>
              <div className={`p-2 rounded-full bg-gray-50 text-gray-400 transition-transform ${isExpanded ? 'rotate-180' : ''}`}>
                <ChevronDown size={20} />
              </div>
            </div>
          </div>
        </div>

        {/* Expanded content */}
        {isExpanded && (
          <div className="border-t border-gray-100 p-4 space-y-4 animate-in fade-in slide-in-from-top-2 duration-200">
            {/* Contact info */}
            <div className="flex gap-4 text-sm">
              {candidate.email && (
                <a href={`mailto:${candidate.email}`} className="text-blue-600 hover:underline">
                  {candidate.email}
                </a>
              )}
              {candidate.phone && (
                <a href={`tel:${candidate.phone}`} className="text-blue-600 hover:underline">
                  {candidate.phone}
                </a>
              )}
            </div>

            {/* Strengths */}
            {candidate.strengthsSummary.length > 0 && (
              <div className="bg-green-50 rounded-xl p-4 border border-green-100">
                <h4 className="font-semibold text-green-800 flex items-center gap-2 mb-2">
                  <CheckCircle2 size={18} />
                  Сильные стороны
                </h4>
                <ul className="space-y-1">
                  {candidate.strengthsSummary.map((item, idx) => (
                    <li key={idx} className="text-green-700 text-sm flex items-start gap-2">
                      <TrendingUp size={14} className="mt-0.5 flex-shrink-0" />
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Gaps */}
            {candidate.gapsSummary.length > 0 && (
              <div className="bg-yellow-50 rounded-xl p-4 border border-yellow-100">
                <h4 className="font-semibold text-yellow-800 flex items-center gap-2 mb-2">
                  <AlertCircle size={18} />
                  Возможные пробелы
                </h4>
                <ul className="space-y-1">
                  {candidate.gapsSummary.map((item, idx) => (
                    <li key={idx} className="text-yellow-700 text-sm">{item}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Interview questions */}
            {candidate.interviewQuestions.length > 0 && (
              <div className="bg-blue-50 rounded-xl p-4 border border-blue-100">
                <h4 className="font-semibold text-blue-800 flex items-center gap-2 mb-3">
                  <MessageCircleQuestion size={18} />
                  Вопросы для собеседования
                </h4>
                <div className="space-y-3">
                  {candidate.interviewQuestions.map((q, idx) => (
                    <div key={idx} className="bg-white rounded-lg p-3 border border-blue-100">
                      <div className="text-xs text-blue-500 font-medium mb-1">{q.topic}</div>
                      <div className="text-gray-800">{q.question}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="p-8 max-w-7xl mx-auto font-sans">
      <Breadcrumbs
        items={[
          { label: 'Главная', path: '/home' },
          { label: 'Вакансии', path: '/vacancy' },
          { label: jobTitle },
        ]}
      />

      <div className="mt-6 mb-8">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-gray-900 tracking-tight">{jobTitle}</h1>
          <div className="flex gap-3">
             <span className={`px-3 py-1 rounded-full text-sm font-medium ${
               status === 'active' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'
             }`}>
               {status === 'active' ? 'Активна' : status === 'closed' ? 'Закрыта' : 'Черновик'}
             </span>
          </div>
        </div>
        <div className="flex items-center gap-6 mt-4 text-gray-500">
          <div className="flex items-center gap-2">
            <Building2 size={18} />
            <span>{companyName}</span>
          </div>
          <div className="flex items-center gap-2">
            <MapPin size={18} />
            <span>{locationCity}</span>
          </div>
          <div className="flex items-center gap-2">
            <Wallet size={18} />
            <span>{salaryText}</span>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-8 border-b border-gray-200 mb-8">
        <button
          onClick={() => setActiveTab('vacancy')}
          className={`pb-4 px-2 text-sm font-medium transition-colors relative ${
            activeTab === 'vacancy' 
              ? 'text-gray-900' 
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          <div className="flex items-center gap-2">
            <FileText size={18} />
            Описание вакансии
          </div>
          {activeTab === 'vacancy' && (
            <div className="absolute bottom-0 left-0 w-full h-0.5 bg-gray-900 rounded-t-full" />
          )}
        </button>
        <button
          onClick={() => setActiveTab('candidates')}
          className={`pb-4 px-2 text-sm font-medium transition-colors relative ${
            activeTab === 'candidates' 
              ? 'text-gray-900' 
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          <div className="flex items-center gap-2">
            <Users size={18} />
            Кандидаты
            {candidates.length > 0 && (
              <span className="bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full text-xs font-semibold">
                {candidates.length}
              </span>
            )}
          </div>
          {activeTab === 'candidates' && (
            <div className="absolute bottom-0 left-0 w-full h-0.5 bg-gray-900 rounded-t-full" />
          )}
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Content */}
        <div className="lg:col-span-2">
          {activeTab === 'vacancy' ? (
            <div className="space-y-4">
              {/* Description Section */}
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 transition-shadow hover:shadow-md">
                <button 
                  onClick={() => toggleSection('description')}
                  className="w-full flex items-center justify-between mb-2 group"
                >
                  <h3 className="text-lg font-semibold text-gray-900">Описание</h3>
                  <div className={`p-2 rounded-full bg-gray-50 text-gray-400 group-hover:bg-gray-100 group-hover:text-gray-600 transition-colors`}>
                    {expandedSections.description ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                  </div>
                </button>
                
                {expandedSections.description && (
                  <div className="mt-4 text-gray-600 leading-relaxed animate-in fade-in slide-in-from-top-2 duration-300">
                    <div className="whitespace-pre-wrap">{descriptionText}</div>
                  </div>
                )}
              </div>

              {/* Company Section */}
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 transition-shadow hover:shadow-md">
                <button 
                  onClick={() => toggleSection('company')}
                  className="w-full flex items-center justify-between mb-2 group"
                >
                  <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2"><Building2 size={20}/> О компании</h3>
                  <div className={`p-2 rounded-full bg-gray-50 text-gray-400 group-hover:bg-gray-100 group-hover:text-gray-600 transition-colors`}>
                    {expandedSections.company ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                  </div>
                </button>
                
                {expandedSections.company && (
                  <div className="mt-4 animate-in fade-in slide-in-from-top-2 duration-300">
                     {renderCompanyDetails()}
                  </div>
                )}
              </div>

               {/* Org Structure Section */}
               <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 transition-shadow hover:shadow-md">
                <button 
                  onClick={() => toggleSection('orgStructure')}
                  className="w-full flex items-center justify-between mb-2 group"
                >
                  <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2"><Network size={20}/> Оргструктура</h3>
                  <div className={`p-2 rounded-full bg-gray-50 text-gray-400 group-hover:bg-gray-100 group-hover:text-gray-600 transition-colors`}>
                    {expandedSections.orgStructure ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                  </div>
                </button>
                
                {expandedSections.orgStructure && (
                  <div className="mt-4 animate-in fade-in slide-in-from-top-2 duration-300">
                     {renderOrgStructure()}
                  </div>
                )}
              </div>

              {/* Responsibilities Section */}
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 transition-shadow hover:shadow-md">
                <button 
                  onClick={() => toggleSection('responsibilities')}
                  className="w-full flex items-center justify-between mb-2 group"
                >
                  <h3 className="text-lg font-semibold text-gray-900">Обязанности</h3>
                  <div className={`p-2 rounded-full bg-gray-50 text-gray-400 group-hover:bg-gray-100 group-hover:text-gray-600 transition-colors`}>
                    {expandedSections.responsibilities ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                  </div>
                </button>
                
                {expandedSections.responsibilities && (
                  <div className="mt-4 animate-in fade-in slide-in-from-top-2 duration-300">
                     {renderResponsibilities()}
                  </div>
                )}
              </div>

              {/* Requirements Section */}
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 transition-shadow hover:shadow-md">
                <button 
                  onClick={() => toggleSection('requirements')}
                  className="w-full flex items-center justify-between mb-2 group"
                >
                  <h3 className="text-lg font-semibold text-gray-900">Требования</h3>
                  <div className={`p-2 rounded-full bg-gray-50 text-gray-400 group-hover:bg-gray-100 group-hover:text-gray-600 transition-colors`}>
                    {expandedSections.requirements ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                  </div>
                </button>
                
                {expandedSections.requirements && (
                  <div className="mt-4 animate-in fade-in slide-in-from-top-2 duration-300">
                     {renderRequirements()}
                  </div>
                )}
              </div>

              {/* Conditions Section */}
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 transition-shadow hover:shadow-md">
                <button 
                  onClick={() => toggleSection('conditions')}
                  className="w-full flex items-center justify-between mb-2 group"
                >
                  <h3 className="text-lg font-semibold text-gray-900">Условия</h3>
                  <div className={`p-2 rounded-full bg-gray-50 text-gray-400 group-hover:bg-gray-100 group-hover:text-gray-600 transition-colors`}>
                    {expandedSections.conditions ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                  </div>
                </button>
                
                {expandedSections.conditions && (
                  <div className="mt-4 animate-in fade-in slide-in-from-top-2 duration-300">
                     {renderConditions()}
                  </div>
                )}
              </div>

               {/* Hiring Context Section */}
               <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 transition-shadow hover:shadow-md">
                <button 
                  onClick={() => toggleSection('hiringContext')}
                  className="w-full flex items-center justify-between mb-2 group"
                >
                  <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2"><Target size={20}/> Контекст найма</h3>
                  <div className={`p-2 rounded-full bg-gray-50 text-gray-400 group-hover:bg-gray-100 group-hover:text-gray-600 transition-colors`}>
                    {expandedSections.hiringContext ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                  </div>
                </button>
                
                {expandedSections.hiringContext && (
                  <div className="mt-4 animate-in fade-in slide-in-from-top-2 duration-300">
                     {renderHiringContext()}
                  </div>
                )}
              </div>

               {/* Success Criteria Section */}
               <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 transition-shadow hover:shadow-md">
                <button 
                  onClick={() => toggleSection('successCriteria')}
                  className="w-full flex items-center justify-between mb-2 group"
                >
                  <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2"><Award size={20}/> Критерии успеха</h3>
                  <div className={`p-2 rounded-full bg-gray-50 text-gray-400 group-hover:bg-gray-100 group-hover:text-gray-600 transition-colors`}>
                    {expandedSections.successCriteria ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                  </div>
                </button>
                
                {expandedSections.successCriteria && (
                  <div className="mt-4 animate-in fade-in slide-in-from-top-2 duration-300">
                     {renderSuccessCriteria()}
                  </div>
                )}
              </div>

              {/* Selection Criteria Section */}
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 transition-shadow hover:shadow-md">
                <button 
                  onClick={() => toggleSection('selectionCriteria')}
                  className="w-full flex items-center justify-between mb-2 group"
                >
                  <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2"><ShieldAlert size={20}/> Критерии отбора</h3>
                  <div className={`p-2 rounded-full bg-gray-50 text-gray-400 group-hover:bg-gray-100 group-hover:text-gray-600 transition-colors`}>
                    {expandedSections.selectionCriteria ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                  </div>
                </button>
                
                {expandedSections.selectionCriteria && (
                  <div className="mt-4 animate-in fade-in slide-in-from-top-2 duration-300">
                     {renderSelectionCriteria()}
                  </div>
                )}
              </div>

            </div>
          ) : (
            <div className="space-y-6">
              {/* Upload Zone */}
              <div 
                onClick={handleDropZoneClick}
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                className={`bg-white border-2 border-dashed rounded-2xl p-8 text-center transition-all cursor-pointer group ${
                  isUploading 
                    ? 'border-blue-400 bg-blue-50' 
                    : 'border-gray-200 hover:border-blue-400 hover:bg-blue-50/50'
                }`}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.docx,.doc,.txt"
                  onChange={handleFileUpload}
                  className="hidden"
                />
                
                <div className={`w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4 transition-all ${
                  isUploading 
                    ? 'bg-blue-100 text-blue-600 animate-pulse' 
                    : 'bg-blue-50 text-blue-500 group-hover:scale-110'
                }`}>
                  {isUploading ? <Loader2 size={28} className="animate-spin" /> : <Upload size={28} />}
                </div>
                
                <h3 className="text-lg font-semibold text-gray-900">
                  {isUploading ? 'Загрузка...' : 'Загрузить резюме'}
                </h3>
                <p className="text-gray-500 mt-1 max-w-sm mx-auto">
                  {isUploading 
                    ? 'Обработка файла и анализ резюме...' 
                    : 'Перетащите файл сюда или кликните для выбора. Поддерживаются PDF, DOCX'}
                </p>
                
                {uploadMessage && (
                  <div className="mt-4 p-3 bg-green-50 text-green-700 rounded-lg flex items-center justify-center gap-2">
                    <CheckCircle2 size={18} />
                    {uploadMessage}
                  </div>
                )}
                
                {uploadError && (
                  <div className="mt-4 p-3 bg-red-50 text-red-700 rounded-lg flex items-center justify-center gap-2">
                    <AlertCircle size={18} />
                    {uploadError}
                  </div>
                )}
              </div>

              {/* Refresh button */}
              <div className="flex justify-end">
                <button
                  onClick={loadCandidates}
                  disabled={candidatesLoading}
                  className="flex items-center gap-2 px-4 py-2 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
                >
                  <RefreshCw size={16} className={candidatesLoading ? 'animate-spin' : ''} />
                  Обновить список
                </button>
              </div>

              {/* Error state */}
              {candidatesError && (
                <div className="bg-red-50 text-red-700 p-4 rounded-xl flex items-center gap-3">
                  <AlertCircle size={20} />
                  {candidatesError}
                </div>
              )}

              {/* Loading state */}
              {candidatesLoading && (
                <div className="flex items-center justify-center py-12">
                  <Loader2 size={32} className="animate-spin text-gray-400" />
                </div>
              )}

              {/* Candidates List */}
              {!candidatesLoading && candidates.length === 0 && (
                <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-12 text-center">
                  <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Users size={28} className="text-gray-400" />
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Кандидатов пока нет</h3>
                  <p className="text-gray-500">
                    Загрузите резюме кандидатов для автоматического анализа и скоринга
                  </p>
                </div>
              )}

              {!candidatesLoading && candidates.length > 0 && (
                <div className="space-y-4">
                  {candidates.map(candidate => renderCandidateCard(candidate))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="lg:col-span-1 space-y-6">
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
            <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4">Детали</h3>
            <div className="space-y-4">
              <div className="flex items-start gap-3">
                <Calendar className="text-gray-400 mt-0.5" size={18} />
                <div>
                  <div className="text-sm text-gray-500">Дата создания</div>
                  <div className="font-medium text-gray-900">
                    {createdAt ? new Date(createdAt).toLocaleDateString() : '-'}
                  </div>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <Briefcase className="text-gray-400 mt-0.5" size={18} />
                <div>
                  <div className="text-sm text-gray-500">Формат работы</div>
                  <div className="font-medium text-gray-900">
                    {vacancy.workConditions?.location?.remote === 'office' ? 'Офис' : 
                     vacancy.workConditions?.location?.remote === 'remote' ? 'Удаленно' :
                     vacancy.workConditions?.location?.remote === 'hybrid' ? 'Гибрид' : 'Не указан'}
                  </div>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <Clock className="text-gray-400 mt-0.5" size={18} />
                <div>
                  <div className="text-sm text-gray-500">Занятость</div>
                  <div className="font-medium text-gray-900">
                    {vacancy.workConditions?.employmentType?.name === 'full-time' ? 'Полная' :
                     vacancy.workConditions?.employmentType?.name === 'part-time' ? 'Частичная' : 'Не указана'}
                  </div>
                </div>
              </div>
              {candidates.length > 0 && (
                <div className="flex items-start gap-3">
                  <Users className="text-gray-400 mt-0.5" size={18} />
                  <div>
                    <div className="text-sm text-gray-500">Кандидатов</div>
                    <div className="font-medium text-gray-900">{candidates.length}</div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
