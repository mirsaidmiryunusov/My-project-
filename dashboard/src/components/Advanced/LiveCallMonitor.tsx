/**
 * Live Call Monitor - Real-time Call Monitoring and Management
 * 
 * This component provides comprehensive real-time call monitoring with
 * advanced features like sentiment analysis, transcription, and AI insights.
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
  Avatar,
  Progress,
  Divider,
  Input,
  InputGroup,
  InputLeftElement,
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
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  TableContainer,
  Flex,
  Spacer,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
  Slider,
  SliderTrack,
  SliderFilledTrack,
  SliderThumb,
} from '@chakra-ui/react';
import {
  FiPhone,
  FiPhoneCall,
  FiPhoneOff,
  FiMic,
  FiMicOff,
  FiVolume2,
  FiVolumeX,
  FiPlay,
  FiPause,
  FiSkipForward,
  FiSearch,
  FiFilter,
  FiEye,
  FiEyeOff,
  FiMessageSquare,
  FiUser,
  FiClock,
  FiTrendingUp,
  FiTrendingDown,
  FiActivity,
  FiHeart,
  FiAlertTriangle,
  FiCheckCircle,
  FiXCircle,
  FiRefreshCw,
  FiSettings,
  FiMaximize2,
  FiMinimize2,
  FiDownload,
  FiShare2,
  FiEdit,
  FiSave,
  FiTarget,
  FiCpu,
  FiZap,
} from 'react-icons/fi';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { useRealtimeStore } from '../../stores/realtimeStore';
import { useAdvancedAnalyticsStore } from '../../stores/advancedAnalyticsStore';

// Call Status Components
const CallStatusBadge: React.FC<{ status: string }> = ({ status }) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ringing': return 'yellow';
      case 'connected': return 'green';
      case 'on_hold': return 'orange';
      case 'transferring': return 'blue';
      case 'ending': return 'red';
      default: return 'gray';
    }
  };

  return (
    <Badge colorScheme={getStatusColor(status)} variant="subtle">
      {status.replace('_', ' ').toUpperCase()}
    </Badge>
  );
};

const SentimentIndicator: React.FC<{ sentiment: string; score: number }> = ({ sentiment, score }) => {
  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case 'positive': return 'green';
      case 'neutral': return 'yellow';
      case 'negative': return 'red';
      default: return 'gray';
    }
  };

  const getSentimentIcon = (sentiment: string) => {
    switch (sentiment) {
      case 'positive': return '😊';
      case 'neutral': return '😐';
      case 'negative': return '😞';
      default: return '❓';
    }
  };

  return (
    <HStack spacing={2}>
      <Text fontSize="lg">{getSentimentIcon(sentiment)}</Text>
      <Badge colorScheme={getSentimentColor(sentiment)} variant="subtle">
        {sentiment}
      </Badge>
      <Text fontSize="sm" color="gray.500">
        {(score * 100).toFixed(0)}%
      </Text>
    </HStack>
  );
};

// Real-time Transcription Component
const RealTimeTranscription: React.FC<{ callId: string }> = ({ callId }) => {
  const { liveCalls } = useRealtimeStore();
  const call = liveCalls.find(c => c.id === callId);
  
  if (!call) return null;

  return (
    <VStack align="stretch" spacing={3} maxH="400px" overflowY="auto">
      {call.transcription.map((segment) => (
        <Box
          key={segment.id}
          p={3}
          borderRadius="md"
          bg={segment.speaker === 'agent' ? 'blue.50' : 'gray.50'}
          borderLeft="4px solid"
          borderColor={segment.speaker === 'agent' ? 'blue.400' : 'gray.400'}
        >
          <HStack justify="space-between" mb={2}>
            <HStack spacing={2}>
              <Badge colorScheme={segment.speaker === 'agent' ? 'blue' : 'gray'}>
                {segment.speaker}
              </Badge>
              <Text fontSize="xs" color="gray.500">
                {new Date(segment.timestamp).toLocaleTimeString()}
              </Text>
            </HStack>
            <HStack spacing={2}>
              <Badge size="sm" colorScheme="green">
                {Math.round(segment.confidence * 100)}%
              </Badge>
              <SentimentIndicator sentiment={segment.sentiment > 0 ? 'positive' : segment.sentiment < -0.2 ? 'negative' : 'neutral'} score={Math.abs(segment.sentiment)} />
            </HStack>
          </HStack>
          <Text fontSize="sm">{segment.text}</Text>
          {segment.keywords.length > 0 && (
            <HStack mt={2} spacing={1}>
              {segment.keywords.map((keyword, i) => (
                <Badge key={i} size="sm" variant="outline">
                  {keyword}
                </Badge>
              ))}
            </HStack>
          )}
        </Box>
      ))}
    </VStack>
  );
};

// Call Analytics Component
const CallAnalytics: React.FC<{ callId: string }> = ({ callId }) => {
  const { liveCalls } = useRealtimeStore();
  const call = liveCalls.find(c => c.id === callId);
  
  if (!call) return null;

  const sentimentData = call.transcription.map((segment, index) => ({
    time: index,
    sentiment: segment.sentiment,
    confidence: segment.confidence,
  }));

  const callMetrics = {
    duration: Math.floor(call.duration / 60),
    avgSentiment: call.sentimentScore,
    confidence: call.transcription.reduce((acc, seg) => acc + seg.confidence, 0) / call.transcription.length,
    keywordCount: [...new Set(call.transcription.flatMap(seg => seg.keywords))].length,
  };

  return (
    <VStack spacing={6} align="stretch">
      {/* Call Metrics */}
      <SimpleGrid columns={4} spacing={4}>
        <Card>
          <CardBody textAlign="center">
            <Text fontSize="2xl" fontWeight="bold" color="blue.500">
              {callMetrics.duration}m
            </Text>
            <Text fontSize="sm" color="gray.500">Duration</Text>
          </CardBody>
        </Card>
        <Card>
          <CardBody textAlign="center">
            <Text fontSize="2xl" fontWeight="bold" color={callMetrics.avgSentiment > 0 ? 'green.500' : 'red.500'}>
              {callMetrics.avgSentiment.toFixed(2)}
            </Text>
            <Text fontSize="sm" color="gray.500">Avg Sentiment</Text>
          </CardBody>
        </Card>
        <Card>
          <CardBody textAlign="center">
            <Text fontSize="2xl" fontWeight="bold" color="purple.500">
              {Math.round(callMetrics.confidence * 100)}%
            </Text>
            <Text fontSize="sm" color="gray.500">Confidence</Text>
          </CardBody>
        </Card>
        <Card>
          <CardBody textAlign="center">
            <Text fontSize="2xl" fontWeight="bold" color="orange.500">
              {callMetrics.keywordCount}
            </Text>
            <Text fontSize="sm" color="gray.500">Keywords</Text>
          </CardBody>
        </Card>
      </SimpleGrid>

      {/* Sentiment Timeline */}
      <Card>
        <CardHeader>
          <Text fontWeight="semibold">Sentiment Timeline</Text>
        </CardHeader>
        <CardBody>
          <Box h="200px">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={sentimentData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis domain={[-1, 1]} />
                <RechartsTooltip />
                <Area
                  type="monotone"
                  dataKey="sentiment"
                  stroke="#3B82F6"
                  fill="#3B82F6"
                  fillOpacity={0.3}
                />
              </AreaChart>
            </ResponsiveContainer>
          </Box>
        </CardBody>
      </Card>
    </VStack>
  );
};

