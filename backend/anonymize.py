"""PII anonymization via Microsoft Presidio."""

import logging

logger = logging.getLogger(__name__)

PII_ENTITIES = [
    "PERSON", "PHONE_NUMBER", "EMAIL_ADDRESS", "US_SSN",
    "DATE_TIME", "LOCATION", "NRP", "MEDICAL_LICENSE",
    "IP_ADDRESS", "US_DRIVER_LICENSE",
]

_analyzer = None
_anonymizer = None


def _get_analyzer():
    global _analyzer
    if _analyzer is None:
        from presidio_analyzer import AnalyzerEngine
        _analyzer = AnalyzerEngine()
    return _analyzer


def _get_anonymizer():
    global _anonymizer
    if _anonymizer is None:
        from presidio_anonymizer import AnonymizerEngine
        _anonymizer = AnonymizerEngine()
    return _anonymizer


def anonymize_text(raw_text: str) -> str:
    analyzer = _get_analyzer()
    anonymizer = _get_anonymizer()

    results = analyzer.analyze(text=raw_text, entities=PII_ENTITIES, language="en")
    anonymized = anonymizer.anonymize(text=raw_text, analyzer_results=results)
    logger.info("Anonymized %d PII entities.", len(results))
    return anonymized.text
