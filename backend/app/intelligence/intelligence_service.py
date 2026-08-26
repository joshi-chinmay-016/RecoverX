"""Intelligence service orchestration for revenue intelligence."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.db.models.payment import Payment
from app.db.models.recovery_case import RecoveryCase
from app.db.models.revenue_intelligence import RevenueIntelligenceResult
from app.intelligence.feature_extractor import FeatureExtractor
from app.intelligence.failure_classifier import FailureClassifier
from app.intelligence.revenue_calculator import RevenueAtRiskCalculator
from app.intelligence.probability_engine import RecoveryProbabilityEngine
from app.intelligence.opportunity_scorer import OpportunityScorer
from app.intelligence.intervention_engine import InterventionRecommendationEngine
from app.intelligence.schemas import (
    IntelligenceResult,
    IntelligenceOverview,
    OpportunityListResponse,
    PriorityLevel,
    FailureCategory,
)
from app.core.logging import logger, get_logger


class IntelligenceService:
    """Service for orchestrating revenue intelligence analysis."""
    
    def __init__(self, db: Session):
        self.db = db
        self.feature_extractor = FeatureExtractor(db)
        self.failure_classifier = FailureClassifier()
        self.revenue_calculator = RevenueAtRiskCalculator()
        self.probability_engine = RecoveryProbabilityEngine()
        self.opportunity_scorer = OpportunityScorer()
        self.intervention_engine = InterventionRecommendationEngine()
        self.logger = get_logger(__name__)
    
    def analyze_payment(self, payment: Payment, force_reanalyze: bool = False) -> IntelligenceResult:
        """Analyze a payment and generate intelligence result."""
        # Check if intelligence result already exists
        existing_result = self.db.query(RevenueIntelligenceResult).filter(
            RevenueIntelligenceResult.payment_id == payment.id
        ).first()
        
        if existing_result and not force_reanalyze:
            logger.info(f"intelligence_result_exists payment_id={payment.id}")
            return self._to_schema(existing_result)
        
        # Extract features
        self.logger.debug(f"extracting_features payment_id={payment.id}")
        features = self.feature_extractor.extract_features(payment)
        
        # Classify failure
        self.logger.debug(f"classifying_failure payment_id={payment.id}")
        classification = self.failure_classifier.classify(features)
        
        # Calculate recovery probability
        self.logger.debug(f"calculating_probability payment_id={payment.id}")
        recovery_probability = self.probability_engine.calculate(features, classification.category)
        
        # Calculate revenue at risk
        self.logger.debug(f"calculating_revenue_risk payment_id={payment.id}")
        revenue_at_risk = self.revenue_calculator.calculate(
            features, classification.category, recovery_probability.probability
        )
        
        # Score opportunity
        self.logger.debug(f"scoring_opportunity payment_id={payment.id}")
        opportunity_score = self.opportunity_scorer.score(
            features, recovery_probability, revenue_at_risk.estimated_recoverable_revenue
        )
        
        # Recommend intervention
        self.logger.debug(f"recommending_intervention payment_id={payment.id}")
        intervention = self.intervention_engine.recommend(
            features, classification.category, opportunity_score.priority, recovery_probability.probability
        )
        
        # Get recovery case ID
        recovery_case = self.db.query(RecoveryCase).filter(
            RecoveryCase.payment_id == payment.id
        ).first()
        
        # Build explanation
        explanation = self._build_explanation(
            classification,
            recovery_probability,
            opportunity_score,
            intervention,
        )
        
        # Create or update intelligence result
        if existing_result:
            self._update_intelligence_result(
                existing_result,
                classification,
                revenue_at_risk,
                recovery_probability,
                opportunity_score,
                intervention,
                explanation,
            )
            result = existing_result
        else:
            result = self._create_intelligence_result(
                payment.id,
                recovery_case.id if recovery_case else None,
                classification,
                revenue_at_risk,
                recovery_probability,
                opportunity_score,
                intervention,
                explanation,
            )
        
        logger.info(
            f"intelligence_analysis_complete "
            f"payment_id={payment.id} "
            f"category={classification.category.value} "
            f"probability={recovery_probability.probability:.2f} "
            f"priority={opportunity_score.priority.value} "
            f"score={opportunity_score.score:.2f} "
            f"model_version=rules-v1"
        )
        
        return self._to_schema(result)
    
    def _create_intelligence_result(
        self,
        payment_id: str,
        recovery_case_id: Optional[str],
        classification,
        revenue_at_risk,
        recovery_probability,
        opportunity_score,
        intervention,
        explanation: str,
    ) -> RevenueIntelligenceResult:
        """Create a new intelligence result."""
        result = RevenueIntelligenceResult(
            payment_id=payment_id,
            recovery_case_id=recovery_case_id,
            failure_category=classification.category,
            failure_reason=classification.normalized_reason,
            revenue_at_risk=revenue_at_risk.gross_failed_revenue,
            recovery_probability=recovery_probability.probability,
            estimated_recoverable_revenue=revenue_at_risk.estimated_recoverable_revenue,
            opportunity_score=opportunity_score.score,
            priority=opportunity_score.priority,
            recommended_intervention=intervention.recommended_action,
            intervention_reason=intervention.reason,
            confidence=intervention.confidence,
            explanation=explanation,
            factors=opportunity_score.score_factors,  # Use score factors for explainability
            model_version="rules-v1",
        )
        
        self.db.add(result)
        self.db.commit()
        self.db.refresh(result)
        
        return result
    
    def _update_intelligence_result(
        self,
        result: RevenueIntelligenceResult,
        classification,
        revenue_at_risk,
        recovery_probability,
        opportunity_score,
        intervention,
        explanation: str,
    ):
        """Update an existing intelligence result."""
        result.failure_category = classification.category
        result.failure_reason = classification.normalized_reason
        result.revenue_at_risk = revenue_at_risk.gross_failed_revenue
        result.recovery_probability = recovery_probability.probability
        result.estimated_recoverable_revenue = revenue_at_risk.estimated_recoverable_revenue
        result.opportunity_score = opportunity_score.score
        result.priority = opportunity_score.priority
        result.recommended_intervention = intervention.recommended_action
        result.intervention_reason = intervention.reason
        result.confidence = intervention.confidence
        result.explanation = explanation
        result.factors = opportunity_score.score_factors  # Use score factors for explainability
        result.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(result)
    
    def _build_explanation(
        self,
        classification,
        recovery_probability,
        opportunity_score,
        intervention,
    ) -> str:
        """Build a comprehensive explanation."""
        parts = [
            f"Payment failed due to {classification.normalized_reason.lower()}. ",
            f"Estimated recovery likelihood is {recovery_probability.probability * 100:.0f}% based on rules-v1 model. ",
            f"Opportunity score is {opportunity_score.score:.1f} with {opportunity_score.priority.value} priority. ",
            f"Recommended action: {intervention.recommended_action}. ",
        ]
        
        return "".join(parts)
    
    def _to_schema(self, result: RevenueIntelligenceResult) -> IntelligenceResult:
        """Convert database model to schema."""
        return IntelligenceResult(
            id=str(result.id),
            payment_id=str(result.payment_id),
            recovery_case_id=str(result.recovery_case_id) if result.recovery_case_id else None,
            failure_category=result.failure_category,
            failure_reason=result.failure_reason,
            revenue_at_risk=result.revenue_at_risk,
            recovery_probability=result.recovery_probability,
            estimated_recoverable_revenue=result.estimated_recoverable_revenue,
            opportunity_score=result.opportunity_score,
            priority=result.priority,
            recommended_intervention=result.recommended_intervention,
            intervention_reason=result.intervention_reason,
            confidence=result.confidence,
            explanation=result.explanation,
            factors=result.factors,
            model_version=result.model_version,
            created_at=result.created_at,
            updated_at=result.updated_at,
        )
    
    def get_intelligence_result(self, result_id: str, merchant_id: Optional[Any] = None) -> Optional[IntelligenceResult]:
        """Get intelligence result by ID, optionally scoped to tenant."""
        query = self.db.query(RevenueIntelligenceResult).filter(
            RevenueIntelligenceResult.id == result_id
        )
        if merchant_id is not None:
            query = query.join(Payment, RevenueIntelligenceResult.payment_id == Payment.id).filter(Payment.merchant_id == merchant_id)

        result = query.first()
        if not result:
            return None
        
        return self._to_schema(result)
    
    def get_intelligence_by_payment(self, payment_id: str, merchant_id: Optional[Any] = None) -> Optional[IntelligenceResult]:
        """Get intelligence result by payment ID, optionally scoped to tenant."""
        query = self.db.query(RevenueIntelligenceResult).filter(
            RevenueIntelligenceResult.payment_id == payment_id
        )
        if merchant_id is not None:
            query = query.join(Payment, RevenueIntelligenceResult.payment_id == Payment.id).filter(Payment.merchant_id == merchant_id)

        result = query.first()
        if not result:
            return None
        
        return self._to_schema(result)
    
    def list_opportunities(
        self,
        priority: Optional[PriorityLevel] = None,
        failure_category: Optional[FailureCategory] = None,
        merchant_id: Optional[Any] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> OpportunityListResponse:
        """List recovery opportunities with filters and tenant scoping."""
        query = self.db.query(RevenueIntelligenceResult)
        
        if merchant_id is not None:
            query = query.join(Payment, RevenueIntelligenceResult.payment_id == Payment.id).filter(Payment.merchant_id == merchant_id)

        if priority:
            query = query.filter(RevenueIntelligenceResult.priority == priority)
        
        if failure_category:
            query = query.filter(RevenueIntelligenceResult.failure_category == failure_category)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * page_size
        results = query.order_by(RevenueIntelligenceResult.opportunity_score.desc()).offset(offset).limit(page_size).all()
        
        opportunities = [self._to_schema(r) for r in results]
        
        return OpportunityListResponse(
            opportunities=opportunities,
            total=total,
            page=page,
            page_size=page_size,
        )
    
    def get_overview(self, merchant_id: Optional[Any] = None) -> IntelligenceOverview:
        """Get merchant-level aggregate intelligence scoped to tenant."""
        # Get all intelligence results for this merchant
        query = self.db.query(RevenueIntelligenceResult)
        if merchant_id is not None:
            query = query.join(Payment, RevenueIntelligenceResult.payment_id == Payment.id).filter(Payment.merchant_id == merchant_id)
        results = query.all()
        
        # Calculate aggregates
        total_revenue_at_risk = sum(r.revenue_at_risk for r in results)
        total_estimated_recoverable = sum(r.estimated_recoverable_revenue for r in results)
        
        # Count by priority
        priority_counts = {}
        for priority in PriorityLevel:
            count = sum(1 for r in results if r.priority == priority)
            priority_counts[priority.value] = count
        
        # Count by failure category
        category_counts = {}
        for category in FailureCategory:
            count = sum(1 for r in results if r.failure_category == category)
            category_counts[category.value] = count
        
        # Get top failure reasons
        reason_counts = {}
        for r in results:
            reason = r.failure_reason
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
        
        top_failure_reasons = [
            {"reason": reason, "count": count}
            for reason, count in sorted(reason_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        ]
        
        # Get total revenue from payments (for context)
        payments_query = self.db.query(Payment)
        if merchant_id is not None:
            payments_query = payments_query.filter(Payment.merchant_id == merchant_id)
        payments = payments_query.all()

        total_revenue = sum(p.amount_minor for p in payments)
        failed_revenue = sum(p.amount_minor for p in payments if (p.status.value if hasattr(p.status, "value") else str(p.status)) == "FAILED")
        
        return IntelligenceOverview(
            total_revenue=total_revenue,
            failed_revenue=failed_revenue,
            revenue_at_risk=total_revenue_at_risk,
            estimated_recoverable_revenue=total_estimated_recoverable,
            recovered_revenue=0,  # Will be calculated from actual recoveries in Phase 3
            recovery_opportunity_count=len(results),
            high_priority_opportunities=priority_counts.get("HIGH", 0) + priority_counts.get("CRITICAL", 0),
            failure_distribution=category_counts,
            top_failure_reasons=top_failure_reasons,
            priority_distribution=priority_counts,
        )
