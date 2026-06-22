/**
 * Écran BiometricLock — verrou biométrique au démarrage de l'app.
 *
 * Si l'utilisateur a activé le déverrouillage biométrique dans ProfileScreen,
 * l'app se verrouille au démarrage et demande l'auth biométrique pour accéder.
 *
 * Bouton de secours : "Se déconnecter" en cas de problème.
 */
import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAuth } from '../context/AuthContext';
import { Ionicons } from '../components/Icons';

export function BiometricLockScreen() {
  const { unlockWithBiometric, logout, user } = useAuth();

  async function handleUnlock() {
    const ok = await unlockWithBiometric();
    if (!ok) {
      Alert.alert(
        'Échec du déverrouillage',
        "L'authentification biométrique a échoué. Réessayez ou déconnectez-vous."
      );
    }
  }

  return (
    <SafeAreaView style={styles.container} edges={['top', 'bottom']}>
      <View style={styles.content}>
        <View style={styles.iconCircle}>
          <Ionicons name="lock-closed" size={48} color="#0f766e" />
        </View>
        <Text style={styles.title}>Application verrouillée</Text>
        <Text style={styles.subtitle}>
          Bonjour {user?.first_name}, authentifiez-vous pour accéder à GuinéeCare.
        </Text>

        <TouchableOpacity style={styles.button} onPress={handleUnlock}>
          <Ionicons name="finger-print" size={24} color="white" style={{ marginRight: 8 }} />
          <Text style={styles.buttonText}>Déverrouiller</Text>
        </TouchableOpacity>

        <TouchableOpacity onPress={logout} style={styles.logoutLink}>
          <Text style={styles.logoutText}>Se déconnecter</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f8fafc' },
  content: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 32,
  },
  iconCircle: {
    width: 96,
    height: 96,
    borderRadius: 48,
    backgroundColor: '#ccfbf1',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 24,
  },
  title: { fontSize: 22, fontWeight: '800', color: '#0f172a', marginBottom: 8 },
  subtitle: {
    fontSize: 14,
    color: '#64748b',
    textAlign: 'center',
    marginBottom: 32,
  },
  button: {
    flexDirection: 'row',
    backgroundColor: '#0f766e',
    paddingVertical: 14,
    paddingHorizontal: 32,
    borderRadius: 8,
    alignItems: 'center',
  },
  buttonText: { color: 'white', fontSize: 16, fontWeight: '700' },
  logoutLink: { marginTop: 24, padding: 8 },
  logoutText: { color: '#dc2626', fontSize: 14 },
});
