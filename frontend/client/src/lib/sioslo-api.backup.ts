const API_BASE_URL = "http://127.0.0.1:8000";

export interface DataHealthMetric {
  reliability_score: number;
  status_color: string;
  warning_message?: string | null;
  score_breakdown?: Record<string, any> | null;
  issues?: Array<Record<string, any>> | null;
}

export interface CorrelationMetric {
  keyword_overlap_score: number;
  market_trend_growth: string;
  trend_reference_source: string;
  per_product_details?: any[] | null;
}

export interface InnovationBlueprintItem {
  id: string;
  title: string;
  target_location: string;
  recommended_price: number;
  competitor_price_ceiling: number;
  justification: string;
  risk_factors: string[];
  whatsapp_copy_text: string;
  description?: string;        // untuk kompatibilitas sementara
  data_justification?: string; // jika masih ada field lama
}

export interface AnalysisResponse {
  status: string;
  data_health: DataHealthMetric;
  correlation_metrics: CorrelationMetric;
  innovation_blueprint: InnovationBlueprintItem[];
}

/**
 * Mengirim CSV ke endpoint /api/v1/analyze/
 */
export async function analyzeCsv(
  file: File,
  targetLokasi: string,
  sessionId?: string
): Promise<AnalysisResponse> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("target_lokasi", targetLokasi);
  if (sessionId) formData.append("session_id", sessionId);

  const response = await fetch(`${API_BASE_URL}/api/v1/analyze/`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`API error ${response.status}: ${errorText}`);
  }

  return response.json() as Promise<AnalysisResponse>;
}

/**
 * Fungsi peringatan konfigurasi API (sesuai log 2.2)
 * Harus berupa fungsi, bukan nilai statis.
 */
export function apiConfigurationNotice() {
  // Saat ini tidak menampilkan apa-apa; cukup return null
  return null;
}