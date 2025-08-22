# ${project_name} - JavaScript Development Guide

## Development Environment Setup

### Node.js and Package Management

```bash

# Install Node.js using nvm (recommended)

curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
source ~/.bashrc

# Install and use specific Node.js version

nvm install ${node_version}
nvm use ${node_version}
nvm alias default ${node_version}

# Verify installation

node --version
npm --version
```

### Project Initialization

```bash

# Initialize new project

npm init -y

# Install core dependencies

npm install ${core_dependencies}

# Install development dependencies

npm install --save-dev ${dev_dependencies}

# Install global tools

npm install -g nodemon eslint prettier
```

### Package.json Configuration

```json
{
  "name": "${project_name}",
  "version": "1.0.0",
  "description": "${project_description}",
  "main": "src/index.js",
  "scripts": {
    "start": "node src/index.js",
    "dev": "nodemon src/index.js",
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage",
    "lint": "eslint src/**/*.js",
    "lint:fix": "eslint src/**/*.js --fix",
    "format": "prettier --write src/**/*.js",
    "build": "babel src -d dist",
    "docker:build": "docker build -t ${project_name} .",
    "docker:run": "docker run -p ${port}:${port} ${project_name}"
  },
  "keywords": ["${keyword1}", "${keyword2}", "${keyword3}"],
  "author": "${author_name} <${author_email}>",
  "license": "${license}",
  "engines": {
    "node": ">=${node_version}",
    "npm": ">=${npm_version}"
  },
  "dependencies": {
    "express": "^${express_version}",
    "mongoose": "^${mongoose_version}",
    "joi": "^${joi_version}",
    "bcryptjs": "^${bcryptjs_version}",
    "jsonwebtoken": "^${jwt_version}",
    "helmet": "^${helmet_version}",
    "cors": "^${cors_version}",
    "compression": "^${compression_version}",
    "express-rate-limit": "^${rate_limit_version}",
    "winston": "^${winston_version}",
    "dotenv": "^${dotenv_version}"
  },
  "devDependencies": {
    "jest": "^${jest_version}",
    "supertest": "^${supertest_version}",
    "mongodb-memory-server": "^${mongodb_memory_server_version}",
    "eslint": "^${eslint_version}",
    "eslint-config-airbnb-base": "^${eslint_airbnb_version}",
    "eslint-plugin-import": "^${eslint_import_version}",
    "prettier": "^${prettier_version}",
    "nodemon": "^${nodemon_version}",
    "@babel/core": "^${babel_core_version}",
    "@babel/preset-env": "^${babel_preset_version}"
  }
}
```

## Code Quality Configuration

### ESLint Configuration

```javascript
// .eslintrc.js
module.exports = {
  env: {
    es2021: true,
    node: true,
    jest: true
  },
  extends: [
    'airbnb-base'
  ],
  parserOptions: {
    ecmaVersion: 12,
    sourceType: 'module'
  },
  rules: {
    // Customize rules as needed
    'no-console': process.env.NODE_ENV === 'production' ? 'error' : 'warn',
    'no-unused-vars': ['error', {
      argsIgnorePattern: '^_',
      varsIgnorePattern: '^_'
    }],
    'prefer-const': 'error',
    'no-var': 'error',
    'object-shorthand': 'error',
    'prefer-arrow-callback': 'error',

    // Allow specific patterns
    'import/no-dynamic-require': 'off',
    'global-require': 'off',
    'no-param-reassign': ['error', {
      props: true,
      ignorePropertyModificationsFor: ['req', 'res', 'next']
    }],

    // Async/await rules
    'prefer-promise-reject-errors': 'error',
    'no-async-promise-executor': 'error',
    'require-await': 'error'
  },
  overrides: [
    {
      files: ['**/*.test.js', '**/*.spec.js'],
      rules: {
        'no-unused-expressions': 'off'
      }
    }
  ]
};
```

### Prettier Configuration

```json
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 80,
  "tabWidth": 2,
  "useTabs": false,
  "bracketSpacing": true,
  "arrowParens": "always",
  "endOfLine": "lf"
}
```

### Pre-commit Hooks

```json
{
  "husky": {
    "hooks": {
      "pre-commit": "lint-staged"
    }
  },
  "lint-staged": {
    "src/**/*.js": [
      "eslint --fix",
      "prettier --write",
      "git add"
    ]
  }
}
```

## Application Architecture

### Express.js Application Setup

