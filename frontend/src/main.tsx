import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

// 设置dayjs中文
import dayjs from 'dayjs';
import 'dayjs/locale/zh-cn';
import relativeTime from 'dayjs/plugin/relativeTime';
import duration from 'dayjs/plugin/duration';

dayjs.locale('zh-cn');
dayjs.extend(relativeTime);
dayjs.extend(duration);

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);