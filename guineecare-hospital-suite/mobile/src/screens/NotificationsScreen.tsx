/**
 * Écran Notifications — liste des notifications de l'utilisateur courant.
 *
 * - Tri par date décroissante
 * - Badge priorité (urgent=rouge, high=orange, normal=bleu, low=gris)
 * - Tap → marquer comme lu
 * - Bouton "Tout marquer comme lu"
 * - Pull-to-refresh
 */
import React, { useCallback, useEffect, useState } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { listNotifications, markNotificationRead } from '../services/api';
import { NotificationItem } from '../types';

const PRIORITY_COLORS: Record<string, string> = {
  urgent: '#dc2626',
  high: '#f59e0b',
  normal: '#0ea5e9',
  low: '#94a3b8',
};

const PRIORITY_LABELS: Record<string, string> = {
  urgent: 'URGENT',
  high: 'HAUTE',
  normal: 'NORMALE',
  low: 'BASSE',
};

const CATEGORY_LABELS: Record<string, string> = {
  lab_result: 'Résultat labo',
  lab_critical: 'Labo critique',
  appointment: 'Rendez-vous',
  appointment_reminder: 'Rappel RDV',
  invoice_ready: 'Facture',
  quality_alert: 'Alerte qualité',
  incident_critical: 'Incident',
  shift_assignment: 'Planning',
  shift_swap_request: 'Remplacement',
  system: 'Système',
};

export function NotificationsScreen() {
  const [items, setItems] = useState<NotificationItem[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    setError('');
    try {
      const data = await listNotifications({ page: 1, page_size: 50 });
      setItems(data.data || []);
      setUnreadCount(data.unread_count || 0);
    } catch (e: any) {
      setError(e?.message || 'Erreur de chargement');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function handleRead(item: NotificationItem) {
    if (item.read_at) return;
    try {
      await markNotificationRead(item.id);
      setItems((prev) =>
        prev.map((n) => (n.id === item.id ? { ...n, read_at: new Date().toISOString() } : n))
      );
      setUnreadCount((c) => Math.max(0, c - 1));
    } catch (e) {
      // ignore
    }
  }

  async function handleMarkAllRead() {
    // Mark all locally optimistic
    setItems((prev) =>
      prev.map((n) => (n.read_at ? n : { ...n, read_at: new Date().toISOString() }))
    );
    setUnreadCount(0);
    // Refresh to sync with server
    load(true);
  }

  const renderItem = ({ item }: { item: NotificationItem }) => {
    const color = PRIORITY_COLORS[item.priority] || '#94a3b8';
    const isUnread = !item.read_at;
    return (
      <TouchableOpacity
        style={[styles.notifCard, isUnread && styles.notifCardUnread]}
        onPress={() => handleRead(item)}
      >
        <View style={[styles.priorityBar, { backgroundColor: color }]} />
        <View style={{ flex: 1, padding: 12 }}>
          <View style={styles.notifHeader}>
            <Text style={styles.category}>
              {CATEGORY_LABELS[item.category] || item.category}
            </Text>
            <Text style={styles.date}>
              {new Date(item.created_at).toLocaleString('fr-FR', {
                day: '2-digit',
                month: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
              })}
            </Text>
          </View>
          <Text style={[styles.title, isUnread && styles.titleUnread]} numberOfLines={2}>
            {item.title}
          </Text>
          {item.body && (
            <Text style={styles.body} numberOfLines={3}>
              {item.body}
            </Text>
          )}
          <View style={styles.notifFooter}>
            <View style={[styles.priorityBadge, { backgroundColor: color + '20' }]}>
              <Text style={[styles.priorityText, { color }]}>{PRIORITY_LABELS[item.priority]}</Text>
            </View>
            {isUnread && <Text style={styles.unreadDot}>●</Text>}
          </View>
        </View>
      </TouchableOpacity>
    );
  };

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <View style={styles.header}>
        <View>
          <Text style={styles.title}>Notifications</Text>
          {unreadCount > 0 && (
            <Text style={styles.subtitle}>
              {unreadCount} non lue{unreadCount > 1 ? 's' : ''}
            </Text>
          )}
        </View>
        {unreadCount > 0 && (
          <TouchableOpacity onPress={handleMarkAllRead} style={styles.markAllBtn}>
            <Text style={styles.markAllText}>Tout marquer lu</Text>
          </TouchableOpacity>
        )}
      </View>

      {error && (
        <View style={styles.errorBox}>
          <Text style={styles.errorText}>{error}</Text>
        </View>
      )}

      <FlatList
        data={items}
        keyExtractor={(item) => item.id}
        renderItem={renderItem}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => load(true)} />}
        contentContainerStyle={{ padding: 16, paddingBottom: 32 }}
        ListEmptyComponent={
          !loading ? (
            <View style={styles.emptyState}>
              <Text style={styles.emptyText}>Aucune notification.</Text>
            </View>
          ) : null
        }
        ListFooterComponent={
          loading ? <ActivityIndicator size="large" color="#0f766e" /> : null
        }
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f8fafc' },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
  },
  title: { fontSize: 24, fontWeight: '800', color: '#0f172a' },
  subtitle: { fontSize: 13, color: '#dc2626', marginTop: 2 },
  markAllBtn: { padding: 8 },
  markAllText: { color: '#0f766e', fontSize: 13, fontWeight: '600' },
  notifCard: {
    flexDirection: 'row',
    backgroundColor: 'white',
    borderRadius: 10,
    marginBottom: 8,
    overflow: 'hidden',
  },
  notifCardUnread: {
    borderLeftWidth: 0,
    backgroundColor: '#f0fdfa',
  },
  priorityBar: { width: 4 },
  notifHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  category: {
    fontSize: 11,
    color: '#0f766e',
    fontWeight: '700',
    textTransform: 'uppercase',
  },
  date: { fontSize: 11, color: '#94a3b8' },
  title: { fontSize: 14, fontWeight: '600', color: '#475569', marginTop: 4 },
  titleUnread: { color: '#0f172a', fontWeight: '700' },
  body: { fontSize: 13, color: '#64748b', marginTop: 4 },
  notifFooter: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 8,
  },
  priorityBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
  },
  priorityText: { fontSize: 10, fontWeight: '700' },
  unreadDot: { color: '#0f766e', fontSize: 10, marginLeft: 8 },
  emptyState: { alignItems: 'center', paddingVertical: 48 },
  emptyText: { color: '#94a3b8', fontSize: 14 },
  errorBox: {
    backgroundColor: '#fef2f2',
    borderWidth: 1,
    borderColor: '#fecaca',
    borderRadius: 8,
    padding: 12,
    marginHorizontal: 16,
  },
  errorText: { color: '#dc2626', fontSize: 13 },
});
