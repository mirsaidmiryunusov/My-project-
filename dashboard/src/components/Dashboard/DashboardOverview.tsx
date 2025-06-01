/**
 * Dashboard Overview Component for Project GeminiVoiceConnect
 * 
 * This component provides a comprehensive overview of the AI Call Center Agent system
 * with real-time metrics, performance indicators, and actionable insights. It implements
 * GPU-accelerated analytics visualization and intelligent business intelligence.
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  GridItem,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  StatArrow,
  Card,
  CardHeader,
  CardBody,
  Heading,
  Text,
  HStack,
  VStack,
  Icon,
  Badge,
  Progress,
  useColorModeValue,
  Flex,
  Button,
  IconButton,
  Tooltip,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  Divider,
  SimpleGrid,
  CircularProgress,
  CircularProgressLabel,
} from '@chakra-ui/react';
import {
  FiPhone,
  FiMessageSquare,
  FiUsers,
  FiDollarSign,
  FiTrendingUp,
  FiTrendingDown,
  FiActivity,
  FiCpu,
  FiZap,
  FiTarget,
  FiAlertTriangle,
  FiCheckCircle,
  FiClock,
  FiRefreshCw,
  FiMaximize2,
  FiBarChart,
  FiPieChart,
} from 'react-icons/fi';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip as ChartTooltip,
  Legend,
  ArcElement,
} from 'chart.js';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  ChartTooltip,
  Legend,
  ArcElement
);

interface MetricCardProps {
  title: string;
  value: string | number;
  change?: number;
  changeLabel?: string;
  icon: React.ElementType;
  color: string;
  isLoading?: boolean;
}

interface SystemAlert {
  id: string;
  type: 'info' | 'warning' | 'error' | 'success';
  title: string;
  message: string;
  timestamp: Date;
}

const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  change,
  changeLabel,
  icon,
  color,
  isLoading = false
}) => {
  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');

  return (
    <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
      <CardBody>
        <HStack justify="space-between" align="start">
          <VStack align="start" spacing={1}>
            <Text fontSize="sm" color="gray.500" fontWeight="medium">
              {title}
            </Text>
            <Text fontSize="2xl" fontWeight="bold" color={color}>
              {isLoading ? '...' : value}
            </Text>
            {change !== undefined && (
              <HStack spacing={1}>
                <Icon
                  as={change >= 0 ? FiTrendingUp : FiTrendingDown}
                  color={change >= 0 ? 'green.500' : 'red.500'}
                  boxSize={4}
                />
                <Text
                  fontSize="sm"
                  color={change >= 0 ? 'green.500' : 'red.500'}
                  fontWeight="medium"
                >
                  {Math.abs(change)}%
                </Text>
                {changeLabel && (
                  <Text fontSize="sm" color="gray.500">
                    {changeLabel}
                  </Text>
                )}
              </HStack>
            )}
          </VStack>
          <Box
            p={3}
            borderRadius="lg"
            bg={`${color.split('.')[0]}.50`}
          >
            <Icon as={icon} boxSize={6} color={color} />
          </Box>
        </HStack>
      </CardBody>
    </Card>
  );
};

const DashboardOverview: React.FC = () => {
  const [isLoading, setIsLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(new Date());
  const [autoRefresh, setAutoRefresh] = useState(true);

  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  const textColor = useColorModeValue('gray.700', 'gray.200');

  // Mock real-time data - would come from API/WebSocket
  const [metrics, setMetrics] = useState({
    activeCalls: 45,
    callsToday: 1247,
    smsToday: 3456,
    revenue: 12450,
    conversionRate: 23.5,
    customerSatisfaction: 4.2,
    systemUptime: 99.8,
    gpuUtilization: 67,
    activeModems: 78,
    campaignsActive: 12,
  });

  const [systemAlerts] = useState<SystemAlert[]>([
    {
      id: '1',
      type: 'warning',
      title: 'High GPU Usage',
      message: 'GPU utilization is at 85%. Consider optimizing workloads.',
      timestamp: new Date(Date.now() - 300000), // 5 minutes ago
    },
    {
      id: '2',
      type: 'info',
      title: 'Campaign Performance',
      message: 'Summer Sale campaign is performing 15% above target.',
      timestamp: new Date(Date.now() - 600000), // 10 minutes ago
    },
  ]);

  // Chart data
  const callVolumeData = {
    labels: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00'],
    datasets: [
      {
        label: 'Calls',
        data: [12, 8, 45, 78, 65, 32],
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.4,
      },
      {
        label: 'SMS',
        data: [25, 15, 67, 89, 78, 45],
        borderColor: 'rgb(16, 185, 129)',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        tension: 0.4,
      },
    ],
  };

  const campaignPerformanceData = {
    labels: ['Summer Sale', 'Product Launch', 'Retention', 'Upsell', 'Survey'],
    datasets: [
      {
        label: 'Conversion Rate (%)',
        data: [23.5, 18.2, 31.7, 15.8, 12.3],
        backgroundColor: [
          'rgba(59, 130, 246, 0.8)',
          'rgba(16, 185, 129, 0.8)',
          'rgba(245, 158, 11, 0.8)',
          'rgba(239, 68, 68, 0.8)',
          'rgba(139, 92, 246, 0.8)',
        ],
      },
    ],
  };

  const revenueDistributionData = {
    labels: ['Calls', 'SMS', 'Upsells', 'Renewals'],
    datasets: [
      {
        data: [45, 25, 20, 10],
        backgroundColor: [
          'rgba(59, 130, 246, 0.8)',
          'rgba(16, 185, 129, 0.8)',
          'rgba(245, 158, 11, 0.8)',
          'rgba(139, 92, 246, 0.8)',
        ],
        borderWidth: 0,
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
    scales: {
      y: {
        beginAtZero: true,
      },
    },
  };

  const doughnutOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom' as const,
      },
    },
  };

  useEffect(() => {
    // Simulate loading
    const timer = setTimeout(() => {
      setIsLoading(false);
    }, 1000);

    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      // Simulate real-time updates
      setMetrics(prev => ({
        ...prev,
        activeCalls: Math.max(0, prev.activeCalls + Math.floor(Math.random() * 6) - 3),
        gpuUtilization: Math.max(0, Math.min(100, prev.gpuUtilization + Math.floor(Math.random() * 10) - 5)),
      }));
      setLastUpdated(new Date());
    }, 5000);

    return () => clearInterval(interval);
  }, [autoRefresh]);

  const handleRefresh = () => {
    setIsLoading(true);
    // Simulate API call
    setTimeout(() => {
      setIsLoading(false);
      setLastUpdated(new Date());
    }, 1000);
  };

  return (
    <Box p={6} maxW="full">
      {/* Header */}
      <Flex justify="space-between" align="center" mb={6}>
        <VStack align="start" spacing={1}>
          <Heading size="lg" color={textColor}>
            Dashboard Overview
          </Heading>
          <Text color="gray.500" fontSize="sm">
            Last updated: {lastUpdated.toLocaleTimeString()}
          </Text>
        </VStack>
        
        <HStack spacing={3}>
          <Tooltip label={autoRefresh ? 'Disable auto-refresh' : 'Enable auto-refresh'}>
            <Button
              size="sm"
              variant={autoRefresh ? 'solid' : 'outline'}
              colorScheme="blue"
              leftIcon={<FiActivity />}
              onClick={() => setAutoRefresh(!autoRefresh)}
            >
              {autoRefresh ? 'Live' : 'Paused'}
            </Button>
          </Tooltip>
          
          <Tooltip label="Refresh data">
            <IconButton
              aria-label="Refresh"
              icon={<FiRefreshCw />}
              size="sm"
              variant="outline"
              onClick={handleRefresh}
              isLoading={isLoading}
            />
          </Tooltip>
        </HStack>
      </Flex>

      {/* System Alerts */}
      {systemAlerts.length > 0 && (
        <VStack spacing={3} mb={6} align="stretch">
          {systemAlerts.map(alert => (
            <Alert key={alert.id} status={alert.type} borderRadius="md">
              <AlertIcon />
              <Box flex="1">
                <AlertTitle fontSize="sm">{alert.title}</AlertTitle>
                <AlertDescription fontSize="sm">{alert.message}</AlertDescription>
              </Box>
            </Alert>
          ))}
        </VStack>
      )}

      {/* Key Metrics */}
      <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={6} mb={8}>
        <MetricCard
          title="Active Calls"
          value={metrics.activeCalls}
          change={12.5}
          changeLabel="vs yesterday"
          icon={FiPhone}
          color="blue.500"
          isLoading={isLoading}
        />
        <MetricCard
          title="Today's Revenue"
          value={`$${metrics.revenue.toLocaleString()}`}
          change={8.3}
          changeLabel="vs yesterday"
          icon={FiDollarSign}
          color="green.500"
          isLoading={isLoading}
        />
        <MetricCard
          title="Conversion Rate"
          value={`${metrics.conversionRate}%`}
          change={-2.1}
          changeLabel="vs last week"
          icon={FiTarget}
          color="purple.500"
          isLoading={isLoading}
        />
        <MetricCard
          title="Customer Satisfaction"
          value={metrics.customerSatisfaction}
          change={5.2}
          changeLabel="vs last month"
          icon={FiUsers}
          color="orange.500"
          isLoading={isLoading}
        />
      </SimpleGrid>

      {/* Charts and Analytics */}
      <Grid templateColumns={{ base: '1fr', lg: '2fr 1fr' }} gap={6} mb={8}>
        {/* Call Volume Chart */}
        <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
          <CardHeader>
            <HStack justify="space-between">
              <VStack align="start" spacing={1}>
                <Heading size="md">Call & SMS Volume</Heading>
                <Text color="gray.500" fontSize="sm">
                  Last 24 hours
                </Text>
              </VStack>
              <IconButton
                aria-label="Expand chart"
                icon={<FiMaximize2 />}
                size="sm"
                variant="ghost"
              />
            </HStack>
          </CardHeader>
          <CardBody>
            <Box h="300px">
              <Line data={callVolumeData} options={chartOptions} />
            </Box>
          </CardBody>
        </Card>

        {/* Revenue Distribution */}
        <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
          <CardHeader>
            <Heading size="md">Revenue Distribution</Heading>
            <Text color="gray.500" fontSize="sm">
              Current month
            </Text>
          </CardHeader>
          <CardBody>
            <Box h="300px">
              <Doughnut data={revenueDistributionData} options={doughnutOptions} />
            </Box>
          </CardBody>
        </Card>
      </Grid>

      {/* System Performance and Campaign Performance */}
      <Grid templateColumns={{ base: '1fr', lg: '1fr 1fr' }} gap={6} mb={8}>
        {/* System Performance */}
        <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
          <CardHeader>
            <Heading size="md">System Performance</Heading>
          </CardHeader>
          <CardBody>
            <VStack spacing={6}>
              <HStack justify="space-between" w="full">
                <VStack align="start" spacing={1}>
                  <Text fontSize="sm" color="gray.500">GPU Utilization</Text>
                  <Text fontSize="lg" fontWeight="bold">{metrics.gpuUtilization}%</Text>
                </VStack>
                <CircularProgress
                  value={metrics.gpuUtilization}
                  color={metrics.gpuUtilization > 80 ? 'red.400' : 'blue.400'}
                  size="60px"
                >
                  <CircularProgressLabel fontSize="sm">
                    {metrics.gpuUtilization}%
                  </CircularProgressLabel>
                </CircularProgress>
              </HStack>

              <HStack justify="space-between" w="full">
                <VStack align="start" spacing={1}>
                  <Text fontSize="sm" color="gray.500">Active Modems</Text>
                  <Text fontSize="lg" fontWeight="bold">{metrics.activeModems}/80</Text>
                </VStack>
                <CircularProgress
                  value={(metrics.activeModems / 80) * 100}
                  color="green.400"
                  size="60px"
                >
                  <CircularProgressLabel fontSize="sm">
                    {Math.round((metrics.activeModems / 80) * 100)}%
                  </CircularProgressLabel>
                </CircularProgress>
              </HStack>

              <HStack justify="space-between" w="full">
                <VStack align="start" spacing={1}>
                  <Text fontSize="sm" color="gray.500">System Uptime</Text>
                  <Text fontSize="lg" fontWeight="bold">{metrics.systemUptime}%</Text>
                </VStack>
                <CircularProgress
                  value={metrics.systemUptime}
                  color="purple.400"
                  size="60px"
                >
                  <CircularProgressLabel fontSize="sm">
                    {metrics.systemUptime}%
                  </CircularProgressLabel>
                </CircularProgress>
              </HStack>
            </VStack>
          </CardBody>
        </Card>

        {/* Campaign Performance */}
        <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
          <CardHeader>
            <Heading size="md">Campaign Performance</Heading>
            <Text color="gray.500" fontSize="sm">
              Conversion rates by campaign
            </Text>
          </CardHeader>
          <CardBody>
            <Box h="300px">
              <Bar data={campaignPerformanceData} options={chartOptions} />
            </Box>
          </CardBody>
        </Card>
      </Grid>

      {/* Quick Actions and Recent Activity */}
      <Grid templateColumns={{ base: '1fr', lg: '1fr 1fr' }} gap={6}>
        {/* Quick Actions */}
        <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
          <CardHeader>
            <Heading size="md">Quick Actions</Heading>
          </CardHeader>
          <CardBody>
            <SimpleGrid columns={2} spacing={4}>
              <Button
                leftIcon={<FiTarget />}
                colorScheme="blue"
                variant="outline"
                size="sm"
              >
                New Campaign
              </Button>
              <Button
                leftIcon={<FiBarChart />}
                colorScheme="green"
                variant="outline"
                size="sm"
              >
                View Reports
              </Button>
              <Button
                leftIcon={<FiUsers />}
                colorScheme="purple"
                variant="outline"
                size="sm"
              >
                Manage Customers
              </Button>
              <Button
                leftIcon={<FiCpu />}
                colorScheme="orange"
                variant="outline"
                size="sm"
              >
                System Health
              </Button>
            </SimpleGrid>
          </CardBody>
        </Card>

        {/* Recent Activity */}
        <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
          <CardHeader>
            <Heading size="md">Recent Activity</Heading>
          </CardHeader>
          <CardBody>
            <VStack spacing={4} align="stretch">
              <HStack>
                <Icon as={FiCheckCircle} color="green.500" />
                <VStack align="start" spacing={0} flex={1}>
                  <Text fontSize="sm" fontWeight="medium">
                    Campaign "Summer Sale" completed
                  </Text>
                  <Text fontSize="xs" color="gray.500">
                    2 minutes ago
                  </Text>
                </VStack>
              </HStack>
              
              <HStack>
                <Icon as={FiAlertTriangle} color="orange.500" />
                <VStack align="start" spacing={0} flex={1}>
                  <Text fontSize="sm" fontWeight="medium">
                    Modem #45 requires attention
                  </Text>
                  <Text fontSize="xs" color="gray.500">
                    5 minutes ago
                  </Text>
                </VStack>
              </HStack>
              
              <HStack>
                <Icon as={FiTrendingUp} color="blue.500" />
                <VStack align="start" spacing={0} flex={1}>
                  <Text fontSize="sm" fontWeight="medium">
                    Revenue target exceeded by 15%
                  </Text>
                  <Text fontSize="xs" color="gray.500">
                    1 hour ago
                  </Text>
                </VStack>
              </HStack>
              
              <HStack>
                <Icon as={FiClock} color="purple.500" />
                <VStack align="start" spacing={0} flex={1}>
                  <Text fontSize="sm" fontWeight="medium">
                    Scheduled maintenance in 2 hours
                  </Text>
                  <Text fontSize="xs" color="gray.500">
                    System notification
                  </Text>
                </VStack>
              </HStack>
            </VStack>
          </CardBody>
        </Card>
      </Grid>
    </Box>
  );
};

export default DashboardOverview;