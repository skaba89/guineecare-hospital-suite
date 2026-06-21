/**
 * Écran Login — authentification email/password.
 *
 * - Logo GuinéeCare + titre
 * - Champs email/password (validation basique)
 * - Bouton "Se connecter" (appel API)
 * - Affichage des erreurs serveur
 * - Lien "Mode démo" qui pré-remplit les identifiants admin
 * - Note: la biométrie est gérée séparément (BiometricLockScreen) au démarrage
 *   si l'utilisateur a déjà une session et a activé le déverrouillage biométrique.
 */
import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAuth } from '../context/AuthContext';

export function LoginScreen() {
  const { login, loading, error } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  async function handleLogin() {
    if (!email.trim() || !password) {
      Alert.alert('Erreur', 'Veuillez saisir votre email et mot de passe.');
      return;
    }
    try {
      await login(email.trim().toLowerCase(), password);
    } catch (e) {
      // Erreur déjà gérée dans le contexte (state.error)
    }
  }

  function fillDemo() {
    setEmail('admin@guineecare.com');
    setPassword('admin123');
  }

  return (
    <SafeAreaView style={styles.container} edges={['top', 'bottom']}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        style={{ flex: 1 }}
      >
        <ScrollView contentContainerStyle={styles.scroll}>
          <View style={styles.logoBlock}>
            <View style={styles.logoCircle}>
              <Text style={styles.logoText}>GC</Text>
            </View>
            <Text style={styles.title}>GuinéeCare</Text>
            <Text style={styles.subtitle}>Suite Hospitalière Mobile</Text>
          </View>

          <View style={styles.form}>
            <Text style={styles.label}>Email</Text>
            <TextInput
              style={styles.input}
              value={email}
              onChangeText={setEmail}
              placeholder="dr.diallo@chu-donka.gn"
              placeholderTextColor="#94a3b8"
              autoCapitalize="none"
              autoCorrect={false}
              keyboardType="email-address"
              textContentType="emailAddress"
            />

            <Text style={styles.label}>Mot de passe</Text>
            <TextInput
              style={styles.input}
              value={password}
              onChangeText={setPassword}
              placeholder="••••••••"
              placeholderTextColor="#94a3b8"
              secureTextEntry
              textContentType="password"
              onSubmitEditing={handleLogin}
            />

            {error && (
              <View style={styles.errorBox}>
                <Text style={styles.errorText}>{error}</Text>
              </View>
            )}

            <TouchableOpacity
              style={[styles.button, loading && styles.buttonDisabled]}
              onPress={handleLogin}
              disabled={loading}
            >
              <Text style={styles.buttonText}>
                {loading ? 'Connexion…' : 'Se connecter'}
              </Text>
            </TouchableOpacity>

            <TouchableOpacity onPress={fillDemo} style={styles.demoLink}>
              <Text style={styles.demoLinkText}>
                Utiliser les identifiants démo (admin)
              </Text>
            </TouchableOpacity>
          </View>

          <View style={styles.footer}>
            <Text style={styles.footerText}>v1.7.0 · CHU Donka · Ministère de la Santé</Text>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f8fafc' },
  scroll: {
    flexGrow: 1,
    padding: 24,
    justifyContent: 'center',
  },
  logoBlock: { alignItems: 'center', marginBottom: 32 },
  logoCircle: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#0f766e',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },
  logoText: { color: 'white', fontSize: 32, fontWeight: '800' },
  title: { fontSize: 28, fontWeight: '800', color: '#0f172a' },
  subtitle: { fontSize: 14, color: '#64748b', marginTop: 4 },
  form: { gap: 8 },
  label: {
    fontSize: 13,
    color: '#475569',
    fontWeight: '600',
    marginTop: 8,
    marginBottom: 4,
  },
  input: {
    backgroundColor: 'white',
    borderWidth: 1,
    borderColor: '#e2e8f0',
    borderRadius: 8,
    padding: 14,
    fontSize: 16,
    color: '#0f172a',
  },
  errorBox: {
    backgroundColor: '#fef2f2',
    borderWidth: 1,
    borderColor: '#fecaca',
    borderRadius: 8,
    padding: 12,
    marginTop: 8,
  },
  errorText: { color: '#dc2626', fontSize: 13 },
  button: {
    backgroundColor: '#0f766e',
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 16,
  },
  buttonDisabled: { opacity: 0.6 },
  buttonText: { color: 'white', fontSize: 16, fontWeight: '700' },
  demoLink: { alignItems: 'center', marginTop: 16, padding: 8 },
  demoLinkText: { color: '#0f766e', fontSize: 13 },
  footer: { marginTop: 32, alignItems: 'center' },
  footerText: { color: '#94a3b8', fontSize: 11 },
});
