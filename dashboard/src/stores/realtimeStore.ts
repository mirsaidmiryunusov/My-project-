/**
 * Real-time Store - WebSocket-based Real-time Data Management
 * 
 * This store manages real-time data streams, WebSocket connections, and live updates
 * for the GeminiVoiceConnect dashboard with advanced performance optimization.
 */

import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';
import { io, Socket } from 'socket.io-client';

// Real-time Data Interfaces
export interface LiveCall {
  id: string;
  callerId: string;
  callerName: string;
  callerNumber: string;
  agentId: string;
  agentName: string;
  startTime: string;
  duration: number;
  status: 'ringing' | 'connected' | 'on_hold' | 'transferring' | 'ending';
  sentiment: 'positive' | 'neutral' | 'negative';
  sentimentScore: number;
  transcription: TranscriptionSegment[];
  metadata: CallMetadata;
}

export interface TranscriptionSegment {
  id: string;
  speaker: 'caller' | 'agent';
  text: string;
  timestamp: string;
  confidence: number;
  sentiment: number;
  keywords: string[];
}

export interface CallMetadata {
  campaign?: string;
  source: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  customerValue: number;
  previousCalls: number;
  tags: string[];
  notes: string[];
}

export interface LiveAgent {
  id: string;
  name: string;
  email: string;
  status: 'available' | 'busy' | 'break' | 'offline' | 'training';
  currentCall?: string;
  skills: string[];
  performance: AgentPerformanceMetrics;
  workload: number;
  location: string;
  shift: AgentShift;
}

export interface AgentPerformanceMetrics {
  callsToday: number;
  averageHandleTime: number;
  conversionRate: number;
  customerSatisfaction: number;
  efficiency: number;
  adherence: number;
}

export interface AgentShift {
  start: string;
  end: string;
  breaks: BreakSchedule[];
  overtime: boolean;
}

export interface BreakSchedule {
  type: 'lunch' | 'break' | 'training';
  start: string;
  end: string;
  taken: boolean;
}

export interface SystemAlert {
  id: string;
  type: 'system' | 'performance' | 'security' | 'business';
  severity: 'info' | 'warning' | 'error' | 'critical';
  title: string;
  message: string;
  timestamp: string;
  source: string;
  acknowledged: boolean;
  assignedTo?: string;
  resolution?: string;
  metadata: Record<string, any>;
}

export interface LiveMetric {
  id: string;
  name: string;
  value: number;
  unit: string;
  trend: 'up' | 'down' | 'stable';
  change: number;
  threshold?: {
    warning: number;
    critical: number;
  };
  timestamp: string;
}

export interface QueueStatus {
  id: string;
  name: string;
  waiting: number;
  averageWaitTime: number;
  longestWait: number;
  abandoned: number;
  serviceLevel: number;
  agents: {
    available: number;
    busy: number;
    total: number;
  };
}

export interface CampaignStatus {
  id: string;
  name: string;
  type: 'inbound' | 'outbound' | 'blended';
  status: 'active' | 'paused' | 'completed' | 'scheduled';
  progress: {
    total: number;
    completed: number;
    successful: number;
    failed: number;
  };
  performance: {
    conversionRate: number;
    averageCallDuration: number;
    costPerLead: number;
    revenue: number;
  };
  schedule?: {
    start: string;
    end: string;
    timezone: string;
  };
}

export interface WebSocketEvent {
  type: string;
  data: any;
  timestamp: string;
  source: string;
}

// Real-time State
interface RealtimeState {
  // WebSocket Connection
  socket: Socket | null;
  connectionStatus: 'connecting' | 'connected' | 'disconnected' | 'error';
  reconnectAttempts: number;
  lastHeartbeat: string | null;
  
  // Live Data
  liveCalls: LiveCall[];
  liveAgents: LiveAgent[];
  systemAlerts: SystemAlert[];
  liveMetrics: LiveMetric[];
  queueStatuses: QueueStatus[];
  campaignStatuses: CampaignStatus[];
  
