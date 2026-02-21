"""
DocuForge AI — Bias Detector

Tests for biases in agent responses using paired queries that differ
in a single dimension (gender, date, company size, etc.). Detects suspicious
response differences that suggest inappropriate bias.
"""

import logging

logger = logging.getLogger(__name__)
