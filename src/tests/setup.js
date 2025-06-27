import { vi } from 'vitest'
import { config } from '@vue/test-utils'

// Mock fetch globally
global.fetch = vi.fn()

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
  length: 0,
  key: vi.fn()
}

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock
})

// Mock console methods to reduce noise in tests
global.console = {
  ...console,
  warn: vi.fn(),
  error: vi.fn()
}

// Vue Test Utils global configuration
config.global.mocks = {
  $t: (key) => key // Mock translation function
}

// Mock axios
vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => ({
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      delete: vi.fn(),
      interceptors: {
        request: { use: vi.fn() },
        response: { use: vi.fn() }
      }
    })),
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn()
  }
}))

// Mock Heroicons
vi.mock('@heroicons/vue/24/outline', () => ({
  CheckCircleIcon: 'CheckCircleIcon',
  XMarkIcon: 'XMarkIcon',
  ExclamationTriangleIcon: 'ExclamationTriangleIcon',
  ArrowDownTrayIcon: 'ArrowDownTrayIcon',
  CloudIcon: 'CloudIcon',
  ArrowPathIcon: 'ArrowPathIcon',
  ChevronDownIcon: 'ChevronDownIcon',
  ClockIcon: 'ClockIcon',
  XCircleIcon: 'XCircleIcon',
  UserIcon: 'UserIcon',
  MapPinIcon: 'MapPinIcon',
  DocumentTextIcon: 'DocumentTextIcon',
  BuildingOfficeIcon: 'BuildingOfficeIcon'
}))

// Setup and teardown for each test
beforeEach(() => {
  // Reset all mocks before each test
  vi.clearAllMocks()
  
  // Reset localStorage
  localStorageMock.getItem.mockClear()
  localStorageMock.setItem.mockClear()
  localStorageMock.removeItem.mockClear()
  localStorageMock.clear.mockClear()
})

afterEach(() => {
  // Cleanup after each test
  vi.resetAllMocks()
})