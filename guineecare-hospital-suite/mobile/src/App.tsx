/**
 * App GuinéeCare Mobile — point d'entrée Expo.
 *
 * Wrap AuthProvider + AppNavigator + hooks globaux (push notifications).
 *
 * Le splash screen natif (configuré dans app.json) reste affiché pendant le
 * chargement initial (récupération de la session persistée).
 *
 * v2.7.0 — Phase 7 : ErrorBoundary pour éviter le crash total sur erreur de rendu.
 */
import React from 'react';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { GestureHandlerRootView } from 'react-native-gesture-handler';

import { AuthProvider, useAuth } from './context/AuthContext';
import { AppNavigator } from './navigation/AppNavigator';
import { usePushNotifications } from './hooks/usePushNotifications';
import { ErrorBoundary } from './components/ErrorBoundary';

function AppInner() {
  usePushNotifications();
  return (
    <ErrorBoundary>
      <AppNavigator />
    </ErrorBoundary>
  );
}

export default function App() {
  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <SafeAreaProvider>
        <AuthProvider>
          <AppInner />
        </AuthProvider>
        <StatusBar style="light" backgroundColor="#0f766e" />
      </SafeAreaProvider>
    </GestureHandlerRootView>
  );
}
