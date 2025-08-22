# ${project_name} - React Development Guide

## Environment Setup

### Node.js and React Installation

```bash

# Ensure Node.js is installed (v18 or higher recommended)

node --version
npm --version

# Create React application with TypeScript

npx create-react-app ${project_name} --template typescript
cd ${project_name}

# Or using Vite (recommended for better performance)

npm create vite@latest ${project_name} -- --template react-ts
cd ${project_name}
npm install
```

### Dependencies Installation

```bash

# Core dependencies

npm install @reduxjs/toolkit react-redux
npm install react-router-dom
npm install react-hook-form @hookform/resolvers yup
npm install axios
npm install classnames
npm install react-hot-toast

# UI and Styling

npm install tailwindcss postcss autoprefixer
npm install @headlessui/react @heroicons/react
npm install framer-motion

# Development dependencies

npm install --save-dev @types/node
npm install --save-dev eslint @typescript-eslint/parser @typescript-eslint/eslint-plugin
npm install --save-dev prettier eslint-config-prettier eslint-plugin-prettier
npm install --save-dev @testing-library/react @testing-library/jest-dom @testing-library/user-event
npm install --save-dev msw
npm install --save-dev husky lint-staged

# Performance and optimization

npm install react-window react-window-infinite-loader
npm install @react-aria/focus @react-aria/dialog @react-aria/overlays
```

### Project Configuration

#### TypeScript Configuration

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "lib": ["dom", "dom.iterable", "ES6"],
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
      "@/types/*": ["types/*"],
      "@/assets/*": ["assets/*"]
    }
  },
  "include": ["src"],
  "exclude": ["node_modules"]
}
```

#### ESLint Configuration

```json
{
  "extends": [
    "react-app",
    "react-app/jest",
    "@typescript-eslint/recommended",
    "prettier"
  ],
  "plugins": ["@typescript-eslint", "prettier"],
  "rules": {
    "prettier/prettier": "error",
    "@typescript-eslint/no-unused-vars": ["error", { "argsIgnorePattern": "^_" }],
    "@typescript-eslint/explicit-function-return-type": "off",
    "@typescript-eslint/explicit-module-boundary-types": "off",
    "@typescript-eslint/no-explicit-any": "warn",
    "react-hooks/exhaustive-deps": "warn",
    "react/prop-types": "off",
    "react/react-in-jsx-scope": "off"
  }
}
```

#### Prettier Configuration

```json
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 80,
  "tabWidth": 2,
  "useTabs": false,
  "bracketSpacing": true,
  "arrowParens": "avoid"
}
```

#### Tailwind CSS Configuration

```bash

# Initialize Tailwind CSS

npx tailwindcss init -p
```

```javascript
// tailwind.config.js
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          900: '#1e3a8a',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      animation: {
        'fade-in': 'fadeIn 0.2s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
};
```

#### Package.json Scripts

```json
{
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "test:coverage": "react-scripts test --coverage --watchAll=false",
    "eject": "react-scripts eject",
    "lint": "eslint src/**/*.{ts,tsx}",
    "lint:fix": "eslint src/**/*.{ts,tsx} --fix",
    "format": "prettier --write src/**/*.{ts,tsx,css,md}",
    "type-check": "tsc --noEmit",
    "pre-commit": "lint-staged",
    "storybook": "start-storybook -p 6006",
    "build-storybook": "build-storybook"
  },
  "lint-staged": {
    "src/**/*.{ts,tsx}": [
      "eslint --fix",
      "prettier --write"
    ]
  }
}
```

## Development Workflow

### Component Development Pattern

```bash

# Create new component directory structure

mkdir -p src/components/ui/ComponentName
touch src/components/ui/ComponentName/ComponentName.tsx
touch src/components/ui/ComponentName/ComponentName.module.css
touch src/components/ui/ComponentName/ComponentName.test.tsx
touch src/components/ui/ComponentName/ComponentName.stories.tsx
touch src/components/ui/ComponentName/index.ts
```

#### Component Template

```tsx
// src/components/ui/ComponentName/ComponentName.tsx
import React from 'react';
import classNames from 'classnames';
import styles from './ComponentName.module.css';

export interface ComponentNameProps {
  /** Component description */
  children?: React.ReactNode;
  /** Additional CSS classes */
  className?: string;
  /** Test identifier */
  'data-testid'?: string;
}

export const ComponentName: React.FC<ComponentNameProps> = ({
  children,
  className,
  'data-testid': testId,
  ...props
}) => {
  const componentClasses = classNames(
    styles.componentName,
    className
  );

  return (
    <div
      className={componentClasses}
      data-testid={testId}
      {...props}
    >
      {children}
    </div>
  );
};

