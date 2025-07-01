import { api } from '@/plugins/axiosInterceptor';

export async function importTemplates(fileIds: string[]) {
  return api.post('/admin/templates/import', { file_ids: fileIds });
}

export async function syncTemplate(id: number) {
  return api.post(`/admin/templates/${id}/sync`);
}

export async function getPreviewUrl(id: number) {
  const { data } = await api.get(`/admin/templates/${id}/preview`);
  return data.preview_url as string;
}

export async function duplicateTemplate(id: number) {
  return api.post(`/admin/templates/${id}/duplicate`);
}

export async function deleteTemplate(id: number) {
  return api.delete(`/admin/templates/${id}`);
}
