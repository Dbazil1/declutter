import React, { useState, useEffect } from 'react';
import { StyleSheet, View, Text, FlatList, TouchableOpacity, Alert, Share, Clipboard, Platform } from 'react-native';
import { Card, Button, Divider, Icon } from '@rneui/themed';
import { supabase } from '../lib/supabase';

// Define the Item type
interface Item {
  id: number;
  name: string;
  photo_url?: string;
  user_id: string;
  created_at: string;
}

export default function PublicLinks() {
  const [loading, setLoading] = useState(true);
  const [items, setItems] = useState<Item[]>([]);

  useEffect(() => {
    getItems();
  }, []);

  async function getItems() {
    try {
      setLoading(true);

      // Get current user
      const { data: userData } = await supabase.auth.getUser();
      
      if (!userData?.user) {
        Alert.alert('Error', 'User not found');
        return;
      }

      // Get all items by the current user
      const { data, error } = await supabase
        .from('items')
        .select('id, name, photo_url, user_id, created_at')
        .eq('user_id', userData.user.id)
        .order('created_at', { ascending: false });

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

  const getPublicUrl = (id: number) => {
    // This would be replaced with your actual public URL structure
    const baseUrl = 'https://declutter.bazil.studio/items/';
    return `${baseUrl}${id}`;
  };

  const shareItem = async (item: Item) => {
    const url = getPublicUrl(item.id);
    try {
      const result = await Share.share({
        message: `Check out this item: ${item.name}`,
        url: url,
        title: item.name,
      });
      
      if (result.action === Share.sharedAction) {
        if (result.activityType) {
          console.log(`Shared via ${result.activityType}`);
        } else {
          console.log('Shared');
        }
      } else if (result.action === Share.dismissedAction) {
        console.log('Share dismissed');
      }
    } catch (error) {
      console.error(error);
      Alert.alert('Error', 'Could not share item');
    }
  };

  const copyToClipboard = (id: number) => {
    const url = getPublicUrl(id);
    Clipboard.setString(url);
    Alert.alert('Success', 'Link copied to clipboard');
  };

  const renderItem = ({ item }: { item: Item }) => (
    <Card containerStyle={styles.card}>
      <Card.Title>{item.name}</Card.Title>
      <Divider style={{ marginBottom: 10 }} />
      
      <View style={styles.linkContainer}>
        <Text style={styles.linkLabel}>Public Link:</Text>
        <Text style={styles.link} numberOfLines={1} ellipsizeMode="middle">
          {getPublicUrl(item.id)}
        </Text>
      </View>
      
      <View style={styles.buttonContainer}>
        <Button
          title="Share"
          icon={<Icon name="share" color="white" size={16} style={{ marginRight: 8 }} />}
          onPress={() => shareItem(item)}
          buttonStyle={[styles.button, styles.shareButton]}
        />
        <Button
          title="Copy"
          icon={<Icon name="content-copy" color="white" size={16} style={{ marginRight: 8 }} />}
          onPress={() => copyToClipboard(item.id)}
          buttonStyle={[styles.button, styles.copyButton]}
        />
      </View>
    </Card>
  );

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Public Links</Text>
      <Text style={styles.description}>
        Share these links with potential buyers to let them view your items.
      </Text>
      
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
    padding: 16,
    backgroundColor: '#fff',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 8,
    textAlign: 'center',
  },
  description: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
    marginBottom: 20,
  },
  card: {
    marginBottom: 15,
    borderRadius: 10,
    elevation: 3,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 3,
  },
  linkContainer: {
    marginBottom: 15,
    padding: 10,
    backgroundColor: '#f5f5f5',
    borderRadius: 5,
  },
  linkLabel: {
    fontWeight: 'bold',
    marginBottom: 5,
  },
  link: {
    color: '#0066cc',
  },
  buttonContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  button: {
    flex: 0.48,
  },
  shareButton: {
    backgroundColor: '#2196F3',
  },
  copyButton: {
    backgroundColor: '#4CAF50',
  },
  emptyContainer: {
    padding: 20,
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 16,
    color: '#777',
  }
}); 