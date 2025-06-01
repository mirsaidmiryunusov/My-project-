import React, { useState } from 'react';
import {
  Box,
  VStack,
  HStack,
  Text,
  Heading,
  Card,
  CardHeader,
  CardBody,
  SimpleGrid,
  Switch,
  Button,
  Input,
  Select,
  Textarea,
  FormControl,
  FormLabel,
  FormHelperText,
  Divider,
  Badge,
  Progress,
  Alert,
  AlertIcon,
  useColorModeValue,
  useToast,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Slider,
  SliderTrack,
  SliderFilledTrack,
  SliderThumb,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  NumberIncrementStepper,
  NumberDecrementStepper,
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
  Icon,
  Tooltip,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalBody,
  ModalCloseButton,
  useDisclosure,
} from '@chakra-ui/react';
import {
  FiSettings,
  FiUser,
  FiShield,
  FiBell,
  FiDatabase,
  FiCloud,
  FiMonitor,
  FiPhone,
  FiMail,
  FiKey,
  FiSave,
  FiRefreshCw,
  FiDownload,
  FiUpload,
  FiTrash2,
  FiAlertTriangle,
  FiCheckCircle,
  FiInfo,
} from 'react-icons/fi';

interface SettingsSection {
  id: string;
  title: string;
  description: string;
  icon: React.ElementType;
  settings: SettingItem[];
}

interface SettingItem {
  key: string;
  label: string;
  description?: string;
  type: 'switch' | 'input' | 'select' | 'slider' | 'number' | 'textarea';
  value: any;
  options?: { label: string; value: string }[];
  min?: number;
  max?: number;
  step?: number;
}

