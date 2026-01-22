"""
Skillio Search Engine

Handles intent understanding and skill matching.
"""

import os
import re
from pathlib import Path
from typing import Optional

import yaml


def _load_skills_index() -> list:
    """Load the skills index from YAML file."""
    index_path = Path(__file__).parent.parent / "index" / "skills.yaml"
    
    if not index_path.exists():
        return []
    
    with open(index_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    return data.get("skills", [])


def _calculate_match_score(skill: dict, query: str, keyword_mode: bool = False) -> float:
    """Calculate relevance score between a skill and query.
    
    In keyword mode, uses simple text matching.
    In intent mode, uses capability and scenario matching.
    """
    query_lower = query.lower()
    score = 0.0
    
    # Exact name match
    if skill["name"].lower() == query_lower:
        return 10.0
    
    # Name partial match
    if query_lower in skill["name"].lower():
        score += 5.0
    
    # Description match
    if query_lower in skill.get("description", "").lower():
        score += 2.0
    
    if query_lower in skill.get("description_zh", "").lower():
        score += 2.0
    
    # Split query into words
    query_words = set(re.findall(r'\w+', query_lower))
    
    # Capability matching (most important for intent mode)
    capabilities = [c.lower() for c in skill.get("capabilities", [])]
    for cap in capabilities:
        cap_words = set(re.findall(r'\w+', cap))
        overlap = len(query_words & cap_words)
        if overlap > 0:
            score += overlap * 1.5
    
    # Scenario matching
    scenarios = [s.lower() for s in skill.get("scenarios", [])]
    for scenario in scenarios:
        scenario_words = set(re.findall(r'\w+', scenario))
        overlap = len(query_words & scenario_words)
        if overlap > 0:
            score += overlap * 1.0
    
    # Tag matching
    tags = [t.lower() for t in skill.get("tags", [])]
    for tag in tags:
        if tag in query_lower or any(word in tag for word in query_words):
            score += 0.5
    
    # Quality score boost
    quality = skill.get("quality_score", 5.0)
    score *= (1 + (quality - 5) / 20)  # ±25% based on quality
    
    return round(score, 2)


def search_skills(
    query: str,
    keyword_mode: bool = False,
    limit: int = 5,
    min_score: float = 0.5
) -> list:
    """Search for skills matching the query.
    
    Args:
        query: Natural language query or keywords
        keyword_mode: If True, use simple keyword matching
        limit: Maximum number of results to return
        min_score: Minimum match score to include in results
    
    Returns:
        List of matching skills with match scores
    """
    skills = _load_skills_index()
    
    if not skills:
        return []
    
    # Calculate scores for all skills
    scored_skills = []
    for skill in skills:
        score = _calculate_match_score(skill, query, keyword_mode)
        if score >= min_score:
            skill_copy = skill.copy()
            skill_copy["match_score"] = score
            scored_skills.append(skill_copy)
    
    # Sort by score descending
    scored_skills.sort(key=lambda x: x["match_score"], reverse=True)
    
    return scored_skills[:limit]


def get_skill_info(skill_name: str) -> Optional[dict]:
    """Get detailed information about a specific skill.
    
    Args:
        skill_name: The name of the skill
    
    Returns:
        Skill information dict or None if not found
    """
    skills = _load_skills_index()
    
    for skill in skills:
        if skill["name"] == skill_name:
            return skill
    
    return None


def get_all_skills(category: Optional[str] = None) -> list:
    """Get all available skills, optionally filtered by category.
    
    Args:
        category: Filter by tag/category
    
    Returns:
        List of skills
    """
    skills = _load_skills_index()
    
    if category:
        category_lower = category.lower()
        skills = [
            s for s in skills
            if category_lower in [t.lower() for t in s.get("tags", [])]
        ]
    
    return skills


def get_categories() -> list:
    """Get all skill categories with counts.
    
    Returns:
        List of category info dicts
    """
    skills = _load_skills_index()
    
    # Collect all tags
    category_skills = {}
    for skill in skills:
        for tag in skill.get("tags", []):
            if tag not in category_skills:
                category_skills[tag] = []
            category_skills[tag].append(skill["name"])
    
    # Build category list
    categories = []
    for cat, skill_names in sorted(category_skills.items()):
        categories.append({
            "name": cat,
            "count": len(skill_names),
            "examples": skill_names[:5]
        })
    
    return categories
