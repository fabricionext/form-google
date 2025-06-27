import { ref } from 'vue'

/**
 * Composable para gerenciar drag and drop
 * Substitui o uso do Interact.js com funcionalidade nativa
 */
export function useDragAndDrop() {
  const isDragging = ref(false)
  const dragData = ref(null)
  
  // Estados de drop zones
  const dropZones = ref(new Map())
  
  const initializeDragAndDrop = () => {
    // Configurar elementos draggáveis
    setupDraggableElements()
    
    // Configurar drop zones
    setupDropZones()
  }
  
  const setupDraggableElements = () => {
    // Clientes draggáveis
    document.addEventListener('dragstart', (event) => {
      const element = event.target.closest('[data-type="cliente"]')
      if (element) {
        handleClientDragStart(event, element)
      }
      
      const autoridade = event.target.closest('[data-type="autoridade"]')
      if (autoridade) {
        handleAuthorityDragStart(event, autoridade)
      }
    })
    
    document.addEventListener('dragend', (event) => {
      isDragging.value = false
      dragData.value = null
      
      // Limpar classes de drag de todos os elementos
      document.querySelectorAll('.dragging').forEach(el => {
        el.classList.remove('dragging')
      })
    })
  }
  
  const setupDropZones = () => {
    // Drop zone para cliente principal
    setupClientDropZone()
    
    // Drop zones para autores
    setupAuthorDropZones()
    
    // Drop zones para autoridades
    setupAuthorityDropZones()
  }
  
  const handleClientDragStart = (event, element) => {
    isDragging.value = true
    
    try {
      const clienteData = JSON.parse(element.dataset.cliente)
      dragData.value = { type: 'cliente', data: clienteData }
      
      // Configurar dados do drag
      event.dataTransfer.setData('application/json', JSON.stringify(clienteData))
      event.dataTransfer.setData('text/plain', clienteData.nome_completo)
      event.dataTransfer.effectAllowed = 'copy'
      
      // Adicionar classe visual
      element.classList.add('dragging')
      
    } catch (error) {
      console.error('Erro ao iniciar drag de cliente:', error)
    }
  }
  
  const handleAuthorityDragStart = (event, element) => {
    isDragging.value = true
    
    try {
      const autoridadeData = JSON.parse(element.dataset.autoridade)
      dragData.value = { type: 'autoridade', data: autoridadeData }
      
      // Configurar dados do drag
      event.dataTransfer.setData('application/json', JSON.stringify(autoridadeData))
      event.dataTransfer.setData('text/plain', autoridadeData.nome)
      event.dataTransfer.effectAllowed = 'copy'
      
      // Adicionar classe visual
      element.classList.add('dragging')
      
    } catch (error) {
      console.error('Erro ao iniciar drag de autoridade:', error)
    }
  }
  
  const setupClientDropZone = () => {
    const dropZone = document.getElementById('drop_placeholder')
    if (!dropZone) return
    
    dropZone.addEventListener('dragover', (event) => {
      event.preventDefault()
      if (dragData.value?.type === 'cliente') {
        dropZone.classList.add('drop-active')
      }
    })
    
    dropZone.addEventListener('dragleave', (event) => {
      // Verificar se realmente saiu da área (não foi para um filho)
      if (!dropZone.contains(event.relatedTarget)) {
        dropZone.classList.remove('drop-active')
      }
    })
    
    dropZone.addEventListener('drop', (event) => {
      event.preventDefault()
      dropZone.classList.remove('drop-active')
      
      if (dragData.value?.type === 'cliente') {
        emitClientDrop(dragData.value.data)
      }
    })
  }
  
  const setupAuthorDropZones = () => {
    // Usar delegação de eventos para drop zones dinâmicos
    document.addEventListener('dragover', (event) => {
      const dropZone = event.target.closest('.autor-drop-zone')
      if (dropZone && dragData.value?.type === 'cliente') {
        event.preventDefault()
        dropZone.classList.add('drop-active')
      }
    })
    
    document.addEventListener('dragleave', (event) => {
      const dropZone = event.target.closest('.autor-drop-zone')
      if (dropZone && !dropZone.contains(event.relatedTarget)) {
        dropZone.classList.remove('drop-active')
      }
    })
    
    document.addEventListener('drop', (event) => {
      const dropZone = event.target.closest('.autor-drop-zone')
      if (dropZone && dragData.value?.type === 'cliente') {
        event.preventDefault()
        dropZone.classList.remove('drop-active')
        
        const autorIndex = dropZone.dataset.autorIndex
        emitAuthorDrop(dragData.value.data, autorIndex)
      }
    })
  }
  
  const setupAuthorityDropZones = () => {
    document.addEventListener('dragover', (event) => {
      const dropZone = event.target.closest('.authority-drop-zone')
      if (dropZone && dragData.value?.type === 'autoridade') {
        event.preventDefault()
        dropZone.classList.add('drop-target')
      }
    })
    
    document.addEventListener('dragleave', (event) => {
      const dropZone = event.target.closest('.authority-drop-zone')
      if (dropZone && !dropZone.contains(event.relatedTarget)) {
        dropZone.classList.remove('drop-target')
      }
    })
    
    document.addEventListener('drop', (event) => {
      const dropZone = event.target.closest('.authority-drop-zone')
      if (dropZone && dragData.value?.type === 'autoridade') {
        event.preventDefault()
        dropZone.classList.remove('drop-target')
        
        const authorityIndex = dropZone.dataset.authorityIndex || 1
        emitAuthorityDrop(dragData.value.data, authorityIndex)
      }
    })
  }
  
  // Event emitters - integração com Vue
  const eventCallbacks = ref({
    clientDrop: null,
    authorDrop: null,
    authorityDrop: null
  })
  
  const onClientDrop = (callback) => {
    eventCallbacks.value.clientDrop = callback
  }
  
  const onAuthorDrop = (callback) => {
    eventCallbacks.value.authorDrop = callback
  }
  
  const onAuthorityDrop = (callback) => {
    eventCallbacks.value.authorityDrop = callback
  }
  
  const emitClientDrop = (clienteData) => {
    if (eventCallbacks.value.clientDrop) {
      eventCallbacks.value.clientDrop(clienteData)
    }
  }
  
  const emitAuthorDrop = (clienteData, autorIndex) => {
    if (eventCallbacks.value.authorDrop) {
      eventCallbacks.value.authorDrop({ clienteData, autorIndex })
    }
  }
  
  const emitAuthorityDrop = (autoridadeData, index) => {
    if (eventCallbacks.value.authorityDrop) {
      eventCallbacks.value.authorityDrop({ autoridadeData, index })
    }
  }
  
  // Utilitários para elementos específicos
  const makeDraggable = (element, type, data) => {
    element.draggable = true
    element.dataset.type = type
    
    if (type === 'cliente') {
      element.dataset.cliente = JSON.stringify(data)
    } else if (type === 'autoridade') {
      element.dataset.autoridade = JSON.stringify(data)
    }
    
    // Adicionar classes CSS
    element.classList.add('draggable-item')
  }
  
  const makeDropZone = (element, acceptTypes = []) => {
    element.classList.add('drop-zone')
    element.dataset.acceptTypes = acceptTypes.join(',')
  }
  
  // Limpeza
  const cleanup = () => {
    // Remover event listeners se necessário
    // (não necessário para delegação de eventos no document)
  }
  
  return {
    // Estado
    isDragging,
    dragData,
    
    // Métodos principais
    initializeDragAndDrop,
    cleanup,
    
    // Event handlers
    onClientDrop,
    onAuthorDrop,
    onAuthorityDrop,
    
    // Utilitários
    makeDraggable,
    makeDropZone
  }
}

