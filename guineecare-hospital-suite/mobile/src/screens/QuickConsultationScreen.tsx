/**
 * QuickConsultationScreen — saisie rapide de note médicale.
 *
 * v2.7.0 — Phase 7 : permet à un médecin/infirmier de saisir rapidement
 * une note d'observation au lit du patient, sans naviguer dans toute la fiche.
 *
 * Workflow :
 * 1. Sélectionner un patient (recherche par nom/numéro)
 * 2. Saisir le type de note (OBSERVATION, CONSULTATION, NOTE)
 * 3. Saisir le contenu (textarea multi-lignes)
 * 4. Sauvegarder → POST /clinical/patients/{id}/notes
 *    - Si online : envoi immédiat
 *    - Si offline : enqueue dans la file d'attente
 *
 * Usage : accessible via FAB sur DashboardScreen.
 */
import React, { useState, useCallback } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Alert,
  ActivityIndicator,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation } from '@react-navigation/native';
import { api } from '../services/api';
import { useOfflineSync } from '../hooks/useOfflineSync';
import { Patient } from '../types';

const NOTE_TYPES = [
  { value: 'OBSERVATION', label: 'Observation' },
  { value: 'CONSULTATION', label: 'Consultation' },
  { value: 'NOTE', label: 'Note générale' },
];

