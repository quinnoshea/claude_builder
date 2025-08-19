# ${project_name} - JavaScript Agent Configuration

## JavaScript-Specific Agent Assignments

### Primary Development Agents

#### backend-architect
**Primary Role**: Node.js backend systems, API design, microservices architecture
- **Specialization**: Express.js applications, MongoDB/PostgreSQL integration, RESTful APIs
- **Responsibilities**: 
  - Design scalable Node.js architectures with proper separation of concerns
  - Implement robust API endpoints with comprehensive error handling
  - Database design and optimization for NoSQL/SQL databases
  - Microservices orchestration and inter-service communication

#### frontend-developer
**Primary Role**: JavaScript frontend development, SPA frameworks, UI implementation
- **Specialization**: ${frontend_framework} applications, modern JavaScript (ES6+), responsive design
- **Responsibilities**:
  - Implement responsive and interactive user interfaces
  - State management with appropriate patterns (Redux, Context API, Vuex)
  - Component-based architecture and reusable UI libraries
  - Frontend performance optimization and bundle management

#### rapid-prototyper  
**Primary Role**: Quick JavaScript prototyping and proof of concepts
- **Specialization**: Fast MVP development, npm ecosystem integration
- **Responsibilities**:
  - Rapid development of JavaScript prototypes using modern frameworks
  - Integration of third-party packages and APIs
  - Quick validation of technical approaches and architectures
  - MVP feature implementation with focus on speed and validation

### Specialized JavaScript Agents

#### node-performance-specialist
**Role**: Node.js performance optimization and scaling
- **Focus Areas**: 
  - Event loop optimization and async performance tuning
  - Memory usage optimization and garbage collection tuning
  - Database query optimization and connection pooling
  - Caching strategies with Redis and in-memory solutions
  - Load testing and performance benchmarking

#### javascript-security-expert
**Role**: Security implementation and vulnerability assessment
- **Focus Areas**:
  - Authentication and authorization (JWT, OAuth, session management)
  - Input validation and sanitization (XSS, injection prevention)
  - Security headers and CORS configuration
  - Dependency vulnerability scanning and updates
  - Secure coding practices and OWASP compliance

### Testing and Quality Agents

#### test-writer-fixer
**JavaScript Testing Specialization**:
- **Unit Testing**: Jest, Mocha/Chai for comprehensive unit test coverage
- **Integration Testing**: Supertest for API testing, database integration tests
- **End-to-End Testing**: Puppeteer, Playwright for browser automation
- **Mocking**: Jest mocks, Sinon.js for external dependencies
- **Coverage**: Istanbul/nyc for code coverage analysis

**Responsibilities**:
- Write comprehensive unit tests following JavaScript testing best practices
- Implement integration tests for API endpoints and database operations
- Create end-to-end tests for critical user workflows
- Maintain high test coverage (>80% target) with meaningful assertions
- Mock external services and dependencies effectively

#### performance-benchmarker
**JavaScript Performance Focus**:
- **Profiling**: Node.js built-in profiler, Chrome DevTools, clinic.js
- **Benchmarking**: Benchmark.js for micro-benchmarks, autocannon for API load testing
- **Memory Analysis**: Memory usage profiling and leak detection
- **Bundle Analysis**: Webpack Bundle Analyzer, source-map-explorer for frontend optimization

### Framework-Specific Agents

#### ${framework}-specialist
**Framework**: ${framework}
**Specialization**: ${framework}-specific patterns and optimizations
- **Responsibilities**:
  - Implement ${framework}-specific features using best practices
  - Optimize ${framework} applications for performance and user experience
  - Handle ${framework} security considerations and compliance
  - Manage ${framework} deployment strategies and CI/CD integration

## Agent Coordination Workflows

### Full-Stack Development Pipeline
```
1. rapid-prototyper: Initial feature prototyping and architecture validation
   ↓
2. backend-architect: Backend API development and database design
   ↓
3. frontend-developer: Frontend implementation and state management
   ↓
4. test-writer-fixer: Comprehensive testing across all layers
   ↓
5. javascript-security-expert: Security review and vulnerability assessment
   ↓
6. node-performance-specialist: Performance optimization and scaling
   ↓
7. devops-automator: Deployment and monitoring setup
```

