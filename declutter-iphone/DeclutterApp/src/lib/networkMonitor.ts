import { useEffect, useState } from 'react';
import { Platform } from 'react-native';
import NetInfo, { NetInfoState } from '@react-native-community/netinfo';

/**
 * Hook to monitor network connectivity status
 * @returns The current connectivity status and a function to manually check connectivity
 */
export const useNetworkStatus = () => {
  const [isConnected, setIsConnected] = useState<boolean | null>(null);

  const checkConnection = async () => {
    try {
      // This function is different based on React Native version
      // For newer versions of React Native:
      if (Platform.OS === 'ios' || Platform.OS === 'android') {
        const state = await NetInfo.fetch();
        setIsConnected(state.isConnected);
        return state.isConnected;
      }
      return true; // Default for web
    } catch (error) {
      console.error('Failed to check network connection:', error);
      return false;
    }
  };

  useEffect(() => {
    // Initial check
    checkConnection();

    // Subscribe to connection changes
    let unsubscribe: (() => void) | null = null;
    
    try {
      unsubscribe = NetInfo.addEventListener((state: NetInfoState) => {
        setIsConnected(state.isConnected);
      });
    } catch (error) {
      console.error('Failed to subscribe to network changes:', error);
    }

    // Cleanup
    return () => {
      if (unsubscribe) {
        unsubscribe();
      }
    };
  }, []);

  return { isConnected, checkConnection };
};

/**
 * Utility to handle network errors with retries
 * @param fn The async function to call
 * @param retries Number of retries
 * @param delayMs Delay between retries in milliseconds
 * @returns Result of the function or throws error after retries
 */
export const withNetworkRetry = async <T>(
  fn: () => Promise<T>,
  retries = 3,
  delayMs = 1000
): Promise<T> => {
  try {
    return await fn();
  } catch (error: any) {
    if (
      retries > 0 &&
      (error.message?.includes('Network request failed') ||
        error.message?.includes('network') ||
        error.code === 'NETWORK_ERROR' ||
        error.code === 'ECONNABORTED')
    ) {
      console.log(`Network error, retrying... (${retries} attempts left)`);
      await new Promise(resolve => setTimeout(resolve, delayMs));
      return withNetworkRetry(fn, retries - 1, delayMs);
    }

    throw error;
  }
}; 