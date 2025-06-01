import React, { useState, useEffect } from 'react';
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
  IconButton,
  useColorModeValue,
  Divider,
  Avatar,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  MenuDivider,
  useDisclosure,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
  Switch,
  FormControl,
  FormLabel,
  Select,
  Textarea,
  useToast,
  Tooltip,
  Flex,
  Spacer,
  SimpleGrid,
} from '@chakra-ui/react';
import {
  FiBell,
  FiX,
  FiCheck,
  FiSettings,
  FiMail,
  FiPhone,
  FiMessageSquare,
  FiAlertTriangle,
  FiInfo,
  FiCheckCircle,
  FiClock,
  FiUser,
  FiActivity,
  FiTrendingUp,
  FiTrendingDown,
  FiFilter,
  FiRefreshCw,
} from 'react-icons/fi';

interface Notification {
  id: string;
  type: 'info' | 'warning' | 'error' | 'success';
  title: string;
  message: string;
  timestamp: Date;
  read: boolean;
  category: 'system' | 'calls' | 'campaigns' | 'users' | 'security';
  priority: 'low' | 'medium' | 'high' | 'critical';
  actionRequired?: boolean;
  relatedUser?: string;
  relatedData?: any;
}

interface NotificationSettings {
  emailNotifications: boolean;
  pushNotifications: boolean;
  soundEnabled: boolean;
  categories: {
    system: boolean;
    calls: boolean;
    campaigns: boolean;
    users: boolean;
    security: boolean;
  };
  priority: {
    low: boolean;
    medium: boolean;
    high: boolean;
    critical: boolean;
  };
}

