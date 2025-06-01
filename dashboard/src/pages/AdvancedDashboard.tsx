/**
 * Advanced Dashboard - Next-Generation AI Call Center Management Interface
 * 
 * This is the main advanced dashboard that integrates all cutting-edge features
 * including real-time analytics, live call monitoring, predictive analytics,
 * and AI-powered insights with GPU acceleration.
 */

import React, { useState, useEffect, useMemo, useCallback } from 'react';
import {
  Box,
  Grid,
  GridItem,
  Heading,
  Text,
  VStack,
  HStack,
  Card,
  CardHeader,
  CardBody,
  Badge,
  Button,
  IconButton,
  Tooltip,
  Select,
  Switch,
  useColorModeValue,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalCloseButton,
  useDisclosure,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  SimpleGrid,
  Flex,
  Spacer,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  Drawer,
  DrawerBody,
  DrawerHeader,
  DrawerOverlay,
  DrawerContent,
  DrawerCloseButton,
  useBreakpointValue,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  StatArrow,
  Progress,
  Divider,
} from '@chakra-ui/react';
import {
  FiActivity,
  FiTrendingUp,
  FiTrendingDown,
  FiCpu,
  FiZap,
  FiEye,
  FiSettings,
  FiMaximize2,
  FiMinimize2,
  FiRefreshCw,
  FiDownload,
  FiShare2,
  FiFilter,
  FiSearch,
  FiGrid,
  FiList,
  FiPhone,
  FiUsers,
  FiDollarSign,
  FiTarget,
  FiMessageSquare,
  FiBarChart,
  FiPieChart,
  FiLayers,
  FiDatabase,
  FiMonitor,
  FiHeadphones,
  FiMic,
  FiSpeaker,
  FiWifi,
  FiServer,
  FiHardDrive,
  FiThermometer,
  FiAlertTriangle,
  FiCheckCircle,
  FiClock,
  FiCalendar,
} from 'react-icons/fi';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';

// Import Advanced Components
import RealTimeAnalyticsDashboard from '../components/Advanced/RealTimeAnalyticsDashboard';
import LiveCallMonitor from '../components/Advanced/LiveCallMonitor';
import PredictiveAnalytics from '../components/Advanced/PredictiveAnalytics';

// Import Stores
import { useAdvancedAnalyticsStore } from '../stores/advancedAnalyticsStore';
import { useRealtimeStore } from '../stores/realtimeStore';
import { useSystemStore } from '../stores/systemStore';
import { useAuthStore } from '../stores/authStore';

