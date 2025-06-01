/**
 * Call Management Page for Project GeminiVoiceConnect
 * 
 * This page provides comprehensive call management functionality including
 * active call monitoring, call history, analytics, and routing configuration.
 */

import React from 'react';
import {
  Box,
  Heading,
  Text,
  VStack,
  HStack,
  Button,
  Card,
  CardBody,
  Badge,
  SimpleGrid,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  StatArrow,
  useColorModeValue,
} from '@chakra-ui/react';
import { FiPhone, FiPhoneCall, FiPhoneIncoming, FiPhoneOutgoing } from 'react-icons/fi';
import { Routes, Route, useNavigate, useLocation } from 'react-router-dom';

const CallManagement: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const cardBg = useColorModeValue('white', 'gray.800');

  const isActive = (path: string) => location.pathname.includes(path);

  return (
    <Box>
      <VStack align="start" spacing={6}>
        {/* Header */}
        <VStack align="start" spacing={2}>
          <Heading size="lg">Call Management</Heading>
          <Text color="gray.500">
            Monitor active calls, analyze performance, and manage call routing
          </Text>
        </VStack>

        {/* Navigation Tabs */}
        <HStack spacing={4}>
          <Button
            variant={isActive('active') ? 'solid' : 'ghost'}
            leftIcon={<FiPhone />}
            onClick={() => navigate('/calls/active')}
          >
            Active Calls
          </Button>
          <Button
            variant={isActive('history') ? 'solid' : 'ghost'}
            leftIcon={<FiPhoneCall />}
            onClick={() => navigate('/calls/history')}
          >
            Call History
          </Button>
          <Button
            variant={isActive('analytics') ? 'solid' : 'ghost'}
            leftIcon={<FiPhoneIncoming />}
            onClick={() => navigate('/calls/analytics')}
          >
            Analytics
          </Button>
          <Button
            variant={isActive('routing') ? 'solid' : 'ghost'}
            leftIcon={<FiPhoneOutgoing />}
            onClick={() => navigate('/calls/routing')}
          >
            Routing
          </Button>
        </HStack>

        {/* Quick Stats */}
        <SimpleGrid columns={{ base: 1, md: 4 }} spacing={6} w="full">
          <Card bg={cardBg}>
            <CardBody>
              <Stat>
                <StatLabel>Active Calls</StatLabel>
                <StatNumber>23</StatNumber>
                <StatHelpText>
                  <StatArrow type="increase" />
                  12% from yesterday
                </StatHelpText>
              </Stat>
            </CardBody>
          </Card>
          
          <Card bg={cardBg}>
            <CardBody>
              <Stat>
                <StatLabel>Total Today</StatLabel>
                <StatNumber>1,247</StatNumber>
                <StatHelpText>
                  <StatArrow type="increase" />
                  8% from yesterday
                </StatHelpText>
              </Stat>
            </CardBody>
          </Card>
          
          <Card bg={cardBg}>
            <CardBody>
              <Stat>
                <StatLabel>Success Rate</StatLabel>
                <StatNumber>94.2%</StatNumber>
                <StatHelpText>
                  <StatArrow type="increase" />
                  2% from yesterday
                </StatHelpText>
              </Stat>
            </CardBody>
          </Card>
          
          <Card bg={cardBg}>
            <CardBody>
              <Stat>
                <StatLabel>Avg Duration</StatLabel>
                <StatNumber>4:32</StatNumber>
                <StatHelpText>
                  <StatArrow type="decrease" />
                  5% from yesterday
                </StatHelpText>
              </Stat>
            </CardBody>
          </Card>
        </SimpleGrid>

        {/* Content Area */}
        <Box w="full">
          <Routes>
            <Route path="active" element={<ActiveCallsView />} />
            <Route path="history" element={<CallHistoryView />} />
            <Route path="analytics" element={<CallAnalyticsView />} />
            <Route path="routing" element={<CallRoutingView />} />
            <Route index element={<ActiveCallsView />} />
          </Routes>
        </Box>
      </VStack>
    </Box>
  );
};

const ActiveCallsView: React.FC = () => {
  const cardBg = useColorModeValue('white', 'gray.800');

  return (
    <Card bg={cardBg}>
      <CardBody>
        <VStack align="start" spacing={4}>
          <Heading size="md">Active Calls</Heading>
          <Text color="gray.500">
            Real-time monitoring of ongoing calls across all modems
          </Text>
          
          {/* Mock active calls list */}
          <VStack spacing={3} w="full">
            {[1, 2, 3, 4, 5].map((call) => (
              <HStack key={call} justify="space-between" w="full" p={3} bg="gray.50" borderRadius="md">
                <VStack align="start" spacing={1}>
                  <Text fontWeight="semibold">Call #{call}</Text>
                  <Text fontSize="sm" color="gray.500">+1-555-0{call}23 → +1-555-9{call}87</Text>
                </VStack>
                <VStack align="end" spacing={1}>
                  <Badge colorScheme="green">Active</Badge>
                  <Text fontSize="sm" color="gray.500">2:3{call} elapsed</Text>
                </VStack>
              </HStack>
            ))}
          </VStack>
        </VStack>
      </CardBody>
    </Card>
  );
};

const CallHistoryView: React.FC = () => {
  const cardBg = useColorModeValue('white', 'gray.800');

  return (
    <Card bg={cardBg}>
      <CardBody>
        <VStack align="start" spacing={4}>
          <Heading size="md">Call History</Heading>
          <Text color="gray.500">
            Complete history of all calls with detailed analytics
          </Text>
          <Text>Call history functionality coming soon...</Text>
        </VStack>
      </CardBody>
    </Card>
  );
};

const CallAnalyticsView: React.FC = () => {
  const cardBg = useColorModeValue('white', 'gray.800');

  return (
    <Card bg={cardBg}>
      <CardBody>
        <VStack align="start" spacing={4}>
          <Heading size="md">Call Analytics</Heading>
          <Text color="gray.500">
            Advanced analytics and insights for call performance
          </Text>
          <Text>Call analytics functionality coming soon...</Text>
        </VStack>
      </CardBody>
    </Card>
  );
};

const CallRoutingView: React.FC = () => {
  const cardBg = useColorModeValue('white', 'gray.800');

  return (
    <Card bg={cardBg}>
      <CardBody>
        <VStack align="start" spacing={4}>
          <Heading size="md">Call Routing</Heading>
          <Text color="gray.500">
            Configure intelligent call routing rules and priorities
          </Text>
          <Text>Call routing configuration coming soon...</Text>
        </VStack>
      </CardBody>
    </Card>
  );
};

export default CallManagement;