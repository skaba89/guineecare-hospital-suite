/**
 * Écran PatientDetail — dossier patient simplifié.
 *
 * Affiche :
 * - Identité (nom, prénom, DOB, genre, n° patient, contact)
 * - Section Constantes vitales (3 dernières mesures)
 * - Section Laboratoire (5 dernières demandes)
 * - Section Ordonnances (3 dernières prescriptions)
 * - Bouton "Saisir constante" (formulaire modal)
 *
 * En mode offline : les données sont mises en cache AsyncStorage et affichées
 * même sans connexion. Les nouvelles constantes saisies offline sont queueées.
 */
import React, { useCallback, useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  ActivityIndicator,
  Modal,
  TouchableOpacity,
  TextInput,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRoute } from '@react-navigation/native';
import {
  getPatient,
  listPatientMeasurements,
  listPatientLabOrders,
  listPatientClinicalNotes,
  createMeasurement,
} from '../services/api';
import { Patient } from '../types';
import { Ionicons } from '../components/Icons';

const VITAL_LABELS: Record<string, { label: string; unit: string; icon: string }> = {
  HEART_RATE: { label: 'Fréquence cardiaque', unit: 'bpm', icon: 'heart' },
  TEMPERATURE: { label: 'Température', unit: '°C', icon: 'thermometer' },
  BLOOD_PRESSURE_SYSTOLIC: { label: 'PAS', unit: 'mmHg', icon: 'pulse' },
  BLOOD_PRESSURE_DIASTOLIC: { label: 'PAD', unit: 'mmHg', icon: 'pulse' },
  RESPIRATORY_RATE: { label: 'Fréq. respiratoire', unit: '/min', icon: 'leaf' },
  OXYGEN_SAT: { label: 'SpO₂', unit: '%', icon: 'water' },
  WEIGHT: { label: 'Poids', unit: 'kg', icon: 'barbell' },
  HEIGHT: { label: 'Taille', unit: 'cm', icon: 'resize' },
  GLASGOW: { label: 'Glasgow', unit: '/15', icon: 'brain' },
  PAIN_LEVEL: { label: 'Douleur', unit: '/10', icon: 'medkit' },
};