```javascript
// src/app.js
const express = require('express');
const helmet = require('helmet');
const cors = require('cors');
const compression = require('compression');
const rateLimit = require('express-rate-limit');

const config = require('./config');
const { logger, requestLogger } = require('./config/logger');
const { errorHandler } = require('./utils/errors');
const routes = require('./routes');

const app = express();

// Security middleware
app.use(helmet());

// CORS configuration
app.use(cors(config.cors));

// Compression middleware
app.use(compression());

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // Limit each IP to 100 requests per windowMs
  message: 'Too many requests from this IP, please try again later',
  standardHeaders: true,
  legacyHeaders: false
});
app.use(limiter);

// Body parsing middleware
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Request logging
app.use(requestLogger);

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({
    status: 'OK',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    environment: config.app.environment
  });
});

// API routes
app.use('/api', routes);

// 404 handler
app.use('*', (req, res) => {
  res.status(404).json({
    success: false,
    error: 'Route not found'
  });
});

// Error handling middleware (must be last)
app.use(errorHandler);

// Graceful shutdown
process.on('SIGTERM', () => {
  logger.info('SIGTERM received, shutting down gracefully');
  process.exit(0);
});

process.on('SIGINT', () => {
  logger.info('SIGINT received, shutting down gracefully');
  process.exit(0);
});

module.exports = app;
```

### Database Connection Management

```javascript
// src/config/database.js
const mongoose = require('mongoose');
const { logger } = require('./logger');
const config = require('./index');

class Database {
  constructor() {
    this.isConnected = false;
  }

  async connect() {
    try {
      // Connection options
      const options = {
        useNewUrlParser: true,
        useUnifiedTopology: true,
        maxPoolSize: config.database.options.maxPoolSize,
        serverSelectionTimeoutMS: config.database.options.serverSelectionTimeoutMS,
        socketTimeoutMS: 45000,
        family: 4, // Use IPv4, skip trying IPv6
        // Performance optimizations
        bufferCommands: false,
        bufferMaxEntries: 0
      };

      await mongoose.connect(config.database.uri, options);
      this.isConnected = true;

      logger.info('Database connected successfully', {
        host: mongoose.connection.host,
        port: mongoose.connection.port,
        name: mongoose.connection.name
      });

      // Connection event handlers
      mongoose.connection.on('error', (err) => {
        logger.error('Database error:', err);
        this.isConnected = false;
      });

      mongoose.connection.on('disconnected', () => {
        logger.warn('Database disconnected');
        this.isConnected = false;
      });

      mongoose.connection.on('reconnected', () => {
        logger.info('Database reconnected');
        this.isConnected = true;
      });

    } catch (error) {
      logger.error('Database connection failed:', error);
      this.isConnected = false;
      throw error;
    }
  }

  async disconnect() {
    try {
      await mongoose.connection.close();
      this.isConnected = false;
      logger.info('Database disconnected successfully');
    } catch (error) {
      logger.error('Error disconnecting from database:', error);
      throw error;
    }
  }

  getConnectionStatus() {
    return {
      isConnected: this.isConnected,
      readyState: mongoose.connection.readyState,
      host: mongoose.connection.host,
      port: mongoose.connection.port,
      name: mongoose.connection.name
    };
  }
}

module.exports = new Database();
```

## Testing Framework Setup

### Jest Configuration

```javascript
// jest.config.js
module.exports = {
  testEnvironment: 'node',
  roots: ['<rootDir>/src', '<rootDir>/tests'],
  testMatch: [
    '**/__tests__/**/*.js',
    '**/?(*.)+(spec|test).js'
  ],
  testPathIgnorePatterns: [
    '/node_modules/',
    '/build/',
    '/dist/'
  ],
  collectCoverageFrom: [
    'src/**/*.js',
    '!src/index.js',
    '!src/config/**/*.js',
    '!**/node_modules/**'
  ],
  coverageDirectory: 'coverage',
  coverageReporters: [
    'text',
    'lcov',
    'html'
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80
    }
  },
  setupFilesAfterEnv: ['<rootDir>/tests/setup.js'],
  testTimeout: 10000,
  verbose: true,
  forceExit: true,
  clearMocks: true,
  resetMocks: true,
  restoreMocks: true
};
```

### Test Setup and Utilities

