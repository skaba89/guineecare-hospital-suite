/**
 * Hook usePushNotifications — enregistre le device auprès du backend.
 *
 * Fonctionnalités :
 * - Demande la permission notifications
 * - Récupère l'Expo Push Token (via Notifications.getExpoPushTokenAsync)
 * - L'enregistre côté backend via registerPushToken()
 * - Écoute les notifications reçues en foreground et les affiche via Alert
 * - Écoute les taps sur notifications pour navigation
 *
 * Usage :
 *   // Dans App.tsx, après AuthProvider :
 *   function AppInner() {
 *     usePushNotifications();
 *     return <AppNavigator />;
 *   }
 *
 * Note : pour les notifications en background, le handler natif est configuré
 * dans app.json (expo-notifications plugin). En v1.7 on gère seulement le
 * foreground + l'enregistrement du token.
 */
import { useEffect } from 'react';
import * as Notifications from 'expo-notifications';
import { Platform } from 'react-native';
import { registerPushToken } from '../services/api';
import { useAuth } from '../context/AuthContext';

// Configurer le handler foreground (une seule fois au démarrage)
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
    shouldShowBanner: true,
    shouldShowList: true,
  }),
});

export function usePushNotifications() {
  const { user } = useAuth();

  useEffect(() => {
    if (!user) return;

    let notificationListener: Notifications.Subscription | null = null;
    let responseListener: Notifications.Subscription | null = null;

    (async () => {
      try {
        // 1. Demander la permission (iOS + Android 13+)
        const { status: existingStatus } = await Notifications.getPermissionsAsync();
        let finalStatus = existingStatus;
        if (existingStatus !== 'granted') {
          const { status } = await Notifications.requestPermissionsAsync();
          finalStatus = status;
        }
        if (finalStatus !== 'granted') {
          console.debug('Push notifications permission not granted');
          return;
        }

        // 2. Configurer le channel Android (requis pour Android 8+)
        if (Platform.OS === 'android') {
          await Notifications.setNotificationChannelAsync('default', {
            name: 'GuinéeCare Notifications',
            importance: Notifications.AndroidImportance.HIGH,
            vibrationPattern: [0, 250, 250, 250],
            lightColor: '#0f766e',
          });
          // Channel séparé pour les alertes urgentes (labo critique, etc.)
          await Notifications.setNotificationChannelAsync('urgent', {
            name: 'Alertes urgentes',
            importance: Notifications.AndroidImportance.MAX,
            vibrationPattern: [0, 500, 250, 500],
            lightColor: '#dc2626',
          });
        }

        // 3. Récupérer l'Expo Push Token
        const tokenData = await Notifications.getExpoPushTokenAsync({
          projectId: 'guineecare-mobile', // doit matcher app.extra.eas.projectId
        });
        const token = tokenData.data;

        // 4. Enregistrer auprès du backend
        await registerPushToken(token);
        console.debug('Push token registered:', token);
      } catch (e) {
        console.warn('Push notifications setup failed:', e);
      }

      // 5. Écouter les notifications reçues en foreground
      notificationListener = Notifications.addNotificationReceivedListener((notification) => {
        const { title, body } = notification.request.content;
        console.debug('Notification received in foreground:', title, body);
        // Pas d'alerte invasive — l'utilisateur verra la bannière système.
        // Les notifications critiques (urgent) pourraient déclencher une Alert
        // si on veut forcer l'attention, mais c'est intrusif en prod.
      });

      // 6. Écouter les taps sur notifications
      responseListener = Notifications.addNotificationResponseReceivedListener((response) => {
        const data = response.notification.request.content.data;
        console.debug('Notification tapped:', data);
        // TODO: navigation vers l'écran pertinent (PatientDetail, LabOrder, etc.)
        // en fonction de data.resource_type + data.resource_id
      });
    })();

    return () => {
      if (notificationListener) {
        Notifications.removeNotificationSubscription(notificationListener);
      }
      if (responseListener) {
        Notifications.removeNotificationSubscription(responseListener);
      }
    };
  }, [user]);
}
