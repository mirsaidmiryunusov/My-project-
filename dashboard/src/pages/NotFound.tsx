/**
 * 404 Not Found Page
 */

import React from 'react';
import { Box, Heading, Text, Button, VStack } from '@chakra-ui/react';
import { useNavigate } from 'react-router-dom';

const NotFound: React.FC = () => {
  const navigate = useNavigate();

  return (
    <Box textAlign="center" py={10} px={6}>
      <VStack spacing={6}>
        <Heading
          display="inline-block"
          as="h2"
          size="2xl"
          bgGradient="linear(to-r, brand.400, brand.600)"
          backgroundClip="text"
        >
          404
        </Heading>
        <Text fontSize="18px" mt={3} mb={2}>
          Page Not Found
        </Text>
        <Text color="gray.500" mb={6}>
          The page you're looking for does not seem to exist
        </Text>
        <Button
          colorScheme="brand"
          bgGradient="linear(to-r, brand.400, brand.500, brand.600)"
          color="white"
          variant="solid"
          onClick={() => navigate('/')}
        >
          Go to Home
        </Button>
      </VStack>
    </Box>
  );
};

export default NotFound;