/**
 * CSS personalizado para drag and drop
 */
export const dragDropCSS = `
.draggable-item {
  cursor: move;
  transition: transform 0.2s ease, opacity 0.2s ease;
}

.draggable-item:hover {
  transform: translateY(-2px);
}

.draggable-item.dragging {
  opacity: 0.6;
  transform: scale(0.95);
}

.drop-zone {
  transition: all 0.3s ease;
}

.drop-zone.drop-active {
  background-color: rgba(78, 115, 223, 0.1);
  border-color: #4e73df;
  transform: scale(1.02);
}

.drop-zone.drop-target {
  background-color: rgba(246, 194, 62, 0.1);
  border-color: #f6c23e;
  transform: scale(1.02);
}

.autor-drop-zone {
  border: 2px dashed rgba(255, 255, 255, 0.5);
  border-radius: 0.375rem;
  transition: all 0.3s ease;
}

.autor-drop-zone.drop-active {
  border-color: #fff;
  background-color: rgba(255, 255, 255, 0.2);
  transform: scale(1.05);
}

.authority-drop-zone {
  border: 2px dashed #dee2e6;
  border-radius: 0.5rem;
  min-height: 100px;
  transition: all 0.3s ease;
}

.authority-drop-zone.drop-target {
  border-color: #f6c23e;
  background-color: #fffbf0;
}

/* Animações de feedback */
@keyframes dropSuccess {
  0% { background-color: transparent; }
  50% { background-color: rgba(40, 167, 69, 0.3); }
  100% { background-color: transparent; }
}

.drop-success {
  animation: dropSuccess 1s ease;
}
`