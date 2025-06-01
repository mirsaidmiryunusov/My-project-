import React, { useEffect, useState } from 'react';
import {
  Box,
  Card,
  CardBody,
  CardHeader,
  Text,
  SimpleGrid,
  Button,
  Progress,
  Badge,
  Table,
  Tbody,
  Td,
  Th,
  Thead,
  Tr,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ModalCloseButton,
  Alert,
  AlertIcon,
  Spinner,
  Divider,
  VStack,
  HStack,
  Icon,
  useDisclosure,
  useToast,
  Heading,
  Flex,
  Spacer,
  List,
  ListItem,
  ListIcon,
} from '@chakra-ui/react';
import {
  FaCheckCircle,
  FaTimes,
  FaArrowUp,
  FaCreditCard,
  FaReceipt,
  FaTrendingUp,
  FaPhone,
  FaBullhorn,
  FaUsers,
  FaClock,
  FaChartBar,
} from 'react-icons/fa';
import { useSubscriptionStore, formatPrice, getPlanColor, getSubscriptionStatusColor, formatUsageDisplay } from '../stores/subscriptionStore';

const SubscriptionPage: React.FC = () => {
  const {
    subscription,
    usage,
    plans,
    billingHistory,
    loading,
    error,
    fetchCurrentSubscription,
    fetchUsage,
    fetchPlans,
    fetchBillingHistory,
    updateSubscription,
    cancelSubscription,
    clearError,
  } = useSubscriptionStore();

  const { isOpen: isUpgradeOpen, onOpen: onUpgradeOpen, onClose: onUpgradeClose } = useDisclosure();
  const { isOpen: isCancelOpen, onOpen: onCancelOpen, onClose: onCancelClose } = useDisclosure();
  const [selectedPlan, setSelectedPlan] = useState<string>('');
  const toast = useToast();

  useEffect(() => {
    fetchCurrentSubscription();
    fetchUsage();
    fetchPlans();
    fetchBillingHistory();
  }, []);

  const handleUpgrade = async () => {
    if (!selectedPlan) return;
    
    const success = await updateSubscription(selectedPlan);
    if (success) {
      onUpgradeClose();
      setSelectedPlan('');
      toast({
        title: 'Plan upgraded successfully',
        status: 'success',
        duration: 3000,
        isClosable: true,
      });
    }
  };

  const handleCancel = async () => {
    const success = await cancelSubscription();
    if (success) {
      onCancelClose();
      toast({
        title: 'Subscription cancelled',
        status: 'info',
        duration: 3000,
        isClosable: true,
      });
    }
  };

  const getUsageColor = (percentage: number) => {
    if (percentage >= 90) return 'red';
    if (percentage >= 75) return 'orange';
    return 'blue';
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount / 100);
  };

  if (loading && !subscription) {
    return (
      <Flex justify="center" align="center" minH="400px">
        <Spinner size="xl" />
      </Flex>
    );
  }

  return (
    <Box p={6}>
      <Heading size="lg" mb={6}>
        Subscription Management
      </Heading>

      {error && (
        <Alert status="error" mb={6}>
          <AlertIcon />
          {error}
        </Alert>
      )}

      {/* Current Subscription */}
      <SimpleGrid columns={{ base: 1, lg: 3 }} spacing={6} mb={8}>
        <Box gridColumn={{ base: 1, lg: "1 / 3" }}>
          <Card>
            <CardHeader>
              <Flex justify="space-between" align="center">
                <Heading size="md">Current Plan</Heading>
                <Badge colorScheme={getSubscriptionStatusColor(subscription?.status || '')}>
                  {subscription?.status || 'Unknown'}
                </Badge>
              </Flex>
            </CardHeader>
            <CardBody>
              {subscription && (
                <VStack align="start" spacing={4}>
                  <Heading size="xl" color="blue.500">
                    {subscription.plan} Plan
                  </Heading>
                  
                  <Text color="gray.600">
                    Current billing period: {formatDate(subscription.currentPeriodStart)} - {formatDate(subscription.currentPeriodEnd)}
                  </Text>

                  <HStack spacing={4}>
                    <Button
                      colorScheme="blue"
                      leftIcon={<Icon as={FaArrowUp} />}
                      onClick={onUpgradeOpen}
                      isDisabled={subscription.plan === 'ENTERPRISE'}
                    >
                      Upgrade Plan
                    </Button>
                    
                    {subscription.plan !== 'FREE' && subscription.status === 'ACTIVE' && (
                      <Button
                        variant="outline"
                        colorScheme="red"
                        leftIcon={<Icon as={FaTimes} />}
                        onClick={onCancelOpen}
                      >
                        Cancel Subscription
                      </Button>
                    )}
                  </HStack>
                </VStack>
              )}
            </CardBody>
          </Card>
        </Box>

        <Card>
          <CardHeader>
            <Heading size="md">Quick Actions</Heading>
          </CardHeader>
          <CardBody>
            <VStack spacing={3} align="stretch">
              <Button
                variant="ghost"
                leftIcon={<Icon as={FaTrendingUp} />}
                justifyContent="flex-start"
                onClick={onUpgradeOpen}
              >
                Upgrade Plan
              </Button>
              
              <Button
                variant="ghost"
                leftIcon={<Icon as={FaCreditCard} />}
                justifyContent="flex-start"
              >
                Payment Methods
              </Button>
              
              <Button
                variant="ghost"
                leftIcon={<Icon as={FaReceipt} />}
                justifyContent="flex-start"
              >
                Download Invoice
              </Button>
            </VStack>
          </CardBody>
        </Card>
      </SimpleGrid>

      {/* Usage Statistics */}
      {usage && (
        <Card mb={8}>
          <CardHeader>
            <Heading size="md">Usage Statistics</Heading>
          </CardHeader>
          <CardBody>
            <SimpleGrid columns={{ base: 1, md: 2, lg: 5 }} spacing={6}>
              <Box>
                <HStack mb={2}>
                  <Icon as={FaPhone} color="blue.500" />
                  <Text fontWeight="semibold">Calls</Text>
                </HStack>
                <Text fontSize="lg" fontWeight="bold">
                  {formatUsageDisplay(usage.usage.calls.used, usage.usage.calls.limit)}
                </Text>
                <Progress
                  value={usage.usage.calls.percentage}
                  colorScheme={getUsageColor(usage.usage.calls.percentage)}
                  mt={2}
                />
              </Box>

              <Box>
                <HStack mb={2}>
                  <Icon as={FaBullhorn} color="blue.500" />
                  <Text fontWeight="semibold">Campaigns</Text>
                </HStack>
                <Text fontSize="lg" fontWeight="bold">
                  {formatUsageDisplay(usage.usage.campaigns.used, usage.usage.campaigns.limit)}
                </Text>
                <Progress
                  value={usage.usage.campaigns.percentage}
                  colorScheme={getUsageColor(usage.usage.campaigns.percentage)}
                  mt={2}
                />
              </Box>

              <Box>
                <HStack mb={2}>
                  <Icon as={FaUsers} color="blue.500" />
                  <Text fontWeight="semibold">Contacts</Text>
                </HStack>
                <Text fontSize="lg" fontWeight="bold">
                  {formatUsageDisplay(usage.usage.contacts.used, usage.usage.contacts.limit)}
                </Text>
                <Progress
                  value={usage.usage.contacts.percentage}
                  colorScheme={getUsageColor(usage.usage.contacts.percentage)}
                  mt={2}
                />
              </Box>

              <Box>
                <HStack mb={2}>
                  <Icon as={FaUsers} color="blue.500" />
                  <Text fontWeight="semibold">Users</Text>
                </HStack>
                <Text fontSize="lg" fontWeight="bold">
                  {formatUsageDisplay(usage.usage.users.used, usage.usage.users.limit)}
                </Text>
                <Progress
                  value={usage.usage.users.percentage}
                  colorScheme={getUsageColor(usage.usage.users.percentage)}
                  mt={2}
                />
              </Box>

              <Box>
                <HStack mb={2}>
                  <Icon as={FaClock} color="blue.500" />
                  <Text fontWeight="semibold">AI Minutes</Text>
                </HStack>
                <Text fontSize="lg" fontWeight="bold">
                  {formatUsageDisplay(usage.usage.aiMinutes.used, usage.usage.aiMinutes.limit)}
                </Text>
                <Progress
                  value={usage.usage.aiMinutes.percentage}
                  colorScheme={getUsageColor(usage.usage.aiMinutes.percentage)}
                  mt={2}
                />
              </Box>
            </SimpleGrid>
          </CardBody>
        </Card>
      )}

      {/* Billing History */}
      <Card>
        <CardHeader>
          <Heading size="md">Billing History</Heading>
        </CardHeader>
        <CardBody>
          <Table variant="simple">
            <Thead>
              <Tr>
                <Th>Date</Th>
                <Th>Amount</Th>
                <Th>Status</Th>
                <Th>Plan</Th>
                <Th>Actions</Th>
              </Tr>
            </Thead>
            <Tbody>
              {billingHistory.length === 0 ? (
                <Tr>
                  <Td colSpan={5} textAlign="center">
                    No billing history available
                  </Td>
                </Tr>
              ) : (
                billingHistory.map((payment) => (
                  <Tr key={payment.id}>
                    <Td>{formatDate(payment.createdAt)}</Td>
                    <Td>{formatCurrency(payment.amount)}</Td>
                    <Td>
                      <Badge colorScheme={payment.status === 'COMPLETED' ? 'green' : 'red'}>
                        {payment.status}
                      </Badge>
                    </Td>
                    <Td>{payment.subscription?.plan || 'N/A'}</Td>
                    <Td>
                      <Button size="sm" leftIcon={<Icon as={FaReceipt} />}>
                        Download
                      </Button>
                    </Td>
                  </Tr>
                ))
              )}
            </Tbody>
          </Table>
        </CardBody>
      </Card>

      {/* Upgrade Modal */}
      <Modal isOpen={isUpgradeOpen} onClose={onUpgradeClose} size="6xl">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Upgrade Your Plan</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={4}>
              {plans.map((plan) => (
                <Card
                  key={plan.id}
                  variant={selectedPlan === plan.id ? 'filled' : 'outline'}
                  cursor="pointer"
                  onClick={() => setSelectedPlan(plan.id)}
                  borderColor={selectedPlan === plan.id ? 'blue.500' : 'gray.200'}
                  borderWidth={selectedPlan === plan.id ? 2 : 1}
                >
                  <CardBody>
                    <VStack spacing={4} align="start">
                      <Heading size="md">{plan.name}</Heading>
                      <Box>
                        <Text fontSize="3xl" fontWeight="bold" color="blue.500">
                          {formatPrice(plan.price)}
                        </Text>
                        <Text color="gray.600">/month</Text>
                      </Box>
                      
                      <Divider />
                      
                      <List spacing={2}>
                        <ListItem>
                          <ListIcon as={FaCheckCircle} color="green.500" />
                          {plan.features.maxCalls === -1 ? 'Unlimited' : plan.features.maxCalls} calls/month
                        </ListItem>
                        <ListItem>
                          <ListIcon as={FaCheckCircle} color="green.500" />
                          {plan.features.maxCampaigns === -1 ? 'Unlimited' : plan.features.maxCampaigns} campaigns
                        </ListItem>
                        <ListItem>
                          <ListIcon as={FaCheckCircle} color="green.500" />
                          {plan.features.maxContacts === -1 ? 'Unlimited' : plan.features.maxContacts} contacts
                        </ListItem>
                        {plan.features.prioritySupport && (
                          <ListItem>
                            <ListIcon as={FaCheckCircle} color="green.500" />
                            Priority Support
                          </ListItem>
                        )}
                        {plan.features.advancedAnalytics && (
                          <ListItem>
                            <ListIcon as={FaChartBar} color="green.500" />
                            Advanced Analytics
                          </ListItem>
                        )}
                      </List>
                    </VStack>
                  </CardBody>
                </Card>
              ))}
            </SimpleGrid>
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onUpgradeClose}>
              Cancel
            </Button>
            <Button
              colorScheme="blue"
              onClick={handleUpgrade}
              isDisabled={!selectedPlan}
              isLoading={loading}
            >
              Upgrade
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>

      {/* Cancel Modal */}
      <Modal isOpen={isCancelOpen} onClose={onCancelClose}>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Cancel Subscription</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <Text>
              Are you sure you want to cancel your subscription? You will lose access to premium features
              at the end of your current billing period.
            </Text>
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onCancelClose}>
              Keep Subscription
            </Button>
            <Button
              colorScheme="red"
              onClick={handleCancel}
              isLoading={loading}
            >
              Cancel Subscription
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Box>
  );
};

export default SubscriptionPage;