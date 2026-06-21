/**
 * Écran Profile — informations utilisateur + paramètres.
 *
 * - Carte profil (nom, email, rôle, établissement)
 * - Section Sécurité : toggle biométrie
 * - Section Déploiement : URL backend (debug)
 * - Bouton Déconnexion
 */
import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Alert,
  Switch,
  ScrollView,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAuth } from '../context/AuthContext';
import { API_BASE_URL } from '../services/api';
import { Ionicons } from '../components/Icons';

export function ProfileScreen() {
  const {
    user,
    logout,
    isBiometricEnabled,
    hasBiometricHardware,
    enableBiometric,
    disableBiometric,
  } = useAuth();

  const roleLabels: Record<string, string> = {
    SUPER_ADMIN: 'Super Administrateur',
    ADMIN: 'Administrateur',
    DOCTOR: 'Médecin',
    NURSE: 'Infirmier',
    MIDWIFE: 'Sage-femme',
    PHARMACIST: 'Pharmacien',
    LAB_TECH: 'Laborantin',
    CASHIER: 'Caissier',
  };

  async function handleBiometricToggle(value: boolean) {
    if (value) {
      await enableBiometric();
    } else {
      await disableBiometric();
    }
  }

  function handleLogout() {
    Alert.alert(
      'Déconnexion',
      'Voulez-vous vraiment vous déconnecter ?',
      [
        { text: 'Annuler', style: 'cancel' },
        { text: 'Déconnexion', style: 'destructive', onPress: () => logout() },
      ]
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <ScrollView contentContainerStyle={{ padding: 16, paddingBottom: 40 }}>
        <Text style={styles.title}>Profil</Text>

        {/* Carte profil */}
        <View style={styles.profileCard}>
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>
              {(user?.first_name?.[0] || '') + (user?.last_name?.[0] || '')}
            </Text>
          </View>
          <View style={{ flex: 1 }}>
            <Text style={styles.userName}>
              {user?.first_name} {user?.last_name}
            </Text>
            <Text style={styles.userEmail}>{user?.email}</Text>
            <View style={styles.roleBadge}>
              <Text style={styles.roleText}>
                {roleLabels[user?.role || ''] || user?.role}
              </Text>
            </View>
          </View>
        </View>

        {/* Section Sécurité */}
        <Text style={styles.sectionTitle}>Sécurité</Text>
        <View style={styles.card}>
          <View style={styles.row}>
            <View style={styles.rowLeft}>
              <Ionicons
                name="finger-print"
                size={22}
                color="#0f766e"
                style={{ marginRight: 12 }}
              />
              <View>
                <Text style={styles.rowLabel}>Déverrouillage biométrique</Text>
                <Text style={styles.rowSub}>
                  {hasBiometricHardware
                    ? 'Empreinte / Face ID au démarrage'
                    : 'Non disponible sur cet appareil'}
                </Text>
              </View>
            </View>
            <Switch
              value={isBiometricEnabled}
              onValueChange={handleBiometricToggle}
              disabled={!hasBiometricHardware}
              trackColor={{ false: '#e2e8f0', true: '#0f766e' }}
            />
          </View>
        </View>

        {/* Section Paramètres */}
        <Text style={styles.sectionTitle}>Paramètres</Text>
        <View style={styles.card}>
          <View style={styles.row}>
            <View style={styles.rowLeft}>
              <Ionicons name="server-outline" size={22} color="#64748b" style={{ marginRight: 12 }} />
              <View>
                <Text style={styles.rowLabel}>Serveur backend</Text>
                <Text style={styles.rowSub}>{API_BASE_URL}</Text>
              </View>
            </View>
          </View>
          <View style={[styles.row, { borderTopWidth: 1, borderTopColor: '#e2e8f0' }]}>
            <View style={styles.rowLeft}>
              <Ionicons name="information-circle-outline" size={22} color="#64748b" style={{ marginRight: 12 }} />
              <View>
                <Text style={styles.rowLabel}>Version</Text>
                <Text style={styles.rowSub}>GuinéeCare Mobile v1.7.0</Text>
              </View>
            </View>
          </View>
        </View>

        {/* Bouton déconnexion */}
        <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
          <Ionicons name="log-out-outline" size={20} color="white" style={{ marginRight: 8 }} />
          <Text style={styles.logoutText}>Se déconnecter</Text>
        </TouchableOpacity>

        <Text style={styles.footer}>CHU Donka · Ministère de la Santé · République de Guinée</Text>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f8fafc' },
  title: { fontSize: 24, fontWeight: '800', color: '#0f172a', marginBottom: 16 },
  profileCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 16,
    marginBottom: 24,
  },
  avatar: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: '#0f766e',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 16,
  },
  avatarText: { color: 'white', fontSize: 20, fontWeight: '800' },
  userName: { fontSize: 18, fontWeight: '800', color: '#0f172a' },
  userEmail: { fontSize: 13, color: '#64748b', marginTop: 2 },
  roleBadge: {
    backgroundColor: '#ccfbf1',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
    alignSelf: 'flex-start',
    marginTop: 6,
  },
  roleText: { color: '#0f766e', fontSize: 11, fontWeight: '700' },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#475569',
    textTransform: 'uppercase',
    marginBottom: 8,
  },
  card: {
    backgroundColor: 'white',
    borderRadius: 12,
    marginBottom: 24,
    overflow: 'hidden',
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 14,
  },
  rowLeft: { flexDirection: 'row', alignItems: 'center', flex: 1 },
  rowLabel: { fontSize: 14, fontWeight: '600', color: '#0f172a' },
  rowSub: { fontSize: 12, color: '#94a3b8', marginTop: 2 },
  logoutButton: {
    flexDirection: 'row',
    backgroundColor: '#dc2626',
    padding: 14,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 16,
  },
  logoutText: { color: 'white', fontWeight: '700', fontSize: 16 },
  footer: {
    color: '#94a3b8',
    fontSize: 11,
    textAlign: 'center',
    marginTop: 32,
  },
});
