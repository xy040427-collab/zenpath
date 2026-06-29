import api from './api';

export interface SchoolData {
  id: string;
  slug: string;
  name: string;
  province: string;
  city: string;
  type: string;
  level: string;
  ranking: number;
  tags: string[];
  description: string;
  website: string;
  logo_slug: string;
}

export interface SchoolsResponse {
  data: SchoolData[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface SchoolsMeta {
  total: number;
  provinces: string[];
  province_counts: Record<string, number>;
  levels: string[];
  level_counts: Record<string, number>;
  types: string[];
}

export async function fetchSchools(params: {
  page?: number;
  page_size?: number;
  search?: string;
  level?: string;
  type?: string;
  province?: string;
}): Promise<SchoolsResponse> {
  const cleanParams: Record<string, string | number> = {};
  if (params.page !== undefined && params.page > 0) cleanParams.page = params.page;
  if (params.page_size !== undefined) cleanParams.page_size = params.page_size;
  if (params.search) cleanParams.search = params.search;
  if (params.level && params.level !== '全部') cleanParams.level = params.level;
  if (params.type && params.type !== '全部') cleanParams.type = params.type;
  if (params.province && params.province !== '全部') cleanParams.province = params.province;

  const response = await api.get<SchoolsResponse>('/schools', { params: cleanParams });
  return response.data;
}

export async function fetchSchoolBySlug(slug: string): Promise<SchoolData> {
  const response = await api.get<SchoolData>(`/schools/${slug}`);
  return response.data;
}

export async function fetchSchoolsMeta(): Promise<SchoolsMeta> {
  const response = await api.get<SchoolsMeta>('/schools/meta');
  return response.data;
}
