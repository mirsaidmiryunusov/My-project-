/**
 * Socket Service
 * 
 * Manages WebSocket connections for real-time features.
 */

import { Server as SocketIOServer, Socket } from 'socket.io';
import jwt from 'jsonwebtoken';
import { PrismaClient } from '@prisma/client';
import { logger } from '../utils/logger';

const prisma = new PrismaClient();

export class SocketService {
  private io: SocketIOServer;
  private connectedUsers: Map<string, Socket> = new Map();

  constructor(io: SocketIOServer) {
    this.io = io;
  }

  initialize(): void {
    this.io.use(this.authenticateSocket.bind(this));
    this.io.on('connection', this.handleConnection.bind(this));
    
    // Start broadcasting real-time data
    this.startRealTimeUpdates();
    
    logger.info('Socket service initialized');
  }

  private async authenticateSocket(socket: Socket, next: Function): Promise<void> {
    try {
      const token = socket.handshake.auth.token;
      
      if (!token) {
        return next(new Error('Authentication token required'));
      }

      const jwtSecret = process.env.JWT_SECRET || 'fallback-secret';
      const decoded = jwt.verify(token, jwtSecret) as any;
      
      const session = await prisma.userSession.findFirst({
        where: {
          token,
          isActive: true,
          expiresAt: { gt: new Date() },
        },
        include: {
          user: {
            include: {
              tenant: true,
              permissions: true,
            },
          },
        },
      });

      if (!session) {
        return next(new Error('Invalid or expired token'));
      }

      (socket as any).user = {
        ...session.user,
        permissions: session.user.permissions.map(p => p.permission),
      };

      next();
    } catch (error) {
      next(new Error('Authentication failed'));
    }
  }

  private handleConnection(socket: Socket): void {
    const user = (socket as any).user;
    
    logger.info(`User connected: ${user.email} (${socket.id})`);
    
    // Store user connection
    this.connectedUsers.set(user.id, socket);
    
    // Join tenant room
    socket.join(`tenant:${user.tenantId}`);
    
    // Join user-specific room
    socket.join(`user:${user.id}`);
    
    // Handle disconnection
    socket.on('disconnect', () => {
      logger.info(`User disconnected: ${user.email} (${socket.id})`);
      this.connectedUsers.delete(user.id);
    });

    // Handle real-time subscriptions
    socket.on('subscribe:dashboard', () => {
      socket.join(`dashboard:${user.tenantId}`);
      logger.debug(`User subscribed to dashboard: ${user.email}`);
    });

    socket.on('subscribe:calls', () => {
      socket.join(`calls:${user.tenantId}`);
      logger.debug(`User subscribed to calls: ${user.email}`);
    });

    socket.on('subscribe:analytics', () => {
      socket.join(`analytics:${user.tenantId}`);
      logger.debug(`User subscribed to analytics: ${user.email}`);
    });

    // Handle call events
    socket.on('call:start', (data) => {
      this.handleCallStart(socket, data);
    });

    socket.on('call:end', (data) => {
      this.handleCallEnd(socket, data);
    });

    socket.on('call:update', (data) => {
      this.handleCallUpdate(socket, data);
    });

    // Send initial data
    this.sendInitialData(socket, user);
  }

  private async sendInitialData(socket: Socket, user: any): Promise<void> {
    try {
      // Send current system status
      const systemStatus = {
        timestamp: new Date().toISOString(),
        status: 'online',
        connectedUsers: this.connectedUsers.size,
      };

      socket.emit('system:status', systemStatus);

      // Send user-specific data
      const userData = {
        id: user.id,
        name: user.name,
        role: user.role,
        permissions: user.permissions,
        lastLogin: user.lastLogin,
      };

      socket.emit('user:data', userData);
    } catch (error) {
      logger.error('Failed to send initial data:', error);
    }
  }

  private handleCallStart(socket: Socket, data: any): void {
    const user = (socket as any).user;
    
    logger.info(`Call started by ${user.email}:`, data);
    
    // Broadcast to tenant
    socket.to(`tenant:${user.tenantId}`).emit('call:started', {
      ...data,
      userId: user.id,
      userName: user.name,
      timestamp: new Date().toISOString(),
    });
  }

