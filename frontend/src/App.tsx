import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import MainLayout from './layouts/MainLayout';
import Home from './pages/Home';
import Vacancy from './pages/Vacancy';
import VacancyCreate from './pages/VacancyCreate';
import VacancyDetail from './pages/VacancyDetail';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<Navigate to="/home" replace />} />
          <Route path="home" element={<Home />} />
          <Route path="vacancy" element={<Vacancy />} />
          <Route path="vacancy/create" element={<VacancyCreate />} />
          <Route path="vacancy/:id" element={<VacancyDetail />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
