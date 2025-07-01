import { defineStore } from 'pinia'
import { api } from '@/plugins/axiosInterceptor'

interface User { id: number; email: string; roles: string[] }

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user   : null as User | null,
    access : ''  as string,
    csrf   : ''  as string,
    refresh: true                // existe cookie HttpOnly?
  }),
  actions: {
    async login(email: string, password: string) {
      const { data } = await api.post('/auth/login', { email, password })
      this.setAccess(data.access_token, data.csrf)
      this.user = data.user
    },
    setAccess(token: string, csrf: string) {
      this.access = token
      this.csrf   = csrf
    },
    logout() {
      this.access = ''
      this.user   = null
      // opcional: chamar /auth/logout para limpar cookie refresh
    }
  },
  getters: {
    isAdmin: s => s.user?.roles.includes('admin') ?? false,
    isEditor: s => s.user?.roles.includes('editor') ?? false
  }
}) 