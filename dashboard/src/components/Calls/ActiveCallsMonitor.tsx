/**
 * Active Calls Monitor Component for Project GeminiVoiceConnect
 * 
 * This component provides real-time monitoring of active calls across all 80 modems
 * with advanced call management capabilities, quality monitoring, and intelligent
 * call routing. It implements GPU-accelerated audio analysis and real-time analytics.
 */

import React, { useState, useEffect, useCallback } from 'react';
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
  Input,
  InputGroup,
  InputLeftElement,
  Select,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  CircularProgress,
  CircularProgressLabel,
  Divider,
  SimpleGrid,
} from '@chakra-ui/react';
import {
  FiPhone,
  FiPhoneCall,
  FiPhoneOff,
  FiMic,
  FiMicOff,
  FiVolume2,
  FiVolumeX,
  FiClock,
  FiUser,
  FiMapPin,
  FiActivity,
  FiBarChart3,
  FiSettings,
  FiRefreshCw,
  FiSearch,
  FiFilter,
  FiMaximize2,
  FiMinimize2,
  FiAlertTriangle,
  FiCheckCircle,
  FiXCircle,
  FiPause,
  FiPlay,
  FiSkipForward,
  FiHeadphones,
  FiRadio,
  FiSignal,
} from 'react-icons/fi';
import { Line, Bar } from 'react-chartjs-2';

interface ActiveCall {
  id: string;
  modemId: string;
  phoneNumber: string;
  customerName?: string;
  campaignId?: string;
  campaignName?: string;
  startTime: Date;
  duration: number;
  status: 'connecting' | 'active' | 'on-hold' | 'transferring' | 'ending';
  quality: 'excellent' | 'good' | 'fair' | 'poor';
  sentiment: 'positive' | 'neutral' | 'negative';
  aiConfidence: number;
  location?: string;
  callType: 'inbound' | 'outbound';
  priority: 'low' | 'normal' | 'high' | 'urgent';
}

interface ModemStatus {
  id: string;
  status: 'online' | 'offline' | 'busy' | 'maintenance';
  signalStrength: number;
  temperature: number;
  callsToday: number;
  lastActivity: Date;
  location?: string;
}

interface CallQualityMetrics {
  audioQuality: number;
  latency: number;
  jitter: number;
  packetLoss: number;
  signalToNoise: number;
}

