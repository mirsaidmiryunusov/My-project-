/**
 * Main Layout Component for Project GeminiVoiceConnect Dashboard
 * 
 * This component provides the overall layout structure with sidebar,
 * header, and main content area with responsive design.
 */

import React, { useState } from 'react';
import { Box, useColorModeValue } from '@chakra-ui/react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Header from './Header';

const Layout: React.FC = () => {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  
  const bgColor = useColorModeValue('gray.50', 'gray.900');
  const sidebarWidth = isSidebarCollapsed ? 64 : 256; // 16 * 4 = 64px, 64 * 4 = 256px

  const toggleSidebar = () => {
    setIsSidebarCollapsed(!isSidebarCollapsed);
  };

  return (
    <Box minH="100vh" bg={bgColor}>
      {/* Sidebar */}
      <Sidebar isCollapsed={isSidebarCollapsed} onToggle={toggleSidebar} />
      
      {/* Header */}
      <Header sidebarWidth={sidebarWidth} />
      
      {/* Main Content */}
      <Box
        ml={`${sidebarWidth}px`}
        mt="16" // Header height
        p={6}
        transition="margin-left 0.2s"
        minH="calc(100vh - 4rem)"
      >
        <Outlet />
      </Box>
    </Box>
  );
};

export default Layout;