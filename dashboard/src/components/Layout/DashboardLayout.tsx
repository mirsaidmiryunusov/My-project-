/**
 * Dashboard Layout Component - Main Layout for Dashboard Pages
 * 
 * This component provides the main layout structure for dashboard pages
 * including sidebar navigation, header, and content area.
 */

import React, { useState } from 'react';
import {
  Box,
  Flex,
  VStack,
  HStack,
  Text,
  Button,
  IconButton,
  Avatar,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  MenuDivider,
  useColorModeValue,
  useBreakpointValue,
  Drawer,
  DrawerBody,
  DrawerHeader,
  DrawerOverlay,
  DrawerContent,
  DrawerCloseButton,
  useDisclosure,
  Badge,
  Tooltip,
} from '@chakra-ui/react';
import {
  FiMenu,
  FiHome,
  FiPhone,
  FiMessageSquare,
  FiUsers,
  FiBarChart,
  FiDollarSign,
  FiSettings,
  FiLogOut,
  FiUser,
  FiBell,
  FiSearch,
  FiMoon,
  FiSun,
  FiMaximize2,
  FiCpu,
  FiActivity,
  FiMonitor,
} from 'react-icons/fi';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '../../stores/authStore';
import { useSystemStore } from '../../stores/systemStore';

// Navigation Items
const navigationItems = [
  { name: 'Dashboard', icon: FiHome, path: '/' },
  { name: 'Advanced Dashboard', icon: FiCpu, path: '/advanced' },
  { name: 'Live Calls', icon: FiPhone, path: '/calls' },
  { name: 'SMS Management', icon: FiMessageSquare, path: '/sms' },
  { name: 'Customers', icon: FiUsers, path: '/customers' },
  { name: 'Analytics', icon: FiBarChart, path: '/analytics' },
  { name: 'Revenue', icon: FiDollarSign, path: '/revenue' },
  { name: 'System', icon: FiMonitor, path: '/system' },
  { name: 'Settings', icon: FiSettings, path: '/settings' },
];

// Sidebar Component
const Sidebar: React.FC<{ isOpen?: boolean; onClose?: () => void }> = ({ isOpen, onClose }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { systemStatus } = useSystemStore();
  
  const sidebarBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  
  const handleNavigation = (path: string) => {
    navigate(path);
    if (onClose) onClose();
  };
  
  const sidebarContent = (
    <VStack spacing={0} align="stretch" h="full">
      {/* Logo */}
      <Box p={6} borderBottom="1px" borderColor={borderColor}>
        <VStack spacing={2}>
          <Text fontSize="xl" fontWeight="bold" color="blue.500">
            GeminiVoice
          </Text>
          <Text fontSize="sm" color="gray.500">
            AI Call Center
          </Text>
        </VStack>
      </Box>
      
      {/* System Status */}
      <Box p={4} borderBottom="1px" borderColor={borderColor}>
        <VStack spacing={2} align="stretch">
          <HStack justify="space-between">
            <Text fontSize="sm" color="gray.500">System Status</Text>
            <Badge
              colorScheme={systemStatus.overallHealth === 'healthy' ? 'green' : systemStatus.overallHealth === 'warning' ? 'yellow' : 'red'}
              size="sm"
            >
              {systemStatus.overallHealth}
            </Badge>
          </HStack>
          <HStack justify="space-between">
            <Text fontSize="xs" color="gray.500">Active Calls</Text>
            <Text fontSize="xs" fontWeight="medium">{systemStatus.activeCalls}</Text>
          </HStack>
          <HStack justify="space-between">
            <Text fontSize="xs" color="gray.500">Modems Online</Text>
            <Text fontSize="xs" fontWeight="medium">
              {systemStatus.modemsOnline}/{systemStatus.totalModems}
            </Text>
          </HStack>
        </VStack>
      </Box>
      
      {/* Navigation */}
      <VStack spacing={1} align="stretch" flex={1} p={4}>
        {navigationItems.map((item) => {
          const isActive = location.pathname === item.path;
          return (
            <Button
              key={item.path}
              leftIcon={<item.icon />}
              variant={isActive ? 'solid' : 'ghost'}
              colorScheme={isActive ? 'blue' : 'gray'}
              justifyContent="flex-start"
              onClick={() => handleNavigation(item.path)}
              size="sm"
            >
              {item.name}
            </Button>
          );
        })}
      </VStack>
      
      {/* Footer */}
      <Box p={4} borderTop="1px" borderColor={borderColor}>
        <Text fontSize="xs" color="gray.500" textAlign="center">
          v1.0.0 • GPU Accelerated
        </Text>
      </Box>
    </VStack>
  );
  
  return (
    <Box
      bg={sidebarBg}
      borderRight="1px"
      borderColor={borderColor}
      w="250px"
      h="100vh"
      position="fixed"
      left={0}
      top={0}
      zIndex={1000}
      display={{ base: 'none', md: 'block' }}
    >
      {sidebarContent}
    </Box>
  );
};