```javascript
// tests/setup.js
const { MongoMemoryServer } = require('mongodb-memory-server');
const mongoose = require('mongoose');
const { logger } = require('../src/config/logger');

let mongoServer;

// Setup before all tests
beforeAll(async () => {
  // Silence logs during testing
  logger.silent = true;

  // Start in-memory MongoDB instance
  mongoServer = await MongoMemoryServer.create();
  const mongoUri = mongoServer.getUri();

  await mongoose.connect(mongoUri, {
    useNewUrlParser: true,
    useUnifiedTopology: true
  });
});

// Cleanup after all tests
afterAll(async () => {
  await mongoose.disconnect();
  await mongoServer.stop();
});

// Clean up after each test
afterEach(async () => {
  const collections = mongoose.connection.collections;

  for (const key in collections) {
    const collection = collections[key];
    await collection.deleteMany({});
  }
});

// Global test utilities
global.testUtils = {
  // Create test user
  createTestUser: async (overrides = {}) => {
    const User = require('../src/models/User');
    const defaultUser = {
      name: 'Test User',
      email: 'test@example.com',
      password: 'password123'
    };

    return User.create({ ...defaultUser, ...overrides });
  },

  // Generate JWT token for testing
  generateAuthToken: (userId) => {
    const jwt = require('jsonwebtoken');
    const config = require('../src/config');

    return jwt.sign({ id: userId }, config.jwt.secret, {
      expiresIn: config.jwt.expiresIn
    });
  },

  // Create authenticated request headers
  authHeaders: (token) => ({
    Authorization: `Bearer ${token}`
  })
};
```

### Advanced Testing Patterns

```javascript
// tests/integration/users.test.js
const request = require('supertest');
const app = require('../../src/app');
const User = require('../../src/models/User');

describe('User API Integration Tests', () => {
  describe('POST /api/users', () => {
    const validUserData = {
      name: 'John Doe',
      email: 'john@example.com',
      password: 'password123'
    };

    it('should create a new user with valid data', async () => {
      const response = await request(app)
        .post('/api/users')
        .send(validUserData)
        .expect(201);

      expect(response.body.success).toBe(true);
      expect(response.body.data).toMatchObject({
        name: validUserData.name,
        email: validUserData.email
      });
      expect(response.body.data.password).toBeUndefined();

      // Verify user was created in database
      const user = await User.findById(response.body.data.id);
      expect(user).toBeTruthy();
      expect(user.email).toBe(validUserData.email);
    });

    it('should hash password before saving', async () => {
      const response = await request(app)
        .post('/api/users')
        .send(validUserData)
        .expect(201);

      const user = await User.findById(response.body.data.id);
      expect(user.password).not.toBe(validUserData.password);
      expect(user.password.length).toBeGreaterThan(20); // Hashed password length
    });

    it('should not allow duplicate email addresses', async () => {
      // Create first user
      await request(app)
        .post('/api/users')
        .send(validUserData)
        .expect(201);

      // Try to create second user with same email
      const response = await request(app)
        .post('/api/users')
        .send(validUserData)
        .expect(400);

      expect(response.body.success).toBe(false);
      expect(response.body.error).toContain('duplicate');
    });

    describe('Validation Tests', () => {
      const testCases = [
        {
          field: 'name',
          value: '',
          expectedError: 'Name is required'
        },
        {
          field: 'email',
          value: 'invalid-email',
          expectedError: 'Valid email is required'
        },
        {
          field: 'password',
          value: '123',
          expectedError: 'Password must be at least 6 characters'
        }
      ];

      testCases.forEach(({ field, value, expectedError }) => {
        it(`should validate ${field} field`, async () => {
          const invalidData = { ...validUserData, [field]: value };

          const response = await request(app)
            .post('/api/users')
            .send(invalidData)
            .expect(400);

          expect(response.body.success).toBe(false);
          expect(response.body.error).toContain(expectedError);
        });
      });
    });
  });

  describe('Authentication Required Endpoints', () => {
    let authToken;
    let testUser;

    beforeEach(async () => {
      testUser = await global.testUtils.createTestUser();
      authToken = global.testUtils.generateAuthToken(testUser.id);
    });

    it('should allow access with valid token', async () => {
      const response = await request(app)
        .get('/api/users/profile')
        .set(global.testUtils.authHeaders(authToken))
        .expect(200);

      expect(response.body.success).toBe(true);
    });

    it('should deny access without token', async () => {
      const response = await request(app)
        .get('/api/users/profile')
        .expect(401);

      expect(response.body.success).toBe(false);
    });

    it('should deny access with invalid token', async () => {
      const response = await request(app)
        .get('/api/users/profile')
        .set({ Authorization: 'Bearer invalid-token' })
        .expect(401);

      expect(response.body.success).toBe(false);
    });
  });
});
```

