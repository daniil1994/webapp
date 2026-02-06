# Frontend Tasks - Weekly Breakdown (Phase 1)
**Период:** Week 1-12
**Стратегия:** Backend first → Frontend integration → Polish

---

## 🎯 Общая стратегия

1. **Week 1:** Минимальные изменения - auth setup
2. **Week 2-3:** Архитектурные изменения (Router, React Query)
3. **Week 4-5:** Интеграция с backend API
4. **Week 6-7:** Real-time features (WebSocket)
5. **Week 8-9:** VS Code Extension + Org Settings
6. **Week 10-12:** Polish, analytics, error handling


На backend обновить сразу доступы в базу данных Postgress. В /backend/.env информация уже внесена.

POSTGRESQL_HOST=cabc149f4093f502673ee7d4.twc1.net
POSTGRESQL_PORT=5432
POSTGRESQL_USER=admin_repa
POSTGRESQL_PASSWORD=D^nFfiTH,$2:k
POSTGRESQL_DBNAME=repa
---

## Week 1: Auth Setup & Package Updates

### Задачи (1-2 дня)

#### 1.1. Dependency Updates
```bash
cd frontend/

# Update React 18 → 19
npm install react@19 react-dom@19

# Add new dependencies
npm install @tanstack/react-query zustand react-router-dom axios

# Remove MUI (уже есть shadcn/ui)
npm uninstall @mui/material @mui/icons-material @emotion/react @emotion/styled
```

**Файлы:**
- `package.json` - обновить dependencies

#### 1.2. Create API Client
**Создать:** `src/lib/api.ts`
```typescript
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor для добавления JWT token
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('repa_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor для обработки 401
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('repa_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// API methods
export const authAPI = {
  login: (email: string, password: string) =>
    apiClient.post('/api/v1/auth/login', { email, password }),
  register: (email: string, password: string, org_name: string) =>
    apiClient.post('/api/v1/auth/register', { email, password, org_name }),
  me: () => apiClient.get('/api/v1/users/me'),
};
```

#### 1.3. Create Auth Store (Zustand)
**Создать:** `src/store/authStore.ts`
```typescript
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface User {
  id: string;
  email: string;
  org_id: string;
  role: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (token: string, user: User) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      login: (token, user) => {
        localStorage.setItem('repa_token', token);
        set({ token, user, isAuthenticated: true });
      },
      logout: () => {
        localStorage.removeItem('repa_token');
        set({ token: null, user: null, isAuthenticated: false });
      },
    }),
    {
      name: 'repa-auth',
    }
  )
);
```

#### 1.4. Create Login Page
**Создать:** `src/pages/LoginPage.tsx`
```typescript
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { authAPI } from '@/lib/api';
import { useAuthStore } from '@/store/authStore';
import { Button, Input, Card } from '@/app/components/UIPrimitives';

export function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const login = useAuthStore((s) => s.login);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      const { data } = await authAPI.login(email, password);
      login(data.access_token, data.user);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0D1117]">
      <Card className="w-full max-w-md p-8">
        <h1 className="text-2xl font-bold mb-6">Repa Login</h1>
        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="text-sm mb-2 block">Email</label>
            <Input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div>
            <label className="text-sm mb-2 block">Password</label>
            <Input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          {error && <p className="text-red-500 text-sm">{error}</p>}
          <Button type="submit" variant="primary" className="w-full">
            Login
          </Button>
        </form>
      </Card>
    </div>
  );
}
```

#### 1.5. Environment Variables
**Создать:** `frontend/.env`
```
VITE_API_URL=http://localhost:8000
```

**Создать:** `frontend/.env.production`
```
VITE_API_URL=https://api.repa.dev
```

### Definition of Done (Week 1)
- [ ] React 19 установлен
- [ ] API client работает с JWT
- [ ] Login page функционирует
- [ ] Token сохраняется в localStorage
- [ ] Zustand store управляет auth state

---

## Week 2-3: React Router + React Query Architecture

### Задачи (3-4 дня)

#### 2.1. Install React Router
```bash
npm install react-router-dom
```

