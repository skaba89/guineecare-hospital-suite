/**
 * Hook useOfflineSync — file d'attente des mutations offline.
 *
 * Fonctionnalités :
 * - Détecte l'état réseau via @react-native-community/netinfo
 * - Quand offline, les mutations (POST/PATCH/DELETE) sont stockées dans AsyncStorage
 * - Quand online, la queue est replayée dans l'ordre (FIFO)
 * - Expose `isOnline`, `pendingCount`, `enqueue()`, `forceSync()`, `clearQueue()`
 *   + `conflicts` (mutations en conflit 409)
 *
 * v2.7.0 — Phase 7 améliorations :
 * - Gestion des conflits 409 : les mutations en conflit sont déplacées vers
 *   une queue `conflicts` séparée (P0-2) au lieu d'être silencieusement drop
 * - Backoff exponentiel entre retries : 2s, 4s, 8s, 16s, 30s (P1-2)
 * - Verrou `syncing` pour éviter 2 syncs parallèles (race condition)
 * - `lastSyncResult` pour afficher le résultat de la dernière synchro
 *
 * Usage :
 *   const { isOnline, pendingCount, conflicts, enqueue, forceSync, clearQueue } = useOfflineSync();
 *
 *   // Dans un handler de création de constante :
 *   if (!isOnline) {
 *     await enqueue('POST', '/clinical/measurements', { patient_id, type, value });
 *     Alert.alert('Sauvegardé hors-ligne', 'Sera synchronisé au retour du réseau.');
 *   } else {
 *     await createMeasurement(payload);
 *   }
 */
import { useCallback, useEffect, useState, useRef } from 'react';
import NetInfo from '@react-native-community/netinfo';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { api } from '../services/api';
import { PendingMutation } from '../types';

const QUEUE_KEY = 'guineecare_offline_queue';
const CONFLICTS_KEY = 'guineecare_offline_conflicts';

function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

async function loadQueue(): Promise<PendingMutation[]> {
  try {
    const raw = await AsyncStorage.getItem(QUEUE_KEY);
    if (!raw) return [];
    return JSON.parse(raw) as PendingMutation[];
  } catch {
    return [];
  }
}

async function saveQueue(queue: PendingMutation[]): Promise<void> {
  await AsyncStorage.setItem(QUEUE_KEY, JSON.stringify(queue));
}

async function loadConflicts(): Promise<PendingMutation[]> {
  try {
    const raw = await AsyncStorage.getItem(CONFLICTS_KEY);
    if (!raw) return [];
    return JSON.parse(raw) as PendingMutation[];
  } catch {
    return [];
  }
}

async function saveConflicts(conflicts: PendingMutation[]): Promise<void> {
  await AsyncStorage.setItem(CONFLICTS_KEY, JSON.stringify(conflicts));
}

// v2.7.0 — Phase 7 : backoff exponentiel (2s, 4s, 8s, 16s, 30s max)
function backoffDelay(retryCount: number): number {
  return Math.min(30000, 2000 * Math.pow(2, retryCount));
}

export type SyncResult = {
  succeeded: number;
  failed: number;
  conflicts: number;
};