export default ComponentName;
```

#### Index Export Pattern

```tsx
// src/components/ui/ComponentName/index.ts
export { ComponentName } from './ComponentName';
export type { ComponentNameProps } from './ComponentName';
```

### Testing Setup and Patterns

#### Test Setup

```tsx
// src/tests/setup.ts
import '@testing-library/jest-dom';

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

// Mock ResizeObserver
global.ResizeObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}));
```

#### Test Utilities

```tsx
// src/tests/utils.tsx
import React from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { Provider } from 'react-redux';
import { BrowserRouter } from 'react-router-dom';
import { store } from '@/store';

interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  initialEntries?: string[];
  store?: typeof store;
}

const AllProviders: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <Provider store={store}>
      <BrowserRouter>
        {children}
      </BrowserRouter>
    </Provider>
  );
};

export const renderWithProviders = (
  ui: React.ReactElement,
  options: CustomRenderOptions = {}
) => {
  return render(ui, {
    wrapper: AllProviders,
    ...options,
  });
};

export * from '@testing-library/react';
export { renderWithProviders as render };

// Custom render hook with providers
import { renderHook, RenderHookOptions } from '@testing-library/react';

export const renderHookWithProviders = <TProps, TResult>(
  hook: (props: TProps) => TResult,
  options: RenderHookOptions<TProps> = {}
) => {
  return renderHook(hook, {
    wrapper: AllProviders,
    ...options,
  });
};
```

#### Component Testing Example

```tsx
// src/components/ui/Button/Button.test.tsx
import React from 'react';
import { screen, fireEvent } from '@testing-library/react';
import { render } from '@/tests/utils';
import { Button } from './Button';

describe('Button', () => {
  it('renders button with text', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByRole('button', { name: /click me/i })).toBeInTheDocument();
  });

  it('calls onClick handler when clicked', () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Click me</Button>);

    fireEvent.click(screen.getByRole('button'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('disables button when loading', () => {
    render(<Button loading>Click me</Button>);
    expect(screen.getByRole('button')).toBeDisabled();
  });

  it('applies custom className', () => {
    render(<Button className="custom-class">Click me</Button>);
    expect(screen.getByRole('button')).toHaveClass('custom-class');
  });

  it('renders with correct variant styles', () => {
    render(<Button variant="primary">Primary</Button>);
    expect(screen.getByRole('button')).toHaveClass('primary');
  });

  describe('accessibility', () => {
    it('has proper ARIA attributes', () => {
      render(<Button disabled>Disabled button</Button>);
      const button = screen.getByRole('button');
      expect(button).toHaveAttribute('disabled');
    });

    it('supports custom test id', () => {
      render(<Button data-testid="custom-button">Test</Button>);
      expect(screen.getByTestId('custom-button')).toBeInTheDocument();
    });
  });
});
```

#### Hook Testing Example

```tsx
// src/hooks/useLocalStorage.test.tsx
import { renderHook, act } from '@testing-library/react';
import { useLocalStorage } from './useLocalStorage';

