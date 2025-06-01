import React, { useEffect, useState } from 'react';
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
  Flex,
  Icon,
  Tooltip,
  Button,
  Select,
  Divider,
} from '@chakra-ui/react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import {
  FiCpu,
  FiHardDrive,
  FiWifi,
  FiUsers,
  FiPhone,
  FiTrendingUp,
  FiTrendingDown,
  FiActivity,
  FiRefreshCw,
  FiAlertTriangle,
  FiCheckCircle,
} from 'react-icons/fi';
import { useDashboardStore } from '../stores/dashboardStore';

interface PerformanceMetric {
  name: string;
  value: number;
  unit: string;
  status: 'excellent' | 'good' | 'warning' | 'critical';
  threshold: number;
  icon: React.ElementType;
}

interface SystemAlert {
  id: string;
  type: 'info' | 'warning' | 'error';
  message: string;
  timestamp: Date;
}

const PerformanceDashboard: React.FC = () => {
  const { metrics, liveMetrics, loading } = useDashboardStore();
  const [timeRange, setTimeRange] = useState('1h');
  const [alerts, setAlerts] = useState<SystemAlert[]>([]);
  const [performanceHistory, setPerformanceHistory] = useState<any[]>([]);

  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');

  // Generate mock performance data
  useEffect(() => {
    const generatePerformanceData = () => {
      const now = new Date();
      const data = [];
      
      for (let i = 23; i >= 0; i--) {
        const time = new Date(now.getTime() - i * 60 * 60 * 1000);
        data.push({
          time: time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          cpu: Math.random() * 80 + 10,
          memory: Math.random() * 70 + 20,
          network: Math.random() * 100 + 50,
          calls: Math.floor(Math.random() * 50) + 10,
          responseTime: Math.random() * 300 + 100,
          throughput: Math.random() * 1000 + 500,
        });
      }
      
      setPerformanceHistory(data);
    };

    generatePerformanceData();
    const interval = setInterval(generatePerformanceData, 30000);

    return () => clearInterval(interval);
  }, [timeRange]);

  // Generate system alerts
  useEffect(() => {
    const generateAlerts = () => {
      const alertMessages = [
        { type: 'info' as const, message: 'System backup completed successfully' },
        { type: 'warning' as const, message: 'High CPU usage detected on server 2' },
        { type: 'error' as const, message: 'Failed to connect to external API' },
        { type: 'info' as const, message: 'New campaign deployed successfully' },
        { type: 'warning' as const, message: 'Memory usage approaching threshold' },
      ];

      const newAlerts = alertMessages.slice(0, 3).map((alert, index) => ({
        id: `alert-${Date.now()}-${index}`,
        ...alert,
        timestamp: new Date(Date.now() - Math.random() * 3600000),
      }));

      setAlerts(newAlerts);
    };

    generateAlerts();
    const interval = setInterval(generateAlerts, 60000);

    return () => clearInterval(interval);
  }, []);

  const performanceMetrics: PerformanceMetric[] = [
    {
      name: 'CPU Usage',
      value: liveMetrics.systemLoad || 45.2,
      unit: '%',
      status: (liveMetrics.systemLoad || 45.2) > 80 ? 'critical' : (liveMetrics.systemLoad || 45.2) > 60 ? 'warning' : 'good',
      threshold: 80,
      icon: FiCpu,
    },
    {
      name: 'Memory Usage',
      value: 62.8,
      unit: '%',
      status: 'good',
      threshold: 85,
      icon: FiHardDrive,
    },
    {
      name: 'Network Latency',
      value: liveMetrics.networkLatency || 45,
      unit: 'ms',
      status: (liveMetrics.networkLatency || 45) > 100 ? 'warning' : 'excellent',
      threshold: 100,
      icon: FiWifi,
    },
    {
      name: 'Active Sessions',
      value: liveMetrics.activeCalls || 28,
      unit: '',
      status: 'excellent',
      threshold: 100,
      icon: FiUsers,
    },
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'excellent': return 'green';
      case 'good': return 'blue';
      case 'warning': return 'yellow';
      case 'critical': return 'red';
      default: return 'gray';
    }
  };

  const getAlertColor = (type: string) => {
    switch (type) {
      case 'info': return 'blue';
      case 'warning': return 'yellow';
      case 'error': return 'red';
      default: return 'gray';
    }
  };

  const getAlertIcon = (type: string) => {
    switch (type) {
      case 'info': return FiCheckCircle;
      case 'warning': return FiAlertTriangle;
      case 'error': return FiAlertTriangle;
      default: return FiActivity;
    }
  };

  const pieData = [
    { name: 'Successful Calls', value: 75, color: '#38A169' },
    { name: 'Failed Calls', value: 15, color: '#E53E3E' },
    { name: 'Pending Calls', value: 10, color: '#D69E2E' },
  ];

  return (
    <VStack spacing={6} align="stretch">
      {/* Header */}
      <HStack justify="space-between">
        <VStack align="start" spacing={1}>
          <Text fontSize="lg" fontWeight="bold">
            Performance Dashboard
          </Text>
          <Text fontSize="sm" color="gray.500">
            Real-time system monitoring and analytics
          </Text>
        </VStack>
        <HStack>
          <Select value={timeRange} onChange={(e) => setTimeRange(e.target.value)} size="sm" maxW="120px">
            <option value="1h">Last Hour</option>
            <option value="6h">Last 6 Hours</option>
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
          </Select>
          <Button leftIcon={<FiRefreshCw />} size="sm" variant="outline">
            Refresh
          </Button>
        </HStack>
      </HStack>

      {/* Performance Metrics Grid */}
      <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={4}>
        {performanceMetrics.map((metric, index) => (
          <Card key={index} bg={cardBg} borderColor={borderColor} borderWidth="1px">
            <CardBody>
              <VStack align="start" spacing={3}>
                <HStack justify="space-between" w="full">
                  <HStack>
                    <Icon as={metric.icon} boxSize={5} color={`${getStatusColor(metric.status)}.500`} />
                    <Text fontSize="sm" fontWeight="medium">
                      {metric.name}
                    </Text>
                  </HStack>
                  <Badge colorScheme={getStatusColor(metric.status)} variant="subtle" size="sm">
                    {metric.status}
                  </Badge>
                </HStack>
                
                <VStack align="start" spacing={1} w="full">
                  <HStack justify="space-between" w="full">
                    <Text fontSize="2xl" fontWeight="bold">
                      {metric.value.toFixed(1)}{metric.unit}
                    </Text>
                    <Text fontSize="xs" color="gray.500">
                      /{metric.threshold}{metric.unit}
                    </Text>
                  </HStack>
                  <Progress
                    value={(metric.value / metric.threshold) * 100}
                    size="sm"
                    colorScheme={getStatusColor(metric.status)}
                    w="full"
                    borderRadius="md"
                  />
                </VStack>
              </VStack>
            </CardBody>
          </Card>
        ))}
      </SimpleGrid>

      {/* Charts Section */}
      <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={6}>
        {/* System Performance Chart */}
        <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
          <CardHeader>
            <Text fontSize="md" fontWeight="bold">
              System Performance Trends
            </Text>
          </CardHeader>
          <CardBody>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={performanceHistory}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <RechartsTooltip />
                <Line
                  type="monotone"
                  dataKey="cpu"
                  stroke="#3182CE"
                  strokeWidth={2}
                  name="CPU %"
                />
                <Line
                  type="monotone"
                  dataKey="memory"
                  stroke="#38A169"
                  strokeWidth={2}
                  name="Memory %"
                />
                <Line
                  type="monotone"
                  dataKey="responseTime"
                  stroke="#D69E2E"
                  strokeWidth={2}
                  name="Response Time (ms)"
                />
              </LineChart>
            </ResponsiveContainer>
          </CardBody>
        </Card>

        {/* Call Distribution */}
        <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
          <CardHeader>
            <Text fontSize="md" fontWeight="bold">
              Call Status Distribution
            </Text>
          </CardHeader>
          <CardBody>
            <Flex justify="center" align="center" h="300px">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <RechartsTooltip />
                </PieChart>
              </ResponsiveContainer>
            </Flex>
            <VStack spacing={2} mt={4}>
              {pieData.map((item, index) => (
                <HStack key={index} justify="space-between" w="full">
                  <HStack>
                    <Box w={3} h={3} bg={item.color} borderRadius="full" />
                    <Text fontSize="sm">{item.name}</Text>
                  </HStack>
                  <Text fontSize="sm" fontWeight="bold">
                    {item.value}%
                  </Text>
                </HStack>
              ))}
            </VStack>
          </CardBody>
        </Card>
      </SimpleGrid>

      {/* Network & Throughput */}
      <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
        <CardHeader>
          <Text fontSize="md" fontWeight="bold">
            Network Throughput & Call Volume
          </Text>
        </CardHeader>
        <CardBody>
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart data={performanceHistory}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <RechartsTooltip />
              <Area
                type="monotone"
                dataKey="throughput"
                stackId="1"
                stroke="#805AD5"
                fill="#805AD5"
                fillOpacity={0.6}
                name="Throughput (KB/s)"
              />
              <Area
                type="monotone"
                dataKey="calls"
                stackId="2"
                stroke="#3182CE"
                fill="#3182CE"
                fillOpacity={0.6}
                name="Active Calls"
              />
            </AreaChart>
          </ResponsiveContainer>
        </CardBody>
      </Card>

      {/* System Alerts */}
      <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
        <CardHeader>
          <HStack justify="space-between">
            <Text fontSize="md" fontWeight="bold">
              System Alerts
            </Text>
            <Badge colorScheme="blue" variant="subtle">
              {alerts.length} Active
            </Badge>
          </HStack>
        </CardHeader>
        <CardBody>
          <VStack spacing={3} align="stretch">
            {alerts.map((alert) => (
              <HStack key={alert.id} p={3} borderRadius="md" bg={useColorModeValue('gray.50', 'gray.700')}>
                <Icon
                  as={getAlertIcon(alert.type)}
                  boxSize={4}
                  color={`${getAlertColor(alert.type)}.500`}
                />
                <VStack align="start" spacing={0} flex={1}>
                  <Text fontSize="sm" fontWeight="medium">
                    {alert.message}
                  </Text>
                  <Text fontSize="xs" color="gray.500">
                    {alert.timestamp.toLocaleString()}
                  </Text>
                </VStack>
                <Badge colorScheme={getAlertColor(alert.type)} variant="subtle" size="sm">
                  {alert.type}
                </Badge>
              </HStack>
            ))}
          </VStack>
        </CardBody>
      </Card>

      {/* Quick Actions */}
      <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
        <CardHeader>
          <Text fontSize="md" fontWeight="bold">
            Quick Actions
          </Text>
        </CardHeader>
        <CardBody>
          <SimpleGrid columns={{ base: 2, md: 4 }} spacing={4}>
            <Button size="sm" variant="outline" leftIcon={<FiRefreshCw />}>
              Restart Services
            </Button>
            <Button size="sm" variant="outline" leftIcon={<FiHardDrive />}>
              Clear Cache
            </Button>
            <Button size="sm" variant="outline" leftIcon={<FiActivity />}>
              Run Diagnostics
            </Button>
            <Button size="sm" variant="outline" leftIcon={<FiTrendingUp />}>
              Generate Report
            </Button>
          </SimpleGrid>
        </CardBody>
      </Card>
    </VStack>
  );
};

export default PerformanceDashboard;