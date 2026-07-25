/**
 * Écran QRScan — scan d'un QR code patient au pied du lit.
 *
 * Le QR code patient contient soit :
 * - l'ID interne du patient (UUID 36 chars), soit
 * - le patient_number (format PAT-YYYYMMDDHHMMSS)
 *
 * Au scan valide → navigation directe vers PatientDetailScreen.
 * En cas d'erreur (patient introuvable) → alerte + reset du scanner.
 *
 * Permission CAMERA requise — gérée par expo-barcode-scanner (prompt automatique).
 */
import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Alert,
  Dimensions,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { BarCodeScanner } from 'expo-barcode-scanner';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { getPatientByQr } from '../services/api';
import { Ionicons } from '../components/Icons';

type RootStackParamList = {
  PatientDetail: { patientId: string };
};

export function QRScanScreen() {
  const navigation = useNavigation<NativeStackNavigationProp<RootStackParamList>>();
  const [hasPermission, setHasPermission] = useState<boolean | null>(null);
  const [scanned, setScanned] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    (async () => {
      const { status } = await BarCodeScanner.requestPermissionsAsync();
      setHasPermission(status === 'granted');
    })();
  }, []);

  async function handleBarCodeScanned({ data }: { data: string }) {
    if (scanned || loading) return;
    setScanned(true);
    setLoading(true);
    try {
      const resp = await getPatientByQr(data.trim());
      if (resp.data?.id) {
        navigation.navigate('PatientDetail', { patientId: resp.data.id });
      } else {
        Alert.alert('Patient introuvable', `Aucun patient pour : ${data}`);
        setScanned(false);
      }
    } catch (e: any) {
      const status = e?.response?.status;
      if (status === 404) {
        Alert.alert('QR code inconnu', `Aucun patient correspondant à : ${data}`);
      } else {
        Alert.alert('Erreur', e?.message || 'Échec de la recherche');
      }
      setScanned(false);
    } finally {
      setLoading(false);
    }
  }

  if (hasPermission === null) {
    return (
      <SafeAreaView style={styles.center}>
        <Text>Demande de permission caméra…</Text>
      </SafeAreaView>
    );
  }

  if (hasPermission === false) {
    return (
      <SafeAreaView style={styles.center}>
        <Ionicons name="camera-outline" size={64} color="#cbd5e1" />
        <Text style={styles.permissionTitle}>Accès caméra refusé</Text>
        <Text style={styles.permissionText}>
          Pour scanner un QR code patient, autorisez l'accès caméra dans les
          réglages de l'app.
        </Text>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <View style={styles.header}>
        <Text style={styles.title}>Scanner un patient</Text>
        <Text style={styles.subtitle}>
          Placez le QR code du patient dans le cadre
        </Text>
      </View>

      <View style={styles.scannerWrap}>
        <BarCodeScanner
          onBarCodeScanned={scanned ? undefined : handleBarCodeScanned}
          style={StyleSheet.absoluteFillObject}
          barCodeTypes={['qr']}
        />
        {/* Cadre de visée */}
        <View style={styles.targetFrame} pointerEvents="none">
          <View style={[styles.corner, styles.cornerTL]} />
          <View style={[styles.corner, styles.cornerTR]} />
          <View style={[styles.corner, styles.cornerBL]} />
          <View style={[styles.corner, styles.cornerBR]} />
        </View>

        {loading && (
          <View style={styles.loadingOverlay}>
            <Text style={styles.loadingText}>Recherche du patient…</Text>
          </View>
        )}
      </View>

      <View style={styles.footer}>
        {scanned && !loading && (
          <TouchableOpacity
            style={styles.retryBtn}
            onPress={() => setScanned(false)}
          >
            <Ionicons name="refresh" size={20} color="white" />
            <Text style={styles.retryText}>Scanner à nouveau</Text>
          </TouchableOpacity>
        )}
        <Text style={styles.helpText}>
          Le QR code patient se trouve sur le bracelet d'identification.
        </Text>
      </View>
    </SafeAreaView>
  );
}

const WINDOW_WIDTH = Dimensions.get('window').width;
const FRAME_SIZE = WINDOW_WIDTH * 0.7;

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#000' },
  header: { padding: 20, alignItems: 'center' },
  title: { color: 'white', fontSize: 20, fontWeight: '800' },
  subtitle: { color: '#cbd5e1', fontSize: 13, marginTop: 4 },
  scannerWrap: {
    flex: 1,
    margin: 24,
    borderRadius: 16,
    overflow: 'hidden',
    position: 'relative',
  },
  targetFrame: {
    position: 'absolute',
    top: '50%',
    left: '50%',
    width: FRAME_SIZE,
    height: FRAME_SIZE,
    marginTop: -FRAME_SIZE / 2,
    marginLeft: -FRAME_SIZE / 2,
  },
  corner: {
    position: 'absolute',
    width: 30,
    height: 30,
    borderColor: '#0f766e',
    borderWidth: 4,
  },
  cornerTL: { top: 0, left: 0, borderRightWidth: 0, borderBottomWidth: 0, borderTopLeftRadius: 8 },
  cornerTR: { top: 0, right: 0, borderLeftWidth: 0, borderBottomWidth: 0, borderTopRightRadius: 8 },
  cornerBL: { bottom: 0, left: 0, borderRightWidth: 0, borderTopWidth: 0, borderBottomLeftRadius: 8 },
  cornerBR: { bottom: 0, right: 0, borderLeftWidth: 0, borderTopWidth: 0, borderBottomRightRadius: 8 },
  loadingOverlay: {
    position: 'absolute',
    bottom: 16,
    left: 16,
    right: 16,
    backgroundColor: 'rgba(0,0,0,0.8)',
    borderRadius: 8,
    padding: 12,
    alignItems: 'center',
  },
  loadingText: { color: 'white', fontSize: 13 },
  footer: { padding: 20, alignItems: 'center' },
  retryBtn: {
    flexDirection: 'row',
    backgroundColor: '#0f766e',
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: 'center',
    marginBottom: 12,
  },
  retryText: { color: 'white', fontWeight: '600', marginLeft: 8 },
  helpText: { color: '#94a3b8', fontSize: 12, textAlign: 'center' },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 32 },
  permissionTitle: { fontSize: 18, fontWeight: '700', color: '#0f172a', marginTop: 16 },
  permissionText: { color: '#64748b', fontSize: 13, textAlign: 'center', marginTop: 8 },
});
