import { useState } from 'react'
import { Routes, Route } from 'react-router-dom'
import { 
  ThemeProvider, 
  createTheme, 
  CssBaseline 
} from '@mui/material'

import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import HostManagement from './pages/HostManagement'
import JobHistory from './pages/JobHistory'
import Settings from './pages/Settings'
import NotFound from './pages/NotFound'

// Create theme instance
const darkTheme = createTheme({
  palette: {
    mode: 'dark',
  },
})

const lightTheme = createTheme({
  palette: {
    mode: 'light',
  },
})

function App() {
  const [darkMode, setDarkMode] = useState(true)
  
  const toggleDarkMode = () => {
    setDarkMode(!darkMode)
  }
  
  return (
    <ThemeProvider theme={darkMode ? darkTheme : lightTheme}>
      <CssBaseline />
      <Layout darkMode={darkMode} toggleDarkMode={toggleDarkMode}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/hosts" element={<HostManagement />} />
          <Route path="/jobs" element={<JobHistory />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </Layout>
    </ThemeProvider>
  )
}

export default App