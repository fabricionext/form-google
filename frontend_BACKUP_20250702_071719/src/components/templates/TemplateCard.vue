<script setup lang="ts">
import { computed } from 'vue';
import { useAuthStore } from '@/stores/auth';

defineProps<{
  template: {
    id: number;
    nome: string;
    categoria: string;
    status: string;
    thumbnail: string;
    usage_count: number;
    avg_generation_time: number;
    detected_fields: string[];
    syncing: boolean;
    last_sync: string | null;
  };
}>();

const emit = defineEmits<{
  (e: 'preview'): void;
  (e: 'generate'): void;
  (e: 'edit'): void;
  (e: 'sync'): void;
  (e: 'duplicate'): void;
  (e: 'delete'): void;
}>();

const auth = useAuthStore();
const isEditor = computed(() => auth.isEditor || auth.isAdmin);
</script>

<template>
  <v-card class="elevation-4 template-card" @click="$emit('preview')">
    <div
      class="template-thumbnail"
      :style="{ backgroundImage: `url(${template.thumbnail})` }"
    >
      <v-overlay absolute :value="template.syncing">
        <v-progress-circular indeterminate size="32" />
      </v-overlay>
      <v-chip
        :color="template.status === 'ativo' ? 'success' : 'grey'"
        small
        class="ma-2"
        style="position: absolute; top: 0; right: 0"
      >
        {{ template.status }}
      </v-chip>
    </div>

    <v-card-title class="pb-2">{{ template.nome }}</v-card-title>

    <v-card-subtitle class="pt-0">
      <v-chip x-small outlined color="primary" class="mr-1">{{
        template.categoria
      }}</v-chip>
      <span class="text-caption"
        >Sync: {{ template.last_sync ?? 'Nunca' }}</span
      >
    </v-card-subtitle>

    <v-card-text>
      <!-- Estatísticas -->
      <div class="d-flex justify-space-between">
        <span class="text-caption">
          <v-icon small class="mr-1">mdi-file-document</v-icon
          >{{ template.usage_count }}
        </span>
        <span class="text-caption">
          <v-icon small class="mr-1">mdi-clock-outline</v-icon
          >{{ template.avg_generation_time }} s
        </span>
      </div>
    </v-card-text>

    <v-card-actions>
      <v-btn text small color="primary" @click.stop="$emit('preview')">
        <v-icon left small>mdi-eye</v-icon>Preview
      </v-btn>
      <v-btn text small color="success" @click.stop="$emit('generate')">
        <v-icon left small>mdi-play</v-icon>Gerar
      </v-btn>
      <v-spacer />
      <!-- menu só para editores/admin -->
      <template v-if="isEditor">
        <v-menu bottom left>
          <template #activator="{ on, attrs }">
            <v-btn icon small v-bind="attrs" v-on="on" @click.stop>
              <v-icon>mdi-dots-vertical</v-icon>
            </v-btn>
          </template>
          <v-list dense>
            <v-list-item @click="$emit('edit')">
              <v-list-item-icon><v-icon>mdi-pencil</v-icon></v-list-item-icon>
              <v-list-item-title>Editar</v-list-item-title>
            </v-list-item>
            <v-list-item @click="$emit('sync')">
              <v-list-item-icon><v-icon>mdi-sync</v-icon></v-list-item-icon>
              <v-list-item-title>Sincronizar</v-list-item-title>
            </v-list-item>
            <v-list-item @click="$emit('duplicate')">
              <v-list-item-icon
                ><v-icon>mdi-content-copy</v-icon></v-list-item-icon
              >
              <v-list-item-title>Duplicar</v-list-item-title>
            </v-list-item>
            <v-divider />
            <v-list-item @click="$emit('delete')" class="error--text">
              <v-list-item-icon
                ><v-icon color="error">mdi-delete</v-icon></v-list-item-icon
              >
              <v-list-item-title>Excluir</v-list-item-title>
            </v-list-item>
          </v-list>
        </v-menu>
      </template>
    </v-card-actions>
  </v-card>
</template>

<style scoped>
.template-card {
  transition: 0.2s;
  cursor: pointer;
}
.template-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15) !important;
}
.template-thumbnail {
  height: 180px;
  background-size: cover;
  background-position: center;
  background-color: #f5f5f5;
  position: relative;
}
</style>
