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
  Flex,
  Spacer,
  Menu,
  MenuButton,
  MenuList,
  MenuItem,
  useColorModeValue,
  InputGroup,
  InputLeftElement,
  Tag,
  TagLabel,
  TagCloseButton,
  Wrap,
  WrapItem,
} from '@chakra-ui/react';
import {
  FiPlus,
  FiEdit,
  FiTrash2,
  FiMoreVertical,
  FiUsers,
  FiPhone,
  FiMail,
  FiSearch,
  FiRefreshCw,
  FiDownload,
  FiUpload,
} from 'react-icons/fi';
import { useDashboardStore, getStatusColor } from '../stores/dashboardStore';

interface ContactFormData {
  firstName: string;
  lastName: string;
  email: string;
  phoneNumber: string;
  status: 'active' | 'inactive' | 'do-not-call';
  tags: string[];
  notes: string;
}

const Contacts: React.FC = () => {
  const {
    contacts,
    loading,
    error,
    fetchContacts,
    createContact,
    updateContact,
    deleteContact,
    clearError,
  } = useDashboardStore();

  const { isOpen, onOpen, onClose } = useDisclosure();
  const [editingContact, setEditingContact] = useState<any>(null);
  const [formData, setFormData] = useState<ContactFormData>({
    firstName: '',
    lastName: '',
    email: '',
    phoneNumber: '',
    status: 'active',
    tags: [],
    notes: '',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [newTag, setNewTag] = useState('');

  const toast = useToast();
  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');

  useEffect(() => {
    fetchContacts();
  }, [fetchContacts]);

  const handleCreateContact = () => {
    setEditingContact(null);
    setFormData({
      firstName: '',
      lastName: '',
      email: '',
      phoneNumber: '',
      status: 'active',
      tags: [],
      notes: '',
    });
    onOpen();
  };

  const handleEditContact = (contact: any) => {
    setEditingContact(contact);
    setFormData({
      firstName: contact.firstName,
      lastName: contact.lastName,
      email: contact.email,
      phoneNumber: contact.phoneNumber,
      status: contact.status,
      tags: contact.tags || [],
      notes: contact.notes || '',
    });
    onOpen();
  };

  const handleSubmit = async () => {
    if (!formData.firstName.trim() || !formData.lastName.trim()) {
      toast({
        title: 'Validation Error',
        description: 'First name and last name are required',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
      return;
    }

    if (!formData.phoneNumber.trim()) {
      toast({
        title: 'Validation Error',
        description: 'Phone number is required',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
      return;
    }

    setIsSubmitting(true);

    try {
      let success = false;
      
      if (editingContact) {
        success = await updateContact(editingContact.id, formData);
      } else {
        success = await createContact(formData);
      }

      if (success) {
        toast({
          title: editingContact ? 'Contact Updated' : 'Contact Created',
          description: `Contact "${formData.firstName} ${formData.lastName}" has been ${editingContact ? 'updated' : 'created'} successfully.`,
          status: 'success',
          duration: 3000,
          isClosable: true,
        });
        onClose();
      } else {
        toast({
          title: 'Error',
          description: `Failed to ${editingContact ? 'update' : 'create'} contact. Please try again.`,
          status: 'error',
          duration: 3000,
          isClosable: true,
        });
      }
    } catch (error) {
      console.error('Contact operation failed:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteContact = async (contact: any) => {
    if (window.confirm(`Are you sure you want to delete contact "${contact.firstName} ${contact.lastName}"?`)) {
      const success = await deleteContact(contact.id);
      
      if (success) {
        toast({
          title: 'Contact Deleted',
          description: `Contact "${contact.firstName} ${contact.lastName}" has been deleted.`,
          status: 'success',
          duration: 3000,
          isClosable: true,
        });
      } else {
        toast({
          title: 'Error',
          description: 'Failed to delete contact. Please try again.',
          status: 'error',
          duration: 3000,
          isClosable: true,
        });
      }
    }
  };

  const handleAddTag = () => {
    if (newTag.trim() && !formData.tags.includes(newTag.trim())) {
      setFormData({
        ...formData,
        tags: [...formData.tags, newTag.trim()],
      });
      setNewTag('');
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    setFormData({
      ...formData,
      tags: formData.tags.filter(tag => tag !== tagToRemove),
    });
  };

  // Filter contacts based on search and status
  const filteredContacts = contacts.filter(contact => {
    const matchesSearch = searchTerm === '' || 
      contact.firstName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      contact.lastName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      contact.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      contact.phoneNumber.includes(searchTerm);
    
    const matchesStatus = statusFilter === 'all' || contact.status === statusFilter;
    
    return matchesSearch && matchesStatus;
  });

  // Calculate contact statistics
  const totalContacts = contacts.length;
  const activeContacts = contacts.filter(c => c.status === 'active').length;
  const inactiveContacts = contacts.filter(c => c.status === 'inactive').length;
  const doNotCallContacts = contacts.filter(c => c.status === 'do-not-call').length;

  return (
    <Box>
      {/* Error Alert */}
      {error && (
        <Alert status="error" mb={4}>
          <AlertIcon />
          <Box>
            <Text fontWeight="bold">Error loading contacts</Text>
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
            <Heading size="lg">Contacts</Heading>
            <Text color="gray.500">
              Manage your contact database
            </Text>
          </VStack>
          <HStack>
            <Button
              leftIcon={<FiUpload />}
              variant="outline"
              size="sm"
            >
              Import
            </Button>
            <Button
              leftIcon={<FiDownload />}
              variant="outline"
              size="sm"
            >
              Export
            </Button>
            <Button
              leftIcon={<FiRefreshCw />}
              variant="outline"
              size="sm"
              onClick={() => fetchContacts()}
              isLoading={loading}
            >
              Refresh
            </Button>
            <Button
              leftIcon={<FiPlus />}
              colorScheme="blue"
              size="sm"
              onClick={handleCreateContact}
            >
              New Contact
            </Button>
          </HStack>
        </HStack>
      </VStack>

      {/* Contact Statistics */}
      <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={6} mb={8}>
        <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
          <CardBody>
            <Stat>
              <StatLabel>Total Contacts</StatLabel>
              <StatNumber>{totalContacts}</StatNumber>
              <StatHelpText>
                All contacts in database
              </StatHelpText>
            </Stat>
          </CardBody>
        </Card>

        <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
          <CardBody>
            <Stat>
              <StatLabel>Active Contacts</StatLabel>
              <StatNumber>{activeContacts}</StatNumber>
              <StatHelpText>
                Available for campaigns
              </StatHelpText>
            </Stat>
          </CardBody>
        </Card>

        <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
          <CardBody>
            <Stat>
              <StatLabel>Inactive Contacts</StatLabel>
              <StatNumber>{inactiveContacts}</StatNumber>
              <StatHelpText>
                Temporarily disabled
              </StatHelpText>
            </Stat>
          </CardBody>
        </Card>

        <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
          <CardBody>
            <Stat>
              <StatLabel>Do Not Call</StatLabel>
              <StatNumber>{doNotCallContacts}</StatNumber>
              <StatHelpText>
                Excluded from campaigns
              </StatHelpText>
            </Stat>
          </CardBody>
        </Card>
      </SimpleGrid>

      {/* Filters */}
      <Card bg={cardBg} borderColor={borderColor} borderWidth="1px" mb={6}>
        <CardBody>
          <HStack spacing={4}>
            <InputGroup maxW="300px">
              <InputLeftElement pointerEvents="none">
                <FiSearch color="gray.300" />
              </InputLeftElement>
              <Input
                placeholder="Search contacts..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </InputGroup>
            
            <Select
              maxW="200px"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <option value="all">All Status</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
              <option value="do-not-call">Do Not Call</option>
            </Select>
            
            <Spacer />
            
            <Text fontSize="sm" color="gray.500">
              Showing {filteredContacts.length} of {totalContacts} contacts
            </Text>
          </HStack>
        </CardBody>
      </Card>

      {/* Contacts Table */}
      <Card bg={cardBg} borderColor={borderColor} borderWidth="1px">
        <CardHeader>
          <Heading size="md">All Contacts</Heading>
        </CardHeader>
        <CardBody>
          {loading ? (
            <Flex justify="center" py={8}>
              <Spinner size="lg" />
            </Flex>
          ) : filteredContacts.length === 0 ? (
            <VStack py={8} spacing={4}>
              <Text color="gray.500">
                {searchTerm || statusFilter !== 'all' ? 'No contacts match your filters' : 'No contacts found'}
              </Text>
              {!searchTerm && statusFilter === 'all' && (
                <Button
                  leftIcon={<FiPlus />}
                  colorScheme="blue"
                  onClick={handleCreateContact}
                >
                  Add Your First Contact
                </Button>
              )}
            </VStack>
          ) : (
            <Table variant="simple">
              <Thead>
                <Tr>
                  <Th>Name</Th>
                  <Th>Contact Info</Th>
                  <Th>Status</Th>
                  <Th>Tags</Th>
                  <Th>Last Contact</Th>
                  <Th>Actions</Th>
                </Tr>
              </Thead>
              <Tbody>
                {filteredContacts.map((contact) => (
                  <Tr key={contact.id}>
                    <Td>
                      <VStack align="start" spacing={1}>
                        <Text fontWeight="medium">
                          {contact.firstName} {contact.lastName}
                        </Text>
                        {contact.notes && (
                          <Text fontSize="sm" color="gray.500" noOfLines={1}>
                            {contact.notes}
                          </Text>
                        )}
                      </VStack>
                    </Td>
                    <Td>
                      <VStack align="start" spacing={1}>
                        <HStack>
                          <FiPhone size={14} />
                          <Text fontSize="sm">{contact.phoneNumber}</Text>
                        </HStack>
                        {contact.email && (
                          <HStack>
                            <FiMail size={14} />
                            <Text fontSize="sm">{contact.email}</Text>
                          </HStack>
                        )}
                      </VStack>
                    </Td>
                    <Td>
                      <Badge colorScheme={getStatusColor(contact.status)}>
                        {contact.status.replace('-', ' ').toUpperCase()}
                      </Badge>
                    </Td>
                    <Td>
                      <Wrap>
                        {contact.tags?.slice(0, 3).map((tag) => (
                          <WrapItem key={tag}>
                            <Tag size="sm" colorScheme="blue">
                              <TagLabel>{tag}</TagLabel>
                            </Tag>
                          </WrapItem>
                        ))}
                        {contact.tags?.length > 3 && (
                          <WrapItem>
                            <Tag size="sm" variant="outline">
                              <TagLabel>+{contact.tags.length - 3}</TagLabel>
                            </Tag>
                          </WrapItem>
                        )}
                      </Wrap>
                    </Td>
                    <Td>
                      <Text fontSize="sm">
                        {contact.lastContact 
                          ? new Date(contact.lastContact).toLocaleDateString()
                          : 'Never'
                        }
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
                            onClick={() => handleEditContact(contact)}
                          >
                            Edit
                          </MenuItem>
                          <MenuItem
                            icon={<FiPhone />}
                          >
                            Call Now
                          </MenuItem>
                          <MenuItem
                            icon={<FiTrash2 />}
                            color="red.500"
                            onClick={() => handleDeleteContact(contact)}
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

      {/* Contact Form Modal */}
      <Modal isOpen={isOpen} onClose={onClose} size="lg">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>
            {editingContact ? 'Edit Contact' : 'Create New Contact'}
          </ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <VStack spacing={4}>
              <HStack w="full" spacing={4}>
                <FormControl isRequired>
                  <FormLabel>First Name</FormLabel>
                  <Input
                    value={formData.firstName}
                    onChange={(e) => setFormData({ ...formData, firstName: e.target.value })}
                    placeholder="Enter first name"
                  />
                </FormControl>

                <FormControl isRequired>
                  <FormLabel>Last Name</FormLabel>
                  <Input
                    value={formData.lastName}
                    onChange={(e) => setFormData({ ...formData, lastName: e.target.value })}
                    placeholder="Enter last name"
                  />
                </FormControl>
              </HStack>

              <FormControl>
                <FormLabel>Email</FormLabel>
                <Input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  placeholder="Enter email address"
                />
              </FormControl>

              <FormControl isRequired>
                <FormLabel>Phone Number</FormLabel>
                <Input
                  value={formData.phoneNumber}
                  onChange={(e) => setFormData({ ...formData, phoneNumber: e.target.value })}
                  placeholder="Enter phone number"
                />
              </FormControl>

              <FormControl>
                <FormLabel>Status</FormLabel>
                <Select
                  value={formData.status}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value as any })}
                >
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                  <option value="do-not-call">Do Not Call</option>
                </Select>
              </FormControl>

              <FormControl>
                <FormLabel>Tags</FormLabel>
                <HStack>
                  <Input
                    value={newTag}
                    onChange={(e) => setNewTag(e.target.value)}
                    placeholder="Add a tag"
                    onKeyPress={(e) => e.key === 'Enter' && handleAddTag()}
                  />
                  <Button onClick={handleAddTag} size="sm">
                    Add
                  </Button>
                </HStack>
                <Wrap mt={2}>
                  {formData.tags.map((tag) => (
                    <WrapItem key={tag}>
                      <Tag size="sm" colorScheme="blue">
                        <TagLabel>{tag}</TagLabel>
                        <TagCloseButton onClick={() => handleRemoveTag(tag)} />
                      </Tag>
                    </WrapItem>
                  ))}
                </Wrap>
              </FormControl>

              <FormControl>
                <FormLabel>Notes</FormLabel>
                <Textarea
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  placeholder="Add notes about this contact"
                  rows={3}
                />
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
              {editingContact ? 'Update' : 'Create'} Contact
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Box>
  );
};

export default Contacts;