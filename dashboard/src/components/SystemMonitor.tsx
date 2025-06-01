import React, { useState, useEffect } from 'react';
import {
  Box,
  VStack,
  HStack,
  Text,
  Card,
  CardHeader,
  CardBody,
  SimpleGrid,
  Progress,
  Badge,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  StatArrow,
  useColorModeValue,
  Icon,
  Tooltip,
  Button,
  Alert,
  AlertIcon,
  Divider,
  CircularProgress,
  CircularProgressLabel,
} from '@chakra-ui/react';
import {
  FiCpu,
  FiHardDrive,
  FiWifi,
  FiDatabase,
  FiServer,
  FiActivity,
  FiAlertTriangle,
  FiCheckCircle,
  FiClock,
  FiUsers,
  FiPhone,
  FiTrendingUp,
  FiTrendingDown,
} from 'react-icons/fi';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';

interface SystemMetrics {
  cpu: {
    usage: number;
    cores: number;
    temperature: number;
  };
  memory: {
    used: number;
    total: number;
    percentage: number;
  };
  disk: {
    used: number;
    total: number;
    percentage: number;
  };
  network: {
    upload: number;
    download: number;
    latency: number;
  };
  database: {
    connections: number;
    maxConnections: number;
    queryTime: number;
  };
  calls: {
    active: number;
    queued: number;
    completed: number;
    failed: number;
  };
}

interface HistoricalData {
  timestamp: string;
  cpu: number;
  memory: number;
  network: number;
  calls: number;
}

