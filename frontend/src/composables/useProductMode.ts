import { computed, ref } from 'vue'

export type ProductMode = 'global' | 'institutional'

function initialMode(): ProductMode {
  if (typeof window === 'undefined') return 'global'
  const stored = localStorage.getItem('gfcri_product_mode')
  return stored === 'institutional' ? 'institutional' : 'global'
}

const mode = ref<ProductMode>(initialMode())

export function useProductMode() {
  function setMode(next: ProductMode) {
    mode.value = next
    if (typeof window !== 'undefined') {
      localStorage.setItem('gfcri_product_mode', next)
    }
  }

  function toggleMode() {
    setMode(mode.value === 'global' ? 'institutional' : 'global')
  }

  return {
    mode: computed(() => mode.value),
    isInstitutional: computed(() => mode.value === 'institutional'),
    setMode,
    toggleMode,
  }
}
