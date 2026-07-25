/**
 * ConnectivityBanner — indicateur global "en ligne / hors ligne".
 *
 * v2.7.0 — Phase 7 : affiche une bannière colorée en haut de l'app quand
 * l'utilisateur est hors-ligne ou a des mutations en attente de sync.
 *
 * États :
 * - Hors-ligne : bannière rouge "Hors ligne — X en attente"
 * - En ligne + pending > 0 : bannière orange "Synchronisation en cours… (X)"
 * - En ligne + syncing : bannière bleue "Synchronisation…"
 * - En ligne + 0 pending : pas de bannière
 *
 * Usage : placer en haut de MainTabs ou dans AppNavigator.
 */
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { useOfflineSync } from '../hooks/useOfflineSync';

export function ConnectivityBanner() {
  const { isOnline, pendingCount, syncing, conflictsCount } = useOfflineSync();

  // Pas de bannière si tout va bien
  if (isOnline && pendingCount === 0 && conflictsCount === 0 && !syncing) {
    return null;
  }

  let backgroundColor = '#16a34a'; // vert
  let message = '';

  if (!isOnline) {
    backgroundColor = '#dc2626'; // rouge
    message = `Hors ligne${pendingCount > 0 ? ` — ${pendingCount} en attente` : ''}`;
  } else if (syncing) {
    backgroundColor = '#2563eb'; // bleu
    message = `Synchronisation en cours${pendingCount > 0 ? ` (${pendingCount})` : '…'}`;
  } else if (pendingCount > 0) {
    backgroundColor = '#d97706'; // orange
    message = `${pendingCount} modification(s) en attente de sync`;
  } else if (conflictsCount > 0) {
    backgroundColor = '#d97706'; // orange
    message = `${conflictsCount} conflit(s) à résoudre`;
  }

  return (
    <View style={[styles.container, { backgroundColor }]}>
      <Text style={styles.text}>{message}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    paddingVertical: 6,
    paddingHorizontal: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  text: {
    color: '#fff',
    fontSize: 13,
    fontWeight: '600',
  },
});
