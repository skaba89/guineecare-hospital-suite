/**
 * ErrorBoundary — capturer les erreurs de rendu React.
 *
 * v2.7.0 — Phase 7 : sans ErrorBoundary, une erreur de rendu dans n'importe
 * quel écran fait crasher toute l'app. Ce composant affiche un fallback
 * avec un bouton "Recharger" au lieu d'un écran blanc.
 *
 * Usage : wrapper autour de AppNavigator dans App.tsx.
 */
import React, { Component, ErrorInfo, ReactNode } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ScrollView } from 'react-native';

type Props = { children: ReactNode };
type State = { hasError: boolean; error: Error | null };

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught:', error, errorInfo);
  }

  handleReload = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <View style={styles.container}>
          <ScrollView contentContainerStyle={styles.scroll}>
            <Text style={styles.title}>Oups, une erreur est survenue</Text>
            <Text style={styles.message}>
              L'application a rencontré un problème inattendu. Vous pouvez
              recharger l'écran pour réessayer.
            </Text>
            {__DEV__ && this.state.error && (
              <Text style={styles.errorDetail}>
                {this.state.error.toString()}
              </Text>
            )}
            <TouchableOpacity style={styles.button} onPress={this.handleReload}>
              <Text style={styles.buttonText}>Recharger</Text>
            </TouchableOpacity>
          </ScrollView>
        </View>
      );
    }

    return this.props.children;
  }
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8fafc',
  },
  scroll: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
  },
  title: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1e293b',
    marginBottom: 12,
    textAlign: 'center',
  },
  message: {
    fontSize: 14,
    color: '#64748b',
    textAlign: 'center',
    marginBottom: 24,
    lineHeight: 20,
  },
  errorDetail: {
    fontSize: 11,
    color: '#dc2626',
    fontFamily: 'monospace',
    marginBottom: 16,
    padding: 8,
    backgroundColor: '#fef2f2',
    borderRadius: 4,
  },
  button: {
    backgroundColor: '#0f6b3e',
    paddingVertical: 12,
    paddingHorizontal: 32,
    borderRadius: 8,
  },
  buttonText: {
    color: '#fff',
    fontSize: 15,
    fontWeight: '600',
  },
});
