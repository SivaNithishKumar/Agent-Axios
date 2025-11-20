/**
 * Main Server
 * Express + Socket.IO setup
 */

import express from 'express';
import cors from 'cors';
import { createServer } from 'http';
import { Server as SocketIOServer } from 'socket.io';
import settings, { validateSettings } from './config/settings';
import logger from './utils/logger';
import conversationRoutes from './routes/conversationRoutes';

// Validate configuration
try {
  validateSettings();
} catch (error: any) {
  logger.error(`Configuration error: ${error.message}`);
  process.exit(1);
}

// Create Express app
const app = express();
const httpServer = createServer(app);

// Create Socket.IO server
const io = new SocketIOServer(httpServer, {
  cors: {
    origin: settings.frontendUrl,
    methods: ['GET', 'POST'],
    credentials: true,
  },
});

// Middleware
app.use(
  cors({
    origin: settings.frontendUrl,
    credentials: true,
  })
);
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Request logging middleware
app.use((req, res, next) => {
  logger.info(`${req.method} ${req.path}`);
  next();
});

// Health check
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    environment: settings.nodeEnv,
  });
});

// API Routes
app.use('/api/conversation', conversationRoutes);

// Root endpoint
app.get('/', (req, res) => {
  res.json({
    name: 'Agent Axios Node Backend',
    version: '1.0.0',
    description: 'LangChain ReAct Agent for Vulnerability Analysis',
    endpoints: {
      health: '/health',
      conversation: '/api/conversation',
    },
  });
});

// Socket.IO connection handling
io.on('connection', (socket) => {
  logger.info(`Socket.IO client connected: ${socket.id}`);

  socket.on('disconnect', () => {
    logger.info(`Socket.IO client disconnected: ${socket.id}`);
  });

  // Join analysis room
  socket.on('join_analysis', (analysisId: string) => {
    socket.join(`analysis_${analysisId}`);
    logger.info(`Client ${socket.id} joined analysis room: ${analysisId}`);
  });

  // Leave analysis room
  socket.on('leave_analysis', (analysisId: string) => {
    socket.leave(`analysis_${analysisId}`);
    logger.info(`Client ${socket.id} left analysis room: ${analysisId}`);
  });
});

// Global Socket.IO instance (can be used by other modules)
export { io };

// Error handling middleware
app.use((err: any, req: express.Request, res: express.Response, next: express.NextFunction) => {
  logger.error('Unhandled error:', err);
  res.status(500).json({
    error: 'Internal server error',
    message: settings.nodeEnv === 'development' ? err.message : undefined,
  });
});

// Start server
const PORT = settings.port;

httpServer.listen(PORT, () => {
  logger.info('='.repeat(60));
  logger.info(`🚀 Server started successfully!`);
  logger.info(`📡 HTTP Server: http://localhost:${PORT}`);
  logger.info(`🔌 Socket.IO: ws://localhost:${PORT}`);
  logger.info(`🌍 Environment: ${settings.nodeEnv}`);
  logger.info(`🗄️  Database: ${settings.databaseUrl}`);
  logger.info(`🤖 LLM: Azure OpenAI (${settings.azureOpenAI.model})`);
  logger.info('='.repeat(60));

  // Check CVE service health asynchronously (don't block startup)
  setTimeout(async () => {
    try {
      const cveHealth = await cveRetrievalService.healthCheck();
      if (cveHealth.available) {
        logger.info('✓ CVE Retrieval Service is healthy');
      } else {
        logger.warn('⚠️  CVE Retrieval Service unavailable:', cveHealth.error);
      }
    } catch (error: any) {
      logger.warn('⚠️  CVE Service check failed:', error.message);
    }
  }, 1000);
});

// Graceful shutdown
process.on('SIGTERM', () => {
  logger.info('SIGTERM received, shutting down gracefully...');
  httpServer.close(() => {
    logger.info('Server closed');
    process.exit(0);
  });
});

process.on('SIGINT', () => {
  logger.info('SIGINT received, shutting down gracefully...');
  httpServer.close(() => {
    logger.info('Server closed');
    process.exit(0);
  });
});

export default app;
