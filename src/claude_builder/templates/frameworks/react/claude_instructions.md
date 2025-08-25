# ${project_name} - React Development Instructions

## Project Context

${project_description}

**Framework**: React ${react_version}
**TypeScript**: ${typescript_version}
**Build Tool**: ${build_tool}
**Project Type**: ${project_type}
**Generated**: ${timestamp}

## React Development Standards

### Project Structure

```text
${project_name}/
├── public/
│   ├── index.html
│   ├── favicon.ico
│   └── manifest.json
├── src/
│   ├── components/           # Reusable UI components
│   │   ├── ui/              # Basic UI components
│   │   │   ├── Button/
│   │   │   │   ├── Button.tsx
│   │   │   │   ├── Button.module.css
│   │   │   │   ├── Button.test.tsx
│   │   │   │   └── index.ts
│   │   │   └── Input/
│   │   └── layout/          # Layout components
│   │       ├── Header/
│   │       ├── Footer/
│   │       └── Sidebar/
│   ├── pages/               # Page components
│   │   ├── Home/
│   │   │   ├── Home.tsx
│   │   │   ├── Home.module.css
│   │   │   └── index.ts
│   │   └── About/
│   ├── hooks/               # Custom React hooks
│   │   ├── useAuth.ts
│   │   ├── useApi.ts
│   │   └── useLocalStorage.ts
│   ├── services/            # API services
│   │   ├── api.ts
│   │   ├── auth.ts
│   │   └── ${service}.ts
│   ├── store/               # State management
│   │   ├── index.ts
│   │   ├── authSlice.ts
│   │   └── ${feature}Slice.ts
│   ├── utils/               # Utility functions
│   │   ├── constants.ts
│   │   ├── helpers.ts
│   │   └── validators.ts
│   ├── types/               # TypeScript type definitions
│   │   ├── api.ts
│   │   ├── auth.ts
│   │   └── ${feature}.ts
│   ├── styles/              # Global styles
│   │   ├── index.css
│   │   ├── globals.css
│   │   └── variables.css
│   ├── assets/              # Static assets
│   │   ├── images/
│   │   ├── icons/
│   │   └── fonts/
│   ├── tests/               # Test utilities
│   │   ├── __mocks__/
│   │   ├── setup.ts
│   │   └── utils.tsx
│   ├── App.tsx
│   ├── App.test.tsx
│   ├── index.tsx
│   └── react-app-env.d.ts
├── .env.example
├── .gitignore
├── package.json
├── tsconfig.json
├── tailwind.config.js       # If using Tailwind CSS
└── README.md
```

### TypeScript Configuration

```json
// tsconfig.json
{
  "compilerOptions": {
    "target": "ES2020",
    "lib": [
      "dom",
      "dom.iterable",
      "ES6"
    ],
    "allowJs": true,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "noFallthroughCasesInSwitch": true,
    "module": "esnext",
    "moduleResolution": "node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "baseUrl": "src",
    "paths": {
      "@/*": ["*"],
      "@/components/*": ["components/*"],
      "@/pages/*": ["pages/*"],
      "@/hooks/*": ["hooks/*"],
      "@/services/*": ["services/*"],
      "@/store/*": ["store/*"],
      "@/utils/*": ["utils/*"],
      "@/types/*": ["types/*"]
    }
  },
  "include": [
    "src"
  ]
}
```

### Component Best Practices