#### 2.2. Create Router Structure
**Обновить:** `src/main.tsx`
```typescript
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import App from './app/App';
import './styles/index.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 min
    },
  },
});

ReactDOM.createRoot(document.getElementById('root')!).render(
  <BrowserRouter>
    <QueryClientProvider client={queryClient}>
      <App />
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  </BrowserRouter>
);
```

#### 2.3. Create Layout Component
**Создать:** `src/app/components/Layout.tsx`
```typescript
import { Outlet, Navigate } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { useAuthStore } from '@/store/authStore';

export function Layout() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="flex h-screen bg-[#0D1117] text-[#E6EDF3]">
      <Sidebar />
      <main className="flex-1 overflow-hidden">
        <Outlet />
      </main>
    </div>
  );
}
```

#### 2.4. Update App.tsx with Routes
**Обновить:** `src/app/App.tsx`
```typescript
import { Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/Layout';
import { LoginPage } from '@/pages/LoginPage';
import { Dashboard } from './components/Dashboard';
import { Projects } from './components/Projects';
import { ProjectDetail } from './components/ProjectDetail';
import { OrgSettings } from './components/OrgSettings';

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/" element={<Layout />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="projects" element={<Projects />} />
        <Route path="projects/:id" element={<ProjectDetail />} />
        <Route path="settings" element={<OrgSettings />} />
      </Route>
    </Routes>
  );
}
```

#### 2.5. Update Sidebar Navigation
**Обновить:** `src/app/components/Sidebar.tsx`
```typescript
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Folder, Settings, LogOut } from 'lucide-react';
import { useAuthStore } from '@/store/authStore';

export function Sidebar() {
  const logout = useAuthStore((s) => s.logout);

  const navItems = [
    { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/projects', icon: Folder, label: 'Projects' },
    { to: '/settings', icon: Settings, label: 'Settings' },
  ];

  return (
    <aside className="w-16 bg-[#161B22] border-r border-[#30363D] flex flex-col">
      <div className="p-4">
        <div className="w-8 h-8 bg-[#00D4FF] rounded"></div>
      </div>

      <nav className="flex-1 py-4">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `flex items-center justify-center h-12 ${
                isActive ? 'text-[#00D4FF]' : 'text-[#7D8590] hover:text-white'
              }`
            }
          >
            <item.icon className="w-5 h-5" />
          </NavLink>
        ))}
      </nav>

      <button onClick={logout} className="p-4 text-[#7D8590] hover:text-white">
        <LogOut className="w-5 h-5" />
      </button>
    </aside>
  );
}
```

### Definition of Done (Week 2-3)
- [ ] React Router работает
- [ ] Protected routes (redirect to login)
- [ ] Navigation через Sidebar
- [ ] React Query setup complete

---

## Week 3: Projects API Integration

### Задачи (3-4 дня)

#### 3.1. Create API Types
**Создать:** `src/types/api.ts`
```typescript
export interface Project {
  id: string;
  name: string;
  repo_path: string;
  status: 'pending' | 'indexing' | 'indexed' | 'failed';
  created_at: string;
  last_indexed_at?: string;
}

export interface IndexingStatus {
  job_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  total_files: number;
  error?: string;
}

export interface CreateProjectDTO {
  name: string;
  repo_url?: string;
  repo_path?: string;
}
```

#### 3.2. Create Projects Hooks
**Создать:** `src/hooks/useProjects.ts`
```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import type { Project, CreateProjectDTO, IndexingStatus } from '@/types/api';

export function useProjects() {
  return useQuery({
    queryKey: ['projects'],
    queryFn: async () => {
      const { data } = await apiClient.get<Project[]>('/api/v1/projects');
      return data;
    },
  });
}

export function useProject(id: string) {
  return useQuery({
    queryKey: ['projects', id],
    queryFn: async () => {
      const { data } = await apiClient.get<Project>(`/api/v1/projects/${id}`);
      return data;
    },
    enabled: !!id,
  });
}

export function useCreateProject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (project: CreateProjectDTO) => {
      const { data } = await apiClient.post('/api/v1/projects', project);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
  });
}

export function useIndexProject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (projectId: string) => {
      const { data } = await apiClient.post(`/api/v1/projects/${projectId}/index`);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
  });
}

export function useIndexStatus(projectId: string) {
  return useQuery({
    queryKey: ['indexing', projectId],
    queryFn: async () => {
      const { data } = await apiClient.get<IndexingStatus>(
        `/api/v1/projects/${projectId}/index/status`
      );
      return data;
    },
    enabled: !!projectId,
    refetchInterval: (data) => {
      // Poll every 2 seconds if running
      return data?.status === 'running' ? 2000 : false;
    },
  });
}
```