### API Development Pipeline
```
1. backend-architect: API design and endpoint implementation
   ↓
2. test-writer-fixer: API testing with supertest and integration tests
   ↓
3. javascript-security-expert: Security implementation (auth, validation)
   ↓
4. performance-benchmarker: API performance testing and optimization
   ↓
5. devops-automator: API deployment and monitoring
```

## JavaScript-Specific Development Standards

### Package.json Configuration
```json
{
  "name": "${project_name}",
  "version": "1.0.0",
  "description": "${project_description}",
  "main": "src/index.js",
  "engines": {
    "node": ">=${node_version}",
    "npm": ">=${npm_version}"
  },
  "scripts": {
    "start": "node src/index.js",
    "dev": "nodemon src/index.js",
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage",
    "lint": "eslint src/ --ext .js",
    "lint:fix": "eslint src/ --ext .js --fix",
    "format": "prettier --write 'src/**/*.js'"
  },
  "dependencies": {
    "express": "^${express_version}",
    "mongoose": "^${mongoose_version}",
    "joi": "^${joi_version}",
    "jsonwebtoken": "^${jwt_version}",
    "bcryptjs": "^${bcrypt_version}",
    "helmet": "^${helmet_version}",
    "cors": "^${cors_version}",
    "winston": "^${winston_version}"
  },
  "devDependencies": {
    "jest": "^${jest_version}",
    "supertest": "^${supertest_version}",
    "eslint": "^${eslint_version}",
    "prettier": "^${prettier_version}",
    "nodemon": "^${nodemon_version}"
  }
}
```

### Code Quality Configuration
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
    'no-console': process.env.NODE_ENV === 'production' ? 'error' : 'warn',
    'prefer-const': 'error',
    'no-var': 'error',
    'prefer-arrow-callback': 'error',
    'no-unused-vars': ['error', { argsIgnorePattern: '^_' }]
  }
};
```

### Agent-Specific Guidelines

#### For backend-architect
```javascript
// Example service architecture pattern
class ${service_name}Service {
  constructor(repository, logger, cache) {
    this.repository = repository;
    this.logger = logger;
    this.cache = cache;
  }

  async processRequest(requestData) {
    try {
      // Input validation
      await this.validateRequest(requestData);

      // Check cache first
      const cacheKey = this.generateCacheKey(requestData);
      const cached = await this.cache.get(cacheKey);
      if (cached) {
        this.logger.info('Cache hit', { key: cacheKey });
        return cached;
      }

      // Start database transaction
      const session = await this.repository.startTransaction();
      
      try {
        // Business logic
        const result = await this.processBusinessLogic(requestData, session);
        
        // Commit transaction
        await session.commitTransaction();
        
        // Update cache
        await this.cache.set(cacheKey, result, 300); // 5 minutes
        
        this.logger.info('Request processed successfully', {
          requestId: requestData.id,
          resultId: result.id
        });
        
        return result;
      } catch (error) {
        await session.abortTransaction();
        throw error;
      } finally {
        session.endSession();
      }
    } catch (error) {
      this.logger.error('Request processing failed', {
        error: error.message,
        stack: error.stack,
        requestData
      });
      throw error;
    }
  }

  async validateRequest(data) {
    const Joi = require('joi');
    
    const schema = Joi.object({
      id: Joi.string().required(),
      type: Joi.string().valid('${valid_types}').required(),
      data: Joi.object().required(),
      metadata: Joi.object().optional()
    });

    const { error, value } = schema.validate(data);
    if (error) {
      throw new ValidationError(error.details[0].message);
    }
    
    return value;
  }

  generateCacheKey(data) {
    const crypto = require('crypto');
    const key = `${this.constructor.name}:${JSON.stringify(data)}`;
    return crypto.createHash('md5').update(key).digest('hex');
  }

