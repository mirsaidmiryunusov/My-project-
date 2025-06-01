/**
 * Header Component for Project GeminiVoiceConnect Dashboard
 * 
 * This component provides the main header with search, notifications,
 * quick actions, and real-time system status indicators.
 */

import React, { useState } from 'react';
import {
  Box,
  HStack,
  VStack,
  Text,
  Input,
  InputGroup,
  InputLeftElement,
  IconButton,
  Badge,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  MenuDivider,
  useColorModeValue,
  useColorMode,
  Tooltip,
  Button,
  Popover,
  PopoverTrigger,
  PopoverContent,
  PopoverHeader,
  PopoverBody,
  PopoverCloseButton,
  Flex,
  Spacer,
  useDisclosure,
} from '@chakra-ui/react';
import {
  FiSearch,
  FiBell,
  FiMoon,
  FiSun,
  FiSettings,
  FiRefreshCw,
  FiActivity,
  FiAlertTriangle,
  FiCheckCircle,
  FiInfo,
  FiX,
  FiPhone,
  FiMessageSquare,
  FiUsers,
  FiTrendingUp,
} from 'react-icons/fi';
import { useSystemStore } from '../../stores/systemStore';
import { useNotificationStore } from '../../stores/notificationStore';

interface HeaderProps {
  sidebarWidth: number;
}

