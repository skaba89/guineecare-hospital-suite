/**
 * Navigation GuinéeCare Mobile — Stack principal + Bottom Tabs.
 *
 * Structure :
 *   RootStack
 *   ├── (Auth) — Login
 *   ├── (Locked) — BiometricLock
 *   └── (App) — BottomTabs
 *       ├── Dashboard
 *       ├── Patients (Stack : Liste → Détail)
 *       ├── QRScan
 *       ├── Notifications
 *       └── Profile
 */
import React from 'react';
import { NavigationContainer, DefaultTheme, DarkTheme } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { useColorScheme } from 'react-native';
import { Ionicons } from './components/Icons';

import { useAuth } from './context/AuthContext';
import { LoginScreen } from './screens/LoginScreen';
import { BiometricLockScreen } from './screens/BiometricLockScreen';
import { DashboardScreen } from './screens/DashboardScreen';
import { PatientsListScreen } from './screens/PatientsListScreen';
import { PatientDetailScreen } from './screens/PatientDetailScreen';
import { QRScanScreen } from './screens/QRScanScreen';
import { NotificationsScreen } from './screens/NotificationsScreen';
import { ProfileScreen } from './screens/ProfileScreen';

const Stack = createNativeStackNavigator();
const Tab = createBottomTabNavigator();

const GuineecareTheme = {
  ...DefaultTheme,
  colors: {
    ...DefaultTheme.colors,
    primary: '#0f766e',
    background: '#f8fafc',
    card: '#ffffff',
    text: '#0f172a',
    border: '#e2e8f0',
    notification: '#dc2626',
  },
};

function MainTabs() {
  return (
    <Tab.Navigator
      screenOptions={{
        tabBarActiveTintColor: '#0f766e',
        tabBarInactiveTintColor: '#94a3b8',
        headerStyle: { backgroundColor: '#0f766e' },
        headerTintColor: '#ffffff',
        headerTitleStyle: { fontWeight: '700' },
      }}
    >
      <Tab.Screen
        name="Dashboard"
        component={DashboardScreen}
        options={{
          title: 'Accueil',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="home-outline" size={size} color={color} />
          ),
        }}
      />
      <Tab.Screen
        name="Patients"
        component={PatientsListScreen}
        options={{
          title: 'Patients',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="people-outline" size={size} color={color} />
          ),
        }}
      />
      <Tab.Screen
        name="QRScan"
        component={QRScanScreen}
        options={{
          title: 'Scanner',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="qr-code-outline" size={size} color={color} />
          ),
        }}
      />
      <Tab.Screen
        name="Notifications"
        component={NotificationsScreen}
        options={{
          title: 'Alertes',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="notifications-outline" size={size} color={color} />
          ),
        }}
      />
      <Tab.Screen
        name="Profile"
        component={ProfileScreen}
        options={{
          title: 'Profil',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="person-outline" size={size} color={color} />
          ),
        }}
      />
    </Tab.Navigator>
  );
}

function AppStack() {
  return (
    <Stack.Navigator>
      <Stack.Screen
        name="MainTabs"
        component={MainTabs}
        options={{ headerShown: false }}
      />
      <Stack.Screen
        name="PatientDetail"
        component={PatientDetailScreen}
        options={{
          title: 'Dossier patient',
          headerStyle: { backgroundColor: '#0f766e' },
          headerTintColor: '#ffffff',
        }}
      />
    </Stack.Navigator>
  );
}

export function AppNavigator() {
  const { user, isLocked, loading } = useAuth();

  if (loading) {
    // Splash géré nativement par app.json
    return null;
  }

  return (
    <NavigationContainer theme={GuineecareTheme}>
      <Stack.Navigator screenOptions={{ headerShown: false }}>
        {!user ? (
          <Stack.Screen name="Login" component={LoginScreen} />
        ) : isLocked ? (
          <Stack.Screen name="BiometricLock" component={BiometricLockScreen} />
        ) : (
          <Stack.Screen name="App" component={AppStack} />
        )}
      </Stack.Navigator>
    </NavigationContainer>
  );
}
