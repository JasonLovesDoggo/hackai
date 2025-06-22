from typing import Dict, List
from .models import AffiliateProgram, OverrideEntry
import logging

logger = logging.getLogger("uvicorn.error")

# Manual overrides for specific products/keywords
AFFILIATE_OVERRIDES: Dict[str, OverrideEntry] = {
    "gaming_mouse": OverrideEntry(
        keywords=["gaming mouse", "gaming mice", "computer mouse"],
        forced_programs=[
            AffiliateProgram(
                name="Amazon Associates",
                website="https://amazon.com",
                affiliate_link="https://affiliate-program.amazon.com/",
                commission_rate="1-10%",
                program_type="marketplace",
                signup_link="https://affiliate-program.amazon.com/",
                requirements="Valid website or app, comply with policies",
                confidence_score=0.95,
            ),
            AffiliateProgram(
                name="Best Buy Affiliate",
                website="https://bestbuy.com",
                affiliate_link="https://www.bestbuy.com/site/affiliate-program/affiliate-program/pcmcat154800050006.c",
                commission_rate="1-4%",
                program_type="direct",
                signup_link="https://www.bestbuy.com/site/affiliate-program/affiliate-program/pcmcat154800050006.c",
                requirements="Active website, US traffic",
                confidence_score=0.85,
            ),
        ],
        replace_all=False,
    ),
    "protein_powder": OverrideEntry(
        keywords=["protein powder", "whey protein", "protein supplement"],
        forced_programs=[
            AffiliateProgram(
                name="iHerb Affiliate",
                website="https://iherb.com",
                affiliate_link="https://www.iherb.com/info/affiliate-program",
                commission_rate="5-10%",
                program_type="direct",
                signup_link="https://www.iherb.com/info/affiliate-program",
                requirements="Active promotion, monthly sales minimums",
                confidence_score=0.9,
            ),
            AffiliateProgram(
                name="Bodybuilding.com Affiliate",
                website="https://bodybuilding.com",
                affiliate_link="https://www.bodybuilding.com/affiliates/",
                commission_rate="3-8%",
                program_type="direct",
                signup_link="https://www.bodybuilding.com/affiliates/",
                requirements="Fitness-related content, active promotion",
                confidence_score=0.88,
            ),
        ],
        replace_all=False,
    ),
    "tech_gadgets": OverrideEntry(
        keywords=["tech gadgets", "electronics", "gadgets", "tech accessories"],
        forced_programs=[
            AffiliateProgram(
                name="Amazon Associates",
                website="https://amazon.com",
                affiliate_link="https://affiliate-program.amazon.com/",
                commission_rate="1-10%",
                program_type="marketplace",
                signup_link="https://affiliate-program.amazon.com/",
                requirements="Valid website or app, comply with policies",
                confidence_score=0.95,
            ),
            AffiliateProgram(
                name="Newegg Affiliate",
                website="https://newegg.com",
                affiliate_link="https://www.newegg.com/promotions/affiliate/",
                commission_rate="1-4%",
                program_type="direct",
                signup_link="https://www.newegg.com/promotions/affiliate/",
                requirements="Tech-focused content, active promotion",
                confidence_score=0.87,
            ),
        ],
        replace_all=False,
    ),
}


class OverrideManager:
    def __init__(self):
        self.overrides = AFFILIATE_OVERRIDES

    def add_override(self, key: str, override: OverrideEntry) -> None:
        """Add a new override entry"""
        self.overrides[key] = override
        logger.info(f"Added override for key: {key}")

    def remove_override(self, key: str) -> bool:
        """Remove an override entry"""
        if key in self.overrides:
            del self.overrides[key]
            logger.info(f"Removed override for key: {key}")
            return True
        return False

    def get_override(self, keywords: List[str]) -> OverrideEntry | None:
        """Find matching override for given keywords"""
        keywords_lower = [k.lower() for k in keywords]

        # Check for exact matches first
        for key, override in self.overrides.items():
            override_keywords_lower = [k.lower() for k in override.keywords]
            if any(kw in keywords_lower for kw in override_keywords_lower):
                logger.info(
                    f"Found override match for keywords {keywords} using key {key}"
                )
                return override

        return None

    def list_overrides(self) -> Dict[str, List[str]]:
        """List all available overrides with their keywords"""
        return {key: override.keywords for key, override in self.overrides.items()}

    def apply_overrides(
        self, keywords: List[str], found_programs: List[AffiliateProgram]
    ) -> List[AffiliateProgram]:
        """Apply overrides to search results"""
        override = self.get_override(keywords)
        if not override:
            return found_programs

        if override.replace_all:
            logger.info(
                f"Replacing all results with override programs for keywords: {keywords}"
            )
            return override.forced_programs
        else:
            # Add override programs to existing results, avoiding duplicates
            combined_programs = list(found_programs)
            existing_names = {p.name.lower() for p in found_programs}

            for override_program in override.forced_programs:
                if override_program.name.lower() not in existing_names:
                    combined_programs.append(override_program)

            logger.info(
                f"Added {len(override.forced_programs)} override programs to {len(found_programs)} found programs"
            )
            return combined_programs


# Global override manager instance
override_manager = OverrideManager()
