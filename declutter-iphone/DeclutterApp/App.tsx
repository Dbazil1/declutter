import React, { useState, useEffect } from 'react';
import { StyleSheet, SafeAreaView, Text, View, LogBox } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { Session } from '@supabase/supabase-js';
import { supabase } from './src/lib/supabase';
import Auth from './src/components/Auth';
import Account from './src/components/Account';
import AddItem from './src/components/AddItem';
import EditItem from './src/components/EditItem';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createStackNavigator } from '@react-navigation/stack';
import { useNetworkStatus } from './src/lib/networkMonitor';
import { MaterialIcons } from '@expo/vector-icons';

// Import screens
import AvailableItemsScreen from './src/screens/AvailableItemsScreen';
import ClaimedItemsScreen from './src/screens/ClaimedItemsScreen';
import ShareScreen from './src/screens/ShareScreen';

// Ignore network request failed errors in development
LogBox.ignoreLogs(['Network request failed']);

// Define navigation parameters
export type RootStackParamList = {
  EditItem: { itemId: number };
  AvailableItems: undefined;
  ClaimedItems: undefined;
  Share: undefined;
};

// Create navigators
const Tab = createBottomTabNavigator();
const Stack = createStackNavigator<RootStackParamList>();

// Screen components for tabs
const ProfileScreen = ({ session }: { session: Session }) => <Account session={session} />;
const AddItemScreen = () => <AddItem onSuccess={() => console.log('Item added successfully')} />;

// Edit Item Screen
const EditItemScreen = ({ route }: any) => {
  const { itemId } = route.params;
  return <EditItem itemId={itemId} onSuccess={() => console.log('Item updated successfully')} />;
};

// Create stack navigators for items with edit capability
const AvailableItemsStack = () => (
  <Stack.Navigator>
    <Stack.Screen name="AvailableItems" component={AvailableItemsScreen} options={{ title: 'Available Items' }} />
    <Stack.Screen name="EditItem" component={EditItemScreen} options={{ title: 'Edit Item' }} />
  </Stack.Navigator>
);

const ClaimedItemsStack = () => (
  <Stack.Navigator>
    <Stack.Screen name="ClaimedItems" component={ClaimedItemsScreen} options={{ title: 'My Items' }} />
    <Stack.Screen name="EditItem" component={EditItemScreen} options={{ title: 'Edit Item' }} />
  </Stack.Navigator>
);

const ShareStack = () => (
  <Stack.Navigator>
    <Stack.Screen name="Share" component={ShareScreen} options={{ title: 'Share' }} />
  </Stack.Navigator>
);

// Offline notice component
const OfflineNotice = () => (
  <View style={styles.offlineContainer}>
    <Text style={styles.offlineText}>No Internet Connection</Text>
  </View>
);

export default function App() {
  const [session, setSession] = useState<Session | null>(null);
  const { isConnected } = useNetworkStatus();
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const getInitialSession = async () => {
      try {
        setIsLoading(true);
        const { data, error } = await supabase.auth.getSession();
        
        if (error) {
          console.error('Error getting session:', error.message);
        } else {
          setSession(data.session);
        }
      } catch (error) {
        console.error('Failed to get session:', error);
      } finally {
        setIsLoading(false);
      }
    };

    getInitialSession();

    // Set up auth state change listener
    const { data: authListener } = supabase.auth.onAuthStateChange(
      async (event, newSession) => {
        console.log('Auth state changed:', event);
        setSession(newSession);
      }
    );

    // Cleanup
    return () => {
      if (authListener && authListener.subscription) {
        authListener.subscription.unsubscribe();
      }
    };
  }, []);

  if (isLoading) {
    return (
      <SafeAreaView style={styles.loadingContainer}>
        <Text>Loading...</Text>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar style="auto" />
      {isConnected === false && <OfflineNotice />}
      {!session ? (
        <Auth />
      ) : (
        <NavigationContainer>
          <Tab.Navigator
            screenOptions={({ route }) => ({
              tabBarIcon: ({ color, size }) => {
                let iconName: any = 'help';

                if (route.name === 'Available') {
                  iconName = 'list';
                } else if (route.name === 'Claimed') {
                  iconName = 'shopping-cart';
                } else if (route.name === 'Add Item') {
                  iconName = 'add-circle';
                } else if (route.name === 'Share') {
                  iconName = 'share';
                } else if (route.name === 'Profile') {
                  iconName = 'account-circle';
                }

                return <MaterialIcons name={iconName} size={size} color={color} />;
              },
              tabBarActiveTintColor: 'tomato',
              tabBarInactiveTintColor: 'gray',
              tabBarStyle: { height: 60 },
              tabBarLabelStyle: { fontSize: 12, marginBottom: 5 },
              headerShown: false,
            })}
          >
            <Tab.Screen 
              name="Available" 
              component={AvailableItemsStack}
              options={{
                tabBarLabel: 'Available',
              }}
            />
            <Tab.Screen 
              name="Claimed" 
              component={ClaimedItemsStack}
              options={{
                tabBarLabel: 'Claimed',
              }}
            />
            <Tab.Screen 
              name="Add Item" 
              component={AddItemScreen}
              options={{
                tabBarLabel: 'Add Item',
                headerShown: true,
              }}
            />
            <Tab.Screen 
              name="Share" 
              component={ShareStack}
              options={{
                tabBarLabel: 'Share',
              }}
            />
            <Tab.Screen 
              name="Profile"
              options={{
                tabBarLabel: 'Profile',
                headerShown: true,
              }}
            >
              {() => <ProfileScreen session={session} />}
            </Tab.Screen>
          </Tab.Navigator>
        </NavigationContainer>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  loadingContainer: {
    flex: 1,
    backgroundColor: '#fff',
    justifyContent: 'center',
    alignItems: 'center',
  },
  offlineContainer: {
    backgroundColor: '#b52424',
    height: 30,
    justifyContent: 'center',
    alignItems: 'center',
    flexDirection: 'row',
    width: '100%',
    position: 'absolute',
    top: 30,
    zIndex: 1000,
  },
  offlineText: {
    color: '#fff',
    fontWeight: 'bold',
  },
});
