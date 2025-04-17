import React, { useState } from 'react';
import { StyleSheet, View, Text, TextInput, ScrollView, Image, TouchableOpacity, Alert, ActivityIndicator } from 'react-native';
import { Button } from '@rneui/themed';
import * as ImagePicker from 'expo-image-picker';
import { supabase } from '../lib/supabase';
import { withNetworkRetry } from '../lib/networkMonitor';
import { generateUUID } from '../lib/uuid';
import { Platform } from 'react-native';

export default function AddItem({ onSuccess }: { onSuccess?: () => void }) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [price, setPrice] = useState('');
  const [photo, setPhoto] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [loading, setLoading] = useState(false);

  // Request camera permissions
  const requestPermission = async () => {
    const { status } = await ImagePicker.requestCameraPermissionsAsync();
    if (status !== 'granted') {
      Alert.alert('Permission needed', 'Sorry, we need camera permissions to make this work!');
      return false;
    }
    return true;
  };

  // Request photo library permissions
  const requestLibraryPermission = async () => {
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (status !== 'granted') {
      Alert.alert('Permission needed', 'Sorry, we need photo library permissions to make this work!');
      return false;
    }
    return true;
  };

  // Take a photo with camera
  const takePhoto = async () => {
    const hasPermission = await requestPermission();
    if (!hasPermission) return;

    try {
      const result = await ImagePicker.launchCameraAsync({
        allowsEditing: true,
        aspect: [4, 3],
        quality: 0.8,
      });

      if (!result.canceled && result.assets && result.assets.length > 0) {
        setPhoto(result.assets[0].uri);
      }
    } catch (error) {
      console.error('Error taking photo:', error);
      Alert.alert('Error', 'Failed to take photo');
    }
  };

  // Pick an image from library
  const pickImage = async () => {
    const hasPermission = await requestLibraryPermission();
    if (!hasPermission) return;

    try {
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsEditing: true,
        aspect: [4, 3],
        quality: 0.8,
      });

      if (!result.canceled && result.assets && result.assets.length > 0) {
        setPhoto(result.assets[0].uri);
      }
    } catch (error) {
      console.error('Error picking image:', error);
      Alert.alert('Error', 'Failed to select image');
    }
  };

  // Upload photo to Supabase storage
  const uploadPhoto = async () => {
    if (!photo) return null;
    
    try {
      setUploading(true);
      
      // Convert image to blob
      const response = await fetch(photo);
      const blob = await response.blob();
      
      // Generate unique file path
      const fileExt = photo.split('.').pop();
      const fileName = `${generateUUID()}.${fileExt}`;
      const filePath = `items/${fileName}`;
      
      // Upload to Supabase storage
      const { data, error } = await supabase.storage
        .from('photos')
        .upload(filePath, blob);
        
      if (error) throw error;
      
      // Return the file path
      return filePath;
    } catch (error) {
      console.error('Error uploading image:', error);
      Alert.alert('Error', 'Failed to upload image');
      return null;
    } finally {
      setUploading(false);
    }
  };

  // Submit the form
  const submitItem = async () => {
    if (!name.trim()) {
      Alert.alert('Error', 'Please enter a name for the item');
      return;
    }

    setLoading(true);
    
    try {
      // Upload photo first if available
      let photoPath = null;
      if (photo) {
        photoPath = await uploadPhoto();
      }
      
      // Get current user
      const { data: { user } } = await supabase.auth.getUser();
      
      if (!user) {
        Alert.alert('Error', 'You must be logged in to add items');
        return;
      }
      
      // Create new item in database
      const { data, error } = await supabase
        .from('items')
        .insert({
          name: name.trim(),
          description: description.trim(),
          price: price ? parseFloat(price) : 0,
          photo_url: photoPath,
          status: 'available',
          user_id: user.id,
          created_at: new Date().toISOString(),
        });
        
      if (error) throw error;
      
      // Reset form
      setName('');
      setDescription('');
      setPrice('');
      setPhoto(null);
      
      Alert.alert('Success', 'Item added successfully!');
      
      // Call success callback if provided
      if (onSuccess) onSuccess();
      
    } catch (error) {
      console.error('Error adding item:', error);
      Alert.alert('Error', 'Failed to add item');
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>Add New Item</Text>
      
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
        <Text style={styles.label}>Price</Text>
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
        <View style={styles.photoButtons}>
          <Button
            title="Take Photo"
            onPress={takePhoto}
            buttonStyle={styles.photoButton}
          />
          <Button
            title="Choose from Library"
            onPress={pickImage}
            buttonStyle={styles.photoButton}
          />
        </View>
        
        {photo && (
          <View style={styles.photoPreview}>
            <Image source={{ uri: photo }} style={styles.previewImage} />
            <TouchableOpacity 
              style={styles.removeButton}
              onPress={() => setPhoto(null)}
            >
              <Text style={styles.removeButtonText}>✕</Text>
            </TouchableOpacity>
          </View>
        )}
      </View>
      
      <Button
        title={loading ? 'Adding...' : 'Add Item'}
        onPress={submitItem}
        buttonStyle={styles.submitButton}
        disabled={loading || uploading}
      />
      
      {(loading || uploading) && (
        <ActivityIndicator size="large" color="#0000ff" style={styles.loader} />
      )}
    </ScrollView>
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
    marginBottom: 24,
    textAlign: 'center',
  },
  formGroup: {
    marginBottom: 20,
  },
  label: {
    fontSize: 16,
    marginBottom: 8,
    fontWeight: '500',
  },
  input: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
  },
  textArea: {
    minHeight: 100,
    textAlignVertical: 'top',
  },
  photoButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  photoButton: {
    flex: 0.48,
  },
  photoPreview: {
    position: 'relative',
    marginBottom: 16,
  },
  previewImage: {
    width: '100%',
    height: 200,
    borderRadius: 8,
    resizeMode: 'cover',
  },
  removeButton: {
    position: 'absolute',
    top: 10,
    right: 10,
    backgroundColor: 'rgba(0,0,0,0.5)',
    width: 30,
    height: 30,
    borderRadius: 15,
    justifyContent: 'center',
    alignItems: 'center',
  },
  removeButtonText: {
    color: 'white',
    fontSize: 16,
    fontWeight: 'bold',
  },
  submitButton: {
    backgroundColor: '#4CAF50',
    paddingVertical: 12,
    marginVertical: 16,
  },
  loader: {
    marginTop: 20,
  },
}); 