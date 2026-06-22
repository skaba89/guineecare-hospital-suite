/**
 * Écran Dashboard — KPIs principaux du facility courant.
 *
 * Affiche :
 * - Salutation personnalisée + nom du facility
 * - Cartes KPI : patients actifs, admissions en cours, lits occupés, urgences
 * - Cartes secondaires : labo en attente, imagerie en attente, recette du jour
 * - Pull-to-refresh
 *
 * En v1.7 on appelle /reporting/dashboard (endpoint existant côté backend).
 * Les KPIs temps réel via WebSocket seront ajoutés en v1.8.
 */
import React, { useCallback, useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAuth } from '../context/AuthContext';
import { getDashboardKPIs } from '../services/api';
import { DashboardKPIs } from '../types';
import { Ionicons } from '../components/Icons';

export function DashboardScreen() {
  const { user } = useAuth();
  const [kpis, setKpis] = useState<DashboardKPIs | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = await getDashboardKPIs();
      setKpis(data);
    } catch (e: any) {
      setError(e?.message || 'Erreur de chargement');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const roleLabels: Record<string, string> = {
    SUPER_ADMIN: 'Super Admin',
    ADMIN: 'Administrateur',
    DOCTOR: 'Médecin',
    NURSE: 'Infirmier',
    MIDWIFE: 'Sage-femme',
    PHARMACIST: 'Pharmacien',
    LAB_TECH: 'Laborantin',
    CASHIER: 'Caissier',
  };

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <ScrollView
        contentContainerStyle={styles.scroll}
        refreshControl={<RefreshControl refreshing={loading} onRefresh={load} />}
      >
        <View style={styles.header}>
          <View>
            <Text style={styles.greeting}>Bonjour,</Text>
            <Text style={styles.userName}>
              {user?.first_name} {user?.last_name}
            </Text>
            <Text style={styles.role}>{roleLabels[user?.role || ''] || user?.role}</Text>
          </View>
          <View style={styles.logoBadge}>
            <Text style={styles.logoText}>GC</Text>
          </View>
        </View>

        {error && (
          <View style={styles.errorBox}>
            <Text style={styles.errorText}>{error}</Text>
          </View>
        )}

        <Text style={styles.sectionTitle}>Aperçu du jour</Text>

        <View style={styles.kpiGrid}>
          <KpiCard
            label="Patients actifs"
            value={kpis?.patients_total}
            icon="people"
            color="#0ea5e9"
          />
          <KpiCard
            label="Admissions en cours"
            value={kpis?.admissions_active}
            icon="log-in"
            color="#10b981"
          />
          <KpiCard
            label="Lits occupés"
            value={kpis?.beds_occupied}
            icon="bed"
            color="#f59e0b"
          />
          <KpiCard
            label="Urgences"
            value={kpis?.emergencies_in_progress}
            icon="warning"
            color="#dc2626"
          />
        </View>

        <Text style={styles.sectionTitle}>Tâches en attente</Text>
        <View style={styles.taskList}>
          <TaskRow
            icon="flask"
            color="#7c3aed"
            label="Résultats labo à valider"
            count={kpis?.pending_lab_results}
          />
          <TaskRow
            icon="scan"
            color="#0891b2"
            label="Imagerie en attente"
            count={kpis?.pending_imaging}
          />
        </View>

        {kpis && (kpis.revenue_today > 0 || kpis.outstanding_balance > 0) && (
          <>
            <Text style={styles.sectionTitle}>Finances</Text>
            <View style={styles.financeCard}>
              <View style={styles.financeRow}>
                <Text style={styles.financeLabel}>Recette du jour</Text>
                <Text style={[styles.financeValue, { color: '#10b981' }]}>
                  {kpis.revenue_today.toLocaleString('fr-FR')} GNF
                </Text>
              </View>
              <View style={[styles.financeRow, { borderBottomWidth: 0 }]}>
                <Text style={styles.financeLabel}>Créances impayées</Text>
                <Text style={[styles.financeValue, { color: '#dc2626' }]}>
                  {kpis.outstanding_balance.toLocaleString('fr-FR')} GNF
                </Text>
              </View>
            </View>
          </>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

function KpiCard({
  label,
  value,
  icon,
  color,
}: {
  label: string;
  value: number | undefined;
  icon: keyof typeof Ionicons.glyphMap;
  color: string;
}) {
  return (
    <View style={[styles.kpiCard, { borderTopColor: color }]}>
      <View style={[styles.kpiIcon, { backgroundColor: color + '20' }]}>
        <Ionicons name={icon} size={20} color={color} />
      </View>
      <Text style={styles.kpiValue}>{value ?? '—'}</Text>
      <Text style={styles.kpiLabel}>{label}</Text>
    </View>
  );
}

function TaskRow({
  icon,
  color,
  label,
  count,
}: {
  icon: keyof typeof Ionicons.glyphMap;
  color: string;
  label: string;
  count: number | undefined;
}) {
  return (
    <View style={styles.taskRow}>
      <View style={[styles.taskIcon, { backgroundColor: color + '20' }]}>
        <Ionicons name={icon} size={20} color={color} />
      </View>
      <Text style={styles.taskLabel}>{label}</Text>
      <View style={[styles.taskBadge, count ? { backgroundColor: color } : { backgroundColor: '#e2e8f0' }]}>
        <Text style={[styles.taskBadgeText, !count && { color: '#94a3b8' }]}>
          {count ?? 0}
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f8fafc' },
  scroll: { padding: 16, paddingBottom: 32 },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 24,
  },
  greeting: { fontSize: 13, color: '#64748b' },
  userName: { fontSize: 22, fontWeight: '800', color: '#0f172a' },
  role: { fontSize: 12, color: '#0f766e', marginTop: 2 },
  logoBadge: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#0f766e',
    alignItems: 'center',
    justifyContent: 'center',
  },
  logoText: { color: 'white', fontWeight: '800', fontSize: 18 },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#0f172a',
    marginTop: 24,
    marginBottom: 12,
  },
  kpiGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  kpiCard: {
    flexBasis: '47%',
    flexGrow: 1,
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 16,
    borderTopWidth: 3,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  kpiIcon: {
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 8,
  },
  kpiValue: { fontSize: 24, fontWeight: '800', color: '#0f172a' },
  kpiLabel: { fontSize: 12, color: '#64748b', marginTop: 4 },
  taskList: { gap: 8 },
  taskRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'white',
    borderRadius: 8,
    padding: 14,
  },
  taskIcon: {
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  taskLabel: { flex: 1, fontSize: 14, color: '#0f172a' },
  taskBadge: {
    minWidth: 28,
    height: 28,
    borderRadius: 14,
    paddingHorizontal: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  taskBadgeText: { color: 'white', fontWeight: '700', fontSize: 13 },
  financeCard: {
    backgroundColor: 'white',
    borderRadius: 12,
    overflow: 'hidden',
  },
  financeRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#e2e8f0',
  },
  financeLabel: { fontSize: 14, color: '#475569' },
  financeValue: { fontSize: 16, fontWeight: '700' },
  errorBox: {
    backgroundColor: '#fef2f2',
    borderWidth: 1,
    borderColor: '#fecaca',
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
  },
  errorText: { color: '#dc2626', fontSize: 13 },
});
