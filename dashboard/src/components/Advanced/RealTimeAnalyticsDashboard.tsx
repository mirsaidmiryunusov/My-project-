/**
 * Real-Time Analytics Dashboard - Advanced GPU-Accelerated Analytics
 * 
 * This component provides a comprehensive real-time analytics dashboard with
 * GPU-accelerated processing, predictive modeling, and AI-powered insights.
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
  Slider,
  SliderTrack,
  SliderFilledTrack,
  SliderThumb,
  Progress,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  useColorModeValue,
  Flex,
  Spacer,
  Divider,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
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
} from '@chakra-ui/react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ComposedChart,
  Treemap,
} from 'recharts';
import {
  FiTrendingUp,
  FiTrendingDown,
  FiActivity,
  FiCpu,
  FiZap,
  FiEye,
  FiRefreshCw,
  FiSettings,
  FiMaximize2,
  FiMinimize2,
  FiDownload,
  FiShare2,
  FiFilter,
  FiSearch,
  FiPlay,
  FiPause,
  FiSkipForward,
  FiAlertTriangle,
  FiCheckCircle,
  FiClock,
  FiTarget,
  FiDollarSign,
  FiUsers,
  FiPhone,
  FiMessageSquare,
} from 'react-icons/fi';
import { useAdvancedAnalyticsStore } from '../../stores/advancedAnalyticsStore';
import { useRealtimeStore } from '../../stores/realtimeStore';

// Advanced Chart Components
const PredictiveModelChart: React.FC<{ modelId: string }> = ({ modelId }) => {
  const { models } = useAdvancedAnalyticsStore();
  const model = models.find(m => m.id === modelId);
  
  if (!model) return null;
  
  const performanceData = [
    { metric: 'Accuracy', value: model.metrics.accuracy * 100, target: 85 },
    { metric: 'Precision', value: model.metrics.precision * 100, target: 80 },
    { metric: 'Recall', value: model.metrics.recall * 100, target: 85 },
    { metric: 'F1-Score', value: model.metrics.f1Score * 100, target: 82 },
    { metric: 'AUC', value: model.metrics.auc * 100, target: 90 },
  ];
  
  return (
    <ResponsiveContainer width="100%" height={300}>
      <ComposedChart data={performanceData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="metric" />
        <YAxis domain={[0, 100]} />
        <RechartsTooltip />
        <Bar dataKey="value" fill="#3B82F6" />
        <Line type="monotone" dataKey="target" stroke="#EF4444" strokeDasharray="5 5" />
      </ComposedChart>
    </ResponsiveContainer>
  );
};

const SentimentHeatmap: React.FC = () => {
  const { realTimeData } = useAdvancedAnalyticsStore();
  
  const heatmapData = useMemo(() => {
    if (!realTimeData) return [];
    
    return realTimeData.sentimentTrends.map((trend, index) => ({
      hour: index,
      positive: trend.positive * 100,
      neutral: trend.neutral * 100,
      negative: trend.negative * 100,
    }));
  }, [realTimeData]);
  
  return (
    <ResponsiveContainer width="100%" height={200}>
      <AreaChart data={heatmapData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="hour" />
        <YAxis />
        <RechartsTooltip />
        <Area
          type="monotone"
          dataKey="positive"
          stackId="1"
          stroke="#10B981"
          fill="#10B981"
          fillOpacity={0.6}
        />
        <Area
          type="monotone"
          dataKey="neutral"
          stackId="1"
          stroke="#F59E0B"
          fill="#F59E0B"
          fillOpacity={0.6}
        />
        <Area
          type="monotone"
          dataKey="negative"
          stackId="1"
          stroke="#EF4444"
          fill="#EF4444"
          fillOpacity={0.6}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
};

const GeographicDistributionMap: React.FC = () => {
  const { realTimeData } = useAdvancedAnalyticsStore();
  
  const mapData = useMemo(() => {
    if (!realTimeData) return [];
    
    return realTimeData.geographicDistribution.map(geo => ({
      name: geo.country,
      value: geo.callVolume,
      revenue: geo.revenue,
      conversion: geo.conversionRate * 100,
    }));
  }, [realTimeData]);
  
  return (
    <ResponsiveContainer width="100%" height={300}>
      <Treemap
        data={mapData}
        dataKey="value"
        stroke="#fff"
        fill="#3B82F6"
      />
    </ResponsiveContainer>
  );
};

const AgentPerformanceRadar: React.FC = () => {
  const { realTimeData } = useAdvancedAnalyticsStore();
  
  const radarData = useMemo(() => {
    if (!realTimeData) return [];
    
    const topAgents = realTimeData.agentPerformance
      .sort((a, b) => b.efficiency - a.efficiency)
      .slice(0, 5);
    
    return [
      {
        metric: 'Efficiency',
        ...topAgents.reduce((acc, agent, i) => ({
          ...acc,
          [`Agent ${i + 1}`]: agent.efficiency * 100,
        }), {}),
      },
      {
        metric: 'Conversion',
        ...topAgents.reduce((acc, agent, i) => ({
          ...acc,
          [`Agent ${i + 1}`]: agent.conversionRate * 100,
        }), {}),
      },
      {
        metric: 'Rating',
        ...topAgents.reduce((acc, agent, i) => ({
          ...acc,
          [`Agent ${i + 1}`]: agent.customerRating * 20,
        }), {}),
      },
    ];
  }, [realTimeData]);
  
  return (
    <ResponsiveContainer width="100%" height={300}>
      <RadarChart data={radarData}>
        <PolarGrid />
        <PolarAngleAxis dataKey="metric" />
        <PolarRadiusAxis domain={[0, 100]} />
        <Radar
          name="Agent 1"
          dataKey="Agent 1"
          stroke="#3B82F6"
          fill="#3B82F6"
          fillOpacity={0.1}
        />
        <Radar
          name="Agent 2"
          dataKey="Agent 2"
          stroke="#10B981"
          fill="#10B981"
          fillOpacity={0.1}
        />
        <Radar
          name="Agent 3"
          dataKey="Agent 3"
          stroke="#F59E0B"
          fill="#F59E0B"
          fillOpacity={0.1}
        />
      </RadarChart>
    </ResponsiveContainer>
  );
};

// Advanced Metric Cards
const AdvancedMetricCard: React.FC<{
  title: string;
  value: string | number;
  change?: number;
  trend?: 'up' | 'down' | 'stable';
  icon: React.ElementType;
  color: string;
  prediction?: number;
  confidence?: number;
}> = ({ title, value, change, trend, icon: Icon, color, prediction, confidence }) => {
  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  
  return (
    <Card bg={cardBg} borderColor={borderColor} borderWidth="1px" position="relative">
      <CardBody>
        <VStack align="stretch" spacing={3}>
          <HStack justify="space-between">
            <Box
              p={2}
              borderRadius="md"
              bg={`${color}.100`}
              color={`${color}.600`}
            >
              <Icon size={20} />
            </Box>
            {trend && (
              <Badge
                colorScheme={trend === 'up' ? 'green' : trend === 'down' ? 'red' : 'gray'}
                variant="subtle"
              >
                {trend === 'up' ? <FiTrendingUp /> : trend === 'down' ? <FiTrendingDown /> : <FiActivity />}
              </Badge>
            )}
          </HStack>
          
          <VStack align="start" spacing={1}>
            <Text fontSize="sm" color="gray.500" fontWeight="medium">
              {title}
            </Text>
            <Text fontSize="2xl" fontWeight="bold">
              {value}
            </Text>
            
            {change !== undefined && (
              <HStack spacing={1}>
                <Icon 
                  as={change >= 0 ? FiTrendingUp : FiTrendingDown} 
                  color={change >= 0 ? 'green.500' : 'red.500'}
                  size={16}
                />
                <Text fontSize="sm" color={change >= 0 ? 'green.500' : 'red.500'}>
                  {Math.abs(change)}%
                </Text>
                <Text fontSize="sm" color="gray.500">vs last hour</Text>
              </HStack>
            )}
            
            {prediction !== undefined && (
              <VStack align="start" spacing={1} w="full">
                <Text fontSize="xs" color="gray.500">
                  Predicted: {prediction}
                </Text>
                {confidence && (
                  <Progress
                    value={confidence * 100}
                    size="sm"
                    colorScheme={confidence > 0.8 ? 'green' : confidence > 0.6 ? 'yellow' : 'red'}
                  />
                )}
              </VStack>
            )}
          </VStack>
        </VStack>
      </CardBody>
    </Card>
  );
};

// AI Insights Panel
const AIInsightsPanel: React.FC = () => {
  const { insights, generateInsights, dismissInsight, insightGeneration } = useAdvancedAnalyticsStore();
  
  return (
    <Card>
      <CardHeader>
        <HStack justify="space-between">
          <VStack align="start" spacing={1}>
            <Text fontWeight="semibold">AI-Powered Insights</Text>
            <Text fontSize="sm" color="gray.500">
              Real-time analysis and recommendations
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
        <VStack spacing={4} align="stretch">
          {insights.slice(0, 3).map((insight) => (
            <Alert
              key={insight.id}
              status={insight.impact === 'high' ? 'error' : insight.impact === 'medium' ? 'warning' : 'info'}
              borderRadius="md"
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
                  <Badge size="sm" colorScheme={insight.impact === 'high' ? 'red' : 'orange'}>
                    {insight.impact} impact
                  </Badge>
                </HStack>
              </Box>
              <IconButton
                aria-label="Dismiss insight"
                icon={<FiCheckCircle />}
                size="sm"
                variant="ghost"
                onClick={() => dismissInsight(insight.id)}
              />
            </Alert>
          ))}
          
          {insights.length === 0 && (
            <Text fontSize="sm" color="gray.500" textAlign="center" py={4}>
              No insights available. Click "Generate" to analyze current data.
            </Text>
          )}
        </VStack>
      </CardBody>
    </Card>
  );
};

// Main Dashboard Component
const RealTimeAnalyticsDashboard: React.FC = () => {
  const [timeRange, setTimeRange] = useState('1h');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(5);
  const [selectedModel, setSelectedModel] = useState<string>('');
  
  const { isOpen: isSettingsOpen, onOpen: onSettingsOpen, onClose: onSettingsClose } = useDisclosure();
  
  const {
    realTimeData,
    models,
    fetchHistoricalData,
    trainModel,
    modelTraining,
    isLoading,
  } = useAdvancedAnalyticsStore();
  
  const {
    liveCalls,
    liveAgents,
    systemAlerts,
    connectionStatus,
  } = useRealtimeStore();
  
  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  
  // Auto-refresh effect
  useEffect(() => {
    if (!autoRefresh) return;
    
    const interval = setInterval(() => {
      fetchHistoricalData(timeRange, 'minute');
    }, refreshInterval * 1000);
    
    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, timeRange, fetchHistoricalData]);
  
  // Real-time metrics calculations
  const realtimeMetrics = useMemo(() => {
    if (!realTimeData) return null;
    
    const totalCalls = liveCalls.length;
    const activeCalls = liveCalls.filter(call => call.status === 'connected').length;
    const availableAgents = liveAgents.filter(agent => agent.status === 'available').length;
    const busyAgents = liveAgents.filter(agent => agent.status === 'busy').length;
    const avgSentiment = realTimeData.sentimentTrends.slice(-1)[0]?.compound || 0;
    
    return {
      totalCalls,
      activeCalls,
      availableAgents,
      busyAgents,
      avgSentiment,
      conversionRate: realTimeData.conversionRate,
      revenuePerHour: realTimeData.revenuePerHour,
      customerSatisfaction: realTimeData.customerSatisfaction,
    };
  }, [realTimeData, liveCalls, liveAgents]);
  
  const handleModelTrain = useCallback(async (modelType: string) => {
    await trainModel(modelType, {
      epochs: 100,
      batchSize: 32,
      learningRate: 0.001,
    });
  }, [trainModel]);
  
  if (!realTimeData || !realtimeMetrics) {
    return (
      <Box p={8} textAlign="center">
        <VStack spacing={4}>
          <FiActivity size={48} />
          <Text fontSize="lg">Loading real-time analytics...</Text>
          <Progress size="lg" isIndeterminate w="300px" />
        </VStack>
      </Box>
    );
  }
  
  return (
    <Box>
      {/* Header */}
      <VStack align="start" spacing={4} mb={6}>
        <HStack justify="space-between" w="full">
          <VStack align="start" spacing={1}>
            <Heading size="lg">Real-Time Analytics Dashboard</Heading>
            <HStack spacing={4}>
              <Badge
                colorScheme={connectionStatus === 'connected' ? 'green' : 'red'}
                variant="subtle"
              >
                {connectionStatus === 'connected' ? 'Live' : 'Disconnected'}
              </Badge>
              <Text fontSize="sm" color="gray.500">
                Last updated: {new Date().toLocaleTimeString()}
              </Text>
            </HStack>
          </VStack>
          
          <HStack spacing={2}>
            <Select
              size="sm"
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              w="100px"
            >
              <option value="1h">1H</option>
              <option value="6h">6H</option>
              <option value="24h">24H</option>
              <option value="7d">7D</option>
            </Select>
            
            <Tooltip label="Auto-refresh">
              <HStack>
                <Switch
                  size="sm"
                  isChecked={autoRefresh}
                  onChange={(e) => setAutoRefresh(e.target.checked)}
                />
                <Text fontSize="sm">{refreshInterval}s</Text>
              </HStack>
            </Tooltip>
            
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
              onClick={() => fetchHistoricalData(timeRange, 'minute')}
              isLoading={isLoading}
            >
              Refresh
            </Button>
          </HStack>
        </HStack>
      </VStack>
      
      {/* Key Metrics */}
      <SimpleGrid columns={{ base: 2, md: 4, lg: 6 }} spacing={4} mb={6}>
        <AdvancedMetricCard
          title="Active Calls"
          value={realtimeMetrics.activeCalls}
          change={12.5}
          trend="up"
          icon={FiPhone}
          color="blue"
          prediction={realtimeMetrics.activeCalls + 3}
          confidence={0.87}
        />
        <AdvancedMetricCard
          title="Available Agents"
          value={realtimeMetrics.availableAgents}
          change={-5.2}
          trend="down"
          icon={FiUsers}
          color="green"
        />
        <AdvancedMetricCard
          title="Conversion Rate"
          value={`${(realtimeMetrics.conversionRate * 100).toFixed(1)}%`}
          change={8.3}
          trend="up"
          icon={FiTarget}
          color="purple"
          prediction={(realtimeMetrics.conversionRate * 100 + 2.1)}
          confidence={0.92}
        />
        <AdvancedMetricCard
          title="Revenue/Hour"
          value={`$${realtimeMetrics.revenuePerHour.toLocaleString()}`}
          change={15.7}
          trend="up"
          icon={FiDollarSign}
          color="orange"
        />
        <AdvancedMetricCard
          title="Avg Sentiment"
          value={realtimeMetrics.avgSentiment.toFixed(2)}
          change={3.1}
          trend="up"
          icon={FiCpu}
          color="pink"
        />
        <AdvancedMetricCard
          title="Customer Satisfaction"
          value={realtimeMetrics.customerSatisfaction.toFixed(1)}
          change={2.8}
          trend="up"
          icon={FiCheckCircle}
          color="teal"
        />
      </SimpleGrid>
      
      {/* Main Analytics Grid */}
      <Grid templateColumns={{ base: '1fr', lg: '2fr 1fr' }} gap={6} mb={6}>
        {/* Performance Overview */}
        <GridItem>
          <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
            <CardHeader>
              <HStack justify="space-between">
                <VStack align="start" spacing={1}>
                  <Text fontWeight="semibold">Performance Overview</Text>
                  <Text fontSize="sm" color="gray.500">
                    Real-time system performance with GPU acceleration
                  </Text>
                </VStack>
                <HStack spacing={2}>
                  <Badge colorScheme="green" variant="subtle">
                    GPU Accelerated
                  </Badge>
                  <IconButton
                    aria-label="Maximize"
                    icon={<FiMaximize2 />}
                    size="xs"
                    variant="ghost"
                  />
                </HStack>
              </HStack>
            </CardHeader>
            <CardBody>
              <Tabs>
                <TabList>
                  <Tab>Calls & Revenue</Tab>
                  <Tab>Sentiment Analysis</Tab>
                  <Tab>Geographic Distribution</Tab>
                </TabList>
                <TabPanels>
                  <TabPanel p={0} pt={4}>
                    <Box h="300px">
                      <ResponsiveContainer width="100%" height="100%">
                        <ComposedChart data={realTimeData.sentimentTrends}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="timestamp" />
                          <YAxis yAxisId="left" />
                          <YAxis yAxisId="right" orientation="right" />
                          <RechartsTooltip />
                          <Bar yAxisId="left" dataKey="positive" fill="#10B981" />
                          <Line
                            yAxisId="right"
                            type="monotone"
                            dataKey="compound"
                            stroke="#3B82F6"
                            strokeWidth={2}
                          />
                        </ComposedChart>
                      </ResponsiveContainer>
                    </Box>
                  </TabPanel>
                  <TabPanel p={0} pt={4}>
                    <SentimentHeatmap />
                  </TabPanel>
                  <TabPanel p={0} pt={4}>
                    <GeographicDistributionMap />
                  </TabPanel>
                </TabPanels>
              </Tabs>
            </CardBody>
          </Card>
        </GridItem>
        
        {/* AI Insights */}
        <GridItem>
          <AIInsightsPanel />
        </GridItem>
      </Grid>
      
      {/* Advanced Analytics Grid */}
      <Grid templateColumns={{ base: '1fr', lg: '1fr 1fr' }} gap={6} mb={6}>
        {/* Predictive Models */}
        <GridItem>
          <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
            <CardHeader>
              <HStack justify="space-between">
                <VStack align="start" spacing={1}>
                  <Text fontWeight="semibold">Predictive Models</Text>
                  <Text fontSize="sm" color="gray.500">
                    GPU-accelerated machine learning models
                  </Text>
                </VStack>
                <HStack spacing={2}>
                  <Select
                    size="sm"
                    value={selectedModel}
                    onChange={(e) => setSelectedModel(e.target.value)}
                    placeholder="Select model"
                  >
                    {models.map((model) => (
                      <option key={model.id} value={model.id}>
                        {model.name}
                      </option>
                    ))}
                  </Select>
                  <Button
                    size="sm"
                    leftIcon={<FiZap />}
                    onClick={() => handleModelTrain('revenue_forecast')}
                    isLoading={modelTraining}
                    colorScheme="purple"
                  >
                    Train
                  </Button>
                </HStack>
              </HStack>
            </CardHeader>
            <CardBody>
              {selectedModel ? (
                <PredictiveModelChart modelId={selectedModel} />
              ) : (
                <VStack spacing={4} py={8}>
                  <FiCpu size={32} />
                  <Text color="gray.500">Select a model to view performance metrics</Text>
                </VStack>
              )}
            </CardBody>
          </Card>
        </GridItem>
        
        {/* Agent Performance */}
        <GridItem>
          <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
            <CardHeader>
              <Text fontWeight="semibold">Agent Performance Analysis</Text>
            </CardHeader>
            <CardBody>
              <AgentPerformanceRadar />
            </CardBody>
          </Card>
        </GridItem>
      </Grid>
      
      {/* Settings Modal */}
      <Modal isOpen={isSettingsOpen} onClose={onSettingsClose}>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Dashboard Settings</ModalHeader>
          <ModalCloseButton />
          <ModalBody pb={6}>
            <VStack spacing={4} align="stretch">
              <Box>
                <Text mb={2} fontWeight="medium">Auto-refresh Interval</Text>
                <Slider
                  value={refreshInterval}
                  onChange={setRefreshInterval}
                  min={1}
                  max={60}
                  step={1}
                >
                  <SliderTrack>
                    <SliderFilledTrack />
                  </SliderTrack>
                  <SliderThumb />
                </Slider>
                <Text fontSize="sm" color="gray.500" mt={1}>
                  {refreshInterval} seconds
                </Text>
              </Box>
              
              <Divider />
              
              <Box>
                <Text mb={2} fontWeight="medium">GPU Acceleration</Text>
                <Switch defaultChecked />
                <Text fontSize="sm" color="gray.500" mt={1}>
                  Enable GPU-accelerated analytics processing
                </Text>
              </Box>
              
              <Box>
                <Text mb={2} fontWeight="medium">Real-time Notifications</Text>
                <Switch defaultChecked />
                <Text fontSize="sm" color="gray.500" mt={1}>
                  Receive alerts for anomalies and insights
                </Text>
              </Box>
            </VStack>
          </ModalBody>
        </ModalContent>
      </Modal>
    </Box>
  );
};

export default RealTimeAnalyticsDashboard;