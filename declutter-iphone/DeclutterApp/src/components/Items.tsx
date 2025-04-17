import React, { useState, useEffect } from 'react';
import { StyleSheet, View, Text, FlatList, TouchableOpacity, Alert, Image } from 'react-native';
import { supabase } from '../lib/supabase';
import { Card, Button, Badge } from '@rneui/themed';
import { useNavigation } from '@react-navigation/native';
import { StackNavigationProp } from '@react-navigation/stack';
import { RootStackParamList } from '../../App';

// Define the Item type
interface Item {
  id: number;
  name: string;
  description: string;
  price: number;
  status: string;
  created_at: string;
  updated_at: string;
  photo_url?: string;
  sold_to?: string;
}

type NavigationProp = StackNavigationProp<RootStackParamList>;

interface ItemsProps {
  status?: 'available' | 'claimed' | 'complete' | 'paid_ready' | 'sold_to' | ('available' | 'claimed' | 'complete' | 'paid_ready' | 'sold_to')[];
  showStatus?: boolean;
}

export default function Items({ status = 'available', showStatus = false }: ItemsProps) {
  const [loading, setLoading] = useState(true);
  const [items, setItems] = useState<Item[]>([]);
  const [soldToValue, setSoldToValue] = useState('');
  const navigation = useNavigation<NavigationProp>();

  useEffect(() => {
    getItems();
  }, [status]);

  async function getItems() {
    try {
      setLoading(true);

      let query = supabase
        .from('items')
        .select('*');

      if (status) {
        if (Array.isArray(status)) {
          query = query.in('status', status);
        } else {
          query = query.eq('status', status);
        }
      }

      const { data, error } = await query.order('created_at', { ascending: false });

      if (error) {
        throw error;
      }

      if (data) {
        setItems(data as Item[]);
      }
    } catch (error) {
      if (error instanceof Error) {
        Alert.alert('Error', error.message);
      }
    } finally {
      setLoading(false);
    }
  }

  async function updateItemStatus(id: number, newStatus: string, soldTo?: string) {
    try {
      setLoading(true);

      const updates: any = {
        id,
        status: newStatus,
        updated_at: new Date().toISOString(),
      };

      if (soldTo) {
        updates.sold_to = soldTo;
      }

      const { error } = await supabase.from('items').update(updates).eq('id', id);

      if (error) {
        throw error;
      }

      Alert.alert('Success', 'Item status updated!');
      getItems();
    } catch (error) {
      if (error instanceof Error) {
        Alert.alert('Error', error.message);
      }
    } finally {
      setLoading(false);
    }
  }

  // Helper function to prompt for sold_to name
  const promptForSoldTo = (id: number) => {
    Alert.prompt(
      'Sold To',
      'Enter the name of the person who bought this item:',
      [
        {
          text: 'Cancel',
          style: 'cancel',
        },
        {
          text: 'OK',
          onPress: (value?: string) => {
            if (value && value.trim()) {
              updateItemStatus(id, 'sold_to', value.trim());
            } else {
              Alert.alert('Error', 'Please enter a name.');
            }
          },
        },
      ],
      'plain-text'
    );
  };

  // Get the appropriate status badge color
  const getStatusColor = (itemStatus: string) => {
    switch (itemStatus) {
      case 'available':
        return '#FFD700'; // Yellow
      case 'claimed':
        return '#9370DB'; // Purple
      case 'paid_ready':
        return '#1E90FF'; // Blue
      case 'complete':
        return '#4CAF50'; // Green
      case 'sold_to':
        return '#808080'; // Gray
      default:
        return '#F5F5F5'; // Light gray
    }
  };

  // Format status text for display
  const formatStatusText = (statusText: string) => {
    return statusText.replace('_', ' ').replace(/\b\w/g, (c) => c.toUpperCase());
  };

  // Handle item edit
  const handleEditItem = (itemId: number) => {
    navigation.navigate('EditItem', { itemId });
  };

  const renderItem = ({ item }: { item: Item }) => (
    <TouchableOpacity onPress={() => handleEditItem(item.id)}>
      <Card containerStyle={styles.card}>
        <Card.Title>{item.name}</Card.Title>
        <Card.Divider />
        
        {/* Always show the photo if it exists */}
        {item.photo_url ? (
          <Image 
            source={{ uri: `https://dbhnhwkzhwjyczsbhdqa.supabase.co/storage/v1/object/public/photos/${item.photo_url}` }} 
            style={styles.itemImage} 
            resizeMode="cover"
          />
        ) : (
          <View style={styles.photoPlaceholder}>
            <Text style={styles.photoPlaceholderText}>No photo available</Text>
          </View>
        )}
        
        <Text style={styles.description}>{item.description}</Text>
        <Text style={styles.price}>Price: ${(item.price || 0).toFixed(2)}</Text>
        
        <View style={styles.statusContainer}>
          {/* Show status badge if showStatus is true or we're viewing a mixed set of statuses */}
          {(showStatus || Array.isArray(status)) && (
            <Badge 
              value={formatStatusText(item.status)}
              badgeStyle={{ backgroundColor: getStatusColor(item.status) }}
              textStyle={styles.badgeText}
              containerStyle={styles.badge}
            />
          )}
          
          {item.sold_to && (
            <Text style={styles.soldTo}>Sold to: {item.sold_to}</Text>
          )}
        </View>
        
        <View style={styles.buttonContainer}>
          {/* Show edit button explicitly */}
          <Button
            title="Edit"
            onPress={() => handleEditItem(item.id)}
            buttonStyle={[styles.button, styles.editButton]}
            icon={{ name: 'edit', color: 'white', size: 16 }}
          />
          
          {/* Action buttons based on item status */}
          {item.status === 'available' && (
            <>
              <Button
                title="Claim"
                onPress={() => updateItemStatus(item.id, 'claimed')}
                buttonStyle={[styles.button, styles.claimButton]}
              />
              <Button
                title="Paid"
                onPress={() => updateItemStatus(item.id, 'paid_ready')}
                buttonStyle={[styles.button, styles.paidReadyButton]}
              />
            </>
          )}
          
          {item.status === 'claimed' && (
            <Button
              title="Complete"
              onPress={() => updateItemStatus(item.id, 'complete')}
              buttonStyle={[styles.button, styles.completeButton]}
            />
          )}
          
          {item.status === 'paid_ready' && (
            <Button
              title="Complete"
              onPress={() => updateItemStatus(item.id, 'complete')}
              buttonStyle={[styles.button, styles.completeButton]}
            />
          )}
          
          {item.status === 'complete' && (
            <Button
              title="Sold To"
              onPress={() => promptForSoldTo(item.id)}
              buttonStyle={[styles.button, styles.soldToButton]}
            />
          )}
        </View>
      </Card>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <FlatList
        data={items}
        renderItem={renderItem}
        keyExtractor={(item) => item.id.toString()}
        refreshing={loading}
        onRefresh={getItems}
        ListEmptyComponent={() => (
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyText}>No items found</Text>
          </View>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 10,
  },
  card: {
    marginBottom: 15,
    borderRadius: 10,
    elevation: 3,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 3,
  },
  itemImage: {
    width: '100%',
    height: 200,
    borderRadius: 5,
    marginBottom: 10,
  },
  photoPlaceholder: {
    width: '100%',
    height: 200,
    borderRadius: 5,
    backgroundColor: '#f0f0f0',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 10,
  },
  photoPlaceholderText: {
    color: '#888',
    fontSize: 16,
  },
  description: {
    marginBottom: 10,
    fontSize: 14,
  },
  price: {
    fontWeight: 'bold',
    fontSize: 16,
    marginBottom: 10,
  },
  statusContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  badge: {
    marginRight: 5,
  },
  badgeText: {
    fontWeight: 'bold',
  },
  soldTo: {
    fontStyle: 'italic',
    color: '#555',
  },
  buttonContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    flexWrap: 'wrap',
  },
  button: {
    marginTop: 5,
    marginRight: 5,
    paddingHorizontal: 10,
    flex: 1,
    minWidth: 80,
  },
  editButton: {
    backgroundColor: '#555',
  },
  claimButton: {
    backgroundColor: '#9370DB',
  },
  paidReadyButton: {
    backgroundColor: '#1E90FF',
  },
  completeButton: {
    backgroundColor: '#4CAF50',
  },
  soldToButton: {
    backgroundColor: '#808080',
  },
  emptyContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    padding: 20,
  },
  emptyText: {
    fontSize: 16,
    color: '#888',
  },
}); 