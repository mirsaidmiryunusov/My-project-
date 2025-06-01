import React, { useEffect, useState } from 'react';
import {
  Box,
  VStack,
  HStack,
  Text,
  Card,
  CardHeader,
  CardBody,
  Badge,
  Button,
  Progress,
  SimpleGrid,
  Flex,
  Icon,
  useColorModeValue,
  Tooltip,
  Divider,
  Alert,
  AlertIcon,
  Spinner,
  List,
  ListItem,
  ListIcon,
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
} from '@chakra-ui/react';
import {
  FiTrendingUp,
  FiTrendingDown,
  FiTarget,
  FiAlertCircle,
  FiCheckCircle,
  FiZap,
  FiBarChart,
  FiPieChart,
  FiActivity,
  FiRefreshCw,
} from 'react-icons/fi';
import { useDashboardStore } from '../stores/dashboardStore';

interface AIInsight {
  id: string;
  type: 'optimization' | 'prediction' | 'anomaly' | 'recommendation';
  title: string;
  description: string;
  confidence: number;
  impact: 'high' | 'medium' | 'low';
  category: string;
  actionable: boolean;
  timestamp: Date;
}

interface PredictionModel {
  name: string;
  accuracy: number;
  lastTrained: Date;
  status: 'active' | 'training' | 'outdated';
  predictions: {
    metric: string;
    current: number;
    predicted: number;
    timeframe: string;
    confidence: number;
  }[];
}

