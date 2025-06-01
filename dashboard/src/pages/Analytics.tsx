import React, { useEffect, useState } from 'react';
import {
  Box,
  Heading,
  Text,
  VStack,
  HStack,
  Button,
  Card,
  CardHeader,
  CardBody,
  SimpleGrid,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  StatArrow,
  Select,
  Flex,
  Spacer,
  useColorModeValue,
  Alert,
  AlertIcon,
  Spinner,
  Badge,
  Progress,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
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
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import {
  FiTrendingUp,
  FiTrendingDown,
  FiPhone,
  FiUsers,
  FiDollarSign,
  FiClock,
  FiRefreshCw,
  FiDownload,
} from 'react-icons/fi';
import { useDashboardStore } from '../stores/dashboardStore';

const Analytics: React.FC = () => {
  const {
    analytics,
    loading,
    error,
    fetchAnalytics,
    clearError,
  } = useDashboardStore();

  const [timeRange, setTimeRange] = useState('7d');
  const [selectedMetric, setSelectedMetric] = useState('calls');

  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');

  useEffect(() => {
    fetchAnalytics(timeRange);
  }, [fetchAnalytics, timeRange]);

  const handleTimeRangeChange = (newTimeRange: string) => {
    setTimeRange(newTimeRange);
  };

  const handleRefresh = () => {
    fetchAnalytics(timeRange);
  };

  // Mock data for demonstration (replace with real analytics data)
  const callVolumeData = analytics?.callVolume || [
    { date: '2024-01-01', calls: 120, successful: 85, failed: 35 },
    { date: '2024-01-02', calls: 135, successful: 98, failed: 37 },
    { date: '2024-01-03', calls: 148, successful: 112, failed: 36 },
    { date: '2024-01-04', calls: 162, successful: 125, failed: 37 },
    { date: '2024-01-05', calls: 178, successful: 142, failed: 36 },
    { date: '2024-01-06', calls: 195, successful: 158, failed: 37 },
    { date: '2024-01-07', calls: 210, successful: 172, failed: 38 },
  ];

  const conversionTrends = analytics?.conversionTrends || [
    { date: '2024-01-01', rate: 70.8 },
    { date: '2024-01-02', rate: 72.6 },
    { date: '2024-01-03', rate: 75.7 },
    { date: '2024-01-04', rate: 77.2 },
    { date: '2024-01-05', rate: 79.8 },
    { date: '2024-01-06', rate: 81.0 },
    { date: '2024-01-07', rate: 81.9 },
  ];

  const campaignPerformance = analytics?.campaignPerformance || [
    { name: 'Holiday Sale', calls: 450, conversions: 342, revenue: 15420 },
    { name: 'Product Launch', calls: 380, conversions: 285, revenue: 12750 },
    { name: 'Customer Retention', calls: 320, conversions: 256, revenue: 9680 },
    { name: 'Lead Generation', calls: 280, conversions: 196, revenue: 7840 },
  ];

  const hourlyDistribution = analytics?.hourlyDistribution || Array.from({ length: 24 }, (_, hour) => ({
    hour,
    calls: Math.floor(Math.random() * 50) + 10,
    successRate: Math.random() * 40 + 60,
  }));

  const geographicData = analytics?.geographicData || [
    { region: 'North America', calls: 1250, successRate: 78.5 },
    { region: 'Europe', calls: 890, successRate: 72.3 },
    { region: 'Asia Pacific', calls: 650, successRate: 68.7 },
    { region: 'Latin America', calls: 420, successRate: 65.2 },
  ];

  const pieChartColors = ['#3182CE', '#38A169', '#D69E2E', '#E53E3E', '#805AD5'];

  // Calculate summary statistics
  const totalCalls = callVolumeData.reduce((sum, day) => sum + day.calls, 0);
  const totalSuccessful = callVolumeData.reduce((sum, day) => sum + day.successful, 0);
  const totalFailed = callVolumeData.reduce((sum, day) => sum + day.failed, 0);
  const avgConversionRate = totalCalls > 0 ? (totalSuccessful / totalCalls) * 100 : 0;
  const totalRevenue = campaignPerformance.reduce((sum, campaign) => sum + campaign.revenue, 0);

  // Calculate trends
  const callsTrend = callVolumeData.length > 1 
    ? ((callVolumeData[callVolumeData.length - 1].calls - callVolumeData[0].calls) / callVolumeData[0].calls) * 100
    : 0;

  const conversionTrend = conversionTrends.length > 1
    ? conversionTrends[conversionTrends.length - 1].rate - conversionTrends[0].rate
    : 0;

  return (
    <Box>
      {/* Error Alert */}
      {error && (
        <Alert status="error" mb={4}>
          <AlertIcon />
          <Box>
            <Text fontWeight="bold">Error loading analytics</Text>
            <Text fontSize="sm">{error}</Text>
          </Box>
          <Spacer />
          <Button size="sm" onClick={clearError}>
            Dismiss
          </Button>
        </Alert>
      )}

      {/* Header */}
      <VStack align="start" spacing={4} mb={8}>
        <HStack justify="space-between" w="full">
          <VStack align="start" spacing={1}>
            <Heading size="lg">Analytics</Heading>
            <Text color="gray.500">
              Comprehensive performance insights and trends
            </Text>
          </VStack>
          <HStack>
            <Select
              value={timeRange}
              onChange={(e) => handleTimeRangeChange(e.target.value)}
              maxW="150px"
            >
              <option value="1d">Last 24 Hours</option>
              <option value="7d">Last 7 Days</option>
              <option value="30d">Last 30 Days</option>
              <option value="90d">Last 90 Days</option>
            </Select>
            <Button
              leftIcon={<FiRefreshCw />}
              variant="outline"
              size="sm"
              onClick={handleRefresh}
              isLoading={loading}
            >
              Refresh
            </Button>
            <Button
              leftIcon={<FiDownload />}
              colorScheme="blue"
              size="sm"
            >
              Export
            </Button>
          </HStack>
        </HStack>
      </VStack>

      {loading ? (
        <Flex justify="center" py={8}>
          <Spinner size="lg" />
        </Flex>
      ) : (
        <>
          {/* Key Metrics */}
          <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={6} mb={8}>
            <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
              <CardBody>
                <Stat>
                  <StatLabel>Total Calls</StatLabel>
                  <StatNumber>{totalCalls.toLocaleString()}</StatNumber>
                  <StatHelpText>
                    <StatArrow type={callsTrend >= 0 ? 'increase' : 'decrease'} />
                    {Math.abs(callsTrend).toFixed(1)}% from last period
                  </StatHelpText>
                </Stat>
              </CardBody>
            </Card>

            <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
              <CardBody>
                <Stat>
                  <StatLabel>Conversion Rate</StatLabel>
                  <StatNumber>{avgConversionRate.toFixed(1)}%</StatNumber>
                  <StatHelpText>
                    <StatArrow type={conversionTrend >= 0 ? 'increase' : 'decrease'} />
                    {Math.abs(conversionTrend).toFixed(1)}% from last period
                  </StatHelpText>
                </Stat>
              </CardBody>
            </Card>

            <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
              <CardBody>
                <Stat>
                  <StatLabel>Total Revenue</StatLabel>
                  <StatNumber>${totalRevenue.toLocaleString()}</StatNumber>
                  <StatHelpText>
                    <StatArrow type="increase" />
                    12.5% from last period
                  </StatHelpText>
                </Stat>
              </CardBody>
            </Card>

            <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
              <CardBody>
                <Stat>
                  <StatLabel>Success Rate</StatLabel>
                  <StatNumber>{((totalSuccessful / totalCalls) * 100).toFixed(1)}%</StatNumber>
                  <StatHelpText>
                    {totalSuccessful.toLocaleString()} successful calls
                  </StatHelpText>
                </Stat>
              </CardBody>
            </Card>
          </SimpleGrid>

          {/* Charts */}
          <Tabs variant="enclosed" mb={8}>
            <TabList>
              <Tab>Call Volume</Tab>
              <Tab>Conversion Trends</Tab>
              <Tab>Campaign Performance</Tab>
              <Tab>Geographic Analysis</Tab>
            </TabList>

            <TabPanels>
              {/* Call Volume Chart */}
              <TabPanel>
                <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
                  <CardHeader>
                    <Heading size="md">Call Volume Over Time</Heading>
                  </CardHeader>
                  <CardBody>
                    <ResponsiveContainer width="100%" height={400}>
                      <AreaChart data={callVolumeData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="date" />
                        <YAxis />
                        <Tooltip />
                        <Legend />
                        <Area
                          type="monotone"
                          dataKey="calls"
                          stackId="1"
                          stroke="#3182CE"
                          fill="#3182CE"
                          fillOpacity={0.6}
                          name="Total Calls"
                        />
                        <Area
                          type="monotone"
                          dataKey="successful"
                          stackId="2"
                          stroke="#38A169"
                          fill="#38A169"
                          fillOpacity={0.6}
                          name="Successful"
                        />
                        <Area
                          type="monotone"
                          dataKey="failed"
                          stackId="3"
                          stroke="#E53E3E"
                          fill="#E53E3E"
                          fillOpacity={0.6}
                          name="Failed"
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  </CardBody>
                </Card>
              </TabPanel>

              {/* Conversion Trends Chart */}
              <TabPanel>
                <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
                  <CardHeader>
                    <Heading size="md">Conversion Rate Trends</Heading>
                  </CardHeader>
                  <CardBody>
                    <ResponsiveContainer width="100%" height={400}>
                      <LineChart data={conversionTrends}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="date" />
                        <YAxis domain={['dataMin - 5', 'dataMax + 5']} />
                        <Tooltip formatter={(value) => [`${value}%`, 'Conversion Rate']} />
                        <Line
                          type="monotone"
                          dataKey="rate"
                          stroke="#3182CE"
                          strokeWidth={3}
                          dot={{ fill: '#3182CE', strokeWidth: 2, r: 6 }}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </CardBody>
                </Card>
              </TabPanel>

              {/* Campaign Performance Chart */}
              <TabPanel>
                <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
                  <CardHeader>
                    <Heading size="md">Campaign Performance</Heading>
                  </CardHeader>
                  <CardBody>
                    <ResponsiveContainer width="100%" height={400}>
                      <BarChart data={campaignPerformance}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="name" />
                        <YAxis />
                        <Tooltip />
                        <Legend />
                        <Bar dataKey="calls" fill="#3182CE" name="Total Calls" />
                        <Bar dataKey="conversions" fill="#38A169" name="Conversions" />
                      </BarChart>
                    </ResponsiveContainer>
                  </CardBody>
                </Card>
              </TabPanel>

              {/* Geographic Analysis */}
              <TabPanel>
                <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={6}>
                  <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
                    <CardHeader>
                      <Heading size="md">Calls by Region</Heading>
                    </CardHeader>
                    <CardBody>
                      <ResponsiveContainer width="100%" height={300}>
                        <PieChart>
                          <Pie
                            data={geographicData}
                            cx="50%"
                            cy="50%"
                            labelLine={false}
                            label={({ region, calls }) => `${region}: ${calls}`}
                            outerRadius={80}
                            fill="#8884d8"
                            dataKey="calls"
                          >
                            {geographicData.map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={pieChartColors[index % pieChartColors.length]} />
                            ))}
                          </Pie>
                          <Tooltip />
                        </PieChart>
                      </ResponsiveContainer>
                    </CardBody>
                  </Card>

                  <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
                    <CardHeader>
                      <Heading size="md">Regional Performance</Heading>
                    </CardHeader>
                    <CardBody>
                      <Table variant="simple">
                        <Thead>
                          <Tr>
                            <Th>Region</Th>
                            <Th>Calls</Th>
                            <Th>Success Rate</Th>
                          </Tr>
                        </Thead>
                        <Tbody>
                          {geographicData.map((region, index) => (
                            <Tr key={region.region}>
                              <Td>
                                <HStack>
                                  <Box
                                    w={3}
                                    h={3}
                                    borderRadius="full"
                                    bg={pieChartColors[index % pieChartColors.length]}
                                  />
                                  <Text>{region.region}</Text>
                                </HStack>
                              </Td>
                              <Td>{region.calls.toLocaleString()}</Td>
                              <Td>
                                <HStack>
                                  <Progress
                                    value={region.successRate}
                                    size="sm"
                                    colorScheme="green"
                                    w="60px"
                                  />
                                  <Text fontSize="sm">{region.successRate.toFixed(1)}%</Text>
                                </HStack>
                              </Td>
                            </Tr>
                          ))}
                        </Tbody>
                      </Table>
                    </CardBody>
                  </Card>
                </SimpleGrid>
              </TabPanel>
            </TabPanels>
          </Tabs>

          {/* Hourly Distribution */}
          <Card bg={cardBg} borderColor={borderColor} borderWidth="1px" mb={8}>
            <CardHeader>
              <Heading size="md">Hourly Call Distribution</Heading>
            </CardHeader>
            <CardBody>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={hourlyDistribution}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="hour" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="calls" fill="#3182CE" name="Calls" />
                </BarChart>
              </ResponsiveContainer>
            </CardBody>
          </Card>

          {/* Campaign Performance Table */}
          <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
            <CardHeader>
              <Heading size="md">Detailed Campaign Performance</Heading>
            </CardHeader>
            <CardBody>
              <Table variant="simple">
                <Thead>
                  <Tr>
                    <Th>Campaign</Th>
                    <Th>Total Calls</Th>
                    <Th>Conversions</Th>
                    <Th>Conversion Rate</Th>
                    <Th>Revenue</Th>
                    <Th>ROI</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {campaignPerformance.map((campaign) => {
                    const conversionRate = (campaign.conversions / campaign.calls) * 100;
                    const roi = ((campaign.revenue - (campaign.calls * 5)) / (campaign.calls * 5)) * 100; // Assuming $5 cost per call
                    
                    return (
                      <Tr key={campaign.name}>
                        <Td fontWeight="medium">{campaign.name}</Td>
                        <Td>{campaign.calls.toLocaleString()}</Td>
                        <Td>{campaign.conversions.toLocaleString()}</Td>
                        <Td>
                          <HStack>
                            <Progress
                              value={conversionRate}
                              size="sm"
                              colorScheme="green"
                              w="60px"
                            />
                            <Text fontSize="sm">{conversionRate.toFixed(1)}%</Text>
                          </HStack>
                        </Td>
                        <Td>${campaign.revenue.toLocaleString()}</Td>
                        <Td>
                          <Badge colorScheme={roi > 0 ? 'green' : 'red'}>
                            {roi > 0 ? '+' : ''}{roi.toFixed(1)}%
                          </Badge>
                        </Td>
                      </Tr>
                    );
                  })}
                </Tbody>
              </Table>
            </CardBody>
          </Card>
        </>
      )}
    </Box>
  );
};

export default Analytics;