#### 3.3. Update Projects.tsx with Real Data
**Обновить:** `src/app/components/Projects.tsx`
```typescript
import { useProjects, useCreateProject, useIndexProject } from '@/hooks/useProjects';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
// ... остальные импорты

export function Projects() {
  const navigate = useNavigate();
  const { data: projects, isLoading } = useProjects();
  const createProject = useCreateProject();
  const indexProject = useIndexProject();
  const [showCreateForm, setShowCreateForm] = useState(false);

  const handleCreateProject = async (name: string, repoPath: string) => {
    await createProject.mutateAsync({ name, repo_path: repoPath });
    setShowCreateForm(false);
  };

  const handleIndexProject = (projectId: string) => {
    indexProject.mutate(projectId);
  };

  if (isLoading) {
    return <div>Loading...</div>; // TODO: skeleton loader
  }

  return (
    <div className="space-y-6 max-w-6xl mx-auto p-8">
      {/* ... header */}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {projects?.map((project) => (
          <ProjectCard
            key={project.id}
            project={project}
            onSelect={() => navigate(`/projects/${project.id}`)}
            onIndex={() => handleIndexProject(project.id)}
          />
        ))}
      </div>

      {showCreateForm && (
        <CreateProjectModal
          onClose={() => setShowCreateForm(false)}
          onCreate={handleCreateProject}
        />
      )}
    </div>
  );
}
```

#### 3.4. Update ProjectCard with Index Status
**Создать:** `src/app/components/ProjectCard.tsx`
```typescript
import { useIndexStatus } from '@/hooks/useProjects';
import type { Project } from '@/types/api';

export function ProjectCard({
  project,
  onSelect,
  onIndex,
}: {
  project: Project;
  onSelect: () => void;
  onIndex: () => void;
}) {
  const { data: indexStatus } = useIndexStatus(project.id);

  const isIndexing = indexStatus?.status === 'running';
  const progress = indexStatus?.progress || 0;

  return (
    <Card className="p-5 cursor-pointer" onClick={onSelect}>
      <div className="flex items-start justify-between mb-4">
        <h3 className="font-bold">{project.name}</h3>
        {isIndexing && (
          <div className="w-8 h-8 rounded-full border-2 border-[#30363D] border-t-[#00D4FF] animate-spin" />
        )}
      </div>

      {isIndexing && (
        <div className="space-y-1.5">
          <div className="flex justify-between text-xs">
            <span>Индексация</span>
            <span className="text-[#00D4FF]">{progress}%</span>
          </div>
          <Progress value={progress} />
        </div>
      )}

      <Button onClick={(e) => { e.stopPropagation(); onIndex(); }}>
        Re-index
      </Button>
    </Card>
  );
}
```

### Definition of Done (Week 3)
- [ ] Projects.tsx показывает реальные проекты из API
- [ ] Создание нового проекта работает
- [ ] Прогресс индексации обновляется (polling)
- [ ] Клик на проект → переход на /projects/:id

---

## Week 4-5: Plan Generation & Diff Integration

### Задачи (3-4 дня)

#### 4.1. Create Plan Types & Hooks
**Обновить:** `src/types/api.ts`
```typescript
export interface PlanStep {
  description: string;
  files: string[];
  reasoning?: string;
}

export interface Plan {
  id: string;
  project_id: string;
  user_prompt: string;
  steps: PlanStep[];
  status: 'pending' | 'generating' | 'ready' | 'failed';
  created_at: string;
}

export interface Diff {
  id: string;
  plan_id: string;
  file_path: string;
  diff_content: string;
  status: 'pending' | 'applied' | 'rejected';
  created_at: string;
}
```

