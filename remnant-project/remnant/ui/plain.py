"""
ui/plain.py — Plain terminal interface. Stdlib only. Always available.
Implements UIProtocol defined in AGENT_CONTEXT.md.
"""

import sys
from ui.prompts import print_line, print_separator, prompt_choice


class PlainUI:
    """Minimal terminal UI using only Python stdlib."""

    def show_article(self, article) -> None:
        print_separator("=")
        print_line(f"  {article.title}")
        print_separator("=")
        print_line(f"  Domain: {article.domain}  |  CS: {article.civilization_score}/100  |  Difficulty: {article.difficulty}/5")
        print_line(f"  Tags: {', '.join(article.tags)}")
        print_separator()
        print_line(article.summary)
        print_separator()
        print_line(article.content)
        if article.sources:
            print_separator()
            print_line("Sources:")
            for s in article.sources:
                print_line(f"  - {s}")
        print_separator("=")

    def show_skill(self, skill) -> None:
        print_separator("=")
        print_line(f"  {skill.title}")
        print_separator("=")
        print_line(f"  Domain: {skill.domain}  |  CS: {skill.civilization_score}/100")
        print_line(f"  Requires: {', '.join(skill.requires) or 'None'}")
        print_line(f"  Unlocks: {', '.join(skill.unlocks) or 'None'}")
        print_line(f"  Time to learn: {skill.time_to_learn_days} days")
        print_separator()
        print_line(skill.summary)
        print_separator("=")

    def show_skill_list(self, skills: list, title: str = "Skills") -> None:
        print_separator("=")
        print_line(f"  {title}")
        print_separator("=")
        if not skills:
            print_line("  (none)")
        for skill in skills:
            print_line(f"  [{skill.civilization_score:3d}] {skill.title} ({skill.domain})")
        print_separator()

    def show_article_list(self, articles: list, title: str = "Articles") -> None:
        print_separator("=")
        print_line(f"  {title}")
        print_separator("=")
        if not articles:
            print_line("  (no results)")
        for a in articles:
            print_line(f"  [{a.civilization_score:3d}] {a.title} [{a.domain}]")
        print_separator()

    def show_tree(self, graph, known: set) -> None:
        from skilltree.renderer import render_tree
        print_line(render_tree(graph, known))

    def prompt_choice(self, items: list, prompt: str = "Choose") -> int:
        return prompt_choice(items, prompt)

    def show_error(self, message: str) -> None:
        print_line(f"[ERROR] {message}")

    def show_success(self, message: str) -> None:
        print_line(f"[OK] {message}")
