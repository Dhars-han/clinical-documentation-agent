import sys
import os
from typing import Dict, List, Tuple

try:
    from backend.evidence_agent import EvidenceItem, EvidenceCategory
except ImportError:
    from ..evidence_agent import EvidenceItem, EvidenceCategory


class EntityComparator:
    """Organizes and correlates evidence items for domain-specific reconciliation."""

    @staticmethod
    def prepare_entity_bundles(
        domain_map: Dict[str, List[EvidenceItem]]
    ) -> List[Tuple[str, str, List[EvidenceItem], List[EvidenceItem]]]:
        """Prepares comparison bundles: (entity_name, category, items, related_context_items).
        
        Links cross-cutting statements (such as general 'no known drug allergies' reports)
        to specific documented allergy entities like 'Penicillin'.
        """
        bundles = []

        # Identify any general allergy assertions (e.g. 'Drug Allergies' reporting NKDA)
        general_allergy_items = []
        for name, items in domain_map.items():
            if name.lower() in ["drug allergies", "allergies", "allergy"]:
                general_allergy_items.extend(items)

        for entity_name, items in domain_map.items():
            if not items:
                continue

            # Determine dominant category
            category = items[0].category.value if hasattr(items[0].category, "value") else str(items[0].category)

            # If this is a general assertion group (like 'Drug Allergies'), check if specific allergies exist
            if entity_name.lower() in ["drug allergies", "allergies", "allergy"]:
                has_specific_allergies = any(
                    k.lower() not in ["drug allergies", "allergies", "allergy"] and
                    any((it.category.value if hasattr(it.category, "value") else str(it.category)) == "allergy" for it in v)
                    for k, v in domain_map.items()
                )
                if has_specific_allergies:
                    # Specific allergies will be evaluated with this general statement as context
                    continue

            related_context = []
            if category == "allergy":
                # Link general allergy statements as related context for specific allergen reconciliation
                related_context.extend(general_allergy_items)

            bundles.append((entity_name, category, items, related_context))

        return bundles