  async processBusinessLogic(data, session) {
    // Implement specific business logic
    const processed = await this.transformData(data);
    const result = await this.repository.save(processed, { session });
    return result;
  }
}

module.exports = ${service_name}Service;
```

#### For test-writer-fixer
```javascript
// Example comprehensive test suite
const request = require('supertest');
const app = require('../../src/app');
const ${model_name} = require('../../src/models/${model}');
const { generateAuthToken } = require('../utils/auth');

describe('${service_name} API Integration Tests', () => {
  let authToken;
  let testUser;

  beforeEach(async () => {
    testUser = await global.testUtils.createTestUser();
    authToken = generateAuthToken(testUser.id);
  });

  describe('POST /api/${resource_name}', () => {
    const validRequestData = {
      name: 'Test ${resource_name}',
      type: '${default_type}',
      data: { key: 'value' },
      metadata: { source: 'test' }
    };

    it('should create ${resource_name} with valid data', async () => {
      const response = await request(app)
        .post('/api/${resource_name}')
        .set('Authorization', `Bearer ${authToken}`)
        .send(validRequestData)
        .expect(201);

      expect(response.body.success).toBe(true);
      expect(response.body.data).toMatchObject({
        name: validRequestData.name,
        type: validRequestData.type
      });

      // Verify in database
      const created = await ${model_name}.findById(response.body.data.id);
      expect(created).toBeTruthy();
      expect(created.name).toBe(validRequestData.name);
    });

    it('should handle validation errors', async () => {
      const invalidData = { ...validRequestData, type: 'invalid' };

      const response = await request(app)
        .post('/api/${resource_name}')
        .set('Authorization', `Bearer ${authToken}`)
        .send(invalidData)
        .expect(400);

      expect(response.body.success).toBe(false);
      expect(response.body.error).toContain('type');
    });

    it('should require authentication', async () => {
      const response = await request(app)
        .post('/api/${resource_name}')
        .send(validRequestData)
        .expect(401);

      expect(response.body.success).toBe(false);
      expect(response.body.error).toContain('token');
    });

    describe('Performance Tests', () => {
      it('should handle concurrent requests', async () => {
        const concurrentRequests = Array(10).fill().map((_, index) => 
          request(app)
            .post('/api/${resource_name}')
            .set('Authorization', `Bearer ${authToken}`)
            .send({
              ...validRequestData,
              name: `Concurrent Test ${index}`
            })
        );

        const responses = await Promise.all(concurrentRequests);
        
        responses.forEach(response => {
          expect(response.status).toBe(201);
          expect(response.body.success).toBe(true);
        });

        // Verify all created in database
        const count = await ${model_name}.countDocuments({
          name: { $regex: /^Concurrent Test/ }
        });
        expect(count).toBe(10);
      });

      it('should complete within acceptable time', async () => {
        const start = Date.now();
        
        await request(app)
          .post('/api/${resource_name}')
          .set('Authorization', `Bearer ${authToken}`)
          .send(validRequestData)
          .expect(201);

        const duration = Date.now() - start;
        expect(duration).toBeLessThan(1000); // Should complete within 1 second
      });
    });
  });

  describe('Error Handling', () => {
    it('should handle database connection errors', async () => {
      // Mock database error
      jest.spyOn(${model_name}, 'create').mockRejectedValueOnce(
        new Error('Database connection failed')
      );

      const response = await request(app)
        .post('/api/${resource_name}')
        .set('Authorization', `Bearer ${authToken}`)
        .send(validRequestData)
        .expect(500);

      expect(response.body.success).toBe(false);
      expect(response.body.error).toContain('Internal server error');
    });

    it('should handle timeout scenarios', async () => {
      // Mock slow database operation
      jest.spyOn(${model_name}, 'create').mockImplementationOnce(
        () => new Promise(resolve => setTimeout(resolve, 6000))
      );

      const response = await request(app)
        .post('/api/${resource_name}')
        .set('Authorization', `Bearer ${authToken}`)
        .send(validRequestData)
        .timeout(5000)
        .expect(408);

      expect(response.body.success).toBe(false);
    });
  });
});

