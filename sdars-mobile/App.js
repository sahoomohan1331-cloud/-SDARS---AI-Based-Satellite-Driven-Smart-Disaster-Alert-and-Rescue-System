import React, { useState, useRef, useEffect, useCallback } from 'react';
import { View, Text, StyleSheet, StatusBar, Platform, TouchableOpacity, ActivityIndicator, LogBox } from 'react-native';
import { WebView } from 'react-native-webview';
import * as Location from 'expo-location';

// Suppress non-critical development warnings and Expo CLI disconnect overlays
LogBox.ignoreLogs([
  'Cannot connect to Expo CLI',
  'Failed to download the latest version of React Native DevTools',
]);
LogBox.ignoreAllLogs(true);

const SERVER_URL = 'http://192.168.0.137:8000/mobile_app.html';

export default function App() {
  const webViewRef = useRef(null);
  const [hasError, setHasError] = useState(false);
  const [errorDetails, setErrorDetails] = useState('');
  const [key, setKey] = useState(0);

  const lastCoordsRef = useRef(null);

  // Native Device GPS via expo-location
  const fetchAndInjectLocation = useCallback(async () => {
    try {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') {
        console.warn('[SDARS Native] Location permission not granted by user');
        webViewRef.current?.injectJavaScript(`
          if (typeof window.onNativeLocationPermissionDenied === 'function') {
            window.onNativeLocationPermissionDenied();
          }
        `);
        return;
      }

      // Step 1: Send last known position immediately for instant zero-lag response
      try {
        const lastKnown = await Location.getLastKnownPositionAsync();
        if (lastKnown && lastKnown.coords) {
          const { latitude, longitude, accuracy } = lastKnown.coords;
          lastCoordsRef.current = { latitude, longitude, accuracy: accuracy || 25 };
          const jsCodeQuick = `
            if (typeof window.onNativeLocationUpdate === 'function') {
              window.onNativeLocationUpdate(${latitude}, ${longitude}, ${accuracy || 25}, 'Native GPS');
            }
          `;
          webViewRef.current?.injectJavaScript(jsCodeQuick);
        }
      } catch (eQuick) {
        // Continue to fresh GPS fix
      }

      // Step 2: Fresh active GPS fix
      try {
        const location = await Location.getCurrentPositionAsync({
          accuracy: Location.Accuracy.Balanced,
        });

        const { latitude, longitude, accuracy } = location.coords;
        lastCoordsRef.current = { latitude, longitude, accuracy: accuracy || 10 };
        console.log(`[SDARS Native] GPS fixed: ${latitude}, ${longitude} (±${accuracy}m)`);

        const jsCode = `
          if (typeof window.onNativeLocationUpdate === 'function') {
            window.onNativeLocationUpdate(${latitude}, ${longitude}, ${accuracy || 10}, 'Native GPS');
          }
        `;
        webViewRef.current?.injectJavaScript(jsCode);
      } catch (errActive) {
        if (lastCoordsRef.current) {
          console.log('[SDARS Native] Retaining valid location fix:', lastCoordsRef.current.latitude, lastCoordsRef.current.longitude);
        } else {
          console.log('[SDARS Native] Satellite acquisition in progress...');
        }
      }
    } catch (err) {
      console.warn('[SDARS Native] Permission or general location error:', err);
    }
  }, []);

  useEffect(() => {
    fetchAndInjectLocation();

    // Active continuous location watcher
    let locationSubscription = null;
    (async () => {
      try {
        const { status } = await Location.requestForegroundPermissionsAsync();
        if (status === 'granted') {
          locationSubscription = await Location.watchPositionAsync(
            {
              accuracy: Location.Accuracy.Balanced,
              timeInterval: 5000,
              distanceInterval: 10,
            },
            (newLoc) => {
              if (newLoc && newLoc.coords) {
                const { latitude, longitude, accuracy } = newLoc.coords;
                lastCoordsRef.current = { latitude, longitude, accuracy: accuracy || 10 };
                webViewRef.current?.injectJavaScript(`
                  if (typeof window.onNativeLocationUpdate === 'function') {
                    window.onNativeLocationUpdate(${latitude}, ${longitude}, ${accuracy || 10}, 'Live GPS');
                  }
                `);
              }
            }
          );
        }
      } catch (e) {
        console.warn('[SDARS Native] watchPosition error:', e);
      }
    })();

    return () => {
      locationSubscription?.remove();
    };
  }, [fetchAndInjectLocation]);

  const handleMessage = (event) => {
    try {
      const data = JSON.parse(event.nativeEvent.data);
      if (data && (data.type === 'REQUEST_LOCATION' || data.type === 'GET_GPS')) {
        // If we already have a cached fix, immediately inject it
        if (lastCoordsRef.current) {
          const { latitude, longitude, accuracy } = lastCoordsRef.current;
          webViewRef.current?.injectJavaScript(`
            if (typeof window.onNativeLocationUpdate === 'function') {
              window.onNativeLocationUpdate(${latitude}, ${longitude}, ${accuracy || 10}, 'Cached GPS');
            }
          `);
        }
        fetchAndInjectLocation();
      }
    } catch (e) {
      // Non-JSON message, ignore
    }
  };

  const handleRetry = () => {
    setHasError(false);
    setErrorDetails('');
    setKey(prev => prev + 1);
  };

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#0a0e17" />
      
      {hasError ? (
        <View style={styles.errorContainer}>
          <Text style={styles.errorIcon}>📡</Text>
          <Text style={styles.errorTitle}>Connecting to SDARS Server...</Text>
          <Text style={styles.errorSub}>
            Make sure your PC backend is running at:{'\n'}
            <Text style={styles.errorUrl}>{SERVER_URL}</Text>
          </Text>
          {errorDetails ? <Text style={styles.errorTech}>{errorDetails}</Text> : null}
          <TouchableOpacity style={styles.retryBtn} onPress={handleRetry}>
            <Text style={styles.retryText}>🔄 Retry Connection</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <WebView 
          key={key}
          ref={webViewRef}
          source={{ uri: `${SERVER_URL}?t=${Date.now()}` }} 
          style={{ flex: 1, backgroundColor: '#0a0e17' }}
          javaScriptEnabled={true}
          domStorageEnabled={true}
          geolocationEnabled={true}
          cacheEnabled={false}
          incognito={true}
          pullToRefreshEnabled={true}
          allowsBackForwardNavigationGestures={true}
          startInLoadingState={true}
          injectedJavaScriptBeforeContentLoaded={`
            window.isNativeApp = true;
            true;
          `}
          injectedJavaScript={`
            (function() {
              const toast = document.getElementById('appToast');
              if (toast) {
                toast.style.display = 'none';
                toast.classList.remove('active-toast');
                toast.textContent = '';
              }
            })();
            true;
          `}
          onMessage={handleMessage}
          onLoadEnd={() => {
            fetchAndInjectLocation();
          }}
          renderLoading={() => (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="large" color="#00e5ff" />
              <Text style={styles.loadingText}>Initializing SDARS Mobile...</Text>
            </View>
          )}
          onError={(syntheticEvent) => {
            const { nativeEvent } = syntheticEvent;
            setHasError(true);
            setErrorDetails(nativeEvent.description || 'Connection unreachable');
          }}
          onHttpError={(syntheticEvent) => {
            const { nativeEvent } = syntheticEvent;
            if (nativeEvent.statusCode >= 400) {
              setHasError(true);
              setErrorDetails(`HTTP ${nativeEvent.statusCode}`);
            }
          }}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0b0f19',
    paddingTop: Platform.OS === 'android' ? StatusBar.currentHeight : 44,
  },
  loadingContainer: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: '#0b0f19',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 10,
  },
  loadingText: {
    color: '#94a3b8',
    marginTop: 14,
    fontSize: 13,
    fontWeight: '600',
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 28,
    backgroundColor: '#0b0f19',
  },
  errorIcon: {
    fontSize: 54,
    marginBottom: 16,
  },
  errorTitle: {
    color: '#f8fafc',
    fontSize: 18,
    fontWeight: '800',
    marginBottom: 8,
    textAlign: 'center',
  },
  errorSub: {
    color: '#94a3b8',
    fontSize: 13,
    textAlign: 'center',
    lineHeight: 20,
    marginBottom: 16,
  },
  errorUrl: {
    color: '#00e5ff',
    fontWeight: '700',
  },
  errorTech: {
    color: '#ef4444',
    fontSize: 11,
    marginBottom: 20,
  },
  retryBtn: {
    backgroundColor: '#00e5ff',
    paddingHorizontal: 24,
    paddingVertical: 14,
    borderRadius: 12,
    marginTop: 10,
  },
  retryText: {
    color: '#090d16',
    fontWeight: '800',
    fontSize: 14,
    letterSpacing: 0.5,
  },
});
