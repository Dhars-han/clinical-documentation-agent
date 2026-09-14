"""DeepSeek API client with zero external network dependencies (standard library urllib).

Features:
- Reads credentials securely from DEEPSEEK_API_KEY and .env
- Configurable model (DEEPSEEK_MODEL, default: deepseek-chat)
- Configurable base URL (DEEPSEEK_BASE_URL, default: https://api.deepseek.com)
- Safe structured output parsing using JSON mode and Pydantic validation
- Comprehensive error handling: timeouts, rate limits, network outages, invalid JSON
- Automatic graceful fallback hooks when unavailable or unconfigured
"""

import os
import sys
import json
import logging
import urllib.request
import urllib.error
from typing import Dict, List, Optional, Any

from .schemas import (
    EvidenceExtractionResponse,
    ReconciliationReasoningResponse,
    DocumentationGenerationResponse,
)
from .prompts import (
    EVIDENCE_EXTRACTION_SYSTEM_PROMPT,
    RECONCILIATION_REASONING_SYSTEM_PROMPT,
    DOCUMENTATION_GENERATION_SYSTEM_PROMPT,
)

logger = logging.getLogger("deepseek_client")


def _load_env_file():
    """Lightweight .env parser to load environment variables without third-party dependencies."""
    # Search in project root (two levels up from backend/llm)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    env_path = os.path.join(project_root, ".env")
    
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip("'\"")
                    if k and k not in os.environ:
                        os.environ[k] = v
        except Exception as e:
            logger.warning(f"Could not parse .env file: {e}")


# Load .env upon module import
_load_env_file()


class DeepSeekClient:
    """Robust client for DeepSeek API reasoning and structured extraction."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 20.0
    ):
        self.api_key = api_key if api_key is not None else os.environ.get("DEEPSEEK_API_KEY", "").strip()
        self.model = model if model is not None else os.environ.get("DEEPSEEK_MODEL", "deepseek-chat").strip()
        self.base_url = (base_url if base_url is not None else os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")).rstrip("/")
        self.timeout = timeout

    def is_available(self) -> bool:
        """Returns True only if a valid, non-placeholder API key is configured."""
        if not self.api_key:
            return False
        # Disallow obvious placeholders
        placeholders = {"your_deepseek_api_key_here", "sk-xxx", "test", "none"}
        if self.api_key.lower() in placeholders:
            return False
        return len(self.api_key) > 8

    def _post_chat_completion(self, messages: List[Dict[str, str]], json_mode: bool = True) -> Optional[str]:
        """Performs raw POST request to DeepSeek /chat/completions."""
        if not self.is_available():
            logger.info("DeepSeek API key not configured; skipping LLM call.")
            return None

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": "AutonomousClinicalAgent/1.0"
        }

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.0,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        try:
            req_data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=req_data, headers=headers, method="POST")

            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                status = resp.status
                if status == 200:
                    body = resp.read().decode("utf-8")
                    data = json.loads(body)
                    content = data["choices"][0]["message"]["content"]
                    return content
                else:
                    logger.error(f"DeepSeek API returned HTTP status {status}")
                    return None

        except urllib.error.HTTPError as e:
            err_body = ""
            try:
                err_body = e.read().decode("utf-8")
            except Exception:
                pass
            if e.code == 429:
                logger.warning("DeepSeek API rate limit encountered (429). Falling back.")
            elif e.code in (401, 403):
                logger.error("DeepSeek API authentication error. Check DEEPSEEK_API_KEY.")
            else:
                logger.error(f"DeepSeek API HTTP error {e.code}: {err_body}")
            return None

        except urllib.error.URLError as e:
            logger.warning(f"DeepSeek API network/connection error: {e.reason}")
            return None

        except Exception as e:
            logger.error(f"Unexpected error communicating with DeepSeek API: {e}")
            return None

    def extract_evidence(
        self,
        text: str,
        source: str = "consultation",
        source_date: Optional[str] = None
    ) -> Optional[EvidenceExtractionResponse]:
        """Uses DeepSeek to extract structured clinical evidence from narrative dialogue."""
        if not self.is_available() or not text or not text.strip():
            return None

        user_content = (
            f"CLINICAL SOURCE: {source}\n"
            f"SOURCE DATE: {source_date or 'Unknown'}\n\n"
            f"NARRATIVE TEXT TO EXTRACT:\n{text.strip()}"
        )

        messages = [
            {"role": "system", "content": EVIDENCE_EXTRACTION_SYSTEM_PROMPT},
            {"role": "user", "content": user_content}
        ]

        raw_json = self._post_chat_completion(messages, json_mode=True)
        if not raw_json:
            return None

        try:
            data = json.loads(raw_json)
            return EvidenceExtractionResponse.model_validate(data)
        except Exception as e:
            logger.warning(f"Failed to validate DeepSeek extraction response: {e}. Raw: {raw_json[:200]}")
            return None

    def reason_reconciliation(
        self,
        entity_name: str,
        category: str,
        competing_items: List[Dict[str, Any]],
        deterministic_status: str
    ) -> Optional[ReconciliationReasoningResponse]:
        """Uses DeepSeek to reason over ambiguous or conflicting evidence items."""
        if not self.is_available() or not competing_items:
            return None

        user_content = json.dumps({
            "entity_name": entity_name,
            "category": category,
            "deterministic_preliminary_status": deterministic_status,
            "competing_evidence_items": competing_items
        }, indent=2)

        messages = [
            {"role": "system", "content": RECONCILIATION_REASONING_SYSTEM_PROMPT},
            {"role": "user", "content": f"Analyze the competing evidence for the following clinical entity:\n{user_content}"}
        ]

        raw_json = self._post_chat_completion(messages, json_mode=True)
        if not raw_json:
            return None

        try:
            data = json.loads(raw_json)
            return ReconciliationReasoningResponse.model_validate(data)
        except Exception as e:
            logger.warning(f"Failed to validate DeepSeek reconciliation reasoning response: {e}")
            return None

    def generate_documentation(
        self,
        patient_info: Dict[str, Any],
        transcript_excerpt: Optional[str],
        verified_evidence: List[Dict[str, Any]],
        reconciliation_summary: List[Dict[str, Any]],
        rag_references: List[Dict[str, Any]]
    ) -> Optional[DocumentationGenerationResponse]:
        """Uses DeepSeek to generate a professional clinical follow-up summary from verified evidence."""
        if not self.is_available():
            return None

        context_payload = {
            "patient_info": patient_info,
            "consultation_transcript": transcript_excerpt,
            "verified_evidence": verified_evidence,
            "reconciliation_summary": reconciliation_summary,
            "clinical_guidelines_background": rag_references
        }

        messages = [
            {"role": "system", "content": DOCUMENTATION_GENERATION_SYSTEM_PROMPT},
            {"role": "user", "content": f"Synthesize a clinical follow-up summary from this verified package:\n{json.dumps(context_payload, indent=2)}"}
        ]

        raw_json = self._post_chat_completion(messages, json_mode=True)
        if not raw_json:
            return None

        try:
            data = json.loads(raw_json)
            return DocumentationGenerationResponse.model_validate(data)
        except Exception as e:
            logger.warning(f"Failed to validate DeepSeek documentation generation response: {e}")
            return None


# Global singleton instance
_llm_client: Optional[DeepSeekClient] = None


def get_llm_client() -> DeepSeekClient:
    """Returns the shared DeepSeekClient instance."""
    global _llm_client
    if _llm_client is None:
        _llm_client = DeepSeekClient()
    return _llm_client
