import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
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
  Network
} from 'lucide-react';
import Breadcrumbs from '../components/Breadcrumbs';
import { getVacancy } from '../api/vacancy';

// Mock data for candidates
const MOCK_CANDIDATES = [
  { id: 1, name: 'Александр Иванов', position: 'Frontend Developer', status: 'New', date: '2024-03-15' },
  { id: 2, name: 'Мария Петрова', position: 'Frontend Developer', status: 'Review', date: '2024-03-14' },
  { id: 3, name: 'Дмитрий Сидоров', position: 'Frontend Developer', status: 'Rejected', date: '2024-03-12' },
];

export default function VacancyDetail() {
  const { id } = useParams();
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<'vacancy' | 'candidates'>('vacancy');
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [vacancy, setVacancy] = useState<any | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  
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
  
  // Renders
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
            <span className="bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full text-xs">
              {MOCK_CANDIDATES.length}
            </span>
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
              <div className="bg-white border-2 border-dashed border-gray-200 rounded-2xl p-8 text-center hover:border-gray-400 transition-colors cursor-pointer group">
                <div className="w-16 h-16 bg-blue-50 text-blue-500 rounded-full flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform">
                  <Upload size={28} />
                </div>
                <h3 className="text-lg font-semibold text-gray-900">Загрузить резюме</h3>
                <p className="text-gray-500 mt-1 max-w-sm mx-auto">
                  Перетащите файлы сюда или кликните для выбора. Поддерживаются PDF, DOCX
                </p>
              </div>

              {/* Candidates List */}
              <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
                <div className="p-6 border-b border-gray-100">
                  <h3 className="text-lg font-semibold text-gray-900">Список кандидатов</h3>
                </div>
                <div className="divide-y divide-gray-100">
                  {MOCK_CANDIDATES.map((candidate) => (
                    <div key={candidate.id} className="p-4 flex items-center justify-between hover:bg-gray-50 transition-colors group cursor-pointer">
                      <div className="flex items-center gap-4">
                        <div className="w-10 h-10 bg-gray-100 rounded-full flex items-center justify-center text-gray-500 font-medium group-hover:bg-white group-hover:shadow-sm transition-all">
                          {candidate.name.charAt(0)}
                        </div>
                        <div>
                          <div className="font-medium text-gray-900">{candidate.name}</div>
                          <div className="text-sm text-gray-500">{candidate.position}</div>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <span className="text-sm text-gray-400">{candidate.date}</span>
                        <div className={`px-3 py-1 rounded-full text-xs font-medium 
                          ${candidate.status === 'New' ? 'bg-blue-50 text-blue-700' : 
                            candidate.status === 'Review' ? 'bg-yellow-50 text-yellow-700' :
                            'bg-red-50 text-red-700'}`}>
                          {candidate.status}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
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
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
