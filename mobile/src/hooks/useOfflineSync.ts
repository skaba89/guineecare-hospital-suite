/**
 * Hook useOfflineSync — file d'attente des mutations offline.
 *
 * Fonctionnalités :
 * - Détecte l'état réseau via @react-native-community/netinfo
 * - Quand offline, les mutations (POST/PATCH/DELETE) sont stockées dans AsyncStorage
 * - Quand online, la queue est replayée dans l'ordre (FIFO)
 * - Expose `isOnline`, `pendingCount`, `enqueue()`, `forceSync()`
 *
 * Usage :
 *   const { isOnline, pendingCount, enqueue, forceSync } = useOfflineSync();
 *
 *   // Dans un handler de création de constante :
 *   if (!isOnline) {
 *     await enqueue('POST', '/clinical/measurements', { patient_id, type, value });
 *     Alert.alert('Sauvegardé hors-ligne', 'Sera synchronisé au retour du réseau.');
 *   } else {
 *     await createMeasurement(payload);
 *   }
 */
import { useCallback, useEffect, useState } from 'react';
import NetInfo from '@react-native-community/netinfo';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { api } from '../services/api';
import { PendingMutation } from '../types';

const QUEUE_KEY = 'guineecare_offline_queue';

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

export function useOfflineSync() {
  const [isOnline, setIsOnline] = useState(true);
  const [pendingCount, setPendingCount] = useState(0);
  const [syncing, setSyncing] = useState(false);

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
    // Charger la queue initiale
    (async () => {
      const q = await loadQueue();
      setPendingCount(q.length);
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
   * Rejoue toutes les mutations en attente. Retourne le nombre de succès.
   */
  const forceSync = useCallback(async (): Promise<{ succeeded: number; failed: number }> => {
    const queue = await loadQueue();
    if (queue.length === 0) {
      setPendingCount(0);
      return { succeeded: 0, failed: 0 };
    }

    setSyncing(true);
    const stillPending: PendingMutation[] = [];
    let succeeded = 0;
    let failed = 0;

    for (const mutation of queue) {
      try {
        const config: any = { method: mutation.method.toLowerCase(), url: mutation.path };
        if (mutation.body) {
          config.data = mutation.body;
        }
        await api.request(config);
        succeeded++;
      } catch (e: any) {
        // 4xx = erreur client définitive → on abandonne
        // 5xx = erreur serveur transitoire → on retente plus tard
        const status = e?.response?.status;
        if (status && status >= 400 && status < 500) {
          // Erreur client : abandonner cette mutation
          failed++;
        } else {
          // Erreur réseau ou 5xx : garder dans la queue
          mutation.retry_count += 1;
          if (mutation.retry_count < 5) {
            stillPending.push(mutation);
          } else {
            // Trop de retries : abandonner
            failed++;
          }
        }
      }
    }

    await saveQueue(stillPending);
    setPendingCount(stillPending.length);
    setSyncing(false);

    return { succeeded, failed };
  }, []);

  /**
   * Vide la queue (utilisable dans l'écran Profile comme "purger les données offline").
   */
  const clearQueue = useCallback(async (): Promise<void> => {
    await saveQueue([]);
    setPendingCount(0);
  }, []);

  return {
    isOnline,
    pendingCount,
    syncing,
    enqueue,
    forceSync,
    clearQueue,
  };
}
