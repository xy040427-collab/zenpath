const API_BASE = '';

export interface ChsiBasicInfo {
  province: string;
  city: string;
  department: string;
  level: string;
  type: string;
  is_public: boolean;
}

export interface ChsiCampus {
  name: string;
  address: string;
  phone: string;
}

export interface ChsiMajorCategory {
  name: string;
  majors: string[];
}

export interface ChsiDepartment {
  name: string;
  description: string;
}

export interface ChsiAdmissionPolicy {
  clause_number: string;
  title: string;
  content: string;
}

export interface ChsiSchoolDetail {
  school_name: string;
  overview: string;
  basic_info: ChsiBasicInfo | null;
  campuses: ChsiCampus[];
  official_site: string;
  admission_site: string;
  contact_phone: string;
  tags: string[];
  major_categories: ChsiMajorCategory[];
  departments: ChsiDepartment[];
  admission_policies: ChsiAdmissionPolicy[];
  admission_summary: string;
  source: string;
  generated_at: string | null;
  from_cache: boolean;
  error?: string;
}

export async function fetchChsiSchoolDetail(schoolName: string): Promise<ChsiSchoolDetail> {
  const encoded = encodeURIComponent(schoolName);
  const res = await fetch(`${API_BASE}/api/chsi/school/${encoded}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const data = await res.json();
  if (!data.success) throw new Error('API returned success=false');
  return data as ChsiSchoolDetail;
}