  // Event Stream
  eventHistory: WebSocketEvent[];
  eventFilters: string[];
  
  // Performance Monitoring
  latency: number;
  messageRate: number;
  errorRate: number;
  
  // Subscriptions
  subscriptions: Set<string>;
  
  // Settings
  autoReconnect: boolean;
  maxReconnectAttempts: number;
  heartbeatInterval: number;
  
  // Loading States
  isLoading: boolean;
  error: string | null;
}

// Real-time Actions
interface RealtimeActions {
  // Connection Management
  connect: (url?: string) => void;
  disconnect: () => void;
  reconnect: () => void;
  
  // Subscription Management
  subscribe: (channel: string) => void;
  unsubscribe: (channel: string) => void;
  subscribeToCall: (callId: string) => void;
  unsubscribeFromCall: (callId: string) => void;
  
  // Data Updates
  updateLiveCall: (call: LiveCall) => void;
  removeLiveCall: (callId: string) => void;
  updateAgent: (agent: LiveAgent) => void;
  addSystemAlert: (alert: SystemAlert) => void;
  acknowledgeAlert: (alertId: string) => void;
  updateMetric: (metric: LiveMetric) => void;
  updateQueueStatus: (queue: QueueStatus) => void;
  updateCampaignStatus: (campaign: CampaignStatus) => void;
  
  // Event Management
  addEvent: (event: WebSocketEvent) => void;
  clearEventHistory: () => void;
  setEventFilters: (filters: string[]) => void;
  
  // Performance Monitoring
  updateLatency: (latency: number) => void;
  incrementMessageRate: () => void;
  incrementErrorRate: () => void;
  
  // Utility Functions
  sendMessage: (type: string, data: any) => void;
  setError: (error: string | null) => void;
  setLoading: (loading: boolean) => void;
}

type RealtimeStore = RealtimeState & RealtimeActions;

// Mock Data Generators
const generateMockLiveCalls = (): LiveCall[] => {
  return Array.from({ length: Math.floor(Math.random() * 10) + 5 }, (_, i) => ({
    id: `call_${Date.now()}_${i}`,
    callerId: `customer_${i + 1}`,
    callerName: `Customer ${i + 1}`,
    callerNumber: `+1-555-${String(Math.floor(Math.random() * 9000) + 1000)}`,
    agentId: `agent_${(i % 12) + 1}`,
    agentName: `Agent ${(i % 12) + 1}`,
    startTime: new Date(Date.now() - Math.random() * 1800000).toISOString(),
    duration: Math.floor(Math.random() * 1200) + 60,
    status: ['ringing', 'connected', 'on_hold', 'transferring'][Math.floor(Math.random() * 4)] as any,
    sentiment: ['positive', 'neutral', 'negative'][Math.floor(Math.random() * 3)] as any,
    sentimentScore: Math.random() * 2 - 1,
    transcription: [
      {
        id: `trans_${i}_1`,
        speaker: 'caller',
        text: 'Hello, I need help with my account.',
        timestamp: new Date(Date.now() - 30000).toISOString(),
        confidence: 0.95,
        sentiment: 0.1,
        keywords: ['help', 'account'],
      },
      {
        id: `trans_${i}_2`,
        speaker: 'agent',
        text: 'I\'d be happy to help you with that. Can you provide your account number?',
        timestamp: new Date(Date.now() - 25000).toISOString(),
        confidence: 0.98,
        sentiment: 0.7,
        keywords: ['help', 'account number'],
      },
    ],
    metadata: {
      campaign: Math.random() > 0.5 ? 'Summer Sale' : undefined,
      source: ['website', 'phone', 'email', 'social'][Math.floor(Math.random() * 4)],
      priority: ['low', 'medium', 'high', 'urgent'][Math.floor(Math.random() * 4)] as any,
      customerValue: Math.floor(Math.random() * 10000) + 500,
      previousCalls: Math.floor(Math.random() * 5),
      tags: ['new_customer', 'vip', 'complaint'].slice(0, Math.floor(Math.random() * 3) + 1),
      notes: ['Customer seems frustrated', 'Previous issue resolved'],
    },
  }));
};

