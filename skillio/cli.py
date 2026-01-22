"""
Skillio CLI - Main entry point

Usage:
    skillio search "I want to download YouTube videos"
    skillio install video-downloader
    skillio list
    skillio info video-downloader
"""

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown

from skillio.core.search import search_skills, get_skill_info
from skillio.core.install import (
    install_skill, 
    list_installed, 
    remove_skill,
    detect_ai_environments
)

console = Console()


@click.group()
@click.version_option(version="0.1.0", prog_name="skillio")
def main():
    """Skillio - AI Agent's capability discovery and assembly hub.
    
    Find and install AI skills using natural language.
    
    Example:
        skillio search "download YouTube video"
        skillio install video-downloader
    """
    pass


@main.command()
@click.argument("query")
@click.option("--keyword", "-k", is_flag=True, help="Use keyword search instead of intent matching")
@click.option("--limit", "-n", default=5, help="Number of results to show")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def search(query: str, keyword: bool, limit: int, as_json: bool):
    """Search for skills using natural language.
    
    Examples:
        skillio search "I want to download videos"
        skillio search "PDF to Word"
        skillio search --keyword video
    """
    console.print(f"\n🔍 Searching for: [bold cyan]{query}[/bold cyan]\n")
    
    results = search_skills(query, keyword_mode=keyword, limit=limit)
    
    if not results:
        console.print("[yellow]No matching skills found.[/yellow]")
        console.print("Try different keywords or check the full skill list with: skillio list --all")
        return
    
    if as_json:
        import json
        click.echo(json.dumps(results, indent=2))
        return
    
    # Display results
    table = Table(title=f"Found {len(results)} matching skills")
    table.add_column("Skill", style="cyan", no_wrap=True)
    table.add_column("Description", style="white")
    table.add_column("Score", justify="right", style="green")
    table.add_column("Source", style="dim")
    
    for skill in results:
        table.add_row(
            skill["name"],
            skill["description"][:50] + "..." if len(skill["description"]) > 50 else skill["description"],
            f"{skill.get('match_score', 0):.1f}",
            skill.get("source", {}).get("repo", "N/A")
        )
    
    console.print(table)
    
    # Show recommended action
    if results:
        top_skill = results[0]["name"]
        console.print(f"\n💡 [bold]Recommended:[/bold] skillio install {top_skill}")


@main.command()
@click.argument("skill_name")
@click.option("--target", "-t", default=None, help="Installation target directory")
@click.option("--force", "-f", is_flag=True, help="Force reinstall if already installed")
@click.option("--no-seekers", is_flag=True, help="Skip skill-seekers, use simple generation")
@click.option("--no-enhance", is_flag=True, help="Skip AI enhancement step")
@click.option("--scope", type=click.Choice(["project", "global"]), default=None, 
              help="Install scope: project (.cursor/skills/) or global (~/.cursor/skills/)")
def install(skill_name: str, target: str, force: bool, no_seekers: bool, no_enhance: bool, scope: str):
    """Install a skill using skill-seekers for high-quality generation.
    
    Examples:
        skillio install video-downloader
        skillio install video-downloader --scope project
        skillio install video-downloader --no-seekers
        skillio install video-downloader --target ~/.cursor/skills/
    """
    # Get skill info first
    skill_info = get_skill_info(skill_name)
    if not skill_info:
        console.print(f"\n❌ [bold red]Skill not found:[/bold red] {skill_name}")
        console.print("Try: skillio search to find available skills")
        return
    
    source = skill_info.get("source", {})
    repo = source.get("repo", "N/A")
    
    console.print(f"\n📦 Installing skill: [bold cyan]{skill_name}[/bold cyan]")
    console.print(f"   Source: [dim]{source.get('type', 'unknown')}[/dim] - [dim]{repo}[/dim]")
    
    # Determine target based on scope
    if scope and not target:
        envs = detect_ai_environments()
        for env in envs:
            if env["scope"] == scope and env["type"] == "cursor":
                target = str(env["path"])
                break
    
    # Show installation method
    if no_seekers:
        console.print("   Method: [yellow]Simple (SKILL.md only)[/yellow]")
    else:
        console.print("   Method: [green]skill-seekers (full Skill with docs & scripts)[/green]")
        if not no_enhance:
            console.print("   Enhancement: [green]AI-enhanced[/green]")
    
    console.print("")
    
    try:
        with console.status("[bold green]Generating skill...", spinner="dots"):
            result = install_skill(
                skill_name, 
                target=target, 
                force=force,
                use_skill_seekers=not no_seekers,
                enhance=not no_enhance
            )
        
        if result["success"]:
            console.print(f"✅ [bold green]Successfully installed {skill_name}![/bold green]")
            console.print(f"   Location: {result['path']}")
            console.print(f"   Method: {result.get('method', 'unknown')}")
            
            # Show generated contents
            contents = result.get("contents", [])
            if contents:
                console.print(f"\n📁 [bold]Generated files:[/bold]")
                for item in contents[:10]:
                    console.print(f"   ├── {item}")
                if len(contents) > 10:
                    console.print(f"   └── ... and {len(contents) - 10} more files")
            
            # Show usage hint
            if skill_info.get("scenarios"):
                console.print(f"\n💡 [bold]Try it:[/bold]")
                for scenario in skill_info["scenarios"][:2]:
                    console.print(f"   - {scenario}")
        else:
            console.print(f"\n❌ [bold red]Installation failed:[/bold red] {result.get('error', 'Unknown error')}")
            
            # Suggest fallback
            if "skill-seekers" in result.get("error", ""):
                console.print("\n💡 [bold]Tip:[/bold] Try with --no-seekers flag for simple installation")
    except Exception as e:
        console.print(f"\n❌ [bold red]Error:[/bold red] {str(e)}")


