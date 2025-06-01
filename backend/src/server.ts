/**
 * GeminiVoiceConnect Backend Server
 * 
 * Main server file that sets up Express app, middleware, routes,
 * and real-time WebSocket connections for the AI Call Center Dashboard.
 */

import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import compression from 'compression';
import morgan from 'morgan';
import rateLimit from 'express-rate-limit';
import { createServer } from 'http';
import { Server as SocketIOServer } from 'socket.io';
import dotenv from 'dotenv';
import path from 'path';

// Import custom modules
import { logger } from './utils/logger';
import { errorHandler, notFoundHandler } from './middleware/errorHandler';
import { authMiddleware } from './middleware/auth';
import { validateRequest } from './middleware/validation';

// Import routes
import authRoutes from './routes/auth';
import userRoutes from './routes/users';
import callRoutes from './routes/calls';
import customerRoutes from './routes/customers';
import campaignRoutes from './routes/campaigns';
import analyticsRoutes from './routes/analytics';
import dashboardRoutes from './routes/dashboard';

// Import services
import { DatabaseService } from './services/database';
import { SocketService } from './services/socket';
import { MetricsService } from './services/metrics';

// Load environment variables
dotenv.config();

class GeminiVoiceConnectServer {
  private app: express.Application;
  private server: any;
  private io!: SocketIOServer;
  private port: number;
  private databaseService: DatabaseService;
  private socketService!: SocketService;
  private metricsService: MetricsService;

  constructor() {
    this.app = express();
    this.port = parseInt(process.env.PORT || '3001', 10);
    this.databaseService = new DatabaseService();
    this.metricsService = new MetricsService();
    
    this.initializeMiddleware();
    this.initializeRoutes();
    this.initializeErrorHandling();
    this.createServer();
    this.initializeSocket();
  }

  private initializeMiddleware(): void {
    // Security middleware
    this.app.use(helmet({
      crossOriginEmbedderPolicy: false,
      contentSecurityPolicy: {
        directives: {
          defaultSrc: ["'self'"],
          styleSrc: ["'self'", "'unsafe-inline'"],
          scriptSrc: ["'self'"],
          imgSrc: ["'self'", "data:", "https:"],
        },
      },
    }));

    // CORS configuration
    const corsOptions = {
      origin: (origin: string | undefined, callback: Function) => {
        const allowedOrigins = process.env.ALLOWED_ORIGINS?.split(',') || [
          'http://localhost:12000',
          'https://work-1-saijrqqlnvbjzerm.prod-runtime.all-hands.dev'
        ];
        
        if (!origin || allowedOrigins.includes(origin)) {
          callback(null, true);
        } else {
          callback(new Error('Not allowed by CORS'));
        }
      },
      credentials: true,
      methods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'],
      allowedHeaders: ['Content-Type', 'Authorization', 'X-Requested-With'],
    };

    this.app.use(cors(corsOptions));

    // Rate limiting
    const limiter = rateLimit({
      windowMs: parseInt(process.env.RATE_LIMIT_WINDOW_MS || '900000', 10), // 15 minutes
      max: parseInt(process.env.RATE_LIMIT_MAX_REQUESTS || '100', 10),
      message: {
        error: 'Too many requests from this IP, please try again later.',
      },
      standardHeaders: true,
      legacyHeaders: false,
    });

    this.app.use('/api/', limiter);

    // General middleware
    this.app.use(compression());
    this.app.use(morgan('combined', { stream: { write: (message) => logger.info(message.trim()) } }));
    this.app.use(express.json({ limit: '10mb' }));
    this.app.use(express.urlencoded({ extended: true, limit: '10mb' }));

    // Static files
    this.app.use('/uploads', express.static(path.join(__dirname, '../uploads')));

    // Health check endpoint
    this.app.get('/health', (req, res) => {
      res.status(200).json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        version: process.env.npm_package_version || '1.0.0',
        environment: process.env.NODE_ENV || 'development',
      });
    });

    // API info endpoint
    this.app.get('/api', (req, res) => {
      res.json({
        name: 'GeminiVoiceConnect API',
        version: process.env.API_VERSION || 'v1',
        description: 'AI-Powered Call Center Management API',
        endpoints: {
          auth: '/api/auth',
          users: '/api/users',
          calls: '/api/calls',
          customers: '/api/customers',
          campaigns: '/api/campaigns',
          analytics: '/api/analytics',
          dashboard: '/api/dashboard',
        },
        documentation: '/api/docs',
      });
    });
  }

  private initializeRoutes(): void {
    const apiRouter = express.Router();

    // Public routes (no authentication required)
    apiRouter.use('/auth', authRoutes);

    // Protected routes (authentication required)
    apiRouter.use('/users', authMiddleware, userRoutes);
    apiRouter.use('/calls', authMiddleware, callRoutes);
    apiRouter.use('/customers', authMiddleware, customerRoutes);
    apiRouter.use('/campaigns', authMiddleware, campaignRoutes);
    apiRouter.use('/analytics', authMiddleware, analyticsRoutes);
    apiRouter.use('/dashboard', authMiddleware, dashboardRoutes);

    this.app.use('/api', apiRouter);
  }

  private initializeErrorHandling(): void {
    // 404 handler
    this.app.use(notFoundHandler);

    // Global error handler
    this.app.use(errorHandler);
  }

  private createServer(): void {
    this.server = createServer(this.app);
  }

  private initializeSocket(): void {
    this.io = new SocketIOServer(this.server, {
      cors: {
        origin: process.env.SOCKET_IO_CORS_ORIGIN?.split(',') || [
          'http://localhost:12000',
          'https://work-1-saijrqqlnvbjzerm.prod-runtime.all-hands.dev'
        ],
        methods: ['GET', 'POST'],
        credentials: true,
      },
    });

    this.socketService = new SocketService(this.io);
    this.socketService.initialize();
  }

  public async start(): Promise<void> {
    try {
      // Initialize database
      await this.databaseService.initialize();
      logger.info('Database initialized successfully');

      // Start metrics collection
      if (process.env.ENABLE_METRICS === 'true') {
        await this.metricsService.start();
        logger.info('Metrics service started');
      }

      // Start server
      this.server.listen(this.port, '0.0.0.0', () => {
        logger.info(`🚀 GeminiVoiceConnect Server running on port ${this.port}`);
        logger.info(`📊 Dashboard: ${process.env.FRONTEND_URL}`);
        logger.info(`🔗 API: http://localhost:${this.port}/api`);
        logger.info(`📡 WebSocket: http://localhost:${this.port}`);
        logger.info(`🏥 Health: http://localhost:${this.port}/health`);
        logger.info(`📝 Environment: ${process.env.NODE_ENV}`);
      });

      // Graceful shutdown
      process.on('SIGTERM', () => this.shutdown());
      process.on('SIGINT', () => this.shutdown());

    } catch (error) {
      logger.error('Failed to start server:', error);
      process.exit(1);
    }
  }

  private async shutdown(): Promise<void> {
    logger.info('Shutting down server...');

    try {
      // Close server
      if (this.server) {
        this.server.close();
      }

      // Close database connections
      await this.databaseService.disconnect();

      // Stop metrics service
      if (this.metricsService) {
        await this.metricsService.stop();
      }

      logger.info('Server shutdown complete');
      process.exit(0);
    } catch (error) {
      logger.error('Error during shutdown:', error);
      process.exit(1);
    }
  }
}

// Start the server
const server = new GeminiVoiceConnectServer();
server.start().catch((error) => {
  logger.error('Failed to start server:', error);
  process.exit(1);
});

export default server;