export function PatientDetailScreen() {
  const route = useRoute();
  const { patientId } = route.params as { patientId: string };

  const [patient, setPatient] = useState<Patient | null>(null);
  const [measurements, setMeasurements] = useState<any[]>([]);
  const [labOrders, setLabOrders] = useState<any[]>([]);
  const [notes, setNotes] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');

  // Modal saisie constante
  const [modalVisible, setModalVisible] = useState(false);
  const [newVitalType, setNewVitalType] = useState('HEART_RATE');
  const [newVitalValue, setNewVitalValue] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const load = useCallback(
    async (isRefresh = false) => {
      if (isRefresh) setRefreshing(true);
      else setLoading(true);
      setError('');
      try {
        const [p, m, l, n] = await Promise.all([
          getPatient(patientId),
          listPatientMeasurements(patientId),
          listPatientLabOrders(patientId),
          listPatientClinicalNotes(patientId),
        ]);
        setPatient(p.data);
        setMeasurements(m.data || []);
        setLabOrders(l.data || []);
        setNotes((n.data || []).filter((x: any) => x.note_type === 'PRESCRIPTION'));
      } catch (e: any) {
        setError(e?.message || 'Erreur de chargement');
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [patientId]
  );

  useEffect(() => {
    load();
  }, [load]);

  async function handleSubmitVital() {
    if (!newVitalValue.trim()) {
      Alert.alert('Erreur', 'Veuillez saisir une valeur.');
      return;
    }
    setSubmitting(true);
    try {
      const meta = VITAL_LABELS[newVitalType];
      await createMeasurement({
        patient_id: patientId,
        measurement_type: newVitalType,
        value: newVitalValue.trim(),
        unit: meta?.unit,
      });
      setModalVisible(false);
      setNewVitalValue('');
      load(true);
      Alert.alert('Succès', 'Constante vitale enregistrée.');
    } catch (e: any) {
      Alert.alert(
        'Erreur',
        e?.response?.data?.detail || e?.message || "Échec de l'enregistrement"
      );
    } finally {
      setSubmitting(false);
    }
  }

  if (loading && !patient) {
    return (
      <SafeAreaView style={styles.center}>
        <ActivityIndicator size="large" color="#0f766e" />
      </SafeAreaView>
    );
  }

  if (error && !patient) {
    return (
      <SafeAreaView style={styles.center}>
        <Text style={styles.errorText}>{error}</Text>
      </SafeAreaView>
    );
  }

  const age = patient?.date_of_birth
    ? Math.floor(
        (Date.now() - new Date(patient.date_of_birth).getTime()) /
          (365.25 * 24 * 3600 * 1000)
      )
    : null;

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <ScrollView
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => load(true)} />}
        contentContainerStyle={{ padding: 16 }}
      >
        {/* Header identité */}
        <View style={styles.headerCard}>
          <View style={styles.avatarLarge}>
            <Text style={styles.avatarText}>
              {(patient?.first_name?.[0] || '') + (patient?.last_name?.[0] || '')}
            </Text>
          </View>
          <View style={{ flex: 1 }}>
            <Text style={styles.patientName}>
              {patient?.first_name} {patient?.last_name}
            </Text>
            <Text style={styles.patientNumber}>{patient?.patient_number}</Text>
            <Text style={styles.patientMeta}>
              {patient?.gender === 'M' ? '♂ Masculin' : patient?.gender === 'F' ? '♀ Féminin' : '○ Autre'}
              {age !== null && ` · ${age} ans`}
              {patient?.phone && ` · ${patient.phone}`}
            </Text>
          </View>
        </View>

        {/* Section Constantes */}
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Constantes vitales</Text>
          <TouchableOpacity
            style={styles.addButton}
            onPress={() => setModalVisible(true)}
          >
            <Ionicons name="add" size={16} color="white" />
            <Text style={styles.addButtonText}>Saisir</Text>
          </TouchableOpacity>
        </View>

        {measurements.length === 0 ? (
          <Text style={styles.emptyText}>Aucune constante enregistrée.</Text>
        ) : (
          measurements.slice(0, 5).map((m: any) => {
            const meta = VITAL_LABELS[m.measurement_type] || {
              label: m.measurement_type,
              unit: m.unit || '',
              icon: 'pulse',
            };
            return (
              <View key={m.id} style={styles.rowCard}>
                <View style={[styles.rowIcon, { backgroundColor: '#0ea5e920' }]}>
                  <Ionicons
                    name={meta.icon as any}
                    size={18}
                    color="#0ea5e9"
                  />
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={styles.rowLabel}>{meta.label}</Text>
                  <Text style={styles.rowDate}>
                    {new Date(m.recorded_at).toLocaleString('fr-FR')}
                  </Text>
                </View>
                <Text style={styles.rowValue}>
                  {m.value} <Text style={styles.rowUnit}>{meta.unit}</Text>
                </Text>
              </View>
            );
          })
        )}

        {/* Section Laboratoire */}
        <Text style={[styles.sectionTitle, { marginTop: 24 }]}>Laboratoire</Text>
        {labOrders.length === 0 ? (
          <Text style={styles.emptyText}>Aucune demande de laboratoire.</Text>
        ) : (
          labOrders.slice(0, 5).map((l: any) => (
            <View key={l.id} style={styles.rowCard}>
              <View style={[styles.rowIcon, { backgroundColor: '#7c3aed20' }]}>
                <Ionicons name="flask" size={18} color="#7c3aed" />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.rowLabel}>Demande labo</Text>
                <Text style={styles.rowDate}>
                  {new Date(l.ordered_at).toLocaleDateString('fr-FR')} ·{' '}
                  {l.priority || 'NORMAL'}
                </Text>
              </View>
              <View
                style={[
                  styles.statusBadge,
                  l.status === 'VALIDATED'
                    ? { backgroundColor: '#10b981' }
                    : l.status === 'CANCELLED'
                    ? { backgroundColor: '#94a3b8' }
                    : { backgroundColor: '#f59e0b' },
                ]}
              >
                <Text style={styles.statusText}>{l.status}</Text>
              </View>
            </View>
          ))
        )}

        {/* Section Ordonnances */}
        <Text style={[styles.sectionTitle, { marginTop: 24 }]}>Ordonnances récentes</Text>
        {notes.length === 0 ? (
          <Text style={styles.emptyText}>Aucune prescription.</Text>
        ) : (
          notes.slice(0, 3).map((n: any) => (
            <View key={n.id} style={styles.rowCard}>
              <View style={[styles.rowIcon, { backgroundColor: '#10b98120' }]}>
                <Ionicons name="medkit" size={18} color="#10b981" />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.rowLabel} numberOfLines={2}>
                  {n.content?.slice(0, 100)}
                  {n.content?.length > 100 ? '…' : ''}
                </Text>
                <Text style={styles.rowDate}>
                  {new Date(n.created_at).toLocaleDateString('fr-FR')}
                </Text>
              </View>
            </View>
          ))
        )}
      </ScrollView>

      {/* Modal saisie constante */}
      <Modal visible={modalVisible} transparent animationType="slide">
        <View style={styles.modalOverlay}>
          <View style={styles.modalCard}>
            <Text style={styles.modalTitle}>Saisir une constante</Text>

            <Text style={styles.modalLabel}>Type</Text>
            <View style={styles.pickerWrap}>
              {Object.entries(VITAL_LABELS).map(([key, meta]) => (
                <TouchableOpacity
                  key={key}
                  style={[
                    styles.pill,
                    newVitalType === key && styles.pillSelected,
                  ]}
                  onPress={() => setNewVitalType(key)}
                >
                  <Text
                    style={[
                      styles.pillText,
                      newVitalType === key && styles.pillTextSelected,
                    ]}
                  >
                    {meta.label}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>

            <Text style={styles.modalLabel}>Valeur</Text>
            <TextInput
              style={styles.modalInput}
              value={newVitalValue}
              onChangeText={setNewVitalValue}
              placeholder={`Saisir en ${VITAL_LABELS[newVitalType]?.unit || ''}`}
              keyboardType="numeric"
              autoFocus
            />

            <View style={styles.modalActions}>
              <TouchableOpacity
                style={[styles.modalBtn, styles.modalBtnSecondary]}
                onPress={() => setModalVisible(false)}
              >
                <Text style={styles.modalBtnText}>Annuler</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.modalBtn, styles.modalBtnPrimary]}
                onPress={handleSubmitVital}
                disabled={submitting}
              >
                <Text style={styles.modalBtnTextPrimary}>
                  {submitting ? 'Enregistrement…' : 'Enregistrer'}
                </Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f8fafc' },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  errorText: { color: '#dc2626', fontSize: 14 },
  headerCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
  },
  avatarLarge: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: '#0f766e',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 16,
  },
  avatarText: { color: 'white', fontWeight: '800', fontSize: 20 },
  patientName: { fontSize: 20, fontWeight: '800', color: '#0f172a' },
  patientNumber: {
    fontSize: 13,
    color: '#64748b',
    fontFamily: 'monospace',
    marginTop: 2,
  },
  patientMeta: { fontSize: 12, color: '#94a3b8', marginTop: 4 },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 16,
    marginBottom: 8,
  },
  sectionTitle: { fontSize: 16, fontWeight: '700', color: '#0f172a' },
  addButton: {
    flexDirection: 'row',
    backgroundColor: '#0f766e',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
    alignItems: 'center',
  },
  addButtonText: { color: 'white', fontSize: 13, fontWeight: '600', marginLeft: 4 },
  emptyText: { color: '#94a3b8', fontSize: 13, paddingVertical: 12 },
  rowCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'white',
    borderRadius: 10,
    padding: 12,
    marginBottom: 6,
  },
  rowIcon: {
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  rowLabel: { fontSize: 14, fontWeight: '600', color: '#0f172a' },
  rowDate: { fontSize: 11, color: '#94a3b8', marginTop: 2 },
  rowValue: { fontSize: 18, fontWeight: '800', color: '#0f172a' },
  rowUnit: { fontSize: 11, color: '#94a3b8', fontWeight: '400' },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  statusText: { color: 'white', fontSize: 10, fontWeight: '700' },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'flex-end',
  },
  modalCard: {
    backgroundColor: 'white',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    padding: 20,
    maxHeight: '90%',
  },
  modalTitle: { fontSize: 18, fontWeight: '800', color: '#0f172a', marginBottom: 16 },
  modalLabel: {
    fontSize: 13,
    color: '#475569',
    fontWeight: '600',
    marginTop: 12,
    marginBottom: 8,
  },
  pickerWrap: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  pill: {
    borderWidth: 1,
    borderColor: '#e2e8f0',
    borderRadius: 16,
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
  pillSelected: { backgroundColor: '#0f766e', borderColor: '#0f766e' },
  pillText: { color: '#475569', fontSize: 12 },
  pillTextSelected: { color: 'white', fontWeight: '600' },
  modalInput: {
    borderWidth: 1,
    borderColor: '#e2e8f0',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    color: '#0f172a',
  },
  modalActions: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 20,
  },
  modalBtn: {
    flex: 1,
    padding: 14,
    borderRadius: 8,
    alignItems: 'center',
  },
  modalBtnSecondary: { backgroundColor: '#f1f5f9' },
  modalBtnPrimary: { backgroundColor: '#0f766e' },
  modalBtnText: { color: '#475569', fontWeight: '600' },
  modalBtnTextPrimary: { color: 'white', fontWeight: '700' },
});