```tsx
// src/components/ui/Button/Button.tsx
import React from 'react';
import classNames from 'classnames';
import styles from './Button.module.css';

export interface ButtonProps {
  /** Button variant */
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost';
  /** Button size */
  size?: 'sm' | 'md' | 'lg';
  /** Disable the button */
  disabled?: boolean;
  /** Loading state */
  loading?: boolean;
  /** Full width button */
  fullWidth?: boolean;
  /** Button type */
  type?: 'button' | 'submit' | 'reset';
  /** Click handler */
  onClick?: (event: React.MouseEvent<HTMLButtonElement>) => void;
  /** Button content */
  children: React.ReactNode;
  /** Additional CSS classes */
  className?: string;
  /** Test ID for testing */
  'data-testid'?: string;
}

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  disabled = false,
  loading = false,
  fullWidth = false,
  type = 'button',
  onClick,
  children,
  className,
  'data-testid': testId,
  ...props
}) => {
  const handleClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    if (!disabled && !loading && onClick) {
      onClick(event);
    }
  };

  const buttonClasses = classNames(
    styles.button,
    styles[variant],
    styles[size],
    {
      [styles.disabled]: disabled,
      [styles.loading]: loading,
      [styles.fullWidth]: fullWidth,
    },
    className
  );

  return (
    <button
      type={type}
      className={buttonClasses}
      onClick={handleClick}
      disabled={disabled || loading}
      data-testid={testId}
      {...props}
    >
      {loading && <span className={styles.spinner} />}
      <span className={loading ? styles.hiddenText : ''}>{children}</span>
    </button>
  );
};

export default Button;

// src/components/ui/Button/Button.module.css
.button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid transparent;
  border-radius: 0.375rem;
  font-weight: 500;
  text-decoration: none;
  cursor: pointer;
  transition: all 0.2s ease-in-out;
  position: relative;
  white-space: nowrap;
}

.button:focus {
  outline: 2px solid var(--primary-color);
  outline-offset: 2px;
}

/* Sizes */
.sm {
  padding: 0.375rem 0.75rem;
  font-size: 0.875rem;
  line-height: 1.25rem;
}

.md {
  padding: 0.5rem 1rem;
  font-size: 1rem;
  line-height: 1.5rem;
}

.lg {
  padding: 0.75rem 1.5rem;
  font-size: 1.125rem;
  line-height: 1.75rem;
}

/* Variants */
.primary {
  background-color: var(--primary-color);
  color: white;
  border-color: var(--primary-color);
}

.primary:hover:not(.disabled):not(.loading) {
  background-color: var(--primary-hover-color);
  border-color: var(--primary-hover-color);
}

.secondary {
  background-color: var(--secondary-color);
  color: white;
  border-color: var(--secondary-color);
}

.outline {
  background-color: transparent;
  color: var(--primary-color);
  border-color: var(--primary-color);
}

.outline:hover:not(.disabled):not(.loading) {
  background-color: var(--primary-color);
  color: white;
}

.ghost {
  background-color: transparent;
  color: var(--text-color);
  border-color: transparent;
}

.ghost:hover:not(.disabled):not(.loading) {
  background-color: var(--gray-100);
}

/* States */
.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.loading {
  cursor: wait;
}

.fullWidth {
  width: 100%;
}

.spinner {
  width: 1rem;
  height: 1rem;
  border: 2px solid transparent;
  border-top-color: currentColor;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-right: 0.5rem;
}

.hiddenText {
  opacity: 0;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
```

### Custom Hooks

