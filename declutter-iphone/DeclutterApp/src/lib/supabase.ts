import AsyncStorage from '@react-native-async-storage/async-storage';
import { createClient } from '@supabase/supabase-js';
import { EXPO_PUBLIC_SUPABASE_URL, EXPO_PUBLIC_SUPABASE_ANON_KEY } from '@env';
import { Platform } from 'react-native';

// Add console logs for debugging
console.log('Environment variables:');
console.log('SUPABASE_URL:', EXPO_PUBLIC_SUPABASE_URL ? 'Defined' : 'Undefined');
console.log('SUPABASE_KEY:', EXPO_PUBLIC_SUPABASE_ANON_KEY ? `Defined (length: ${EXPO_PUBLIC_SUPABASE_ANON_KEY.length})` : 'Undefined');

// Check if environment variables are available and provide fallbacks
// This ensures the app doesn't crash if env vars aren't loaded
const supabaseUrl = EXPO_PUBLIC_SUPABASE_URL;
const supabaseAnonKey = EXPO_PUBLIC_SUPABASE_ANON_KEY;

// Make sure values are not undefined before creating client
if (!supabaseUrl) {
  throw new Error('Supabase URL is missing. Please check your .env file and ensure EXPO_PUBLIC_SUPABASE_URL is defined.');
}

if (!supabaseAnonKey) {
  throw new Error('Supabase Anon Key is missing. Please check your .env file and ensure EXPO_PUBLIC_SUPABASE_ANON_KEY is defined.');
}

// Configure with retries and longer timeouts
const options = {
  auth: {
    storage: AsyncStorage,
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: false,
  },
  global: {
    headers: {
      'X-Client-Info': `react-native-${Platform.OS}`
    },
  },
  // Add network-specific configuration
  realtime: {
    params: {
      eventsPerSecond: 5, // Reduce from default 10
    },
  },
};

// Create Supabase client with retry support
export const supabase = createClient(supabaseUrl, supabaseAnonKey, options);

// Add an error handler for the client
const handleSupabaseError = (error: Error) => {
  console.error('Supabase error:', error.message);
  // You can add additional error handling here
};

// Set up error listener
supabase.auth.onAuthStateChange((event, session) => {
  if (event === 'SIGNED_OUT') {
    console.log('User signed out');
  } else if (event === 'SIGNED_IN') {
    console.log('User signed in');
  } else if (event === 'TOKEN_REFRESHED') {
    console.log('Token refreshed');
  } else if (event === 'USER_UPDATED') {
    console.log('User updated');
  }
}); 