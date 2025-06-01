/**
 * Main Dashboard Page for Project GeminiVoiceConnect
 * 
 * This page provides the main dashboard overview with real-time metrics,
 * system status, recent activities, and key performance indicators.
 */

import React, { useEffect, useState } from 'react';
import {
  Box,
  Grid,
  GridItem,
  Heading,
  Text,
  VStack,
  HStack,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  StatArrow,
  useColorModeValue,
  Card,
  CardHeader,
  CardBody,
  Badge,
  Progress,
  Divider,
  Button,
  IconButton,
  Tooltip,
  SimpleGrid,
  Flex,
  Spacer,
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
  FiWifi,
  FiRefreshCw,
  FiExternalLink,
  FiAlertTriangle,
  FiCheckCircle,
} from 'react-icons/fi';
import { useSystemStore } from '../stores/systemStore';
import { useAuthStore } from '../stores/authStore';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';

interface MetricCardProps {
  title: string;
  value: string | number;
  change?: number;
  changeLabel?: string;
  icon: React.ElementType;
  color: string;
  isLoading?: boolean;
}

const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  change,
  changeLabel,
  icon: Icon,
  color,
  isLoading = false,
}) => {
  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');

  return (
    <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
      <CardBody>
        <HStack spacing={4}>
          <Box
            p={3}
            borderRadius="lg"
            bg={`${color}.100`}
            color={`${color}.600`}
          >
            <Icon size={24} />
          </Box>
          <VStack align="start" spacing={1} flex={1}>
            <Text fontSize="sm" color="gray.500" fontWeight="medium">
              {title}
            </Text>
            <Text fontSize="2xl" fontWeight="bold">
              {isLoading ? '...' : value}
            </Text>
            {change !== undefined && (
              <HStack spacing={1}>
                <StatArrow type={change >= 0 ? 'increase' : 'decrease'} />
                <Text fontSize="sm" color={change >= 0 ? 'green.500' : 'red.500'}>
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
        </HStack>
      </CardBody>
    </Card>
  );
};

interface SystemHealthCardProps {
  title: string;
  status: 'healthy' | 'warning' | 'critical';
  details: Array<{
    label: string;
    value: string | number;
    status?: 'healthy' | 'warning' | 'critical';
  }>;
}

const SystemHealthCard: React.FC<SystemHealthCardProps> = ({ title, status, details }) => {
  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'green';
      case 'warning': return 'yellow';
      case 'critical': return 'red';
      default: return 'gray';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy': return FiCheckCircle;
      case 'warning': return FiAlertTriangle;
      case 'critical': return FiAlertTriangle;
      default: return FiActivity;
    }
  };

  const StatusIcon = getStatusIcon(status);

  return (
    <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
      <CardHeader pb={2}>
        <HStack justify="space-between">
          <Text fontWeight="semibold">{title}</Text>
          <HStack spacing={2}>
            <StatusIcon color={getStatusColor(status)} size={16} />
            <Badge colorScheme={getStatusColor(status)} size="sm">
              {status.toUpperCase()}
            </Badge>
          </HStack>
        </HStack>
      </CardHeader>
      <CardBody pt={0}>
        <VStack spacing={3} align="stretch">
          {details.map((detail, index) => (
            <HStack key={index} justify="space-between">
              <Text fontSize="sm" color="gray.600">
                {detail.label}
              </Text>
              <HStack spacing={2}>
                <Text fontSize="sm" fontWeight="medium">
                  {detail.value}
                </Text>
                {detail.status && (
                  <Box
                    w={2}
                    h={2}
                    borderRadius="full"
                    bg={`${getStatusColor(detail.status)}.500`}
                  />
                )}
              </HStack>
            </HStack>
          ))}
        </VStack>
      </CardBody>
    </Card>
  );
};