```tsx
// src/hooks/useApi.ts
import { useState, useEffect, useCallback } from 'react';
import { ApiResponse, ApiError } from '@/types/api';

interface UseApiOptions<T> {
  /** Initial data */
  initialData?: T;
  /** Auto-fetch on mount */
  immediate?: boolean;
  /** Dependencies for auto-refetch */
  deps?: React.DependencyList;
}

interface UseApiReturn<T> {
  data: T | null;
  error: ApiError | null;
  loading: boolean;
  execute: () => Promise<void>;
  reset: () => void;
}

export function useApi<T>(
  apiCall: () => Promise<ApiResponse<T>>,
  options: UseApiOptions<T> = {}
): UseApiReturn<T> {
  const { initialData = null, immediate = true, deps = [] } = options;

  const [data, setData] = useState<T | null>(initialData);
  const [error, setError] = useState<ApiError | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  const execute = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await apiCall();
      setData(response.data);
    } catch (err) {
      const apiError = err as ApiError;
      setError(apiError);
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [apiCall]);

  const reset = useCallback(() => {
    setData(initialData);
    setError(null);
    setLoading(false);
  }, [initialData]);

  useEffect(() => {
    if (immediate) {
      execute();
    }
  }, [execute, immediate, ...deps]);

  return { data, error, loading, execute, reset };
}

// src/hooks/useLocalStorage.ts
import { useState, useEffect, useCallback } from 'react';

type SetValue<T> = (value: T | ((prevValue: T) => T)) => void;

export function useLocalStorage<T>(
  key: string,
  initialValue: T
): [T, SetValue<T>, () => void] {
  const [storedValue, setStoredValue] = useState<T>(() => {
    if (typeof window === 'undefined') {
      return initialValue;
    }

    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      console.warn(`Error reading localStorage key "${key}":`, error);
      return initialValue;
    }
  });

  const setValue: SetValue<T> = useCallback(
    (value: T | ((prevValue: T) => T)) => {
      try {
        const valueToStore = value instanceof Function ? value(storedValue) : value;
        setStoredValue(valueToStore);

        if (typeof window !== 'undefined') {
          window.localStorage.setItem(key, JSON.stringify(valueToStore));
        }
      } catch (error) {
        console.warn(`Error setting localStorage key "${key}":`, error);
      }
    },
    [key, storedValue]
  );

  const removeValue = useCallback(() => {
    try {
      setStoredValue(initialValue);
      if (typeof window !== 'undefined') {
        window.localStorage.removeItem(key);
      }
    } catch (error) {
      console.warn(`Error removing localStorage key "${key}":`, error);
    }
  }, [key, initialValue]);

  return [storedValue, setValue, removeValue];
}

// src/hooks/useAuth.ts
import { useCallback } from 'react';
import { useAppSelector, useAppDispatch } from '@/store/hooks';
import { authSlice } from '@/store/authSlice';
import { authService } from '@/services/auth';
import { LoginCredentials, User } from '@/types/auth';

export interface UseAuthReturn {
  user: User | null;
  isAuthenticated: boolean;
  loading: boolean;
  error: string | null;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
  register: (userData: RegisterData) => Promise<void>;
  updateProfile: (profileData: Partial<User>) => Promise<void>;
  clearError: () => void;
}

export function useAuth(): UseAuthReturn {
  const dispatch = useAppDispatch();
  const { user, loading, error } = useAppSelector((state) => state.auth);

  const login = useCallback(async (credentials: LoginCredentials) => {
    dispatch(authSlice.actions.setLoading(true));
    dispatch(authSlice.actions.clearError());

    try {
      const response = await authService.login(credentials);
      dispatch(authSlice.actions.loginSuccess(response.user));
    } catch (error) {
      dispatch(authSlice.actions.setError(error.message));
    } finally {
      dispatch(authSlice.actions.setLoading(false));
    }
  }, [dispatch]);

  const logout = useCallback(() => {
    authService.logout();
    dispatch(authSlice.actions.logout());
  }, [dispatch]);

  const register = useCallback(async (userData: RegisterData) => {
    dispatch(authSlice.actions.setLoading(true));
    dispatch(authSlice.actions.clearError());

    try {
      const response = await authService.register(userData);
      dispatch(authSlice.actions.loginSuccess(response.user));
    } catch (error) {
      dispatch(authSlice.actions.setError(error.message));
    } finally {
      dispatch(authSlice.actions.setLoading(false));
    }
  }, [dispatch]);

  const updateProfile = useCallback(async (profileData: Partial<User>) => {
    if (!user) return;

    dispatch(authSlice.actions.setLoading(true));
    dispatch(authSlice.actions.clearError());

    try {
      const response = await authService.updateProfile(user.id, profileData);
      dispatch(authSlice.actions.updateUser(response.user));
    } catch (error) {
      dispatch(authSlice.actions.setError(error.message));
    } finally {
      dispatch(authSlice.actions.setLoading(false));
    }
  }, [user, dispatch]);

  const clearError = useCallback(() => {
    dispatch(authSlice.actions.clearError());
  }, [dispatch]);

  return {
    user,
    isAuthenticated: !!user,
    loading,
    error,
    login,
    logout,
    register,
    updateProfile,
    clearError,
  };
}
```

### State Management with Redux Toolkit

