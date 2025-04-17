import React, { useState, useEffect } from 'react';
import { StyleSheet, View, Text, FlatList, TouchableOpacity, Alert, ScrollView, ActivityIndicator, Share as RNShare } from 'react-native';
import { Card, Button, Input, Tab, TabView } from '@rneui/themed';
import { supabase } from '../lib/supabase';
import * as FileSystem from 'expo-file-system';
import * as MediaLibrary from 'expo-media-library';
import * as ImageManipulator from 'expo-image-manipulator';

interface PublicLink {
  id: number;
  name: string;
  link_code: string;
  created_at: string;
  is_active: boolean;
}

interface Item {
  id: number;
  name: string;
  description: string;
  price: number;
  status: string;
  photo_url?: string;
}

export default function ShareScreen() {
  const [links, setLinks] = useState<PublicLink[]>([]);
  const [newLinkName, setNewLinkName] = useState('My Items Collection');
  const [loadingLinks, setLoadingLinks] = useState(true);
  const [availableItems, setAvailableItems] = useState<Item[]>([]);
  const [loadingItems, setLoadingItems] = useState(true);
  const [downloadingIndex, setDownloadingIndex] = useState<number | null>(null);
  const [tabIndex, setTabIndex] = useState(0);
  const [downloadingAll, setDownloadingAll] = useState(false);

  useEffect(() => {
    fetchLinks();
    fetchAvailableItems();
  }, []);

  async function fetchLinks() {
    try {
      setLoadingLinks(true);
      const { data: userData } = await supabase.auth.getUser();
      
      if (!userData || !userData.user) {
        throw new Error('No authenticated user');
      }

      const { data, error } = await supabase
        .from('public_links')
        .select('*')
        .eq('user_id', userData.user.id)
        .order('created_at', { ascending: false });

      if (error) {
        throw error;
      }

      setLinks(data || []);
    } catch (error) {
      console.error('Error fetching links:', error);
      Alert.alert('Error', 'Failed to load public links');
    } finally {
      setLoadingLinks(false);
    }
  }

  async function fetchAvailableItems() {
    try {
      setLoadingItems(true);
      
      const { data, error } = await supabase
        .from('items')
        .select('*')
        .eq('status', 'available')
        .order('created_at', { ascending: false });

      if (error) {
        throw error;
      }

      setAvailableItems(data || []);
    } catch (error) {
      console.error('Error fetching items:', error);
      Alert.alert('Error', 'Failed to load available items');
    } finally {
      setLoadingItems(false);
    }
  }

  async function createPublicLink() {
    if (!newLinkName.trim()) {
      Alert.alert('Error', 'Please enter a name for the link');
      return;
    }
    
    try {
      setLoadingLinks(true);
      
      const { data: userData } = await supabase.auth.getUser();
      if (!userData || !userData.user) {
        throw new Error('No authenticated user');
      }
      
      // Generate a random code
      const linkCode = Math.random().toString(36).substring(2, 10);
      
      const { data, error } = await supabase
        .from('public_links')
        .insert([{
          name: newLinkName.trim(),
          link_code: linkCode,
          user_id: userData.user.id,
          is_active: true
        }])
        .select();
      
      if (error) {
        throw error;
      }
      
      Alert.alert('Success', 'Public link created successfully');
      fetchLinks();
      setNewLinkName('My Items Collection');
    } catch (error) {
      console.error('Error creating link:', error);
      Alert.alert('Error', 'Failed to create public link');
    } finally {
      setLoadingLinks(false);
    }
  }

  async function updateLinkStatus(id: number, isActive: boolean) {
    try {
      setLoadingLinks(true);
      
      const { error } = await supabase
        .from('public_links')
        .update({ is_active: isActive })
        .eq('id', id);
      
      if (error) {
        throw error;
      }
      
      Alert.alert('Success', isActive ? 'Link activated' : 'Link deactivated');
      fetchLinks();
    } catch (error) {
      console.error('Error updating link:', error);
      Alert.alert('Error', 'Failed to update link status');
    } finally {
      setLoadingLinks(false);
    }
  }

  async function deleteLink(id: number) {
    try {
      setLoadingLinks(true);
      
      const { error } = await supabase
        .from('public_links')
        .delete()
        .eq('id', id);
      
      if (error) {
        throw error;
      }
      
      Alert.alert('Success', 'Link deleted successfully');
      fetchLinks();
    } catch (error) {
      console.error('Error deleting link:', error);
      Alert.alert('Error', 'Failed to delete link');
    } finally {
      setLoadingLinks(false);
    }
  }

  async function shareLink(linkCode: string) {
    try {
      const url = `https://declutter.bazil.studio?code=${linkCode}`;
      await RNShare.share({
        message: 'Check out items I have for sale',
        url
      });
    } catch (error) {
      console.error('Error sharing link:', error);
      Alert.alert('Error', 'Failed to share link');
    }
  }

  async function downloadPhoto(item: Item, index: number) {
    try {
      setDownloadingIndex(index);
      
      // Request permissions
      const { status } = await MediaLibrary.requestPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Permission needed', 'We need permission to save photos to your gallery');
        return;
      }

      if (!item.photo_url) {
        Alert.alert('Error', 'No photo available for this item');
        return;
      }

      // Download the photo
      const photoUri = `https://dbhnhwkzhwjyczsbhdqa.supabase.co/storage/v1/object/public/photos/${item.photo_url}`;
      const fileUri = FileSystem.documentDirectory + `item_${item.id}.jpg`;
      
      const downloadResult = await FileSystem.downloadAsync(photoUri, fileUri);

      if (downloadResult.status !== 200) {
        throw new Error('Failed to download photo');
      }

      // Add price overlay
      const manipResult = await ImageManipulator.manipulateAsync(
        fileUri,
        [],
        {
          format: ImageManipulator.SaveFormat.JPEG,
          compress: 0.8,
        }
      );

      // Save to gallery
      const asset = await MediaLibrary.createAssetAsync(manipResult.uri);
      await MediaLibrary.createAlbumAsync('Declutter Items', asset, false);

      Alert.alert('Success', 'Photo saved to gallery');
    } catch (error) {
      console.error('Error downloading photo:', error);
      Alert.alert('Error', 'Failed to download photo');
    } finally {
      setDownloadingIndex(null);
    }
  }

  async function downloadAllPhotos() {
    try {
      setDownloadingAll(true);
      
      // Request permissions
      const { status } = await MediaLibrary.requestPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Permission needed', 'We need permission to save photos to your gallery');
        return;
      }

      const itemsWithPhotos = availableItems.filter(item => item.photo_url);
      
      if (itemsWithPhotos.length === 0) {
        Alert.alert('No photos', 'There are no photos to download');
        return;
      }

      for (let i = 0; i < itemsWithPhotos.length; i++) {
        const item = itemsWithPhotos[i];
        
        if (!item.photo_url) continue;

        // Download the photo
        const photoUri = `https://dbhnhwkzhwjyczsbhdqa.supabase.co/storage/v1/object/public/photos/${item.photo_url}`;
        const fileUri = FileSystem.documentDirectory + `item_${item.id}.jpg`;
        
        const downloadResult = await FileSystem.downloadAsync(photoUri, fileUri);

        if (downloadResult.status !== 200) {
          continue;
        }

        // Add price overlay
        const manipResult = await ImageManipulator.manipulateAsync(
          fileUri,
          [],
          {
            format: ImageManipulator.SaveFormat.JPEG,
            compress: 0.8,
          }
        );

        // Save to gallery
        const asset = await MediaLibrary.createAssetAsync(manipResult.uri);
        await MediaLibrary.createAlbumAsync('Declutter Items', asset, false);
      }

      Alert.alert('Success', `${itemsWithPhotos.length} photos saved to gallery`);
    } catch (error) {
      console.error('Error downloading photos:', error);
      Alert.alert('Error', 'Failed to download photos');
    } finally {
      setDownloadingAll(false);
    }
  }

  const renderPublicLinksTab = () => (
    <ScrollView style={styles.container} contentContainerStyle={{ paddingBottom: 20 }}>
      <Card containerStyle={styles.card}>
        <Card.Title>Create New Public Link</Card.Title>
        <Input
          placeholder="Enter link name"
          value={newLinkName}
          onChangeText={setNewLinkName}
        />
        <Button
          title="Create Link"
          onPress={createPublicLink}
          loading={loadingLinks}
          buttonStyle={styles.createButton}
        />
      </Card>

      {loadingLinks ? (
        <ActivityIndicator size="large" color="#0000ff" style={styles.loader} />
      ) : links.length === 0 ? (
        <Text style={styles.noDataText}>No public links created yet</Text>
      ) : (
        <>
          <Text style={styles.sectionTitle}>Active Links</Text>
          {links.filter(link => link.is_active).map(link => (
            <Card key={link.id} containerStyle={styles.linkCard}>
              <Text style={styles.linkName}>{link.name}</Text>
              <Text style={styles.linkDate}>Created: {new Date(link.created_at).toLocaleDateString()}</Text>
              <Text style={styles.linkCode}>{`https://declutter.bazil.studio?code=${link.link_code}`}</Text>
              <View style={styles.buttonRow}>
                <Button
                  title="Share"
                  icon={{ name: 'share', color: 'white', size: 16 }}
                  onPress={() => shareLink(link.link_code)}
                  buttonStyle={[styles.actionButton, styles.shareButton]}
                />
                <Button
                  title="Deactivate"
                  onPress={() => updateLinkStatus(link.id, false)}
                  buttonStyle={[styles.actionButton, styles.deactivateButton]}
                />
              </View>
            </Card>
          ))}

          <Text style={styles.sectionTitle}>Inactive Links</Text>
          {links.filter(link => !link.is_active).map(link => (
            <Card key={link.id} containerStyle={styles.linkCard}>
              <Text style={styles.linkName}>{link.name}</Text>
              <Text style={styles.linkDate}>Created: {new Date(link.created_at).toLocaleDateString()}</Text>
              <Text style={styles.linkCode}>{`https://declutter.bazil.studio?code=${link.link_code}`}</Text>
              <View style={styles.buttonRow}>
                <Button
                  title="Activate"
                  onPress={() => updateLinkStatus(link.id, true)}
                  buttonStyle={[styles.actionButton, styles.activateButton]}
                />
                <Button
                  title="Delete"
                  onPress={() => deleteLink(link.id)}
                  buttonStyle={[styles.actionButton, styles.deleteButton]}
                />
              </View>
            </Card>
          ))}
        </>
      )}
    </ScrollView>
  );

  const renderPhotosTab = () => (
    <View style={styles.container}>
      <Button
        title="Download All Photos"
        onPress={downloadAllPhotos}
        loading={downloadingAll}
        buttonStyle={styles.downloadAllButton}
        containerStyle={styles.downloadAllContainer}
      />
      
      {loadingItems ? (
        <ActivityIndicator size="large" color="#0000ff" style={styles.loader} />
      ) : availableItems.length === 0 ? (
        <Text style={styles.noDataText}>No available items with photos</Text>
      ) : (
        <FlatList
          data={availableItems}
          renderItem={({ item, index }) => (
            <Card containerStyle={styles.itemCard}>
              {item.photo_url ? (
                <View>
                  <Card.Image
                    source={{ uri: `https://dbhnhwkzhwjyczsbhdqa.supabase.co/storage/v1/object/public/photos/${item.photo_url}` }}
                    style={styles.itemImage}
                  />
                  <Text style={styles.itemName}>{item.name}</Text>
                  <Text style={styles.itemPrice}>${(item.price || 0).toFixed(2)}</Text>
                  <Button
                    title="Download Photo"
                    onPress={() => downloadPhoto(item, index)}
                    loading={downloadingIndex === index}
                    buttonStyle={styles.downloadButton}
                  />
                </View>
              ) : (
                <Text style={styles.noPhotoText}>No photo available for {item.name}</Text>
              )}
            </Card>
          )}
          keyExtractor={(item) => item.id.toString()}
          numColumns={2}
          contentContainerStyle={styles.photoGrid}
        />
      )}
    </View>
  );

  return (
    <View style={styles.mainContainer}>
      <Tab
        value={tabIndex}
        onChange={setTabIndex}
        indicatorStyle={{ backgroundColor: 'blue' }}
      >
        <Tab.Item
          title="Public Links"
          titleStyle={{ fontSize: 12 }}
          icon={{ name: 'link', type: 'material', color: tabIndex === 0 ? 'blue' : 'gray' }}
        />
        <Tab.Item
          title="Photos"
          titleStyle={{ fontSize: 12 }}
          icon={{ name: 'photo', type: 'material', color: tabIndex === 1 ? 'blue' : 'gray' }}
        />
      </Tab>

      <TabView value={tabIndex} onChange={setTabIndex} animationType="spring">
        <TabView.Item style={{ width: '100%' }}>
          {renderPublicLinksTab()}
        </TabView.Item>
        <TabView.Item style={{ width: '100%' }}>
          {renderPhotosTab()}
        </TabView.Item>
      </TabView>
    </View>
  );
}

