"""
LMS Registry
Configuration module mapping subject code prefixes to specific Moodle portal URLs.
"""
import logging
from typing import Dict
from app.core.config import settings

logger = logging.getLogger(__name__)

# Registry mapping department subject code prefixes to their LMS instances
LMS_REGISTRY: Dict[str, str] = {
    "AI": "https://lms2.ai.saveetha.in",
    "CS": "https://lms2.cse.saveetha.in",
    "EE": "https://lms2.eee.saveetha.in",
    # MoodleCloud instance for general/fallback testing
    "TEST": "https://saveetha-exam-middleware.moodlecloud.com"
}

def get_lms_prefix(subject_code: str) -> str:
    """Extract department prefix from subject code (e.g. 19AI405 -> AI)."""
    if not subject_code:
        return "DEFAULT"
        
    code_upper = subject_code.upper()
    for prefix in LMS_REGISTRY.keys():
        if prefix in code_upper:
            return prefix
            
    return "DEFAULT"

def get_lms_url(subject_code: str) -> str:
    """Get the appropriate LMS URL based on the subject code prefix."""
    prefix = get_lms_prefix(subject_code)
    
    if prefix in LMS_REGISTRY:
        url = LMS_REGISTRY[prefix]
        logger.debug(f"Routing subject {subject_code} to LMS: {url}")
        return url
        
    # Fallback to the default configured Moodle URL
    logger.debug(f"No specific LMS mapping for {subject_code}, using default: {settings.moodle_base_url}")
    return settings.moodle_base_url

def get_all_registered_portals() -> Dict[str, str]:
    """Return all registered portals plus the default one."""
    portals = {"DEFAULT": settings.moodle_base_url}
    portals.update(LMS_REGISTRY)
    return portals
