/**
 * Wrapper d'icônes — utilise @expo/vector-icons (Ionicons) qui est bundlé avec Expo.
 *
 * Ce wrapper isole le reste du code de la lib d'icônes — si on veut plus tard
 * migrer vers lucide-react-native ou une autre lib, seul ce fichier change.
 */
import React from 'react';
import { Ionicons } from '@expo/vector-icons';

export { Ionicons };

export type IconName = keyof typeof Ionicons.glyphMap;

export function Icon({
  name,
  size = 24,
  color = '#0f172a',
}: {
  name: IconName;
  size?: number;
  color?: string;
}) {
  return <Ionicons name={name} size={size} color={color} />;
}
