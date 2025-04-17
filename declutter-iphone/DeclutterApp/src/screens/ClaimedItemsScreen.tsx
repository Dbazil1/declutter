import React from 'react';
import { View } from 'react-native';
import Items from '../components/Items';

export default function ClaimedItemsScreen() {
  return (
    <View style={{ flex: 1 }}>
      <Items 
        status={["claimed", "paid_ready", "complete"]} 
        showStatus={true} 
      />
    </View>
  );
} 