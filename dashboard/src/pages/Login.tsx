/**
 * Login Page for Project GeminiVoiceConnect Dashboard
 * 
 * This page provides user authentication with modern design,
 * security features, and seamless user experience.
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Container,
  FormControl,
  FormLabel,
  Input,
  VStack,
  HStack,
  Text,
  Heading,
  Alert,
  AlertIcon,
  InputGroup,
  InputRightElement,
  IconButton,
  Checkbox,
  Link,
  Divider,
  useColorModeValue,
  useToast,
  Card,
  CardBody,
  Image,
  Flex,
  Spacer,
} from '@chakra-ui/react';
import { FiEye, FiEyeOff, FiMail, FiLock, FiShield } from 'react-icons/fi';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';

const Login: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { login, isLoading, error, clearError } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();
  const toast = useToast();

  const bgColor = useColorModeValue('gray.50', 'gray.900');
  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');

  // Get the intended destination from location state
  const from = (location.state as any)?.from?.pathname || '/';

  useEffect(() => {
    // Clear any existing errors when component mounts
    clearError();
  }, [clearError]);

  useEffect(() => {
    // Show error toast if there's an error
    if (error) {
      toast({
        title: 'Login Failed',
        description: error,
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    }
  }, [error, toast]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!email || !password) {
      toast({
        title: 'Validation Error',
        description: 'Please enter both email and password',
        status: 'warning',
        duration: 3000,
        isClosable: true,
      });
      return;
    }

    setIsSubmitting(true);
    
    try {
      await login(email, password);
      
      toast({
        title: 'Login Successful',
        description: 'Welcome to GeminiVoiceConnect!',
        status: 'success',
        duration: 3000,
        isClosable: true,
      });
      
      // Navigate to intended destination or dashboard
      navigate(from, { replace: true });
    } catch (err) {
      // Error is handled by the store and useEffect above
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDemoLogin = async () => {
    setEmail('admin@geminivoice.com');
    setPassword('demo123');
    
    // Trigger login with demo credentials
    setTimeout(() => {
      handleSubmit(new Event('submit') as any);
    }, 100);
  };

  return (
    <Box minH="100vh" bg={bgColor}>
      <Container maxW="lg" py={{ base: '12', md: '24' }} px={{ base: '0', sm: '8' }}>
        <VStack spacing={8}>
          {/* Header */}
          <VStack spacing={4} textAlign="center">
            <Box>
              <Heading size="xl" color="brand.500" fontWeight="bold">
                GeminiVoiceConnect
              </Heading>
              <Text color="gray.500" fontSize="lg" mt={2}>
                AI-Powered Call Center Management
              </Text>
            </Box>
            
            <HStack spacing={2} color="gray.400" fontSize="sm">
              <FiShield />
              <Text>Enterprise-grade security</Text>
            </HStack>
          </VStack>

          {/* Login Card */}
          <Card
            bg={cardBg}
            borderColor={borderColor}
            borderWidth="1px"
            shadow="lg"
            w="full"
            maxW="md"
          >
            <CardBody p={8}>
              <VStack spacing={6}>
                <VStack spacing={2} textAlign="center">
                  <Heading size="md">Sign in to your account</Heading>
                  <Text color="gray.500" fontSize="sm">
                    Enter your credentials to access the dashboard
                  </Text>
                </VStack>

                {/* Demo Login Notice */}
                <Alert status="info" borderRadius="md">
                  <AlertIcon />
                  <VStack align="start" spacing={1} flex={1}>
                    <Text fontSize="sm" fontWeight="semibold">
                      Demo Mode Available
                    </Text>
                    <Text fontSize="xs">
                      Click "Demo Login" to try the system with sample data
                    </Text>
                  </VStack>
                </Alert>

                {/* Login Form */}
                <Box as="form" onSubmit={handleSubmit} w="full">
                  <VStack spacing={4}>
                    <FormControl isRequired>
                      <FormLabel fontSize="sm" fontWeight="medium">
                        Email Address
                      </FormLabel>
                      <InputGroup>
                        <Input
                          type="email"
                          value={email}
                          onChange={(e) => setEmail(e.target.value)}
                          placeholder="Enter your email"
                          size="lg"
                          bg={useColorModeValue('gray.50', 'gray.700')}
                        />
                      </InputGroup>
                    </FormControl>

                    <FormControl isRequired>
                      <FormLabel fontSize="sm" fontWeight="medium">
                        Password
                      </FormLabel>
                      <InputGroup>
                        <Input
                          type={showPassword ? 'text' : 'password'}
                          value={password}
                          onChange={(e) => setPassword(e.target.value)}
                          placeholder="Enter your password"
                          size="lg"
                          bg={useColorModeValue('gray.50', 'gray.700')}
                        />
                        <InputRightElement h="full">
                          <IconButton
                            aria-label={showPassword ? 'Hide password' : 'Show password'}
                            icon={showPassword ? <FiEyeOff /> : <FiEye />}
                            variant="ghost"
                            size="sm"
                            onClick={() => setShowPassword(!showPassword)}
                          />
                        </InputRightElement>
                      </InputGroup>
                    </FormControl>

                    <HStack justify="space-between" w="full">
                      <Checkbox
                        isChecked={rememberMe}
                        onChange={(e) => setRememberMe(e.target.checked)}
                        size="sm"
                      >
                        <Text fontSize="sm">Remember me</Text>
                      </Checkbox>
                      <Link
                        fontSize="sm"
                        color="brand.500"
                        fontWeight="medium"
                        _hover={{ textDecoration: 'underline' }}
                      >
                        Forgot password?
                      </Link>
                    </HStack>

                    <VStack spacing={3} w="full">
                      <Button
                        type="submit"
                        colorScheme="brand"
                        size="lg"
                        w="full"
                        isLoading={isLoading || isSubmitting}
                        loadingText="Signing in..."
                        leftIcon={<FiLock />}
                      >
                        Sign In
                      </Button>

                      <HStack w="full">
                        <Divider />
                        <Text fontSize="sm" color="gray.500" px={2}>
                          OR
                        </Text>
                        <Divider />
                      </HStack>

                      <Button
                        variant="outline"
                        size="lg"
                        w="full"
                        onClick={handleDemoLogin}
                        isDisabled={isLoading || isSubmitting}
                        leftIcon={<FiShield />}
                      >
                        Demo Login
                      </Button>
                    </VStack>
                  </VStack>
                </Box>

                {/* Additional Info */}
                <VStack spacing={2} textAlign="center" pt={4}>
                  <Text fontSize="xs" color="gray.500">
                    By signing in, you agree to our{' '}
                    <Link color="brand.500" fontWeight="medium">
                      Terms of Service
                    </Link>{' '}
                    and{' '}
                    <Link color="brand.500" fontWeight="medium">
                      Privacy Policy
                    </Link>
                  </Text>
                </VStack>
              </VStack>
            </CardBody>
          </Card>

          {/* Features */}
          <VStack spacing={4} textAlign="center" maxW="md">
            <Text fontSize="sm" color="gray.500" fontWeight="medium">
              Trusted by leading call centers worldwide
            </Text>
            
            <HStack spacing={8} justify="center" wrap="wrap">
              <VStack spacing={1}>
                <Text fontSize="lg" fontWeight="bold" color="brand.500">
                  99.9%
                </Text>
                <Text fontSize="xs" color="gray.500">
                  Uptime
                </Text>
              </VStack>
              <VStack spacing={1}>
                <Text fontSize="lg" fontWeight="bold" color="brand.500">
                  &lt;200ms
                </Text>
                <Text fontSize="xs" color="gray.500">
                  Latency
                </Text>
              </VStack>
              <VStack spacing={1}>
                <Text fontSize="lg" fontWeight="bold" color="brand.500">
                  80+
                </Text>
                <Text fontSize="xs" color="gray.500">
                  Modems
                </Text>
              </VStack>
              <VStack spacing={1}>
                <Text fontSize="lg" fontWeight="bold" color="brand.500">
                  24/7
                </Text>
                <Text fontSize="xs" color="gray.500">
                  Support
                </Text>
              </VStack>
            </HStack>
          </VStack>
        </VStack>
      </Container>
    </Box>
  );
};

export default Login;