```tsx
// src/store/index.ts
import { configureStore } from '@reduxjs/toolkit';
import { setupListeners } from '@reduxjs/toolkit/query';
import { authSlice } from './authSlice';
import { ${feature}Slice } from './${feature}Slice';
import { api } from './api';

export const store = configureStore({
  reducer: {
    auth: authSlice.reducer,
    ${feature}: ${feature}Slice.reducer,
    api: api.reducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST', 'persist/REHYDRATE'],
      },
    }).concat(api.middleware),
  devTools: process.env.NODE_ENV !== 'production',
});

setupListeners(store.dispatch);

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

// src/store/hooks.ts
import { useDispatch, useSelector, TypedUseSelectorHook } from 'react-redux';
import type { RootState, AppDispatch } from './index';

export const useAppDispatch = () => useDispatch<AppDispatch>();
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;

// src/store/authSlice.ts
import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { User } from '@/types/auth';

interface AuthState {
  user: User | null;
  loading: boolean;
  error: string | null;
}

const initialState: AuthState = {
  user: null,
  loading: false,
  error: null,
};

export const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload;
    },
    setError: (state, action: PayloadAction<string>) => {
      state.error = action.payload;
    },
    clearError: (state) => {
      state.error = null;
    },
    loginSuccess: (state, action: PayloadAction<User>) => {
      state.user = action.payload;
      state.loading = false;
      state.error = null;
    },
    logout: (state) => {
      state.user = null;
      state.loading = false;
      state.error = null;
    },
    updateUser: (state, action: PayloadAction<User>) => {
      state.user = action.payload;
    },
  },
});

export const { actions: authActions, reducer: authReducer } = authSlice;

// src/store/api.ts (RTK Query)
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import { RootState } from './index';

export const api = createApi({
  reducerPath: 'api',
  baseQuery: fetchBaseQuery({
    baseUrl: process.env.REACT_APP_API_URL || 'http://localhost:8000/api',
    prepareHeaders: (headers, { getState }) => {
      const token = (getState() as RootState).auth.user?.token;
      if (token) {
        headers.set('authorization', `Bearer ${token}`);
      }
      return headers;
    },
  }),
  tagTypes: ['User', '${model_name}'],
  endpoints: (builder) => ({
    getUser: builder.query<User, string>({
      query: (id) => `users/${id}`,
      providesTags: ['User'],
    }),
    get${model_name}s: builder.query<${model_name}[], void>({
      query: () => '${model_name_lower}s',
      providesTags: ['${model_name}'],
    }),
    create${model_name}: builder.mutation<${model_name}, Partial<${model_name}>>({
      query: (${model_name_lower}) => ({
        url: '${model_name_lower}s',
        method: 'POST',
        body: ${model_name_lower},
      }),
      invalidatesTags: ['${model_name}'],
    }),
    update${model_name}: builder.mutation<
      ${model_name}, 
      { id: string; ${model_name_lower}: Partial<${model_name}> }
    >({
      query: ({ id, ${model_name_lower} }) => ({
        url: `${model_name_lower}s/${id}`,
        method: 'PUT',
        body: ${model_name_lower},
      }),
      invalidatesTags: ['${model_name}'],
    }),
    delete${model_name}: builder.mutation<void, string>({
      query: (id) => ({
        url: `${model_name_lower}s/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: ['${model_name}'],
    }),
  }),
});

export const {
  useGetUserQuery,
  useGet${model_name}sQuery,
  useCreate${model_name}Mutation,
  useUpdate${model_name}Mutation,
  useDelete${model_name}Mutation,
} = api;
```

### Form Handling with React Hook Form

```tsx
// src/components/forms/${model_name}Form.tsx
import React from 'react';
import { useForm, Controller } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import * as yup from 'yup';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { TextArea } from '@/components/ui/TextArea';
import { ${model_name} } from '@/types/${feature}';

const schema = yup.object({
  title: yup.string()
    .required('Title is required')
    .min(3, 'Title must be at least 3 characters'),
  description: yup.string().optional(),
  content: yup.string().required('Content is required'),
  status: yup.string().oneOf(['draft', 'published'], 'Invalid status'),
});

type FormData = yup.InferType<typeof schema>;

interface ${model_name}FormProps {
  initialData?: Partial<${model_name}>;
  onSubmit: (data: FormData) => Promise<void>;
  loading?: boolean;
}

