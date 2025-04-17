import React from 'react';
import { View } from 'react-native';
import Items from '../components/Items';

export default function SoldItemsScreen() {
  return (
    <View style={{ flex: 1 }}>
      <Items status="sold_to" />
    </View>
  );
} 