"""Prometheus metrics for message processing."""

from prometheus_client import Counter

MESSAGES_TOTAL = Counter("matching_messages_total", "Messages processed", ["result"])
SPAM_FILTERED = Counter("matching_spam_filtered_total", "Messages filtered as spam", ["reason"])
LEADS_CREATED = Counter("matching_leads_created_total", "Leads created")
SEMANTIC_HITS = Counter("matching_semantic_hits_total", "Semantic product gate hits")
SEMANTIC_ERRORS = Counter("matching_semantic_errors_total", "Semantic path failures", ["stage"])
DEGRADED_TOTAL = Counter("matching_degraded_total", "Degraded matching (semantic unavailable, fuzzy only)")
INTENT_CLASS = Counter("matching_intent_class_total", "Intent class distribution", ["intent_class"])
GATE_REJECTED = Counter("matching_product_gate_rejected_total", "Product gate rejections", ["reason"])
