import React, { useState } from 'react';
import { useDropzone } from 'react-dropzone';
import axios from 'axios';
import {
  Box, Button, Text, VStack,
  Center, Spinner, Alert, AlertIcon
} from '@chakra-ui/react';

const ReceiptUploader = ({ onReceiptProcessed }) => {
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState(null);

  const onDrop = async (acceptedFiles) => {
    if (acceptedFiles.length === 0) return;

    setIsUploading(true);
    setError(null);

    const file = acceptedFiles[0];
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post('http://localhost:5001/process-receipt', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      if (response.data.success) {
        onReceiptProcessed(response.data);
      } else {
        setError('Failed to process receipt. Please try again.');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to upload receipt. Please try again.');
    } finally {
      setIsUploading(false);
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.jpeg', '.jpg', '.png'],
      'application/pdf': ['.pdf']
    },
    maxFiles: 1
  });

  return (
    <VStack spacing={4}>
      <Text fontSize="lg" fontWeight="medium">
        Upload your receipt to start splitting
      </Text>

      <Box
        {...getRootProps()}
        borderWidth={2}
        borderRadius="lg"
        borderStyle="dashed"
        borderColor={isDragActive ? "blue.400" : "gray.300"}
        bg={isDragActive ? "blue.50" : "gray.50"}
        p={10}
        width="100%"
        textAlign="center"
        cursor="pointer"
        _hover={{ bg: "blue.50" }}
      >
        <input {...getInputProps()} />

        {isUploading ? (
          <Center p={10}>
            <VStack>
              <Spinner size="xl" />
              <Text mt={4}>Processing receipt with Mistral OCR...</Text>
            </VStack>
          </Center>
        ) : (
          <Center>
            <VStack>
              <Text>
                {isDragActive
                  ? "Drop the receipt here..."
                  : "Drag & drop a receipt image or PDF here, or click to select files"}
              </Text>
              <Text fontSize="sm" color="gray.500">
                Supported formats: JPEG, PNG, PDF
              </Text>
            </VStack>
          </Center>
        )}
      </Box>

      {error && (
        <Alert status="error" borderRadius="md">
          <AlertIcon />
          {error}
        </Alert>
      )}

      <Text fontSize="sm" color="gray.500">
        Your receipt will be processed with Mistral OCR to extract items and prices.
      </Text>
    </VStack>
  );
};

export default ReceiptUploader;
