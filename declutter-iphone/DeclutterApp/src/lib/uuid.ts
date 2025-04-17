// Import 'react-native-get-random-values' BEFORE importing 'uuid'
// This is required for React Native compatibility
import 'react-native-get-random-values';
import { v4 as uuidv4 } from 'uuid';

export const generateUUID = (): string => {
  return uuidv4();
}; 