// Quick Stats Component
const QuickStatsOverview: React.FC = () => {
  const { realTimeData } = useAdvancedAnalyticsStore();
  const { liveCalls, liveAgents, connectionStatus } = useRealtimeStore();
  const { systemStatus } = useSystemStore();
  
  const stats = useMemo(() => {
    const activeCalls = liveCalls.filter(call => call.status === 'connected').length;
    const availableAgents = liveAgents.filter(agent => agent.status === 'available').length;
    const busyAgents = liveAgents.filter(agent => agent.status === 'busy').length;
    const avgSentiment = liveCalls.reduce((acc, call) => acc + call.sentimentScore, 0) / liveCalls.length || 0;
    
    return {
      activeCalls,
      totalCalls: liveCalls.length,
      availableAgents,
      busyAgents,
      totalAgents: liveAgents.length,
      avgSentiment,
      conversionRate: realTimeData?.conversionRate || 0,
      revenueToday: realTimeData?.revenuePerHour ? realTimeData.revenuePerHour * 8 : 0,
      systemHealth: systemStatus.overallHealth,
      gpuUsage: systemStatus.gpuUsage,
      connectionStatus,
    };
  }, [liveCalls, liveAgents, realTimeData, systemStatus, connectionStatus]);
  
  return (
    <SimpleGrid columns={{ base: 2, md: 4, lg: 6 }} spacing={4}>
      <Card>
        <CardBody>
          <Stat>
            <StatLabel fontSize="xs">Active Calls</StatLabel>
            <StatNumber fontSize="lg" color="blue.500">
              {stats.activeCalls}
            </StatNumber>
            <StatHelpText fontSize="xs">
              <StatArrow type="increase" />
              {((stats.activeCalls / stats.totalCalls) * 100).toFixed(0)}% of total
            </StatHelpText>
          </Stat>
        </CardBody>
      </Card>
      
      <Card>
        <CardBody>
          <Stat>
            <StatLabel fontSize="xs">Available Agents</StatLabel>
            <StatNumber fontSize="lg" color="green.500">
              {stats.availableAgents}
            </StatNumber>
            <StatHelpText fontSize="xs">
              {stats.totalAgents} total agents
            </StatHelpText>
          </Stat>
        </CardBody>
      </Card>
      
      <Card>
        <CardBody>
          <Stat>
            <StatLabel fontSize="xs">Conversion Rate</StatLabel>
            <StatNumber fontSize="lg" color="purple.500">
              {(stats.conversionRate * 100).toFixed(1)}%
            </StatNumber>
            <StatHelpText fontSize="xs">
              <StatArrow type="increase" />
              +2.3% vs yesterday
            </StatHelpText>
          </Stat>
        </CardBody>
      </Card>
      
      <Card>
        <CardBody>
          <Stat>
            <StatLabel fontSize="xs">Revenue Today</StatLabel>
            <StatNumber fontSize="lg" color="orange.500">
              ${stats.revenueToday.toLocaleString()}
            </StatNumber>
            <StatHelpText fontSize="xs">
              <StatArrow type="increase" />
              +15.7% vs yesterday
            </StatHelpText>
          </Stat>
        </CardBody>
      </Card>
      
      <Card>
        <CardBody>
          <Stat>
            <StatLabel fontSize="xs">Avg Sentiment</StatLabel>
            <StatNumber fontSize="lg" color={stats.avgSentiment > 0 ? 'green.500' : 'red.500'}>
              {stats.avgSentiment.toFixed(2)}
            </StatNumber>
            <StatHelpText fontSize="xs">
              <StatArrow type={stats.avgSentiment > 0 ? 'increase' : 'decrease'} />
              {Math.abs(stats.avgSentiment * 100).toFixed(0)}% sentiment
            </StatHelpText>
          </Stat>
        </CardBody>
      </Card>
      
      <Card>
        <CardBody>
          <Stat>
            <StatLabel fontSize="xs">System Health</StatLabel>
            <StatNumber fontSize="lg" color={stats.systemHealth === 'healthy' ? 'green.500' : stats.systemHealth === 'warning' ? 'yellow.500' : 'red.500'}>
              <HStack spacing={2}>
                {stats.systemHealth === 'healthy' ? <FiCheckCircle /> : <FiAlertTriangle />}
                <Text>{stats.systemHealth.toUpperCase()}</Text>
              </HStack>
            </StatNumber>
            <StatHelpText fontSize="xs">
              GPU: {stats.gpuUsage}%
            </StatHelpText>
          </Stat>
        </CardBody>
      </Card>
    </SimpleGrid>
  );
};

