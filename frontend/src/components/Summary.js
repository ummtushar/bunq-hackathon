import React from 'react';
import {
  VStack, Box, Text, Button, Divider,
  Table, Thead, Tbody, Tr, Th, Td,
  Heading, Badge, Tooltip
} from '@chakra-ui/react';
import { InfoIcon } from '@chakra-ui/icons';

const Summary = ({ items, friends, assignments, splitItems, onReset }) => {
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

  // Add up items for each friend, handling split items properly
  Object.entries(assignments).forEach(([itemId, friendIds]) => {
    const item = items.find(i => i.id === itemId);
    const isSplitItem = splitItems[itemId] !== undefined;

    friendIds.forEach(friendId => {
      // Get the split count if this is a split item
      const splitCount = isSplitItem ? splitItems[itemId].splitCount : 1;

      // Calculate split price (divide price by number of people sharing)
      const pricePerPerson = isSplitItem ? item.price / splitCount : item.price;

      friendTotals[friendId].items.push({
        name: item.name,
        price: pricePerPerson,
        originalPrice: item.price,
        isSplit: isSplitItem,
        splitCount: splitCount
      });

      friendTotals[friendId].total += pricePerPerson;
    });
  });

  const totalBill = items.reduce((sum, item) => sum + (item.price * item.quantity), 0);

  // Format currency
  const formatCurrency = (amount) => {
    return `€${amount.toFixed(2)}`;
  };

  return (
    <VStack spacing={6} width="100%">
      <Heading size="lg">Bill Summary</Heading>

      <Box width="100%" borderWidth={1} borderRadius="md" p={4}>
        <Heading size="md" mb={4}>Overview</Heading>

        <Table variant="simple" size="sm">
          <Tbody>
            <Tr>
              <Td fontWeight="bold">Total Bill</Td>
              <Td isNumeric>{formatCurrency(totalBill)}</Td>
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
              <span>{formatCurrency(friend.total)}</span>
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
                    <Td>
                      {item.name}
                      {item.isSplit && (
                        <Tooltip
                          label={`Split ${formatCurrency(item.originalPrice)} between ${item.splitCount} people`}
                          placement="top"
                        >
                          <Badge ml={2} colorScheme="purple">
                            Split {item.splitCount} ways
                          </Badge>
                        </Tooltip>
                      )}
                    </Td>
                    <Td isNumeric>
                      {formatCurrency(item.price)}
                      {item.isSplit && (
                        <Text as="span" fontSize="xs" color="gray.500" ml={1}>
                          ({formatCurrency(item.originalPrice)} ÷ {item.splitCount})
                        </Text>
                      )}
                    </Td>
                  </Tr>
                ))}
                <Tr fontWeight="bold">
                  <Td>Total</Td>
                  <Td isNumeric>{formatCurrency(friend.total)}</Td>
                </Tr>
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