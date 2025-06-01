import React, { useEffect, useState } from 'react';
import {
  Box,
  VStack,
  HStack,
  Text,
  Badge,
  Card,
  CardBody,
  Progress,
  Flex,
  Icon,
  useColorModeValue,
  Tooltip,
  SimpleGrid,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  StatArrow,
  Divider,
} from '@chakra-ui/react';
import {
  FiActivity,
  FiWifi,
  FiWifiOff,
  FiPhone,
  FiUsers,
  FiTrendingUp,
  FiTrendingDown,
  FiClock,
  FiZap,
} from 'react-icons/fi';
import { useDashboardStore } from '../stores/dashboardStore';

interface RealTimeMetric {
  label: string;
  value: number | string;
  change?: number;
  unit?: string;
  color?: string;
  icon?: React.ElementType;
}

const RealTimeMonitor: React.FC = () => {
  const {
    isConnected,
    liveMetrics,
    metrics,
    connectRealTime,
    disconnectRealTime,
    updateLiveMetrics,
  } = useDashboardStore();

  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [connectionQuality, setConnectionQuality] = useState<'excellent' | 'good' | 'poor'>('excellent');

  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  const connectedColor = useColorModeValue('green.500', 'green.300');
  const disconnectedColor = useColorModeValue('red.500', 'red.300');

  useEffect(() => {
    // Connect to real-time updates when component mounts
    connectRealTime();

    // Simulate real-time metric updates
    const interval = setInterval(() => {
      const mockUpdates = {
        activeCalls: Math.floor(Math.random() * 50) + 10,
        callsPerMinute: Math.floor(Math.random() * 20) + 5,
        avgResponseTime: Math.floor(Math.random() * 500) + 200,
        systemLoad: Math.random() * 100,
        networkLatency: Math.floor(Math.random() * 100) + 10,
        errorRate: Math.random() * 5,
      };

      updateLiveMetrics(mockUpdates);
      setLastUpdate(new Date());

      // Simulate connection quality changes
      const qualities: Array<'excellent' | 'good' | 'poor'> = ['excellent', 'good', 'poor'];
      setConnectionQuality(qualities[Math.floor(Math.random() * qualities.length)]);
    }, 3000);

    return () => {
      clearInterval(interval);
      disconnectRealTime();
    };
  }, [connectRealTime, disconnectRealTime, updateLiveMetrics]);

  const realTimeMetrics: RealTimeMetric[] = [
    {
      label: 'Active Calls',
      value: liveMetrics.activeCalls || 0,
      change: Math.random() * 10 - 5,
      icon: FiPhone,
      color: 'blue',
    },
    {
      label: 'Calls/Min',
      value: liveMetrics.callsPerMinute || 0,
      change: Math.random() * 20 - 10,
      icon: FiTrendingUp,
      color: 'green',
    },
    {
      label: 'Response Time',
      value: liveMetrics.avgResponseTime || 0,
      unit: 'ms',
      change: Math.random() * 100 - 50,
      icon: FiClock,
      color: 'orange',
    },
    {
      label: 'System Load',
      value: `${(liveMetrics.systemLoad || 0).toFixed(1)}%`,
      change: Math.random() * 10 - 5,
      icon: FiZap,
      color: 'purple',
    },
  ];

  const getConnectionQualityColor = () => {
    switch (connectionQuality) {
      case 'excellent': return 'green';
      case 'good': return 'yellow';
      case 'poor': return 'red';
      default: return 'gray';
    }
  };

  const getConnectionQualityValue = () => {
    switch (connectionQuality) {
      case 'excellent': return 100;
      case 'good': return 70;
      case 'poor': return 30;
      default: return 0;
    }
  };

  return (
    <Card bg={cardBg} borderColor={borderColor} borderWidth="1px" size="sm">
      <CardBody>
        <VStack spacing={4} align="stretch">
          {/* Connection Status Header */}
          <HStack justify="space-between">
            <HStack>
              <Icon
                as={isConnected ? FiWifi : FiWifiOff}
                color={isConnected ? connectedColor : disconnectedColor}
                boxSize={4}
              />
              <Text fontSize="sm" fontWeight="medium">
                Real-Time Monitor
              </Text>
              <Badge
                colorScheme={isConnected ? 'green' : 'red'}
                variant="subtle"
                size="sm"
              >
                {isConnected ? 'Connected' : 'Disconnected'}
              </Badge>
            </HStack>
            <Tooltip label={`Last updated: ${lastUpdate.toLocaleTimeString()}`}>
              <Icon as={FiActivity} boxSize={3} color="gray.500" />
            </Tooltip>
          </HStack>

          {/* Connection Quality */}
          {isConnected && (
            <Box>
              <HStack justify="space-between" mb={1}>
                <Text fontSize="xs" color="gray.500">
                  Connection Quality
                </Text>
                <Text fontSize="xs" color="gray.500">
                  {connectionQuality.charAt(0).toUpperCase() + connectionQuality.slice(1)}
                </Text>
              </HStack>
              <Progress
                value={getConnectionQualityValue()}
                size="sm"
                colorScheme={getConnectionQualityColor()}
                borderRadius="md"
              />
            </Box>
          )}

          <Divider />

          {/* Real-Time Metrics Grid */}
          <SimpleGrid columns={2} spacing={3}>
            {realTimeMetrics.map((metric, index) => (
              <Box key={index} p={2} borderRadius="md" bg={useColorModeValue('gray.50', 'gray.700')}>
                <VStack spacing={1} align="start">
                  <HStack>
                    {metric.icon && (
                      <Icon as={metric.icon} boxSize={3} color={`${metric.color}.500`} />
                    )}
                    <Text fontSize="xs" color="gray.500" noOfLines={1}>
                      {metric.label}
                    </Text>
                  </HStack>
                  <HStack justify="space-between" w="full">
                    <Text fontSize="sm" fontWeight="bold">
                      {metric.value}{metric.unit}
                    </Text>
                    {metric.change !== undefined && (
                      <HStack spacing={1}>
                        <Icon
                          as={metric.change >= 0 ? FiTrendingUp : FiTrendingDown}
                          boxSize={3}
                          color={metric.change >= 0 ? 'green.500' : 'red.500'}
                        />
                        <Text
                          fontSize="xs"
                          color={metric.change >= 0 ? 'green.500' : 'red.500'}
                        >
                          {Math.abs(metric.change).toFixed(1)}%
                        </Text>
                      </HStack>
                    )}
                  </HStack>
                </VStack>
              </Box>
            ))}
          </SimpleGrid>

          {/* System Health Indicators */}
          <Box>
            <Text fontSize="xs" color="gray.500" mb={2}>
              System Health
            </Text>
            <VStack spacing={2}>
              <HStack justify="space-between" w="full">
                <Text fontSize="xs">Network Latency</Text>
                <HStack>
                  <Text fontSize="xs">{liveMetrics.networkLatency || 0}ms</Text>
                  <Progress
                    value={Math.max(0, 100 - (liveMetrics.networkLatency || 0))}
                    size="sm"
                    w="40px"
                    colorScheme="green"
                  />
                </HStack>
              </HStack>
              
              <HStack justify="space-between" w="full">
                <Text fontSize="xs">Error Rate</Text>
                <HStack>
                  <Text fontSize="xs">{(liveMetrics.errorRate || 0).toFixed(2)}%</Text>
                  <Progress
                    value={Math.min(100, (liveMetrics.errorRate || 0) * 20)}
                    size="sm"
                    w="40px"
                    colorScheme="red"
                  />
                </HStack>
              </HStack>
            </VStack>
          </Box>

          {/* Quick Stats */}
          <Box>
            <Text fontSize="xs" color="gray.500" mb={2}>
              Quick Stats
            </Text>
            <SimpleGrid columns={2} spacing={2}>
              <Stat size="sm">
                <StatLabel fontSize="xs">Total Today</StatLabel>
                <StatNumber fontSize="sm">{metrics?.totalCalls || 0}</StatNumber>
              </Stat>
              <Stat size="sm">
                <StatLabel fontSize="xs">Success Rate</StatLabel>
                <StatNumber fontSize="sm">{metrics?.conversionRate?.toFixed(1) || 0}%</StatNumber>
              </Stat>
            </SimpleGrid>
          </Box>
        </VStack>
      </CardBody>
    </Card>
  );
};

export default RealTimeMonitor;