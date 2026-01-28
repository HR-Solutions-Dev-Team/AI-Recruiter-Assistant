import Breadcrumbs from '../components/Breadcrumbs';

export default function Home() {
  return (
    <div className="p-8">
      <Breadcrumbs items={[{ label: 'Главная' }]} />

      <div className="mt-6">
        <h1 className="text-2xl font-semibold text-gray-900">Главная</h1>
        <p className="text-gray-500 mt-2">Добро пожаловать в CRM HR AI</p>
      </div>
    </div>
  );
}
