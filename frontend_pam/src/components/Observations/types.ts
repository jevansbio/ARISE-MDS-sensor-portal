export interface Observation {
  id: number;
  obs_dt: string;
  source: string;
  needs_review: boolean;
  extra_data: {
    start_time: number;
    end_time: number;
    duration: number;
    avg_amplitude: number;
    auto_detected: boolean;
    needs_review?: boolean;
  };
  taxon: {
    species_name: string;
    species_common_name: string;
    id: number;
  };
} 