/**
 * Écran PatientsList — liste paginée des patients avec recherche debouncée.
 *
 * - Recherche server-side (debounce 300ms) via /patients?search=...
 * - Pagination offset classique (20/page)
 * - Pull-to-refresh
 * - Navigation vers PatientDetailScreen sur tap
 * - Bouton flottant pour scanner un QR patient (raccourci)
 */
import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  View,
  Text,
  TextInput,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { listPatients } from '../services/api';
import { Patient } from '../types';
import { Ionicons } from '../components/Icons';

type RootStackParamList = {
  MainTabs: undefined;
  PatientDetail: { patientId: string };
  PatientForm: undefined;
};

export function PatientsListScreen() {
  const navigation = useNavigation<NativeStackNavigationProp<RootStackParamList>>();
  const [patients, setPatients] = useState<Patient[]>([]);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const load = useCallback(
    async (pageNum: number, searchTerm: string, isRefresh = false) => {
      if (isRefresh) setRefreshing(true);
      else setLoading(true);
      setError('');
      try {
        const data = await listPatients({
          page: pageNum,
          page_size: 20,
          search: searchTerm || undefined,
        });
        setPatients(data.data || []);
        setPage(data.page || pageNum);
        setTotalPages(data.total_pages || 0);
        setTotal(data.total || 0);
      } catch (e: any) {
        setError(e?.message || 'Erreur de chargement');
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    []
  );

  useEffect(() => {
    load(1, '');
  }, [load]);

  const onSearchChange = (text: string) => {
    setSearch(text);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      load(1, text);
    }, 300);
  };

  const onRefresh = useCallback(() => {
    load(1, search, true);
  }, [load, search]);

  const renderItem = ({ item }: { item: Patient }) => (
    <TouchableOpacity
      style={styles.patientCard}
      onPress={() => navigation.navigate('PatientDetail', { patientId: item.id })}
    >
      <View style={styles.avatar}>
        <Text style={styles.avatarText}>
          {(item.first_name?.[0] || '') + (item.last_name?.[0] || '')}
        </Text>
      </View>
      <View style={styles.patientInfo}>
        <Text style={styles.patientName}>
          {item.first_name} {item.last_name}
        </Text>
        <Text style={styles.patientNumber}>{item.patient_number}</Text>
        <Text style={styles.patientMeta}>
          {item.gender === 'M' ? '♂' : item.gender === 'F' ? '♀' : '○'} ·{' '}
          {item.date_of_birth
            ? new Date(item.date_of_birth).toLocaleDateString('fr-FR')
            : 'N/A'}{' '}
          · {item.status === 'ACTIVE' ? '✓' : '⚠'}
        </Text>
      </View>
      <Ionicons name="chevron-forward" size={20} color="#cbd5e1" />
    </TouchableOpacity>
  );

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <View style={styles.header}>
        <Text style={styles.title}>Patients</Text>
        <TouchableOpacity
          style={styles.addButton}
          onPress={() => navigation.navigate('PatientForm')}
        >
          <Ionicons name="person-add" size={20} color="white" />
          <Text style={styles.addButtonText}>Nouveau</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.searchBar}>
        <Ionicons name="search" size={18} color="#94a3b8" style={{ marginHorizontal: 8 }} />
        <TextInput
          style={styles.searchInput}
          placeholder="Rechercher par nom, numéro, ID..."
          placeholderTextColor="#94a3b8"
          value={search}
          onChangeText={onSearchChange}
          autoCapitalize="none"
          autoCorrect={false}
        />
        {search.length > 0 && (
          <TouchableOpacity
            onPress={() => {
              onSearchChange('');
            }}
            style={{ paddingHorizontal: 8 }}
          >
            <Ionicons name="close-circle" size={18} color="#94a3b8" />
          </TouchableOpacity>
        )}
      </View>

      {error && (
        <View style={styles.errorBox}>
          <Text style={styles.errorText}>{error}</Text>
        </View>
      )}

      <FlatList
        data={patients}
        keyExtractor={(item) => item.id}
        renderItem={renderItem}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        contentContainerStyle={{ padding: 16, paddingBottom: 80 }}
        ListEmptyComponent={
          !loading ? (
            <View style={styles.emptyState}>
              <Ionicons name="people-outline" size={48} color="#cbd5e1" />
              <Text style={styles.emptyText}>
                {search ? 'Aucun patient trouvé pour cette recherche.' : 'Aucun patient.'}
              </Text>
            </View>
          ) : null
        }
        ListFooterComponent={
          loading ? (
            <ActivityIndicator size="large" color="#0f766e" style={{ marginVertical: 16 }} />
          ) : null
        }
      />

      {/* Pagination bar */}
      {totalPages > 1 && (
        <View style={styles.paginationBar}>
          <TouchableOpacity
            onPress={() => load(Math.max(1, page - 1), search)}
            disabled={page <= 1}
            style={[styles.pageBtn, page <= 1 && styles.pageBtnDisabled]}
          >
            <Ionicons name="chevron-back" size={20} color={page <= 1 ? '#cbd5e1' : '#0f766e'} />
          </TouchableOpacity>
          <Text style={styles.pageInfo}>
            Page {page} / {totalPages} · {total} patients
          </Text>
          <TouchableOpacity
            onPress={() => load(Math.min(totalPages, page + 1), search)}
            disabled={page >= totalPages}
            style={[styles.pageBtn, page >= totalPages && styles.pageBtnDisabled]}
          >
            <Ionicons
              name="chevron-forward"
              size={20}
              color={page >= totalPages ? '#cbd5e1' : '#0f766e'}
            />
          </TouchableOpacity>
        </View>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f8fafc' },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  title: { fontSize: 24, fontWeight: '800', color: '#0f172a' },
  addButton: {
    flexDirection: 'row',
    backgroundColor: '#0f766e',
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: 'center',
    gap: 6,
  },
  addButtonText: { color: 'white', fontSize: 13, fontWeight: '700' },
  searchBar: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'white',
    marginHorizontal: 16,
    marginBottom: 8,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#e2e8f0',
    height: 44,
  },
  searchInput: { flex: 1, fontSize: 14, color: '#0f172a' },
  patientCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'white',
    borderRadius: 10,
    padding: 14,
    marginBottom: 8,
  },
  avatar: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#0f766e',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  avatarText: { color: 'white', fontWeight: '700', fontSize: 16 },
  patientInfo: { flex: 1 },
  patientName: { fontSize: 15, fontWeight: '700', color: '#0f172a' },
  patientNumber: {
    fontSize: 12,
    color: '#64748b',
    fontFamily: 'monospace',
    marginTop: 2,
  },
  patientMeta: { fontSize: 11, color: '#94a3b8', marginTop: 2 },
  emptyState: { alignItems: 'center', paddingVertical: 48 },
  emptyText: { color: '#94a3b8', marginTop: 12, fontSize: 14 },
  paginationBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: 'white',
    borderTopWidth: 1,
    borderTopColor: '#e2e8f0',
  },
  pageBtn: { padding: 8 },
  pageBtnDisabled: { opacity: 0.5 },
  pageInfo: { fontSize: 13, color: '#475569' },
  errorBox: {
    backgroundColor: '#fef2f2',
    borderWidth: 1,
    borderColor: '#fecaca',
    borderRadius: 8,
    padding: 12,
    marginHorizontal: 16,
    marginVertical: 8,
  },
  errorText: { color: '#dc2626', fontSize: 13 },
});
