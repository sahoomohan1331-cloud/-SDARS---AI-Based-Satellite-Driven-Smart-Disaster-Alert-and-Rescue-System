import React, { useState, useRef, useEffect, useCallback } from 'react';
import { View, Text, TextInput, StyleSheet, StatusBar, Platform, TouchableOpacity, ActivityIndicator, LogBox } from 'react-native';
import { WebView } from 'react-native-webview';
import * as Location from 'expo-location';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Suppress non-critical development warnings
LogBox.ignoreLogs([
  'Cannot connect to Expo CLI',
  'Failed to download the latest version of React Native DevTools',
]);
LogBox.ignoreAllLogs(true);

const DEFAULT_SERVER_URL = 'http://192.168.0.137:8000/mobile_app.html';
const STORAGE_KEY = 'SDARS_MOBILE_SERVER_URL';

export default function App() {
  const webViewRef = useRef(null);
  const [serverUrl, setServerUrl] = useState(DEFAULT_SERVER_URL);
  const [inputUrl, setInputUrl] = useState(DEFAULT_SERVER_URL);
  const [isUrlLoaded, setIsUrlLoaded] = useState(false);
  const [showConfig, setShowConfig] = useState(false);
  const [hasError, setHasError] = useState(false);
  const [errorDetails, setErrorDetails] = useState('');
  const [key, setKey] = useState(0);

  const lastCoordsRef = useRef(null);

  // Load saved server URL on startup
  useEffect(() => {
    (async () => {
      try {
        const saved = await AsyncStorage.getItem(STORAGE_KEY);
        if (saved && saved.trim().length > 0) {
          setServerUrl(saved.trim());
          setInputUrl(saved.trim());
        }
      } catch (err) {
        console.warn('[SDARS Native] Error loading saved server URL:', err);
      } finally {
        setIsUrlLoaded(true);
      }
    })();
  }, []);

  // Save new server URL
  const handleSaveUrl = async () => {
    let cleanUrl = inputUrl.trim();
    if (!cleanUrl.startsWith('http://') && !cleanUrl.startsWith('https://')) {
      cleanUrl = 'https://' + cleanUrl;
    }
    if (!cleanUrl.includes('/mobile_app.html') && !cleanUrl.endsWith('.html')) {
      cleanUrl = cleanUrl.replace(/\/+$/, '') + '/mobile_app.html';
    }
    try {
      await AsyncStorage.setItem(STORAGE_KEY, cleanUrl);
      setServerUrl(cleanUrl);
      setInputUrl(cleanUrl);
      setShowConfig(false);
      setHasError(false);
      setErrorDetails('');
      setKey(prev => prev + 1);
    } catch (err) {
      console.warn('[SDARS Native] Failed to save URL:', err);
    }
  };

  const handleResetDefault = async () => {
    try {
      await AsyncStorage.removeItem(STORAGE_KEY);
      setServerUrl(DEFAULT_SERVER_URL);
      setInputUrl(DEFAULT_SERVER_URL);
      setShowConfig(false);
      setHasError(false);
      setErrorDetails('');
      setKey(prev => prev + 1);
    } catch (err) {}
  };

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

      // Step 1: Send last known position immediately
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
      } catch (eQuick) {}

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
        }
      }
    } catch (err) {
      console.warn('[SDARS Native] Permission or general location error:', err);
    }
  }, []);

  useEffect(() => {
    fetchAndInjectLocation();

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
                const jsCode = `
                  if (typeof window.onNativeLocationUpdate === 'function') {
                    window.onNativeLocationUpdate(${latitude}, ${longitude}, ${accuracy || 10}, 'Native GPS Watcher');
                  }
                `;
                webViewRef.current?.injectJavaScript(jsCode);
              }
            }
          );
        }
      } catch (err) {}
    })();

    return () => {
      if (locationSubscription) {
        locationSubscription.remove();
      }
    };
  }, [fetchAndInjectLocation]);

  const handleMessage = (event) => {
    try {
      const data = JSON.parse(event.nativeEvent.data);
      if (data.type === 'REQUEST_NATIVE_LOCATION') {
        if (lastCoordsRef.current) {
          const { latitude, longitude, accuracy } = lastCoordsRef.current;
          webViewRef.current?.injectJavaScript(`
            if (typeof window.onNativeLocationUpdate === 'function') {
              window.onNativeLocationUpdate(${latitude}, ${longitude}, ${accuracy}, 'Native Cache');
            }
          `);
        }
        fetchAndInjectLocation();
      }
    } catch (e) {}
  };

  const handleRetry = () => {
    setHasError(false);
    setErrorDetails('');
    setKey(prev => prev + 1);
  };

  if (!isUrlLoaded) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#00e5ff" />
        <Text style={styles.loadingText}>Initializing SDARS Mobile...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#0b0f19" />
      
      {hasError || showConfig ? (
        <View style={styles.errorContainer}>
          <Text style={styles.errorIcon}>📡</Text>
          <Text style={styles.errorTitle}>
            {showConfig ? 'SDARS Server Configuration' : 'Connection Standby'}
          </Text>
          <Text style={styles.errorSub}>
            Target Server Endpoint:
          </Text>

          <TextInput
            style={styles.urlInput}
            value={inputUrl}
            onChangeText={setInputUrl}
            placeholder="http://192.168.x.x:8000/mobile_app.html"
            placeholderTextColor="#64748b"
            autoCapitalize="none"
            autoCorrect={false}
            keyboardType="url"
          />

          {errorDetails && !showConfig ? (
            <Text style={styles.errorTech}>{errorDetails}</Text>
          ) : null}

          <View style={styles.btnRow}>
            <TouchableOpacity style={styles.saveBtn} onPress={handleSaveUrl}>
              <Text style={styles.saveBtnText}>Connect to Server</Text>
            </TouchableOpacity>

            <TouchableOpacity style={styles.resetBtn} onPress={handleResetDefault}>
              <Text style={styles.resetBtnText}>Reset Local IP</Text>
            </TouchableOpacity>
          </View>

          {hasError && !showConfig ? (
            <TouchableOpacity style={styles.retryBtn} onPress={handleRetry}>
              <Text style={styles.retryText}>Retry Connection</Text>
            </TouchableOpacity>
          ) : null}
        </View>
      ) : (
        <WebView 
          key={key}
          ref={webViewRef}
          source={{ uri: `${serverUrl}?t=${Date.now()}` }} 
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
              <Text style={styles.loadingText}>Syncing Disaster Telemetry...</Text>
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
    padding: 24,
    backgroundColor: '#0b0f19',
  },
  errorIcon: {
    fontSize: 48,
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
    marginBottom: 12,
  },
  urlInput: {
    width: '100%',
    backgroundColor: '#1e293b',
    borderWidth: 1,
    borderColor: '#334155',
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 12,
    color: '#00e5ff',
    fontFamily: Platform.OS === 'android' ? 'monospace' : 'Courier',
    fontSize: 12,
    marginBottom: 14,
  },
  errorTech: {
    color: '#ef4444',
    fontSize: 12,
    marginBottom: 16,
    textAlign: 'center',
  },
  btnRow: {
    width: '100%',
    gap: 10,
    marginBottom: 12,
  },
  saveBtn: {
    backgroundColor: '#00e5ff',
    paddingVertical: 14,
    borderRadius: 10,
    alignItems: 'center',
  },
  saveBtnText: {
    color: '#090d16',
    fontWeight: '800',
    fontSize: 14,
    letterSpacing: 0.5,
  },
  resetBtn: {
    backgroundColor: 'rgba(255, 255, 255, 0.06)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.12)',
    paddingVertical: 12,
    borderRadius: 10,
    alignItems: 'center',
  },
  resetBtnText: {
    color: '#94a3b8',
    fontWeight: '600',
    fontSize: 13,
  },
  retryBtn: {
    paddingVertical: 10,
    alignItems: 'center',
  },
  retryText: {
    color: '#38bdf8',
    fontSize: 13,
    fontWeight: '600',
  },
});
