from app.nlp.product_gate import ProductGateResult
from app.pipeline.orchestrator import MatchResult, match_message

ProductMatch = ProductGateResult

__all__ = ["MatchResult", "ProductGateResult", "ProductMatch", "match_message"]
