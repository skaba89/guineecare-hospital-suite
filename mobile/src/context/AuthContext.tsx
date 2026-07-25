/**
 * AuthContext — état d'authentification global de l'app mobile.
 *
 * Fonctionnalités :
 * - Login email/password via API
 * - Logout avec révocation côté serveur
 * - Persistance de la session via expo-secure-store
 * - Authentification biométrique (empreinte/Face ID) via expo-local-authentication
 *   Au démarrage, si une session existe, on demande l'auth biométrique pour
 *   déverrouiller l'app (sauf si l'utilisateur a désactivé cette option).
 *
 * v2.7.0 — Phase 7 améliorations :
 * - Messages d'erreur FR compréhensibles (plus de "Network Error" brut)
 * - Re-verrouillage automatique sur app background→foreground (P0-8)
 * - Vérification expiry token JWT au démarrage (P1-1)
 * - Callback onSessionLost pour synchroniser React state quand api.ts
 *   invalide la session (refresh failure) (P0-5)
 *
 * Usage :
 *   <AuthProvider><App /></AuthProvider>
 *   const { user, login, logout, unlockWithBiometric } = useAuth();
 */
import React, { createContext, useContext, useEffect, useState, useCallback, useRef } from 'react';
import { AppState, AppStateStatus } from 'react-native';
import * as LocalAuthentication from 'expo-local-authentication';
import * as SecureStore from 'expo-secure-store';
import {
  AuthSession,
  User,
} from '../types';
import {
  login as apiLogin,
  logout as apiLogout,
  loadSession,
  clearSession,
  setOnSessionLost,
} from '../services/api';

const BIOMETRIC_ENABLED_KEY = 'guineecare_biometric_enabled';

// v2.7.0 — Phase 7 : mappe les erreurs axios/HTTP en messages FR compréhensibles
function mapLoginError(e: any): string {
  // Erreur réseau (pas de connexion serveur)
  if (e?.code === 'ERR_NETWORK' || e?.message === 'Network Error') {
    return 'Connexion impossible. Vérifiez votre réseau Wi-Fi ou mobile.';
  }
  // Timeout
  if (e?.code === 'ECONNABORTED' || e?.message?.includes('timeout')) {
    return 'Délai de connexion dépassé. Réessayez dans un instant.';
  }
  // Erreur HTTP avec détail serveur
  const status = e?.response?.status;
  const detail = e?.response?.data?.detail;
  if (status === 401) {
    return typeof detail === 'string' ? detail : 'Identifiants invalides.';
  }
  if (status === 403) {
    return 'Compte désactivé. Contactez votre administrateur.';
  }
  if (status === 423) {
    return 'Compte verrouillé après plusieurs échecs. Réessayez dans 15 minutes.';
  }
  if (status === 429) {
    return 'Trop de tentatives. Patientez 1 minute avant de réessayer.';
  }
  if (status && status >= 500) {
    return 'Serveur indisponible. Réessayez dans un instant.';
  }
  // Fallback
  return typeof detail === 'string' ? detail : (e?.message || 'Échec de connexion');
}

// v2.7.0 — Phase 7 : décode le JWT pour vérifier l'expiry
function isTokenExpired(token: string | undefined): boolean {
  if (!token) return true;
  try {
    const parts = token.split('.');
    if (parts.length !== 3) return true;
    // Decode payload (base64url)
    const payload = parts[1].replace(/-/g, '+').replace(/_/g, '/');
    const json = JSON.parse(atob(payload));
    if (!json.exp) return false;
    // exp est en secondes unix
    const now = Math.floor(Date.now() / 1000);
    return now >= json.exp;
  } catch {
    return true; // token malformé → considéré expiré
  }
}

// atob polyfill pour React Native (pas de atob natif)
function atob(input: string): string {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=';
  let output = '';
  let i = 0;
  const str = input.replace(/[^A-Za-z0-9+/=]/g, '');
  while (i < str.length) {
    const enc1 = chars.indexOf(str.charAt(i++));
    const enc2 = chars.indexOf(str.charAt(i++));
    const enc3 = chars.indexOf(str.charAt(i++));
    const enc4 = chars.indexOf(str.charAt(i++));
    const chr1 = (enc1 << 2) | (enc2 >> 4);
    const chr2 = ((enc2 & 15) << 4) | (enc3 >> 2);
    const chr3 = ((enc3 & 3) << 6) | enc4;
    output += String.fromCharCode(chr1);
    if (enc3 !== 64) output += String.fromCharCode(chr2);
    if (enc4 !== 64) output += String.fromCharCode(chr3);
  }
  return output;
}

type AuthState = {
  user: User | null;
  session: AuthSession | null;
  loading: boolean;
  isLocked: boolean; // session existante mais biométrie non validée
  error: string | null;
};

