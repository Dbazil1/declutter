import React, { useState, useEffect } from 'react';
import { StyleSheet, View, Text, TextInput, TouchableOpacity, Image, ActivityIndicator, Alert, ScrollView, KeyboardAvoidingView, Platform } from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { supabase } from '../lib/supabase';
import * as FileSystem from 'expo-file-system';
import { decode } from 'base64-arraybuffer';
import { FontAwesome } from '@expo/vector-icons';
import { useNavigation } from '@react-navigation/native';

interface EditItemProps {
  itemId: number;
  onSuccess?: () => void;
}

export default function EditItem({ itemId, onSuccess }: EditItemProps) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [price, setPrice] = useState('');
  const [photo, setPhoto] = useState<string | null>(null);
  const [photoUrl, setPhotoUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingItem, setLoadingItem] = useState(true);
  const [photoChanged, setPhotoChanged] = useState(false);
  const navigation = useNavigation();

  useEffect(() => {
    getItem();
  }, [itemId]);

  async function getItem() {
    try {
      setLoadingItem(true);
      
      const { data, error } = await supabase
        .from('items')
        .select('*')
        .eq('id', itemId)
        .single();
      
      if (error) {
        throw error;
      }
      
      if (data) {
        setName(data.name || '');
        setDescription(data.description || '');
        setPrice(data.price ? data.price.toString() : '');
        if (data.photo_url) {
          setPhotoUrl(data.photo_url);
        }
      }
    } catch (error) {
      if (error instanceof Error) {
        Alert.alert('Error', error.message);
      }
    } finally {
      setLoadingItem(false);
    }
  }

  // Request permissions for camera
  async function requestPermission() {
    const { status } = await ImagePicker.requestCameraPermissionsAsync();
    if (status !== 'granted') {
      Alert.alert('Permission needed', 'We need camera permission to take photos');
      return false;
    }
    return true;
  }

  // Take a photo with camera
  async function takePhoto() {
    const hasPermission = await requestPermission();
    if (!hasPermission) return;

    try {
      const result = await ImagePicker.launchCameraAsync({
        allowsEditing: true,
        aspect: [4, 3],
        quality: 0.5,
        base64: true,
      });

      if (!result.canceled && result.assets && result.assets.length > 0) {
        const asset = result.assets[0];
        if (asset.base64) {
          setPhoto(asset.base64);
          setPhotoChanged(true);
        }
      }
    } catch (error) {
      console.error('Error taking photo:', error);
      Alert.alert('Error', 'Failed to take photo');
    }
  }

  // Pick an image from library
  async function pickImage() {
    try {
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsEditing: true,
        aspect: [4, 3],
        quality: 0.5,
        base64: true,
      });

      if (!result.canceled && result.assets && result.assets.length > 0) {
        const asset = result.assets[0];
        if (asset.base64) {
          setPhoto(asset.base64);
          setPhotoChanged(true);
        }
      }
    } catch (error) {
      console.error('Error picking image:', error);
      Alert.alert('Error', 'Failed to pick image');
    }
  }

  // Upload photo to Supabase Storage
  async function uploadPhoto() {
    if (!photo) return null;

    try {
      // Generate a unique filename
      const filename = `${Date.now()}.jpg`;
      
      // Upload photo to Supabase Storage
      const { data, error } = await supabase.storage
        .from('photos')
        .upload(filename, decode(photo), {
          contentType: 'image/jpeg',
        });

      if (error) {
        throw error;
      }

      return filename;
    } catch (error) {
      console.error('Error uploading photo:', error);
      throw error;
    }
  }

  // Update item in the database
  async function updateItem() {
    if (!name.trim()) {
      Alert.alert('Error', 'Please enter a name for the item');
      return;
    }

    try {
      setLoading(true);
      
      let updates: any = {
        name,
        description,
        price: price ? parseFloat(price) : 0,
        updated_at: new Date().toISOString(),
      };

      // Only upload a new photo if it has changed
      if (photoChanged && photo) {
        const photoFilename = await uploadPhoto();
        if (photoFilename) {
          updates.photo_url = photoFilename;
        }
      }

      // Update the item in Supabase
      const { error } = await supabase
        .from('items')
        .update(updates)
        .eq('id', itemId);

      if (error) {
        throw error;
      }

      Alert.alert('Success', 'Item updated successfully!');
      
      if (onSuccess) {
        onSuccess();
      }
      
      // Navigate back
      navigation.goBack();
    } catch (error) {
      if (error instanceof Error) {
        Alert.alert('Error', error.message);
      }
    } finally {
      setLoading(false);
    }
  }

  if (loadingItem) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#0000ff" />
        <Text style={{ marginTop: 10 }}>Loading item...</Text>
      </View>
    );
  }

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      style={styles.container}
    >
      <ScrollView contentContainerStyle={styles.scrollContainer}>
        <Text style={styles.title}>Edit Item</Text>
        
        <View style={styles.formGroup}>
          <Text style={styles.label}>Name</Text>
          <TextInput
            style={styles.input}
            value={name}
            onChangeText={setName}
            placeholder="Item name"
          />
        </View>
        
        <View style={styles.formGroup}>
          <Text style={styles.label}>Description</Text>
          <TextInput
            style={[styles.input, styles.textArea]}
            value={description}
            onChangeText={setDescription}
            placeholder="Item description"
            multiline
            numberOfLines={4}
          />
        </View>
        
        <View style={styles.formGroup}>
          <Text style={styles.label}>Price ($)</Text>
          <TextInput
            style={styles.input}
            value={price}
            onChangeText={setPrice}
            placeholder="0.00"
            keyboardType="numeric"
          />
        </View>
        
        <View style={styles.formGroup}>
          <Text style={styles.label}>Photo</Text>
          {photo ? (
            <Image source={{ uri: `data:image/jpeg;base64,${photo}` }} style={styles.photo} />
          ) : photoUrl ? (
            <Image 
              source={{ uri: `https://dbhnhwkzhwjyczsbhdqa.supabase.co/storage/v1/object/public/photos/${photoUrl}` }} 
              style={styles.photo} 
            />
          ) : (
            <View style={styles.photoPlaceholder}>
              <FontAwesome name="camera" size={40} color="#ccc" />
              <Text style={styles.photoPlaceholderText}>No photo selected</Text>
            </View>
          )}
          
          <View style={styles.photoButtons}>
            <TouchableOpacity style={styles.photoButton} onPress={takePhoto}>
              <Text style={styles.photoButtonText}>Take Photo</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.photoButton} onPress={pickImage}>
              <Text style={styles.photoButtonText}>Select Photo</Text>
            </TouchableOpacity>
          </View>
        </View>
        
        <TouchableOpacity
          style={[styles.button, loading && styles.buttonDisabled]}
          onPress={updateItem}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator color="#fff" size="small" />
          ) : (
            <Text style={styles.buttonText}>Update Item</Text>
          )}
        </TouchableOpacity>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  scrollContainer: {
    padding: 20,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 20,
    textAlign: 'center',
  },
  formGroup: {
    marginBottom: 20,
  },
  label: {
    fontSize: 16,
    marginBottom: 5,
    fontWeight: '500',
  },
  input: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 5,
    padding: 10,
    fontSize: 16,
  },
  textArea: {
    height: 100,
    textAlignVertical: 'top',
  },
  photo: {
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
    marginTop: 10,
    color: '#888',
  },
  photoButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  photoButton: {
    backgroundColor: '#ddd',
    padding: 10,
    borderRadius: 5,
    flex: 0.48,
    alignItems: 'center',
  },
  photoButtonText: {
    fontWeight: '500',
  },
  button: {
    backgroundColor: '#2196F3',
    padding: 15,
    borderRadius: 5,
    alignItems: 'center',
    marginTop: 10,
  },
  buttonDisabled: {
    backgroundColor: '#A9A9A9',
  },
  buttonText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 16,
  },
}); 