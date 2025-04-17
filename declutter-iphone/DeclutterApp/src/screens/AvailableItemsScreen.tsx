import React from 'react';
import { View } from 'react-native';
import Items from '../components/Items';

export default function AvailableItemsScreen() {
  return (
    <View style={{ flex: 1 }}>
      <Items status="available" />
    </View>
  );
} 