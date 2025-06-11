import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Navigation } from './components/Navigation';
import { HomePage } from './pages/HomePage';
import { EnrollmentPage } from './pages/EnrollmentPage';
import { ZendeskPage } from './pages/ZendeskPage';
import './App.css';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Navigation />
        <main className="container mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/enrollment" element={<EnrollmentPage />} />
            <Route path="/zendesk" element={<ZendeskPage />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
