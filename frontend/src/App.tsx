import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactElement } from 'react';
import { BrowserRouter, Navigate, Routes, Route } from 'react-router';
import Login from './pages/Login.tsx';
import Home from './pages/Home.tsx';

const queryClient = new QueryClient();

function ProtectedRoute({ children }: { children: ReactElement }) {
  const accessToken = localStorage.getItem('accessToken');

  if (!accessToken) {
    return <Navigate to="/login" replace />;
  }

  return children;
}

function App() {

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Navigate to="/login" replace />} />
          <Route path="/login" element={<Login />} />
          <Route
            path="/home"
            element={(
              <ProtectedRoute>
                <Home />
              </ProtectedRoute>
            )}
          />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App