// Call Control Panel
const CallControlPanel: React.FC<{ callId: string }> = ({ callId }) => {
  const [isMuted, setIsMuted] = useState(false);
  const [volume, setVolume] = useState(80);
  const [isRecording, setIsRecording] = useState(true);
  
  const { liveCalls, sendMessage } = useRealtimeStore();
  const call = liveCalls.find(c => c.id === callId);
  
  if (!call) return null;

  const handleAction = (action: string, data?: any) => {
    sendMessage('call_action', { callId, action, data });
  };

  return (
    <VStack spacing={4} align="stretch">
      {/* Call Actions */}
      <SimpleGrid columns={3} spacing={3}>
        <Button
          leftIcon={<FiPhoneOff />}
          colorScheme="red"
          onClick={() => handleAction('end_call')}
        >
          End Call
        </Button>
        <Button
          leftIcon={call.status === 'on_hold' ? <FiPlay /> : <FiPause />}
          colorScheme={call.status === 'on_hold' ? 'green' : 'orange'}
          onClick={() => handleAction(call.status === 'on_hold' ? 'resume_call' : 'hold_call')}
        >
          {call.status === 'on_hold' ? 'Resume' : 'Hold'}
        </Button>
        <Button
          leftIcon={<FiSkipForward />}
          colorScheme="blue"
          onClick={() => handleAction('transfer_call')}
        >
          Transfer
        </Button>
      </SimpleGrid>

      {/* Audio Controls */}
      <Card>
        <CardHeader>
          <Text fontWeight="semibold">Audio Controls</Text>
        </CardHeader>
        <CardBody>
          <VStack spacing={4}>
            <HStack w="full" justify="space-between">
              <HStack spacing={2}>
                <IconButton
                  aria-label="Toggle mute"
                  icon={isMuted ? <FiMicOff /> : <FiMic />}
                  colorScheme={isMuted ? 'red' : 'green'}
                  onClick={() => setIsMuted(!isMuted)}
                />
                <Text fontSize="sm">Microphone</Text>
              </HStack>
              <Switch
                isChecked={!isMuted}
                onChange={(e) => setIsMuted(!e.target.checked)}
              />
            </HStack>

            <HStack w="full" spacing={4}>
              <FiVolume2 />
              <Slider
                value={volume}
                onChange={setVolume}
                min={0}
                max={100}
                flex={1}
              >
                <SliderTrack>
                  <SliderFilledTrack />
                </SliderTrack>
                <SliderThumb />
              </Slider>
              <Text fontSize="sm" w="40px">
                {volume}%
              </Text>
            </HStack>

            <HStack w="full" justify="space-between">
              <HStack spacing={2}>
                <IconButton
                  aria-label="Toggle recording"
                  icon={isRecording ? <FiPause /> : <FiPlay />}
                  colorScheme={isRecording ? 'red' : 'green'}
                  onClick={() => setIsRecording(!isRecording)}
                />
                <Text fontSize="sm">Recording</Text>
              </HStack>
              <Badge colorScheme={isRecording ? 'red' : 'gray'}>
                {isRecording ? 'REC' : 'STOPPED'}
              </Badge>
            </HStack>
          </VStack>
        </CardBody>
      </Card>

      {/* Call Notes */}
      <Card>
        <CardHeader>
          <Text fontWeight="semibold">Call Notes</Text>
        </CardHeader>
        <CardBody>
          <VStack spacing={3}>
            <Input placeholder="Add a note about this call..." />
            <Button size="sm" leftIcon={<FiSave />} colorScheme="blue" w="full">
              Save Note
            </Button>
          </VStack>
        </CardBody>
      </Card>
    </VStack>
  );
};