const generateMockLiveAgents = (): LiveAgent[] => {
  return Array.from({ length: 12 }, (_, i) => ({
    id: `agent_${i + 1}`,
    name: `Agent ${i + 1}`,
    email: `agent${i + 1}@company.com`,
    status: ['available', 'busy', 'break', 'offline'][Math.floor(Math.random() * 4)] as any,
    currentCall: Math.random() > 0.6 ? `call_${Date.now()}_${i}` : undefined,
    skills: ['sales', 'support', 'technical', 'billing'].slice(0, Math.floor(Math.random() * 3) + 1),
    performance: {
      callsToday: Math.floor(Math.random() * 30) + 10,
      averageHandleTime: Math.random() * 300 + 180,
      conversionRate: Math.random() * 0.4 + 0.1,
      customerSatisfaction: Math.random() * 2 + 3,
      efficiency: Math.random() * 0.3 + 0.7,
      adherence: Math.random() * 0.2 + 0.8,
    },
    workload: Math.random(),
    location: ['New York', 'Los Angeles', 'Chicago', 'Houston'][Math.floor(Math.random() * 4)],
    shift: {
      start: '09:00',
      end: '17:00',
      breaks: [
        { type: 'break', start: '10:30', end: '10:45', taken: true },
        { type: 'lunch', start: '12:00', end: '13:00', taken: false },
        { type: 'break', start: '15:00', end: '15:15', taken: false },
      ],
      overtime: Math.random() > 0.8,
    },
  }));
};

const generateMockSystemAlerts = (): SystemAlert[] => {
  const alerts = [
    {
      type: 'performance',
      severity: 'warning',
      title: 'High CPU Usage',
      message: 'CPU usage has exceeded 80% for the last 5 minutes',
      source: 'system_monitor',
    },
    {
      type: 'business',
      severity: 'info',
      title: 'Campaign Milestone',
      message: 'Summer Sale campaign has reached 75% completion',
      source: 'campaign_manager',
    },
    {
      type: 'security',
      severity: 'error',
      title: 'Failed Login Attempts',
      message: 'Multiple failed login attempts detected from IP 192.168.1.100',
      source: 'security_monitor',
    },
  ];

  return alerts.map((alert, i) => ({
    id: `alert_${Date.now()}_${i}`,
    ...alert,
    timestamp: new Date(Date.now() - Math.random() * 3600000).toISOString(),
    acknowledged: Math.random() > 0.7,
    metadata: { source_ip: '192.168.1.100', attempts: 5 },
  })) as SystemAlert[];
};

