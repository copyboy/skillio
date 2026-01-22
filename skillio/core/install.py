"""
Skillio Installation Module

Handles skill installation, removal, and management.
Integrates with skill-seekers for high-quality Skill generation.
"""

import os
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, List

from skillio.core.search import get_skill_info


def _get_default_install_path() -> Path:
    """Get the default skill installation path.
    
    Priority:
    1. SKILLIO_INSTALL_PATH env var
    2. Project-level .cursor/skills/ (if in a Cursor project)
    3. ~/.cursor/skills/ (Cursor IDE global)
    4. ~/.skillio/skills/ (standalone)
    """
    # Check env var
    env_path = os.environ.get("SKILLIO_INSTALL_PATH")
    if env_path:
        return Path(env_path)
    
    # Check for project-level Cursor directory
    project_root = _find_project_root()
    if project_root:
        project_cursor = project_root / ".cursor" / "skills"
        if project_cursor.exists() or (project_root / ".cursor").exists():
            return project_cursor
    
    # Check for Cursor global skills directory
    cursor_path = Path.home() / ".cursor" / "skills"
    if cursor_path.exists():
        return cursor_path
    
    # Default to skillio directory
    return Path.home() / ".skillio" / "skills"


def _find_project_root() -> Optional[Path]:
    """Find the project root by looking for .git or .cursor directory."""
    cwd = Path.cwd()
    
    for parent in [cwd] + list(cwd.parents):
        if (parent / ".git").exists() or (parent / ".cursor").exists():
            return parent
    
    return None


def detect_ai_environments() -> List[dict]:
    """Detect available AI environments for skill installation.
    
    Returns:
        List of detected environments with type, scope, and path.
    """
    environments = []
    
    # 1. Check project-level directories
    project_root = _find_project_root()
    if project_root:
        # Cursor project
        cursor_project = project_root / ".cursor" / "skills"
        if cursor_project.exists():
            environments.append({
                "type": "cursor",
                "scope": "project",
                "path": cursor_project,
                "exists": True
            })
        elif (project_root / ".cursor").exists():
            environments.append({
                "type": "cursor",
                "scope": "project", 
                "path": cursor_project,
                "exists": False
            })
        
        # Windsurf project
        windsurf_project = project_root / ".windsurf" / "skills"
        if (project_root / ".windsurf").exists():
            environments.append({
                "type": "windsurf",
                "scope": "project",
                "path": windsurf_project,
                "exists": windsurf_project.exists()
            })
    
    # 2. Check global directories
    # Cursor global
    cursor_global = Path.home() / ".cursor" / "skills"
    if cursor_global.parent.exists():
        environments.append({
            "type": "cursor",
            "scope": "global",
            "path": cursor_global,
            "exists": cursor_global.exists()
        })
    
    # Claude Desktop (macOS)
    claude_path = Path.home() / "Library" / "Application Support" / "Claude"
    if claude_path.exists():
        environments.append({
            "type": "claude_desktop",
            "scope": "global",
            "path": claude_path / "skills",
            "exists": (claude_path / "skills").exists()
        })
    
    # Continue (VSCode extension)
    continue_path = Path.home() / ".continue" / "skills"
    if continue_path.parent.exists():
        environments.append({
            "type": "continue",
            "scope": "global",
            "path": continue_path,
            "exists": continue_path.exists()
        })
    
    # 3. Standalone fallback
    skillio_path = Path.home() / ".skillio" / "skills"
    environments.append({
        "type": "standalone",
        "scope": "global",
        "path": skillio_path,
        "exists": skillio_path.exists()
    })
    
    return environments


def _check_skill_seekers() -> bool:
    """Check if skill-seekers is installed."""
    return shutil.which("skill-seekers") is not None


def _install_skill_seekers() -> bool:
    """Install skill-seekers package."""
    try:
        subprocess.run(
            ["pip", "install", "skill-seekers"],
            check=True,
            capture_output=True
        )
        return True
    except subprocess.CalledProcessError:
        return False


def _get_installed_skills_registry() -> Path:
    """Get path to installed skills registry."""
    return _get_default_install_path().parent / "installed_skills.json"