**Создать:** `src/hooks/usePlans.ts`
```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';

export function usePlans(projectId: string) {
  return useQuery({
    queryKey: ['plans', projectId],
    queryFn: async () => {
      const { data } = await apiClient.get(`/api/v1/projects/${projectId}/plans`);
      return data;
    },
  });
}

export function useCreatePlan() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ projectId, prompt }: { projectId: string; prompt: string }) => {
      const { data } = await apiClient.post(`/api/v1/projects/${projectId}/plan`, {
        prompt,
      });
      return data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['plans', variables.projectId] });
    },
  });
}

export function usePlanDiffs(planId: string) {
  return useQuery({
    queryKey: ['diffs', planId],
    queryFn: async () => {
      const { data } = await apiClient.get(`/api/v1/plans/${planId}/diffs`);
      return data;
    },
  });
}

export function useApplyDiff() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (diffId: string) => {
      const { data } = await apiClient.post(`/api/v1/diffs/${diffId}/apply`);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['diffs'] });
    },
  });
}
```

#### 4.2. Update ProjectDetail with Real Plans
**Обновить:** `src/app/components/ProjectDetail.tsx`
```typescript
import { useParams } from 'react-router-dom';
import { useProject } from '@/hooks/useProjects';
import { usePlans, useCreatePlan, usePlanDiffs } from '@/hooks/usePlans';
import { useState } from 'react';

export function ProjectDetail() {
  const { id } = useParams<{ id: string }>();
  const { data: project } = useProject(id!);
  const { data: plans } = usePlans(id!);
  const createPlan = useCreatePlan();
  const [prompt, setPrompt] = useState('');
  const [selectedPlanId, setSelectedPlanId] = useState<string | null>(null);

  const handleCreatePlan = async () => {
    if (!id || !prompt.trim()) return;
    await createPlan.mutateAsync({ projectId: id, prompt });
    setPrompt('');
  };

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <header className="px-6 py-4 border-b border-[#30363D]">
        <h1 className="text-xl font-bold">{project?.name}</h1>

        <div className="mt-4">
          <input
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Что нужно добавить или изменить?"
            className="w-full bg-[#0D1117] border border-[#30363D] rounded p-3"
          />
          <Button onClick={handleCreatePlan} disabled={!prompt.trim()}>
            Создать план
          </Button>
        </div>
      </header>

      {/* Plans List */}
      <div className="flex-1 overflow-y-auto p-6">
        {plans?.map((plan) => (
          <PlanCard
            key={plan.id}
            plan={plan}
            onSelect={() => setSelectedPlanId(plan.id)}
          />
        ))}
      </div>
    </div>
  );
}
```

#### 4.3. Update DiffViewer Component
**Обновить:** `src/app/components/DiffViewer.tsx`
```typescript
import { usePlanDiffs, useApplyDiff } from '@/hooks/usePlans';
import ReactDiffViewer from 'react-diff-viewer-continued';

export function DiffViewer({ diffId, onClose }: { diffId: string; onClose: () => void }) {
  const { data: diff } = usePlanDiffs(diffId);
  const applyDiff = useApplyDiff();

  const handleApply = () => {
    applyDiff.mutate(diffId);
    onClose();
  };

  if (!diff) return null;

  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50">
      <div className="bg-[#0D1117] border border-[#30363D] rounded-lg w-[90%] h-[90%] flex flex-col">
        <header className="p-4 border-b border-[#30363D] flex justify-between">
          <h2 className="font-bold">{diff.file_path}</h2>
          <div className="flex gap-2">
            <Button variant="primary" onClick={handleApply}>
              Apply
            </Button>
            <Button variant="ghost" onClick={onClose}>
              Close
            </Button>
          </div>
        </header>

        <div className="flex-1 overflow-auto">
          <ReactDiffViewer
            oldValue={diff.original_content}
            newValue={diff.new_content}
            splitView={true}
            useDarkTheme={true}
          />
        </div>
      </div>
    </div>
  );
}
```

