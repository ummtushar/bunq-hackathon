import React, { useState } from 'react';
import { ChakraProvider, Box, VStack, Heading } from '@chakra-ui/react';
import ReceiptUploader from './components/ReceiptUploader';
import FriendInput from './components/FriendInput';
import ItemMatching from './components/ItemMatching';
import Summary from './components/Summary';
import './App.css';

function App() {
  const [receiptData, setReceiptData] = useState(null);
  const [friends, setFriends] = useState([]);
  const [assignments, setAssignments] = useState({});
  const [step, setStep] = useState(1); // 1: Upload, 2: Add Friends, 3: Match Items, 4: Summary

  const handleReceiptProcessed = (data) => {
    // Transform receipt items to track quantities
    const itemsWithQuantities = {};

    data.items.forEach(item => {
      const key = `${item.name}-${item.price}`;
      if (!itemsWithQuantities[key]) {
        itemsWithQuantities[key] = {
          ...item,
          id: key,
          quantity: 1,
          remainingQuantity: 1
        };
      } else {
        itemsWithQuantities[key].quantity += 1;
        itemsWithQuantities[key].remainingQuantity += 1;
      }
    });

    // Convert back to array
    const processedItems = Object.values(itemsWithQuantities);

    setReceiptData({
      ...data,
      processedItems
    });
    setStep(2); // Move to Add Friends step
  };

  const handleFriendsAdded = (friendsList) => {
    setFriends(friendsList);
    setStep(3); // Move to Match Items step
  };

  const handleItemAssigned = (itemId, friendId) => {
    setAssignments(prev => {
      const newAssignments = {...prev};

      if (!newAssignments[itemId]) {
        newAssignments[itemId] = [];
      }

      newAssignments[itemId].push(friendId);

      return newAssignments;
    });

    // Update remaining quantity
    setReceiptData(prev => {
      const updatedItems = prev.processedItems.map(item => {
        if (item.id === itemId && item.remainingQuantity > 0) {
          return {
            ...item,
            remainingQuantity: item.remainingQuantity - 1
          };
        }
        return item;
      });

      return {
        ...prev,
        processedItems: updatedItems
      };
    });
  };

  const handleComplete = () => {
    setStep(4); // Move to Summary step
  };

  const resetApp = () => {
    setReceiptData(null);
    setFriends([]);
    setAssignments({});
    setStep(1);
  };

  return (
    <ChakraProvider>
      <Box p={5}>
        <VStack spacing={6} align="stretch">
          <Heading as="h1" size="xl" textAlign="center" mb={6}>
            Receipt Splitter
          </Heading>

          {step === 1 && (
            <ReceiptUploader onReceiptProcessed={handleReceiptProcessed} />
          )}

          {step === 2 && (
            <FriendInput onFriendsAdded={handleFriendsAdded} />
          )}

          {step === 3 && receiptData && (
            <ItemMatching
              items={receiptData.processedItems}
              friends={friends}
              assignments={assignments}
              onItemAssigned={handleItemAssigned}
              onComplete={handleComplete}
            />
          )}

          {step === 4 && (
            <Summary
              items={receiptData.processedItems}
              friends={friends}
              assignments={assignments}
              onReset={resetApp}
            />
          )}
        </VStack>
      </Box>
    </ChakraProvider>
  );
}

export default App;