const styles = StyleSheet.create({
  mainContainer: {
    flex: 1,
    backgroundColor: '#fff',
  },
  container: {
    flex: 1,
    padding: 10,
  },
  card: {
    borderRadius: 10,
    marginBottom: 15,
  },
  createButton: {
    backgroundColor: '#2196F3',
    borderRadius: 5,
    marginTop: 10,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginVertical: 10,
    marginLeft: 10,
  },
  linkCard: {
    borderRadius: 10,
    marginBottom: 10,
  },
  linkName: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 5,
  },
  linkDate: {
    fontSize: 12,
    color: '#666',
    marginBottom: 5,
  },
  linkCode: {
    fontSize: 14,
    backgroundColor: '#f0f0f0',
    padding: 10,
    borderRadius: 5,
    marginBottom: 10,
  },
  buttonRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  actionButton: {
    paddingHorizontal: 10,
    height: 40,
  },
  shareButton: {
    backgroundColor: '#4CAF50',
  },
  activateButton: {
    backgroundColor: '#2196F3',
  },
  deactivateButton: {
    backgroundColor: '#FF9800',
  },
  deleteButton: {
    backgroundColor: '#F44336',
  },
  loader: {
    marginTop: 30,
  },
  noDataText: {
    textAlign: 'center',
    fontSize: 16,
    color: '#666',
    marginTop: 30,
  },
  itemCard: {
    flex: 1,
    margin: 5,
    borderRadius: 10,
  },
  itemImage: {
    height: 150,
    width: '100%',
    borderRadius: 5,
  },
  itemName: {
    fontSize: 14,
    fontWeight: 'bold',
    marginTop: 5,
    textAlign: 'center',
  },
  itemPrice: {
    fontSize: 14,
    color: '#2196F3',
    marginBottom: 10,
    textAlign: 'center',
  },
  downloadButton: {
    backgroundColor: '#2196F3',
    borderRadius: 5,
  },
  noPhotoText: {
    textAlign: 'center',
    color: '#666',
    padding: 15,
  },
  photoGrid: {
    paddingBottom: 20,
  },
  downloadAllButton: {
    backgroundColor: '#4CAF50',
    borderRadius: 5,
  },
  downloadAllContainer: {
    margin: 10,
  },
}); 