def _load_installed_registry() -> dict:
    """Load the installed skills registry."""
    registry_path = _get_installed_skills_registry()
    
    if not registry_path.exists():
        return {"skills": {}}
    
    with open(registry_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_installed_registry(registry: dict):
    """Save the installed skills registry."""
    registry_path = _get_installed_skills_registry()
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(registry_path, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2)


def install_skill(
    skill_name: str,
    target: Optional[str] = None,
    force: bool = False,
    use_skill_seekers: bool = True,
    enhance: bool = True
) -> dict:
    """Install a skill.
    
    For GitHub-sourced skills, uses skill-seekers to generate high-quality
    Skill with documentation, scripts, and references.
    
    Args:
        skill_name: Name of the skill to install
        target: Custom installation directory
        force: Force reinstall if already installed
        use_skill_seekers: Use skill-seekers for GitHub sources (default: True)
        enhance: Run AI enhancement on generated Skill (default: True)
    
    Returns:
        Result dict with success status and details
    """
    # Get skill info from index
    skill = get_skill_info(skill_name)
    if not skill:
        return {
            "success": False,
            "error": f"Skill '{skill_name}' not found in index"
        }
    
    # Determine install path
    install_base = Path(target) if target else _get_default_install_path()
    skill_path = install_base / skill_name
    
    # Check if already installed
    registry = _load_installed_registry()
    if skill_name in registry["skills"] and not force:
        return {
            "success": False,
            "error": f"Skill '{skill_name}' is already installed. Use --force to reinstall."
        }
    
    # Remove existing if force reinstall
    if skill_path.exists() and force:
        shutil.rmtree(skill_path)
    
    source = skill.get("source", {})
    source_type = source.get("type", "")
    
    # For GitHub sources, use skill-seekers
    if source_type == "github" and use_skill_seekers:
        result = _install_with_skill_seekers(
            skill=skill,
            skill_path=skill_path,
            enhance=enhance
        )
        if not result["success"]:
            # Fallback to simple generation
            result = _install_simple(skill, skill_path)
    else:
        # For non-GitHub sources, use simple generation
        result = _install_simple(skill, skill_path)
    
    if not result["success"]:
        return result
    
    # Update registry
    registry["skills"][skill_name] = {
        "version": skill.get("version", "1.0.0"),
        "path": str(skill_path),
        "source": source,
        "installed_at": str(Path.cwd()),
        "method": result.get("method", "simple")
    }
    _save_installed_registry(registry)
    
    return {
        "success": True,
        "path": str(skill_path),
        "version": skill.get("version", "1.0.0"),
        "method": result.get("method", "simple"),
        "contents": result.get("contents", [])
    }


def _install_with_skill_seekers(
    skill: dict,
    skill_path: Path,
    enhance: bool = True
) -> dict:
    """Install a skill using skill-seekers for high-quality generation.
    
    Args:
        skill: Skill metadata dict
        skill_path: Target installation path
        enhance: Whether to run AI enhancement
    
    Returns:
        Result dict with success status
    """
    source = skill.get("source", {})
    repo = source.get("repo", "")
    skill_name = skill.get("name", "")
    
    if not repo:
        return {
            "success": False,
            "error": "No GitHub repo specified in skill source"
        }
    
    # Check/install skill-seekers
    if not _check_skill_seekers():
        if not _install_skill_seekers():
            return {
                "success": False,
                "error": "Failed to install skill-seekers. Please run: pip install skill-seekers"
            }
    
    # Create temp directory for generation
    with tempfile.TemporaryDirectory() as temp_dir:
        # skill-seekers outputs to ./output/ by default
        work_dir = Path(temp_dir)
        
        try:
            # Step 1: Generate skill from GitHub
            # skill-seekers github --repo owner/repo --name skill-name
            cmd = [
                "skill-seekers", "github",
                "--repo", repo,
                "--name", skill_name,
                "--non-interactive"  # Fail fast on rate limits
            ]
            
            # Add enhance flag if requested
            if enhance:
                cmd.append("--enhance-local")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minutes timeout
                cwd=str(work_dir)  # Run in temp directory
            )
            
            # skill-seekers outputs to ./output/<name>/
            output_dir = work_dir / "output" / skill_name
            
            # Also check for repo-based naming (e.g., output/yt-dlp/)
            if not output_dir.exists():
                # Try to find any output directory
                output_base = work_dir / "output"
                if output_base.exists():
                    for item in output_base.iterdir():
                        if item.is_dir() and item.name != "__pycache__":
                            output_dir = item
                            break
            
            if result.returncode != 0 and not output_dir.exists():
                error_msg = result.stderr or result.stdout or "Unknown error"
                return {
                    "success": False,
                    "error": f"skill-seekers failed: {error_msg[:200]}"
                }
            
            if not output_dir.exists():
                return {
                    "success": False,
                    "error": "skill-seekers did not generate output directory"
                }
            
            # Step 2: Move to target location
            skill_path.parent.mkdir(parents=True, exist_ok=True)
            
            if skill_path.exists():
                shutil.rmtree(skill_path)
            
            shutil.move(str(output_dir), str(skill_path))
            
            # List generated contents
            contents = []
            for item in skill_path.rglob("*"):
                if item.is_file():
                    contents.append(str(item.relative_to(skill_path)))
            
            return {
                "success": True,
                "method": "skill-seekers",
                "contents": sorted(contents)[:20]  # Limit to first 20 files
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "skill-seekers timed out (10min). Try with --no-seekers flag."
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"skill-seekers error: {str(e)}"
            }


