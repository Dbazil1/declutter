import React, { useState, useEffect } from 'react';
import { StyleSheet, View, Alert, ScrollView, Switch, Text, ActivityIndicator } from 'react-native';
import { supabase } from '../lib/supabase';
import { Button, Input, Divider, Icon } from '@rneui/themed';
import { Session } from '@supabase/supabase-js';
import { Picker } from '@react-native-picker/picker';

interface Profile {
  id: string;
  username: string;
  first_name: string;
  last_name: string;
  website: string;
  whatsapp_phone: string;
  share_whatsapp_for_items: boolean;
  language: string;
  avatar_url?: string;
}

interface AccountProps {
  session: Session;
}

export default function Account({ session }: AccountProps) {
  const [loading, setLoading] = useState(true);
  const [profile, setProfile] = useState<Profile>({
    id: '',
    username: '',
    first_name: '',
    last_name: '',
    website: '',
    whatsapp_phone: '',
    share_whatsapp_for_items: false,
    language: 'en',
    avatar_url: '',
  });

  useEffect(() => {
    if (session) getProfile();
  }, [session]);

  async function getProfile() {
    try {
      setLoading(true);
      if (!session?.user) throw new Error('No user on the session!');

      // First check the profiles table (for backward compatibility)
      let { data, error, status } = await supabase
        .from('profiles')
        .select('*')
        .eq('id', session?.user.id)
        .single();

      if (error && status !== 406) {
        throw error;
      }

      // If profile exists in the profiles table
      if (data) {
        // Now check if we also have data in the users table
        const { data: userData, error: userError } = await supabase
          .from('users')
          .select('*')
          .eq('id', session?.user.id)
          .single();

        if (!userError && userData) {
          // Merge data from both tables, with users taking precedence
          setProfile({
            id: session?.user.id,
            username: data.username || '',
            first_name: userData.first_name || '',
            last_name: userData.last_name || '',
            website: data.website || '',
            whatsapp_phone: userData.whatsapp_phone || '',
            share_whatsapp_for_items: userData.share_whatsapp_for_items || false,
            language: userData.language || 'en',
            avatar_url: data.avatar_url || '',
          });
        } else {
          // If no data in users table, just use profiles data
          setProfile({
            id: session?.user.id,
            username: data.username || '',
            first_name: '',
            last_name: '',
            website: data.website || '',
            whatsapp_phone: '',
            share_whatsapp_for_items: false,
            language: 'en',
            avatar_url: data.avatar_url || '',
          });
        }
      } else {
        // Check if we have data in the users table only
        const { data: userData, error: userError } = await supabase
          .from('users')
          .select('*')
          .eq('id', session?.user.id)
          .single();

        if (!userError && userData) {
          setProfile({
            id: session?.user.id,
            username: '',
            first_name: userData.first_name || '',
            last_name: userData.last_name || '',
            website: '',
            whatsapp_phone: userData.whatsapp_phone || '',
            share_whatsapp_for_items: userData.share_whatsapp_for_items || false,
            language: userData.language || 'en',
            avatar_url: '',
          });
        } else {
          // No profile data in either table
          setProfile({
            id: session?.user.id,
            username: '',
            first_name: '',
            last_name: '',
            website: '',
            whatsapp_phone: '',
            share_whatsapp_for_items: false,
            language: 'en',
            avatar_url: '',
          });
        }
      }
    } catch (error) {
      if (error instanceof Error) {
        Alert.alert('Error', error.message);
      }
    } finally {
      setLoading(false);
    }
  }

  async function updateProfile() {
    try {
      setLoading(true);
      if (!session?.user) throw new Error('No user on the session!');

      // Update profiles table
      const profileUpdates = {
        id: session?.user.id,
        username: profile.username,
        website: profile.website,
        avatar_url: profile.avatar_url,
        updated_at: new Date().toISOString(),
      };

      let { error } = await supabase.from('profiles').upsert(profileUpdates);

      if (error) {
        throw error;
      }

      // Update users table
      const userUpdates = {
        id: session?.user.id,
        first_name: profile.first_name,
        last_name: profile.last_name,
        whatsapp_phone: profile.whatsapp_phone,
        share_whatsapp_for_items: profile.share_whatsapp_for_items,
        language: profile.language,
        updated_at: new Date().toISOString(),
      };

      const { error: userError } = await supabase.from('users').upsert(userUpdates);

      if (userError) {
        throw userError;
      }

      Alert.alert('Success', 'Profile updated!');
    } catch (error) {
      if (error instanceof Error) {
        Alert.alert('Error', error.message);
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerText}>Account Settings</Text>
      </View>

      {loading ? (
        <ActivityIndicator size="large" color="#0066cc" style={styles.loader} />
      ) : (
        <>
          <Text style={styles.sectionHeader}>Account Information</Text>
          <View style={styles.section}>
            <Input
              label="Email"
              value={session?.user?.email}
              disabled
              leftIcon={<Icon name="email" size={20} color="#777" />}
            />
            <Input
              label="Username"
              value={profile.username || ''}
              onChangeText={(text) => setProfile({ ...profile, username: text })}
              leftIcon={<Icon name="person" size={20} color="#777" />}
              autoCapitalize="none"
            />
          </View>

          <Text style={styles.sectionHeader}>Personal Information</Text>
          <View style={styles.section}>
            <Input
              label="First Name"
              value={profile.first_name || ''}
              onChangeText={(text) => setProfile({ ...profile, first_name: text })}
              leftIcon={<Icon name="badge" size={20} color="#777" />}
            />
            <Input
              label="Last Name"
              value={profile.last_name || ''}
              onChangeText={(text) => setProfile({ ...profile, last_name: text })}
              leftIcon={<Icon name="badge" size={20} color="#777" />}
            />
            <Input
              label="Website"
              value={profile.website || ''}
              onChangeText={(text) => setProfile({ ...profile, website: text })}
              leftIcon={<Icon name="language" size={20} color="#777" />}
              autoCapitalize="none"
            />
          </View>

          <Text style={styles.sectionHeader}>Contact Information</Text>
          <View style={styles.section}>
            <Input
              label="WhatsApp Phone"
              value={profile.whatsapp_phone || ''}
              onChangeText={(text) => setProfile({ ...profile, whatsapp_phone: text })}
              leftIcon={<Icon name="phone" size={20} color="#777" />}
              keyboardType="phone-pad"
            />

            <View style={styles.switchContainer}>
              <Text style={styles.switchLabel}>Share WhatsApp for Items</Text>
              <Switch
                value={profile.share_whatsapp_for_items}
                onValueChange={(value) => setProfile({ ...profile, share_whatsapp_for_items: value })}
                trackColor={{ false: '#767577', true: '#4CAF50' }}
              />
            </View>
          </View>

          <Text style={styles.sectionHeader}>Preferences</Text>
          <View style={styles.section}>
            <Text style={styles.pickerLabel}>Language</Text>
            <View style={styles.pickerContainer}>
              <Picker
                selectedValue={profile.language}
                onValueChange={(value: string) => setProfile({ ...profile, language: value })}
                style={styles.picker}
              >
                <Picker.Item label="English" value="en" />
                <Picker.Item label="Español" value="es" />
              </Picker>
            </View>
          </View>

          <View style={styles.buttonSection}>
            <Button
              title={loading ? 'Updating...' : 'Update Profile'}
              onPress={updateProfile}
              disabled={loading}
              buttonStyle={styles.updateButton}
              icon={<Icon name="save" color="white" size={16} style={{ marginRight: 8 }} />}
            />
            <Divider style={{ marginVertical: 15 }} />
            <Button
              title="Sign Out"
              onPress={() => supabase.auth.signOut()}
              buttonStyle={styles.signOutButton}
              icon={<Icon name="logout" color="white" size={16} style={{ marginRight: 8 }} />}
            />
          </View>
        </>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  header: {
    padding: 15,
    backgroundColor: '#f8f8f8',
    alignItems: 'center',
    marginBottom: 10,
  },
  headerText: {
    fontSize: 20,
    fontWeight: 'bold',
  },
  loader: {
    marginTop: 20,
  },
  sectionHeader: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#555',
    marginHorizontal: 15,
    marginTop: 20,
    marginBottom: 5,
  },
  section: {
    backgroundColor: '#fff',
    paddingHorizontal: 5,
    paddingVertical: 10,
    marginBottom: 10,
  },
  switchContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 10,
    marginVertical: 15,
  },
  switchLabel: {
    fontSize: 16,
    color: '#86939e',
  },
  pickerLabel: {
    fontSize: 16,
    color: '#86939e',
    marginHorizontal: 10,
    marginBottom: 5,
  },
  pickerContainer: {
    borderWidth: 1,
    borderColor: '#e3e3e3',
    borderRadius: 5,
    marginHorizontal: 10,
  },
  picker: {
    height: 50,
  },
  buttonSection: {
    padding: 15,
    marginBottom: 30,
  },
  updateButton: {
    backgroundColor: '#2089dc',
    borderRadius: 5,
    padding: 12,
  },
  signOutButton: {
    backgroundColor: '#d9534f',
    borderRadius: 5,
    padding: 12,
  },
}); 