### Definition of Done (Week 4-5)
- [ ] Создание плана работает через UI
- [ ] Список планов показывается из API
- [ ] DiffViewer показывает реальный diff
- [ ] Apply diff применяет изменения

---

## Week 6-7: WebSocket Real-Time Updates

### Задачи (3-4 дня)

#### 6.1. Create WebSocket Client
**Создать:** `src/lib/websocket.ts`
```typescript
export class JobStream {
  private ws: WebSocket | null = null;
  private jobId: string;

  constructor(jobId: string) {
    this.jobId = jobId;
  }

  connect(callbacks: {
    onProgress?: (data: any) => void;
    onComplete?: (data: any) => void;
    onError?: (error: string) => void;
  }) {
    const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';
    this.ws = new WebSocket(`${wsUrl}/ws/${this.jobId}`);

    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);

      switch (message.type) {
        case 'progress':
          callbacks.onProgress?.(message.data);
          break;
        case 'complete':
          callbacks.onComplete?.(message.data);
          break;
        case 'error':
          callbacks.onError?.(message.data.error);
          break;
      }
    };

    this.ws.onerror = () => {
      callbacks.onError?.('WebSocket connection failed');
    };
  }

  disconnect() {
    this.ws?.close();
  }
}
```

#### 6.2. Create useJobStream Hook
**Создать:** `src/hooks/useJobStream.ts`
```typescript
import { useEffect, useState } from 'react';
import { JobStream } from '@/lib/websocket';

export function useJobStream(jobId: string | null) {
  const [progress, setProgress] = useState(0);
  const [isComplete, setIsComplete] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!jobId) return;

    const stream = new JobStream(jobId);

    stream.connect({
      onProgress: (data) => setProgress(data.progress),
      onComplete: () => setIsComplete(true),
      onError: (err) => setError(err),
    });

    return () => stream.disconnect();
  }, [jobId]);

  return { progress, isComplete, error };
}
```

#### 6.3. Update ProjectCard with WebSocket
**Обновить:** `src/app/components/ProjectCard.tsx`
```typescript
import { useJobStream } from '@/hooks/useJobStream';

export function ProjectCard({ project }: { project: Project }) {
  const indexStatus = useIndexStatus(project.id);
  const { progress, isComplete } = useJobStream(indexStatus.data?.job_id);

  useEffect(() => {
    if (isComplete) {
      // Refetch project status
      queryClient.invalidateQueries(['projects', project.id]);
    }
  }, [isComplete]);

  return (
    <Card>
      {/* ... */}
      <Progress value={progress} />
    </Card>
  );
}
```

### Definition of Done (Week 6-7)
- [ ] WebSocket connection работает
- [ ] Progress обновляется в real-time
- [ ] Toast notifications при complete/error

---

## Week 8-9: Org Settings & Usage Dashboard

### Задачи (2-3 дня)