// Create the Realtime Store
export const useRealtimeStore = create<RealtimeStore>()(
  subscribeWithSelector((set, get) => ({
    // Initial State
    socket: null,
    connectionStatus: 'disconnected',
    reconnectAttempts: 0,
    lastHeartbeat: null,
    
    liveCalls: generateMockLiveCalls(),
    liveAgents: generateMockLiveAgents(),
    systemAlerts: generateMockSystemAlerts(),
    liveMetrics: [],
    queueStatuses: [],
    campaignStatuses: [],
    
    eventHistory: [],
    eventFilters: [],
    
    latency: 0,
    messageRate: 0,
    errorRate: 0,
    
    subscriptions: new Set(),
    
    autoReconnect: true,
    maxReconnectAttempts: 5,
    heartbeatInterval: 30000,
    
    isLoading: false,
    error: null,

    // Connection Management
    connect: (url = 'ws://localhost:8000') => {
      if (get().socket?.connected) return;
      
      set({ connectionStatus: 'connecting', error: null });
      
      const socket = io(url, {
        transports: ['websocket'],
        timeout: 5000,
        reconnection: get().autoReconnect,
        reconnectionAttempts: get().maxReconnectAttempts,
      });
      
      socket.on('connect', () => {
        set({
          socket,
          connectionStatus: 'connected',
          reconnectAttempts: 0,
          lastHeartbeat: new Date().toISOString(),
        });
        
        // Subscribe to default channels
        socket.emit('subscribe', 'system_metrics');
        socket.emit('subscribe', 'live_calls');
        socket.emit('subscribe', 'agent_status');
      });
      
      socket.on('disconnect', () => {
        set({ connectionStatus: 'disconnected' });
      });
      
      socket.on('connect_error', (error) => {
        set({
          connectionStatus: 'error',
          error: error.message,
          reconnectAttempts: get().reconnectAttempts + 1,
        });
      });
      
      socket.on('heartbeat', () => {
        set({ lastHeartbeat: new Date().toISOString() });
      });
      
      // Data event handlers
      socket.on('call_update', (call: LiveCall) => {
        get().updateLiveCall(call);
      });
      
      socket.on('agent_update', (agent: LiveAgent) => {
        get().updateAgent(agent);
      });
      
      socket.on('system_alert', (alert: SystemAlert) => {
        get().addSystemAlert(alert);
      });
      
      socket.on('metric_update', (metric: LiveMetric) => {
        get().updateMetric(metric);
      });
      
      // Performance monitoring
      socket.on('pong', (latency: number) => {
        get().updateLatency(latency);
      });
      
      set({ socket });
    },

    disconnect: () => {
      const socket = get().socket;
      if (socket) {
        socket.disconnect();
        set({
          socket: null,
          connectionStatus: 'disconnected',
          subscriptions: new Set(),
        });
      }
    },

    reconnect: () => {
      get().disconnect();
      setTimeout(() => get().connect(), 1000);
    },

    // Subscription Management
    subscribe: (channel: string) => {
      const socket = get().socket;
      if (socket?.connected) {
        socket.emit('subscribe', channel);
        set((state) => ({
          subscriptions: new Set([...state.subscriptions, channel]),
        }));
      }
    },

    unsubscribe: (channel: string) => {
      const socket = get().socket;
      if (socket?.connected) {
        socket.emit('unsubscribe', channel);
        set((state) => {
          const newSubscriptions = new Set(state.subscriptions);
          newSubscriptions.delete(channel);
          return { subscriptions: newSubscriptions };
        });
      }
    },

    subscribeToCall: (callId: string) => {
      get().subscribe(`call_${callId}`);
    },

    unsubscribeFromCall: (callId: string) => {
      get().unsubscribe(`call_${callId}`);
    },

    // Data Updates
    updateLiveCall: (call: LiveCall) => {
      set((state) => ({
        liveCalls: state.liveCalls.some(c => c.id === call.id)
          ? state.liveCalls.map(c => c.id === call.id ? call : c)
          : [...state.liveCalls, call],
      }));
      
      get().addEvent({
        type: 'call_update',
        data: call,
        timestamp: new Date().toISOString(),
        source: 'call_manager',
      });
    },

    removeLiveCall: (callId: string) => {
      set((state) => ({
        liveCalls: state.liveCalls.filter(call => call.id !== callId),
      }));
      
      get().addEvent({
        type: 'call_ended',
        data: { callId },
        timestamp: new Date().toISOString(),
        source: 'call_manager',
      });
    },

    updateAgent: (agent: LiveAgent) => {
      set((state) => ({
        liveAgents: state.liveAgents.some(a => a.id === agent.id)
          ? state.liveAgents.map(a => a.id === agent.id ? agent : a)
          : [...state.liveAgents, agent],
      }));
      
      get().addEvent({
        type: 'agent_update',
        data: agent,
        timestamp: new Date().toISOString(),
        source: 'agent_manager',
      });
    },

    addSystemAlert: (alert: SystemAlert) => {
      set((state) => ({
        systemAlerts: [alert, ...state.systemAlerts].slice(0, 100), // Keep latest 100
      }));
      
      get().addEvent({
        type: 'system_alert',
        data: alert,
        timestamp: new Date().toISOString(),
        source: 'alert_manager',
      });
    },

    acknowledgeAlert: (alertId: string) => {
      set((state) => ({
        systemAlerts: state.systemAlerts.map(alert =>
          alert.id === alertId ? { ...alert, acknowledged: true } : alert
        ),
      }));
    },

    updateMetric: (metric: LiveMetric) => {
      set((state) => ({
        liveMetrics: state.liveMetrics.some(m => m.id === metric.id)
          ? state.liveMetrics.map(m => m.id === metric.id ? metric : m)
          : [...state.liveMetrics, metric],
      }));
    },

    updateQueueStatus: (queue: QueueStatus) => {
      set((state) => ({
        queueStatuses: state.queueStatuses.some(q => q.id === queue.id)
          ? state.queueStatuses.map(q => q.id === queue.id ? queue : q)
          : [...state.queueStatuses, queue],
      }));
    },

    updateCampaignStatus: (campaign: CampaignStatus) => {
      set((state) => ({
        campaignStatuses: state.campaignStatuses.some(c => c.id === campaign.id)
          ? state.campaignStatuses.map(c => c.id === campaign.id ? campaign : c)
          : [...state.campaignStatuses, campaign],
      }));
    },

    // Event Management
    addEvent: (event: WebSocketEvent) => {
      set((state) => ({
        eventHistory: [event, ...state.eventHistory].slice(0, 1000), // Keep latest 1000
      }));
      
      get().incrementMessageRate();
    },

    clearEventHistory: () => {
      set({ eventHistory: [] });
    },

    setEventFilters: (filters: string[]) => {
      set({ eventFilters: filters });
    },

    // Performance Monitoring
    updateLatency: (latency: number) => {
      set({ latency });
    },

    incrementMessageRate: () => {
      set((state) => ({ messageRate: state.messageRate + 1 }));
    },

    incrementErrorRate: () => {
      set((state) => ({ errorRate: state.errorRate + 1 }));
    },

    // Utility Functions
    sendMessage: (type: string, data: any) => {
      const socket = get().socket;
      if (socket?.connected) {
        socket.emit(type, data);
        get().addEvent({
          type: 'message_sent',
          data: { type, data },
          timestamp: new Date().toISOString(),
          source: 'client',
        });
      }
    },

    setError: (error: string | null) => set({ error }),
    setLoading: (loading: boolean) => set({ isLoading: loading }),
  }))
);

// Auto-connect on store creation
setTimeout(() => {
  useRealtimeStore.getState().connect();
}, 1000);

// Simulate real-time updates
setInterval(() => {
  const store = useRealtimeStore.getState();
  if (store.connectionStatus === 'connected') {
    // Simulate call updates
    if (Math.random() > 0.8) {
      const calls = store.liveCalls;
      if (calls.length > 0) {
        const randomCall = calls[Math.floor(Math.random() * calls.length)];
        store.updateLiveCall({
          ...randomCall,
          duration: randomCall.duration + 5,
          sentiment: ['positive', 'neutral', 'negative'][Math.floor(Math.random() * 3)] as any,
        });
      }
    }
    
    // Simulate agent status changes
    if (Math.random() > 0.9) {
      const agents = store.liveAgents;
      if (agents.length > 0) {
        const randomAgent = agents[Math.floor(Math.random() * agents.length)];
        store.updateAgent({
          ...randomAgent,
          status: ['available', 'busy', 'break'][Math.floor(Math.random() * 3)] as any,
        });
      }
    }
  }
}, 5000);

// Reset message and error rates every minute
setInterval(() => {
  useRealtimeStore.setState({ messageRate: 0, errorRate: 0 });
}, 60000);