export const ${model_name}Form: React.FC<${model_name}FormProps> = ({
  initialData,
  onSubmit,
  loading = false,
}) => {
  const {
    control,
    handleSubmit,
    formState: { errors, isValid, isDirty },
    reset,
  } = useForm<FormData>({
    resolver: yupResolver(schema),
    defaultValues: {
      title: initialData?.title || '',
      description: initialData?.description || '',
      content: initialData?.content || '',
      status: initialData?.status || 'draft',
    },
    mode: 'onChange',
  });

  const handleFormSubmit = async (data: FormData) => {
    try {
      await onSubmit(data);
      if (!initialData) {
        reset(); // Reset form after successful creation
      }
    } catch (error) {
      console.error('Form submission error:', error);
    }
  };

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">
      <Controller
        name="title"
        control={control}
        render={({ field }) => (
          <Input
            {...field}
            label="Title"
            error={errors.title?.message}
            placeholder="Enter ${model_name_lower} title"
            required
          />
        )}
      />

      <Controller
        name="description"
        control={control}
        render={({ field }) => (
          <TextArea
            {...field}
            label="Description"
            error={errors.description?.message}
            placeholder="Enter ${model_name_lower} description"
            rows={3}
          />
        )}
      />

      <Controller
        name="content"
        control={control}
        render={({ field }) => (
          <TextArea
            {...field}
            label="Content"
            error={errors.content?.message}
            placeholder="Enter ${model_name_lower} content"
            rows={6}
            required
          />
        )}
      />

      <Controller
        name="status"
        control={control}
        render={({ field }) => (
          <div className="form-group">
            <label className="form-label">Status</label>
            <select {...field} className="form-select">
              <option value="draft">Draft</option>
              <option value="published">Published</option>
            </select>
            {errors.status && (
              <p className="form-error">{errors.status.message}</p>
            )}
          </div>
        )}
      />

      <div className="flex justify-end space-x-2">
        <Button
          type="button"
          variant="outline"
          onClick={() => reset()}
          disabled={loading || !isDirty}
        >
          Reset
        </Button>
        <Button
          type="submit"
          loading={loading}
          disabled={!isValid || loading}
        >
          {initialData ? 'Update' : 'Create'} ${model_name}
        </Button>
      </div>
    </form>
  );
};
```

### Error Boundaries and Error Handling

```tsx
// src/components/ErrorBoundary.tsx
import React from 'react';

interface ErrorBoundaryState {
  hasError: boolean;
  error?: Error;
  errorInfo?: React.ErrorInfo;
}

interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ComponentType<{ error: Error; retry: () => void }>;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
}

export class ErrorBoundary extends React.Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    this.setState({ errorInfo });

    // Log error to monitoring service
    console.error('Error caught by boundary:', error, errorInfo);

    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  retry = () => {
    this.setState({ hasError: false, error: undefined, errorInfo: undefined });
  };

  render() {
    if (this.state.hasError && this.state.error) {
      const FallbackComponent = this.props.fallback || DefaultErrorFallback;
      return <FallbackComponent error={this.state.error} retry={this.retry} />;
    }

    return this.props.children;
  }
}

const DefaultErrorFallback: React.FC<{ error: Error; retry: () => void }> = ({
  error,
  retry,
}) => (
  <div className="error-boundary">
    <h2>Something went wrong</h2>
    <details>
      <summary>Error details</summary>
      <pre>{error.message}</pre>
    </details>
    <button onClick={retry}>Try again</button>
  </div>
);

// src/hooks/useErrorHandler.ts
import { useCallback } from 'react';
import { toast } from 'react-hot-toast';

interface ErrorHandlerOptions {
  showToast?: boolean;
  logError?: boolean;
  rethrow?: boolean;
}

export function useErrorHandler() {
  const handleError = useCallback(
    (error: unknown, options: ErrorHandlerOptions = {}) => {
      const {
        showToast = true,
        logError = true,
        rethrow = false,
      } = options;

      const errorMessage = error instanceof Error ? 
        error.message : 'An unexpected error occurred';

      if (logError) {
        console.error('Error handled:', error);
      }

      if (showToast) {
        toast.error(errorMessage);
      }

      if (rethrow) {
        throw error;
      }
    },
    []
  );

  return { handleError };
}
```

### Performance Optimization

```tsx
// src/components/LazyComponent.tsx
import React, { Suspense, lazy } from 'react';
import { Spinner } from '@/components/ui/Spinner';

// Lazy load components for code splitting
const Heavy${model_name}Component = lazy(() =>
  import('./Heavy${model_name}Component').then(module => ({
    default: module.Heavy${model_name}Component
  }))
);

export const LazyComponent: React.FC = () => {
  return (
    <Suspense fallback={<Spinner />}>
      <Heavy${model_name}Component />
    </Suspense>
  );
};

// src/components/VirtualizedList.tsx
import React, { memo, useMemo } from 'react';
import { FixedSizeList as List } from 'react-window';
import { ${model_name} } from '@/types/${feature}';

interface VirtualizedListProps {
  items: ${model_name}[];
  height: number;
  itemHeight: number;
  onItemClick: (item: ${model_name}) => void;
}

