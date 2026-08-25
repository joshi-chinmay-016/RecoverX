import { IntelligenceResult, PriorityLevel, FailureCategory } from './intelligence';

export interface OpportunityListResponse {
  total: number;
  page: number;
  page_size: number;
  opportunities: IntelligenceResult[];
}

export interface OpportunityFilter {
  priority?: PriorityLevel | '';
  failure_category?: FailureCategory | '';
  page?: number;
  page_size?: number;
}