const AIInsights: React.FC = () => {
  const { metrics, analytics, loading } = useDashboardStore();
  const [insights, setInsights] = useState<AIInsight[]>([]);
  const [models, setModels] = useState<PredictionModel[]>([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');

  // Generate AI insights
  useEffect(() => {
    const generateInsights = () => {
      const mockInsights: AIInsight[] = [
        {
          id: '1',
          type: 'optimization',
          title: 'Peak Hour Optimization Opportunity',
          description: 'Call volume peaks at 2-4 PM with 23% higher success rates. Consider reallocating resources during this window.',
          confidence: 87,
          impact: 'high',
          category: 'Resource Management',
          actionable: true,
          timestamp: new Date(Date.now() - 3600000),
        },
        {
          id: '2',
          type: 'prediction',
          title: 'Conversion Rate Forecast',
          description: 'Based on current trends, conversion rates are predicted to increase by 12% over the next 7 days.',
          confidence: 92,
          impact: 'medium',
          category: 'Performance Prediction',
          actionable: false,
          timestamp: new Date(Date.now() - 7200000),
        },
        {
          id: '3',
          type: 'anomaly',
          title: 'Unusual Call Pattern Detected',
          description: 'Call failure rate increased by 45% in the last 2 hours. Potential system issue or external factor.',
          confidence: 78,
          impact: 'high',
          category: 'Anomaly Detection',
          actionable: true,
          timestamp: new Date(Date.now() - 1800000),
        },
        {
          id: '4',
          type: 'recommendation',
          title: 'Campaign Timing Optimization',
          description: 'Historical data suggests launching campaigns on Tuesday-Thursday yields 18% better results.',
          confidence: 85,
          impact: 'medium',
          category: 'Campaign Strategy',
          actionable: true,
          timestamp: new Date(Date.now() - 5400000),
        },
        {
          id: '5',
          type: 'optimization',
          title: 'Agent Performance Correlation',
          description: 'Agents with 5+ years experience show 34% higher conversion rates. Consider pairing with newer agents.',
          confidence: 91,
          impact: 'high',
          category: 'Human Resources',
          actionable: true,
          timestamp: new Date(Date.now() - 10800000),
        },
      ];

      setInsights(mockInsights);
    };

    const generateModels = () => {
      const mockModels: PredictionModel[] = [
        {
          name: 'Call Success Predictor',
          accuracy: 89.5,
          lastTrained: new Date(Date.now() - 86400000),
          status: 'active',
          predictions: [
            {
              metric: 'Success Rate',
              current: 76.2,
              predicted: 78.8,
              timeframe: 'Next 24h',
              confidence: 87,
            },
            {
              metric: 'Call Volume',
              current: 1250,
              predicted: 1380,
              timeframe: 'Next 24h',
              confidence: 92,
            },
          ],
        },
        {
          name: 'Revenue Forecaster',
          accuracy: 84.2,
          lastTrained: new Date(Date.now() - 172800000),
          status: 'active',
          predictions: [
            {
              metric: 'Daily Revenue',
              current: 15420,
              predicted: 17250,
              timeframe: 'Tomorrow',
              confidence: 81,
            },
            {
              metric: 'Weekly Revenue',
              current: 98500,
              predicted: 112300,
              timeframe: 'Next 7 days',
              confidence: 85,
            },
          ],
        },
        {
          name: 'Churn Predictor',
          accuracy: 76.8,
          lastTrained: new Date(Date.now() - 259200000),
          status: 'training',
          predictions: [
            {
              metric: 'Churn Risk',
              current: 12.5,
              predicted: 14.2,
              timeframe: 'Next 30 days',
              confidence: 73,
            },
          ],
        },
      ];

      setModels(mockModels);
    };

    generateInsights();
    generateModels();

    const interval = setInterval(() => {
      generateInsights();
      generateModels();
    }, 300000); // Update every 5 minutes

    return () => clearInterval(interval);
  }, []);

  const getInsightIcon = (type: string) => {
    switch (type) {
      case 'optimization': return FiZap;
      case 'prediction': return FiTrendingUp;
      case 'anomaly': return FiAlertCircle;
      case 'recommendation': return FiZap;
      default: return FiActivity;
    }
  };

  const getInsightColor = (type: string) => {
    switch (type) {
      case 'optimization': return 'purple';
      case 'prediction': return 'blue';
      case 'anomaly': return 'red';
      case 'recommendation': return 'green';
      default: return 'gray';
    }
  };

  const getImpactColor = (impact: string) => {
    switch (impact) {
      case 'high': return 'red';
      case 'medium': return 'yellow';
      case 'low': return 'green';
      default: return 'gray';
    }
  };

  const getModelStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'green';
      case 'training': return 'yellow';
      case 'outdated': return 'red';
      default: return 'gray';
    }
  };

  const runAIAnalysis = async () => {
    setIsAnalyzing(true);
    // Simulate AI analysis
    await new Promise(resolve => setTimeout(resolve, 3000));
    setIsAnalyzing(false);
    // Refresh insights
    const newInsight: AIInsight = {
      id: Date.now().toString(),
      type: 'optimization',
      title: 'New Optimization Discovered',
      description: 'AI analysis completed. New optimization opportunities identified based on latest data patterns.',
      confidence: 94,
      impact: 'high',
      category: 'Real-time Analysis',
      actionable: true,
      timestamp: new Date(),
    };
    setInsights(prev => [newInsight, ...prev.slice(0, 4)]);
  };

  return (
    <VStack spacing={6} align="stretch">
      {/* Header */}
      <HStack justify="space-between">
        <HStack>
          <Icon as={FiActivity} boxSize={6} color="purple.500" />
          <VStack align="start" spacing={0}>
            <Text fontSize="lg" fontWeight="bold">
              AI-Powered Insights
            </Text>
            <Text fontSize="sm" color="gray.500">
              Machine learning analysis and predictions
            </Text>
          </VStack>
        </HStack>
        <Button
          leftIcon={<FiRefreshCw />}
          colorScheme="purple"
          size="sm"
          onClick={runAIAnalysis}
          isLoading={isAnalyzing}
          loadingText="Analyzing..."
        >
          Run AI Analysis
        </Button>
      </HStack>

      {/* AI Models Status */}
      <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
        <CardHeader>
          <HStack justify="space-between">
            <Text fontSize="md" fontWeight="bold">
              AI Models Status
            </Text>
            <Badge colorScheme="purple" variant="subtle">
              {models.filter(m => m.status === 'active').length} Active
            </Badge>
          </HStack>
        </CardHeader>
        <CardBody>
          <SimpleGrid columns={{ base: 1, md: 3 }} spacing={4}>
            {models.map((model, index) => (
              <Box key={index} p={4} borderRadius="md" bg={useColorModeValue('gray.50', 'gray.700')}>
                <VStack align="start" spacing={3}>
                  <HStack justify="space-between" w="full">
                    <Text fontSize="sm" fontWeight="medium" noOfLines={1}>
                      {model.name}
                    </Text>
                    <Badge colorScheme={getModelStatusColor(model.status)} size="sm">
                      {model.status}
                    </Badge>
                  </HStack>
                  
                  <VStack align="start" spacing={1} w="full">
                    <HStack justify="space-between" w="full">
                      <Text fontSize="xs" color="gray.500">Accuracy</Text>
                      <Text fontSize="xs" fontWeight="bold">{model.accuracy}%</Text>
                    </HStack>
                    <Progress
                      value={model.accuracy}
                      size="sm"
                      colorScheme="green"
                      w="full"
                      borderRadius="md"
                    />
                  </VStack>

                  <Text fontSize="xs" color="gray.500">
                    Last trained: {model.lastTrained.toLocaleDateString()}
                  </Text>
                </VStack>
              </Box>
            ))}
          </SimpleGrid>
        </CardBody>
      </Card>

      {/* Predictions */}
      <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
        <CardHeader>
          <Text fontSize="md" fontWeight="bold">
            AI Predictions
          </Text>
        </CardHeader>
        <CardBody>
          <Accordion allowMultiple>
            {models.filter(m => m.status === 'active').map((model, index) => (
              <AccordionItem key={index}>
                <AccordionButton>
                  <Box flex="1" textAlign="left">
                    <HStack>
                      <Icon as={FiBarChart} boxSize={4} color="blue.500" />
                      <Text fontSize="sm" fontWeight="medium">{model.name}</Text>
                      <Badge colorScheme="blue" size="sm">{model.accuracy}% accurate</Badge>
                    </HStack>
                  </Box>
                  <AccordionIcon />
                </AccordionButton>
                <AccordionPanel pb={4}>
                  <VStack spacing={3} align="stretch">
                    {model.predictions.map((prediction, pIndex) => (
                      <Box key={pIndex} p={3} borderRadius="md" bg={useColorModeValue('blue.50', 'blue.900')}>
                        <HStack justify="space-between" mb={2}>
                          <Text fontSize="sm" fontWeight="medium">{prediction.metric}</Text>
                          <Badge colorScheme="blue" size="sm">{prediction.confidence}% confidence</Badge>
                        </HStack>
                        <HStack justify="space-between">
                          <VStack align="start" spacing={0}>
                            <Text fontSize="xs" color="gray.500">Current</Text>
                            <Text fontSize="sm" fontWeight="bold">
                              {typeof prediction.current === 'number' && prediction.current > 1000 
                                ? prediction.current.toLocaleString() 
                                : prediction.current}
                            </Text>
                          </VStack>
                          <Icon as={FiTrendingUp} boxSize={4} color="green.500" />
                          <VStack align="end" spacing={0}>
                            <Text fontSize="xs" color="gray.500">{prediction.timeframe}</Text>
                            <Text fontSize="sm" fontWeight="bold" color="green.500">
                              {typeof prediction.predicted === 'number' && prediction.predicted > 1000 
                                ? prediction.predicted.toLocaleString() 
                                : prediction.predicted}
                            </Text>
                          </VStack>
                        </HStack>
                      </Box>
                    ))}
                  </VStack>
                </AccordionPanel>
              </AccordionItem>
            ))}
          </Accordion>
        </CardBody>
      </Card>

      {/* Insights */}
      <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
        <CardHeader>
          <HStack justify="space-between">
            <Text fontSize="md" fontWeight="bold">
              AI Insights & Recommendations
            </Text>
            <Badge colorScheme="green" variant="subtle">
              {insights.filter(i => i.actionable).length} Actionable
            </Badge>
          </HStack>
        </CardHeader>
        <CardBody>
          <VStack spacing={4} align="stretch">
            {insights.map((insight) => (
              <Box
                key={insight.id}
                p={4}
                borderRadius="md"
                borderWidth="1px"
                borderColor={borderColor}
                bg={useColorModeValue('gray.50', 'gray.700')}
              >
                <VStack align="start" spacing={3}>
                  <HStack justify="space-between" w="full">
                    <HStack>
                      <Icon
                        as={getInsightIcon(insight.type)}
                        boxSize={5}
                        color={`${getInsightColor(insight.type)}.500`}
                      />
                      <VStack align="start" spacing={0}>
                        <Text fontSize="sm" fontWeight="bold">
                          {insight.title}
                        </Text>
                        <HStack>
                          <Badge colorScheme={getInsightColor(insight.type)} size="sm">
                            {insight.type}
                          </Badge>
                          <Badge colorScheme={getImpactColor(insight.impact)} size="sm">
                            {insight.impact} impact
                          </Badge>
                          <Text fontSize="xs" color="gray.500">
                            {insight.category}
                          </Text>
                        </HStack>
                      </VStack>
                    </HStack>
                    <VStack align="end" spacing={1}>
                      <Text fontSize="xs" color="gray.500">
                        {insight.confidence}% confidence
                      </Text>
                      <Progress
                        value={insight.confidence}
                        size="sm"
                        w="60px"
                        colorScheme={getInsightColor(insight.type)}
                      />
                    </VStack>
                  </HStack>

                  <Text fontSize="sm" color="gray.600">
                    {insight.description}
                  </Text>

                  <HStack justify="space-between" w="full">
                    <Text fontSize="xs" color="gray.500">
                      {insight.timestamp.toLocaleString()}
                    </Text>
                    {insight.actionable && (
                      <Button size="xs" colorScheme={getInsightColor(insight.type)} variant="outline">
                        Take Action
                      </Button>
                    )}
                  </HStack>
                </VStack>
              </Box>
            ))}
          </VStack>
        </CardBody>
      </Card>

      {/* AI Analysis Summary */}
      <SimpleGrid columns={{ base: 1, md: 3 }} spacing={4}>
        <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
          <CardBody>
            <VStack spacing={3}>
              <Icon as={FiTarget} boxSize={8} color="green.500" />
              <Text fontSize="sm" fontWeight="bold" textAlign="center">
                Optimization Score
              </Text>
              <Text fontSize="2xl" fontWeight="bold" color="green.500">
                87%
              </Text>
              <Text fontSize="xs" color="gray.500" textAlign="center">
                Based on current performance metrics
              </Text>
            </VStack>
          </CardBody>
        </Card>

        <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
          <CardBody>
            <VStack spacing={3}>
              <Icon as={FiActivity} boxSize={8} color="blue.500" />
              <Text fontSize="sm" fontWeight="bold" textAlign="center">
                Prediction Accuracy
              </Text>
              <Text fontSize="2xl" fontWeight="bold" color="blue.500">
                84.2%
              </Text>
              <Text fontSize="xs" color="gray.500" textAlign="center">
                Average across all models
              </Text>
            </VStack>
          </CardBody>
        </Card>

        <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
          <CardBody>
            <VStack spacing={3}>
              <Icon as={FiZap} boxSize={8} color="yellow.500" />
              <Text fontSize="sm" fontWeight="bold" textAlign="center">
                Actionable Insights
              </Text>
              <Text fontSize="2xl" fontWeight="bold" color="yellow.500">
                {insights.filter(i => i.actionable).length}
              </Text>
              <Text fontSize="xs" color="gray.500" textAlign="center">
                Ready for implementation
              </Text>
            </VStack>
          </CardBody>
        </Card>
      </SimpleGrid>
    </VStack>
  );
};

export default AIInsights;