## Performance Optimization

### Caching Strategies

```javascript
// src/utils/cache.js
const redis = require('redis');
const { logger } = require('../config/logger');
const config = require('../config');

class CacheManager {
  constructor() {
    this.client = redis.createClient({
      host: config.redis.host,
      port: config.redis.port,
      password: config.redis.password,
      retry_strategy: (options) => {
        if (options.error && options.error.code === 'ECONNREFUSED') {
          logger.error('Redis server refused connection');
          return new Error('Redis server refused connection');
        }
        if (options.total_retry_time > 1000 * 60 * 60) {
          return new Error('Redis retry time exhausted');
        }
        if (options.attempt > 10) {
          return undefined;
        }
        return Math.min(options.attempt * 100, 3000);
      }
    });

    this.client.on('error', (err) => {
      logger.error('Redis client error:', err);
    });

    this.client.on('connect', () => {
      logger.info('Redis connected successfully');
    });
  }

  async get(key) {
    try {
      const value = await this.client.get(key);
      return value ? JSON.parse(value) : null;
    } catch (error) {
      logger.error('Cache get error:', error);
      return null;
    }
  }

  async set(key, value, ttl = 3600) {
    try {
      const stringValue = JSON.stringify(value);
      await this.client.setex(key, ttl, stringValue);
      return true;
    } catch (error) {
      logger.error('Cache set error:', error);
      return false;
    }
  }

  async del(key) {
    try {
      await this.client.del(key);
      return true;
    } catch (error) {
      logger.error('Cache delete error:', error);
      return false;
    }
  }

  async invalidatePattern(pattern) {
    try {
      const keys = await this.client.keys(pattern);
      if (keys.length > 0) {
        await this.client.del(...keys);
      }
      return true;
    } catch (error) {
      logger.error('Cache invalidate pattern error:', error);
      return false;
    }
  }

  // Cache decorator for methods
  cached(ttl = 3600) {
    return (target, propertyName, descriptor) => {
      const method = descriptor.value;

      descriptor.value = async function (...args) {
        const cacheKey = `${target.constructor.name}:${propertyName}:${JSON.stringify(args)}`;

        // Try to get from cache first
        const cached = await this.cache.get(cacheKey);
        if (cached !== null) {
          logger.debug('Cache hit', { key: cacheKey });
          return cached;
        }

        // Execute original method
        const result = await method.apply(this, args);

        // Store in cache
        await this.cache.set(cacheKey, result, ttl);
        logger.debug('Cache stored', { key: cacheKey });

        return result;
      };
    };
  }
}

module.exports = new CacheManager();
```

### Database Query Optimization

```javascript
// src/repositories/BaseRepository.js
class BaseRepository {
  constructor(model) {
    this.model = model;
  }

  // Optimized pagination with counting
  async findWithPagination(filters = {}, options = {}) {
    const {
      page = 1,
      limit = 10,
      sortBy = 'createdAt',
      sortOrder = 'desc',
      populate = [],
      select = ''
    } = options;

    const skip = (page - 1) * limit;
    const sort = { [sortBy]: sortOrder === 'desc' ? -1 : 1 };

    // Use aggregation for efficient counting and data retrieval
    const pipeline = [
      { $match: filters },
      { $sort: sort },
      {
        $facet: {
          data: [
            { $skip: skip },
            { $limit: limit },
            ...(select ? [{ $project: this.buildProjection(select) }] : [])
          ],
          total: [{ $count: 'count' }]
        }
      }
    ];

    const [result] = await this.model.aggregate(pipeline);
    const total = result.total[0]?.count || 0;

    let data = result.data;

    // Handle population if needed (note: less efficient with aggregation)
    if (populate.length > 0) {
      data = await this.model.populate(data, populate);
    }

    return {
      data,
      pagination: {
        page,
        limit,
        total,
        pages: Math.ceil(total / limit),
        hasNext: page < Math.ceil(total / limit),
        hasPrev: page > 1
      }
    };
  }

  // Build MongoDB projection object from select string
  buildProjection(selectString) {
    const projection = {};
    selectString.split(' ').forEach(field => {
      if (field.startsWith('-')) {
        projection[field.substring(1)] = 0;
      } else {
        projection[field] = 1;
      }
    });
    return projection;
  }

  // Bulk operations for better performance
  async bulkCreate(documents) {
    const operations = documents.map(doc => ({
      insertOne: { document: doc }
    }));

    const result = await this.model.bulkWrite(operations, {
      ordered: false,
      writeConcern: { w: 'majority' }
    });

    return result;
  }

  async bulkUpdate(updates) {
    const operations = updates.map(({ filter, update }) => ({
      updateOne: {
        filter,
        update,
        upsert: false
      }
    }));

    const result = await this.model.bulkWrite(operations, {
      ordered: false,
      writeConcern: { w: 'majority' }
    });

    return result;
  }

  // Efficient exists check
  async exists(filters) {
    const count = await this.model.countDocuments(filters).limit(1);
    return count > 0;
  }

  // Memory-efficient streaming for large datasets
  async streamProcess(filters, processor) {
    const cursor = this.model.find(filters).cursor();
    let processedCount = 0;

    for (let doc = await cursor.next(); doc != null; doc = await cursor.next()) {
      await processor(doc);
      processedCount++;

      // Log progress for long operations
      if (processedCount % 1000 === 0) {
        logger.info(`Processed ${processedCount} documents`);
      }
    }

    return processedCount;
  }
}

module.exports = BaseRepository;
```