const Header: React.FC<HeaderProps> = ({ sidebarWidth }) => {
  const { colorMode, toggleColorMode } = useColorMode();
  const { systemStatus, refreshSystemStatus } = useSystemStore();
  const { notifications, markAsRead, markAllAsRead } = useNotificationStore();
  const [searchQuery, setSearchQuery] = useState('');
  const { isOpen: isNotificationOpen, onOpen: onNotificationOpen, onClose: onNotificationClose } = useDisclosure();

  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  const textColor = useColorModeValue('gray.700', 'gray.200');

  const unreadNotifications = notifications.filter(n => !n.read);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'green';
      case 'warning': return 'yellow';
      case 'critical': return 'red';
      default: return 'gray';
    }
  };

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'success': return FiCheckCircle;
      case 'warning': return FiAlertTriangle;
      case 'error': return FiAlertTriangle;
      case 'info': return FiInfo;
      default: return FiBell;
    }
  };

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (days > 0) return `${days}d ago`;
    if (hours > 0) return `${hours}h ago`;
    if (minutes > 0) return `${minutes}m ago`;
    return 'Just now';
  };

  const renderQuickStats = () => (
    <HStack spacing={6}>
      <Tooltip label="Active Calls">
        <HStack spacing={2}>
          <FiPhone color={getStatusColor('healthy')} />
          <VStack spacing={0} align="start">
            <Text fontSize="sm" fontWeight="semibold" color={textColor}>
              {systemStatus.activeCalls}
            </Text>
            <Text fontSize="xs" color="gray.500">
              Active Calls
            </Text>
          </VStack>
        </HStack>
      </Tooltip>

      <Tooltip label="SMS Queue">
        <HStack spacing={2}>
          <FiMessageSquare color={getStatusColor('healthy')} />
          <VStack spacing={0} align="start">
            <Text fontSize="sm" fontWeight="semibold" color={textColor}>
              {systemStatus.smsQueue}
            </Text>
            <Text fontSize="xs" color="gray.500">
              SMS Queue
            </Text>
          </VStack>
        </HStack>
      </Tooltip>

      <Tooltip label="Online Agents">
        <HStack spacing={2}>
          <FiUsers color={getStatusColor('healthy')} />
          <VStack spacing={0} align="start">
            <Text fontSize="sm" fontWeight="semibold" color={textColor}>
              {systemStatus.onlineAgents}
            </Text>
            <Text fontSize="xs" color="gray.500">
              Online Agents
            </Text>
          </VStack>
        </HStack>
      </Tooltip>

      <Tooltip label="Today's Revenue">
        <HStack spacing={2}>
          <FiTrendingUp color={getStatusColor('healthy')} />
          <VStack spacing={0} align="start">
            <Text fontSize="sm" fontWeight="semibold" color={textColor}>
              ${systemStatus.todayRevenue?.toLocaleString()}
            </Text>
            <Text fontSize="xs" color="gray.500">
              Today's Revenue
            </Text>
          </VStack>
        </HStack>
      </Tooltip>
    </HStack>
  );

  const renderNotifications = () => (
    <Popover
      isOpen={isNotificationOpen}
      onOpen={onNotificationOpen}
      onClose={onNotificationClose}
      placement="bottom-end"
    >
      <PopoverTrigger>
        <IconButton
          aria-label="Notifications"
          icon={<FiBell />}
          variant="ghost"
          position="relative"
        >
          {unreadNotifications.length > 0 && (
            <Badge
              colorScheme="red"
              position="absolute"
              top="-1"
              right="-1"
              fontSize="xs"
              borderRadius="full"
            >
              {unreadNotifications.length}
            </Badge>
          )}
        </IconButton>
      </PopoverTrigger>
      
      <PopoverContent w="400px">
        <PopoverHeader>
          <HStack justify="space-between">
            <Text fontWeight="semibold">Notifications</Text>
            {unreadNotifications.length > 0 && (
              <Button size="xs" variant="ghost" onClick={markAllAsRead}>
                Mark all as read
              </Button>
            )}
          </HStack>
        </PopoverHeader>
        <PopoverCloseButton />
        
        <PopoverBody p={0} maxH="400px" overflowY="auto">
          {notifications.length === 0 ? (
            <Box p={4} textAlign="center" color="gray.500">
              No notifications
            </Box>
          ) : (
            <VStack spacing={0} align="stretch">
              {notifications.slice(0, 10).map((notification) => {
                const IconComponent = getNotificationIcon(notification.type);
                return (
                  <Box
                    key={notification.id}
                    p={3}
                    borderBottom="1px"
                    borderColor={borderColor}
                    bg={notification.read ? 'transparent' : useColorModeValue('blue.50', 'blue.900')}
                    cursor="pointer"
                    _hover={{ bg: useColorModeValue('gray.50', 'gray.700') }}
                    onClick={() => markAsRead(notification.id)}
                  >
                    <HStack align="start" spacing={3}>
                      <IconComponent
                        size={16}
                        color={getStatusColor(notification.type)}
                      />
                      <VStack align="start" spacing={1} flex={1}>
                        <Text fontSize="sm" fontWeight={notification.read ? 'normal' : 'semibold'}>
                          {notification.title}
                        </Text>
                        <Text fontSize="xs" color="gray.500" noOfLines={2}>
                          {notification.message}
                        </Text>
                        <Text fontSize="xs" color="gray.400">
                          {formatTime(notification.timestamp)}
                        </Text>
                      </VStack>
                      {!notification.read && (
                        <Box w={2} h={2} bg="blue.500" borderRadius="full" />
                      )}
                    </HStack>
                  </Box>
                );
              })}
            </VStack>
          )}
        </PopoverBody>
      </PopoverContent>
    </Popover>
  );

  const renderSystemHealth = () => (
    <Tooltip label={`System Health: ${systemStatus.overallHealth}`}>
      <HStack spacing={2}>
        <FiActivity color={getStatusColor(systemStatus.overallHealth)} />
        <Badge colorScheme={getStatusColor(systemStatus.overallHealth)} size="sm">
          {systemStatus.overallHealth.toUpperCase()}
        </Badge>
      </HStack>
    </Tooltip>
  );

  return (
    <Box
      position="fixed"
      top={0}
      left={sidebarWidth}
      right={0}
      h="16"
      bg={bgColor}
      borderBottom="1px"
      borderColor={borderColor}
      zIndex={999}
      px={6}
      py={4}
    >
      <Flex align="center" h="full">
        {/* Search */}
        <InputGroup maxW="400px" mr={6}>
          <InputLeftElement>
            <FiSearch color="gray.400" />
          </InputLeftElement>
          <Input
            placeholder="Search customers, campaigns, calls..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            bg={useColorModeValue('gray.50', 'gray.700')}
            border="none"
            _focus={{
              bg: useColorModeValue('white', 'gray.600'),
              boxShadow: 'md',
            }}
          />
        </InputGroup>

        {/* Quick Stats */}
        {renderQuickStats()}

        <Spacer />

        {/* Right Side Actions */}
        <HStack spacing={4}>
          {/* System Health */}
          {renderSystemHealth()}

          {/* Refresh Button */}
          <Tooltip label="Refresh System Status">
            <IconButton
              aria-label="Refresh"
              icon={<FiRefreshCw />}
              variant="ghost"
              onClick={refreshSystemStatus}
            />
          </Tooltip>

          {/* Color Mode Toggle */}
          <Tooltip label={`Switch to ${colorMode === 'light' ? 'dark' : 'light'} mode`}>
            <IconButton
              aria-label="Toggle color mode"
              icon={colorMode === 'light' ? <FiMoon /> : <FiSun />}
              variant="ghost"
              onClick={toggleColorMode}
            />
          </Tooltip>

          {/* Notifications */}
          {renderNotifications()}

          {/* Settings */}
          <Tooltip label="Settings">
            <IconButton
              aria-label="Settings"
              icon={<FiSettings />}
              variant="ghost"
            />
          </Tooltip>
        </HStack>
      </Flex>
    </Box>
  );
};

export default Header;