# ${project_name} - JavaScript Development Instructions

## Project Context
${project_description}

**Language**: JavaScript (Node.js ${node_version})
**Framework**: ${framework}
**Project Type**: ${project_type}
**Generated**: ${timestamp}

## JavaScript Development Standards

### Code Style and Formatting
- Use ESLint with Airbnb configuration for consistent code style
- Prettier for automatic code formatting
- Use modern ES6+ syntax and features
- Prefer const/let over var
- Use arrow functions where appropriate

### Project Structure
```
${project_name}/
├── package.json                  # Project configuration
├── package-lock.json            # Dependency lock file
├── .eslintrc.js                 # ESLint configuration
├── .prettierrc                  # Prettier configuration
├── .gitignore                   # Git ignore patterns
├── src/
│   ├── index.js                 # Application entry point
│   ├── app.js                   # Main application setup
│   ├── config/
│   │   ├── index.js
│   │   ├── database.js
│   │   └── ${config_file}.js
│   ├── controllers/             # Route controllers
│   │   └── ${controller}.js
│   ├── models/                  # Data models
│   │   └── ${model}.js
│   ├── services/                # Business logic
│   │   └── ${service}.js
│   ├── middleware/              # Express middleware
│   │   └── ${middleware}.js
│   ├── utils/                   # Utility functions
│   │   └── ${utility}.js
│   └── routes/                  # Route definitions
│       └── ${route}.js
├── tests/                       # Test files
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── docs/                        # Documentation
└── scripts/                     # Build/deployment scripts
```

### Error Handling Patterns
```javascript
// Custom error classes
class AppError extends Error {
  constructor(message, statusCode = 500, isOperational = true) {
    super(message);
    this.statusCode = statusCode;
    this.isOperational = isOperational;
    this.name = this.constructor.name;
    
    Error.captureStackTrace(this, this.constructor);
  }
}

class ValidationError extends AppError {
  constructor(message, field = null) {
    super(message, 400);
    this.field = field;
  }
}

class NotFoundError extends AppError {
  constructor(resource = 'Resource') {
    super(`${resource} not found`, 404);
  }
}

// Async error wrapper
const asyncHandler = (fn) => (req, res, next) => {
  Promise.resolve(fn(req, res, next)).catch(next);
};

// Error handling middleware
const errorHandler = (err, req, res, next) => {
  let error = { ...err };
  error.message = err.message;

  // Log error
  console.error(err);

  // Mongoose bad ObjectId
  if (err.name === 'CastError') {
    const message = 'Resource not found';
    error = new NotFoundError(message);
  }

  // Mongoose duplicate key
  if (err.code === 11000) {
    const message = 'Duplicate field value entered';
    error = new ValidationError(message);
  }

  // Mongoose validation error
  if (err.name === 'ValidationError') {
    const message = Object.values(err.errors).map(val => val.message);
    error = new ValidationError(message.join(', '));
  }

  res.status(error.statusCode || 500).json({
    success: false,
    error: error.message || 'Server Error',
    ...(process.env.NODE_ENV === 'development' && { stack: err.stack })
  });
};

module.exports = {
  AppError,
  ValidationError,
  NotFoundError,
  asyncHandler,
  errorHandler
};
```