type AuthContextValue = AuthState & {
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  unlockWithBiometric: () => Promise<boolean>;
  enableBiometric: () => Promise<void>;
  disableBiometric: () => Promise<void>;
  isBiometricEnabled: boolean;
  hasBiometricHardware: boolean;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AuthState>({
    user: null,
    session: null,
    loading: true,
    isLocked: false,
    error: null,
  });
  const [isBiometricEnabled, setIsBiometricEnabled] = useState(false);
  const [hasBiometricHardware, setHasBiometricHardware] = useState(false);

  // v2.7.0 — Phase 7 : ref pour vérifier la biométrie dans AppState listener
  const bioEnabledRef = useRef(false);
  bioEnabledRef.current = isBiometricEnabled;

  // v2.7.0 — Phase 7 : callback appelé par api.ts quand la session est perdue
  // (refresh token invalide). Permet de synchroniser React state.
  const handleSessionLost = useCallback(() => {
    setState({
      user: null,
      session: null,
      loading: false,
      isLocked: false,
      error: 'Session expirée. Veuillez vous reconnecter.',
    });
  }, []);

  // Enregistrer le callback au montage
  useEffect(() => {
    setOnSessionLost(handleSessionLost);
    return () => setOnSessionLost(null);
  }, [handleSessionLost]);

  // Au démarrage : charger la session persistée + vérifier hardware biométrie
  useEffect(() => {
    (async () => {
      const saved = await loadSession();
      const compatible = await LocalAuthentication.hasHardwareAsync();
      const enrolled = await LocalAuthentication.isEnrolledAsync();
      const bioEnabled = (await SecureStore.getItemAsync(BIOMETRIC_ENABLED_KEY)) === 'true';

      setHasBiometricHardware(compatible && enrolled);
      setIsBiometricEnabled(bioEnabled);

      // v2.7.0 — Phase 7 : vérifier expiry du token avant de restaurer
      if (saved?.user && saved?.access_token) {
        if (isTokenExpired(saved.access_token)) {
          // Token expiré — ne pas restaurer, l'utilisateur doit se reconnecter
          // (le refresh token pourrait encore être valide mais on préfère
          // forcer le login pour éviter une boucle de refresh en arrière-plan)
          await clearSession();
          setState({
            user: null,
            session: null,
            loading: false,
            isLocked: false,
            error: 'Session expirée. Veuillez vous reconnecter.',
          });
          return;
        }
        // Si biométrie activée → on garde la session mais verrouille l'app
        setState({
          user: saved.user,
          session: saved,
          loading: false,
          isLocked: bioEnabled,
          error: null,
        });
      } else {
        setState({
          user: null,
          session: null,
          loading: false,
          isLocked: false,
          error: null,
        });
      }
    })();
  }, []);

  // v2.7.0 — Phase 7 : re-verrouillage sur app background→foreground (P0-8)
  useEffect(() => {
    const subscription = AppState.addEventListener('change', (nextState: AppStateStatus) => {
      if (nextState === 'active') {
        // L'app revient au premier plan — si biométrie activée et utilisateur
        // connecté, re-verrouiller
        if (bioEnabledRef.current && state.user) {
          setState((s) => ({ ...s, isLocked: true }));
        }
      }
    });
    return () => subscription.remove();
  }, [state.user]);

  const login = useCallback(async (email: string, password: string) => {
    setState((s) => ({ ...s, loading: true, error: null }));
    try {
      const session = await apiLogin(email, password);
      setState({
        user: session.user,
        session,
        loading: false,
        isLocked: false,
        error: null,
      });
    } catch (e: any) {
      // v2.7.0 — Phase 7 : message d'erreur FR compréhensible
      const msg = mapLoginError(e);
      setState({
        user: null,
        session: null,
        loading: false,
        isLocked: false,
        error: msg,
      });
      throw e;
    }
  }, []);

  const logout = useCallback(async () => {
    await apiLogout();
    setState({
      user: null,
      session: null,
      loading: false,
      isLocked: false,
      error: null,
    });
  }, []);

  const unlockWithBiometric = useCallback(async (): Promise<boolean> => {
    if (!hasBiometricHardware) return false;
    try {
      const result = await LocalAuthentication.authenticateAsync({
        promptMessage: 'Déverrouillez GuinéeCare',
        fallbackLabel: 'Utiliser le code',
        cancelLabel: 'Annuler',
        disableDeviceFallback: false,
      });
      if (result.success) {
        setState((s) => ({ ...s, isLocked: false }));
        return true;
      }
      return false;
    } catch (e) {
      console.warn('Biometric auth failed:', e);
      return false;
    }
  }, [hasBiometricHardware]);

  const enableBiometric = useCallback(async () => {
    if (!hasBiometricHardware) return;
    const result = await LocalAuthentication.authenticateAsync({
      promptMessage: 'Activez le déverrouillage biométrique',
      cancelLabel: 'Annuler',
    });
    if (result.success) {
      await SecureStore.setItemAsync(BIOMETRIC_ENABLED_KEY, 'true');
      setIsBiometricEnabled(true);
    }
  }, [hasBiometricHardware]);

  const disableBiometric = useCallback(async () => {
    await SecureStore.deleteItemAsync(BIOMETRIC_ENABLED_KEY);
    setIsBiometricEnabled(false);
  }, []);

  const value: AuthContextValue = {
    ...state,
    login,
    logout,
    unlockWithBiometric,
    enableBiometric,
    disableBiometric,
    isBiometricEnabled,
    hasBiometricHardware,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within <AuthProvider>');
  return ctx;
}
