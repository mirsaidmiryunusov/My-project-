/**
 * System Monitoring Dashboard for Project GeminiVoiceConnect
 * 
 * This component provides comprehensive system monitoring capabilities including
 * real-time hardware status, GPU utilization, modem health, performance metrics,
 * and predictive maintenance alerts with GPU-accelerated analytics.
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  GridItem,
  Card,
  CardHeader,
  CardBody,
  Heading,
  Text,
  HStack,
  VStack,
  Icon,
  Badge,
  Button,
  IconButton,
  Progress,
  useColorModeValue,
  Flex,
  Tooltip,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  StatArrow,
  CircularProgress,
  CircularProgressLabel,
  SimpleGrid,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  TableContainer,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Switch,
  FormControl,
  FormLabel,
  Select,
  Divider,
} from '@chakra-ui/react';
import {
  FiCpu,
  FiZap,
  FiActivity,
  FiThermometer,
  FiWifi,
  FiHardDrive,
  FiMemory,
  FiMonitor,
  FiServer,
  FiAlertTriangle,
  FiCheckCircle,
  FiXCircle,
  FiClock,
  FiRefreshCw,
  FiSettings,
  FiTrendingUp,
  FiTrendingDown,
  FiBarChart3,
  FiRadio,
  FiSignal,
  FiDatabase,
  FiCloud,
  FiShield,
} from 'react-icons/fi';
import { Line, Bar, Doughnut } from 'react-chartjs-2';

interface SystemMetrics {
  cpu: {
    usage: number;
    temperature: number;
    cores: number;
    frequency: number;
  };
  memory: {
    used: number;
    total: number;
    usage: number;
  };
  gpu: {
    usage: number;
    memory: number;
    temperature: number;
    powerUsage: number;
  };
  storage: {
    used: number;
    total: number;
    usage: number;
    iops: number;
  };
  network: {
    inbound: number;
    outbound: number;
    latency: number;
    packetLoss: number;
  };
}

interface ModemHealth {
  id: string;
  status: 'healthy' | 'warning' | 'critical' | 'offline';
  signalStrength: number;
  temperature: number;
  uptime: number;
  callsToday: number;
  errorRate: number;
  lastMaintenance: Date;
  predictedFailure: number; // Days until predicted failure
}

interface SystemAlert {
  id: string;
  severity: 'info' | 'warning' | 'error' | 'critical';
  component: string;
  message: string;
  timestamp: Date;
  acknowledged: boolean;
}

const SystemMonitoring: React.FC = () => {
  const [systemMetrics, setSystemMetrics] = useState<SystemMetrics>({
    cpu: { usage: 45, temperature: 62, cores: 80, frequency: 3.2 },
    memory: { used: 48, total: 64, usage: 75 },
    gpu: { usage: 67, memory: 85, temperature: 72, powerUsage: 280 },
    storage: { used: 2.1, total: 10, usage: 21, iops: 15000 },
    network: { inbound: 125, outbound: 89, latency: 12, packetLoss: 0.02 },
  });

  const [modemHealth, setModemHealth] = useState<ModemHealth[]>([]);
  const [systemAlerts, setSystemAlerts] = useState<SystemAlert[]>([]);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(5);
  const [lastUpdated, setLastUpdated] = useState(new Date());

  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  const textColor = useColorModeValue('gray.700', 'gray.200');

  // Initialize mock data
  useEffect(() => {
    const mockModems: ModemHealth[] = Array.from({ length: 80 }, (_, i) => {
      const status = Math.random();
      return {
        id: `modem_${i + 1}`,
        status: status > 0.9 ? 'critical' : status > 0.8 ? 'warning' : status > 0.05 ? 'healthy' : 'offline',
        signalStrength: Math.floor(Math.random() * 40) + 60,
        temperature: Math.floor(Math.random() * 20) + 35,
        uptime: Math.floor(Math.random() * 8760), // Hours
        callsToday: Math.floor(Math.random() * 50),
        errorRate: Math.random() * 5,
        lastMaintenance: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000),
        predictedFailure: Math.floor(Math.random() * 365),
      };
    });

    const mockAlerts: SystemAlert[] = [
      {
        id: 'alert_001',
        severity: 'warning',
        component: 'GPU',
        message: 'GPU temperature approaching threshold (72°C)',
        timestamp: new Date(Date.now() - 300000),
        acknowledged: false,
      },
      {
        id: 'alert_002',
        severity: 'error',
        component: 'Modem #45',
        message: 'Signal strength critically low (-85 dBm)',
        timestamp: new Date(Date.now() - 600000),
        acknowledged: false,
      },
      {
        id: 'alert_003',
        severity: 'info',
        component: 'System',
        message: 'Scheduled maintenance window in 2 hours',
        timestamp: new Date(Date.now() - 900000),
        acknowledged: true,
      },
    ];

    setModemHealth(mockModems);
    setSystemAlerts(mockAlerts);
  }, []);

  // Auto-refresh system metrics
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      setSystemMetrics(prev => ({
        cpu: {
          ...prev.cpu,
          usage: Math.max(0, Math.min(100, prev.cpu.usage + (Math.random() - 0.5) * 10)),
          temperature: Math.max(30, Math.min(85, prev.cpu.temperature + (Math.random() - 0.5) * 5)),
        },
        memory: {
          ...prev.memory,
          usage: Math.max(0, Math.min(100, prev.memory.usage + (Math.random() - 0.5) * 5)),
        },
        gpu: {
          ...prev.gpu,
          usage: Math.max(0, Math.min(100, prev.gpu.usage + (Math.random() - 0.5) * 15)),
          temperature: Math.max(40, Math.min(90, prev.gpu.temperature + (Math.random() - 0.5) * 8)),
        },
        storage: {
          ...prev.storage,
          iops: Math.max(5000, Math.min(50000, prev.storage.iops + (Math.random() - 0.5) * 5000)),
        },
        network: {
          ...prev.network,
          inbound: Math.max(0, prev.network.inbound + (Math.random() - 0.5) * 50),
          outbound: Math.max(0, prev.network.outbound + (Math.random() - 0.5) * 30),
          latency: Math.max(1, Math.min(100, prev.network.latency + (Math.random() - 0.5) * 5)),
        },
      }));
      setLastUpdated(new Date());
    }, refreshInterval * 1000);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'green';
      case 'warning': return 'yellow';
      case 'critical': return 'red';
      case 'offline': return 'gray';
      default: return 'gray';
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'info': return 'blue';
      case 'warning': return 'yellow';
      case 'error': return 'orange';
      case 'critical': return 'red';
      default: return 'gray';
    }
  };

  const healthyModems = modemHealth.filter(m => m.status === 'healthy').length;
  const warningModems = modemHealth.filter(m => m.status === 'warning').length;
  const criticalModems = modemHealth.filter(m => m.status === 'critical').length;
  const offlineModems = modemHealth.filter(m => m.status === 'offline').length;

  const unacknowledgedAlerts = systemAlerts.filter(a => !a.acknowledged).length;
  const criticalAlerts = systemAlerts.filter(a => a.severity === 'critical' || a.severity === 'error').length;

  // Chart data
  const performanceHistoryData = {
    labels: ['1h ago', '45m', '30m', '15m', 'Now'],
    datasets: [
      {
        label: 'CPU Usage (%)',
        data: [42, 38, 45, 52, systemMetrics.cpu.usage],
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
      },
      {
        label: 'GPU Usage (%)',
        data: [65, 72, 68, 71, systemMetrics.gpu.usage],
        borderColor: 'rgb(139, 92, 246)',
        backgroundColor: 'rgba(139, 92, 246, 0.1)',
      },
      {
        label: 'Memory Usage (%)',
        data: [78, 75, 73, 76, systemMetrics.memory.usage],
        borderColor: 'rgb(16, 185, 129)',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
      },
    ],
  };

  const modemStatusData = {
    labels: ['Healthy', 'Warning', 'Critical', 'Offline'],
    datasets: [
      {
        data: [healthyModems, warningModems, criticalModems, offlineModems],
        backgroundColor: [
          'rgba(34, 197, 94, 0.8)',
          'rgba(245, 158, 11, 0.8)',
          'rgba(239, 68, 68, 0.8)',
          'rgba(156, 163, 175, 0.8)',
        ],
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
    },
  };

  return (
    <Box p={6} maxW="full">
      {/* Header */}
      <Flex justify="space-between" align="center" mb={6}>
        <VStack align="start" spacing={1}>
          <Heading size="lg" color={textColor}>
            System Monitoring
          </Heading>
          <Text color="gray.500" fontSize="sm">
            Real-time hardware monitoring and predictive maintenance • Last updated: {lastUpdated.toLocaleTimeString()}
          </Text>
        </VStack>
        
        <HStack spacing={3}>
          <FormControl display="flex" alignItems="center">
            <FormLabel htmlFor="auto-refresh" mb="0" fontSize="sm">
              Auto-refresh
            </FormLabel>
            <Switch
              id="auto-refresh"
              isChecked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
            />
          </FormControl>
          
          <Select size="sm" value={refreshInterval} onChange={(e) => setRefreshInterval(Number(e.target.value))} w="100px">
            <option value={1}>1s</option>
            <option value={5}>5s</option>
            <option value={10}>10s</option>
            <option value={30}>30s</option>
          </Select>
          
          <IconButton
            aria-label="Refresh"
            icon={<FiRefreshCw />}
            size="sm"
            variant="outline"
            onClick={() => setLastUpdated(new Date())}
          />
        </HStack>
      </Flex>

      {/* System Alerts */}
      {unacknowledgedAlerts > 0 && (
        <Alert status={criticalAlerts > 0 ? 'error' : 'warning'} mb={6} borderRadius="md">
          <AlertIcon />
          <Box flex="1">
            <AlertTitle fontSize="sm">
              {unacknowledgedAlerts} Unacknowledged Alert{unacknowledgedAlerts > 1 ? 's' : ''}
            </AlertTitle>
            <AlertDescription fontSize="sm">
              {criticalAlerts > 0 ? `${criticalAlerts} critical alerts require immediate attention` : 'System warnings detected'}
            </AlertDescription>
          </Box>
          <Button size="sm" variant="outline">
            View All
          </Button>
        </Alert>
      )}

      {/* Key System Metrics */}
      <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={6} mb={8}>
        <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
          <CardBody>
            <HStack justify="space-between">
              <VStack align="start" spacing={1}>
                <Text fontSize="sm" color="gray.500">System Health</Text>
                <Text fontSize="2xl" fontWeight="bold" color="green.500">
                  {Math.round(((healthyModems + warningModems * 0.5) / 80) * 100)}%
                </Text>
                <Text fontSize="xs" color="gray.500">
                  {healthyModems}/80 modems healthy
                </Text>
              </VStack>
              <CircularProgress
                value={((healthyModems + warningModems * 0.5) / 80) * 100}
                color="green.400"
                size="60px"
              >
                <CircularProgressLabel fontSize="xs">
                  {Math.round(((healthyModems + warningModems * 0.5) / 80) * 100)}%
                </CircularProgressLabel>
              </CircularProgress>
            </HStack>
          </CardBody>
        </Card>

        <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
          <CardBody>
            <HStack justify="space-between">
              <VStack align="start" spacing={1}>
                <Text fontSize="sm" color="gray.500">GPU Utilization</Text>
                <Text fontSize="2xl" fontWeight="bold" color="purple.500">
                  {systemMetrics.gpu.usage}%
                </Text>
                <Text fontSize="xs" color="gray.500">
                  {systemMetrics.gpu.temperature}°C • {systemMetrics.gpu.powerUsage}W
                </Text>
              </VStack>
              <CircularProgress
                value={systemMetrics.gpu.usage}
                color={systemMetrics.gpu.usage > 80 ? 'red.400' : 'purple.400'}
                size="60px"
              >
                <CircularProgressLabel fontSize="xs">
                  {systemMetrics.gpu.usage}%
                </CircularProgressLabel>
              </CircularProgress>
            </HStack>
          </CardBody>
        </Card>

        <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
          <CardBody>
            <HStack justify="space-between">
              <VStack align="start" spacing={1}>
                <Text fontSize="sm" color="gray.500">Memory Usage</Text>
                <Text fontSize="2xl" fontWeight="bold" color="blue.500">
                  {systemMetrics.memory.usage}%
                </Text>
                <Text fontSize="xs" color="gray.500">
                  {systemMetrics.memory.used}GB / {systemMetrics.memory.total}GB
                </Text>
              </VStack>
              <CircularProgress
                value={systemMetrics.memory.usage}
                color={systemMetrics.memory.usage > 85 ? 'red.400' : 'blue.400'}
                size="60px"
              >
                <CircularProgressLabel fontSize="xs">
                  {systemMetrics.memory.usage}%
                </CircularProgressLabel>
              </CircularProgress>
            </HStack>
          </CardBody>
        </Card>

        <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
          <CardBody>
            <HStack justify="space-between">
              <VStack align="start" spacing={1}>
                <Text fontSize="sm" color="gray.500">Network I/O</Text>
                <Text fontSize="2xl" fontWeight="bold" color="orange.500">
                  {Math.round(systemMetrics.network.inbound + systemMetrics.network.outbound)}
                </Text>
                <Text fontSize="xs" color="gray.500">
                  Mbps • {systemMetrics.network.latency}ms latency
                </Text>
              </VStack>
              <VStack spacing={1}>
                <Icon as={FiTrendingUp} color="green.500" boxSize={6} />
                <Text fontSize="xs" color="gray.500">
                  ↑{Math.round(systemMetrics.network.inbound)}
                </Text>
                <Text fontSize="xs" color="gray.500">
                  ↓{Math.round(systemMetrics.network.outbound)}
                </Text>
              </VStack>
            </HStack>
          </CardBody>
        </Card>
      </SimpleGrid>

      {/* Main Content Tabs */}
      <Tabs>
        <TabList>
          <Tab>Hardware Overview</Tab>
          <Tab>Modem Health</Tab>
          <Tab>Performance History</Tab>
          <Tab>Alerts & Maintenance</Tab>
        </TabList>

        <TabPanels>
          {/* Hardware Overview Tab */}
          <TabPanel>
            <Grid templateColumns={{ base: '1fr', lg: '2fr 1fr' }} gap={6}>
              {/* Detailed Hardware Metrics */}
              <VStack spacing={6} align="stretch">
                {/* CPU Metrics */}
                <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
                  <CardHeader>
                    <HStack>
                      <Icon as={FiCpu} color="blue.500" boxSize={6} />
                      <Heading size="md">CPU Performance</Heading>
                    </HStack>
                  </CardHeader>
                  <CardBody>
                    <SimpleGrid columns={2} spacing={6}>
                      <VStack align="start" spacing={3}>
                        <Box w="full">
                          <HStack justify="space-between" mb={2}>
                            <Text fontSize="sm">Usage</Text>
                            <Text fontSize="sm" fontWeight="bold">{systemMetrics.cpu.usage}%</Text>
                          </HStack>
                          <Progress
                            value={systemMetrics.cpu.usage}
                            colorScheme={systemMetrics.cpu.usage > 80 ? 'red' : 'blue'}
                            size="lg"
                          />
                        </Box>
                        <Box w="full">
                          <HStack justify="space-between" mb={2}>
                            <Text fontSize="sm">Temperature</Text>
                            <Text fontSize="sm" fontWeight="bold">{systemMetrics.cpu.temperature}°C</Text>
                          </HStack>
                          <Progress
                            value={(systemMetrics.cpu.temperature / 85) * 100}
                            colorScheme={systemMetrics.cpu.temperature > 70 ? 'red' : 'green'}
                            size="lg"
                          />
                        </Box>
                      </VStack>
                      <VStack align="start" spacing={3}>
                        <HStack justify="space-between" w="full">
                          <Text fontSize="sm" color="gray.500">Cores</Text>
                          <Text fontSize="sm" fontWeight="bold">{systemMetrics.cpu.cores}</Text>
                        </HStack>
                        <HStack justify="space-between" w="full">
                          <Text fontSize="sm" color="gray.500">Frequency</Text>
                          <Text fontSize="sm" fontWeight="bold">{systemMetrics.cpu.frequency} GHz</Text>
                        </HStack>
                        <HStack justify="space-between" w="full">
                          <Text fontSize="sm" color="gray.500">Load Average</Text>
                          <Text fontSize="sm" fontWeight="bold">2.45</Text>
                        </HStack>
                      </VStack>
                    </SimpleGrid>
                  </CardBody>
                </Card>

                {/* GPU Metrics */}
                <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
                  <CardHeader>
                    <HStack>
                      <Icon as={FiZap} color="purple.500" boxSize={6} />
                      <Heading size="md">GPU Performance</Heading>
                    </HStack>
                  </CardHeader>
                  <CardBody>
                    <SimpleGrid columns={2} spacing={6}>
                      <VStack align="start" spacing={3}>
                        <Box w="full">
                          <HStack justify="space-between" mb={2}>
                            <Text fontSize="sm">GPU Usage</Text>
                            <Text fontSize="sm" fontWeight="bold">{systemMetrics.gpu.usage}%</Text>
                          </HStack>
                          <Progress
                            value={systemMetrics.gpu.usage}
                            colorScheme="purple"
                            size="lg"
                          />
                        </Box>
                        <Box w="full">
                          <HStack justify="space-between" mb={2}>
                            <Text fontSize="sm">Memory Usage</Text>
                            <Text fontSize="sm" fontWeight="bold">{systemMetrics.gpu.memory}%</Text>
                          </HStack>
                          <Progress
                            value={systemMetrics.gpu.memory}
                            colorScheme={systemMetrics.gpu.memory > 90 ? 'red' : 'blue'}
                            size="lg"
                          />
                        </Box>
                      </VStack>
                      <VStack align="start" spacing={3}>
                        <HStack justify="space-between" w="full">
                          <Text fontSize="sm" color="gray.500">Temperature</Text>
                          <Text fontSize="sm" fontWeight="bold">{systemMetrics.gpu.temperature}°C</Text>
                        </HStack>
                        <HStack justify="space-between" w="full">
                          <Text fontSize="sm" color="gray.500">Power Usage</Text>
                          <Text fontSize="sm" fontWeight="bold">{systemMetrics.gpu.powerUsage}W</Text>
                        </HStack>
                        <HStack justify="space-between" w="full">
                          <Text fontSize="sm" color="gray.500">Clock Speed</Text>
                          <Text fontSize="sm" fontWeight="bold">1.85 GHz</Text>
                        </HStack>
                      </VStack>
                    </SimpleGrid>
                  </CardBody>
                </Card>

                {/* Storage & Network */}
                <SimpleGrid columns={{ base: 1, md: 2 }} spacing={6}>
                  <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
                    <CardHeader>
                      <HStack>
                        <Icon as={FiHardDrive} color="green.500" boxSize={5} />
                        <Heading size="sm">Storage</Heading>
                      </HStack>
                    </CardHeader>
                    <CardBody>
                      <VStack spacing={3}>
                        <HStack justify="space-between" w="full">
                          <Text fontSize="sm">Used Space</Text>
                          <Text fontSize="sm" fontWeight="bold">
                            {systemMetrics.storage.used}TB / {systemMetrics.storage.total}TB
                          </Text>
                        </HStack>
                        <Progress value={systemMetrics.storage.usage} colorScheme="green" size="lg" w="full" />
                        <HStack justify="space-between" w="full">
                          <Text fontSize="sm" color="gray.500">IOPS</Text>
                          <Text fontSize="sm" fontWeight="bold">{systemMetrics.storage.iops.toLocaleString()}</Text>
                        </HStack>
                      </VStack>
                    </CardBody>
                  </Card>

                  <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
                    <CardHeader>
                      <HStack>
                        <Icon as={FiWifi} color="orange.500" boxSize={5} />
                        <Heading size="sm">Network</Heading>
                      </HStack>
                    </CardHeader>
                    <CardBody>
                      <VStack spacing={3}>
                        <HStack justify="space-between" w="full">
                          <Text fontSize="sm">Inbound</Text>
                          <Text fontSize="sm" fontWeight="bold">{Math.round(systemMetrics.network.inbound)} Mbps</Text>
                        </HStack>
                        <HStack justify="space-between" w="full">
                          <Text fontSize="sm">Outbound</Text>
                          <Text fontSize="sm" fontWeight="bold">{Math.round(systemMetrics.network.outbound)} Mbps</Text>
                        </HStack>
                        <HStack justify="space-between" w="full">
                          <Text fontSize="sm" color="gray.500">Latency</Text>
                          <Text fontSize="sm" fontWeight="bold">{systemMetrics.network.latency}ms</Text>
                        </HStack>
                      </VStack>
                    </CardBody>
                  </Card>
                </SimpleGrid>
              </VStack>

              {/* System Status Summary */}
              <VStack spacing={6} align="stretch">
                <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
                  <CardHeader>
                    <Heading size="md">Modem Status</Heading>
                  </CardHeader>
                  <CardBody>
                    <Box h="250px">
                      <Doughnut data={modemStatusData} options={chartOptions} />
                    </Box>
                  </CardBody>
                </Card>

                <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
                  <CardHeader>
                    <Heading size="md">System Status</Heading>
                  </CardHeader>
                  <CardBody>
                    <VStack spacing={4}>
                      <HStack justify="space-between" w="full">
                        <HStack>
                          <Icon as={FiCheckCircle} color="green.500" />
                          <Text fontSize="sm">System Uptime</Text>
                        </HStack>
                        <Text fontSize="sm" fontWeight="bold">99.8%</Text>
                      </HStack>
                      
                      <HStack justify="space-between" w="full">
                        <HStack>
                          <Icon as={FiActivity} color="blue.500" />
                          <Text fontSize="sm">Active Processes</Text>
                        </HStack>
                        <Text fontSize="sm" fontWeight="bold">247</Text>
                      </HStack>
                      
                      <HStack justify="space-between" w="full">
                        <HStack>
                          <Icon as={FiShield} color="purple.500" />
                          <Text fontSize="sm">Security Status</Text>
                        </HStack>
                        <Badge colorScheme="green" size="sm">Secure</Badge>
                      </HStack>
                      
                      <HStack justify="space-between" w="full">
                        <HStack>
                          <Icon as={FiDatabase} color="orange.500" />
                          <Text fontSize="sm">Database Health</Text>
                        </HStack>
                        <Badge colorScheme="green" size="sm">Optimal</Badge>
                      </HStack>
                    </VStack>
                  </CardBody>
                </Card>
              </VStack>
            </Grid>
          </TabPanel>

          {/* Modem Health Tab */}
          <TabPanel>
            <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
              <CardHeader>
                <HStack justify="space-between">
                  <Heading size="md">Modem Health Status (80 Modems)</Heading>
                  <HStack>
                    <Button size="sm" leftIcon={<FiSettings />} variant="outline">
                      Configure
                    </Button>
                    <Button size="sm" leftIcon={<FiRefreshCw />} variant="outline">
                      Refresh All
                    </Button>
                  </HStack>
                </HStack>
              </CardHeader>
              <CardBody>
                <TableContainer>
                  <Table variant="simple" size="sm">
                    <Thead>
                      <Tr>
                        <Th>Modem ID</Th>
                        <Th>Status</Th>
                        <Th>Signal Strength</Th>
                        <Th>Temperature</Th>
                        <Th>Uptime</Th>
                        <Th>Calls Today</Th>
                        <Th>Error Rate</Th>
                        <Th>Predicted Failure</Th>
                        <Th>Actions</Th>
                      </Tr>
                    </Thead>
                    <Tbody>
                      {modemHealth.slice(0, 20).map((modem) => (
                        <Tr key={modem.id}>
                          <Td fontFamily="mono">{modem.id}</Td>
                          <Td>
                            <Badge colorScheme={getStatusColor(modem.status)} size="sm">
                              {modem.status}
                            </Badge>
                          </Td>
                          <Td>
                            <HStack>
                              <Progress
                                value={(modem.signalStrength + 100) / 1.4} // Convert dBm to percentage
                                size="sm"
                                colorScheme={modem.signalStrength > -70 ? 'green' : modem.signalStrength > -80 ? 'yellow' : 'red'}
                                w="50px"
                              />
                              <Text fontSize="xs">{modem.signalStrength} dBm</Text>
                            </HStack>
                          </Td>
                          <Td>
                            <Text fontSize="sm" color={modem.temperature > 60 ? 'red.500' : 'inherit'}>
                              {modem.temperature}°C
                            </Text>
                          </Td>
                          <Td>{Math.floor(modem.uptime / 24)}d {modem.uptime % 24}h</Td>
                          <Td>{modem.callsToday}</Td>
                          <Td>
                            <Text fontSize="sm" color={modem.errorRate > 2 ? 'red.500' : 'inherit'}>
                              {modem.errorRate.toFixed(1)}%
                            </Text>
                          </Td>
                          <Td>
                            <Text fontSize="sm" color={modem.predictedFailure < 30 ? 'red.500' : modem.predictedFailure < 90 ? 'yellow.500' : 'green.500'}>
                              {modem.predictedFailure}d
                            </Text>
                          </Td>
                          <Td>
                            <HStack spacing={1}>
                              <Tooltip label="View Details">
                                <IconButton
                                  aria-label="View details"
                                  icon={<FiMonitor />}
                                  size="xs"
                                  variant="ghost"
                                />
                              </Tooltip>
                              <Tooltip label="Restart">
                                <IconButton
                                  aria-label="Restart"
                                  icon={<FiRefreshCw />}
                                  size="xs"
                                  variant="ghost"
                                />
                              </Tooltip>
                            </HStack>
                          </Td>
                        </Tr>
                      ))}
                    </Tbody>
                  </Table>
                </TableContainer>
                
                <Flex justify="center" mt={4}>
                  <Text fontSize="sm" color="gray.500">
                    Showing 20 of 80 modems • {healthyModems} healthy, {warningModems} warning, {criticalModems} critical, {offlineModems} offline
                  </Text>
                </Flex>
              </CardBody>
            </Card>
          </TabPanel>

          {/* Performance History Tab */}
          <TabPanel>
            <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
              <CardHeader>
                <Heading size="md">Performance History</Heading>
                <Text fontSize="sm" color="gray.500">
                  Real-time system performance metrics
                </Text>
              </CardHeader>
              <CardBody>
                <Box h="400px">
                  <Line data={performanceHistoryData} options={chartOptions} />
                </Box>
              </CardBody>
            </Card>
          </TabPanel>

          {/* Alerts & Maintenance Tab */}
          <TabPanel>
            <Grid templateColumns={{ base: '1fr', lg: '2fr 1fr' }} gap={6}>
              <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
                <CardHeader>
                  <HStack justify="space-between">
                    <Heading size="md">System Alerts</Heading>
                    <Button size="sm" colorScheme="blue">
                      Acknowledge All
                    </Button>
                  </HStack>
                </CardHeader>
                <CardBody>
                  <VStack spacing={4} align="stretch">
                    {systemAlerts.map((alert) => (
                      <Alert key={alert.id} status={getSeverityColor(alert.severity)} borderRadius="md">
                        <AlertIcon />
                        <Box flex="1">
                          <HStack justify="space-between" mb={1}>
                            <Text fontSize="sm" fontWeight="bold">
                              {alert.component}
                            </Text>
                            <Text fontSize="xs" color="gray.500">
                              {alert.timestamp.toLocaleTimeString()}
                            </Text>
                          </HStack>
                          <Text fontSize="sm">{alert.message}</Text>
                        </Box>
                        {!alert.acknowledged && (
                          <Button size="xs" variant="outline">
                            Acknowledge
                          </Button>
                        )}
                      </Alert>
                    ))}
                  </VStack>
                </CardBody>
              </Card>

              <VStack spacing={6} align="stretch">
                <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
                  <CardHeader>
                    <Heading size="md">Maintenance Schedule</Heading>
                  </CardHeader>
                  <CardBody>
                    <VStack spacing={3} align="stretch">
                      <Box p={3} borderWidth="1px" borderRadius="md" borderColor="blue.200" bg="blue.50">
                        <HStack justify="space-between" mb={1}>
                          <Text fontSize="sm" fontWeight="bold">Scheduled Maintenance</Text>
                          <Badge colorScheme="blue" size="sm">Upcoming</Badge>
                        </HStack>
                        <Text fontSize="xs" color="gray.600">
                          System update and modem calibration
                        </Text>
                        <Text fontSize="xs" color="gray.500">
                          Today, 2:00 AM - 4:00 AM
                        </Text>
                      </Box>
                      
                      <Box p={3} borderWidth="1px" borderRadius="md">
                        <HStack justify="space-between" mb={1}>
                          <Text fontSize="sm" fontWeight="bold">GPU Maintenance</Text>
                          <Badge colorScheme="green" size="sm">Completed</Badge>
                        </HStack>
                        <Text fontSize="xs" color="gray.600">
                          Driver update and thermal optimization
                        </Text>
                        <Text fontSize="xs" color="gray.500">
                          Yesterday, 3:00 AM
                        </Text>
                      </Box>
                    </VStack>
                  </CardBody>
                </Card>

                <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
                  <CardHeader>
                    <Heading size="md">Quick Actions</Heading>
                  </CardHeader>
                  <CardBody>
                    <VStack spacing={3}>
                      <Button size="sm" w="full" leftIcon={<FiRefreshCw />} colorScheme="blue">
                        Restart All Modems
                      </Button>
                      <Button size="sm" w="full" leftIcon={<FiSettings />} variant="outline">
                        System Configuration
                      </Button>
                      <Button size="sm" w="full" leftIcon={<FiBarChart3 />} variant="outline">
                        Generate Report
                      </Button>
                      <Button size="sm" w="full" leftIcon={<FiShield />} variant="outline">
                        Security Scan
                      </Button>
                    </VStack>
                  </CardBody>
                </Card>
              </VStack>
            </Grid>
          </TabPanel>
        </TabPanels>
      </Tabs>
    </Box>
  );
};

export default SystemMonitoring;