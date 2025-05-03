import React, { useState } from 'react';
import {
  VStack, HStack, Input, Button, Text,
  Box, List, ListItem, IconButton,
  Alert, AlertIcon
} from '@chakra-ui/react';
import { CloseIcon } from '@chakra-ui/icons';

const FriendInput = ({ onFriendsAdded }) => {
  const [friendName, setFriendName] = useState('');
  const [friends, setFriends] = useState([]);
  const [error, setError] = useState(null);

  const handleAddFriend = () => {
    if (!friendName.trim()) {
      setError('Please enter a friend name');
      return;
    }

    // Add friend with a unique ID
    const newFriend = {
      id: `friend-${Date.now()}`,
      name: friendName.trim()
    };

    setFriends([...friends, newFriend]);
    setFriendName('');
    setError(null);
  };

  const handleRemoveFriend = (friendId) => {
    setFriends(friends.filter(friend => friend.id !== friendId));
  };

  const handleContinue = () => {
    if (friends.length === 0) {
      setError('Please add at least one friend');
      return;
    }

    // Include yourself in the list
    const friendsWithYou = [
      { id: 'you', name: 'You (Me)' },
      ...friends
    ];

    onFriendsAdded(friendsWithYou);
  };

  return (
    <VStack spacing={4}>
      <Text fontSize="lg" fontWeight="medium">
        Who's splitting this bill?
      </Text>

      <Box width="100%">
        <HStack>
          <Input
            placeholder="Enter a friend's name"
            value={friendName}
            onChange={(e) => setFriendName(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter') handleAddFriend();
            }}
          />
          <Button onClick={handleAddFriend} colorScheme="blue">
            Add
          </Button>
        </HStack>

        {error && (
          <Alert status="error" mt={2} size="sm" borderRadius="md">
            <AlertIcon />
            {error}
          </Alert>
        )}
      </Box>

      <Box width="100%" borderWidth={1} borderRadius="md" p={4}>
        <Text fontWeight="medium" mb={2}>
          Friends List:
        </Text>

        <List spacing={2}>
          <ListItem p={2} bg="gray.100" borderRadius="md">
            You (Me) <Text as="span" fontSize="sm" color="green.500">(Automatically included)</Text>
          </ListItem>

          {friends.map(friend => (
            <ListItem
              key={friend.id}
              p={2}
              bg="blue.50"
              borderRadius="md"
              display="flex"
              justifyContent="space-between"
              alignItems="center"
            >
              {friend.name}
              <IconButton
                size="sm"
                icon={<CloseIcon />}
                onClick={() => handleRemoveFriend(friend.id)}
                aria-label="Remove friend"
                variant="ghost"
                colorScheme="red"
              />
            </ListItem>
          ))}
        </List>
      </Box>

      <Button
        onClick={handleContinue}
        colorScheme="green"
        size="lg"
        width="100%"
        isDisabled={friends.length === 0}
      >
        Continue to Item Matching
      </Button>
    </VStack>
  );
};

export default FriendInput;