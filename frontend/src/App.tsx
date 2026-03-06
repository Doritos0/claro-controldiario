import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Navigate, Routes, Route } from 'react-router';
import Login from './pages/Login.tsx';

const queryClient = new QueryClient();


function App() {

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Navigate to="/login" replace />} />
          <Route path="/login" element={<Login />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App