// Main Live Call Monitor Component
const LiveCallMonitor: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [selectedCall, setSelectedCall] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  
  const { isOpen: isCallDetailsOpen, onOpen: onCallDetailsOpen, onClose: onCallDetailsClose } = useDisclosure();
  
  const { liveCalls, liveAgents, connectionStatus } = useRealtimeStore();
  const { realTimeData } = useAdvancedAnalyticsStore();
  
  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');

  // Filter calls based on search and status
  const filteredCalls = useMemo(() => {
    return liveCalls.filter(call => {
      const matchesSearch = call.callerName.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           call.callerNumber.includes(searchTerm) ||
                           call.agentName.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesStatus = statusFilter === 'all' || call.status === statusFilter;
      return matchesSearch && matchesStatus;
    });
  }, [liveCalls, searchTerm, statusFilter]);

  // Calculate summary statistics
  const callStats = useMemo(() => {
    const total = liveCalls.length;
    const connected = liveCalls.filter(c => c.status === 'connected').length;
    const onHold = liveCalls.filter(c => c.status === 'on_hold').length;
    const avgDuration = liveCalls.reduce((acc, call) => acc + call.duration, 0) / total || 0;
    const avgSentiment = liveCalls.reduce((acc, call) => acc + call.sentimentScore, 0) / total || 0;
    
    return { total, connected, onHold, avgDuration, avgSentiment };
  }, [liveCalls]);

  const handleCallSelect = (callId: string) => {
    setSelectedCall(callId);
    onCallDetailsOpen();
  };

  const selectedCallData = selectedCall ? liveCalls.find(c => c.id === selectedCall) : null;

  return (
    <Box>
      {/* Header */}
      <VStack align="start" spacing={4} mb={6}>
        <HStack justify="space-between" w="full">
          <VStack align="start" spacing={1}>
            <Heading size="lg">Live Call Monitor</Heading>
            <HStack spacing={4}>
              <Badge
                colorScheme={connectionStatus === 'connected' ? 'green' : 'red'}
                variant="subtle"
              >
                {connectionStatus === 'connected' ? 'Live' : 'Disconnected'}
              </Badge>
              <Text fontSize="sm" color="gray.500">
                {callStats.total} active calls
              </Text>
            </HStack>
          </VStack>
          
          <HStack spacing={2}>
            <InputGroup size="sm" w="250px">
              <InputLeftElement>
                <FiSearch />
              </InputLeftElement>
              <Input
                placeholder="Search calls..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </InputGroup>
            
            <Select
              size="sm"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              w="150px"
            >
              <option value="all">All Status</option>
              <option value="ringing">Ringing</option>
              <option value="connected">Connected</option>
              <option value="on_hold">On Hold</option>
              <option value="transferring">Transferring</option>
            </Select>
            
            <IconButton
              aria-label="Toggle view"
              icon={viewMode === 'grid' ? <FiEye /> : <FiEyeOff />}
              size="sm"
              variant="outline"
              onClick={() => setViewMode(viewMode === 'grid' ? 'list' : 'grid')}
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
      </VStack>

      {/* Call Statistics */}
      <SimpleGrid columns={{ base: 2, md: 5 }} spacing={4} mb={6}>
        <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
          <CardBody textAlign="center">
            <Text fontSize="2xl" fontWeight="bold" color="blue.500">
              {callStats.total}
            </Text>
            <Text fontSize="sm" color="gray.500">Total Calls</Text>
          </CardBody>
        </Card>
        <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
          <CardBody textAlign="center">
            <Text fontSize="2xl" fontWeight="bold" color="green.500">
              {callStats.connected}
            </Text>
            <Text fontSize="sm" color="gray.500">Connected</Text>
          </CardBody>
        </Card>
        <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
          <CardBody textAlign="center">
            <Text fontSize="2xl" fontWeight="bold" color="orange.500">
              {callStats.onHold}
            </Text>
            <Text fontSize="sm" color="gray.500">On Hold</Text>
          </CardBody>
        </Card>
        <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
          <CardBody textAlign="center">
            <Text fontSize="2xl" fontWeight="bold" color="purple.500">
              {Math.floor(callStats.avgDuration / 60)}m
            </Text>
            <Text fontSize="sm" color="gray.500">Avg Duration</Text>
          </CardBody>
        </Card>
        <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
          <CardBody textAlign="center">
            <Text fontSize="2xl" fontWeight="bold" color={callStats.avgSentiment > 0 ? 'green.500' : 'red.500'}>
              {callStats.avgSentiment.toFixed(2)}
            </Text>
            <Text fontSize="sm" color="gray.500">Avg Sentiment</Text>
          </CardBody>
        </Card>
      </SimpleGrid>

      {/* Calls Display */}
      {viewMode === 'grid' ? (
        <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={4}>
          {filteredCalls.map((call) => (
            <Card
              key={call.id}
              bg={cardBg}
              borderColor={borderColor}
              borderWidth="1px"
              cursor="pointer"
              onClick={() => handleCallSelect(call.id)}
              _hover={{ shadow: 'md', transform: 'translateY(-2px)' }}
              transition="all 0.2s"
            >
              <CardHeader pb={2}>
                <HStack justify="space-between">
                  <HStack spacing={3}>
                    <Avatar size="sm" name={call.callerName} />
                    <VStack align="start" spacing={0}>
                      <Text fontWeight="semibold" fontSize="sm">
                        {call.callerName}
                      </Text>
                      <Text fontSize="xs" color="gray.500">
                        {call.callerNumber}
                      </Text>
                    </VStack>
                  </HStack>
                  <CallStatusBadge status={call.status} />
                </HStack>
              </CardHeader>
              <CardBody pt={0}>
                <VStack spacing={3} align="stretch">
                  <HStack justify="space-between">
                    <Text fontSize="sm" color="gray.600">Agent:</Text>
                    <Text fontSize="sm" fontWeight="medium">{call.agentName}</Text>
                  </HStack>
                  
                  <HStack justify="space-between">
                    <Text fontSize="sm" color="gray.600">Duration:</Text>
                    <Text fontSize="sm" fontWeight="medium">
                      {Math.floor(call.duration / 60)}:{(call.duration % 60).toString().padStart(2, '0')}
                    </Text>
                  </HStack>
                  
                  <HStack justify="space-between">
                    <Text fontSize="sm" color="gray.600">Sentiment:</Text>
                    <SentimentIndicator sentiment={call.sentiment} score={Math.abs(call.sentimentScore)} />
                  </HStack>
                  
                  {call.metadata.priority !== 'low' && (
                    <HStack justify="space-between">
                      <Text fontSize="sm" color="gray.600">Priority:</Text>
                      <Badge colorScheme={call.metadata.priority === 'urgent' ? 'red' : 'orange'}>
                        {call.metadata.priority}
                      </Badge>
                    </HStack>
                  )}
                  
                  <Progress
                    value={(call.duration / 1800) * 100}
                    size="sm"
                    colorScheme="blue"
                  />
                </VStack>
              </CardBody>
            </Card>
          ))}
        </SimpleGrid>
      ) : (
        <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
          <TableContainer>
            <Table size="sm">
              <Thead>
                <Tr>
                  <Th>Caller</Th>
                  <Th>Agent</Th>
                  <Th>Status</Th>
                  <Th>Duration</Th>
                  <Th>Sentiment</Th>
                  <Th>Priority</Th>
                  <Th>Actions</Th>
                </Tr>
              </Thead>
              <Tbody>
                {filteredCalls.map((call) => (
                  <Tr key={call.id}>
                    <Td>
                      <HStack spacing={2}>
                        <Avatar size="xs" name={call.callerName} />
                        <VStack align="start" spacing={0}>
                          <Text fontSize="sm" fontWeight="medium">
                            {call.callerName}
                          </Text>
                          <Text fontSize="xs" color="gray.500">
                            {call.callerNumber}
                          </Text>
                        </VStack>
                      </HStack>
                    </Td>
                    <Td>
                      <Text fontSize="sm">{call.agentName}</Text>
                    </Td>
                    <Td>
                      <CallStatusBadge status={call.status} />
                    </Td>
                    <Td>
                      <Text fontSize="sm">
                        {Math.floor(call.duration / 60)}:{(call.duration % 60).toString().padStart(2, '0')}
                      </Text>
                    </Td>
                    <Td>
                      <SentimentIndicator sentiment={call.sentiment} score={Math.abs(call.sentimentScore)} />
                    </Td>
                    <Td>
                      <Badge colorScheme={call.metadata.priority === 'urgent' ? 'red' : call.metadata.priority === 'high' ? 'orange' : 'gray'}>
                        {call.metadata.priority}
                      </Badge>
                    </Td>
                    <Td>
                      <HStack spacing={1}>
                        <IconButton
                          aria-label="View details"
                          icon={<FiEye />}
                          size="xs"
                          variant="ghost"
                          onClick={() => handleCallSelect(call.id)}
                        />
                        <IconButton
                          aria-label="Join call"
                          icon={<FiPhoneCall />}
                          size="xs"
                          variant="ghost"
                          colorScheme="green"
                        />
                      </HStack>
                    </Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
          </TableContainer>
        </Card>
      )}

      {/* Call Details Modal */}
      <Modal isOpen={isCallDetailsOpen} onClose={onCallDetailsClose} size="6xl">
        <ModalOverlay />
        <ModalContent maxW="90vw" maxH="90vh">
          <ModalHeader>
            <HStack justify="space-between">
              <VStack align="start" spacing={1}>
                <Text>Call Details: {selectedCallData?.callerName}</Text>
                <HStack spacing={4}>
                  <CallStatusBadge status={selectedCallData?.status || ''} />
                  <Text fontSize="sm" color="gray.500">
                    Duration: {Math.floor((selectedCallData?.duration || 0) / 60)}:{((selectedCallData?.duration || 0) % 60).toString().padStart(2, '0')}
                  </Text>
                </HStack>
              </VStack>
              <HStack spacing={2}>
                <IconButton
                  aria-label="Maximize"
                  icon={<FiMaximize2 />}
                  size="sm"
                  variant="ghost"
                />
                <IconButton
                  aria-label="Download"
                  icon={<FiDownload />}
                  size="sm"
                  variant="ghost"
                />
              </HStack>
            </HStack>
          </ModalHeader>
          <ModalCloseButton />
          <ModalBody pb={6}>
            {selectedCall && (
              <Grid templateColumns={{ base: '1fr', lg: '2fr 1fr' }} gap={6} h="70vh">
                <GridItem>
                  <Tabs h="full">
                    <TabList>
                      <Tab>Live Transcription</Tab>
                      <Tab>Analytics</Tab>
                      <Tab>Customer Info</Tab>
                    </TabList>
                    <TabPanels h="calc(100% - 40px)">
                      <TabPanel h="full" p={0} pt={4}>
                        <RealTimeTranscription callId={selectedCall} />
                      </TabPanel>
                      <TabPanel h="full" p={0} pt={4}>
                        <CallAnalytics callId={selectedCall} />
                      </TabPanel>
                      <TabPanel h="full" p={0} pt={4}>
                        <VStack spacing={4} align="stretch">
                          <Card>
                            <CardHeader>
                              <Text fontWeight="semibold">Customer Information</Text>
                            </CardHeader>
                            <CardBody>
                              <VStack spacing={3} align="stretch">
                                <HStack justify="space-between">
                                  <Text fontSize="sm" color="gray.600">Name:</Text>
                                  <Text fontSize="sm" fontWeight="medium">{selectedCallData?.callerName}</Text>
                                </HStack>
                                <HStack justify="space-between">
                                  <Text fontSize="sm" color="gray.600">Phone:</Text>
                                  <Text fontSize="sm" fontWeight="medium">{selectedCallData?.callerNumber}</Text>
                                </HStack>
                                <HStack justify="space-between">
                                  <Text fontSize="sm" color="gray.600">Customer Value:</Text>
                                  <Text fontSize="sm" fontWeight="medium">${selectedCallData?.metadata.customerValue.toLocaleString()}</Text>
                                </HStack>
                                <HStack justify="space-between">
                                  <Text fontSize="sm" color="gray.600">Previous Calls:</Text>
                                  <Text fontSize="sm" fontWeight="medium">{selectedCallData?.metadata.previousCalls}</Text>
                                </HStack>
                                <HStack justify="space-between">
                                  <Text fontSize="sm" color="gray.600">Source:</Text>
                                  <Badge>{selectedCallData?.metadata.source}</Badge>
                                </HStack>
                                {selectedCallData?.metadata.tags && (
                                  <VStack align="start" spacing={2}>
                                    <Text fontSize="sm" color="gray.600">Tags:</Text>
                                    <HStack spacing={1} flexWrap="wrap">
                                      {selectedCallData.metadata.tags.map((tag, i) => (
                                        <Badge key={i} size="sm" variant="outline">
                                          {tag}
                                        </Badge>
                                      ))}
                                    </HStack>
                                  </VStack>
                                )}
                              </VStack>
                            </CardBody>
                          </Card>
                        </VStack>
                      </TabPanel>
                    </TabPanels>
                  </Tabs>
                </GridItem>
                <GridItem>
                  <CallControlPanel callId={selectedCall} />
                </GridItem>
              </Grid>
            )}
          </ModalBody>
        </ModalContent>
      </Modal>
    </Box>
  );
};

export default LiveCallMonitor;