### Async/Await Best Practices
```javascript
// Service layer with proper error handling
class ${service_name}Service {
  constructor(repository, logger) {
    this.repository = repository;
    this.logger = logger;
  }

  async processData(inputData) {
    try {
      // Input validation
      this.validateInput(inputData);

      // Start transaction if needed
      const session = await this.repository.startTransaction();
      
      try {
        // Business logic
        const processedData = await this.transformData(inputData);
        const result = await this.repository.save(processedData, { session });
        
        // Commit transaction
        await session.commitTransaction();
        
        this.logger.info('Data processed successfully', { 
          id: result.id,
          inputSize: inputData.length 
        });
        
        return result;
      } catch (error) {
        // Rollback on error
        await session.abortTransaction();
        throw error;
      } finally {
        session.endSession();
      }
    } catch (error) {
      this.logger.error('Data processing failed', { 
        error: error.message,
        stack: error.stack 
      });
      throw error;
    }
  }

  async transformData(data) {
    // Parallel processing where possible
    const transformPromises = data.map(async (item) => {
      const transformed = await this.transformSingleItem(item);
      return transformed;
    });

    return Promise.all(transformPromises);
  }

  async transformSingleItem(item) {
    // Simulate async transformation
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          ...item,
          processed: true,
          timestamp: new Date().toISOString()
        });
      }, 10);
    });
  }

  validateInput(data) {
    if (!Array.isArray(data)) {
      throw new ValidationError('Input must be an array');
    }

    if (data.length === 0) {
      throw new ValidationError('Input array cannot be empty');
    }

    data.forEach((item, index) => {
      if (!item || typeof item !== 'object') {
        throw new ValidationError(`Invalid item at index ${index}`);
      }
    });
  }
}

// Controller with async/await
const ${controller_name}Controller = {
  async create(req, res, next) {
    try {
      const { body } = req;
      
      // Service call
      const result = await ${service_name}Service.create(body);
      
      res.status(201).json({
        success: true,
        data: result
      });
    } catch (error) {
      next(error);
    }
  },

  async getById(req, res, next) {
    try {
      const { id } = req.params;
      
      const result = await ${service_name}Service.findById(id);
      
      if (!result) {
        throw new NotFoundError('${resource_name}');
      }
      
      res.json({
        success: true,
        data: result
      });
    } catch (error) {
      next(error);
    }
  },

  async update(req, res, next) {
    try {
      const { id } = req.params;
      const { body } = req;
      
      const result = await ${service_name}Service.update(id, body);
      
      res.json({
        success: true,
        data: result
      });
    } catch (error) {
      next(error);
    }
  },

  async delete(req, res, next) {
    try {
      const { id } = req.params;
      
      await ${service_name}Service.delete(id);
      
      res.status(204).send();
    } catch (error) {
      next(error);
    }
  }
};

module.exports = ${controller_name}Controller;
```

## Testing Standards

### Test Organization
```javascript
// Jest configuration (jest.config.js)
module.exports = {
  testEnvironment: 'node',
  roots: ['<rootDir>/src', '<rootDir>/tests'],
  testMatch: [
    '**/__tests__/**/*.js',
    '**/?(*.)+(spec|test).js'
  ],
  collectCoverageFrom: [
    'src/**/*.js',
    '!src/index.js',
    '!src/config/**/*.js'
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80
    }
  },
  setupFilesAfterEnv: ['<rootDir>/tests/setup.js']
};

// Test setup file
const mongoose = require('mongoose');
const { MongoMemoryServer } = require('mongodb-memory-server');

let mongoServer;

beforeAll(async () => {
  mongoServer = await MongoMemoryServer.create();
  const mongoUri = mongoServer.getUri();
  await mongoose.connect(mongoUri);
});

afterAll(async () => {
  await mongoose.disconnect();
  await mongoServer.stop();
});

afterEach(async () => {
  const collections = mongoose.connection.collections;
  for (const key in collections) {
    const collection = collections[key];
    await collection.deleteMany({});
  }
});
```