@main.command()
@click.option("--all", "show_all", is_flag=True, help="Show all available skills")
@click.option("--category", "-c", default=None, help="Filter by category")
def list(show_all: bool, category: str):
    """List installed skills.
    
    Examples:
        skillio list
        skillio list --all
        skillio list --category media
    """
    if show_all:
        console.print("\n📚 [bold]All Available Skills[/bold]\n")
        from skillio.core.search import get_all_skills
        skills = get_all_skills(category=category)
    else:
        console.print("\n📦 [bold]Installed Skills[/bold]\n")
        skills = list_installed()
    
    if not skills:
        if show_all:
            console.print("[yellow]No skills found in the index.[/yellow]")
        else:
            console.print("[yellow]No skills installed yet.[/yellow]")
            console.print("Try: skillio search \"your need\" to find skills")
        return
    
    table = Table()
    table.add_column("Skill", style="cyan")
    table.add_column("Version", style="dim")
    table.add_column("Description", style="white")
    
    for skill in skills:
        table.add_row(
            skill["name"],
            skill.get("version", "N/A"),
            skill["description"][:60] + "..." if len(skill["description"]) > 60 else skill["description"]
        )
    
    console.print(table)
    console.print(f"\nTotal: {len(skills)} skills")


@main.command()
@click.argument("skill_name")
def info(skill_name: str):
    """Show detailed information about a skill.
    
    Example:
        skillio info video-downloader
    """
    skill = get_skill_info(skill_name)
    
    if not skill:
        console.print(f"\n❌ [bold red]Skill not found:[/bold red] {skill_name}")
        console.print("Try: skillio search to find available skills")
        return
    
    # Build info panel
    info_text = f"""
# {skill['name']} v{skill.get('version', 'N/A')}

{skill['description']}

## Capabilities
{chr(10).join('- ' + cap for cap in skill.get('capabilities', []))}

## Usage Scenarios
{chr(10).join('- ' + s for s in skill.get('scenarios', [])[:5])}

## Source
- Type: {skill.get('source', {}).get('type', 'N/A')}
- Repo: {skill.get('source', {}).get('repo', 'N/A')}

## Dependencies
{chr(10).join('- ' + dep for dep in skill.get('dependencies', [])) or '- None'}

## Quality Score: {skill.get('quality_score', 'N/A')}/10
"""
    
    console.print(Panel(Markdown(info_text), title=f"Skill: {skill_name}", border_style="cyan"))


@main.command()
@click.argument("skill_name")
@click.option("--force", "-f", is_flag=True, help="Force remove without confirmation")
def remove(skill_name: str, force: bool):
    """Remove an installed skill.
    
    Example:
        skillio remove video-downloader
    """
    if not force:
        if not click.confirm(f"Are you sure you want to remove {skill_name}?"):
            console.print("Cancelled.")
            return
    
    try:
        result = remove_skill(skill_name)
        if result["success"]:
            console.print(f"\n✅ [bold green]Successfully removed {skill_name}[/bold green]")
        else:
            console.print(f"\n❌ [bold red]Failed to remove:[/bold red] {result.get('error', 'Unknown error')}")
    except Exception as e:
        console.print(f"\n❌ [bold red]Error:[/bold red] {str(e)}")


@main.command()
def categories():
    """Show available skill categories."""
    from skillio.core.search import get_categories
    
    cats = get_categories()
    
    console.print("\n📁 [bold]Skill Categories[/bold]\n")
    
    table = Table()
    table.add_column("Category", style="cyan")
    table.add_column("Count", justify="right", style="green")
    table.add_column("Examples", style="dim")
    
    for cat in cats:
        table.add_row(
            cat["name"],
            str(cat["count"]),
            ", ".join(cat["examples"][:3])
        )
    
    console.print(table)


@main.command()
def environments():
    """Detect and show available AI environments for skill installation."""
    
    envs = detect_ai_environments()
    
    console.print("\n🔍 [bold]Detected AI Environments[/bold]\n")
    
    table = Table()
    table.add_column("#", style="dim", width=3)
    table.add_column("Type", style="cyan")
    table.add_column("Scope", style="yellow")
    table.add_column("Path", style="white")
    table.add_column("Status", style="green")
    
    for i, env in enumerate(envs, 1):
        status = "✓ exists" if env.get("exists") else "○ will create"
        table.add_row(
            str(i),
            env["type"],
            env["scope"],
            str(env["path"]),
            status
        )
    
    console.print(table)
    
    # Show recommendation
    if envs:
        recommended = envs[0]
        console.print(f"\n💡 [bold]Recommended:[/bold] {recommended['type']} ({recommended['scope']})")
        console.print(f"   Path: {recommended['path']}")
        console.print(f"\n   Use: skillio install <skill> --scope {recommended['scope']}")


if __name__ == "__main__":
    main()