## Security Best Practices

### Authentication and Authorization

```javascript
// src/middleware/auth.js
const jwt = require('jsonwebtoken');
const User = require('../models/User');
const { AppError } = require('../utils/errors');
const config = require('../config');
const cache = require('../utils/cache');

// JWT authentication middleware
const authenticate = async (req, res, next) => {
  try {
    const token = extractToken(req);

    if (!token) {
      throw new AppError('Access token required', 401);
    }

    // Verify JWT token
    const decoded = jwt.verify(token, config.jwt.secret);

    // Check if token is blacklisted
    const isBlacklisted = await cache.get(`blacklist:${token}`);
    if (isBlacklisted) {
      throw new AppError('Token has been revoked', 401);
    }

    // Get user from cache or database
    let user = await cache.get(`user:${decoded.id}`);
    if (!user) {
      user = await User.findById(decoded.id).select('-password');
      if (!user) {
        throw new AppError('User not found', 401);
      }
      // Cache user for future requests
      await cache.set(`user:${decoded.id}`, user, 300); // 5 minutes
    }

    req.user = user;
    next();
  } catch (error) {
    if (error.name === 'JsonWebTokenError') {
      next(new AppError('Invalid token', 401));
    } else if (error.name === 'TokenExpiredError') {
      next(new AppError('Token expired', 401));
    } else {
      next(error);
    }
  }
};

// Role-based authorization
const authorize = (...roles) => {
  return (req, res, next) => {
    if (!req.user) {
      return next(new AppError('Authentication required', 401));
    }

    if (!roles.includes(req.user.role)) {
      return next(new AppError('Insufficient permissions', 403));
    }

    next();
  };
};

// Resource ownership check
const checkOwnership = (resourceField = 'userId') => {
  return async (req, res, next) => {
    try {
      const resourceId = req.params.id;
      const userId = req.user.id;

      // Get resource from database
      const resource = await req.model.findById(resourceId);

      if (!resource) {
        return next(new AppError('Resource not found', 404));
      }

      // Check if user owns the resource or is admin
      if (resource[resourceField].toString() !== userId && req.user.role !== 'admin') {
        return next(new AppError('Access denied', 403));
      }

      req.resource = resource;
      next();
    } catch (error) {
      next(error);
    }
  };
};

// Extract token from request
const extractToken = (req) => {
  const authHeader = req.headers.authorization;

  if (authHeader && authHeader.startsWith('Bearer ')) {
    return authHeader.substring(7);
  }

  return null;
};

// Generate JWT token
const generateToken = (payload) => {
  return jwt.sign(payload, config.jwt.secret, {
    expiresIn: config.jwt.expiresIn,
    issuer: config.app.name,
    audience: config.app.name
  });
};

// Blacklist token (for logout)
const blacklistToken = async (token) => {
  const decoded = jwt.decode(token);
  const ttl = decoded.exp - Math.floor(Date.now() / 1000);

  if (ttl > 0) {
    await cache.set(`blacklist:${token}`, true, ttl);
  }
};

module.exports = {
  authenticate,
  authorize,
  checkOwnership,
  generateToken,
  blacklistToken
};
```

---

*Generated by Claude Builder v${version} on ${timestamp}*