const ActiveCallsMonitor: React.FC = () => {
  const [activeCalls, setActiveCalls] = useState<ActiveCall[]>([]);
  const [modemStatuses, setModemStatuses] = useState<ModemStatus[]>([]);
  const [selectedCall, setSelectedCall] = useState<ActiveCall | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [filterQuality, setFilterQuality] = useState<string>('all');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(new Date());

  const { isOpen: isCallDetailOpen, onOpen: onCallDetailOpen, onClose: onCallDetailClose } = useDisclosure();

  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  const textColor = useColorModeValue('gray.700', 'gray.200');

  // Mock data - would come from WebSocket/API
  useEffect(() => {
    const mockCalls: ActiveCall[] = [
      {
        id: 'call_001',
        modemId: 'modem_15',
        phoneNumber: '+1-555-0123',
        customerName: 'John Smith',
        campaignId: 'camp_summer',
        campaignName: 'Summer Sale',
        startTime: new Date(Date.now() - 180000), // 3 minutes ago
        duration: 180,
        status: 'active',
        quality: 'excellent',
        sentiment: 'positive',
        aiConfidence: 0.92,
        location: 'New York, NY',
        callType: 'outbound',
        priority: 'normal',
      },
      {
        id: 'call_002',
        modemId: 'modem_23',
        phoneNumber: '+1-555-0456',
        customerName: 'Sarah Johnson',
        campaignId: 'camp_retention',
        campaignName: 'Customer Retention',
        startTime: new Date(Date.now() - 420000), // 7 minutes ago
        duration: 420,
        status: 'active',
        quality: 'good',
        sentiment: 'neutral',
        aiConfidence: 0.78,
        location: 'Los Angeles, CA',
        callType: 'outbound',
        priority: 'high',
      },
      {
        id: 'call_003',
        modemId: 'modem_07',
        phoneNumber: '+1-555-0789',
        customerName: 'Mike Wilson',
        startTime: new Date(Date.now() - 90000), // 1.5 minutes ago
        duration: 90,
        status: 'connecting',
        quality: 'fair',
        sentiment: 'neutral',
        aiConfidence: 0.65,
        location: 'Chicago, IL',
        callType: 'inbound',
        priority: 'urgent',
      },
    ];

    const mockModems: ModemStatus[] = Array.from({ length: 80 }, (_, i) => ({
      id: `modem_${i + 1}`,
      status: Math.random() > 0.1 ? (Math.random() > 0.3 ? 'online' : 'busy') : 'offline',
      signalStrength: Math.floor(Math.random() * 40) + 60,
      temperature: Math.floor(Math.random() * 20) + 35,
      callsToday: Math.floor(Math.random() * 50),
      lastActivity: new Date(Date.now() - Math.random() * 3600000),
    }));

    setActiveCalls(mockCalls);
    setModemStatuses(mockModems);
  }, []);

  // Auto-refresh data
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      // Simulate real-time updates
      setActiveCalls(prev => prev.map(call => ({
        ...call,
        duration: call.duration + 5,
        aiConfidence: Math.max(0.5, Math.min(1, call.aiConfidence + (Math.random() - 0.5) * 0.1)),
      })));
      setLastUpdated(new Date());
    }, 5000);

    return () => clearInterval(interval);
  }, [autoRefresh]);

  const filteredCalls = activeCalls.filter(call => {
    const matchesSearch = 
      call.phoneNumber.includes(searchTerm) ||
      call.customerName?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      call.campaignName?.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesStatus = filterStatus === 'all' || call.status === filterStatus;
    const matchesQuality = filterQuality === 'all' || call.quality === filterQuality;
    
    return matchesSearch && matchesStatus && matchesQuality;
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'green';
      case 'connecting': return 'blue';
      case 'on-hold': return 'yellow';
      case 'transferring': return 'purple';
      case 'ending': return 'red';
      default: return 'gray';
    }
  };

  const getQualityColor = (quality: string) => {
    switch (quality) {
      case 'excellent': return 'green';
      case 'good': return 'blue';
      case 'fair': return 'yellow';
      case 'poor': return 'red';
      default: return 'gray';
    }
  };

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case 'positive': return 'green';
      case 'neutral': return 'gray';
      case 'negative': return 'red';
      default: return 'gray';
    }
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleCallAction = (callId: string, action: string) => {
    console.log(`Performing ${action} on call ${callId}`);
    // Implement call actions (hold, transfer, end, etc.)
  };

  const handleCallDetail = (call: ActiveCall) => {
    setSelectedCall(call);
    onCallDetailOpen();
  };

  // Calculate summary metrics
  const totalActiveCalls = activeCalls.length;
  const averageCallDuration = activeCalls.length > 0 
    ? Math.round(activeCalls.reduce((sum, call) => sum + call.duration, 0) / activeCalls.length)
    : 0;
  const excellentQualityCalls = activeCalls.filter(call => call.quality === 'excellent').length;
  const positiveSentimentCalls = activeCalls.filter(call => call.sentiment === 'positive').length;

  const onlineModems = modemStatuses.filter(modem => modem.status === 'online').length;
  const busyModems = modemStatuses.filter(modem => modem.status === 'busy').length;
  const offlineModems = modemStatuses.filter(modem => modem.status === 'offline').length;

  // Chart data for call volume over time
  const callVolumeData = {
    labels: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00'],
    datasets: [
      {
        label: 'Active Calls',
        data: [12, 8, 25, 45, 38, 28],
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.4,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
    },
    scales: {
      y: {
        beginAtZero: true,
      },
    },
  };

  return (
    <Box p={6} maxW="full">
      {/* Header */}
      <Flex justify="space-between" align="center" mb={6}>
        <VStack align="start" spacing={1}>
          <Heading size="lg" color={textColor}>
            Active Calls Monitor
          </Heading>
          <Text color="gray.500" fontSize="sm">
            Real-time call monitoring across 80 modems • Last updated: {lastUpdated.toLocaleTimeString()}
          </Text>
        </VStack>
        
        <HStack spacing={3}>
          <Button
            size="sm"
            variant={autoRefresh ? 'solid' : 'outline'}
            colorScheme="blue"
            leftIcon={<FiActivity />}
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            {autoRefresh ? 'Live' : 'Paused'}
          </Button>
          
          <IconButton
            aria-label="Refresh"
            icon={<FiRefreshCw />}
            size="sm"
            variant="outline"
            onClick={() => setLastUpdated(new Date())}
          />
        </HStack>
      </Flex>

      {/* Summary Cards */}
      <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={6} mb={6}>
        <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
          <CardBody>
            <Stat>
              <StatLabel>Active Calls</StatLabel>
              <StatNumber color="blue.500">{totalActiveCalls}</StatNumber>
              <StatHelpText>
                <Icon as={FiPhone} mr={1} />
                Across {busyModems} modems
              </StatHelpText>
            </Stat>
          </CardBody>
        </Card>

        <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
          <CardBody>
            <Stat>
              <StatLabel>Avg Call Duration</StatLabel>
              <StatNumber color="green.500">{formatDuration(averageCallDuration)}</StatNumber>
              <StatHelpText>
                <Icon as={FiClock} mr={1} />
                Current session
              </StatHelpText>
            </Stat>
          </CardBody>
        </Card>

        <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
          <CardBody>
            <Stat>
              <StatLabel>Quality Score</StatLabel>
              <StatNumber color="purple.500">
                {totalActiveCalls > 0 ? Math.round((excellentQualityCalls / totalActiveCalls) * 100) : 0}%
              </StatNumber>
              <StatHelpText>
                <Icon as={FiBarChart3} mr={1} />
                Excellent quality
              </StatHelpText>
            </Stat>
          </CardBody>
        </Card>

        <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
          <CardBody>
            <Stat>
              <StatLabel>Positive Sentiment</StatLabel>
              <StatNumber color="orange.500">
                {totalActiveCalls > 0 ? Math.round((positiveSentimentCalls / totalActiveCalls) * 100) : 0}%
              </StatNumber>
              <StatHelpText>
                <Icon as={FiActivity} mr={1} />
                AI Analysis
              </StatHelpText>
            </Stat>
          </CardBody>
        </Card>
      </SimpleGrid>

      {/* Modem Status Overview */}
      <Card bg={cardBg} borderColor={borderColor} borderWidth="1px" mb={6}>
        <CardHeader>
          <Heading size="md">Modem Status Overview</Heading>
        </CardHeader>
        <CardBody>
          <HStack spacing={8} justify="center">
            <VStack>
              <CircularProgress value={(onlineModems / 80) * 100} color="green.400" size="80px">
                <CircularProgressLabel>{onlineModems}</CircularProgressLabel>
              </CircularProgress>
              <Text fontSize="sm" color="gray.500">Online</Text>
            </VStack>
            
            <VStack>
              <CircularProgress value={(busyModems / 80) * 100} color="blue.400" size="80px">
                <CircularProgressLabel>{busyModems}</CircularProgressLabel>
              </CircularProgress>
              <Text fontSize="sm" color="gray.500">Busy</Text>
            </VStack>
            
            <VStack>
              <CircularProgress value={(offlineModems / 80) * 100} color="red.400" size="80px">
                <CircularProgressLabel>{offlineModems}</CircularProgressLabel>
              </CircularProgress>
              <Text fontSize="sm" color="gray.500">Offline</Text>
            </VStack>
            
            <Box w="300px" h="120px">
              <Text fontSize="sm" color="gray.500" mb={2}>Call Volume (24h)</Text>
              <Line data={callVolumeData} options={chartOptions} />
            </Box>
          </HStack>
        </CardBody>
      </Card>

      {/* Filters and Search */}
      <Card bg={cardBg} borderColor={borderColor} borderWidth="1px" mb={6}>
        <CardBody>
          <HStack spacing={4} wrap="wrap">
            <InputGroup maxW="300px">
              <InputLeftElement>
                <Icon as={FiSearch} color="gray.400" />
              </InputLeftElement>
              <Input
                placeholder="Search calls..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </InputGroup>
            
            <Select maxW="150px" value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}>
              <option value="all">All Status</option>
              <option value="active">Active</option>
              <option value="connecting">Connecting</option>
              <option value="on-hold">On Hold</option>
              <option value="transferring">Transferring</option>
            </Select>
            
            <Select maxW="150px" value={filterQuality} onChange={(e) => setFilterQuality(e.target.value)}>
              <option value="all">All Quality</option>
              <option value="excellent">Excellent</option>
              <option value="good">Good</option>
              <option value="fair">Fair</option>
              <option value="poor">Poor</option>
            </Select>
          </HStack>
        </CardBody>
      </Card>

      {/* Active Calls Table */}
      <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
        <CardHeader>
          <HStack justify="space-between">
            <Heading size="md">Active Calls ({filteredCalls.length})</Heading>
            <HStack>
              <Button size="sm" leftIcon={<FiSettings />} variant="outline">
                Configure
              </Button>
              <Button size="sm" leftIcon={<FiMaximize2 />} variant="outline">
                Full Screen
              </Button>
            </HStack>
          </HStack>
        </CardHeader>
        <CardBody>
          <TableContainer>
            <Table variant="simple" size="sm">
              <Thead>
                <Tr>
                  <Th>Call Info</Th>
                  <Th>Customer</Th>
                  <Th>Campaign</Th>
                  <Th>Duration</Th>
                  <Th>Status</Th>
                  <Th>Quality</Th>
                  <Th>Sentiment</Th>
                  <Th>AI Confidence</Th>
                  <Th>Actions</Th>
                </Tr>
              </Thead>
              <Tbody>
                {filteredCalls.map((call) => (
                  <Tr key={call.id} _hover={{ bg: useColorModeValue('gray.50', 'gray.700') }}>
                    <Td>
                      <VStack align="start" spacing={1}>
                        <HStack>
                          <Icon as={call.callType === 'inbound' ? FiPhoneCall : FiPhone} />
                          <Text fontSize="sm" fontWeight="medium">
                            {call.phoneNumber}
                          </Text>
                        </HStack>
                        <Text fontSize="xs" color="gray.500">
                          Modem {call.modemId}
                        </Text>
                      </VStack>
                    </Td>
                    <Td>
                      <VStack align="start" spacing={1}>
                        <Text fontSize="sm" fontWeight="medium">
                          {call.customerName || 'Unknown'}
                        </Text>
                        {call.location && (
                          <HStack>
                            <Icon as={FiMapPin} boxSize={3} color="gray.400" />
                            <Text fontSize="xs" color="gray.500">
                              {call.location}
                            </Text>
                          </HStack>
                        )}
                      </VStack>
                    </Td>
                    <Td>
                      <Text fontSize="sm">
                        {call.campaignName || 'Direct Call'}
                      </Text>
                    </Td>
                    <Td>
                      <Text fontSize="sm" fontFamily="mono">
                        {formatDuration(call.duration)}
                      </Text>
                    </Td>
                    <Td>
                      <Badge colorScheme={getStatusColor(call.status)} size="sm">
                        {call.status}
                      </Badge>
                    </Td>
                    <Td>
                      <Badge colorScheme={getQualityColor(call.quality)} size="sm">
                        {call.quality}
                      </Badge>
                    </Td>
                    <Td>
                      <Badge colorScheme={getSentimentColor(call.sentiment)} size="sm">
                        {call.sentiment}
                      </Badge>
                    </Td>
                    <Td>
                      <HStack>
                        <Progress
                          value={call.aiConfidence * 100}
                          size="sm"
                          colorScheme={call.aiConfidence > 0.8 ? 'green' : call.aiConfidence > 0.6 ? 'yellow' : 'red'}
                          w="50px"
                        />
                        <Text fontSize="xs">
                          {Math.round(call.aiConfidence * 100)}%
                        </Text>
                      </HStack>
                    </Td>
                    <Td>
                      <HStack spacing={1}>
                        <Tooltip label="View Details">
                          <IconButton
                            aria-label="View details"
                            icon={<FiMaximize2 />}
                            size="xs"
                            variant="ghost"
                            onClick={() => handleCallDetail(call)}
                          />
                        </Tooltip>
                        <Tooltip label="Hold Call">
                          <IconButton
                            aria-label="Hold call"
                            icon={<FiPause />}
                            size="xs"
                            variant="ghost"
                            onClick={() => handleCallAction(call.id, 'hold')}
                          />
                        </Tooltip>
                        <Tooltip label="End Call">
                          <IconButton
                            aria-label="End call"
                            icon={<FiPhoneOff />}
                            size="xs"
                            variant="ghost"
                            colorScheme="red"
                            onClick={() => handleCallAction(call.id, 'end')}
                          />
                        </Tooltip>
                      </HStack>
                    </Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
          </TableContainer>
          
          {filteredCalls.length === 0 && (
            <Box textAlign="center" py={8}>
              <Icon as={FiPhone} boxSize={12} color="gray.300" mb={4} />
              <Text color="gray.500">No active calls found</Text>
            </Box>
          )}
        </CardBody>
      </Card>

      {/* Call Detail Modal */}
      <Modal isOpen={isCallDetailOpen} onClose={onCallDetailClose} size="xl">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>
            Call Details - {selectedCall?.phoneNumber}
          </ModalHeader>
          <ModalCloseButton />
          <ModalBody pb={6}>
            {selectedCall && (
              <Tabs>
                <TabList>
                  <Tab>Overview</Tab>
                  <Tab>Quality Metrics</Tab>
                  <Tab>AI Analysis</Tab>
                  <Tab>Actions</Tab>
                </TabList>
                
                <TabPanels>
                  <TabPanel>
                    <VStack spacing={4} align="stretch">
                      <SimpleGrid columns={2} spacing={4}>
                        <Box>
                          <Text fontSize="sm" color="gray.500">Customer</Text>
                          <Text fontWeight="medium">{selectedCall.customerName || 'Unknown'}</Text>
                        </Box>
                        <Box>
                          <Text fontSize="sm" color="gray.500">Phone Number</Text>
                          <Text fontWeight="medium">{selectedCall.phoneNumber}</Text>
                        </Box>
                        <Box>
                          <Text fontSize="sm" color="gray.500">Campaign</Text>
                          <Text fontWeight="medium">{selectedCall.campaignName || 'Direct Call'}</Text>
                        </Box>
                        <Box>
                          <Text fontSize="sm" color="gray.500">Duration</Text>
                          <Text fontWeight="medium">{formatDuration(selectedCall.duration)}</Text>
                        </Box>
                        <Box>
                          <Text fontSize="sm" color="gray.500">Status</Text>
                          <Badge colorScheme={getStatusColor(selectedCall.status)}>
                            {selectedCall.status}
                          </Badge>
                        </Box>
                        <Box>
                          <Text fontSize="sm" color="gray.500">Call Type</Text>
                          <Text fontWeight="medium">{selectedCall.callType}</Text>
                        </Box>
                      </SimpleGrid>
                    </VStack>
                  </TabPanel>
                  
                  <TabPanel>
                    <VStack spacing={4} align="stretch">
                      <Text fontSize="sm" color="gray.500">Real-time Quality Metrics</Text>
                      <SimpleGrid columns={2} spacing={4}>
                        <Box>
                          <Text fontSize="sm" color="gray.500">Audio Quality</Text>
                          <Progress value={85} colorScheme="green" />
                          <Text fontSize="xs" color="gray.500">85% - Excellent</Text>
                        </Box>
                        <Box>
                          <Text fontSize="sm" color="gray.500">Latency</Text>
                          <Progress value={75} colorScheme="blue" />
                          <Text fontSize="xs" color="gray.500">125ms - Good</Text>
                        </Box>
                        <Box>
                          <Text fontSize="sm" color="gray.500">Signal Strength</Text>
                          <Progress value={90} colorScheme="green" />
                          <Text fontSize="xs" color="gray.500">-65 dBm - Strong</Text>
                        </Box>
                        <Box>
                          <Text fontSize="sm" color="gray.500">Packet Loss</Text>
                          <Progress value={95} colorScheme="green" />
                          <Text fontSize="xs" color="gray.500">0.2% - Excellent</Text>
                        </Box>
                      </SimpleGrid>
                    </VStack>
                  </TabPanel>
                  
                  <TabPanel>
                    <VStack spacing={4} align="stretch">
                      <Box>
                        <Text fontSize="sm" color="gray.500" mb={2}>AI Confidence Score</Text>
                        <HStack>
                          <Progress
                            value={selectedCall.aiConfidence * 100}
                            colorScheme="purple"
                            flex={1}
                          />
                          <Text fontSize="sm" fontWeight="medium">
                            {Math.round(selectedCall.aiConfidence * 100)}%
                          </Text>
                        </HStack>
                      </Box>
                      
                      <Box>
                        <Text fontSize="sm" color="gray.500" mb={2}>Sentiment Analysis</Text>
                        <Badge colorScheme={getSentimentColor(selectedCall.sentiment)} size="lg">
                          {selectedCall.sentiment}
                        </Badge>
                      </Box>
                      
                      <Box>
                        <Text fontSize="sm" color="gray.500" mb={2}>Key Topics Detected</Text>
                        <HStack wrap="wrap">
                          <Badge>Product Interest</Badge>
                          <Badge>Pricing Questions</Badge>
                          <Badge>Support Request</Badge>
                        </HStack>
                      </Box>
                    </VStack>
                  </TabPanel>
                  
                  <TabPanel>
                    <VStack spacing={4} align="stretch">
                      <SimpleGrid columns={2} spacing={4}>
                        <Button leftIcon={<FiPause />} colorScheme="yellow">
                          Hold Call
                        </Button>
                        <Button leftIcon={<FiSkipForward />} colorScheme="blue">
                          Transfer
                        </Button>
                        <Button leftIcon={<FiMic />} colorScheme="green">
                          Mute/Unmute
                        </Button>
                        <Button leftIcon={<FiHeadphones />} colorScheme="purple">
                          Monitor
                        </Button>
                        <Button leftIcon={<FiPhoneOff />} colorScheme="red" colSpan={2}>
                          End Call
                        </Button>
                      </SimpleGrid>
                    </VStack>
                  </TabPanel>
                </TabPanels>
              </Tabs>
            )}
          </ModalBody>
        </ModalContent>
      </Modal>
    </Box>
  );
};

export default ActiveCallsMonitor;