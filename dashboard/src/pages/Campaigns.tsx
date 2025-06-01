import React, { useEffect, useState } from 'react';
import {
  Box,
  Heading,
  Text,
  VStack,
  HStack,
  Button,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
  IconButton,
  useDisclosure,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
  FormControl,
  FormLabel,
  Input,
  Textarea,
  Select,
  NumberInput,
  NumberInputField,
  useToast,
  Alert,
  AlertIcon,
  Spinner,
  Card,
  CardHeader,
  CardBody,
  SimpleGrid,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  Progress,
  Flex,
  Spacer,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  useColorModeValue,
} from '@chakra-ui/react';
import {
  FiPlus,
  FiEdit,
  FiTrash2,
  FiPlay,
  FiPause,
  FiMoreVertical,
  FiUsers,
  FiPhone,
  FiTrendingUp,
  FiDollarSign,
  FiRefreshCw,
} from 'react-icons/fi';
import { useDashboardStore, getStatusColor, formatMetricValue } from '../stores/dashboardStore';

interface CampaignFormData {
  name: string;
  targetAudience: string;
  script: string;
  budget: number;
  status: 'active' | 'paused' | 'completed' | 'draft';
}

const Campaigns: React.FC = () => {
  const {
    campaigns,
    loading,
    error,
    fetchCampaigns,
    createCampaign,
    updateCampaign,
    deleteCampaign,
    clearError,
  } = useDashboardStore();

  const { isOpen, onOpen, onClose } = useDisclosure();
  const [editingCampaign, setEditingCampaign] = useState<any>(null);
  const [formData, setFormData] = useState<CampaignFormData>({
    name: '',
    targetAudience: '',
    script: '',
    budget: 0,
    status: 'draft',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const toast = useToast();
  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');

  useEffect(() => {
    fetchCampaigns();
  }, [fetchCampaigns]);

  const handleCreateCampaign = () => {
    setEditingCampaign(null);
    setFormData({
      name: '',
      targetAudience: '',
      script: '',
      budget: 0,
      status: 'draft',
    });
    onOpen();
  };

  const handleEditCampaign = (campaign: any) => {
    setEditingCampaign(campaign);
    setFormData({
      name: campaign.name,
      targetAudience: campaign.targetAudience,
      script: campaign.script || '',
      budget: campaign.budget || 0,
      status: campaign.status,
    });
    onOpen();
  };

  const handleSubmit = async () => {
    if (!formData.name.trim()) {
      toast({
        title: 'Validation Error',
        description: 'Campaign name is required',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
      return;
    }

    setIsSubmitting(true);

    try {
      let success = false;
      
      if (editingCampaign) {
        success = await updateCampaign(editingCampaign.id, formData);
      } else {
        success = await createCampaign(formData);
      }

      if (success) {
        toast({
          title: editingCampaign ? 'Campaign Updated' : 'Campaign Created',
          description: `Campaign "${formData.name}" has been ${editingCampaign ? 'updated' : 'created'} successfully.`,
          status: 'success',
          duration: 3000,
          isClosable: true,
        });
        onClose();
      } else {
        toast({
          title: 'Error',
          description: `Failed to ${editingCampaign ? 'update' : 'create'} campaign. Please try again.`,
          status: 'error',
          duration: 3000,
          isClosable: true,
        });
      }
    } catch (error) {
      console.error('Campaign operation failed:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteCampaign = async (campaign: any) => {
    if (window.confirm(`Are you sure you want to delete campaign "${campaign.name}"?`)) {
      const success = await deleteCampaign(campaign.id);
      
      if (success) {
        toast({
          title: 'Campaign Deleted',
          description: `Campaign "${campaign.name}" has been deleted.`,
          status: 'success',
          duration: 3000,
          isClosable: true,
        });
      } else {
        toast({
          title: 'Error',
          description: 'Failed to delete campaign. Please try again.',
          status: 'error',
          duration: 3000,
          isClosable: true,
        });
      }
    }
  };

  const handleStatusChange = async (campaign: any, newStatus: 'draft' | 'active' | 'paused' | 'completed') => {
    const success = await updateCampaign(campaign.id, { status: newStatus });
    
    if (success) {
      toast({
        title: 'Status Updated',
        description: `Campaign "${campaign.name}" is now ${newStatus}.`,
        status: 'success',
        duration: 3000,
        isClosable: true,
      });
    }
  };

  // Calculate campaign statistics
  const totalCampaigns = campaigns.length;
  const activeCampaigns = campaigns.filter(c => c.status === 'active').length;
  const totalCalls = campaigns.reduce((sum, c) => sum + c.totalCalls, 0);
  const totalConversions = campaigns.reduce((sum, c) => sum + c.successfulCalls, 0);
  const avgConversionRate = totalCalls > 0 ? (totalConversions / totalCalls) * 100 : 0;

  return (
    <Box>
      {/* Error Alert */}
      {error && (
        <Alert status="error" mb={4}>
          <AlertIcon />
          <Box>
            <Text fontWeight="bold">Error loading campaigns</Text>
            <Text fontSize="sm">{error}</Text>
          </Box>
          <Spacer />
          <Button size="sm" onClick={clearError}>
            Dismiss
          </Button>
        </Alert>
      )}

      {/* Header */}
      <VStack align="start" spacing={4} mb={8}>
        <HStack justify="space-between" w="full">
          <VStack align="start" spacing={1}>
            <Heading size="lg">Campaigns</Heading>
            <Text color="gray.500">
              Manage your voice and SMS campaigns
            </Text>
          </VStack>
          <HStack>
            <Button
              leftIcon={<FiRefreshCw />}
              variant="outline"
              size="sm"
              onClick={fetchCampaigns}
              isLoading={loading}
            >
              Refresh
            </Button>
            <Button
              leftIcon={<FiPlus />}
              colorScheme="blue"
              size="sm"
              onClick={handleCreateCampaign}
            >
              New Campaign
            </Button>
          </HStack>
        </HStack>
      </VStack>

      {/* Campaign Statistics */}
      <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={6} mb={8}>
        <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
          <CardBody>
            <Stat>
              <StatLabel>Total Campaigns</StatLabel>
              <StatNumber>{totalCampaigns}</StatNumber>
              <StatHelpText>
                {activeCampaigns} active
              </StatHelpText>
            </Stat>
          </CardBody>
        </Card>

        <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
          <CardBody>
            <Stat>
              <StatLabel>Total Calls</StatLabel>
              <StatNumber>{totalCalls.toLocaleString()}</StatNumber>
              <StatHelpText>
                Across all campaigns
              </StatHelpText>
            </Stat>
          </CardBody>
        </Card>

        <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
          <CardBody>
            <Stat>
              <StatLabel>Conversions</StatLabel>
              <StatNumber>{totalConversions.toLocaleString()}</StatNumber>
              <StatHelpText>
                Successful calls
              </StatHelpText>
            </Stat>
          </CardBody>
        </Card>

        <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
          <CardBody>
            <Stat>
              <StatLabel>Avg. Conversion Rate</StatLabel>
              <StatNumber>{avgConversionRate.toFixed(1)}%</StatNumber>
              <StatHelpText>
                Overall performance
              </StatHelpText>
            </Stat>
          </CardBody>
        </Card>
      </SimpleGrid>

      {/* Campaigns Table */}
      <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
        <CardHeader>
          <Heading size="md">All Campaigns</Heading>
        </CardHeader>
        <CardBody>
          {loading ? (
            <Flex justify="center" py={8}>
              <Spinner size="lg" />
            </Flex>
          ) : campaigns.length === 0 ? (
            <VStack py={8} spacing={4}>
              <Text color="gray.500">No campaigns found</Text>
              <Button
                leftIcon={<FiPlus />}
                colorScheme="blue"
                onClick={handleCreateCampaign}
              >
                Create Your First Campaign
              </Button>
            </VStack>
          ) : (
            <Table variant="simple">
              <Thead>
                <Tr>
                  <Th>Name</Th>
                  <Th>Status</Th>
                  <Th>Target Audience</Th>
                  <Th>Calls</Th>
                  <Th>Conversion Rate</Th>
                  <Th>Start Date</Th>
                  <Th>Actions</Th>
                </Tr>
              </Thead>
              <Tbody>
                {campaigns.map((campaign) => (
                  <Tr key={campaign.id}>
                    <Td>
                      <VStack align="start" spacing={1}>
                        <Text fontWeight="medium">{campaign.name}</Text>
                        {campaign.budget && (
                          <Text fontSize="sm" color="gray.500">
                            Budget: {formatMetricValue(campaign.budget, 'currency')}
                          </Text>
                        )}
                      </VStack>
                    </Td>
                    <Td>
                      <Badge colorScheme={getStatusColor(campaign.status)}>
                        {campaign.status.toUpperCase()}
                      </Badge>
                    </Td>
                    <Td>
                      <Text fontSize="sm">{campaign.targetAudience}</Text>
                    </Td>
                    <Td>
                      <VStack align="start" spacing={1}>
                        <Text fontWeight="medium">
                          {campaign.totalCalls.toLocaleString()}
                        </Text>
                        <Text fontSize="sm" color="green.500">
                          {campaign.successfulCalls} successful
                        </Text>
                      </VStack>
                    </Td>
                    <Td>
                      <VStack align="start" spacing={1}>
                        <Text fontWeight="medium">
                          {campaign.conversionRate.toFixed(1)}%
                        </Text>
                        <Progress
                          value={campaign.conversionRate}
                          size="sm"
                          colorScheme="green"
                          w="60px"
                        />
                      </VStack>
                    </Td>
                    <Td>
                      <Text fontSize="sm">
                        {new Date(campaign.startDate).toLocaleDateString()}
                      </Text>
                    </Td>
                    <Td>
                      <Menu>
                        <MenuButton
                          as={IconButton}
                          icon={<FiMoreVertical />}
                          variant="ghost"
                          size="sm"
                        />
                        <MenuList>
                          <MenuItem
                            icon={<FiEdit />}
                            onClick={() => handleEditCampaign(campaign)}
                          >
                            Edit
                          </MenuItem>
                          {campaign.status === 'active' ? (
                            <MenuItem
                              icon={<FiPause />}
                              onClick={() => handleStatusChange(campaign, 'paused')}
                            >
                              Pause
                            </MenuItem>
                          ) : (
                            <MenuItem
                              icon={<FiPlay />}
                              onClick={() => handleStatusChange(campaign, 'active')}
                            >
                              Start
                            </MenuItem>
                          )}
                          <MenuItem
                            icon={<FiTrash2 />}
                            color="red.500"
                            onClick={() => handleDeleteCampaign(campaign)}
                          >
                            Delete
                          </MenuItem>
                        </MenuList>
                      </Menu>
                    </Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
          )}
        </CardBody>
      </Card>

      {/* Campaign Form Modal */}
      <Modal isOpen={isOpen} onClose={onClose} size="lg">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>
            {editingCampaign ? 'Edit Campaign' : 'Create New Campaign'}
          </ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <VStack spacing={4}>
              <FormControl isRequired>
                <FormLabel>Campaign Name</FormLabel>
                <Input
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="Enter campaign name"
                />
              </FormControl>

              <FormControl isRequired>
                <FormLabel>Target Audience</FormLabel>
                <Input
                  value={formData.targetAudience}
                  onChange={(e) => setFormData({ ...formData, targetAudience: e.target.value })}
                  placeholder="e.g., Existing customers, New leads"
                />
              </FormControl>

              <FormControl>
                <FormLabel>Script</FormLabel>
                <Textarea
                  value={formData.script}
                  onChange={(e) => setFormData({ ...formData, script: e.target.value })}
                  placeholder="Enter call script or message template"
                  rows={4}
                />
              </FormControl>

              <FormControl>
                <FormLabel>Budget</FormLabel>
                <NumberInput
                  value={formData.budget}
                  onChange={(_, value) => setFormData({ ...formData, budget: value || 0 })}
                  min={0}
                >
                  <NumberInputField placeholder="0.00" />
                </NumberInput>
              </FormControl>

              <FormControl>
                <FormLabel>Status</FormLabel>
                <Select
                  value={formData.status}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value as any })}
                >
                  <option value="draft">Draft</option>
                  <option value="active">Active</option>
                  <option value="paused">Paused</option>
                  <option value="completed">Completed</option>
                </Select>
              </FormControl>
            </VStack>
          </ModalBody>

          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onClose}>
              Cancel
            </Button>
            <Button
              colorScheme="blue"
              onClick={handleSubmit}
              isLoading={isSubmitting}
            >
              {editingCampaign ? 'Update' : 'Create'} Campaign
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Box>
  );
};

export default Campaigns;