  private handleCallEnd(socket: Socket, data: any): void {
    const user = (socket as any).user;
    
    logger.info(`Call ended by ${user.email}:`, data);
    
    // Broadcast to tenant
    socket.to(`tenant:${user.tenantId}`).emit('call:ended', {
      ...data,
      userId: user.id,
      userName: user.name,
      timestamp: new Date().toISOString(),
    });
  }

  private handleCallUpdate(socket: Socket, data: any): void {
    const user = (socket as any).user;
    
    // Broadcast to tenant
    socket.to(`tenant:${user.tenantId}`).emit('call:updated', {
      ...data,
      userId: user.id,
      timestamp: new Date().toISOString(),
    });
  }

  private startRealTimeUpdates(): void {
    // Send real-time metrics every 5 seconds
    setInterval(() => {
      this.broadcastMetrics();
    }, 5000);

    // Send dashboard updates every 10 seconds
    setInterval(() => {
      this.broadcastDashboardUpdates();
    }, 10000);
  }

  private async broadcastMetrics(): Promise<void> {
    try {
      const metrics = {
        timestamp: new Date().toISOString(),
        system: {
          uptime: process.uptime(),
          memory: process.memoryUsage(),
          cpu: Math.random() * 100, // Mock CPU usage
          connectedUsers: this.connectedUsers.size,
        },
        calls: {
          active: Math.floor(Math.random() * 20) + 5,
          queued: Math.floor(Math.random() * 10),
          completed: Math.floor(Math.random() * 100) + 50,
        },
      };

      this.io.emit('metrics:update', metrics);
    } catch (error) {
      logger.error('Failed to broadcast metrics:', error);
    }
  }

  private async broadcastDashboardUpdates(): Promise<void> {
    try {
      // Get all connected tenants
      const tenantIds = new Set<string>();
      this.connectedUsers.forEach((socket) => {
        const user = (socket as any).user;
        if (user?.tenantId) {
          tenantIds.add(user.tenantId);
        }
      });

      // Send updates for each tenant
      for (const tenantId of tenantIds) {
        const dashboardData = await this.getDashboardData(tenantId);
        this.io.to(`dashboard:${tenantId}`).emit('dashboard:update', dashboardData);
      }
    } catch (error) {
      logger.error('Failed to broadcast dashboard updates:', error);
    }
  }

  private async getDashboardData(tenantId: string): Promise<any> {
    try {
      const now = new Date();
      const last24h = new Date(now.getTime() - 24 * 60 * 60 * 1000);

      const [totalCalls, activeCalls, callsLast24h] = await Promise.all([
        prisma.call.count({ where: { tenantId } }),
        prisma.call.count({ 
          where: { 
            tenantId, 
            status: { in: ['RINGING', 'ANSWERED'] } 
          } 
        }),
        prisma.call.count({ 
          where: { 
            tenantId, 
            createdAt: { gte: last24h } 
          } 
        }),
      ]);

      return {
        timestamp: new Date().toISOString(),
        totalCalls,
        activeCalls,
        callsLast24h,
        realTimeMetrics: {
          callsPerMinute: Math.floor(Math.random() * 10) + 2,
          avgWaitTime: Math.floor(Math.random() * 60) + 15,
          successRate: Math.random() * 30 + 60, // 60-90%
        },
      };
    } catch (error) {
      logger.error('Failed to get dashboard data:', error);
      return {
        timestamp: new Date().toISOString(),
        error: 'Failed to fetch data',
      };
    }
  }

  // Public methods for external use
  public broadcastToTenant(tenantId: string, event: string, data: any): void {
    this.io.to(`tenant:${tenantId}`).emit(event, data);
  }

  public broadcastToUser(userId: string, event: string, data: any): void {
    this.io.to(`user:${userId}`).emit(event, data);
  }

  public broadcastToAll(event: string, data: any): void {
    this.io.emit(event, data);
  }

  public getConnectedUserCount(): number {
    return this.connectedUsers.size;
  }

  public isUserConnected(userId: string): boolean {
    return this.connectedUsers.has(userId);
  }
}