/**
 * Écran PatientForm — création d'un nouveau patient (première visite).
 *
 * Champs :
 * - Obligatoires : Prénom, Nom
 * - Optionnels : Date de naissance, Genre, Téléphone, Adresse, ID national,
 *   N° assurance, Contact d'urgence (nom + téléphone)
 *
 * Comportement :
 * - Validation basique (prénom + nom non vides)
 * - Si online : POST /patients → navigation vers PatientDetail
 * - Si offline : enqueue mutation → message "Sera synchronisé" → retour liste
 * - Le patient_number (PAT-YYYYMMDDHHMMSS) et facility_id sont auto-générés
 *   côté backend, donc non saisis ici.
 */
import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { createPatient } from '../services/api';
import { useOfflineSync } from '../hooks/useOfflineSync';
import { useAuth } from '../context/AuthContext';
import { Ionicons } from '../components/Icons';

type RootStackParamList = {
  MainTabs: undefined;
  PatientDetail: { patientId: string };
};

export function PatientFormScreen() {
  const navigation = useNavigation<NativeStackNavigationProp<RootStackParamList>>();
  const { user } = useAuth();
  const { isOnline, enqueue } = useOfflineSync();

  // Champs obligatoires
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');

  // Champs optionnels
  const [dateOfBirth, setDateOfBirth] = useState(''); // YYYY-MM-DD
  const [gender, setGender] = useState<string>('');
  const [phone, setPhone] = useState('');
  const [address, setAddress] = useState('');
  const [nationalId, setNationalId] = useState('');
  const [insuranceNumber, setInsuranceNumber] = useState('');
  const [emergencyName, setEmergencyName] = useState('');
  const [emergencyPhone, setEmergencyPhone] = useState('');

  // Champs médicaux (v1.7.1) — valeurs par défaut "Non renseigné"
  const [bloodType, setBloodType] = useState('NON_RENSEIGNE');
  const [allergies, setAllergies] = useState('Non renseigné');
  const [medicalHistory, setMedicalHistory] = useState('Non renseigné');
  const [currentMedication, setCurrentMedication] = useState('Non renseigné');
  const [chronicConditions, setChronicConditions] = useState('Non renseigné');

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  function validateDate(s: string): boolean {
    if (!s) return true; // optionnel
    const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(s);
    if (!match) return false;
    const y = parseInt(match[1], 10);
    const m = parseInt(match[2], 10);
    const d = parseInt(match[3], 10);
    if (y < 1900 || y > new Date().getFullYear()) return false;
    if (m < 1 || m > 12) return false;
    if (d < 1 || d > 31) return false;
    return true;
  }

  async function handleSubmit() {
    // Validation
    if (!firstName.trim() || !lastName.trim()) {
      setError('Le prénom et le nom sont obligatoires.');
      return;
    }
    if (dateOfBirth && !validateDate(dateOfBirth)) {
      setError('Date de naissance invalide (format attendu : AAAA-MM-JJ).');
      return;
    }
    if (phone && phone.replace(/[+\d\s-]/g, '').length > 0) {
      setError('Téléphone invalide (chiffres, espaces, +, - uniquement).');
      return;
    }

    setError('');
    setSubmitting(true);

    const payload = {
      first_name: firstName.trim(),
      last_name: lastName.trim(),
      date_of_birth: dateOfBirth || undefined,
      gender: gender || undefined,
      phone: phone.trim() || undefined,
      address: address.trim() || undefined,
      national_id: nationalId.trim() || undefined,
      insurance_number: insuranceNumber.trim() || undefined,
      emergency_contact_name: emergencyName.trim() || undefined,
      emergency_contact_phone: emergencyPhone.trim() || undefined,
      // Champs médicaux — toujours envoyés (jamais vides)
      blood_type: bloodType,
      allergies: allergies.trim() || 'Non renseigné',
      medical_history: medicalHistory.trim() || 'Non renseigné',
      current_medication: currentMedication.trim() || 'Non renseigné',
      chronic_conditions: chronicConditions.trim() || 'Non renseigné',
    };

    try {
      if (isOnline) {
        const resp = await createPatient(payload);
        Alert.alert(
          'Patient créé',
          `N° ${resp.data.patient_number}\nLe patient a été enregistré avec succès.`,
          [
            {
              text: 'Voir le dossier',
              onPress: () =>
                navigation.replace('PatientDetail', { patientId: resp.data.id }),
            },
            {
              text: 'Retour à la liste',
              style: 'cancel',
              onPress: () => navigation.navigate('MainTabs'),
            },
          ]
        );
      } else {
        // Offline : queue la mutation pour synchronisation ultérieure
        await enqueue('POST', '/patients', payload);
        Alert.alert(
          'Sauvegardé hors-ligne',
          'Le patient sera créé au retour de la connexion. Notez que le numéro patient sera généré à ce moment-là.',
          [
            {
              text: 'OK',
              onPress: () => navigation.navigate('MainTabs'),
            },
          ]
        );
      }
    } catch (e: any) {
      const status = e?.response?.status;
      let msg = e?.message || "Échec de la création du patient";
      if (status === 409) {
        msg = 'Un patient avec cet ID national ou ce numéro existe déjà.';
      } else if (status === 403) {
        msg = "Vous n'avez pas la permission de créer un patient.";
      } else if (status === 422) {
        msg = 'Données invalides : ' + (e?.response?.data?.detail?.[0]?.msg || 'vérifiez les champs');
      } else if (e?.response?.data?.detail) {
        msg = typeof e.response.data.detail === 'string'
          ? e.response.data.detail
          : JSON.stringify(e.response.data.detail);
      }
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        style={{ flex: 1 }}
        keyboardVerticalOffset={100}
      >
        <View style={styles.header}>
          <TouchableOpacity
            onPress={() => navigation.goBack()}
            style={styles.backBtn}
          >
            <Ionicons name="arrow-back" size={22} color="#0f766e" />
          </TouchableOpacity>
          <Text style={styles.title}>Nouveau patient</Text>
          <View style={{ width: 40 }} />
        </View>

        <ScrollView contentContainerStyle={{ padding: 16, paddingBottom: 100 }}>
          <View style={styles.infoBox}>
            <Ionicons name="information-circle" size={18} color="#0f766e" />
            <Text style={styles.infoText}>
              Le numéro patient (PAT-AAAAMMJJHHMMSS) et l'établissement seront
              attribués automatiquement.
            </Text>
          </View>

          {!isOnline && (
            <View style={styles.offlineBox}>
              <Ionicons name="cloud-offline" size={18} color="#f59e0b" />
              <Text style={styles.offlineText}>
                Mode hors-ligne — le patient sera synchronisé au retour du réseau.
              </Text>
            </View>
          )}

          <Text style={styles.sectionTitle}>Identité *</Text>
          <View style={styles.row}>
            <View style={{ flex: 1, marginRight: 8 }}>
              <Text style={styles.label}>Prénom *</Text>
              <TextInput
                style={styles.input}
                value={firstName}
                onChangeText={setFirstName}
                placeholder="Amadou"
                placeholderTextColor="#94a3b8"
                autoCapitalize="words"
              />
            </View>
            <View style={{ flex: 1 }}>
              <Text style={styles.label}>Nom *</Text>
              <TextInput
                style={styles.input}
                value={lastName}
                onChangeText={setLastName}
                placeholder="Diallo"
                placeholderTextColor="#94a3b8"
                autoCapitalize="words"
              />
            </View>
          </View>

          <View style={styles.row}>
            <View style={{ flex: 1, marginRight: 8 }}>
              <Text style={styles.label}>Date de naissance</Text>
              <TextInput
                style={styles.input}
                value={dateOfBirth}
                onChangeText={setDateOfBirth}
                placeholder="1985-05-15"
                placeholderTextColor="#94a3b8"
                keyboardType="numeric"
              />
            </View>
            <View style={{ flex: 1 }}>
              <Text style={styles.label}>Genre</Text>
              <View style={styles.genderRow}>
                {[
                  { val: 'M', label: '♂ M' },
                  { val: 'F', label: '♀ F' },
                  { val: 'O', label: '○ Autre' },
                ].map((g) => (
                  <TouchableOpacity
                    key={g.val}
                    style={[
                      styles.genderPill,
                      gender === g.val && styles.genderPillSelected,
                    ]}
                    onPress={() => setGender(g.val)}
                  >
                    <Text
                      style={[
                        styles.genderPillText,
                        gender === g.val && styles.genderPillTextSelected,
                      ]}
                    >
                      {g.label}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>
          </View>

          <Text style={styles.sectionTitle}>Coordonnées</Text>
          <Text style={styles.label}>Téléphone</Text>
          <TextInput
            style={styles.input}
            value={phone}
            onChangeText={setPhone}
            placeholder="+224 622 33 44 55"
            placeholderTextColor="#94a3b8"
            keyboardType="phone-pad"
          />

          <Text style={styles.label}>Adresse</Text>
          <TextInput
            style={[styles.input, { minHeight: 60 }]}
            value={address}
            onChangeText={setAddress}
            placeholder="Conakry, Guinée"
            placeholderTextColor="#94a3b8"
            multiline
          />

          <Text style={styles.sectionTitle}>Identifiants</Text>
          <Text style={styles.label}>N° ID national / CIN</Text>
          <TextInput
            style={styles.input}
            value={nationalId}
            onChangeText={setNationalId}
            placeholder="GN-123456789"
            placeholderTextColor="#94a3b8"
            autoCapitalize="characters"
          />

          <Text style={styles.label}>N° assurance maladie</Text>
          <TextInput
            style={styles.input}
            value={insuranceNumber}
            onChangeText={setInsuranceNumber}
            placeholder="ASS-001-2026"
            placeholderTextColor="#94a3b8"
          />

          <Text style={styles.sectionTitle}>Informations médicales</Text>
          <Text style={styles.sectionHint}>
            Les champs laissés à "Non renseigné" pourront être complétés ultérieurement
            depuis le dossier patient.
          </Text>

          <Text style={styles.label}>Groupe sanguin</Text>
          <View style={styles.bloodTypeRow}>
            {[
              'NON_RENSEIGNE',
              'A+', 'A-', 'B+', 'B-',
              'AB+', 'AB-', 'O+', 'O-',
            ].map((bt) => (
              <TouchableOpacity
                key={bt}
                style={[
                  styles.bloodPill,
                  bloodType === bt && styles.bloodPillSelected,
                ]}
                onPress={() => setBloodType(bt)}
              >
                <Text
                  style={[
                    styles.bloodPillText,
                    bloodType === bt && styles.bloodPillTextSelected,
                  ]}
                >
                  {bt === 'NON_RENSEIGNE' ? '?' : bt}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          <Text style={styles.label}>Allergies connues</Text>
          <TextInput
            style={[styles.input, { minHeight: 60 }]}
            value={allergies}
            onChangeText={setAllergies}
            placeholder="Pénicilline, arachide, iodé... ou 'Non renseigné'"
            placeholderTextColor="#94a3b8"
            multiline
          />

          <Text style={styles.label}>Antécédents médicaux</Text>
          <TextInput
            style={[styles.input, { minHeight: 60 }]}
            value={medicalHistory}
            onChangeText={setMedicalHistory}
            placeholder="Chirurgicaux, familiaux... ou 'Non renseigné'"
            placeholderTextColor="#94a3b8"
            multiline
          />

          <Text style={styles.label}>Traitement en cours</Text>
          <TextInput
            style={[styles.input, { minHeight: 60 }]}
            value={currentMedication}
            onChangeText={setCurrentMedication}
            placeholder="Médicaments, posologie... ou 'Non renseigné'"
            placeholderTextColor="#94a3b8"
            multiline
          />

          <Text style={styles.label}>Maladies chroniques</Text>
          <TextInput
            style={[styles.input, { minHeight: 60 }]}
            value={chronicConditions}
            onChangeText={setChronicConditions}
            placeholder="Diabète, HTA, asthme... ou 'Non renseigné'"
            placeholderTextColor="#94a3b8"
            multiline
          />

          <Text style={styles.sectionTitle}>Contact d'urgence</Text>
          <Text style={styles.label}>Nom du contact</Text>
          <TextInput
            style={styles.input}
            value={emergencyName}
            onChangeText={setEmergencyName}
            placeholder="Époux(se), parent, tuteur..."
            placeholderTextColor="#94a3b8"
            autoCapitalize="words"
          />

          <Text style={styles.label}>Téléphone du contact</Text>
          <TextInput
            style={styles.input}
            value={emergencyPhone}
            onChangeText={setEmergencyPhone}
            placeholder="+224 628 00 00 00"
            placeholderTextColor="#94a3b8"
            keyboardType="phone-pad"
          />

          {error && (
            <View style={styles.errorBox}>
              <Ionicons name="alert-circle" size={18} color="#dc2626" />
              <Text style={styles.errorText}>{error}</Text>
            </View>
          )}

          <TouchableOpacity
            style={[styles.submitBtn, submitting && styles.submitBtnDisabled]}
            onPress={handleSubmit}
            disabled={submitting}
          >
            {submitting ? (
              <ActivityIndicator color="white" size="small" />
            ) : (
              <>
                <Ionicons name="checkmark-circle" size={20} color="white" />
                <Text style={styles.submitText}>
                  {isOnline ? 'Créer le patient' : 'Enregistrer hors-ligne'}
                </Text>
              </>
            )}
          </TouchableOpacity>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f8fafc' },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#e2e8f0',
    backgroundColor: 'white',
  },
  backBtn: { padding: 4 },
  title: { fontSize: 18, fontWeight: '800', color: '#0f172a' },
  infoBox: {
    flexDirection: 'row',
    backgroundColor: '#f0fdfa',
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
    alignItems: 'flex-start',
  },
  infoText: {
    flex: 1,
    fontSize: 12,
    color: '#0f766e',
    marginLeft: 8,
  },
  offlineBox: {
    flexDirection: 'row',
    backgroundColor: '#fef3c7',
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
    alignItems: 'flex-start',
  },
  offlineText: {
    flex: 1,
    fontSize: 12,
    color: '#92400e',
    marginLeft: 8,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#475569',
    textTransform: 'uppercase',
    marginTop: 16,
    marginBottom: 8,
  },
  sectionHint: {
    fontSize: 11,
    color: '#94a3b8',
    marginBottom: 8,
    fontStyle: 'italic',
  },
  row: { flexDirection: 'row' },
  label: {
    fontSize: 12,
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
    padding: 12,
    fontSize: 15,
    color: '#0f172a',
  },
  genderRow: {
    flexDirection: 'row',
    gap: 6,
  },
  genderPill: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#e2e8f0',
    borderRadius: 8,
    padding: 10,
    alignItems: 'center',
    backgroundColor: 'white',
  },
  genderPillSelected: {
    backgroundColor: '#0f766e',
    borderColor: '#0f766e',
  },
  genderPillText: { color: '#475569', fontSize: 13 },
  genderPillTextSelected: { color: 'white', fontWeight: '700' },
  bloodTypeRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
  },
  bloodPill: {
    borderWidth: 1,
    borderColor: '#e2e8f0',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 8,
    minWidth: 44,
    alignItems: 'center',
    backgroundColor: 'white',
  },
  bloodPillSelected: {
    backgroundColor: '#dc2626',
    borderColor: '#dc2626',
  },
  bloodPillText: { color: '#475569', fontSize: 13, fontWeight: '600' },
  bloodPillTextSelected: { color: 'white', fontWeight: '800' },
  errorBox: {
    flexDirection: 'row',
    backgroundColor: '#fef2f2',
    borderWidth: 1,
    borderColor: '#fecaca',
    borderRadius: 8,
    padding: 12,
    marginTop: 16,
    alignItems: 'flex-start',
  },
  errorText: {
    flex: 1,
    color: '#dc2626',
    fontSize: 13,
    marginLeft: 8,
  },
  submitBtn: {
    flexDirection: 'row',
    backgroundColor: '#0f766e',
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 24,
    gap: 8,
  },
  submitBtnDisabled: { opacity: 0.6 },
  submitText: { color: 'white', fontSize: 16, fontWeight: '700' },
});
