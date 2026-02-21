"""
DocuForge AI — Hallucination Scorer

Detects hallucinations in agent outputs by measuring faithfulness to
source documents. Flags claims that cannot be grounded in the retrieval
context.
"""

import logging

logger = logging.getLogger(__name__)
