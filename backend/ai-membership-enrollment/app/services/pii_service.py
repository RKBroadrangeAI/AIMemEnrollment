from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from typing import Dict, List, Any
import logging

class PIIService:
    def __init__(self):
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()
    
    def detect_pii(self, text: str) -> List[Dict[str, Any]]:
        try:
            results = self.analyzer.analyze(text=text, language='en')
            return [
                {
                    "entity_type": result.entity_type,
                    "start": result.start,
                    "end": result.end,
                    "score": result.score
                }
                for result in results
            ]
        except Exception as e:
            logging.error(f"PII detection error: {str(e)}")
            return []
    
    def anonymize_text(self, text: str) -> str:
        try:
            analyzer_results = self.analyzer.analyze(text=text, language='en')
            anonymized_result = self.anonymizer.anonymize(
                text=text,
                analyzer_results=analyzer_results
            )
            return anonymized_result.text
        except Exception as e:
            logging.error(f"PII anonymization error: {str(e)}")
            return text
    
    def strip_pii_from_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        cleaned_data = {}
        for key, value in data.items():
            if isinstance(value, str):
                cleaned_data[key] = self.anonymize_text(value)
            elif isinstance(value, dict):
                cleaned_data[key] = self.strip_pii_from_data(value)
            elif isinstance(value, list):
                cleaned_data[key] = [
                    self.anonymize_text(item) if isinstance(item, str) else item
                    for item in value
                ]
            else:
                cleaned_data[key] = value
        return cleaned_data