// Unit tests for service layer
describe('${service_name}Service Unit Tests', () => {
  let service;
  let mockRepository;
  let mockLogger;
  let mockCache;

  beforeEach(() => {
    mockRepository = {
      startTransaction: jest.fn(),
      save: jest.fn(),
      findById: jest.fn()
    };

    mockLogger = {
      info: jest.fn(),
      error: jest.fn(),
      debug: jest.fn()
    };

    mockCache = {
      get: jest.fn(),
      set: jest.fn(),
      del: jest.fn()
    };

    service = new ${service_name}Service(mockRepository, mockLogger, mockCache);
  });

  describe('processRequest', () => {
    const mockRequestData = {
      id: 'test-id',
      type: '${default_type}',
      data: { test: 'data' },
      metadata: {}
    };

    it('should return cached result when available', async () => {
      const cachedResult = { id: 'cached', status: 'completed' };
      mockCache.get.mockResolvedValue(cachedResult);

      const result = await service.processRequest(mockRequestData);

      expect(result).toEqual(cachedResult);
      expect(mockCache.get).toHaveBeenCalled();
      expect(mockRepository.startTransaction).not.toHaveBeenCalled();
      expect(mockLogger.info).toHaveBeenCalledWith('Cache hit', expect.any(Object));
    });

    it('should process and cache new requests', async () => {
      const processedResult = { id: 'processed', status: 'completed' };
      const mockSession = {
        commitTransaction: jest.fn(),
        abortTransaction: jest.fn(),
        endSession: jest.fn()
      };

      mockCache.get.mockResolvedValue(null);
      mockRepository.startTransaction.mockResolvedValue(mockSession);
      mockRepository.save.mockResolvedValue(processedResult);

      const result = await service.processRequest(mockRequestData);

      expect(result).toEqual(processedResult);
      expect(mockRepository.startTransaction).toHaveBeenCalled();
      expect(mockRepository.save).toHaveBeenCalledWith(
        expect.any(Object),
        { session: mockSession }
      );
      expect(mockSession.commitTransaction).toHaveBeenCalled();
      expect(mockCache.set).toHaveBeenCalledWith(
        expect.any(String),
        processedResult,
        300
      );
    });

    it('should rollback transaction on error', async () => {
      const mockSession = {
        commitTransaction: jest.fn(),
        abortTransaction: jest.fn(),
        endSession: jest.fn()
      };

      mockCache.get.mockResolvedValue(null);
      mockRepository.startTransaction.mockResolvedValue(mockSession);
      mockRepository.save.mockRejectedValue(new Error('Save failed'));

      await expect(service.processRequest(mockRequestData))
        .rejects
        .toThrow('Save failed');

      expect(mockSession.abortTransaction).toHaveBeenCalled();
      expect(mockSession.endSession).toHaveBeenCalled();
      expect(mockSession.commitTransaction).not.toHaveBeenCalled();
    });
  });
});
```

#### For node-performance-specialist
```javascript
// Performance optimization examples
const cluster = require('cluster');
const os = require('os');
const { promisify } = require('util');

// Cluster setup for production scaling
if (cluster.isMaster && process.env.NODE_ENV === 'production') {
  const numCPUs = os.cpus().length;
  
  console.log(`Master ${process.pid} is running`);
  console.log(`Forking ${numCPUs} workers`);

  // Fork workers
  for (let i = 0; i < numCPUs; i++) {
    cluster.fork();
  }

  // Handle worker death
  cluster.on('exit', (worker, code, signal) => {
    console.log(`Worker ${worker.process.pid} died`);
    console.log('Starting a new worker');
    cluster.fork();
  });
} else {
  // Worker process - run the actual application
  const app = require('./app');
  const port = process.env.PORT || 3000;
  
  app.listen(port, () => {
    console.log(`Worker ${process.pid} listening on port ${port}`);
  });
}

