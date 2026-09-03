import { computed, ref } from 'vue'
import { useAuth } from './useAuth'

export type ProductMode = 'global' | 'institutional'

const selectedMode = ref<ProductMode>('global')

export function useProductMode() {
  const { isInstitutionalAccount } = useAuth()
  const mode = computed<ProductMode>(() => (
    isInstitutionalAccount.value ? 'institutional' : selectedMode.value
  ))

  function setMode(next: ProductMode) {
    selectedMode.value = next === 'global' || isInstitutionalAccount.value ? next : 'global'
  }

  function toggleMode() {
    if (isInstitutionalAccount.value) return
    setMode(mode.value === 'global' ? 'institutional' : 'global')
  }

  return {
    mode,
    isInstitutional: computed(() => mode.value === 'institutional'),
    setMode,
    toggleMode,
  }
}