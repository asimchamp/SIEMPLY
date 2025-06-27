import { useState } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { ConfigProvider, theme } from 'antd'

import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import HostManagement from './pages/HostManagement'
import JobHistory from './pages/JobHistory'
import Settings from './pages/Settings'
import Login from './pages/Login'
import Register from './pages/Register'
import ChangePassword from './pages/ChangePassword'
import NotFound from './pages/NotFound'
import { AuthProvider, RequireAuth } from './services/authContext'

function App() {
  const [darkMode, setDarkMode] = useState(true)
  
  const toggleDarkMode = () => {
    setDarkMode(!darkMode)
  }
  
  return (
    <ConfigProvider
      theme={{
        algorithm: darkMode ? theme.darkAlgorithm : theme.defaultAlgorithm,
      }}
    >
      <AuthProvider>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          
          {/* Protected routes */}
          <Route path="/" element={
            <RequireAuth>
              <Layout darkMode={darkMode} toggleDarkMode={toggleDarkMode}>
                <Dashboard />
              </Layout>
            </RequireAuth>
          } />
          <Route path="/dashboard" element={
            <RequireAuth>
              <Layout darkMode={darkMode} toggleDarkMode={toggleDarkMode}>
                <Dashboard />
              </Layout>
            </RequireAuth>
          } />
          <Route path="/hosts" element={
            <RequireAuth>
              <Layout darkMode={darkMode} toggleDarkMode={toggleDarkMode}>
                <HostManagement />
              </Layout>
            </RequireAuth>
          } />
          <Route path="/jobs" element={
            <RequireAuth>
              <Layout darkMode={darkMode} toggleDarkMode={toggleDarkMode}>
                <JobHistory />
              </Layout>
            </RequireAuth>
          } />
          <Route path="/settings" element={
            <RequireAuth>
              <Layout darkMode={darkMode} toggleDarkMode={toggleDarkMode}>
                <Settings />
              </Layout>
            </RequireAuth>
          } />
          <Route path="/change-password" element={
            <RequireAuth>
              <Layout darkMode={darkMode} toggleDarkMode={toggleDarkMode}>
                <ChangePassword />
              </Layout>
            </RequireAuth>
          } />
          
          {/* Redirect root to dashboard */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          
          {/* 404 page */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </AuthProvider>
    </ConfigProvider>
  )
}

export default App