#### 8.1. Update OrgSettings.tsx
**Обновить:** `src/app/components/OrgSettings.tsx`
```typescript
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';

export function OrgSettings() {
  const { data: usage } = useQuery({
    queryKey: ['org-usage'],
    queryFn: async () => {
      const { data } = await apiClient.get('/api/v1/orgs/me/usage');
      return data;
    },
  });

  const { data: subscription } = useQuery({
    queryKey: ['subscription'],
    queryFn: async () => {
      const { data } = await apiClient.get('/api/v1/orgs/me/subscription');
      return data;
    },
  });

  return (
    <div className="p-8 space-y-8">
      <section>
        <h2 className="text-lg font-bold mb-4">Current Plan</h2>
        <Card className="p-6">
          <div className="flex justify-between">
            <div>
              <p className="text-2xl font-bold">{subscription?.plan}</p>
              <p className="text-sm text-[#7D8590]">
                {subscription?.status === 'active' ? 'Active' : 'Inactive'}
              </p>
            </div>
            <Button variant="primary">Upgrade</Button>
          </div>
        </Card>
      </section>

      <section>
        <h2 className="text-lg font-bold mb-4">Usage This Month</h2>
        <div className="grid grid-cols-3 gap-4">
          <Card className="p-4">
            <p className="text-sm text-[#7D8590]">API Calls</p>
            <p className="text-2xl font-bold">{usage?.api_calls || 0}</p>
          </Card>
          <Card className="p-4">
            <p className="text-sm text-[#7D8590]">Plans Generated</p>
            <p className="text-2xl font-bold">{usage?.plans_generated || 0}</p>
          </Card>
          <Card className="p-4">
            <p className="text-sm text-[#7D8590]">Embeddings</p>
            <p className="text-2xl font-bold">{usage?.embeddings || 0}</p>
          </Card>
        </div>
      </section>

      <section>
        <h2 className="text-lg font-bold mb-4">Usage Chart</h2>
        <BarChart width={600} height={300} data={usage?.history || []}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis />
          <Tooltip />
          <Bar dataKey="api_calls" fill="#00D4FF" />
        </BarChart>
      </section>
    </div>
  );
}
```

### Definition of Done (Week 8-9)
- [ ] OrgSettings показывает реальную usage статистику
- [ ] Recharts графики работают
- [ ] Current plan отображается

---

## Week 10-12: Polish & Error Handling

### Задачи (3-4 дня)

#### 10.1. Error Boundary
**Создать:** `src/app/components/ErrorBoundary.tsx`
```typescript
import { Component, ReactNode } from 'react';

export class ErrorBoundary extends Component<
  { children: ReactNode },
  { hasError: boolean }
> {
  state = { hasError: false };

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-[#0D1117]">
          <div className="text-center">
            <h1 className="text-2xl font-bold mb-4">Oops! Something went wrong</h1>
            <Button onClick={() => window.location.reload()}>Reload</Button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
```

#### 10.2. Loading States
**Создать:** `src/app/components/SkeletonLoader.tsx`
```typescript
export function ProjectCardSkeleton() {
  return (
    <Card className="p-5 animate-pulse">
      <div className="h-6 bg-[#30363D] rounded w-3/4 mb-4"></div>
      <div className="h-4 bg-[#30363D] rounded w-1/2"></div>
    </Card>
  );
}
```

#### 10.3. Toast Notifications
```bash
npm install sonner
```

**Обновить:** `src/main.tsx`
```typescript
import { Toaster } from 'sonner';

// В App:
<Toaster theme="dark" />
```

**Использование:**
```typescript
import { toast } from 'sonner';

createPlan.mutate(data, {
  onSuccess: () => toast.success('Plan created!'),
  onError: () => toast.error('Failed to create plan'),
});
```

### Definition of Done (Week 10-12)
- [ ] Error boundaries везде
- [ ] Skeleton loaders для всех списков
- [ ] Toast notifications для всех actions
- [ ] Empty states (нет проектов, нет планов)

---

## Checklist: Complete Frontend Integration

### Architecture
- [ ] React Router для навигации
- [ ] React Query для API state
- [ ] Zustand для auth state
- [ ] Axios для API calls
- [ ] WebSocket для real-time

### Pages
- [ ] LoginPage - работает с backend
- [ ] Dashboard - показывает реальную статистику
- [ ] Projects - CRUD операции
- [ ] ProjectDetail - планы и диффы
- [ ] OrgSettings - usage metrics

### Components
- [ ] DiffViewer - react-diff-viewer
- [ ] ProgressBar - real-time WebSocket updates
- [ ] ErrorBoundary - error handling
- [ ] SkeletonLoader - loading states

### UX
- [ ] Toast notifications (sonner)
- [ ] Optimistic updates
- [ ] Error messages
- [ ] Empty states
- [ ] Loading states

---

## Next Steps → Phase 2

После завершения Phase 1 frontend готов к:
- Multi-agent интерфейсам (PM, Marketing, SEO modes)
- Team collaboration features
- Advanced analytics dashboard
- VS Code Extension web view sync
