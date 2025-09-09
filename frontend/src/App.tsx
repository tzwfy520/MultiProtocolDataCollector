import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider, theme } from 'antd';
import { QueryClient, QueryClientProvider } from 'react-query';
import zhCN from 'antd/locale/zh_CN';
import 'dayjs/locale/zh-cn';

import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import ServerManagement from './pages/ServerManagement';
import TaskManagement from './pages/TaskManagement';
import DataCollection from './pages/DataCollection';
import SystemLogs from './pages/SystemLogs';
import Settings from './pages/Settings';

import { useThemeStore } from './stores/themeStore';

import './App.css';

// 创建 React Query 客户端
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5分钟
    },
  },
});

const App: React.FC = () => {
  const { isDarkMode } = useThemeStore();

  return (
    <QueryClientProvider client={queryClient}>
      <ConfigProvider
        locale={zhCN}
        theme={{
          algorithm: isDarkMode ? theme.darkAlgorithm : theme.defaultAlgorithm,
          token: {
            colorPrimary: '#1890ff',
            borderRadius: 6,
          },
        }}
      >
        <Router>
          <Layout>
            <Routes>
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/servers" element={<ServerManagement />} />
              <Route path="/tasks" element={<TaskManagement />} />
              <Route path="/collection" element={<DataCollection />} />
              <Route path="/logs" element={<SystemLogs />} />
              <Route path="/settings" element={<Settings />} />
            </Routes>
          </Layout>
        </Router>
      </ConfigProvider>
    </QueryClientProvider>
  );
};

export default App;