// Connection pooling optimization
class DatabaseManager {
  constructor() {
    this.pools = new Map();
  }

  async getConnection(database = 'default') {
    if (!this.pools.has(database)) {
      const pool = this.createPool(database);
      this.pools.set(database, pool);
    }

    return this.pools.get(database);
  }

  createPool(database) {
    const mongoose = require('mongoose');
    
    return mongoose.createConnection(process.env[`${database.toUpperCase()}_DB_URI`], {
      useNewUrlParser: true,
      useUnifiedTopology: true,
      maxPoolSize: 20,          // Maximum number of connections
      serverSelectionTimeoutMS: 5000,  // How long to wait for server selection
      socketTimeoutMS: 45000,   // How long to wait for socket
      bufferCommands: false,    // Disable mongoose buffering
      bufferMaxEntries: 0       // Disable mongoose buffering
    });
  }
}

// Memory-efficient streaming for large data processing
async function processLargeDataset(query, processor) {
  const mongoose = require('mongoose');
  const Model = mongoose.model('${model_name}');
  
  let processedCount = 0;
  const batchSize = 1000;

  // Use cursor for memory-efficient processing
  const cursor = Model.find(query).cursor();

  for (let doc = await cursor.next(); doc != null; doc = await cursor.next()) {
    try {
      await processor(doc);
      processedCount++;

      // Log progress and perform garbage collection periodically
      if (processedCount % batchSize === 0) {
        console.log(`Processed ${processedCount} documents`);
        
        // Force garbage collection if --expose-gc flag is used
        if (global.gc) {
          global.gc();
        }
      }
    } catch (error) {
      console.error(`Error processing document ${doc._id}:`, error);
    }
  }

  return processedCount;
}

// Optimized async operations with proper error handling
class AsyncOperationManager {
  constructor(concurrencyLimit = 10) {
    this.concurrencyLimit = concurrencyLimit;
    this.activeOperations = 0;
    this.queue = [];
  }

  async execute(operation) {
    return new Promise((resolve, reject) => {
      this.queue.push({ operation, resolve, reject });
      this.processQueue();
    });
  }

  async processQueue() {
    while (this.queue.length > 0 && this.activeOperations < this.concurrencyLimit) {
      const { operation, resolve, reject } = this.queue.shift();
      
      this.activeOperations++;
      
      try {
        const result = await operation();
        resolve(result);
      } catch (error) {
        reject(error);
      } finally {
        this.activeOperations--;
        // Process next item in queue
        setImmediate(() => this.processQueue());
      }
    }
  }
}

// Usage example
const asyncManager = new AsyncOperationManager(5);

async function processMultipleItems(items) {
  const operations = items.map(item => 
    () => asyncManager.execute(() => processItem(item))
  );

  return Promise.all(operations);
}
```

## Environment-Specific Configurations

### Development Environment
```javascript
// config/development.js
module.exports = {
  app: {
    port: 3000,
    environment: 'development'
  },
  database: {
    uri: 'mongodb://localhost:27017/${project_name}_dev',
    options: {
      maxPoolSize: 5,
      serverSelectionTimeoutMS: 5000
    }
  },
  logging: {
    level: 'debug',
    format: 'dev'
  },
  cors: {
    origin: ['http://localhost:3000', 'http://localhost:8080'],
    credentials: true
  }
};
```

### Production Environment
```javascript
// config/production.js
module.exports = {
  app: {
    port: process.env.PORT || 8080,
    environment: 'production'
  },
  database: {
    uri: process.env.DATABASE_URI,
    options: {
      maxPoolSize: 20,
      serverSelectionTimeoutMS: 30000,
      bufferCommands: false,
      bufferMaxEntries: 0
    }
  },
  logging: {
    level: 'info',
    format: 'json'
  },
  cors: {
    origin: process.env.ALLOWED_ORIGINS?.split(',') || [],
    credentials: true
  }
};
```

---

*Generated by Claude Builder v${version} on ${timestamp}*