/**
 * Sidebar Component for Project GeminiVoiceConnect Dashboard
 * 
 * This component provides the main navigation sidebar with intelligent menu
 * organization, role-based access control, and real-time status indicators.
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  VStack,
  HStack,
  Text,
  Icon,
  Collapse,
  useColorModeValue,
  Badge,
  Tooltip,
  Divider,
  Avatar,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  useDisclosure,
  Flex,
  IconButton,
} from '@chakra-ui/react';
import {
  FiHome,
  FiPhone,
  FiMessageSquare,
  FiUsers,
  FiBarChart3,
  FiDollarSign,
  FiSettings,
  FiShield,
  FiActivity,
  FiTrendingUp,
  FiTarget,
  FiMail,
  FiCalendar,
  FiFileText,
  FiDatabase,
  FiCpu,
  FiWifi,
  FiChevronDown,
  FiChevronRight,
  FiLogOut,
  FiUser,
  FiBell,
  FiHelpCircle,
} from 'react-icons/fi';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '../../stores/authStore';
import { useSystemStore } from '../../stores/systemStore';

interface MenuItem {
  id: string;
  label: string;
  icon: React.ElementType;
  path?: string;
  children?: MenuItem[];
  badge?: string;
  badgeColor?: string;
  requiredRole?: string[];
  isNew?: boolean;
}

const menuItems: MenuItem[] = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    icon: FiHome,
    path: '/',
  },
  {
    id: 'calls',
    label: 'Call Management',
    icon: FiPhone,
    children: [
      { id: 'active-calls', label: 'Active Calls', icon: FiActivity, path: '/calls/active' },
      { id: 'call-history', label: 'Call History', icon: FiFileText, path: '/calls/history' },
      { id: 'call-analytics', label: 'Call Analytics', icon: FiBarChart3, path: '/calls/analytics' },
      { id: 'call-routing', label: 'Call Routing', icon: FiTarget, path: '/calls/routing' },
    ],
  },
  {
    id: 'sms',
    label: 'SMS Management',
    icon: FiMessageSquare,
    children: [
      { id: 'sms-campaigns', label: 'SMS Campaigns', icon: FiMail, path: '/sms/campaigns' },
      { id: 'sms-templates', label: 'Templates', icon: FiFileText, path: '/sms/templates' },
      { id: 'sms-analytics', label: 'SMS Analytics', icon: FiTrendingUp, path: '/sms/analytics' },
      { id: 'sms-compliance', label: 'Compliance', icon: FiShield, path: '/sms/compliance' },
    ],
  },
  {
    id: 'customers',
    label: 'Customer Management',
    icon: FiUsers,
    children: [
      { id: 'customer-list', label: 'Customer List', icon: FiUsers, path: '/customers/list' },
      { id: 'customer-segments', label: 'Segmentation', icon: FiTarget, path: '/customers/segments' },
      { id: 'customer-analytics', label: 'Analytics', icon: FiBarChart3, path: '/customers/analytics' },
      { id: 'customer-journey', label: 'Journey Mapping', icon: FiActivity, path: '/customers/journey' },
    ],
  },
  {
    id: 'campaigns',
    label: 'Campaign Management',
    icon: FiTarget,
    children: [
      { id: 'campaign-list', label: 'All Campaigns', icon: FiTarget, path: '/campaigns/list' },
      { id: 'campaign-builder', label: 'Campaign Builder', icon: FiSettings, path: '/campaigns/builder' },
      { id: 'campaign-scheduler', label: 'Scheduler', icon: FiCalendar, path: '/campaigns/scheduler' },
      { id: 'campaign-performance', label: 'Performance', icon: FiTrendingUp, path: '/campaigns/performance' },
    ],
  },
  {
    id: 'revenue',
    label: 'Revenue Optimization',
    icon: FiDollarSign,
    children: [
      { id: 'revenue-dashboard', label: 'Revenue Dashboard', icon: FiBarChart3, path: '/revenue/dashboard' },
      { id: 'pricing-optimization', label: 'Pricing Optimization', icon: FiTrendingUp, path: '/revenue/pricing' },
      { id: 'upsell-opportunities', label: 'Upsell Opportunities', icon: FiTarget, path: '/revenue/upsell' },
      { id: 'clv-analysis', label: 'CLV Analysis', icon: FiDollarSign, path: '/revenue/clv' },
    ],
    isNew: true,
  },
  {
    id: 'analytics',
    label: 'Analytics & Reports',
    icon: FiBarChart3,
    children: [
      { id: 'real-time-analytics', label: 'Real-time Analytics', icon: FiActivity, path: '/analytics/realtime' },
      { id: 'performance-reports', label: 'Performance Reports', icon: FiFileText, path: '/analytics/performance' },
      { id: 'custom-reports', label: 'Custom Reports', icon: FiSettings, path: '/analytics/custom' },
      { id: 'predictive-insights', label: 'Predictive Insights', icon: FiTrendingUp, path: '/analytics/predictive' },
    ],
  },
  {
    id: 'system',
    label: 'System Management',
    icon: FiCpu,
    children: [
      { id: 'modem-status', label: 'Modem Status', icon: FiWifi, path: '/system/modems' },
      { id: 'system-health', label: 'System Health', icon: FiActivity, path: '/system/health' },
      { id: 'gpu-monitoring', label: 'GPU Monitoring', icon: FiCpu, path: '/system/gpu' },
      { id: 'system-logs', label: 'System Logs', icon: FiFileText, path: '/system/logs' },
    ],
    requiredRole: ['admin', 'operator'],
  },
  {
    id: 'settings',
    label: 'Settings',
    icon: FiSettings,
    children: [
      { id: 'tenant-settings', label: 'Tenant Settings', icon: FiSettings, path: '/settings/tenant' },
      { id: 'user-management', label: 'User Management', icon: FiUsers, path: '/settings/users' },
      { id: 'integrations', label: 'Integrations', icon: FiDatabase, path: '/settings/integrations' },
      { id: 'compliance-settings', label: 'Compliance', icon: FiShield, path: '/settings/compliance' },
    ],
    requiredRole: ['admin'],
  },
];

interface SidebarProps {
  isCollapsed: boolean;
  onToggle: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ isCollapsed, onToggle }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuthStore();
  const { systemStatus, notifications } = useSystemStore();
  
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());
  const { isOpen: isUserMenuOpen, onOpen: onUserMenuOpen, onClose: onUserMenuClose } = useDisclosure();
  
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  const textColor = useColorModeValue('gray.700', 'gray.200');
  const activeColor = useColorModeValue('blue.500', 'blue.300');
  const hoverBg = useColorModeValue('gray.50', 'gray.700');

  useEffect(() => {
    // Auto-expand menu items based on current path
    const currentPath = location.pathname;
    menuItems.forEach(item => {
      if (item.children) {
        const hasActiveChild = item.children.some(child => child.path === currentPath);
        if (hasActiveChild) {
          setExpandedItems(prev => new Set([...prev, item.id]));
        }
      }
    });
  }, [location.pathname]);

  const toggleExpanded = (itemId: string) => {
    setExpandedItems(prev => {
      const newSet = new Set(prev);
      if (newSet.has(itemId)) {
        newSet.delete(itemId);
      } else {
        newSet.add(itemId);
      }
      return newSet;
    });
  };

  const isItemActive = (path?: string) => {
    return path === location.pathname;
  };

  const hasPermission = (requiredRole?: string[]) => {
    if (!requiredRole) return true;
    return requiredRole.includes(user?.role || '');
  };

  const getNotificationCount = () => {
    return notifications.filter(n => !n.read).length;
  };

  const renderMenuItem = (item: MenuItem, level: number = 0) => {
    if (!hasPermission(item.requiredRole)) {
      return null;
    }

    const isExpanded = expandedItems.has(item.id);
    const isActive = isItemActive(item.path);
    const hasChildren = item.children && item.children.length > 0;

    return (
      <Box key={item.id} w="full">
        <Tooltip
          label={isCollapsed ? item.label : ''}
          placement="right"
          isDisabled={!isCollapsed}
        >
          <HStack
            w="full"
            px={isCollapsed ? 2 : 4}
            py={3}
            cursor="pointer"
            borderRadius="md"
            bg={isActive ? activeColor : 'transparent'}
            color={isActive ? 'white' : textColor}
            _hover={{
              bg: isActive ? activeColor : hoverBg,
            }}
            onClick={() => {
              if (hasChildren) {
                toggleExpanded(item.id);
              } else if (item.path) {
                navigate(item.path);
              }
            }}
            pl={level > 0 ? (isCollapsed ? 2 : 6) : (isCollapsed ? 2 : 4)}
          >
            <Icon as={item.icon} boxSize={5} />
            
            {!isCollapsed && (
              <>
                <Text flex={1} fontSize="sm" fontWeight={isActive ? 'semibold' : 'medium'}>
                  {item.label}
                </Text>
                
                {item.isNew && (
                  <Badge colorScheme="green" size="sm">
                    NEW
                  </Badge>
                )}
                
                {item.badge && (
                  <Badge colorScheme={item.badgeColor || 'blue'} size="sm">
                    {item.badge}
                  </Badge>
                )}
                
                {hasChildren && (
                  <Icon
                    as={isExpanded ? FiChevronDown : FiChevronRight}
                    boxSize={4}
                  />
                )}
              </>
            )}
          </HStack>
        </Tooltip>

        {hasChildren && !isCollapsed && (
          <Collapse in={isExpanded} animateOpacity>
            <VStack spacing={0} align="stretch" mt={1}>
              {item.children!.map(child => renderMenuItem(child, level + 1))}
            </VStack>
          </Collapse>
        )}
      </Box>
    );
  };

  const renderUserSection = () => (
    <Box px={isCollapsed ? 2 : 4} py={3}>
      <Menu isOpen={isUserMenuOpen} onOpen={onUserMenuOpen} onClose={onUserMenuClose}>
        <MenuButton
          as={Box}
          cursor="pointer"
          w="full"
        >
          <HStack spacing={isCollapsed ? 0 : 3}>
            <Avatar
              size={isCollapsed ? 'sm' : 'md'}
              name={user?.name}
              src={user?.avatar}
            />
            
            {!isCollapsed && (
              <VStack align="start" spacing={0} flex={1}>
                <Text fontSize="sm" fontWeight="semibold" color={textColor}>
                  {user?.name}
                </Text>
                <Text fontSize="xs" color="gray.500">
                  {user?.role}
                </Text>
              </VStack>
            )}
            
            {!isCollapsed && (
              <Icon as={FiChevronDown} boxSize={4} color={textColor} />
            )}
          </HStack>
        </MenuButton>
        
        <MenuList>
          <MenuItem icon={<FiUser />} onClick={() => navigate('/profile')}>
            Profile Settings
          </MenuItem>
          <MenuItem icon={<FiBell />} onClick={() => navigate('/notifications')}>
            Notifications
            {getNotificationCount() > 0 && (
              <Badge ml={2} colorScheme="red" size="sm">
                {getNotificationCount()}
              </Badge>
            )}
          </MenuItem>
          <MenuItem icon={<FiHelpCircle />} onClick={() => navigate('/help')}>
            Help & Support
          </MenuItem>
          <Divider />
          <MenuItem icon={<FiLogOut />} onClick={logout} color="red.500">
            Logout
          </MenuItem>
        </MenuList>
      </Menu>
    </Box>
  );

  const renderSystemStatus = () => {
    if (isCollapsed) return null;

    return (
      <Box px={4} py={3}>
        <Text fontSize="xs" fontWeight="semibold" color="gray.500" mb={2}>
          SYSTEM STATUS
        </Text>
        
        <VStack spacing={2} align="stretch">
          <HStack justify="space-between">
            <Text fontSize="xs" color={textColor}>Modems Online</Text>
            <Badge
              colorScheme={systemStatus.modemsOnline > 70 ? 'green' : 'orange'}
              size="sm"
            >
              {systemStatus.modemsOnline}/80
            </Badge>
          </HStack>
          
          <HStack justify="space-between">
            <Text fontSize="xs" color={textColor}>GPU Usage</Text>
            <Badge
              colorScheme={systemStatus.gpuUsage < 80 ? 'green' : 'red'}
              size="sm"
            >
              {systemStatus.gpuUsage}%
            </Badge>
          </HStack>
          
          <HStack justify="space-between">
            <Text fontSize="xs" color={textColor}>Active Calls</Text>
            <Badge colorScheme="blue" size="sm">
              {systemStatus.activeCalls}
            </Badge>
          </HStack>
        </VStack>
      </Box>
    );
  };

  return (
    <Box
      w={isCollapsed ? '16' : '64'}
      h="100vh"
      bg={bgColor}
      borderRight="1px"
      borderColor={borderColor}
      transition="width 0.2s"
      position="fixed"
      left={0}
      top={0}
      zIndex={1000}
      display="flex"
      flexDirection="column"
    >
      {/* Header */}
      <Box px={isCollapsed ? 2 : 4} py={4} borderBottom="1px" borderColor={borderColor}>
        <HStack justify="space-between">
          {!isCollapsed && (
            <Text fontSize="lg" fontWeight="bold" color={activeColor}>
              GeminiVoice
            </Text>
          )}
          <IconButton
            aria-label="Toggle sidebar"
            icon={<Icon as={isCollapsed ? FiChevronRight : FiChevronDown} />}
            size="sm"
            variant="ghost"
            onClick={onToggle}
          />
        </HStack>
      </Box>

      {/* Navigation Menu */}
      <Box flex={1} overflowY="auto" py={4}>
        <VStack spacing={1} align="stretch">
          {menuItems.map(item => renderMenuItem(item))}
        </VStack>
      </Box>

      {/* System Status */}
      {renderSystemStatus()}
      
      {!isCollapsed && <Divider />}

      {/* User Section */}
      {renderUserSection()}
    </Box>
  );
};

export default Sidebar;