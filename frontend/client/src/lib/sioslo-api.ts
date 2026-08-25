export function apiConfigurationNotice() {
    return null;
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
    // optional legacy fields (fallback)
    description?: string;
    data_justification?: string;
}

export interface AnalysisResponse {
    status: string;
    data_health: {
        reliability_score: number;
        status_color: string;           // "green" | "yellow" | "red"
        warning_message: string;
        score_breakdown?: Record<string, number>;
        issues?: {
            row_index?: number | null;
            column?: string | null;
            issue_type: string;
            detail: string;
        }[];
    };
    correlation_metrics: {
        keyword_overlap_score: number;
        market_trend_growth: string;
        trend_reference_source: string;
    };
    innovation_blueprint: InnovationBlueprintItem[];
}

export async function analyzeCsv(file: File, targetLocation: string): Promise<AnalysisResponse> {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("target_lokasi", targetLocation);

    const response = await fetch("http://localhost:8000/api/v1/analyze/", {
        method: "POST",
        body: formData,
    });

    if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(errorData?.detail || `API error: ${response.statusText}`);
    }

    return response.json();
}