export function useOfflineSync() {
  const [isOnline, setIsOnline] = useState(true);
  const [pendingCount, setPendingCount] = useState(0);
  const [conflictsCount, setConflictsCount] = useState(0);
  const [syncing, setSyncing] = useState(false);
  const [lastSyncResult, setLastSyncResult] = useState<SyncResult | null>(null);

  // v2.7.0 — Phase 7 : ref pour éviter 2 syncs parallèles (race condition)
  const syncingRef = useRef(false);

  // Souscrire à l'état réseau
  useEffect(() => {
    const unsub = NetInfo.addEventListener((state) => {
      const online = Boolean(state.isConnected && state.isInternetReachable);
      setIsOnline(online);
      if (online) {
        // Tenter de synchroniser dès qu'on repasse online
        forceSync();
      }
    });
    // Charger la queue initiale + conflicts
    (async () => {
      const q = await loadQueue();
      const c = await loadConflicts();
      setPendingCount(q.length);
      setConflictsCount(c.length);
    })();
    return () => unsub();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  /**
   * Ajoute une mutation à la queue (utilisée quand offline).
   */
  const enqueue = useCallback(
    async (
      method: 'POST' | 'PATCH' | 'DELETE',
      path: string,
      body?: any
    ): Promise<PendingMutation> => {
      const mutation: PendingMutation = {
        id: generateId(),
        method,
        path,
        body,
        created_at: new Date().toISOString(),
        retry_count: 0,
      };
      const q = await loadQueue();
      q.push(mutation);
      await saveQueue(q);
      setPendingCount(q.length);
      return mutation;
    },
    []
  );

  /**
   * Rejoue toutes les mutations en attente. Retourne le nombre de succès/échecs/conflits.
   *
   * v2.7.0 — Phase 7 :
   * - 409 Conflict → mutation déplacée vers `conflicts` (P0-2)
   * - 5xx/réseau → backoff exponentiel avant retry suivant (P1-2)
   * - Verrou syncingRef pour éviter 2 syncs parallèles
   */
  const forceSync = useCallback(async (): Promise<SyncResult> => {
    // v2.7.0 — Phase 7 : verrou anti-race
    if (syncingRef.current) {
      return lastSyncResult || { succeeded: 0, failed: 0, conflicts: 0 };
    }
    syncingRef.current = true;

    const queue = await loadQueue();
    if (queue.length === 0) {
      setPendingCount(0);
      syncingRef.current = false;
      const result = { succeeded: 0, failed: 0, conflicts: 0 };
      setLastSyncResult(result);
      return result;
    }

    setSyncing(true);
    const stillPending: PendingMutation[] = [];
    const newConflicts: PendingMutation[] = [];
    let succeeded = 0;
    let failed = 0;
    let conflictsCount = 0;

    for (const mutation of queue) {
      try {
        const config: any = { method: mutation.method.toLowerCase(), url: mutation.path };
        if (mutation.body) {
          config.data = mutation.body;
        }
        await api.request(config);
        succeeded++;
      } catch (e: any) {
        const status = e?.response?.status;

        if (status === 409) {
          // v2.7.0 — Phase 7 : conflit → déplacer vers conflicts (P0-2)
          // Au lieu de dropper silencieusement, on conserve pour résolution manuelle
          mutation.retry_count += 1;
          newConflicts.push(mutation);
          conflictsCount++;
        } else if (status && status >= 400 && status < 500 && status !== 409) {
          // 4xx (sauf 409) = erreur client définitive → abandonner
          failed++;
        } else {
          // 5xx ou erreur réseau → garder dans la queue avec backoff
          mutation.retry_count += 1;
          if (mutation.retry_count < 5) {
            // v2.7.0 — Phase 7 : backoff exponentiel entre retries (P1-2)
            const delay = backoffDelay(mutation.retry_count - 1);
            await new Promise(resolve => setTimeout(resolve, delay));
            stillPending.push(mutation);
          } else {
            // Trop de retries : abandonner
            failed++;
          }
        }
      }
    }

    // Sauvegarder la queue restante + nouveaux conflits
    await saveQueue(stillPending);
    const existingConflicts = await loadConflicts();
    await saveConflicts([...existingConflicts, ...newConflicts]);

    setPendingCount(stillPending.length);
    setConflictsCount(existingConflicts.length + newConflicts.length);
    setSyncing(false);
    syncingRef.current = false;

    const result: SyncResult = { succeeded, failed, conflicts: conflictsCount };
    setLastSyncResult(result);
    return result;
  }, [lastSyncResult]);

  /**
   * Vide la queue (utilisable dans l'écran Profile comme "purger les données offline").
   */
  const clearQueue = useCallback(async (): Promise<void> => {
    await saveQueue([]);
    setPendingCount(0);
  }, []);

  /**
   * v2.7.0 — Phase 7 : vide la queue des conflits (après résolution manuelle).
   */
  const clearConflicts = useCallback(async (): Promise<void> => {
    await saveConflicts([]);
    setConflictsCount(0);
  }, []);

  /**
   * v2.7.0 — Phase 7 : récupère la liste des conflits pour résolution UI.
   */
  const getConflicts = useCallback(async (): Promise<PendingMutation[]> => {
    return await loadConflicts();
  }, []);

  return {
    isOnline,
    pendingCount,
    conflictsCount,
    syncing,
    lastSyncResult,
    enqueue,
    forceSync,
    clearQueue,
    clearConflicts,
    getConflicts,
  };
}
