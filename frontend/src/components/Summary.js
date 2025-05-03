import React from 'react';
import {
  VStack, Box, Text, Button, Divider,
  Table, Thead, Tbody, Tr, Th, Td,
  Heading, Badge
} from '@chakra-ui/react';

const Summary = ({ items, friends, assignments, onReset }) => {
  // Calculate what each friend owes
  const friendTotals = {};

  // Initialize totals for each friend
  friends.forEach(friend => {
    friendTotals[friend.id] = {
      name: friend.name,
      items: [],
      total: 0
    };
  });

  // Add up items for each friend
  Object.entries(assignments).forEach(([itemId, friendIds]) => {
    const item = items.find(i => i.id === itemId);

    friendIds.forEach(friendId => {
      friendTotals[friendId].items.push({
        name: item.name,
        price: item.price
      });

      friendTotals[friendId].total += item.price;
    });
  });

  const totalBill = items.reduce((sum, item) => sum + (item.price * item.quantity), 0);

  return (
    <VStack spacing={6} width="100%">
      <Heading size="lg">Bill Summary</Heading>

      <Box width="100%" borderWidth={1} borderRadius="md" p={4}>
        <Heading size="md" mb={4}>Overview</Heading>

        <Table variant="simple" size="sm">
          <Tbody>
            <Tr>
              <Td fontWeight="bold">Total Bill</Td>
              <Td isNumeric>€{totalBill.toFixed(2)}</Td>
            </Tr>
            <Tr>
              <Td fontWeight="bold">Number of People</Td>
              <Td isNumeric>{friends.length}</Td>
            </Tr>
          </Tbody>
        </Table>
      </Box>

      <Box width="100%" borderWidth={1} borderRadius="md" p={4}>
        <Heading size="md" mb={4}>Individual Breakdown</Heading>

        {Object.values(friendTotals).map((friend) => (
          <Box key={friend.name} mb={6}>
            <Heading size="sm" mb={2} display="flex" justifyContent="space-between">
              <span>{friend.name}</span>
              <span>€{friend.total.toFixed(2)}</span>
            </Heading>

            <Table variant="simple" size="sm">
              <Thead>
                <Tr>
                  <Th>Item</Th>
                  <Th isNumeric>Price</Th>
                </Tr>
              </Thead>
              <Tbody>
                {friend.items.map((item, index) => (
                  <Tr key={index}>
                    <Td>{item.name}</Td>
                    <Td isNumeric>€{item.price.toFixed(2)}</Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
          </Box>
        ))}
      </Box>

      <Button onClick={onReset} colorScheme="blue" size="lg">
        Start New Split
      </Button>
    </VStack>
  );
};

export default Summary;