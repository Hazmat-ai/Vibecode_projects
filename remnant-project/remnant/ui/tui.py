"""
ui/tui.py — Optional Textual TUI. Imports textual/rich inside functions.
Falls back gracefully if not installed.
"""


class TUI:
    """Rich terminal UI using textual (optional). Falls back to PlainUI if unavailable."""

    def __init__(self):
        from ui.plain import PlainUI
        self._fallback = PlainUI()
        try:
            import textual  # noqa: F401
            import rich  # noqa: F401
            self._available = True
        except ImportError:
            self._available = False
        if not self._available:
            from ui.plain import PlainUI
            self._fallback = PlainUI()

    def _rich_print(self, *args, **kwargs):
        try:
            from rich.console import Console
            Console().print(*args, **kwargs)
        except ImportError:
            from ui.prompts import print_line
            for a in args:
                print_line(str(a))

    def show_article(self, article) -> None:
        if not self._available:
            return self._fallback.show_article(article)
        try:
            from rich.panel import Panel
            from rich.markdown import Markdown
            from rich.console import Console
            from rich.text import Text
            console = Console()
            header = Text()
            header.append(f"CS: {article.civilization_score}/100 | ", style="bold green")
            header.append(f"Domain: {article.domain} | ", style="bold cyan")
            header.append(f"Difficulty: {'★' * article.difficulty}{'☆' * (5 - article.difficulty)}", style="bold yellow")
            console.print(Panel(Markdown(article.content), title=article.title, subtitle=str(header)))
        except Exception:
            self._fallback.show_article(article)

    def show_skill(self, skill) -> None:
        if not self._available:
            return self._fallback.show_skill(skill)
        try:
            from rich.panel import Panel
            from rich.console import Console
            console = Console()
            body = (
                f"[bold]Domain:[/] {skill.domain}\n"
                f"[bold]CS:[/] {skill.civilization_score}/100\n"
                f"[bold]Difficulty:[/] {skill.difficulty}/5\n"
                f"[bold]Time to learn:[/] {skill.time_to_learn_days} days\n"
                f"[bold]Requires:[/] {', '.join(skill.requires) or 'None'}\n\n"
                f"{skill.summary}"
            )
            console.print(Panel(body, title=f"[bold]{skill.title}[/]"))
        except Exception:
            self._fallback.show_skill(skill)

    def show_skill_list(self, skills: list, title: str = "Skills") -> None:
        if not self._available:
            return self._fallback.show_skill_list(skills, title)
        try:
            from rich.table import Table
            from rich.console import Console
            console = Console()
            table = Table(title=title, show_header=True, header_style="bold magenta")
            table.add_column("CS", style="green", width=4)
            table.add_column("Title")
            table.add_column("Domain", style="cyan")
            table.add_column("Difficulty", width=10)
            for s in skills:
                table.add_row(
                    str(s.civilization_score),
                    s.title,
                    s.domain,
                    '★' * s.difficulty + '☆' * (5 - s.difficulty),
                )
            console.print(table)
        except Exception:
            self._fallback.show_skill_list(skills, title)

    def show_article_list(self, articles: list, title: str = "Articles") -> None:
        if not self._available:
            return self._fallback.show_article_list(articles, title)
        try:
            from rich.table import Table
            from rich.console import Console
            console = Console()
            table = Table(title=title, show_header=True, header_style="bold blue")
            table.add_column("CS", style="green", width=4)
            table.add_column("Title")
            table.add_column("Domain", style="cyan")
            for a in articles:
                table.add_row(str(a.civilization_score), a.title, a.domain)
            console.print(table)
        except Exception:
            self._fallback.show_article_list(articles, title)

    def show_tree(self, graph, known: set) -> None:
        if not self._available:
            return self._fallback.show_tree(graph, known)
        from skilltree.renderer import render_tree
        self._rich_print(render_tree(graph, known))

    def prompt_choice(self, items: list, prompt: str = "Choose") -> int:
        from ui.prompts import prompt_choice
        return prompt_choice(items, prompt)

    def show_error(self, message: str) -> None:
        self._rich_print(f"[bold red][ERROR][/] {message}" if self._available else f"[ERROR] {message}")

    def show_success(self, message: str) -> None:
        self._rich_print(f"[bold green][OK][/] {message}" if self._available else f"[OK] {message}")
