/**
 * Error Fallback Component - Advanced Error Boundary UI
 * 
 * This component provides a comprehensive error fallback interface with
 * detailed error information, recovery options, and reporting capabilities.
 */

import React from 'react';
import {
  Box,
  VStack,
  HStack,
  Heading,
  Text,
  Button,
  Card,
  CardBody,
  Badge,
  Code,
  Divider,
  useColorModeValue,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
  IconButton,
  Tooltip,
} from '@chakra-ui/react';
import {
  FiAlertTriangle,
  FiRefreshCw,
  FiHome,
  FiMail,
  FiCopy,
  FiDownload,
  FiExternalLink,
  FiInfo,
} from 'react-icons/fi';

interface ErrorFallbackProps {
  error: Error;
  resetErrorBoundary: () => void;
}

export const ErrorFallback: React.FC<ErrorFallbackProps> = ({ error, resetErrorBoundary }) => {
  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  
  const handleCopyError = () => {
    const errorInfo = {
      message: error.message,
      stack: error.stack,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href,
    };
    
    navigator.clipboard.writeText(JSON.stringify(errorInfo, null, 2));
  };
  
  const handleReportError = () => {
    const subject = encodeURIComponent(`Dashboard Error Report: ${error.message}`);
    const body = encodeURIComponent(`
Error Details:
- Message: ${error.message}
- Timestamp: ${new Date().toISOString()}
- URL: ${window.location.href}
- User Agent: ${navigator.userAgent}

Stack Trace:
${error.stack}

Please describe what you were doing when this error occurred:
[Your description here]
    `);
    
    window.open(`mailto:support@geminivoiceconnect.com?subject=${subject}&body=${body}`);
  };
  
  const handleDownloadReport = () => {
    const errorReport = {
      message: error.message,
      stack: error.stack,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href,
      localStorage: { ...localStorage },
      sessionStorage: { ...sessionStorage },
    };
    
    const blob = new Blob([JSON.stringify(errorReport, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `error-report-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };
  
  return (
    <Box minH="100vh" bg={useColorModeValue('gray.50', 'gray.900')} p={8}>
      <VStack spacing={8} maxW="4xl" mx="auto">
        {/* Header */}
        <VStack spacing={4} textAlign="center">
          <Box p={4} bg="red.100" borderRadius="full">
            <FiAlertTriangle size={48} color="red" />
          </Box>
          <VStack spacing={2}>
            <Heading size="lg" color="red.500">
              Oops! Something went wrong
            </Heading>
            <Text color="gray.600" maxW="md">
              We encountered an unexpected error. Don't worry, our team has been notified and we're working on a fix.
            </Text>
          </VStack>
        </VStack>
        
        {/* Error Alert */}
        <Alert status="error" borderRadius="md" maxW="2xl">
          <AlertIcon />
          <Box flex="1">
            <AlertTitle>Error Details</AlertTitle>
            <AlertDescription mt={2}>
              <Code colorScheme="red" p={2} borderRadius="md" display="block">
                {error.message}
              </Code>
            </AlertDescription>
          </Box>
        </Alert>
        
        {/* Action Buttons */}
        <HStack spacing={4} flexWrap="wrap" justify="center">
          <Button
            leftIcon={<FiRefreshCw />}
            colorScheme="blue"
            onClick={resetErrorBoundary}
            size="lg"
          >
            Try Again
          </Button>
          <Button
            leftIcon={<FiHome />}
            variant="outline"
            onClick={() => window.location.href = '/'}
            size="lg"
          >
            Go Home
          </Button>
          <Button
            leftIcon={<FiMail />}
            variant="outline"
            onClick={handleReportError}
            size="lg"
          >
            Report Issue
          </Button>
        </HStack>
        
        {/* Detailed Error Information */}
        <Card bg={cardBg} borderColor={borderColor} borderWidth="1px" maxW="4xl" w="full">
          <CardBody>
            <VStack spacing={4} align="stretch">
              <HStack justify="space-between">
                <HStack spacing={2}>
                  <FiAlertTriangle />
                  <Text fontWeight="semibold">Technical Details</Text>
                </HStack>
                <HStack spacing={2}>
                  <Tooltip label="Copy error details">
                    <IconButton
                      aria-label="Copy error"
                      icon={<FiCopy />}
                      size="sm"
                      variant="ghost"
                      onClick={handleCopyError}
                    />
                  </Tooltip>
                  <Tooltip label="Download error report">
                    <IconButton
                      aria-label="Download report"
                      icon={<FiDownload />}
                      size="sm"
                      variant="ghost"
                      onClick={handleDownloadReport}
                    />
                  </Tooltip>
                </HStack>
              </HStack>
              
              <Divider />
              
              <Accordion allowToggle>
                <AccordionItem>
                  <AccordionButton>
                    <Box flex="1" textAlign="left">
                      <HStack spacing={2}>
                        <FiInfo />
                        <Text>Error Message</Text>
                      </HStack>
                    </Box>
                    <AccordionIcon />
                  </AccordionButton>
                  <AccordionPanel pb={4}>
                    <Code p={3} borderRadius="md" display="block" whiteSpace="pre-wrap">
                      {error.message}
                    </Code>
                  </AccordionPanel>
                </AccordionItem>
                
                <AccordionItem>
                  <AccordionButton>
                    <Box flex="1" textAlign="left">
                      <HStack spacing={2}>
                        <FiAlertTriangle />
                        <Text>Stack Trace</Text>
                      </HStack>
                    </Box>
                    <AccordionIcon />
                  </AccordionButton>
                  <AccordionPanel pb={4}>
                    <Code
                      p={3}
                      borderRadius="md"
                      display="block"
                      whiteSpace="pre-wrap"
                      fontSize="xs"
                      maxH="300px"
                      overflowY="auto"
                    >
                      {error.stack}
                    </Code>
                  </AccordionPanel>
                </AccordionItem>
                
                <AccordionItem>
                  <AccordionButton>
                    <Box flex="1" textAlign="left">
                      <HStack spacing={2}>
                        <FiExternalLink />
                        <Text>Environment Information</Text>
                      </HStack>
                    </Box>
                    <AccordionIcon />
                  </AccordionButton>
                  <AccordionPanel pb={4}>
                    <VStack spacing={2} align="stretch">
                      <HStack justify="space-between">
                        <Text fontSize="sm" color="gray.600">Timestamp:</Text>
                        <Text fontSize="sm">{new Date().toISOString()}</Text>
                      </HStack>
                      <HStack justify="space-between">
                        <Text fontSize="sm" color="gray.600">URL:</Text>
                        <Text fontSize="sm" fontFamily="mono">{window.location.href}</Text>
                      </HStack>
                      <HStack justify="space-between">
                        <Text fontSize="sm" color="gray.600">User Agent:</Text>
                        <Text fontSize="sm" fontFamily="mono" noOfLines={1}>
                          {navigator.userAgent}
                        </Text>
                      </HStack>
                      <HStack justify="space-between">
                        <Text fontSize="sm" color="gray.600">Viewport:</Text>
                        <Text fontSize="sm">
                          {window.innerWidth} × {window.innerHeight}
                        </Text>
                      </HStack>
                    </VStack>
                  </AccordionPanel>
                </AccordionItem>
              </Accordion>
            </VStack>
          </CardBody>
        </Card>
        
        {/* Help Information */}
        <Card bg={cardBg} borderColor={borderColor} borderWidth="1px" maxW="2xl" w="full">
          <CardBody>
            <VStack spacing={4} align="stretch">
              <Text fontWeight="semibold">What can you do?</Text>
              <VStack spacing={3} align="stretch">
                <HStack spacing={3}>
                  <Badge colorScheme="blue">1</Badge>
                  <Text fontSize="sm">
                    Try refreshing the page or clicking "Try Again" to see if the issue resolves itself.
                  </Text>
                </HStack>
                <HStack spacing={3}>
                  <Badge colorScheme="blue">2</Badge>
                  <Text fontSize="sm">
                    Check your internet connection and ensure you're connected to the network.
                  </Text>
                </HStack>
                <HStack spacing={3}>
                  <Badge colorScheme="blue">3</Badge>
                  <Text fontSize="sm">
                    Clear your browser cache and cookies, then try accessing the dashboard again.
                  </Text>
                </HStack>
                <HStack spacing={3}>
                  <Badge colorScheme="blue">4</Badge>
                  <Text fontSize="sm">
                    If the problem persists, please report the issue using the "Report Issue" button above.
                  </Text>
                </HStack>
              </VStack>
            </VStack>
          </CardBody>
        </Card>
        
        {/* Footer */}
        <Text fontSize="sm" color="gray.500" textAlign="center">
          GeminiVoiceConnect Dashboard v1.0.0 • Need help? Contact{' '}
          <Text as="span" color="blue.500" cursor="pointer" onClick={handleReportError}>
            support@geminivoiceconnect.com
          </Text>
        </Text>
      </VStack>
    </Box>
  );
};