export function QuickConsultationScreen() {
  const navigation = useNavigation<any>();
  const { isOnline, enqueue } = useOfflineSync();

  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<Patient[]>([]);
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [searching, setSearching] = useState(false);

  const [noteType, setNoteType] = useState('OBSERVATION');
  const [content, setContent] = useState('');
  const [saving, setSaving] = useState(false);

  const searchPatients = useCallback(async (query: string) => {
    if (query.trim().length < 2) {
      setSearchResults([]);
      return;
    }
    setSearching(true);
    try {
      const resp = await api.get('/patients', {
        params: { search: query.trim(), page: 1, page_size: 10 },
      });
      setSearchResults(resp.data?.data || []);
    } catch (e) {
      // En offline, on ne peut pas rechercher — l'utilisateur doit scanner le QR
      setSearchResults([]);
    } finally {
      setSearching(false);
    }
  }, []);

  const handleSave = async () => {
    if (!selectedPatient) {
      Alert.alert('Erreur', 'Veuillez sélectionner un patient.');
      return;
    }
    if (!content.trim()) {
      Alert.alert('Erreur', 'Veuillez saisir le contenu de la note.');
      return;
    }

    setSaving(true);
    const payload = {
      note_type: noteType,
      content: content.trim(),
    };
    const path = `/clinical/patients/${selectedPatient.id}/notes`;

    try {
      if (isOnline) {
        await api.post(path, payload);
        Alert.alert('Succès', 'Note enregistrée.', [
          { text: 'OK', onPress: () => navigation.goBack() },
        ]);
      } else {
        // Offline : mettre en file d'attente
        await enqueue('POST', path, payload);
        Alert.alert(
          'Sauvegardé hors-ligne',
          'La note sera synchronisée au retour du réseau.',
          [{ text: 'OK', onPress: () => navigation.goBack() }]
        );
      }
    } catch (e: any) {
      const status = e?.response?.status;
      let msg = 'Erreur lors de l\'enregistrement.';
      if (status === 403) msg = 'Vous n\'avez pas la permission de créer une note.';
      else if (status === 404) msg = 'Patient introuvable.';
      else if (status >= 500) msg = 'Serveur indisponible. Réessayez.';
      Alert.alert('Erreur', msg);
    } finally {
      setSaving(false);
    }
  };

  return (
    <SafeAreaView style={styles.container} edges={['top', 'bottom']}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        style={{ flex: 1 }}
      >
        <ScrollView contentContainerStyle={styles.scroll}>
          <Text style={styles.title}>Note rapide</Text>
          <Text style={styles.subtitle}>
            Saisissez une note d'observation au lit du patient
          </Text>

          {/* Étape 1 : sélection patient */}
          {!selectedPatient ? (
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>1. Sélectionner le patient</Text>
              <TextInput
                style={styles.input}
                placeholder="Nom, numéro ou ID patient…"
                value={searchQuery}
                onChangeText={(text) => {
                  setSearchQuery(text);
                  searchPatients(text);
                }}
                autoCapitalize="none"
              />
              {searching && <ActivityIndicator style={{ marginVertical: 8 }} />}
              {searchResults.length > 0 && (
                <View style={styles.resultsList}>
                  {searchResults.map((p) => (
                    <TouchableOpacity
                      key={p.id}
                      style={styles.resultItem}
                      onPress={() => setSelectedPatient(p)}
                    >
                      <Text style={styles.resultName}>
                        {p.first_name} {p.last_name}
                      </Text>
                      <Text style={styles.resultSub}>{p.patient_number}</Text>
                    </TouchableOpacity>
                  ))}
                </View>
              )}
              {searchQuery.length >= 2 && !searching && searchResults.length === 0 && (
                <Text style={styles.emptyText}>
                  {isOnline ? 'Aucun patient trouvé.' : 'Recherche impossible hors-ligne — utilisez le scan QR.'}
                </Text>
              )}
            </View>
          ) : (
            <View style={styles.section}>
              <View style={styles.selectedPatientRow}>
                <View style={{ flex: 1 }}>
                  <Text style={styles.selectedName}>
                    {selectedPatient.first_name} {selectedPatient.last_name}
                  </Text>
                  <Text style={styles.selectedSub}>{selectedPatient.patient_number}</Text>
                </View>
                <TouchableOpacity
                  onPress={() => setSelectedPatient(null)}
                  style={styles.changeButton}
                >
                  <Text style={styles.changeButtonText}>Changer</Text>
                </TouchableOpacity>
              </View>
            </View>
          )}

          {/* Étape 2 : type de note */}
          {selectedPatient && (
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>2. Type de note</Text>
              <View style={styles.typeRow}>
                {NOTE_TYPES.map((t) => (
                  <TouchableOpacity
                    key={t.value}
                    style={[
                      styles.typeButton,
                      noteType === t.value && styles.typeButtonActive,
                    ]}
                    onPress={() => setNoteType(t.value)}
                  >
                    <Text
                      style={[
                        styles.typeButtonText,
                        noteType === t.value && styles.typeButtonTextActive,
                      ]}
                    >
                      {t.label}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>
          )}

          {/* Étape 3 : contenu */}
          {selectedPatient && (
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>3. Contenu de la note</Text>
              <TextInput
                style={[styles.input, styles.textarea]}
                placeholder="Saisissez vos observations cliniques…"
                value={content}
                onChangeText={setContent}
                multiline
                numberOfLines={6}
                textAlignVertical="top"
              />
            </View>
          )}

          {/* Bouton sauvegarder */}
          {selectedPatient && (
            <TouchableOpacity
              style={[styles.saveButton, !isOnline && styles.saveButtonOffline]}
              onPress={handleSave}
              disabled={saving}
            >
              {saving ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text style={styles.saveButtonText}>
                  {isOnline ? 'Enregistrer' : 'Enregistrer hors-ligne'}
                </Text>
              )}
            </TouchableOpacity>
          )}
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f8fafc' },
  scroll: { padding: 16 },
  title: { fontSize: 22, fontWeight: '700', color: '#1e293b', marginBottom: 4 },
  subtitle: { fontSize: 14, color: '#64748b', marginBottom: 20 },
  section: { marginBottom: 20 },
  sectionTitle: { fontSize: 15, fontWeight: '600', color: '#475569', marginBottom: 8 },
  input: {
    borderWidth: 1,
    borderColor: '#e2e8f0',
    borderRadius: 8,
    padding: 12,
    fontSize: 15,
    backgroundColor: '#fff',
    color: '#1e293b',
  },
  textarea: {
    minHeight: 120,
  },
  resultsList: {
    marginTop: 8,
    borderWidth: 1,
    borderColor: '#e2e8f0',
    borderRadius: 8,
    backgroundColor: '#fff',
    overflow: 'hidden',
  },
  resultItem: {
    padding: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f1f5f9',
  },
  resultName: { fontSize: 15, fontWeight: '600', color: '#1e293b' },
  resultSub: { fontSize: 12, color: '#64748b', marginTop: 2 },
  emptyText: { fontSize: 13, color: '#94a3b8', marginTop: 8, fontStyle: 'italic' },
  selectedPatientRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#e8f5ee',
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#bbf7d0',
  },
  selectedName: { fontSize: 15, fontWeight: '600', color: '#0f6b3e' },
  selectedSub: { fontSize: 12, color: '#16a34a', marginTop: 2 },
  changeButton: {
    paddingVertical: 6,
    paddingHorizontal: 12,
    backgroundColor: '#fff',
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#bbf7d0',
  },
  changeButtonText: { fontSize: 12, color: '#0f6b3e', fontWeight: '600' },
  typeRow: { flexDirection: 'row', gap: 8 },
  typeButton: {
    flex: 1,
    paddingVertical: 10,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#e2e8f0',
    borderRadius: 8,
    backgroundColor: '#fff',
  },
  typeButtonActive: {
    backgroundColor: '#0f6b3e',
    borderColor: '#0f6b3e',
  },
  typeButtonText: { fontSize: 13, color: '#64748b', fontWeight: '500' },
  typeButtonTextActive: { color: '#fff', fontWeight: '600' },
  saveButton: {
    backgroundColor: '#0f6b3e',
    paddingVertical: 14,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 8,
  },
  saveButtonOffline: {
    backgroundColor: '#d97706',
  },
  saveButtonText: { color: '#fff', fontSize: 16, fontWeight: '600' },
});
