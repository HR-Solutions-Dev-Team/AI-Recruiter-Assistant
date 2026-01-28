import Breadcrumbs from '../components/Breadcrumbs';

export default function Vacancy() {
  return (
    <div className="p-8">
      <Breadcrumbs
        items={[
          { label: 'Главная', path: '/home' },
          { label: 'Вакансии' },
        ]}
      />

      <div className="mt-6">
        <h1 className="text-2xl font-semibold text-gray-900">Вакансии</h1>
        <p className="text-gray-500 mt-2">Управление вакансиями компании</p>
      </div>
    </div>
  );
}
