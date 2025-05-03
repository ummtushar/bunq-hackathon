import React, { useState } from 'react';
import {
  VStack, HStack, Box, Text, Button,
  Grid, GridItem, Badge, Progress,
  Alert, AlertIcon, Tooltip, IconButton,
  Modal, ModalOverlay, ModalContent,
  ModalHeader, ModalFooter, ModalBody,
  ModalCloseButton, useDisclosure,
  Radio, RadioGroup, Stack, Flex
} from '@chakra-ui/react';
import { InfoIcon, CloseIcon } from '@chakra-ui/icons';

const ItemMatching = ({ items, friends, assignments, onItemAssigned, onComplete }) => {
  const [selectedItemId, setSelectedItemId] = useState(null);
  const [error, setError] = useState(null);
  const { isOpen, onOpen, onClose } = useDisclosure();
  const [splitOption, setSplitOption] = useState('whole');
  const [selectedFriends, setSelectedFriends] = useState([]);

  // Calculate total items and how many have been fully assigned
  const totalQuantity = items.reduce((sum, item) => sum + item.quantity, 0);
  const assignedQuantity = totalQuantity - items.reduce((sum, item) => sum + item.remainingQuantity, 0);
  const progressPercentage = (assignedQuantity / totalQuantity) * 100;

  const handleItemClick = (itemId) => {
    // Only allow selection if the item has remaining quantity
    const item = items.find(i => i.id === itemId);
    if (item && item.remainingQuantity > 0) {
      setSelectedItemId(itemId);
      setError(null);
      // Reset split options when selecting a new item
      setSplitOption('whole');
      setSelectedFriends([]);
    }
  };

  const handleFriendClick = (friendId) => {
    if (!selectedItemId) {
      setError('Please select an item first');
      return;
    }

    if (splitOption === 'whole') {
      // Traditional single assignment
      onItemAssigned(selectedItemId, friendId);

      // Check if all quantities of the item have been assigned
      const updatedItem = items.find(i => i.id === selectedItemId);
      if (updatedItem.remainingQuantity - 1 <= 0) {
        setSelectedItemId(null); // Reset selection if no remaining quantity
      }
    } else {
      // For split items, we open the modal to select multiple friends
      onOpen();
      setSelectedFriends([friendId]); // Start with the clicked friend
    }
  };

  const toggleFriendSelection = (friendId) => {
    if (selectedFriends.includes(friendId)) {
      setSelectedFriends(selectedFriends.filter(id => id !== friendId));
    } else {
      setSelectedFriends([...selectedFriends, friendId]);
    }
  };

  const handleSplitConfirm = () => {
    if (selectedFriends.length === 0) {
      return; // Don't do anything if no friends selected
    }

    // For each selected friend, assign the item with a split indicator
    selectedFriends.forEach(friendId => {
      onItemAssigned(selectedItemId, friendId, true, selectedFriends.length);
    });

    // Close modal and reset
    onClose();
    setSelectedFriends([]);

    // Check if all quantities of the item have been assigned
    const updatedItem = items.find(i => i.id === selectedItemId);
    if (updatedItem.remainingQuantity - 1 <= 0) {
      setSelectedItemId(null); // Reset selection if no remaining quantity
    }
  };

  const handleCompleteClick = () => {
    if (assignedQuantity < totalQuantity) {
      setError('Please assign all items before continuing');
      return;
    }

    onComplete();
  };

  // Get assignment counts for each friend
  const friendCounts = friends.reduce((counts, friend) => {
    counts[friend.id] = 0;
    Object.entries(assignments).forEach(([itemId, friendIds]) => {
      const count = friendIds.filter(id => id === friend.id).length;
      counts[friend.id] += count;
    });
    return counts;
  }, {});

  return (
    <VStack spacing={6} width="100%">
      <Text fontSize="xl" fontWeight="bold">
        Match Items with Friends
      </Text>

      <Box width="100%">
        <HStack justifyContent="space-between" mb={2}>
          <Text>Progress: {assignedQuantity} of {totalQuantity} items assigned</Text>
          <Text>{Math.round(progressPercentage)}%</Text>
        </HStack>
        <Progress colorScheme="green" size="sm" value={progressPercentage} borderRadius="md" />
      </Box>

      {error && (
        <Alert status="error" borderRadius="md">
          <AlertIcon />
          {error}
        </Alert>
      )}

      {selectedItemId && (
        <HStack width="100%" spacing={4}>
          <Text>Assign as:</Text>
          <RadioGroup onChange={setSplitOption} value={splitOption}>
            <Stack direction="row">
              <Radio value="whole">Whole item</Radio>
              <Radio value="split">Split item</Radio>
            </Stack>
          </RadioGroup>
          <Tooltip label="Use 'Split item' when multiple people share one item">
            <InfoIcon />
          </Tooltip>
        </HStack>
      )}

      <Grid templateColumns="1fr 1fr" gap={6} width="100%">
        <GridItem>
          <Box borderWidth={1} borderRadius="md" p={4} height="400px" overflowY="auto">
            <Text fontWeight="bold" mb={4}>Receipt Items</Text>

            <VStack spacing={3} align="stretch">
              {items.map(item => (
                <Box
                  key={item.id}
                  p={3}
                  borderRadius="md"
                  bg={selectedItemId === item.id ? "blue.100" :
                     item.remainingQuantity === 0 ? "gray.100" : "white"}
                  borderWidth={1}
                  borderColor={selectedItemId === item.id ? "blue.500" : "gray.200"}
                  onClick={() => handleItemClick(item.id)}
                  cursor={item.remainingQuantity > 0 ? "pointer" : "default"}
                  opacity={item.remainingQuantity > 0 ? 1 : 0.6}
                  _hover={item.remainingQuantity > 0 ? { bg: "blue.50" } : {}}
                >
                  <HStack justifyContent="space-between">
                    <VStack align="start" spacing={1}>
                      <Text fontWeight="medium">{item.name}</Text>
                      <Text fontSize="sm" color="gray.600">
                        €{item.price.toFixed(2)} each
                      </Text>
                    </VStack>

                    <VStack align="end">
                      <Badge colorScheme={item.remainingQuantity > 0 ? "green" : "gray"}>
                        {item.remainingQuantity} / {item.quantity} left
                      </Badge>
                    </VStack>
                  </HStack>
                </Box>
              ))}
            </VStack>
          </Box>
        </GridItem>

        <GridItem>
          <Box borderWidth={1} borderRadius="md" p={4} height="400px" overflowY="auto">
            <Text fontWeight="bold" mb={4}>Friends</Text>

            <VStack spacing={3} align="stretch">
              {friends.map(friend => (
                <Box
                  key={friend.id}
                  p={3}
                  borderRadius="md"
                  bg="white"
                  borderWidth={1}
                  borderColor="green.200"
                  onClick={() => handleFriendClick(friend.id)}
                  cursor="pointer"
                  _hover={{ bg: "green.50" }}
                >
                  <HStack justifyContent="space-between">
                    <Text fontWeight="medium">{friend.name}</Text>
                    <Badge colorScheme="blue">
                      {friendCounts[friend.id] || 0} items
                    </Badge>
                  </HStack>
                </Box>
              ))}
            </VStack>
          </Box>
        </GridItem>
      </Grid>

      <Button
        colorScheme="green"
        size="lg"
        width="100%"
        onClick={handleCompleteClick}
        isDisabled={assignedQuantity < totalQuantity}
      >
        Complete Assignment
      </Button>

      {/* Split Item Modal */}
      <Modal isOpen={isOpen} onClose={onClose}>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>
            Split Item Between Friends
          </ModalHeader>
          <ModalCloseButton />
          <ModalBody>
            <Text mb={4}>
              Select all friends who will share this item:
            </Text>
            <VStack align="stretch" spacing={2}>
              {friends.map(friend => (
                <Flex
                  key={friend.id}
                  p={2}
                  borderWidth={1}
                  borderRadius="md"
                  alignItems="center"
                  borderColor={selectedFriends.includes(friend.id) ? "blue.500" : "gray.200"}
                  bg={selectedFriends.includes(friend.id) ? "blue.50" : "white"}
                  onClick={() => toggleFriendSelection(friend.id)}
                  cursor="pointer"
                  _hover={{ bg: "blue.50" }}
                >
                  <Text flex="1">{friend.name}</Text>
                  {selectedFriends.includes(friend.id) && (
                    <Badge colorScheme="blue">Selected</Badge>
                  )}
                </Flex>
              ))}
            </VStack>
            {selectedFriends.length > 0 && (
              <Text mt={4} fontSize="sm" color="gray.600">
                This item will be split evenly between {selectedFriends.length} people.
              </Text>
            )}
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onClose}>
              Cancel
            </Button>
            <Button
              colorScheme="blue"
              onClick={handleSplitConfirm}
              isDisabled={selectedFriends.length === 0}
            >
              Confirm Split
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </VStack>
  );
};

export default ItemMatching;