const Settings: React.FC = () => {
  const toast = useToast();
  const { isOpen, onOpen, onClose } = useDisclosure();
  const [activeTab, setActiveTab] = useState(0);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const cardBg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');

  // Settings configuration
  const [settingsData, setSettingsData] = useState<SettingsSection[]>([
    {
      id: 'general',
      title: 'General Settings',
      description: 'Basic application configuration',
      icon: FiSettings,
      settings: [
        {
          key: 'autoRefresh',
          label: 'Auto Refresh Dashboard',
          description: 'Automatically refresh dashboard data every 5 minutes',
          type: 'switch',
          value: true,
        },
        {
          key: 'refreshInterval',
          label: 'Refresh Interval (minutes)',
          description: 'How often to refresh dashboard data',
          type: 'slider',
          value: 5,
          min: 1,
          max: 60,
          step: 1,
        },
        {
          key: 'timezone',
          label: 'Timezone',
          description: 'Display timezone for all timestamps',
          type: 'select',
          value: 'UTC',
          options: [
            { label: 'UTC', value: 'UTC' },
            { label: 'EST (Eastern)', value: 'EST' },
            { label: 'PST (Pacific)', value: 'PST' },
            { label: 'CST (Central)', value: 'CST' },
          ],
        },
        {
          key: 'language',
          label: 'Language',
          description: 'Interface language',
          type: 'select',
          value: 'en',
          options: [
            { label: 'English', value: 'en' },
            { label: 'Spanish', value: 'es' },
            { label: 'French', value: 'fr' },
            { label: 'German', value: 'de' },
          ],
        },
      ],
    },
    {
      id: 'calling',
      title: 'Call Center Settings',
      description: 'Configure call center operations',
      icon: FiPhone,
      settings: [
        {
          key: 'maxConcurrentCalls',
          label: 'Max Concurrent Calls',
          description: 'Maximum number of simultaneous calls',
          type: 'number',
          value: 50,
          min: 1,
          max: 1000,
        },
        {
          key: 'callTimeout',
          label: 'Call Timeout (seconds)',
          description: 'Automatic call timeout duration',
          type: 'slider',
          value: 30,
          min: 10,
          max: 300,
          step: 5,
        },
        {
          key: 'recordCalls',
          label: 'Record Calls',
          description: 'Enable call recording for quality assurance',
          type: 'switch',
          value: true,
        },
        {
          key: 'callQualityThreshold',
          label: 'Call Quality Threshold (%)',
          description: 'Minimum call quality score for alerts',
          type: 'slider',
          value: 80,
          min: 50,
          max: 100,
          step: 5,
        },
        {
          key: 'voicemailEnabled',
          label: 'Voicemail System',
          description: 'Enable voicemail for missed calls',
          type: 'switch',
          value: true,
        },
      ],
    },
    {
      id: 'notifications',
      title: 'Notifications',
      description: 'Configure alerts and notifications',
      icon: FiBell,
      settings: [
        {
          key: 'emailNotifications',
          label: 'Email Notifications',
          description: 'Receive notifications via email',
          type: 'switch',
          value: true,
        },
        {
          key: 'smsNotifications',
          label: 'SMS Notifications',
          description: 'Receive critical alerts via SMS',
          type: 'switch',
          value: false,
        },
        {
          key: 'pushNotifications',
          label: 'Push Notifications',
          description: 'Browser push notifications',
          type: 'switch',
          value: true,
        },
        {
          key: 'notificationEmail',
          label: 'Notification Email',
          description: 'Email address for notifications',
          type: 'input',
          value: 'admin@company.com',
        },
        {
          key: 'alertThresholds',
          label: 'Alert Thresholds',
          description: 'Configure when to send alerts',
          type: 'textarea',
          value: 'High CPU: >80%\nHigh Memory: >85%\nCall Failure Rate: >10%',
        },
      ],
    },
    {
      id: 'security',
      title: 'Security & Privacy',
      description: 'Security and privacy settings',
      icon: FiShield,
      settings: [
        {
          key: 'twoFactorAuth',
          label: 'Two-Factor Authentication',
          description: 'Enable 2FA for enhanced security',
          type: 'switch',
          value: false,
        },
        {
          key: 'sessionTimeout',
          label: 'Session Timeout (hours)',
          description: 'Automatic logout after inactivity',
          type: 'slider',
          value: 8,
          min: 1,
          max: 24,
          step: 1,
        },
        {
          key: 'dataRetention',
          label: 'Data Retention (days)',
          description: 'How long to keep call records',
          type: 'number',
          value: 90,
          min: 30,
          max: 365,
        },
        {
          key: 'encryptData',
          label: 'Encrypt Stored Data',
          description: 'Encrypt sensitive data at rest',
          type: 'switch',
          value: true,
        },
        {
          key: 'auditLogging',
          label: 'Audit Logging',
          description: 'Log all user actions for compliance',
          type: 'switch',
          value: true,
        },
      ],
    },
    {
      id: 'integration',
      title: 'Integrations',
      description: 'Third-party service integrations',
      icon: FiCloud,
      settings: [
        {
          key: 'crmIntegration',
          label: 'CRM Integration',
          description: 'Connect with your CRM system',
          type: 'select',
          value: 'none',
          options: [
            { label: 'None', value: 'none' },
            { label: 'Salesforce', value: 'salesforce' },
            { label: 'HubSpot', value: 'hubspot' },
            { label: 'Pipedrive', value: 'pipedrive' },
          ],
        },
        {
          key: 'webhookUrl',
          label: 'Webhook URL',
          description: 'URL for webhook notifications',
          type: 'input',
          value: '',
        },
        {
          key: 'apiRateLimit',
          label: 'API Rate Limit (requests/minute)',
          description: 'Limit API requests per minute',
          type: 'number',
          value: 1000,
          min: 100,
          max: 10000,
        },
        {
          key: 'slackIntegration',
          label: 'Slack Integration',
          description: 'Send notifications to Slack',
          type: 'switch',
          value: false,
        },
      ],
    },
  ]);

  const handleSettingChange = (sectionId: string, settingKey: string, value: any) => {
    setSettingsData(prev => 
      prev.map(section => 
        section.id === sectionId 
          ? {
              ...section,
              settings: section.settings.map(setting =>
                setting.key === settingKey ? { ...setting, value } : setting
              )
            }
          : section
      )
    );
    setHasUnsavedChanges(true);
  };

  const handleSaveSettings = async () => {
    setIsLoading(true);
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      setHasUnsavedChanges(false);
      toast({
        title: 'Settings saved',
        description: 'Your settings have been saved successfully.',
        status: 'success',
        duration: 3000,
        isClosable: true,
      });
    } catch (error) {
      toast({
        title: 'Error saving settings',
        description: 'There was an error saving your settings. Please try again.',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleResetSettings = () => {
    onOpen();
  };

  const confirmReset = () => {
    // Reset to default values
    setSettingsData(prev => 
      prev.map(section => ({
        ...section,
        settings: section.settings.map(setting => ({
          ...setting,
          value: getDefaultValue(setting.type)
        }))
      }))
    );
    setHasUnsavedChanges(true);
    onClose();
    toast({
      title: 'Settings reset',
      description: 'All settings have been reset to default values.',
      status: 'info',
      duration: 3000,
      isClosable: true,
    });
  };

  const getDefaultValue = (type: string) => {
    switch (type) {
      case 'switch': return false;
      case 'input': return '';
      case 'textarea': return '';
      case 'select': return '';
      case 'number': return 0;
      case 'slider': return 50;
      default: return '';
    }
  };

  const renderSettingControl = (section: SettingsSection, setting: SettingItem) => {
    const value = setting.value;
    const onChange = (newValue: any) => handleSettingChange(section.id, setting.key, newValue);

    switch (setting.type) {
      case 'switch':
        return (
          <Switch
            isChecked={value}
            onChange={(e) => onChange(e.target.checked)}
            colorScheme="blue"
          />
        );

      case 'input':
        return (
          <Input
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder={setting.description}
          />
        );

      case 'textarea':
        return (
          <Textarea
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder={setting.description}
            rows={4}
          />
        );

      case 'select':
        return (
          <Select value={value} onChange={(e) => onChange(e.target.value)}>
            {setting.options?.map(option => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </Select>
        );

      case 'number':
        return (
          <NumberInput
            value={value}
            onChange={(_, num) => onChange(num)}
            min={setting.min}
            max={setting.max}
          >
            <NumberInputField />
            <NumberInputStepper>
              <NumberIncrementStepper />
              <NumberDecrementStepper />
            </NumberInputStepper>
          </NumberInput>
        );

      case 'slider':
        return (
          <VStack spacing={2} w="full">
            <HStack justify="space-between" w="full">
              <Text fontSize="sm">{setting.min}</Text>
              <Badge colorScheme="blue">{value}</Badge>
              <Text fontSize="sm">{setting.max}</Text>
            </HStack>
            <Slider
              value={value}
              onChange={onChange}
              min={setting.min}
              max={setting.max}
              step={setting.step}
              colorScheme="blue"
            >
              <SliderTrack>
                <SliderFilledTrack />
              </SliderTrack>
              <SliderThumb />
            </Slider>
          </VStack>
        );

      default:
        return null;
    }
  };

  return (
    <Box>
      {/* Header */}
      <VStack align="start" spacing={4} mb={8}>
        <HStack justify="space-between" w="full">
          <VStack align="start" spacing={1}>
            <Heading size="lg">Settings</Heading>
            <Text color="gray.500">
              Configure your call center dashboard and system preferences
            </Text>
          </VStack>
          <HStack>
            {hasUnsavedChanges && (
              <Badge colorScheme="yellow" variant="subtle">
                Unsaved Changes
              </Badge>
            )}
            <Button
              leftIcon={<FiRefreshCw />}
              variant="outline"
              size="sm"
              onClick={handleResetSettings}
            >
              Reset
            </Button>
            <Button
              leftIcon={<FiSave />}
              colorScheme="blue"
              size="sm"
              onClick={handleSaveSettings}
              isLoading={isLoading}
              loadingText="Saving..."
              isDisabled={!hasUnsavedChanges}
            >
              Save Changes
            </Button>
          </HStack>
        </HStack>
      </VStack>

      {/* Settings Tabs */}
      <Tabs variant="enclosed" colorScheme="blue" index={activeTab} onChange={setActiveTab}>
        <TabList>
          {settingsData.map((section) => (
            <Tab key={section.id}>
              <HStack>
                <Icon as={section.icon} boxSize={4} />
                <Text>{section.title}</Text>
              </HStack>
            </Tab>
          ))}
        </TabList>

        <TabPanels>
          {settingsData.map((section) => (
            <TabPanel key={section.id} px={0}>
              <VStack spacing={6} align="stretch">
                {/* Section Description */}
                <Alert status="info" variant="left-accent">
                  <AlertIcon />
                  <Box>
                    <Text fontWeight="bold">{section.title}</Text>
                    <Text fontSize="sm">{section.description}</Text>
                  </Box>
                </Alert>

                {/* Settings */}
                <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={6}>
                  {section.settings.map((setting) => (
                    <Card key={setting.key} bg={cardBg} borderColor={borderColor} borderWidth="1px">
                      <CardBody>
                        <VStack spacing={4} align="stretch">
                          <VStack align="start" spacing={1}>
                            <Text fontWeight="medium">{setting.label}</Text>
                            {setting.description && (
                              <Text fontSize="sm" color="gray.500">
                                {setting.description}
                              </Text>
                            )}
                          </VStack>
                          {renderSettingControl(section, setting)}
                        </VStack>
                      </CardBody>
                    </Card>
                  ))}
                </SimpleGrid>
              </VStack>
            </TabPanel>
          ))}
        </TabPanels>
      </Tabs>

      {/* System Information */}
      <Card bg={cardBg} borderColor={borderColor} borderWidth="1px" mt={8}>
        <CardHeader>
          <Heading size="md">System Information</Heading>
        </CardHeader>
        <CardBody>
          <SimpleGrid columns={{ base: 1, md: 3 }} spacing={6}>
            <VStack align="start" spacing={2}>
              <Text fontSize="sm" fontWeight="bold">Application Version</Text>
              <Text fontSize="sm" color="gray.500">v2.1.0</Text>
            </VStack>
            <VStack align="start" spacing={2}>
              <Text fontSize="sm" fontWeight="bold">Last Updated</Text>
              <Text fontSize="sm" color="gray.500">2024-01-15</Text>
            </VStack>
            <VStack align="start" spacing={2}>
              <Text fontSize="sm" fontWeight="bold">Database Version</Text>
              <Text fontSize="sm" color="gray.500">PostgreSQL 14.2</Text>
            </VStack>
          </SimpleGrid>
        </CardBody>
      </Card>

      {/* Reset Confirmation Modal */}
      <Modal isOpen={isOpen} onClose={onClose}>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Reset Settings</ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <VStack spacing={4} align="start">
              <HStack>
                <Icon as={FiAlertTriangle} color="red.500" boxSize={5} />
                <Text fontWeight="bold">Are you sure?</Text>
              </HStack>
              <Text>
                This will reset all settings to their default values. This action cannot be undone.
              </Text>
            </VStack>
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onClose}>
              Cancel
            </Button>
            <Button colorScheme="red" onClick={confirmReset}>
              Reset All Settings
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Box>
  );
};

export default Settings;