def _install_simple(skill: dict, skill_path: Path) -> dict:
    """Simple installation - generates basic SKILL.md only.
    
    Used as fallback when skill-seekers is unavailable or fails.
    """
    try:
        skill_path.mkdir(parents=True, exist_ok=True)
        
        # Generate SKILL.md
        skill_md_content = _generate_skill_md(skill)
        skill_md_path = skill_path / "SKILL.md"
        
        with open(skill_md_path, "w", encoding="utf-8") as f:
            f.write(skill_md_content)
        
        return {
            "success": True,
            "method": "simple",
            "contents": ["SKILL.md"]
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def _generate_skill_md(skill: dict) -> str:
    """Generate SKILL.md content for a skill."""
    
    # Build capabilities list
    capabilities = "\n".join(f"- {cap}" for cap in skill.get("capabilities", []))
    
    # Build scenarios list
    scenarios = "\n".join(f"- {s}" for s in skill.get("scenarios", []))
    
    # Build dependencies
    deps = skill.get("dependencies", [])
    deps_section = ""
    if deps:
        deps_list = "\n".join(f"- {d}" for d in deps)
        deps_section = f"""
## Prerequisites

{deps_list}
"""
    
    # Get source info
    source = skill.get("source", {})
    source_type = source.get("type", "unknown")
    source_info = ""
    
    if source_type == "github":
        repo = source.get("repo", "")
        source_info = f"""
## Source

- GitHub: https://github.com/{repo}
- Type: {source_type}
"""
    
    content = f"""---
name: {skill['name']}
description: {skill['description']}
---

# {skill['name']}

{skill['description']}

{skill.get('description_zh', '')}

## Capabilities

{capabilities}

## Usage Scenarios

{scenarios}
{deps_section}{source_info}
## Quick Start

```bash
# Installation handled by Skillio
skillio install {skill['name']}
```

## Notes

- Quality Score: {skill.get('quality_score', 'N/A')}/10
- License: {skill.get('license', 'Unknown')}

---

*Generated by Skillio v0.1.0*
"""
    
    return content


def list_installed() -> list:
    """List all installed skills.
    
    Returns:
        List of installed skill info dicts
    """
    registry = _load_installed_registry()
    
    installed = []
    for name, info in registry.get("skills", {}).items():
        # Get full skill info
        skill = get_skill_info(name)
        if skill:
            skill["installed_path"] = info.get("path")
            installed.append(skill)
        else:
            # Skill removed from index but still installed
            installed.append({
                "name": name,
                "version": info.get("version", "unknown"),
                "description": "(Skill removed from index)",
                "installed_path": info.get("path")
            })
    
    return installed


def remove_skill(skill_name: str) -> dict:
    """Remove an installed skill.
    
    Args:
        skill_name: Name of the skill to remove
    
    Returns:
        Result dict with success status
    """
    registry = _load_installed_registry()
    
    if skill_name not in registry.get("skills", {}):
        return {
            "success": False,
            "error": f"Skill '{skill_name}' is not installed"
        }
    
    skill_info = registry["skills"][skill_name]
    skill_path = Path(skill_info.get("path", ""))
    
    # Remove skill directory
    if skill_path.exists():
        shutil.rmtree(skill_path)
    
    # Update registry
    del registry["skills"][skill_name]
    _save_installed_registry(registry)
    
    return {"success": True}