const SystemMonitor: React.FC = () => {
  const [metrics, setMetrics] = useState<SystemMetrics>({
    cpu: { usage: 45, cores: 8, temperature: 65 },
    memory: { used: 12.5, total: 32, percentage: 39 },
    disk: { used: 450, total: 1000, percentage: 45 },
    network: { upload: 125, download: 850, latency: 12 },
    database: { connections: 45, maxConnections: 100, queryTime: 2.3 },
    calls: { active: 23, queued: 5, completed: 1247, failed: 12 },
  });

  const [historicalData, setHistoricalData] = useState<HistoricalData[]>([]);
  const [isOnline, setIsOnline] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(new Date());

  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');

  // Simulate real-time data updates
  useEffect(() => {
    const interval = setInterval(() => {
      setMetrics(prev => ({
        cpu: {
          ...prev.cpu,
          usage: Math.max(10, Math.min(90, prev.cpu.usage + (Math.random() - 0.5) * 10)),
          temperature: Math.max(40, Math.min(80, prev.cpu.temperature + (Math.random() - 0.5) * 5)),
        },
        memory: {
          ...prev.memory,
          percentage: Math.max(20, Math.min(85, prev.memory.percentage + (Math.random() - 0.5) * 5)),
        },
        disk: {
          ...prev.disk,
          percentage: Math.max(30, Math.min(90, prev.disk.percentage + (Math.random() - 0.5) * 2)),
        },
        network: {
          upload: Math.max(50, Math.min(500, prev.network.upload + (Math.random() - 0.5) * 50)),
          download: Math.max(200, Math.min(1500, prev.network.download + (Math.random() - 0.5) * 100)),
          latency: Math.max(5, Math.min(50, prev.network.latency + (Math.random() - 0.5) * 5)),
        },
        database: {
          ...prev.database,
          connections: Math.max(20, Math.min(80, prev.database.connections + Math.floor((Math.random() - 0.5) * 10))),
          queryTime: Math.max(0.5, Math.min(10, prev.database.queryTime + (Math.random() - 0.5) * 1)),
        },
        calls: {
          active: Math.max(0, Math.min(50, prev.calls.active + Math.floor((Math.random() - 0.5) * 5))),
          queued: Math.max(0, Math.min(20, prev.calls.queued + Math.floor((Math.random() - 0.5) * 3))),
          completed: prev.calls.completed + Math.floor(Math.random() * 3),
          failed: prev.calls.failed + (Math.random() < 0.1 ? 1 : 0),
        },
      }));

      // Update historical data
      setHistoricalData(prev => {
        const newData = {
          timestamp: new Date().toLocaleTimeString(),
          cpu: metrics.cpu.usage,
          memory: metrics.memory.percentage,
          network: metrics.network.latency,
          calls: metrics.calls.active,
        };
        return [...prev.slice(-19), newData]; // Keep last 20 data points
      });

      setLastUpdate(new Date());
    }, 3000);

    return () => clearInterval(interval);
  }, [metrics.cpu.usage, metrics.memory.percentage, metrics.network.latency, metrics.calls.active]);

  const getStatusColor = (value: number, thresholds: { warning: number; critical: number }) => {
    if (value >= thresholds.critical) return 'red';
    if (value >= thresholds.warning) return 'yellow';
    return 'green';
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <VStack spacing={6} align="stretch">
      {/* Header */}
      <HStack justify="space-between">
        <VStack align="start" spacing={1}>
          <Text fontSize="xl" fontWeight="bold">System Monitor</Text>
          <HStack>
            <Badge colorScheme={isOnline ? 'green' : 'red'} variant="subtle">
              {isOnline ? '🟢 Online' : '🔴 Offline'}
            </Badge>
            <Text fontSize="sm" color="gray.500">
              Last updated: {lastUpdate.toLocaleTimeString()}
            </Text>
          </HStack>
        </VStack>
        <Button size="sm" variant="outline" leftIcon={<FiActivity />}>
          View Logs
        </Button>
      </HStack>

      {/* System Health Overview */}
      <SimpleGrid columns={{ base: 2, md: 4 }} spacing={4}>
        {/* CPU */}
        <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
          <CardBody>
            <VStack spacing={3}>
              <HStack justify="space-between" w="full">
                <Icon as={FiCpu} boxSize={5} color="blue.500" />
                <Badge colorScheme={getStatusColor(metrics.cpu.usage, { warning: 70, critical: 85 })}>
                  {metrics.cpu.usage.toFixed(1)}%
                </Badge>
              </HStack>
              <CircularProgress
                value={metrics.cpu.usage}
                color={`${getStatusColor(metrics.cpu.usage, { warning: 70, critical: 85 })}.400`}
                size="60px"
                thickness="8px"
              >
                <CircularProgressLabel fontSize="sm">
                  {metrics.cpu.usage.toFixed(0)}%
                </CircularProgressLabel>
              </CircularProgress>
              <VStack spacing={0}>
                <Text fontSize="sm" fontWeight="medium">CPU Usage</Text>
                <Text fontSize="xs" color="gray.500">{metrics.cpu.cores} cores</Text>
                <Text fontSize="xs" color="gray.500">{metrics.cpu.temperature}°C</Text>
              </VStack>
            </VStack>
          </CardBody>
        </Card>

        {/* Memory */}
        <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
          <CardBody>
            <VStack spacing={3}>
              <HStack justify="space-between" w="full">
                <Icon as={FiHardDrive} boxSize={5} color="purple.500" />
                <Badge colorScheme={getStatusColor(metrics.memory.percentage, { warning: 75, critical: 90 })}>
                  {metrics.memory.percentage.toFixed(1)}%
                </Badge>
              </HStack>
              <CircularProgress
                value={metrics.memory.percentage}
                color={`${getStatusColor(metrics.memory.percentage, { warning: 75, critical: 90 })}.400`}
                size="60px"
                thickness="8px"
              >
                <CircularProgressLabel fontSize="sm">
                  {metrics.memory.percentage.toFixed(0)}%
                </CircularProgressLabel>
              </CircularProgress>
              <VStack spacing={0}>
                <Text fontSize="sm" fontWeight="medium">Memory</Text>
                <Text fontSize="xs" color="gray.500">
                  {formatBytes(metrics.memory.used * 1024 * 1024 * 1024)} / {formatBytes(metrics.memory.total * 1024 * 1024 * 1024)}
                </Text>
              </VStack>
            </VStack>
          </CardBody>
        </Card>

        {/* Network */}
        <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
          <CardBody>
            <VStack spacing={3}>
              <HStack justify="space-between" w="full">
                <Icon as={FiWifi} boxSize={5} color="green.500" />
                <Badge colorScheme={getStatusColor(metrics.network.latency, { warning: 30, critical: 50 })}>
                  {metrics.network.latency}ms
                </Badge>
              </HStack>
              <VStack spacing={1}>
                <Text fontSize="lg" fontWeight="bold">{metrics.network.latency}ms</Text>
                <Text fontSize="xs" color="gray.500">Latency</Text>
              </VStack>
              <VStack spacing={0}>
                <Text fontSize="sm" fontWeight="medium">Network</Text>
                <Text fontSize="xs" color="gray.500">↑ {metrics.network.upload} KB/s</Text>
                <Text fontSize="xs" color="gray.500">↓ {metrics.network.download} KB/s</Text>
              </VStack>
            </VStack>
          </CardBody>
        </Card>

        {/* Database */}
        <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
          <CardBody>
            <VStack spacing={3}>
              <HStack justify="space-between" w="full">
                <Icon as={FiDatabase} boxSize={5} color="orange.500" />
                <Badge colorScheme={getStatusColor((metrics.database.connections / metrics.database.maxConnections) * 100, { warning: 70, critical: 85 })}>
                  {metrics.database.connections}/{metrics.database.maxConnections}
                </Badge>
              </HStack>
              <VStack spacing={1}>
                <Text fontSize="lg" fontWeight="bold">{metrics.database.queryTime.toFixed(1)}ms</Text>
                <Text fontSize="xs" color="gray.500">Avg Query Time</Text>
              </VStack>
              <VStack spacing={0}>
                <Text fontSize="sm" fontWeight="medium">Database</Text>
                <Text fontSize="xs" color="gray.500">{metrics.database.connections} connections</Text>
              </VStack>
            </VStack>
          </CardBody>
        </Card>
      </SimpleGrid>

      {/* Call Center Metrics */}
      <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
        <CardHeader>
          <Text fontSize="lg" fontWeight="bold">Call Center Status</Text>
        </CardHeader>
        <CardBody>
          <SimpleGrid columns={{ base: 2, md: 4 }} spacing={6}>
            <Stat>
              <StatLabel>Active Calls</StatLabel>
              <StatNumber color="green.500">{metrics.calls.active}</StatNumber>
              <StatHelpText>
                <StatArrow type="increase" />
                Real-time
              </StatHelpText>
            </Stat>
            <Stat>
              <StatLabel>Queued Calls</StatLabel>
              <StatNumber color="yellow.500">{metrics.calls.queued}</StatNumber>
              <StatHelpText>
                <StatArrow type={metrics.calls.queued > 10 ? "increase" : "decrease"} />
                Waiting
              </StatHelpText>
            </Stat>
            <Stat>
              <StatLabel>Completed Today</StatLabel>
              <StatNumber color="blue.500">{metrics.calls.completed}</StatNumber>
              <StatHelpText>
                <StatArrow type="increase" />
                +12% from yesterday
              </StatHelpText>
            </Stat>
            <Stat>
              <StatLabel>Failed Calls</StatLabel>
              <StatNumber color="red.500">{metrics.calls.failed}</StatNumber>
              <StatHelpText>
                <StatArrow type="decrease" />
                -5% from yesterday
              </StatHelpText>
            </Stat>
          </SimpleGrid>
        </CardBody>
      </Card>

      {/* Historical Performance Chart */}
      <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
        <CardHeader>
          <Text fontSize="lg" fontWeight="bold">Performance Trends</Text>
        </CardHeader>
        <CardBody>
          <Box h="300px">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={historicalData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="timestamp" />
                <YAxis />
                <RechartsTooltip />
                <Area
                  type="monotone"
                  dataKey="cpu"
                  stackId="1"
                  stroke="#3182ce"
                  fill="#3182ce"
                  fillOpacity={0.6}
                  name="CPU %"
                />
                <Area
                  type="monotone"
                  dataKey="memory"
                  stackId="2"
                  stroke="#805ad5"
                  fill="#805ad5"
                  fillOpacity={0.6}
                  name="Memory %"
                />
                <Area
                  type="monotone"
                  dataKey="calls"
                  stackId="3"
                  stroke="#38a169"
                  fill="#38a169"
                  fillOpacity={0.6}
                  name="Active Calls"
                />
              </AreaChart>
            </ResponsiveContainer>
          </Box>
        </CardBody>
      </Card>

      {/* System Alerts */}
      <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
        <CardHeader>
          <Text fontSize="lg" fontWeight="bold">System Alerts</Text>
        </CardHeader>
        <CardBody>
          <VStack spacing={3} align="stretch">
            {metrics.cpu.usage > 80 && (
              <Alert status="warning" variant="left-accent">
                <AlertIcon />
                <Box>
                  <Text fontWeight="bold">High CPU Usage</Text>
                  <Text fontSize="sm">CPU usage is at {metrics.cpu.usage.toFixed(1)}%. Consider scaling resources.</Text>
                </Box>
              </Alert>
            )}
            {metrics.memory.percentage > 85 && (
              <Alert status="error" variant="left-accent">
                <AlertIcon />
                <Box>
                  <Text fontWeight="bold">Critical Memory Usage</Text>
                  <Text fontSize="sm">Memory usage is at {metrics.memory.percentage.toFixed(1)}%. Immediate action required.</Text>
                </Box>
              </Alert>
            )}
            {metrics.network.latency > 40 && (
              <Alert status="warning" variant="left-accent">
                <AlertIcon />
                <Box>
                  <Text fontWeight="bold">High Network Latency</Text>
                  <Text fontSize="sm">Network latency is {metrics.network.latency}ms. Check network connectivity.</Text>
                </Box>
              </Alert>
            )}
            {metrics.calls.queued > 15 && (
              <Alert status="info" variant="left-accent">
                <AlertIcon />
                <Box>
                  <Text fontWeight="bold">High Call Queue</Text>
                  <Text fontSize="sm">{metrics.calls.queued} calls are waiting. Consider adding more agents.</Text>
                </Box>
              </Alert>
            )}
            {metrics.cpu.usage <= 80 && metrics.memory.percentage <= 85 && metrics.network.latency <= 40 && metrics.calls.queued <= 15 && (
              <Alert status="success" variant="left-accent">
                <AlertIcon />
                <Box>
                  <Text fontWeight="bold">All Systems Operational</Text>
                  <Text fontSize="sm">All system metrics are within normal ranges.</Text>
                </Box>
              </Alert>
            )}
          </VStack>
        </CardBody>
      </Card>
    </VStack>
  );
};

export default SystemMonitor;