const NotificationCenter: React.FC = () => {
  const toast = useToast();
  const { isOpen, onOpen, onClose } = useDisclosure();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [filter, setFilter] = useState<'all' | 'unread' | 'priority'>('all');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [settings, setSettings] = useState<NotificationSettings>({
    emailNotifications: true,
    pushNotifications: true,
    soundEnabled: false,
    categories: {
      system: true,
      calls: true,
      campaigns: true,
      users: true,
      security: true,
    },
    priority: {
      low: true,
      medium: true,
      high: true,
      critical: true,
    },
  });

  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');

  // Generate sample notifications
  useEffect(() => {
    const sampleNotifications: Notification[] = [
      {
        id: '1',
        type: 'error',
        title: 'System Alert',
        message: 'High CPU usage detected (85%). Consider scaling resources.',
        timestamp: new Date(Date.now() - 5 * 60 * 1000),
        read: false,
        category: 'system',
        priority: 'critical',
        actionRequired: true,
      },
      {
        id: '2',
        type: 'success',
        title: 'Campaign Completed',
        message: 'Marketing campaign "Summer Sale" completed successfully with 95% success rate.',
        timestamp: new Date(Date.now() - 15 * 60 * 1000),
        read: false,
        category: 'campaigns',
        priority: 'medium',
        relatedData: { campaignId: 'camp_123', successRate: 95 },
      },
      {
        id: '3',
        type: 'warning',
        title: 'Call Queue Alert',
        message: '15 calls are waiting in queue. Average wait time: 3 minutes.',
        timestamp: new Date(Date.now() - 30 * 60 * 1000),
        read: true,
        category: 'calls',
        priority: 'high',
        actionRequired: true,
      },
      {
        id: '4',
        type: 'info',
        title: 'New User Registration',
        message: 'John Smith has registered as a new agent.',
        timestamp: new Date(Date.now() - 45 * 60 * 1000),
        read: true,
        category: 'users',
        priority: 'low',
        relatedUser: 'John Smith',
      },
      {
        id: '5',
        type: 'warning',
        title: 'Security Alert',
        message: 'Multiple failed login attempts detected from IP 192.168.1.100.',
        timestamp: new Date(Date.now() - 60 * 60 * 1000),
        read: false,
        category: 'security',
        priority: 'high',
        actionRequired: true,
      },
      {
        id: '6',
        type: 'success',
        title: 'Database Backup',
        message: 'Daily database backup completed successfully.',
        timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000),
        read: true,
        category: 'system',
        priority: 'low',
      },
    ];

    setNotifications(sampleNotifications);
  }, []);

  // Simulate real-time notifications
  useEffect(() => {
    const interval = setInterval(() => {
      if (Math.random() < 0.3) { // 30% chance every 10 seconds
        const newNotification: Notification = {
          id: Date.now().toString(),
          type: ['info', 'warning', 'error', 'success'][Math.floor(Math.random() * 4)] as any,
          title: 'Real-time Alert',
          message: 'This is a simulated real-time notification.',
          timestamp: new Date(),
          read: false,
          category: ['system', 'calls', 'campaigns', 'users', 'security'][Math.floor(Math.random() * 5)] as any,
          priority: ['low', 'medium', 'high', 'critical'][Math.floor(Math.random() * 4)] as any,
        };

        setNotifications(prev => [newNotification, ...prev]);

        // Show toast for high priority notifications
        if (newNotification.priority === 'critical' || newNotification.priority === 'high') {
          toast({
            title: newNotification.title,
            description: newNotification.message,
            status: newNotification.type,
            duration: 5000,
            isClosable: true,
          });
        }
      }
    }, 10000);

    return () => clearInterval(interval);
  }, [toast]);

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'error': return FiAlertTriangle;
      case 'warning': return FiAlertTriangle;
      case 'success': return FiCheckCircle;
      case 'info': return FiInfo;
      default: return FiInfo;
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'system': return FiActivity;
      case 'calls': return FiPhone;
      case 'campaigns': return FiTrendingUp;
      case 'users': return FiUser;
      case 'security': return FiAlertTriangle;
      default: return FiInfo;
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'error': return 'red';
      case 'warning': return 'yellow';
      case 'success': return 'green';
      case 'info': return 'blue';
      default: return 'gray';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical': return 'red';
      case 'high': return 'orange';
      case 'medium': return 'yellow';
      case 'low': return 'green';
      default: return 'gray';
    }
  };

  const markAsRead = (id: string) => {
    setNotifications(prev =>
      prev.map(notif =>
        notif.id === id ? { ...notif, read: true } : notif
      )
    );
  };

  const markAllAsRead = () => {
    setNotifications(prev =>
      prev.map(notif => ({ ...notif, read: true }))
    );
  };

  const deleteNotification = (id: string) => {
    setNotifications(prev => prev.filter(notif => notif.id !== id));
  };

  const clearAll = () => {
    setNotifications([]);
  };

  const filteredNotifications = notifications.filter(notif => {
    if (filter === 'unread' && notif.read) return false;
    if (filter === 'priority' && notif.priority !== 'high' && notif.priority !== 'critical') return false;
    if (categoryFilter !== 'all' && notif.category !== categoryFilter) return false;
    return true;
  });

  const unreadCount = notifications.filter(n => !n.read).length;
  const criticalCount = notifications.filter(n => n.priority === 'critical' && !n.read).length;

  return (
    <VStack spacing={6} align="stretch">
      {/* Header */}
      <HStack justify="space-between">
        <VStack align="start" spacing={1}>
          <HStack>
            <Text fontSize="xl" fontWeight="bold">Notification Center</Text>
            {unreadCount > 0 && (
              <Badge colorScheme="red" variant="solid" borderRadius="full">
                {unreadCount}
              </Badge>
            )}
            {criticalCount > 0 && (
              <Badge colorScheme="red" variant="outline">
                {criticalCount} Critical
              </Badge>
            )}
          </HStack>
          <Text fontSize="sm" color="gray.500">
            {notifications.length} total notifications
          </Text>
        </VStack>
        <HStack>
          <Menu>
            <MenuButton as={Button} size="sm" variant="outline" leftIcon={<FiFilter />}>
              Filter
            </MenuButton>
            <MenuList>
              <MenuItem onClick={() => setFilter('all')}>All Notifications</MenuItem>
              <MenuItem onClick={() => setFilter('unread')}>Unread Only</MenuItem>
              <MenuItem onClick={() => setFilter('priority')}>High Priority</MenuItem>
              <MenuDivider />
              <MenuItem onClick={() => setCategoryFilter('all')}>All Categories</MenuItem>
              <MenuItem onClick={() => setCategoryFilter('system')}>System</MenuItem>
              <MenuItem onClick={() => setCategoryFilter('calls')}>Calls</MenuItem>
              <MenuItem onClick={() => setCategoryFilter('campaigns')}>Campaigns</MenuItem>
              <MenuItem onClick={() => setCategoryFilter('users')}>Users</MenuItem>
              <MenuItem onClick={() => setCategoryFilter('security')}>Security</MenuItem>
            </MenuList>
          </Menu>
          <Button size="sm" variant="outline" onClick={markAllAsRead}>
            Mark All Read
          </Button>
          <Button size="sm" variant="outline" onClick={onOpen} leftIcon={<FiSettings />}>
            Settings
          </Button>
        </HStack>
      </HStack>

      {/* Quick Stats */}
      <SimpleGrid columns={{ base: 2, md: 4 }} spacing={4}>
        <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
          <CardBody>
            <VStack spacing={2}>
              <Text fontSize="2xl" fontWeight="bold" color="blue.500">
                {notifications.length}
              </Text>
              <Text fontSize="sm" color="gray.500">Total</Text>
            </VStack>
          </CardBody>
        </Card>
        <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
          <CardBody>
            <VStack spacing={2}>
              <Text fontSize="2xl" fontWeight="bold" color="red.500">
                {unreadCount}
              </Text>
              <Text fontSize="sm" color="gray.500">Unread</Text>
            </VStack>
          </CardBody>
        </Card>
        <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
          <CardBody>
            <VStack spacing={2}>
              <Text fontSize="2xl" fontWeight="bold" color="orange.500">
                {criticalCount}
              </Text>
              <Text fontSize="sm" color="gray.500">Critical</Text>
            </VStack>
          </CardBody>
        </Card>
        <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
          <CardBody>
            <VStack spacing={2}>
              <Text fontSize="2xl" fontWeight="bold" color="green.500">
                {notifications.filter(n => n.actionRequired && !n.read).length}
              </Text>
              <Text fontSize="sm" color="gray.500">Action Required</Text>
            </VStack>
          </CardBody>
        </Card>
      </SimpleGrid>

      {/* Notifications List */}
      <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
        <CardHeader>
          <HStack justify="space-between">
            <Text fontSize="lg" fontWeight="bold">Recent Notifications</Text>
            <Button size="sm" variant="ghost" onClick={clearAll} leftIcon={<FiX />}>
              Clear All
            </Button>
          </HStack>
        </CardHeader>
        <CardBody>
          <VStack spacing={4} align="stretch">
            {filteredNotifications.length === 0 ? (
              <Text textAlign="center" color="gray.500" py={8}>
                No notifications match your current filter.
              </Text>
            ) : (
              filteredNotifications.map((notification, index) => (
                <Box key={notification.id}>
                  <HStack spacing={4} align="start">
                    <Avatar
                      size="sm"
                      icon={React.createElement(getTypeIcon(notification.type))}
                      bg={`${getTypeColor(notification.type)}.500`}
                    />
                    <VStack align="start" spacing={1} flex={1}>
                      <HStack justify="space-between" w="full">
                        <HStack>
                          <Text fontWeight={notification.read ? 'normal' : 'bold'}>
                            {notification.title}
                          </Text>
                          <Badge
                            colorScheme={getPriorityColor(notification.priority)}
                            size="sm"
                            variant="subtle"
                          >
                            {notification.priority}
                          </Badge>
                          <Badge
                            colorScheme="gray"
                            size="sm"
                            variant="outline"
                          >
                            {notification.category}
                          </Badge>
                          {notification.actionRequired && (
                            <Badge colorScheme="red" size="sm">
                              Action Required
                            </Badge>
                          )}
                        </HStack>
                        <HStack>
                          <Text fontSize="xs" color="gray.500">
                            {notification.timestamp.toLocaleTimeString()}
                          </Text>
                          {!notification.read && (
                            <Tooltip label="Mark as read">
                              <IconButton
                                size="xs"
                                variant="ghost"
                                icon={<FiCheck />}
                                onClick={() => markAsRead(notification.id)}
                                aria-label="Mark as read"
                              />
                            </Tooltip>
                          )}
                          <Tooltip label="Delete">
                            <IconButton
                              size="xs"
                              variant="ghost"
                              icon={<FiX />}
                              onClick={() => deleteNotification(notification.id)}
                              aria-label="Delete notification"
                            />
                          </Tooltip>
                        </HStack>
                      </HStack>
                      <Text fontSize="sm" color="gray.600">
                        {notification.message}
                      </Text>
                      {notification.relatedUser && (
                        <Text fontSize="xs" color="blue.500">
                          Related to: {notification.relatedUser}
                        </Text>
                      )}
                    </VStack>
                  </HStack>
                  {index < filteredNotifications.length - 1 && <Divider mt={4} />}
                </Box>
              ))
            )}
          </VStack>
        </CardBody>
      </Card>

      {/* Settings Modal */}
      <Modal isOpen={isOpen} onClose={onClose} size="lg">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Notification Settings</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <VStack spacing={6} align="stretch">
              {/* General Settings */}
              <Box>
                <Text fontSize="lg" fontWeight="bold" mb={4}>General Settings</Text>
                <VStack spacing={4} align="stretch">
                  <FormControl display="flex" alignItems="center">
                    <FormLabel htmlFor="email-notifications" mb="0">
                      Email Notifications
                    </FormLabel>
                    <Spacer />
                    <Switch
                      id="email-notifications"
                      isChecked={settings.emailNotifications}
                      onChange={(e) => setSettings(prev => ({ ...prev, emailNotifications: e.target.checked }))}
                    />
                  </FormControl>
                  <FormControl display="flex" alignItems="center">
                    <FormLabel htmlFor="push-notifications" mb="0">
                      Push Notifications
                    </FormLabel>
                    <Spacer />
                    <Switch
                      id="push-notifications"
                      isChecked={settings.pushNotifications}
                      onChange={(e) => setSettings(prev => ({ ...prev, pushNotifications: e.target.checked }))}
                    />
                  </FormControl>
                  <FormControl display="flex" alignItems="center">
                    <FormLabel htmlFor="sound-enabled" mb="0">
                      Sound Alerts
                    </FormLabel>
                    <Spacer />
                    <Switch
                      id="sound-enabled"
                      isChecked={settings.soundEnabled}
                      onChange={(e) => setSettings(prev => ({ ...prev, soundEnabled: e.target.checked }))}
                    />
                  </FormControl>
                </VStack>
              </Box>

              <Divider />

              {/* Category Settings */}
              <Box>
                <Text fontSize="lg" fontWeight="bold" mb={4}>Categories</Text>
                <SimpleGrid columns={2} spacing={4}>
                  {Object.entries(settings.categories).map(([category, enabled]) => (
                    <FormControl key={category} display="flex" alignItems="center">
                      <FormLabel htmlFor={`category-${category}`} mb="0" textTransform="capitalize">
                        {category}
                      </FormLabel>
                      <Spacer />
                      <Switch
                        id={`category-${category}`}
                        isChecked={enabled}
                        onChange={(e) => setSettings(prev => ({
                          ...prev,
                          categories: { ...prev.categories, [category]: e.target.checked }
                        }))}
                      />
                    </FormControl>
                  ))}
                </SimpleGrid>
              </Box>

              <Divider />

              {/* Priority Settings */}
              <Box>
                <Text fontSize="lg" fontWeight="bold" mb={4}>Priority Levels</Text>
                <SimpleGrid columns={2} spacing={4}>
                  {Object.entries(settings.priority).map(([priority, enabled]) => (
                    <FormControl key={priority} display="flex" alignItems="center">
                      <FormLabel htmlFor={`priority-${priority}`} mb="0" textTransform="capitalize">
                        {priority}
                      </FormLabel>
                      <Spacer />
                      <Switch
                        id={`priority-${priority}`}
                        isChecked={enabled}
                        onChange={(e) => setSettings(prev => ({
                          ...prev,
                          priority: { ...prev.priority, [priority]: e.target.checked }
                        }))}
                      />
                    </FormControl>
                  ))}
                </SimpleGrid>
              </Box>
            </VStack>
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onClose}>
              Cancel
            </Button>
            <Button colorScheme="blue" onClick={onClose}>
              Save Settings
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </VStack>
  );
};

export default NotificationCenter;