const localStorageMock = (() => {
  let store: Record<string, string> = {};

  return {
    getItem: jest.fn((key: string) => store[key] || null),
    setItem: jest.fn((key: string, value: string) => {
      store[key] = value;
    }),
    removeItem: jest.fn((key: string) => {
      delete store[key];
    }),
    clear: jest.fn(() => {
      store = {};
    }),
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

describe('useLocalStorage', () => {
  beforeEach(() => {
    localStorageMock.clear();
    jest.clearAllMocks();
  });

  it('returns initial value when localStorage is empty', () => {
    const { result } = renderHook(() => useLocalStorage('test-key', 'initial'));
    expect(result.current[0]).toBe('initial');
  });

  it('returns stored value from localStorage', () => {
    localStorageMock.setItem('test-key', JSON.stringify('stored'));
    const { result } = renderHook(() => useLocalStorage('test-key', 'initial'));
    expect(result.current[0]).toBe('stored');
  });

  it('updates localStorage when value changes', () => {
    const { result } = renderHook(() => useLocalStorage('test-key', 'initial'));

    act(() => {
      result.current[1]('updated');
    });

    expect(localStorageMock.setItem).toHaveBeenCalledWith(
      'test-key',
      JSON.stringify('updated')
    );
    expect(result.current[0]).toBe('updated');
  });

  it('removes item from localStorage', () => {
    const { result } = renderHook(() => useLocalStorage('test-key', 'initial'));

    act(() => {
      result.current[2](); // removeValue
    });

    expect(localStorageMock.removeItem).toHaveBeenCalledWith('test-key');
    expect(result.current[0]).toBe('initial');
  });
});
```

### Mock Service Worker (MSW) Setup

#### API Mocking Setup

```tsx
// src/mocks/handlers.ts
import { rest } from 'msw';
import { ${model_name} } from '@/types/${feature}';

const mockItems: ${model_name}[] = [
  {
    id: '1',
    title: 'Mock ${model_name} 1',
    description: 'This is a mock ${model_name_lower}',
    status: 'published',
    createdAt: '2024-01-01T00:00:00Z',
  },
  {
    id: '2',
    title: 'Mock ${model_name} 2',
    description: 'Another mock ${model_name_lower}',
    status: 'draft',
    createdAt: '2024-01-02T00:00:00Z',
  },
];

export const handlers = [
  // Get all items
  rest.get('/api/${model_name_lower}s', (req, res, ctx) => {
    return res(ctx.json(mockItems));
  }),

  // Get single item
  rest.get('/api/${model_name_lower}s/:id', (req, res, ctx) => {
    const { id } = req.params;
    const item = mockItems.find(item => item.id === id);

    if (!item) {
      return res(ctx.status(404), ctx.json({ message: 'Not found' }));
    }

    return res(ctx.json(item));
  }),

  // Create item
  rest.post('/api/${model_name_lower}s', async (req, res, ctx) => {
    const body = await req.json();
    const newItem: ${model_name} = {
      id: String(mockItems.length + 1),
      ...body,
      createdAt: new Date().toISOString(),
    };

    mockItems.push(newItem);
    return res(ctx.status(201), ctx.json(newItem));
  }),

  // Update item
  rest.put('/api/${model_name_lower}s/:id', async (req, res, ctx) => {
    const { id } = req.params;
    const body = await req.json();
    const itemIndex = mockItems.findIndex(item => item.id === id);

    if (itemIndex === -1) {
      return res(ctx.status(404), ctx.json({ message: 'Not found' }));
    }

    mockItems[itemIndex] = { ...mockItems[itemIndex], ...body };
    return res(ctx.json(mockItems[itemIndex]));
  }),

  // Delete item
  rest.delete('/api/${model_name_lower}s/:id', (req, res, ctx) => {
    const { id } = req.params;
    const itemIndex = mockItems.findIndex(item => item.id === id);

    if (itemIndex === -1) {
      return res(ctx.status(404), ctx.json({ message: 'Not found' }));
    }

    mockItems.splice(itemIndex, 1);
    return res(ctx.status(204));
  }),

  // Authentication
  rest.post('/api/auth/login', async (req, res, ctx) => {
    const { email, password } = await req.json();

    if (email === 'test@example.com' && password === 'password') {
      return res(
        ctx.json({
          user: {
            id: '1',
            email: 'test@example.com',
            name: 'Test User',
          },
          token: 'mock-jwt-token',
        })
      );
    }

    return res(
      ctx.status(401),
      ctx.json({ message: 'Invalid credentials' })
    );
  }),
];

// src/mocks/browser.ts
import { setupWorker } from 'msw';
import { handlers } from './handlers';

export const worker = setupWorker(...handlers);

// src/mocks/server.ts
import { setupServer } from 'msw/node';
import { handlers } from './handlers';

export const server = setupServer(...handlers);
```

#### Integration with Tests

```tsx
// src/setupTests.ts
import '@testing-library/jest-dom';
import { server } from './mocks/server';

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

### Performance Optimization Techniques

#### Code Splitting with React.lazy

```tsx
// src/pages/LazyPages.tsx
import React, { Suspense } from 'react';
import { Routes, Route } from 'react-router-dom';
import { Spinner } from '@/components/ui/Spinner';

// Lazy load page components
const HomePage = React.lazy(() => import('./Home'));
const AboutPage = React.lazy(() => import('./About'));
const ${model_name}Page = React.lazy(() => import('./${model_name}'));

export const AppRoutes: React.FC = () => {
  return (
    <Suspense fallback={<Spinner />}>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/about" element={<AboutPage />} />
        <Route path="/${model_name_lower}s" element={<${model_name}Page />} />
      </Routes>
    </Suspense>
  );
};
```

#### Memoization Strategies

```tsx
// src/components/optimized/${model_name}List.tsx
import React, { memo, useMemo, useCallback } from 'react';
import { ${model_name} } from '@/types/${feature}';

interface ${model_name}ListProps {
  items: ${model_name}[];
  onItemClick: (id: string) => void;
  searchTerm: string;
}

// Memoized list item component
const ${model_name}Item = memo<{
  item: ${model_name};
  onClick: (id: string) => void;
}>(({ item, onClick }) => {
  const handleClick = useCallback(() => {
    onClick(item.id);
  }, [item.id, onClick]);

  return (
    <div className="item" onClick={handleClick}>
      <h3>{item.title}</h3>
      <p>{item.description}</p>
    </div>
  );
});

${model_name}Item.displayName = '${model_name}Item';

// Memoized list component
export const ${model_name}List = memo<${model_name}ListProps>(({
  items,
  onItemClick,
  searchTerm,
}) => {
  // Memoized filtered items
  const filteredItems = useMemo(() => {
    if (!searchTerm) return items;

    return items.filter(item =>
      item.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.description.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [items, searchTerm]);

  // Memoized click handler
  const handleItemClick = useCallback((id: string) => {
    onItemClick(id);
  }, [onItemClick]);

  return (
    <div className="list">
      {filteredItems.map(item => (
        <${model_name}Item
          key={item.id}
          item={item}
          onClick={handleItemClick}
        />
      ))}
    </div>
  );
});

${model_name}List.displayName = '${model_name}List';
```

#### Virtual Scrolling Implementation

```tsx
// src/components/VirtualList.tsx
import React, { memo } from 'react';
import { FixedSizeList as List, ListChildComponentProps } from 'react-window';
import { ${model_name} } from '@/types/${feature}';

interface VirtualListProps {
  items: ${model_name}[];
  height: number;
  itemHeight: number;
  onItemClick: (item: ${model_name}) => void;
}

const Row = memo<ListChildComponentProps<${model_name}[]>>(
  ({ index, style, data }) => {
    const item = data[index];

    return (
      <div style={style} className="virtual-row">
        <div className="item-content">
          <h3>{item.title}</h3>
          <p>{item.description}</p>
          <span className="item-status">{item.status}</span>
        </div>
      </div>
    );
  }
);

Row.displayName = 'VirtualListRow';

export const VirtualList: React.FC<VirtualListProps> = memo(({
  items,
  height,
  itemHeight,
  onItemClick,
}) => {
  return (
    <List
      height={height}
      itemCount={items.length}
      itemSize={itemHeight}
      itemData={items}
      overscanCount={5}
    >
      {Row}
    </List>
  );
});

VirtualList.displayName = 'VirtualList';
```

### Build Optimization

#### Bundle Analysis

```bash

# Install bundle analyzer

npm install --save-dev webpack-bundle-analyzer

# Add script to package.json

"analyze": "npm run build && npx webpack-bundle-analyzer build/static/js/*.js"

# Run analysis

npm run analyze
```

#### Environment Configuration

```bash

# .env.development

REACT_APP_API_URL=http://localhost:8000/api
REACT_APP_ENV=development
REACT_APP_LOG_LEVEL=debug

# .env.production

REACT_APP_API_URL=https://api.${project_name}.com
REACT_APP_ENV=production
REACT_APP_LOG_LEVEL=error

# .env.test

REACT_APP_API_URL=http://localhost:3001/api
REACT_APP_ENV=test
REACT_APP_LOG_LEVEL=silent
```

#### Build Configuration

```json
// package.json build optimization
{
  "scripts": {
    "build": "GENERATE_SOURCEMAP=false react-scripts build",
    "build:analyze": "npm run build && npx webpack-bundle-analyzer build/static/js/*.js",
    "build:profile": "react-scripts build --profile"
  }
}
```

### Deployment Configuration

#### Docker Setup

```dockerfile

# Dockerfile

FROM node:18-alpine as build

WORKDIR /app

# Install dependencies

COPY package*.json ./
RUN npm ci --only=production

# Copy source code

COPY . .

# Build application

RUN npm run build

# Production stage

FROM nginx:alpine

# Copy built assets

COPY --from=build /app/build /usr/share/nginx/html

# Copy nginx configuration

COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

```nginx

# nginx.conf

server {
    listen 80;
    server_name localhost;

    root /usr/share/nginx/html;
    index index.html;

    # Enable gzip compression

    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    # Handle client-side routing

    location / {
        try_files $uri $uri/ /index.html;
    }

    # Cache static assets

    location /static/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Security headers

    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
}
```

#### CI/CD Pipeline

```yaml

# .github/workflows/ci.yml

name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:

    - uses: actions/checkout@v3

    - name: Setup Node.js

      uses: actions/setup-node@v3
      with:
        node-version: '18'
        cache: 'npm'

    - name: Install dependencies

      run: npm ci

    - name: Run linter

      run: npm run lint

    - name: Run type check

      run: npm run type-check

    - name: Run tests

      run: npm run test:coverage

    - name: Upload coverage

      uses: codecov/codecov-action@v3
      with:
        file: ./coverage/lcov.info

  build:
    needs: test
    runs-on: ubuntu-latest

    steps:

    - uses: actions/checkout@v3

    - name: Setup Node.js

      uses: actions/setup-node@v3
      with:
        node-version: '18'
        cache: 'npm'

    - name: Install dependencies

      run: npm ci

    - name: Build application

      run: npm run build

    - name: Upload build artifacts

      uses: actions/upload-artifact@v3
      with:
        name: build-files
        path: build/
```

---

*Generated by Claude Builder v${version} on ${timestamp}*