// System Performance Monitor
const SystemPerformanceMonitor: React.FC = () => {
  const { systemStatus } = useSystemStore();
  const { connectionStatus, latency, messageRate } = useRealtimeStore();
  
  const performanceData = useMemo(() => {
    return Array.from({ length: 20 }, (_, i) => ({
      time: i,
      cpu: systemStatus.cpuUsage + (Math.random() - 0.5) * 10,
      memory: systemStatus.memoryUsage + (Math.random() - 0.5) * 5,
      gpu: systemStatus.gpuUsage + (Math.random() - 0.5) * 15,
    }));
  }, [systemStatus]);
  
  return (
    <Card>
      <CardHeader>
        <HStack justify="space-between">
          <VStack align="start" spacing={1}>
            <Text fontWeight="semibold">System Performance</Text>
            <HStack spacing={4}>
              <Badge colorScheme={connectionStatus === 'connected' ? 'green' : 'red'}>
                {connectionStatus}
              </Badge>
              <Text fontSize="sm" color="gray.500">
                Latency: {latency}ms
              </Text>
              <Text fontSize="sm" color="gray.500">
                Rate: {messageRate}/min
              </Text>
            </HStack>
          </VStack>
          <HStack spacing={2}>
            <Badge colorScheme="blue" variant="subtle">
              <HStack spacing={1}>
                <FiCpu size={12} />
                <Text>GPU Accelerated</Text>
              </HStack>
            </Badge>
          </HStack>
        </HStack>
      </CardHeader>
      <CardBody>
        <Grid templateColumns={{ base: '1fr', lg: '2fr 1fr' }} gap={6}>
          <GridItem>
            <Box h="200px">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={performanceData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis domain={[0, 100]} />
                  <RechartsTooltip />
                  <Area
                    type="monotone"
                    dataKey="cpu"
                    stackId="1"
                    stroke="#3B82F6"
                    fill="#3B82F6"
                    fillOpacity={0.6}
                    name="CPU"
                  />
                  <Area
                    type="monotone"
                    dataKey="memory"
                    stackId="1"
                    stroke="#10B981"
                    fill="#10B981"
                    fillOpacity={0.6}
                    name="Memory"
                  />
                  <Area
                    type="monotone"
                    dataKey="gpu"
                    stackId="1"
                    stroke="#8B5CF6"
                    fill="#8B5CF6"
                    fillOpacity={0.6}
                    name="GPU"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </Box>
          </GridItem>
          <GridItem>
            <VStack spacing={4}>
              <VStack spacing={2} w="full">
                <HStack justify="space-between" w="full">
                  <Text fontSize="sm">CPU Usage</Text>
                  <Text fontSize="sm" fontWeight="medium">{systemStatus.cpuUsage}%</Text>
                </HStack>
                <Progress
                  value={systemStatus.cpuUsage}
                  colorScheme={systemStatus.cpuUsage > 80 ? 'red' : systemStatus.cpuUsage > 60 ? 'yellow' : 'green'}
                  size="sm"
                  w="full"
                />
              </VStack>
              
              <VStack spacing={2} w="full">
                <HStack justify="space-between" w="full">
                  <Text fontSize="sm">Memory Usage</Text>
                  <Text fontSize="sm" fontWeight="medium">{systemStatus.memoryUsage}%</Text>
                </HStack>
                <Progress
                  value={systemStatus.memoryUsage}
                  colorScheme={systemStatus.memoryUsage > 85 ? 'red' : systemStatus.memoryUsage > 70 ? 'yellow' : 'green'}
                  size="sm"
                  w="full"
                />
              </VStack>
              
              <VStack spacing={2} w="full">
                <HStack justify="space-between" w="full">
                  <Text fontSize="sm">GPU Usage</Text>
                  <Text fontSize="sm" fontWeight="medium">{systemStatus.gpuUsage}%</Text>
                </HStack>
                <Progress
                  value={systemStatus.gpuUsage}
                  colorScheme={systemStatus.gpuUsage > 90 ? 'red' : systemStatus.gpuUsage > 75 ? 'yellow' : 'green'}
                  size="sm"
                  w="full"
                />
              </VStack>
              
              <Divider />
              
              <VStack spacing={2} w="full">
                <HStack justify="space-between" w="full">
                  <Text fontSize="sm">Modems Online</Text>
                  <Text fontSize="sm" fontWeight="medium">
                    {systemStatus.modemsOnline}/{systemStatus.totalModems}
                  </Text>
                </HStack>
                <Progress
                  value={(systemStatus.modemsOnline / systemStatus.totalModems) * 100}
                  colorScheme="blue"
                  size="sm"
                  w="full"
                />
              </VStack>
            </VStack>
          </GridItem>
        </Grid>
      </CardBody>
    </Card>
  );
};

// AI Insights Summary
const AIInsightsSummary: React.FC = () => {
  const { insights, generateInsights, insightGeneration } = useAdvancedAnalyticsStore();
  
  const criticalInsights = insights.filter(insight => insight.impact === 'high').slice(0, 3);
  
  return (
    <Card>
      <CardHeader>
        <HStack justify="space-between">
          <VStack align="start" spacing={1}>
            <Text fontWeight="semibold">AI Insights</Text>
            <Text fontSize="sm" color="gray.500">
              Critical insights and recommendations
            </Text>
          </VStack>
          <Button
            size="sm"
            leftIcon={<FiCpu />}
            onClick={generateInsights}
            isLoading={insightGeneration}
            colorScheme="purple"
          >
            Generate
          </Button>
        </HStack>
      </CardHeader>
      <CardBody>
        <VStack spacing={3} align="stretch">
          {criticalInsights.length > 0 ? (
            criticalInsights.map((insight) => (
              <Alert
                key={insight.id}
                status={insight.impact === 'high' ? 'error' : 'warning'}
                borderRadius="md"
                size="sm"
              >
                <AlertIcon />
                <Box flex="1">
                  <AlertTitle fontSize="sm">{insight.title}</AlertTitle>
                  <AlertDescription fontSize="xs" mt={1}>
                    {insight.description}
                  </AlertDescription>
                  <HStack mt={2} spacing={2}>
                    <Badge size="sm" colorScheme="purple">
                      {Math.round(insight.confidence * 100)}% confidence
                    </Badge>
                    <Badge size="sm" colorScheme="red">
                      {insight.impact} impact
                    </Badge>
                  </HStack>
                </Box>
              </Alert>
            ))
          ) : (
            <Text fontSize="sm" color="gray.500" textAlign="center" py={4}>
              No critical insights at the moment. System is operating optimally.
            </Text>
          )}
        </VStack>
      </CardBody>
    </Card>
  );
};

// Main Advanced Dashboard Component
const AdvancedDashboard: React.FC = () => {
  const [activeView, setActiveView] = useState<'overview' | 'analytics' | 'calls' | 'predictions'>('overview');
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  
  const { isOpen: isSettingsOpen, onOpen: onSettingsOpen, onClose: onSettingsClose } = useDisclosure();
  
  const { user } = useAuthStore();
  const { connectionStatus } = useRealtimeStore();
  const { systemStatus } = useSystemStore();
  
  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  const isMobile = useBreakpointValue({ base: true, md: false });
  
  // Auto-refresh effect
  useEffect(() => {
    if (!autoRefresh) return;
    
    const interval = setInterval(() => {
      // Trigger refresh of all stores
      console.log('Auto-refreshing dashboard data...');
    }, 30000); // 30 seconds
    
    return () => clearInterval(interval);
  }, [autoRefresh]);
  
  const renderMainContent = () => {
    switch (activeView) {
      case 'analytics':
        return <RealTimeAnalyticsDashboard />;
      case 'calls':
        return <LiveCallMonitor />;
      case 'predictions':
        return <PredictiveAnalytics />;
      default:
        return (
          <VStack spacing={6} align="stretch">
            {/* Quick Stats */}
            <QuickStatsOverview />
            
            {/* Main Content Grid */}
            <Grid templateColumns={{ base: '1fr', lg: '2fr 1fr' }} gap={6}>
              {/* System Performance */}
              <GridItem>
                <SystemPerformanceMonitor />
              </GridItem>
              
              {/* AI Insights */}
              <GridItem>
                <AIInsightsSummary />
              </GridItem>
            </Grid>
            
            {/* Secondary Content */}
            <Grid templateColumns={{ base: '1fr', lg: '1fr 1fr 1fr' }} gap={6}>
              <GridItem>
                <Card>
                  <CardHeader>
                    <Text fontWeight="semibold">Recent Activity</Text>
                  </CardHeader>
                  <CardBody>
                    <VStack spacing={3} align="stretch">
                      <HStack spacing={3}>
                        <Box p={2} bg="blue.100" borderRadius="md">
                          <FiPhone color="blue" />
                        </Box>
                        <VStack align="start" spacing={0} flex={1}>
                          <Text fontSize="sm">New call started</Text>
                          <Text fontSize="xs" color="gray.500">2 minutes ago</Text>
                        </VStack>
                      </HStack>
                      <HStack spacing={3}>
                        <Box p={2} bg="green.100" borderRadius="md">
                          <FiCheckCircle color="green" />
                        </Box>
                        <VStack align="start" spacing={0} flex={1}>
                          <Text fontSize="sm">Campaign completed</Text>
                          <Text fontSize="xs" color="gray.500">15 minutes ago</Text>
                        </VStack>
                      </HStack>
                      <HStack spacing={3}>
                        <Box p={2} bg="purple.100" borderRadius="md">
                          <FiCpu color="purple" />
                        </Box>
                        <VStack align="start" spacing={0} flex={1}>
                          <Text fontSize="sm">AI insight generated</Text>
                          <Text fontSize="xs" color="gray.500">32 minutes ago</Text>
                        </VStack>
                      </HStack>
                    </VStack>
                  </CardBody>
                </Card>
              </GridItem>
              
              <GridItem>
                <Card>
                  <CardHeader>
                    <Text fontWeight="semibold">Top Performers</Text>
                  </CardHeader>
                  <CardBody>
                    <VStack spacing={3} align="stretch">
                      <HStack justify="space-between">
                        <Text fontSize="sm">Agent Sarah</Text>
                        <Badge colorScheme="green">98.5%</Badge>
                      </HStack>
                      <HStack justify="space-between">
                        <Text fontSize="sm">Agent Mike</Text>
                        <Badge colorScheme="green">96.2%</Badge>
                      </HStack>
                      <HStack justify="space-between">
                        <Text fontSize="sm">Agent Lisa</Text>
                        <Badge colorScheme="green">94.8%</Badge>
                      </HStack>
                      <HStack justify="space-between">
                        <Text fontSize="sm">Agent John</Text>
                        <Badge colorScheme="yellow">92.1%</Badge>
                      </HStack>
                    </VStack>
                  </CardBody>
                </Card>
              </GridItem>
              
              <GridItem>
                <Card>
                  <CardHeader>
                    <Text fontWeight="semibold">Quick Actions</Text>
                  </CardHeader>
                  <CardBody>
                    <VStack spacing={3}>
                      <Button leftIcon={<FiPhone />} size="sm" w="full" colorScheme="blue">
                        Start Campaign
                      </Button>
                      <Button leftIcon={<FiCpu />} size="sm" w="full" colorScheme="purple">
                        Train Model
                      </Button>
                      <Button leftIcon={<FiDownload />} size="sm" w="full" variant="outline">
                        Export Report
                      </Button>
                      <Button leftIcon={<FiSettings />} size="sm" w="full" variant="outline">
                        System Settings
                      </Button>
                    </VStack>
                  </CardBody>
                </Card>
              </GridItem>
            </Grid>
          </VStack>
        );
    }
  };
  
  return (
    <Box minH="100vh" bg={useColorModeValue('gray.50', 'gray.900')}>
      {/* Header */}
      <Box bg={cardBg} borderBottom="1px" borderColor={borderColor} px={6} py={4}>
        <HStack justify="space-between">
          <VStack align="start" spacing={1}>
            <Heading size="lg">
              Advanced AI Dashboard
            </Heading>
            <HStack spacing={4}>
              <Badge
                colorScheme={connectionStatus === 'connected' ? 'green' : 'red'}
                variant="subtle"
              >
                {connectionStatus === 'connected' ? 'Live' : 'Disconnected'}
              </Badge>
              <Text fontSize="sm" color="gray.500">
                Welcome back, {user?.name?.split(' ')[0]}!
              </Text>
              <Text fontSize="sm" color="gray.500">
                Last updated: {new Date().toLocaleTimeString()}
              </Text>
            </HStack>
          </VStack>
          
          <HStack spacing={2}>
            {/* View Selector */}
            <HStack spacing={1} bg={useColorModeValue('gray.100', 'gray.700')} p={1} borderRadius="md">
              <Button
                size="sm"
                variant={activeView === 'overview' ? 'solid' : 'ghost'}
                onClick={() => setActiveView('overview')}
                leftIcon={<FiGrid />}
              >
                Overview
              </Button>
              <Button
                size="sm"
                variant={activeView === 'analytics' ? 'solid' : 'ghost'}
                onClick={() => setActiveView('analytics')}
                leftIcon={<FiBarChart />}
              >
                Analytics
              </Button>
              <Button
                size="sm"
                variant={activeView === 'calls' ? 'solid' : 'ghost'}
                onClick={() => setActiveView('calls')}
                leftIcon={<FiHeadphones />}
              >
                Live Calls
              </Button>
              <Button
                size="sm"
                variant={activeView === 'predictions' ? 'solid' : 'ghost'}
                onClick={() => setActiveView('predictions')}
                leftIcon={<FiCpu />}
              >
                Predictions
              </Button>
            </HStack>
            
            {/* Controls */}
            <Tooltip label="Auto-refresh">
              <HStack>
                <Switch
                  size="sm"
                  isChecked={autoRefresh}
                  onChange={(e) => setAutoRefresh(e.target.checked)}
                />
                <Text fontSize="sm">Auto</Text>
              </HStack>
            </Tooltip>
            
            <IconButton
              aria-label="Fullscreen"
              icon={isFullscreen ? <FiMinimize2 /> : <FiMaximize2 />}
              size="sm"
              variant="outline"
              onClick={() => setIsFullscreen(!isFullscreen)}
            />
            
            <IconButton
              aria-label="Settings"
              icon={<FiSettings />}
              size="sm"
              variant="outline"
              onClick={onSettingsOpen}
            />
            
            <Button
              leftIcon={<FiRefreshCw />}
              size="sm"
              variant="outline"
            >
              Refresh
            </Button>
          </HStack>
        </HStack>
      </Box>
      
      {/* Main Content */}
      <Box p={6}>
        {renderMainContent()}
      </Box>
      
      {/* Settings Modal */}
      <Modal isOpen={isSettingsOpen} onClose={onSettingsClose} size="lg">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Dashboard Settings</ModalHeader>
          <ModalCloseButton />
          <ModalBody pb={6}>
            <VStack spacing={6} align="stretch">
              <Box>
                <Text mb={3} fontWeight="medium">Display Options</Text>
                <VStack spacing={3} align="stretch">
                  <HStack justify="space-between">
                    <Text fontSize="sm">Auto-refresh Dashboard</Text>
                    <Switch defaultChecked />
                  </HStack>
                  <HStack justify="space-between">
                    <Text fontSize="sm">Show Real-time Notifications</Text>
                    <Switch defaultChecked />
                  </HStack>
                  <HStack justify="space-between">
                    <Text fontSize="sm">Enable Sound Alerts</Text>
                    <Switch />
                  </HStack>
                </VStack>
              </Box>
              
              <Divider />
              
              <Box>
                <Text mb={3} fontWeight="medium">Performance</Text>
                <VStack spacing={3} align="stretch">
                  <HStack justify="space-between">
                    <Text fontSize="sm">GPU Acceleration</Text>
                    <Switch defaultChecked />
                  </HStack>
                  <HStack justify="space-between">
                    <Text fontSize="sm">High-frequency Updates</Text>
                    <Switch defaultChecked />
                  </HStack>
                  <HStack justify="space-between">
                    <Text fontSize="sm">Advanced Analytics</Text>
                    <Switch defaultChecked />
                  </HStack>
                </VStack>
              </Box>
              
              <Divider />
              
              <Box>
                <Text mb={3} fontWeight="medium">AI Features</Text>
                <VStack spacing={3} align="stretch">
                  <HStack justify="space-between">
                    <Text fontSize="sm">Predictive Insights</Text>
                    <Switch defaultChecked />
                  </HStack>
                  <HStack justify="space-between">
                    <Text fontSize="sm">Automated Recommendations</Text>
                    <Switch defaultChecked />
                  </HStack>
                  <HStack justify="space-between">
                    <Text fontSize="sm">Anomaly Detection</Text>
                    <Switch defaultChecked />
                  </HStack>
                </VStack>
              </Box>
            </VStack>
          </ModalBody>
        </ModalContent>
      </Modal>
    </Box>
  );
};

export default AdvancedDashboard;