### Unit Testing Patterns
```javascript
// tests/unit/services/${service}.test.js
const ${service_name}Service = require('../../src/services/${service}');
const ${model_name} = require('../../src/models/${model}');
const { ValidationError } = require('../../src/utils/errors');

// Mock dependencies
jest.mock('../../src/models/${model}');

describe('${service_name}Service', () => {
  let service;
  let mockLogger;
  let mockRepository;

  beforeEach(() => {
    mockLogger = {
      info: jest.fn(),
      error: jest.fn(),
      debug: jest.fn()
    };
    
    mockRepository = {
      findById: jest.fn(),
      create: jest.fn(),
      update: jest.fn(),
      delete: jest.fn(),
      startTransaction: jest.fn()
    };

    service = new ${service_name}Service(mockRepository, mockLogger);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('processData', () => {
    it('should process valid data successfully', async () => {
      // Arrange
      const inputData = [
        { id: 1, name: 'Test Item 1' },
        { id: 2, name: 'Test Item 2' }
      ];
      
      const expectedResult = {
        id: 'processed-123',
        items: inputData.length,
        status: 'completed'
      };

      const mockSession = {
        commitTransaction: jest.fn(),
        abortTransaction: jest.fn(),
        endSession: jest.fn()
      };

      mockRepository.startTransaction.mockResolvedValue(mockSession);
      mockRepository.save.mockResolvedValue(expectedResult);

      // Act
      const result = await service.processData(inputData);

      // Assert
      expect(result).toEqual(expectedResult);
      expect(mockRepository.startTransaction).toHaveBeenCalled();
      expect(mockRepository.save).toHaveBeenCalledWith(
        expect.arrayContaining([
          expect.objectContaining({ processed: true })
        ]),
        { session: mockSession }
      );
      expect(mockSession.commitTransaction).toHaveBeenCalled();
      expect(mockLogger.info).toHaveBeenCalledWith(
        'Data processed successfully',
        expect.objectContaining({ id: expectedResult.id })
      );
    });

    it('should throw ValidationError for invalid input', async () => {
      // Arrange
      const invalidInput = null;

      // Act & Assert
      await expect(service.processData(invalidInput))
        .rejects
        .toThrow(ValidationError);
      
      expect(mockLogger.error).toHaveBeenCalledWith(
        'Data processing failed',
        expect.objectContaining({
          error: expect.stringContaining('Input must be an array')
        })
      );
    });

    it('should rollback transaction on processing error', async () => {
      // Arrange
      const inputData = [{ id: 1, name: 'Test' }];
      
      const mockSession = {
        commitTransaction: jest.fn(),
        abortTransaction: jest.fn(),
        endSession: jest.fn()
      };

      mockRepository.startTransaction.mockResolvedValue(mockSession);
      mockRepository.save.mockRejectedValue(new Error('Database error'));

      // Act & Assert
      await expect(service.processData(inputData))
        .rejects
        .toThrow('Database error');

      expect(mockSession.abortTransaction).toHaveBeenCalled();
      expect(mockSession.endSession).toHaveBeenCalled();
      expect(mockSession.commitTransaction).not.toHaveBeenCalled();
    });
  });

  describe('transformData', () => {
    it('should transform all items in parallel', async () => {
      // Arrange
      const inputData = [
        { id: 1, name: 'Item 1' },
        { id: 2, name: 'Item 2' },
        { id: 3, name: 'Item 3' }
      ];

      // Act
      const result = await service.transformData(inputData);

      // Assert
      expect(result).toHaveLength(inputData.length);
      result.forEach((item, index) => {
        expect(item).toMatchObject({
          ...inputData[index],
          processed: true,
          timestamp: expect.any(String)
        });
      });
    });
  });
});
```

