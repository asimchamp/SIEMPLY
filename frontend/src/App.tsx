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
import NewJob from './pages/NewJob'
import Database from './pages/Database'
import Users from './pages/Users'
import ServerClass from './pages/ServerClass'
import Files from './pages/Files'
import PlaybookBuilder from './pages/PlaybookBuilder'
import PlaybookList from './pages/PlaybookList'
import Executions from './pages/Executions'

// Workflows Pages
import Build from './workflows/Build'

// Splunk ACS Pages
import SplunkACSDashboard from './splunk_acs/pages/splunk_acs_dashboard'
import SplunkACSConfigs from './splunk_acs/pages/splunk_acs_configs'
import SplunkACSChanges from './splunk_acs/pages/splunk_acs_changes'
import SplunkACSIPAllowLists from './splunk_acs/pages/splunk_acs_ip_allow_lists'

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
          <Route path="/hosts/server-classes" element={
            <RequireAuth>
              <Layout darkMode={darkMode} toggleDarkMode={toggleDarkMode}>
                <ServerClass />
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
          <Route path="/jobs/new" element={
            <RequireAuth>
              <Layout darkMode={darkMode} toggleDarkMode={toggleDarkMode}>
                <NewJob />
              </Layout>
            </RequireAuth>
          } />
          <Route path="/build" element={
            <RequireAuth>
              <Layout darkMode={darkMode} toggleDarkMode={toggleDarkMode}>
                <Build />
              </Layout>
            </RequireAuth>
          } />
          <Route path="/database" element={
            <Navigate to="/database/packages" replace />
          } />
          <Route path="/database/packages" element={
            <RequireAuth>
              <Layout darkMode={darkMode} toggleDarkMode={toggleDarkMode}>
                <Database />
              </Layout>
            </RequireAuth>
          } />
          <Route path="/database/users" element={
            <RequireAuth>
              <Layout darkMode={darkMode} toggleDarkMode={toggleDarkMode}>
                <Users />
              </Layout>
            </RequireAuth>
          } />
          <Route path="/database/files" element={
            <RequireAuth>
              <Layout darkMode={darkMode} toggleDarkMode={toggleDarkMode}>
                <Files />
              </Layout>
            </RequireAuth>
          } />

          <Route path="/playbooks" element={
            <RequireAuth>
              <Layout darkMode={darkMode} toggleDarkMode={toggleDarkMode}>
                <PlaybookList />
              </Layout>
            </RequireAuth>
          } />
          <Route path="/playbook-builder" element={
            <RequireAuth>
              <Layout darkMode={darkMode} toggleDarkMode={toggleDarkMode}>
                <PlaybookBuilder />
              </Layout>
            </RequireAuth>
          } />
          <Route path="/executions" element={
            <RequireAuth>
              <Layout darkMode={darkMode} toggleDarkMode={toggleDarkMode}>
                <Executions />
              </Layout>
            </RequireAuth>
          } />
          
          {/* Splunk ACS Routes */}
          <Route path="/splunk-acs/dashboard" element={
            <RequireAuth>
              <Layout darkMode={darkMode} toggleDarkMode={toggleDarkMode}>
                <SplunkACSDashboard />
              </Layout>
            </RequireAuth>
          } />
          <Route path="/splunk-acs/configs" element={
            <RequireAuth>
              <Layout darkMode={darkMode} toggleDarkMode={toggleDarkMode}>
                <SplunkACSConfigs />
              </Layout>
            </RequireAuth>
          } />
          <Route path="/splunk-acs/changes" element={
            <RequireAuth>
              <Layout darkMode={darkMode} toggleDarkMode={toggleDarkMode}>
                <SplunkACSChanges />
              </Layout>
            </RequireAuth>
          } />
          <Route path="/splunk-acs/ip-allow-lists" element={
            <RequireAuth>
              <Layout darkMode={darkMode} toggleDarkMode={toggleDarkMode}>
                <SplunkACSIPAllowLists />
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
          
          {/* 404 page */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </AuthProvider>
    </ConfigProvider>
  )
}

export default App