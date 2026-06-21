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
 * Usage :
 *   <AuthProvider><App /></AuthProvider>
 *   const { user, login, logout, unlockWithBiometric } = useAuth();
 */
import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
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
  getProfile,
} from '../services/api';

const BIOMETRIC_ENABLED_KEY = 'guineecare_biometric_enabled';

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

  // Au démarrage : charger la session persistée + vérifier hardware biométrie
  useEffect(() => {
    (async () => {
      const saved = await loadSession();
      const compatible = await LocalAuthentication.hasHardwareAsync();
      const enrolled = await LocalAuthentication.isEnrolledAsync();
      const bioEnabled = (await SecureStore.getItemAsync(BIOMETRIC_ENABLED_KEY)) === 'true';

      setHasBiometricHardware(compatible && enrolled);
      setIsBiometricEnabled(bioEnabled);

      if (saved?.user) {
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
      const msg = e?.response?.data?.detail || e?.message || 'Échec de connexion';
      setState({
        user: null,
        session: null,
        loading: false,
        isLocked: false,
        error: typeof msg === 'string' ? msg : 'Identifiants invalides',
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