const ListItem = memo<{
  index: number;
  style: React.CSSProperties;
  data: { items: ${model_name}[]; onItemClick: (item: ${model_name}) => void };
}>(({ index, style, data }) => {
  const item = data.items[index];

  return (
    <div style={style}>
      <div
        className="list-item"
        onClick={() => data.onItemClick(item)}
      >
        <h3>{item.title}</h3>
        <p>{item.description}</p>
      </div>
    </div>
  );
});

ListItem.displayName = 'ListItem';

export const VirtualizedList: React.FC<VirtualizedListProps> = memo(({
  items,
  height,
  itemHeight,
  onItemClick,
}) => {
  const itemData = useMemo(
    () => ({ items, onItemClick }),
    [items, onItemClick]
  );

  return (
    <List
      height={height}
      itemCount={items.length}
      itemSize={itemHeight}
      itemData={itemData}
    >
      {ListItem}
    </List>
  );
});

VirtualizedList.displayName = 'VirtualizedList';

// src/hooks/useDebounce.ts
import { useState, useEffect } from 'react';

export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}

// Usage in search component
export const SearchComponent: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const debouncedSearchTerm = useDebounce(searchTerm, 300);

  const { data: searchResults } = useGet${model_name}sQuery({
    search: debouncedSearchTerm,
  }, {
    skip: !debouncedSearchTerm,
  });

  return (
    <div>
      <input
        type="text"
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
        placeholder="Search ${model_name_lower}s..."
      />
      {/* Render search results */}
    </div>
  );
};
```

### Accessibility Best Practices

```tsx
// src/components/ui/Modal/Modal.tsx
import React, { useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import { FocusScope } from '@react-aria/focus';
import { useDialog } from '@react-aria/dialog';
import { useModal, useOverlay } from '@react-aria/overlays';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl';
}

export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  children,
  size = 'md',
}) => {
  const ref = useRef<HTMLDivElement>(null);
  const { modalProps, underlayProps } = useModal();
  const { overlayProps } = useOverlay(
    {
      isOpen,
      onClose,
      shouldCloseOnBlur: true,
      isDismissable: true,
    },
    ref
  );
  const { dialogProps, titleProps } = useDialog({}, ref);

  // Focus management
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }

    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  if (!isOpen) return null;

  const modal = (
    <div className="modal-overlay" {...underlayProps}>
      <FocusScope contain restoreFocus autoFocus>
        <div
          className={`modal modal-${size}`}
          {...overlayProps}
          {...dialogProps}
          {...modalProps}
          ref={ref}
        >
          <div className="modal-header">
            <h2 {...titleProps} className="modal-title">
              {title}
            </h2>
            <button
              type="button"
              className="modal-close"
              onClick={onClose}
              aria-label="Close modal"
            >
              ×
            </button>
          </div>
          <div className="modal-body">{children}</div>
        </div>
      </FocusScope>
    </div>
  );

  return createPortal(modal, document.body);
};

// src/components/ui/Input/Input.tsx
import React, { forwardRef } from 'react';
import classNames from 'classnames';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  required?: boolean;
  fullWidth?: boolean;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    { label, error, helperText, required, fullWidth, className, id, ...props },
    ref
  ) => {
    const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`;
    const errorId = error ? `${inputId}-error` : undefined;
    const helperTextId = helperText ? `${inputId}-helper` : undefined;

    return (
      <div className={classNames('form-group', { 'full-width': fullWidth })}>
        {label && (
          <label htmlFor={inputId} className="form-label">
            {label}
            {required && (
              <span className="required-indicator" aria-hidden="true"> *</span>
            )}
          </label>
        )}
        <input
          ref={ref}
          id={inputId}
          className={classNames(
            'form-input',
            {
              'error': error,
            },
            className
          )}
          aria-invalid={error ? 'true' : 'false'}
          aria-describedby={classNames(errorId, helperTextId)
            .split(' ')
            .filter(Boolean)
            .join(' ') || undefined}
          required={required}
          {...props}
        />
        {helperText && (
          <p id={helperTextId} className="form-helper-text">
            {helperText}
          </p>
        )}
        {error && (
          <p id={errorId} className="form-error" role="alert">
            {error}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';
```

---

*Generated by Claude Builder v${version} on ${timestamp}*