const Dashboard: React.FC = () => {
  const { user } = useAuthStore();
  const { systemStatus, metrics, refreshSystemStatus, isLoading } = useSystemStore();
  const [timeRange, setTimeRange] = useState('24h');

  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');

  useEffect(() => {
    // Initial load
    refreshSystemStatus();
  }, [refreshSystemStatus]);

  // Mock data for charts
  const performanceData = [
    { time: '00:00', calls: 45, sms: 120, revenue: 1200 },
    { time: '04:00', calls: 32, sms: 89, revenue: 980 },
    { time: '08:00', calls: 67, sms: 156, revenue: 1850 },
    { time: '12:00', calls: 89, sms: 203, revenue: 2340 },
    { time: '16:00', calls: 76, sms: 178, revenue: 2100 },
    { time: '20:00', calls: 54, sms: 134, revenue: 1650 },
  ];

  const modemStatusData = [
    { name: 'Online', value: systemStatus.modemsOnline, color: '#10B981' },
    { name: 'Offline', value: systemStatus.totalModems - systemStatus.modemsOnline, color: '#EF4444' },
  ];

  const recentActivities = [
    {
      id: 1,
      type: 'call',
      message: 'New inbound call from +1-555-0123',
      timestamp: '2 minutes ago',
      status: 'active',
    },
    {
      id: 2,
      type: 'sms',
      message: 'SMS campaign "Holiday Sale" completed',
      timestamp: '15 minutes ago',
      status: 'completed',
    },
    {
      id: 3,
      type: 'system',
      message: 'Modem #23 came back online',
      timestamp: '32 minutes ago',
      status: 'resolved',
    },
    {
      id: 4,
      type: 'revenue',
      message: 'New customer conversion: $450 revenue',
      timestamp: '1 hour ago',
      status: 'success',
    },
  ];

  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'call': return FiPhone;
      case 'sms': return FiMessageSquare;
      case 'system': return FiCpu;
      case 'revenue': return FiDollarSign;
      default: return FiActivity;
    }
  };

  const getActivityColor = (status: string) => {
    switch (status) {
      case 'active': return 'blue';
      case 'completed': return 'green';
      case 'resolved': return 'green';
      case 'success': return 'green';
      case 'warning': return 'yellow';
      case 'error': return 'red';
      default: return 'gray';
    }
  };

  return (
    <Box>
      {/* Header */}
      <VStack align="start" spacing={4} mb={8}>
        <HStack justify="space-between" w="full">
          <VStack align="start" spacing={1}>
            <Heading size="lg">
              Welcome back, {user?.name?.split(' ')[0]}!
            </Heading>
            <Text color="gray.500">
              Here's what's happening with your call center today.
            </Text>
          </VStack>
          <HStack spacing={2}>
            <Button
              leftIcon={<FiRefreshCw />}
              variant="outline"
              size="sm"
              onClick={refreshSystemStatus}
              isLoading={isLoading}
            >
              Refresh
            </Button>
            <Button
              leftIcon={<FiExternalLink />}
              colorScheme="blue"
              size="sm"
            >
              View Reports
            </Button>
          </HStack>
        </HStack>
      </VStack>

      {/* Key Metrics */}
      <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={6} mb={8}>
        <MetricCard
          title="Active Calls"
          value={systemStatus.activeCalls}
          change={12.5}
          changeLabel="vs yesterday"
          icon={FiPhone}
          color="blue"
          isLoading={isLoading}
        />
        <MetricCard
          title="SMS Queue"
          value={systemStatus.smsQueue}
          change={-8.2}
          changeLabel="vs yesterday"
          icon={FiMessageSquare}
          color="green"
          isLoading={isLoading}
        />
        <MetricCard
          title="Online Agents"
          value={systemStatus.onlineAgents}
          change={5.1}
          changeLabel="vs yesterday"
          icon={FiUsers}
          color="purple"
          isLoading={isLoading}
        />
        <MetricCard
          title="Today's Revenue"
          value={`$${systemStatus.todayRevenue?.toLocaleString()}`}
          change={18.7}
          changeLabel="vs yesterday"
          icon={FiDollarSign}
          color="orange"
          isLoading={isLoading}
        />
      </SimpleGrid>

      {/* Main Content Grid */}
      <Grid templateColumns={{ base: '1fr', lg: '2fr 1fr' }} gap={6} mb={8}>
        {/* Performance Chart */}
        <GridItem>
          <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
            <CardHeader>
              <HStack justify="space-between">
                <VStack align="start" spacing={1}>
                  <Text fontWeight="semibold">Performance Overview</Text>
                  <Text fontSize="sm" color="gray.500">
                    Real-time system performance metrics
                  </Text>
                </VStack>
                <HStack spacing={2}>
                  {['1h', '6h', '24h', '7d'].map((range) => (
                    <Button
                      key={range}
                      size="xs"
                      variant={timeRange === range ? 'solid' : 'ghost'}
                      onClick={() => setTimeRange(range)}
                    >
                      {range}
                    </Button>
                  ))}
                </HStack>
              </HStack>
            </CardHeader>
            <CardBody>
              <Box h="300px">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={performanceData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="time" />
                    <YAxis />
                    <RechartsTooltip />
                    <Line
                      type="monotone"
                      dataKey="calls"
                      stroke="#3B82F6"
                      strokeWidth={2}
                      name="Active Calls"
                    />
                    <Line
                      type="monotone"
                      dataKey="sms"
                      stroke="#10B981"
                      strokeWidth={2}
                      name="SMS Queue"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </Box>
            </CardBody>
          </Card>
        </GridItem>

        {/* System Health */}
        <GridItem>
          <VStack spacing={6} align="stretch">
            <SystemHealthCard
              title="System Health"
              status={systemStatus.overallHealth}
              details={[
                {
                  label: 'CPU Usage',
                  value: `${systemStatus.cpuUsage}%`,
                  status: systemStatus.cpuUsage > 80 ? 'critical' : systemStatus.cpuUsage > 60 ? 'warning' : 'healthy',
                },
                {
                  label: 'Memory Usage',
                  value: `${systemStatus.memoryUsage}%`,
                  status: systemStatus.memoryUsage > 85 ? 'critical' : systemStatus.memoryUsage > 70 ? 'warning' : 'healthy',
                },
                {
                  label: 'GPU Usage',
                  value: `${systemStatus.gpuUsage}%`,
                  status: systemStatus.gpuUsage > 90 ? 'critical' : systemStatus.gpuUsage > 75 ? 'warning' : 'healthy',
                },
                {
                  label: 'Uptime',
                  value: systemStatus.uptime,
                  status: 'healthy',
                },
              ]}
            />

            <SystemHealthCard
              title="Modem Status"
              status={systemStatus.modemsOnline > 75 ? 'healthy' : systemStatus.modemsOnline > 70 ? 'warning' : 'critical'}
              details={[
                {
                  label: 'Online Modems',
                  value: `${systemStatus.modemsOnline}/${systemStatus.totalModems}`,
                  status: systemStatus.modemsOnline > 75 ? 'healthy' : 'warning',
                },
                {
                  label: 'Success Rate',
                  value: '98.5%',
                  status: 'healthy',
                },
                {
                  label: 'Avg Signal',
                  value: '85%',
                  status: 'healthy',
                },
              ]}
            />
          </VStack>
        </GridItem>
      </Grid>

      {/* Bottom Section */}
      <Grid templateColumns={{ base: '1fr', lg: '1fr 1fr' }} gap={6}>
        {/* Recent Activities */}
        <GridItem>
          <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
            <CardHeader>
              <HStack justify="space-between">
                <Text fontWeight="semibold">Recent Activities</Text>
                <Button size="xs" variant="ghost">
                  View All
                </Button>
              </HStack>
            </CardHeader>
            <CardBody>
              <VStack spacing={4} align="stretch">
                {recentActivities.map((activity) => {
                  const ActivityIcon = getActivityIcon(activity.type);
                  return (
                    <HStack key={activity.id} spacing={3}>
                      <Box
                        p={2}
                        borderRadius="md"
                        bg={`${getActivityColor(activity.status)}.100`}
                        color={`${getActivityColor(activity.status)}.600`}
                      >
                        <ActivityIcon size={16} />
                      </Box>
                      <VStack align="start" spacing={0} flex={1}>
                        <Text fontSize="sm">{activity.message}</Text>
                        <Text fontSize="xs" color="gray.500">
                          {activity.timestamp}
                        </Text>
                      </VStack>
                      <Badge
                        colorScheme={getActivityColor(activity.status)}
                        size="sm"
                      >
                        {activity.status}
                      </Badge>
                    </HStack>
                  );
                })}
              </VStack>
            </CardBody>
          </Card>
        </GridItem>

        {/* Quick Actions */}
        <GridItem>
          <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
            <CardHeader>
              <Text fontWeight="semibold">Quick Actions</Text>
            </CardHeader>
            <CardBody>
              <SimpleGrid columns={2} spacing={4}>
                <Button
                  leftIcon={<FiPhone />}
                  variant="outline"
                  size="sm"
                  h="auto"
                  py={4}
                  flexDirection="column"
                  spacing={2}
                >
                  <Text>Start Call</Text>
                  <Text fontSize="xs" color="gray.500">
                    Initiate outbound call
                  </Text>
                </Button>
                <Button
                  leftIcon={<FiMessageSquare />}
                  variant="outline"
                  size="sm"
                  h="auto"
                  py={4}
                  flexDirection="column"
                  spacing={2}
                >
                  <Text>Send SMS</Text>
                  <Text fontSize="xs" color="gray.500">
                    Quick SMS campaign
                  </Text>
                </Button>
                <Button
                  leftIcon={<FiUsers />}
                  variant="outline"
                  size="sm"
                  h="auto"
                  py={4}
                  flexDirection="column"
                  spacing={2}
                >
                  <Text>Add Customer</Text>
                  <Text fontSize="xs" color="gray.500">
                    New customer entry
                  </Text>
                </Button>
                <Button
                  leftIcon={<FiTrendingUp />}
                  variant="outline"
                  size="sm"
                  h="auto"
                  py={4}
                  flexDirection="column"
                  spacing={2}
                >
                  <Text>View Reports</Text>
                  <Text fontSize="xs" color="gray.500">
                    Analytics dashboard
                  </Text>
                </Button>
              </SimpleGrid>
            </CardBody>
          </Card>
        </GridItem>
      </Grid>
    </Box>
  );
};

export default Dashboard;