### Integration Testing
```javascript
// tests/integration/${controller}.test.js
const request = require('supertest');
const app = require('../../src/app');
const ${model_name} = require('../../src/models/${model}');

describe('${controller_name} Integration Tests', () => {
  describe('POST /api/${resource_name}', () => {
    it('should create a new ${resource_name}', async () => {
      // Arrange
      const ${resource_name}Data = {
        name: 'Test ${resource_name}',
        description: 'Test description',
        status: 'active'
      };

      // Act
      const response = await request(app)
        .post('/api/${resource_name}')
        .send(${resource_name}Data)
        .expect(201);

      // Assert
      expect(response.body.success).toBe(true);
      expect(response.body.data).toMatchObject(${resource_name}Data);
      expect(response.body.data.id).toBeDefined();

      // Verify in database
      const created${resource_name} = await ${model_name}.findById(response.body.data.id);
      expect(created${resource_name}).toBeTruthy();
      expect(created${resource_name}.name).toBe(${resource_name}Data.name);
    });

    it('should return validation error for invalid data', async () => {
      // Arrange
      const invalidData = {
        description: 'Missing required name field'
      };

      // Act
      const response = await request(app)
        .post('/api/${resource_name}')
        .send(invalidData)
        .expect(400);

      // Assert
      expect(response.body.success).toBe(false);
      expect(response.body.error).toContain('name');
    });
  });

  describe('GET /api/${resource_name}/:id', () => {
    let created${resource_name};

    beforeEach(async () => {
      created${resource_name} = await ${model_name}.create({
        name: 'Test ${resource_name}',
        description: 'Test description',
        status: 'active'
      });
    });

    it('should retrieve ${resource_name} by id', async () => {
      // Act
      const response = await request(app)
        .get(`/api/${resource_name}/${created${resource_name}.id}`)
        .expect(200);

      // Assert
      expect(response.body.success).toBe(true);
      expect(response.body.data.id).toBe(created${resource_name}.id.toString());
      expect(response.body.data.name).toBe(created${resource_name}.name);
    });

    it('should return 404 for non-existent ${resource_name}', async () => {
      // Arrange
      const nonExistentId = '507f1f77bcf86cd799439011';

      // Act
      const response = await request(app)
        .get(`/api/${resource_name}/${nonExistentId}`)
        .expect(404);

      // Assert
      expect(response.body.success).toBe(false);
      expect(response.body.error).toContain('not found');
    });
  });
});
```

## Configuration Management

### Environment Configuration
```javascript
// src/config/index.js
const dotenv = require('dotenv');
const path = require('path');

// Load environment variables
dotenv.config({
  path: path.resolve(__dirname, `../../.env.${process.env.NODE_ENV || 'development'}`)
});

const config = {
  app: {
    name: process.env.APP_NAME || '${project_name}',
    port: parseInt(process.env.PORT, 10) || ${default_port},
    environment: process.env.NODE_ENV || 'development'
  },
  
  database: {
    uri: process.env.DATABASE_URI || 'mongodb://localhost:27017/${project_name}',
    options: {
      useNewUrlParser: true,
      useUnifiedTopology: true,
      maxPoolSize: parseInt(process.env.DB_MAX_POOL_SIZE, 10) || 10,
      serverSelectionTimeoutMS: parseInt(process.env.DB_TIMEOUT, 10) || 5000
    }
  },
  
  jwt: {
    secret: process.env.JWT_SECRET || 'your-secret-key',
    expiresIn: process.env.JWT_EXPIRES_IN || '24h'
  },
  
  logging: {
    level: process.env.LOG_LEVEL || 'info',
    format: process.env.LOG_FORMAT || 'json'
  },
  
  redis: {
    host: process.env.REDIS_HOST || 'localhost',
    port: parseInt(process.env.REDIS_PORT, 10) || 6379,
    password: process.env.REDIS_PASSWORD || null
  },
  
  email: {
    from: process.env.EMAIL_FROM || 'noreply@${project_name}.com',
    smtp: {
      host: process.env.SMTP_HOST || 'localhost',
      port: parseInt(process.env.SMTP_PORT, 10) || 587,
      secure: process.env.SMTP_SECURE === 'true',
      auth: {
        user: process.env.SMTP_USER || '',
        pass: process.env.SMTP_PASS || ''
      }
    }
  },
  
  cors: {
    origin: process.env.CORS_ORIGIN ? 
      process.env.CORS_ORIGIN.split(',') : 
      ['http://localhost:3000'],
    credentials: process.env.CORS_CREDENTIALS === 'true'
  }
};

// Validation
const requiredEnvVars = ['DATABASE_URI'];
const missingEnvVars = requiredEnvVars.filter(envVar => !process.env[envVar]);

if (missingEnvVars.length > 0) {
  throw new Error(`Missing required environment variables: ${missingEnvVars.join(', ')}`);
}

module.exports = config;
```

## Logging and Monitoring

