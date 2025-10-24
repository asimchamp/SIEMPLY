/**
 * Cross-browser compatible storage utility
 * Provides fallback storage methods for different browsers and privacy modes
 */

// Storage interface for consistent API
interface StorageInterface {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
  removeItem(key: string): void;
}

// Cookie-based storage fallback
class CookieStorage implements StorageInterface {
  getItem(key: string): string | null {
    const name = key + "=";
    const decodedCookie = decodeURIComponent(document.cookie);
    const ca = decodedCookie.split(';');
    for (let i = 0; i < ca.length; i++) {
      let c = ca[i];
      while (c.charAt(0) === ' ') {
        c = c.substring(1);
      }
      if (c.indexOf(name) === 0) {
        return c.substring(name.length, c.length);
      }
    }
    return null;
  }

  setItem(key: string, value: string): void {
    // Set cookie with 7 days expiration
    const expires = new Date();
    expires.setTime(expires.getTime() + (7 * 24 * 60 * 60 * 1000));
    document.cookie = `${key}=${value};expires=${expires.toUTCString()};path=/;SameSite=Lax`;
  }

  removeItem(key: string): void {
    document.cookie = `${key}=;expires=Thu, 01 Jan 1970 00:00:01 GMT;path=/;SameSite=Lax`;
  }
}

// Memory storage fallback (session-only)
class MemoryStorage implements StorageInterface {
  private storage: Map<string, string> = new Map();

  getItem(key: string): string | null {
    return this.storage.get(key) || null;
  }

  setItem(key: string, value: string): void {
    this.storage.set(key, value);
  }

  removeItem(key: string): void {
    this.storage.delete(key);
  }
}

// Test if a storage method is available
function isStorageAvailable(storage: Storage): boolean {
  try {
    const testKey = '__storage_test__';
    storage.setItem(testKey, 'test');
    storage.removeItem(testKey);
    return true;
  } catch (e) {
    return false;
  }
}

// Get browser information for debugging
function getBrowserInfo(): string {
  const userAgent = navigator.userAgent;
  let browser = 'Unknown';
  
  if (userAgent.includes('Chrome') && !userAgent.includes('Edg')) {
    browser = 'Chrome';
  } else if (userAgent.includes('Firefox')) {
    browser = 'Firefox';
  } else if (userAgent.includes('Safari') && !userAgent.includes('Chrome')) {
    browser = 'Safari';
  } else if (userAgent.includes('Edg')) {
    browser = 'Edge';
  } else if (userAgent.includes('Opera')) {
    browser = 'Opera';
  }
  
  const isIncognito = !isStorageAvailable(localStorage);
  return `${browser}${isIncognito ? ' (Incognito/Private)' : ''}`;
}

// Cross-browser storage manager
class CrossBrowserStorage {
  private primaryStorage: StorageInterface;
  private fallbackStorage: StorageInterface;
  private cookieStorage: StorageInterface;
  private memoryStorage: StorageInterface;
  
  constructor() {
    this.cookieStorage = new CookieStorage();
    this.memoryStorage = new MemoryStorage();
    
    // Determine the best storage method
    if (isStorageAvailable(localStorage)) {
      console.log(`[Storage] Using localStorage (${getBrowserInfo()})`);
      this.primaryStorage = localStorage;
      this.fallbackStorage = isStorageAvailable(sessionStorage) ? sessionStorage : this.cookieStorage;
    } else if (isStorageAvailable(sessionStorage)) {
      console.log(`[Storage] localStorage not available, using sessionStorage (${getBrowserInfo()})`);
      this.primaryStorage = sessionStorage;
      this.fallbackStorage = this.cookieStorage;
    } else {
      console.log(`[Storage] Browser storage not available, using cookies (${getBrowserInfo()})`);
      this.primaryStorage = this.cookieStorage;
      this.fallbackStorage = this.memoryStorage;
    }
  }

  getItem(key: string): string | null {
    try {
      // Try primary storage first
      let value = this.primaryStorage.getItem(key);
      if (value !== null) {
        return value;
      }

      // Try fallback storage
      value = this.fallbackStorage.getItem(key);
      if (value !== null) {
        // Sync back to primary if possible
        try {
          this.primaryStorage.setItem(key, value);
        } catch (e) {
          console.warn('[Storage] Could not sync to primary storage:', e);
        }
        return value;
      }

      // Try cookie storage as last resort
      if (this.primaryStorage !== this.cookieStorage && this.fallbackStorage !== this.cookieStorage) {
        value = this.cookieStorage.getItem(key);
        if (value !== null) {
          // Sync back to primary if possible
          try {
            this.primaryStorage.setItem(key, value);
          } catch (e) {
            console.warn('[Storage] Could not sync to primary storage:', e);
          }
          return value;
        }
      }

      return null;
    } catch (error) {
      console.error('[Storage] Error getting item:', error);
      return null;
    }
  }

  setItem(key: string, value: string): void {
    const errors: string[] = [];

    // Try to save to all available storage methods
    try {
      this.primaryStorage.setItem(key, value);
    } catch (error) {
      errors.push(`Primary: ${error}`);
    }

    try {
      this.fallbackStorage.setItem(key, value);
    } catch (error) {
      errors.push(`Fallback: ${error}`);
    }

    // Always try to save to cookies as ultimate fallback
    if (this.primaryStorage !== this.cookieStorage && this.fallbackStorage !== this.cookieStorage) {
      try {
        this.cookieStorage.setItem(key, value);
      } catch (error) {
        errors.push(`Cookie: ${error}`);
      }
    }

    if (errors.length > 0) {
      console.warn(`[Storage] Some storage methods failed for key "${key}":`, errors);
    }
  }

  removeItem(key: string): void {
    // Remove from all storage methods
    try {
      this.primaryStorage.removeItem(key);
    } catch (error) {
      console.warn('[Storage] Error removing from primary storage:', error);
    }

    try {
      this.fallbackStorage.removeItem(key);
    } catch (error) {
      console.warn('[Storage] Error removing from fallback storage:', error);
    }

    try {
      this.cookieStorage.removeItem(key);
    } catch (error) {
      console.warn('[Storage] Error removing from cookie storage:', error);
    }

    try {
      this.memoryStorage.removeItem(key);
    } catch (error) {
      console.warn('[Storage] Error removing from memory storage:', error);
    }
  }

  // Debug method to show storage status
  getStorageInfo(): object {
    return {
      browser: getBrowserInfo(),
      localStorage: isStorageAvailable(localStorage),
      sessionStorage: isStorageAvailable(sessionStorage),
      cookieSupport: typeof document !== 'undefined' && typeof document.cookie === 'string',
      primaryStorage: this.primaryStorage === localStorage ? 'localStorage' : 
                     this.primaryStorage === sessionStorage ? 'sessionStorage' : 
                     this.primaryStorage === this.cookieStorage ? 'cookies' : 'memory',
      fallbackStorage: this.fallbackStorage === localStorage ? 'localStorage' : 
                      this.fallbackStorage === sessionStorage ? 'sessionStorage' : 
                      this.fallbackStorage === this.cookieStorage ? 'cookies' : 'memory'
    };
  }
}

// Create and export the storage instance
export const storage = new CrossBrowserStorage();

// Export utility functions
export { getBrowserInfo };
