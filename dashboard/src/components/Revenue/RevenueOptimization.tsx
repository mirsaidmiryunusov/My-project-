/**
 * Revenue Optimization Dashboard for Project GeminiVoiceConnect
 * 
 * This component provides comprehensive revenue optimization capabilities with
 * GPU-accelerated ML algorithms for customer lifetime value prediction, dynamic
 * pricing optimization, upselling opportunities, and churn prevention analytics.
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
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  TableContainer,
  Progress,
  useColorModeValue,
  Flex,
  Tooltip,
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
  Alert,
  AlertIcon,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  StatArrow,
  CircularProgress,
  CircularProgressLabel,
  SimpleGrid,
  Divider,
  Select,
  Input,
  InputGroup,
  InputLeftElement,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  NumberIncrementStepper,
  NumberDecrementStepper,
  Switch,
  FormControl,
  FormLabel,
  Slider,
  SliderTrack,
  SliderFilledTrack,
  SliderThumb,
} from '@chakra-ui/react';
import {
  FiDollarSign,
  FiTrendingUp,
  FiTrendingDown,
  FiTarget,
  FiUsers,
  FiShield,
  FiZap,
  FiBarChart,
  FiPieChart,
  FiActivity,
  FiRefreshCw,
  FiSettings,
  FiAlertTriangle,
  FiCheckCircle,
  FiClock,
  FiArrowUp,
  FiArrowDown,
  FiMaximize2,
  FiFilter,
  FiSearch,
  FiDownload,
  FiPlay,
  FiPause,
} from 'react-icons/fi';
import { Line, Bar, Doughnut, Scatter } from 'react-chartjs-2';

interface RevenueOpportunity {
  id: string;
  customerId: string;
  customerName: string;
  type: 'upsell' | 'cross-sell' | 'retention' | 'pricing';
  currentValue: number;
  potentialValue: number;
  upliftPercentage: number;
  confidence: number;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  estimatedROI: number;
  implementationTime: string;
  riskLevel: 'low' | 'medium' | 'high';
  description: string;
  aiRecommendation: string;
}

interface CustomerSegment {
  id: string;
  name: string;
  customerCount: number;
  averageCLV: number;
  churnRate: number;
  revenueContribution: number;
  growthRate: number;
  characteristics: string[];
}

interface PricingRecommendation {
  productId: string;
  productName: string;
  currentPrice: number;
  recommendedPrice: number;
  priceChange: number;
  expectedDemandChange: number;
  revenueImpact: number;
  confidence: number;
  marketFactors: string[];
}

const RevenueOptimization: React.FC = () => {
  const [opportunities, setOpportunities] = useState<RevenueOpportunity[]>([]);
  const [customerSegments, setCustomerSegments] = useState<CustomerSegment[]>([]);
  const [pricingRecommendations, setPricingRecommendations] = useState<PricingRecommendation[]>([]);
  const [selectedOpportunity, setSelectedOpportunity] = useState<RevenueOpportunity | null>(null);
  const [activeTab, setActiveTab] = useState(0);
  const [autoOptimization, setAutoOptimization] = useState(false);
  const [optimizationRunning, setOptimizationRunning] = useState(false);
  const [lastOptimization, setLastOptimization] = useState(new Date());

  const { isOpen: isOpportunityDetailOpen, onOpen: onOpportunityDetailOpen, onClose: onOpportunityDetailClose } = useDisclosure();

  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  const textColor = useColorModeValue('gray.700', 'gray.200');

  // Mock data - would come from GPU-accelerated ML models
  useEffect(() => {
    const mockOpportunities: RevenueOpportunity[] = [
      {
        id: 'opp_001',
        customerId: 'cust_123',
        customerName: 'Acme Corporation',
        type: 'upsell',
        currentValue: 2500,
        potentialValue: 3750,
        upliftPercentage: 50,
        confidence: 0.89,
        priority: 'high',
        estimatedROI: 450,
        implementationTime: '2-3 weeks',
        riskLevel: 'low',
        description: 'Premium service upgrade opportunity',
        aiRecommendation: 'Customer shows high engagement with current service and has budget capacity for premium features.',
      },
      {
        id: 'opp_002',
        customerId: 'cust_456',
        customerName: 'TechStart Inc',
        type: 'cross-sell',
        currentValue: 1200,
        potentialValue: 1800,
        upliftPercentage: 50,
        confidence: 0.76,
        priority: 'medium',
        estimatedROI: 320,
        implementationTime: '1-2 weeks',
        riskLevel: 'medium',
        description: 'SMS marketing add-on opportunity',
        aiRecommendation: 'Customer has shown interest in multi-channel marketing. SMS addition would complement their current call campaigns.',
      },
      {
        id: 'opp_003',
        customerId: 'cust_789',
        customerName: 'Global Retail Co',
        type: 'retention',
        currentValue: 5000,
        potentialValue: 5000,
        upliftPercentage: 0,
        confidence: 0.92,
        priority: 'urgent',
        estimatedROI: 4200,
        implementationTime: 'Immediate',
        riskLevel: 'high',
        description: 'Churn prevention - high-value customer at risk',
        aiRecommendation: 'Customer satisfaction scores declining. Immediate intervention with personalized retention offer recommended.',
      },
    ];

    const mockSegments: CustomerSegment[] = [
      {
        id: 'seg_enterprise',
        name: 'Enterprise',
        customerCount: 45,
        averageCLV: 15000,
        churnRate: 5.2,
        revenueContribution: 65,
        growthRate: 12.5,
        characteristics: ['High volume', 'Long contracts', 'Multiple services'],
      },
      {
        id: 'seg_smb',
        name: 'Small-Medium Business',
        customerCount: 234,
        averageCLV: 3500,
        churnRate: 12.8,
        revenueContribution: 28,
        growthRate: 8.3,
        characteristics: ['Price sensitive', 'Quick decisions', 'Growth potential'],
      },
      {
        id: 'seg_startup',
        name: 'Startups',
        customerCount: 156,
        averageCLV: 1200,
        churnRate: 22.1,
        revenueContribution: 7,
        growthRate: 25.7,
        characteristics: ['Budget constraints', 'High growth', 'Tech-savvy'],
      },
    ];

    const mockPricing: PricingRecommendation[] = [
      {
        productId: 'prod_basic',
        productName: 'Basic Call Package',
        currentPrice: 99,
        recommendedPrice: 109,
        priceChange: 10.1,
        expectedDemandChange: -3.2,
        revenueImpact: 6.8,
        confidence: 0.84,
        marketFactors: ['Competitor pricing', 'Demand elasticity', 'Customer feedback'],
      },
      {
        productId: 'prod_premium',
        productName: 'Premium AI Package',
        currentPrice: 299,
        recommendedPrice: 279,
        priceChange: -6.7,
        expectedDemandChange: 12.5,
        revenueImpact: 4.2,
        confidence: 0.91,
        marketFactors: ['Market penetration', 'Feature adoption', 'Competitive pressure'],
      },
    ];

    setOpportunities(mockOpportunities);
    setCustomerSegments(mockSegments);
    setPricingRecommendations(mockPricing);
  }, []);

  const totalPotentialRevenue = opportunities.reduce((sum, opp) => sum + (opp.potentialValue - opp.currentValue), 0);
  const averageConfidence = opportunities.length > 0 
    ? opportunities.reduce((sum, opp) => sum + opp.confidence, 0) / opportunities.length 
    : 0;
  const highPriorityOpportunities = opportunities.filter(opp => opp.priority === 'high' || opp.priority === 'urgent').length;

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent': return 'red';
      case 'high': return 'orange';
      case 'medium': return 'yellow';
      case 'low': return 'green';
      default: return 'gray';
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'upsell': return 'blue';
      case 'cross-sell': return 'purple';
      case 'retention': return 'red';
      case 'pricing': return 'green';
      default: return 'gray';
    }
  };

  const handleRunOptimization = async () => {
    setOptimizationRunning(true);
    // Simulate GPU-accelerated ML optimization
    setTimeout(() => {
      setOptimizationRunning(false);
      setLastOptimization(new Date());
    }, 3000);
  };

  const handleImplementOpportunity = (opportunityId: string) => {
    console.log(`Implementing opportunity: ${opportunityId}`);
    // Implementation logic here
  };

  // Chart data
  const revenueProjectionData = {
    labels: ['Current', 'Month 1', 'Month 2', 'Month 3', 'Month 6', 'Month 12'],
    datasets: [
      {
        label: 'Current Trajectory',
        data: [100000, 102000, 104000, 106000, 112000, 124000],
        borderColor: 'rgb(156, 163, 175)',
        backgroundColor: 'rgba(156, 163, 175, 0.1)',
        borderDash: [5, 5],
      },
      {
        label: 'Optimized Trajectory',
        data: [100000, 108000, 116000, 125000, 145000, 175000],
        borderColor: 'rgb(34, 197, 94)',
        backgroundColor: 'rgba(34, 197, 94, 0.1)',
      },
    ],
  };

  const segmentRevenueData = {
    labels: customerSegments.map(seg => seg.name),
    datasets: [
      {
        label: 'Revenue Contribution (%)',
        data: customerSegments.map(seg => seg.revenueContribution),
        backgroundColor: [
          'rgba(59, 130, 246, 0.8)',
          'rgba(16, 185, 129, 0.8)',
          'rgba(245, 158, 11, 0.8)',
        ],
      },
    ],
  };

  const clvVsChurnData = {
    datasets: [
      {
        label: 'Customer Segments',
        data: customerSegments.map(seg => ({
          x: seg.churnRate,
          y: seg.averageCLV,
          r: Math.sqrt(seg.customerCount) * 2,
        })),
        backgroundColor: [
          'rgba(59, 130, 246, 0.6)',
          'rgba(16, 185, 129, 0.6)',
          'rgba(245, 158, 11, 0.6)',
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
            Revenue Optimization
          </Heading>
          <Text color="gray.500" fontSize="sm">
            AI-powered revenue optimization with GPU-accelerated analytics
          </Text>
        </VStack>
        
        <HStack spacing={3}>
          <FormControl display="flex" alignItems="center">
            <FormLabel htmlFor="auto-optimization" mb="0" fontSize="sm">
              Auto-optimization
            </FormLabel>
            <Switch
              id="auto-optimization"
              isChecked={autoOptimization}
              onChange={(e) => setAutoOptimization(e.target.checked)}
            />
          </FormControl>
          
          <Button
            colorScheme="blue"
            leftIcon={<FiZap />}
            onClick={handleRunOptimization}
            isLoading={optimizationRunning}
            loadingText="Optimizing..."
          >
            Run Optimization
          </Button>
        </HStack>
      </Flex>

      {/* Key Metrics */}
      <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={6} mb={8}>
        <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
          <CardBody>
            <Stat>
              <StatLabel>Potential Revenue Uplift</StatLabel>
              <StatNumber color="green.500">
                ${totalPotentialRevenue.toLocaleString()}
              </StatNumber>
              <StatHelpText>
                <StatArrow type="increase" />
                Next 12 months
              </StatHelpText>
            </Stat>
          </CardBody>
        </Card>

        <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
          <CardBody>
            <Stat>
              <StatLabel>AI Confidence Score</StatLabel>
              <StatNumber color="blue.500">
                {Math.round(averageConfidence * 100)}%
              </StatNumber>
              <StatHelpText>
                <Icon as={FiZap} mr={1} />
                GPU-accelerated ML
              </StatHelpText>
            </Stat>
          </CardBody>
        </Card>

        <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
          <CardBody>
            <Stat>
              <StatLabel>High Priority Opportunities</StatLabel>
              <StatNumber color="orange.500">
                {highPriorityOpportunities}
              </StatNumber>
              <StatHelpText>
                <Icon as={FiTarget} mr={1} />
                Immediate action
              </StatHelpText>
            </Stat>
          </CardBody>
        </Card>

        <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
          <CardBody>
            <Stat>
              <StatLabel>Last Optimization</StatLabel>
              <StatNumber color="purple.500" fontSize="lg">
                {lastOptimization.toLocaleTimeString()}
              </StatNumber>
              <StatHelpText>
                <Icon as={FiClock} mr={1} />
                {autoOptimization ? 'Auto-enabled' : 'Manual'}
              </StatHelpText>
            </Stat>
          </CardBody>
        </Card>
      </SimpleGrid>

      {/* Main Content Tabs */}
      <Tabs index={activeTab} onChange={setActiveTab}>
        <TabList>
          <Tab>Revenue Opportunities</Tab>
          <Tab>Customer Segments</Tab>
          <Tab>Pricing Optimization</Tab>
          <Tab>Predictive Analytics</Tab>
        </TabList>

        <TabPanels>
          {/* Revenue Opportunities Tab */}
          <TabPanel>
            <Grid templateColumns={{ base: '1fr', lg: '2fr 1fr' }} gap={6}>
              {/* Opportunities Table */}
              <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
                <CardHeader>
                  <HStack justify="space-between">
                    <Heading size="md">Revenue Opportunities</Heading>
                    <HStack>
                      <Button size="sm" leftIcon={<FiFilter />} variant="outline">
                        Filter
                      </Button>
                      <Button size="sm" leftIcon={<FiDownload />} variant="outline">
                        Export
                      </Button>
                    </HStack>
                  </HStack>
                </CardHeader>
                <CardBody>
                  <TableContainer>
                    <Table variant="simple" size="sm">
                      <Thead>
                        <Tr>
                          <Th>Customer</Th>
                          <Th>Type</Th>
                          <Th>Current Value</Th>
                          <Th>Potential</Th>
                          <Th>Uplift</Th>
                          <Th>Confidence</Th>
                          <Th>Priority</Th>
                          <Th>Actions</Th>
                        </Tr>
                      </Thead>
                      <Tbody>
                        {opportunities.map((opp) => (
                          <Tr key={opp.id}>
                            <Td>
                              <VStack align="start" spacing={1}>
                                <Text fontSize="sm" fontWeight="medium">
                                  {opp.customerName}
                                </Text>
                                <Text fontSize="xs" color="gray.500">
                                  {opp.customerId}
                                </Text>
                              </VStack>
                            </Td>
                            <Td>
                              <Badge colorScheme={getTypeColor(opp.type)} size="sm">
                                {opp.type}
                              </Badge>
                            </Td>
                            <Td>${opp.currentValue.toLocaleString()}</Td>
                            <Td>${opp.potentialValue.toLocaleString()}</Td>
                            <Td>
                              <HStack>
                                <Icon as={FiArrowUp} color="green.500" boxSize={3} />
                                <Text color="green.500" fontSize="sm" fontWeight="medium">
                                  {opp.upliftPercentage}%
                                </Text>
                              </HStack>
                            </Td>
                            <Td>
                              <HStack>
                                <Progress
                                  value={opp.confidence * 100}
                                  size="sm"
                                  colorScheme="blue"
                                  w="50px"
                                />
                                <Text fontSize="xs">
                                  {Math.round(opp.confidence * 100)}%
                                </Text>
                              </HStack>
                            </Td>
                            <Td>
                              <Badge colorScheme={getPriorityColor(opp.priority)} size="sm">
                                {opp.priority}
                              </Badge>
                            </Td>
                            <Td>
                              <HStack spacing={1}>
                                <Tooltip label="View Details">
                                  <IconButton
                                    aria-label="View details"
                                    icon={<FiMaximize2 />}
                                    size="xs"
                                    variant="ghost"
                                    onClick={() => {
                                      setSelectedOpportunity(opp);
                                      onOpportunityDetailOpen();
                                    }}
                                  />
                                </Tooltip>
                                <Tooltip label="Implement">
                                  <IconButton
                                    aria-label="Implement"
                                    icon={<FiPlay />}
                                    size="xs"
                                    variant="ghost"
                                    colorScheme="green"
                                    onClick={() => handleImplementOpportunity(opp.id)}
                                  />
                                </Tooltip>
                              </HStack>
                            </Td>
                          </Tr>
                        ))}
                      </Tbody>
                    </Table>
                  </TableContainer>
                </CardBody>
              </Card>

              {/* Revenue Projection Chart */}
              <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
                <CardHeader>
                  <Heading size="md">Revenue Projection</Heading>
                  <Text color="gray.500" fontSize="sm">
                    Current vs Optimized trajectory
                  </Text>
                </CardHeader>
                <CardBody>
                  <Box h="400px">
                    <Line data={revenueProjectionData} options={chartOptions} />
                  </Box>
                </CardBody>
              </Card>
            </Grid>
          </TabPanel>

          {/* Customer Segments Tab */}
          <TabPanel>
            <Grid templateColumns={{ base: '1fr', lg: '1fr 1fr' }} gap={6}>
              {/* Segment Analysis */}
              <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
                <CardHeader>
                  <Heading size="md">Customer Segments</Heading>
                </CardHeader>
                <CardBody>
                  <VStack spacing={4} align="stretch">
                    {customerSegments.map((segment) => (
                      <Box key={segment.id} p={4} borderWidth="1px" borderRadius="md">
                        <HStack justify="space-between" mb={3}>
                          <VStack align="start" spacing={1}>
                            <Text fontWeight="bold">{segment.name}</Text>
                            <Text fontSize="sm" color="gray.500">
                              {segment.customerCount} customers
                            </Text>
                          </VStack>
                          <VStack align="end" spacing={1}>
                            <Text fontWeight="bold" color="green.500">
                              ${segment.averageCLV.toLocaleString()}
                            </Text>
                            <Text fontSize="sm" color="gray.500">
                              Avg CLV
                            </Text>
                          </VStack>
                        </HStack>
                        
                        <SimpleGrid columns={3} spacing={4} mb={3}>
                          <Box>
                            <Text fontSize="xs" color="gray.500">Churn Rate</Text>
                            <Text fontSize="sm" fontWeight="medium" color="red.500">
                              {segment.churnRate}%
                            </Text>
                          </Box>
                          <Box>
                            <Text fontSize="xs" color="gray.500">Revenue Share</Text>
                            <Text fontSize="sm" fontWeight="medium" color="blue.500">
                              {segment.revenueContribution}%
                            </Text>
                          </Box>
                          <Box>
                            <Text fontSize="xs" color="gray.500">Growth Rate</Text>
                            <Text fontSize="sm" fontWeight="medium" color="green.500">
                              {segment.growthRate}%
                            </Text>
                          </Box>
                        </SimpleGrid>
                        
                        <HStack wrap="wrap">
                          {segment.characteristics.map((char, index) => (
                            <Badge key={index} size="sm" variant="outline">
                              {char}
                            </Badge>
                          ))}
                        </HStack>
                      </Box>
                    ))}
                  </VStack>
                </CardBody>
              </Card>

              {/* CLV vs Churn Analysis */}
              <VStack spacing={6}>
                <Card bg={cardBg} borderColor={borderColor} borderWidth="1px" w="full">
                  <CardHeader>
                    <Heading size="md">Revenue Distribution</Heading>
                  </CardHeader>
                  <CardBody>
                    <Box h="250px">
                      <Doughnut data={segmentRevenueData} options={chartOptions} />
                    </Box>
                  </CardBody>
                </Card>

                <Card bg={cardBg} borderColor={borderColor} borderWidth="1px" w="full">
                  <CardHeader>
                    <Heading size="md">CLV vs Churn Rate</Heading>
                    <Text fontSize="sm" color="gray.500">
                      Bubble size = customer count
                    </Text>
                  </CardHeader>
                  <CardBody>
                    <Box h="250px">
                      <Scatter
                        data={clvVsChurnData}
                        options={{
                          ...chartOptions,
                          scales: {
                            x: {
                              title: {
                                display: true,
                                text: 'Churn Rate (%)',
                              },
                            },
                            y: {
                              title: {
                                display: true,
                                text: 'Average CLV ($)',
                              },
                            },
                          },
                        }}
                      />
                    </Box>
                  </CardBody>
                </Card>
              </VStack>
            </Grid>
          </TabPanel>

          {/* Pricing Optimization Tab */}
          <TabPanel>
            <VStack spacing={6} align="stretch">
              {pricingRecommendations.map((pricing) => (
                <Card key={pricing.productId} bg={cardBg} borderColor={borderColor} borderWidth="1px">
                  <CardBody>
                    <Grid templateColumns={{ base: '1fr', lg: '2fr 1fr 1fr' }} gap={6}>
                      <VStack align="start" spacing={3}>
                        <Heading size="md">{pricing.productName}</Heading>
                        <HStack>
                          <Text fontSize="sm" color="gray.500">Current Price:</Text>
                          <Text fontSize="lg" fontWeight="bold">${pricing.currentPrice}</Text>
                        </HStack>
                        <HStack>
                          <Text fontSize="sm" color="gray.500">Recommended:</Text>
                          <Text fontSize="lg" fontWeight="bold" color="green.500">
                            ${pricing.recommendedPrice}
                          </Text>
                          <Badge colorScheme={pricing.priceChange > 0 ? 'green' : 'red'}>
                            {pricing.priceChange > 0 ? '+' : ''}{pricing.priceChange.toFixed(1)}%
                          </Badge>
                        </HStack>
                        <VStack align="start" spacing={1}>
                          <Text fontSize="sm" color="gray.500">Market Factors:</Text>
                          <HStack wrap="wrap">
                            {pricing.marketFactors.map((factor, index) => (
                              <Badge key={index} size="sm" variant="outline">
                                {factor}
                              </Badge>
                            ))}
                          </HStack>
                        </VStack>
                      </VStack>

                      <VStack spacing={4}>
                        <Box w="full">
                          <Text fontSize="sm" color="gray.500" mb={2}>Expected Demand Change</Text>
                          <HStack>
                            <Progress
                              value={Math.abs(pricing.expectedDemandChange)}
                              colorScheme={pricing.expectedDemandChange > 0 ? 'green' : 'red'}
                              size="lg"
                              flex={1}
                            />
                            <Text fontSize="sm" fontWeight="medium">
                              {pricing.expectedDemandChange > 0 ? '+' : ''}{pricing.expectedDemandChange}%
                            </Text>
                          </HStack>
                        </Box>

                        <Box w="full">
                          <Text fontSize="sm" color="gray.500" mb={2}>Revenue Impact</Text>
                          <HStack>
                            <Progress
                              value={pricing.revenueImpact}
                              colorScheme="blue"
                              size="lg"
                              flex={1}
                            />
                            <Text fontSize="sm" fontWeight="medium" color="blue.500">
                              +{pricing.revenueImpact}%
                            </Text>
                          </HStack>
                        </Box>

                        <Box w="full">
                          <Text fontSize="sm" color="gray.500" mb={2}>AI Confidence</Text>
                          <HStack>
                            <Progress
                              value={pricing.confidence * 100}
                              colorScheme="purple"
                              size="lg"
                              flex={1}
                            />
                            <Text fontSize="sm" fontWeight="medium">
                              {Math.round(pricing.confidence * 100)}%
                            </Text>
                          </HStack>
                        </Box>
                      </VStack>

                      <VStack spacing={3}>
                        <Button colorScheme="green" size="sm" w="full">
                          Apply Recommendation
                        </Button>
                        <Button variant="outline" size="sm" w="full">
                          Simulate Impact
                        </Button>
                        <Button variant="ghost" size="sm" w="full">
                          View Details
                        </Button>
                      </VStack>
                    </Grid>
                  </CardBody>
                </Card>
              ))}
            </VStack>
          </TabPanel>

          {/* Predictive Analytics Tab */}
          <TabPanel>
            <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={6}>
              <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
                <CardHeader>
                  <Heading size="md">Churn Prediction Model</Heading>
                  <Text fontSize="sm" color="gray.500">
                    GPU-accelerated ML model performance
                  </Text>
                </CardHeader>
                <CardBody>
                  <VStack spacing={4}>
                    <HStack justify="space-between" w="full">
                      <Text fontSize="sm">Model Accuracy</Text>
                      <Text fontSize="sm" fontWeight="bold" color="green.500">94.2%</Text>
                    </HStack>
                    <Progress value={94.2} colorScheme="green" size="lg" w="full" />
                    
                    <HStack justify="space-between" w="full">
                      <Text fontSize="sm">Precision</Text>
                      <Text fontSize="sm" fontWeight="bold" color="blue.500">91.8%</Text>
                    </HStack>
                    <Progress value={91.8} colorScheme="blue" size="lg" w="full" />
                    
                    <HStack justify="space-between" w="full">
                      <Text fontSize="sm">Recall</Text>
                      <Text fontSize="sm" fontWeight="bold" color="purple.500">89.5%</Text>
                    </HStack>
                    <Progress value={89.5} colorScheme="purple" size="lg" w="full" />
                    
                    <Divider />
                    
                    <VStack align="start" spacing={2} w="full">
                      <Text fontSize="sm" fontWeight="medium">Key Predictive Features:</Text>
                      <VStack align="start" spacing={1} pl={4}>
                        <Text fontSize="xs">• Customer engagement score (32% importance)</Text>
                        <Text fontSize="xs">• Support ticket frequency (28% importance)</Text>
                        <Text fontSize="xs">• Payment history (24% importance)</Text>
                        <Text fontSize="xs">• Feature usage patterns (16% importance)</Text>
                      </VStack>
                    </VStack>
                  </VStack>
                </CardBody>
              </Card>

              <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
                <CardHeader>
                  <Heading size="md">Revenue Forecasting</Heading>
                  <Text fontSize="sm" color="gray.500">
                    12-month revenue prediction
                  </Text>
                </CardHeader>
                <CardBody>
                  <VStack spacing={4}>
                    <HStack justify="space-between" w="full">
                      <Text fontSize="sm">Forecast Confidence</Text>
                      <Text fontSize="sm" fontWeight="bold" color="green.500">87.3%</Text>
                    </HStack>
                    <Progress value={87.3} colorScheme="green" size="lg" w="full" />
                    
                    <SimpleGrid columns={2} spacing={4} w="full">
                      <Box textAlign="center">
                        <Text fontSize="xs" color="gray.500">Conservative</Text>
                        <Text fontSize="lg" fontWeight="bold" color="blue.500">$1.2M</Text>
                      </Box>
                      <Box textAlign="center">
                        <Text fontSize="xs" color="gray.500">Optimistic</Text>
                        <Text fontSize="lg" fontWeight="bold" color="green.500">$1.8M</Text>
                      </Box>
                    </SimpleGrid>
                    
                    <Divider />
                    
                    <VStack align="start" spacing={2} w="full">
                      <Text fontSize="sm" fontWeight="medium">Growth Drivers:</Text>
                      <VStack align="start" spacing={1} pl={4}>
                        <Text fontSize="xs">• Customer acquisition (+15%)</Text>
                        <Text fontSize="xs">• Upselling success (+22%)</Text>
                        <Text fontSize="xs">• Churn reduction (-8%)</Text>
                        <Text fontSize="xs">• Price optimization (+5%)</Text>
                      </VStack>
                    </VStack>
                  </VStack>
                </CardBody>
              </Card>
            </SimpleGrid>
          </TabPanel>
        </TabPanels>
      </Tabs>

      {/* Opportunity Detail Modal */}
      <Modal isOpen={isOpportunityDetailOpen} onClose={onOpportunityDetailClose} size="xl">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>
            Revenue Opportunity Details
          </ModalHeader>
          <ModalCloseButton />
          <ModalBody pb={6}>
            {selectedOpportunity && (
              <VStack spacing={6} align="stretch">
                <SimpleGrid columns={2} spacing={4}>
                  <Box>
                    <Text fontSize="sm" color="gray.500">Customer</Text>
                    <Text fontWeight="medium">{selectedOpportunity.customerName}</Text>
                  </Box>
                  <Box>
                    <Text fontSize="sm" color="gray.500">Opportunity Type</Text>
                    <Badge colorScheme={getTypeColor(selectedOpportunity.type)}>
                      {selectedOpportunity.type}
                    </Badge>
                  </Box>
                  <Box>
                    <Text fontSize="sm" color="gray.500">Current Value</Text>
                    <Text fontWeight="medium">${selectedOpportunity.currentValue.toLocaleString()}</Text>
                  </Box>
                  <Box>
                    <Text fontSize="sm" color="gray.500">Potential Value</Text>
                    <Text fontWeight="medium" color="green.500">
                      ${selectedOpportunity.potentialValue.toLocaleString()}
                    </Text>
                  </Box>
                  <Box>
                    <Text fontSize="sm" color="gray.500">Expected ROI</Text>
                    <Text fontWeight="medium" color="blue.500">
                      ${selectedOpportunity.estimatedROI.toLocaleString()}
                    </Text>
                  </Box>
                  <Box>
                    <Text fontSize="sm" color="gray.500">Implementation Time</Text>
                    <Text fontWeight="medium">{selectedOpportunity.implementationTime}</Text>
                  </Box>
                </SimpleGrid>

                <Box>
                  <Text fontSize="sm" color="gray.500" mb={2}>AI Confidence Score</Text>
                  <HStack>
                    <Progress
                      value={selectedOpportunity.confidence * 100}
                      colorScheme="purple"
                      size="lg"
                      flex={1}
                    />
                    <Text fontSize="sm" fontWeight="medium">
                      {Math.round(selectedOpportunity.confidence * 100)}%
                    </Text>
                  </HStack>
                </Box>

                <Box>
                  <Text fontSize="sm" color="gray.500" mb={2}>Description</Text>
                  <Text fontSize="sm">{selectedOpportunity.description}</Text>
                </Box>

                <Box>
                  <Text fontSize="sm" color="gray.500" mb={2}>AI Recommendation</Text>
                  <Alert status="info">
                    <AlertIcon />
                    <Text fontSize="sm">{selectedOpportunity.aiRecommendation}</Text>
                  </Alert>
                </Box>

                <HStack spacing={4}>
                  <Button
                    colorScheme="green"
                    flex={1}
                    onClick={() => handleImplementOpportunity(selectedOpportunity.id)}
                  >
                    Implement Opportunity
                  </Button>
                  <Button variant="outline" flex={1}>
                    Schedule for Later
                  </Button>
                </HStack>
              </VStack>
            )}
          </ModalBody>
        </ModalContent>
      </Modal>
    </Box>
  );
};

export default RevenueOptimization;