### Structured Logging Setup
```javascript
// src/config/logger.js
const winston = require('winston');
const config = require('./index');

// Custom format for development
const devFormat = winston.format.combine(
  winston.format.colorize(),
  winston.format.timestamp({ format: 'HH:mm:ss' }),
  winston.format.printf(({ level, message, timestamp, ...meta }) => {
    const metaString = Object.keys(meta).length ? JSON.stringify(meta, null, 2) : '';
    return `${timestamp} [${level}]: ${message} ${metaString}`;
  })
);

// JSON format for production
const prodFormat = winston.format.combine(
  winston.format.timestamp(),
  winston.format.errors({ stack: true }),
  winston.format.json()
);

const logger = winston.createLogger({
  level: config.logging.level,
  format: config.app.environment === 'production' ? prodFormat : devFormat,
  defaultMeta: { 
    service: config.app.name,
    environment: config.app.environment
  },
  transports: [
    new winston.transports.Console(),
    
    // File transports for production
    ...(config.app.environment === 'production' ? [
      new winston.transports.File({ 
        filename: 'logs/error.log', 
        level: 'error' 
      }),
      new winston.transports.File({ 
        filename: 'logs/combined.log' 
      })
    ] : [])
  ]
});

// Request logging middleware
const requestLogger = (req, res, next) => {
  const start = Date.now();
  
  res.on('finish', () => {
    const duration = Date.now() - start;
    const logData = {
      method: req.method,
      url: req.url,
      statusCode: res.statusCode,
      duration: `${duration}ms`,
      userAgent: req.get('User-Agent'),
      ip: req.ip
    };
    
    if (res.statusCode >= 400) {
      logger.error('Request failed', logData);
    } else {
      logger.info('Request completed', logData);
    }
  });
  
  next();
};

module.exports = {
  logger,
  requestLogger
};
```

## Performance Guidelines

### Database Optimization
```javascript
// Efficient database queries
class ${resource_name}Repository {
  async findWithPagination(filters = {}, options = {}) {
    const {
      page = 1,
      limit = 10,
      sortBy = 'createdAt',
      sortOrder = 'desc'
    } = options;

    const skip = (page - 1) * limit;
    const sort = { [sortBy]: sortOrder === 'desc' ? -1 : 1 };

    // Use aggregation for complex queries
    const pipeline = [
      { $match: filters },
      { $sort: sort },
      {
        $facet: {
          data: [{ $skip: skip }, { $limit: limit }],
          total: [{ $count: 'count' }]
        }
      }
    ];

    const [result] = await ${model_name}.aggregate(pipeline);
    const total = result.total[0]?.count || 0;

    return {
      data: result.data,
      pagination: {
        page,
        limit,
        total,
        pages: Math.ceil(total / limit)
      }
    };
  }

  async findByIdWithCache(id, ttl = 300) {
    const cacheKey = `${model_name}:${id}`;
    
    // Try cache first
    const cached = await redis.get(cacheKey);
    if (cached) {
      return JSON.parse(cached);
    }

    // Fetch from database
    const document = await ${model_name}.findById(id);
    if (document) {
      // Cache for future requests
      await redis.setex(cacheKey, ttl, JSON.stringify(document));
    }

    return document;
  }
}

// Connection pooling and optimization
const mongoose = require('mongoose');

mongoose.connect(config.database.uri, {
  ...config.database.options,
  // Connection pooling
  maxPoolSize: 10,
  serverSelectionTimeoutMS: 5000,
  socketTimeoutMS: 45000,
  // Performance optimizations
  bufferCommands: false,
  bufferMaxEntries: 0
});

// Connection event handlers
mongoose.connection.on('connected', () => {
  logger.info('MongoDB connected successfully');
});

mongoose.connection.on('error', (err) => {
  logger.error('MongoDB connection error:', err);
});

mongoose.connection.on('disconnected', () => {
  logger.warn('MongoDB disconnected');
});

// Graceful shutdown
process.on('SIGINT', async () => {
  await mongoose.connection.close();
  logger.info('MongoDB connection closed through app termination');
  process.exit(0);
});
```

---

*Generated by Claude Builder v${version} on ${timestamp}*