// Mobile Sidebar
const MobileSidebar: React.FC<{ isOpen: boolean; onClose: () => void }> = ({ isOpen, onClose }) => {
  return (
    <Drawer isOpen={isOpen} placement="left" onClose={onClose}>
      <DrawerOverlay />
      <DrawerContent>
        <DrawerCloseButton />
        <DrawerHeader>Navigation</DrawerHeader>
        <DrawerBody p={0}>
          <Sidebar isOpen={isOpen} onClose={onClose} />
        </DrawerBody>
      </DrawerContent>
    </Drawer>
  );
};

// Header Component
const Header: React.FC<{ onMenuClick: () => void }> = ({ onMenuClick }) => {
  const { user, logout } = useAuthStore();
  const { systemStatus } = useSystemStore();
  const navigate = useNavigate();
  
  const headerBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  
  const handleLogout = () => {
    logout();
    navigate('/login');
  };
  
  return (
    <Box
      bg={headerBg}
      borderBottom="1px"
      borderColor={borderColor}
      px={6}
      py={4}
      position="fixed"
      top={0}
      left={{ base: 0, md: '250px' }}
      right={0}
      zIndex={999}
      h="70px"
    >
      <Flex justify="space-between" align="center" h="full">
        {/* Left Side */}
        <HStack spacing={4}>
          <IconButton
            aria-label="Open menu"
            icon={<FiMenu />}
            variant="ghost"
            onClick={onMenuClick}
            display={{ base: 'flex', md: 'none' }}
          />
          
          <VStack spacing={0} align="start">
            <Text fontSize="lg" fontWeight="semibold">
              Dashboard
            </Text>
            <HStack spacing={4}>
              <Badge
                colorScheme={systemStatus.overallHealth === 'healthy' ? 'green' : 'red'}
                variant="subtle"
                size="sm"
              >
                System {systemStatus.overallHealth}
              </Badge>
              <Text fontSize="sm" color="gray.500">
                {systemStatus.activeCalls} active calls
              </Text>
            </HStack>
          </VStack>
        </HStack>
        
        {/* Right Side */}
        <HStack spacing={4}>
          <Tooltip label="Search">
            <IconButton
              aria-label="Search"
              icon={<FiSearch />}
              variant="ghost"
              size="sm"
            />
          </Tooltip>
          
          <Tooltip label="Notifications">
            <IconButton
              aria-label="Notifications"
              icon={<FiBell />}
              variant="ghost"
              size="sm"
            />
          </Tooltip>
          
          <Tooltip label="Advanced Dashboard">
            <IconButton
              aria-label="Advanced Dashboard"
              icon={<FiMaximize2 />}
              variant="ghost"
              size="sm"
              onClick={() => navigate('/advanced')}
            />
          </Tooltip>
          
          {/* User Menu */}
          <Menu>
            <MenuButton>
              <HStack spacing={2}>
                <Avatar size="sm" name={`${user?.firstName} ${user?.lastName}`} />
                <VStack spacing={0} align="start" display={{ base: 'none', md: 'flex' }}>
                  <Text fontSize="sm" fontWeight="medium">
                    {`${user?.firstName} ${user?.lastName}`}
                  </Text>
                  <Text fontSize="xs" color="gray.500">
                    {user?.role}
                  </Text>
                </VStack>
              </HStack>
            </MenuButton>
            <MenuList>
              <MenuItem icon={<FiUser />}>Profile</MenuItem>
              <MenuItem icon={<FiSettings />}>Settings</MenuItem>
              <MenuItem icon={<FiCpu />} onClick={() => navigate('/advanced')}>
                Advanced Dashboard
              </MenuItem>
              <MenuDivider />
              <MenuItem icon={<FiLogOut />} onClick={handleLogout}>
                Logout
              </MenuItem>
            </MenuList>
          </Menu>
        </HStack>
      </Flex>
    </Box>
  );
};

// Main Dashboard Layout
export const DashboardLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isOpen, onOpen, onClose } = useDisclosure();
  const isMobile = useBreakpointValue({ base: true, md: false });
  
  return (
    <Box minH="100vh" bg={useColorModeValue('gray.50', 'gray.900')}>
      {/* Sidebar */}
      {!isMobile && <Sidebar />}
      
      {/* Mobile Sidebar */}
      {isMobile && <MobileSidebar isOpen={isOpen} onClose={onClose} />}
      
      {/* Header */}
      <Header onMenuClick={onOpen} />
      
      {/* Main Content */}
      <Box
        ml={{ base: 0, md: '250px' }}
        mt="70px"
        p={6}
        minH="calc(100vh - 70px)"
      >
        {children}
      </Box>
    </Box>
  );
};