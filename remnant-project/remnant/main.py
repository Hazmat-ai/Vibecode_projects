"""
main.py — CLI entry point for REMNANT. Uses stdlib argparse only.
Exit codes: 0 success, 1 user error, 2 internal error, 3 not found.
"""

import sys
import os
import argparse

# Ensure the remnant package directory is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import DEFAULT_DB_PATH, EXIT_NOT_FOUND, EXIT_USER_ERROR, EXIT_INTERNAL_ERROR, DOMAINS
from core.db import Database


# ------------------------------------------------------------------ #
#  Helpers                                                             #
# ------------------------------------------------------------------ #

def _open_db(args) -> Database:
    import atexit
    db = Database(getattr(args, "db", DEFAULT_DB_PATH))
    atexit.register(db.close)
    return db


def positive_limit(value):
    number = int(value)
    if not 1 <= number <= 1000:
        raise argparse.ArgumentTypeError("Limit must be between 1 and 1000.")
    return number


def _get_ui(args):
    from ui import get_ui
    return get_ui(getattr(args, "ui", None))


def _dict_to_article(data: dict, custom: bool = False):
    from core.models import Article
    from datetime import date
    lu = data.get("last_updated")
    if isinstance(lu, str):
        try:
            lu = date.fromisoformat(lu)
        except ValueError:
            lu = None
    return Article(
        id=data["id"],
        title=data["title"],
        domain=data.get("domain", "other"),
        tags=data.get("tags") or [],
        civilization_score=int(data.get("civilization_score", 50)),
        difficulty=int(data.get("difficulty", 3)),
        requires_skills=data.get("requires_skills") or [],
        summary=(data.get("summary") or "").strip(),
        content=(data.get("content") or "").strip(),
        sources=data.get("sources") or [],
        last_updated=lu,
        custom=custom,
    )


# ------------------------------------------------------------------ #
#  library handlers                                                    #
# ------------------------------------------------------------------ #

def cmd_library_search(args):
    db = _open_db(args)
    ui = _get_ui(args)
    from core.search import search_library
    results = search_library(db, args.query, domain=args.domain, limit=args.limit, min_cs=args.min_cs)
    if not results:
        ui.show_error(f"No results for '{args.query}'")
        sys.exit(EXIT_NOT_FOUND)
    ui.show_article_list(results, title=f"Search: '{args.query}'")


def cmd_library_read(args):
    db = _open_db(args)
    ui = _get_ui(args)
    from library.engine import get_article
    article = get_article(db, args.id_or_title)
    if not article:
        ui.show_error(f"Article not found: '{args.id_or_title}'")
        sys.exit(EXIT_NOT_FOUND)
    ui.show_article(article)


def cmd_library_top(args):
    db = _open_db(args)
    ui = _get_ui(args)
    from library.engine import top_articles
    articles = top_articles(db, limit=args.limit, domain=args.domain)
    title = f"Top {args.limit} Articles" + (f" [{args.domain}]" if args.domain else "")
    ui.show_article_list(articles, title=title)


def cmd_library_add(args):
    db = _open_db(args)
    ui = _get_ui(args)
    try:
        from core.yaml_loader import load_file
        data = load_file(args.file)
        article = _dict_to_article(data, custom=True)
        added = db.insert_article(article)
        if added:
            ui.show_success(f"Article '{article.id}' added.")
        else:
            ui.show_error(f"Article '{article.id}' already exists.")
            sys.exit(EXIT_USER_ERROR)
    except Exception as e:
        ui.show_error(f"Failed to import article: {e}")
        sys.exit(EXIT_USER_ERROR)


def cmd_library_export(args):
    db = _open_db(args)
    ui = _get_ui(args)
    from library.engine import get_article
    from library.exporter import export_article
    article = get_article(db, args.id)
    if not article:
        ui.show_error(f"Article not found: '{args.id}'")
        sys.exit(EXIT_NOT_FOUND)
    text = export_article(article, fmt=args.format, output_path=args.output)
    if not args.output:
        print(text)
    else:
        ui.show_success(f"Exported to {args.output}")


# ------------------------------------------------------------------ #
#  tree handlers                                                       #
# ------------------------------------------------------------------ #

def cmd_tree_show(args):
    db = _open_db(args)
    ui = _get_ui(args)
    from skilltree.graph import SkillGraph
    graph = SkillGraph(db)
    known = set()
    if args.community:
        c = db.get_community(args.community)
        if c:
            known = set(c.known_skills)
    if args.domain:
        from skilltree.renderer import render_tree
        from ui.prompts import print_line
        print_line(render_tree(graph, known, domain=args.domain))
    else:
        ui.show_tree(graph, known)


def cmd_tree_next(args):
    db = _open_db(args)
    ui = _get_ui(args)
    from skilltree.graph import SkillGraph
    c = db.get_community(args.community)
    if not c:
        _get_ui(args).show_error(f"Community '{args.community}' not found.")
        sys.exit(EXIT_NOT_FOUND)
    graph = SkillGraph(db)
    unlockable = graph.get_unlockable(set(c.known_skills))[:args.limit]
    ui.show_skill_list(unlockable, title=f"Unlockable skills for '{c.name}'")


def cmd_tree_path(args):
    db = _open_db(args)
    ui = _get_ui(args)
    from skilltree.graph import SkillGraph
    known = set()
    if args.community:
        c = db.get_community(args.community)
        if c:
            known = set(c.known_skills)
    graph = SkillGraph(db)
    if not graph.get_skill(args.skill):
        ui.show_error(f"Skill '{args.skill}' not found.")
        sys.exit(EXIT_NOT_FOUND)
    path = graph.shortest_path(known, args.skill)
    if not path:
        ui.show_success(f"'{args.skill}' is already known by this community.")
    else:
        ui.show_skill_list(path, title=f"Path to unlock '{args.skill}'")


def cmd_tree_learn(args):
    db = _open_db(args)
    ui = _get_ui(args)
    from skilltree.community import learn_skill
    try:
        learned = learn_skill(db, args.community, args.skill)
        if learned:
            ui.show_success(f"Community '{args.community}' learned '{args.skill}'.")
        else:
            ui.show_error(f"Skill '{args.skill}' was already known.")
    except ValueError as e:
        ui.show_error(str(e))
        sys.exit(EXIT_USER_ERROR)


def cmd_tree_unlearn(args):
    db = _open_db(args)
    ui = _get_ui(args)
    from skilltree.community import unlearn_skill
    try:
        removed = unlearn_skill(db, args.community, args.skill)
        if removed:
            ui.show_success(f"Skill '{args.skill}' removed from '{args.community}'.")
        else:
            ui.show_error(f"Skill '{args.skill}' was not known.")
    except ValueError as e:
        ui.show_error(str(e))
        sys.exit(EXIT_USER_ERROR)


# ------------------------------------------------------------------ #
#  community handlers                                                  #
# ------------------------------------------------------------------ #

def cmd_community_new(args):
    db = _open_db(args)
    ui = _get_ui(args)
    from skilltree.community import create_community
    try:
        c = create_community(db, args.name)
        ui.show_success(f"Community '{c.name}' created (id: '{c.id}').")
    except ValueError as e:
        ui.show_error(str(e))
        sys.exit(EXIT_USER_ERROR)


def cmd_community_list(args):
    db = _open_db(args)
    communities = db.list_communities()
    if not communities:
        print("No communities found. Create one with:  community new <NAME>")
        return
    print(f"{'ID':<25} {'Name':<30} Known skills")
    print("-" * 65)
    for c in communities:
        print(f"{c.id:<25} {c.name:<30} {len(c.known_skills)}")


# ------------------------------------------------------------------ #
#  sync handlers                                                       #
# ------------------------------------------------------------------ #

def cmd_sync_merge(args):
    db = _open_db(args)
    ui = _get_ui(args)
    from core.sync import merge_databases
    try:
        summary = merge_databases(db, args.source)
        ui.show_success(
            f"Merge complete: +{summary['articles_added']} articles, "
            f"+{summary['skills_added']} skills, "
            f"{summary['conflicts']} conflicts, "
            f"{summary['communities_merged']} communities updated."
        )
    except RuntimeError as e:
        ui.show_error(str(e))
        sys.exit(EXIT_INTERNAL_ERROR)


def cmd_sync_export(args):
    db = _open_db(args)
    try:
        db.backup(args.output)
        _get_ui(args).show_success("Database snapshot exported to " + args.output)
    finally:
        db.close()


# ------------------------------------------------------------------ #
#  Interactive menu                                                    #
# ------------------------------------------------------------------ #

def cmd_menu(args):
    db = _open_db(args)
    ui = _get_ui(args)
    choices = [
        "Search library",
        "Top articles by Civilization Score",
        "Show skill tree",
        "List communities",
        "Quit",
    ]
    while True:
        print("\n--- REMNANT Main Menu ---")
        idx = ui.prompt_choice(choices, "Select")
        if idx == 0:
            query = input("Search query: ").strip()
            from core.search import search_library
            results = search_library(db, query)
            ui.show_article_list(results, title=f"Results for '{query}'")
        elif idx == 1:
            from library.engine import top_articles
            articles = top_articles(db, limit=20)
            ui.show_article_list(articles, title="Top Articles")
        elif idx == 2:
            from skilltree.graph import SkillGraph
            graph = SkillGraph(db)
            ui.show_tree(graph, set())
        elif idx == 3:
            communities = db.list_communities()
            for c in communities:
                print(f"  {c.id}: {c.name} ({len(c.known_skills)} skills)")
            if not communities:
                print("  (none)")
        elif idx == 4 or idx == -1:
            print("Goodbye.")
            break


# ------------------------------------------------------------------ #
#  Parser construction                                                 #
# ------------------------------------------------------------------ #

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="remnant",
        description="REMNANT — Offline survival knowledge base and skill tree.",
    )
    parser.add_argument("--db", default=DEFAULT_DB_PATH, metavar="PATH", help="Path to remnant.db")
    parser.add_argument("--ui", choices=["plain", "tui"], default=None, help="Force UI mode")
    parser.set_defaults(func=cmd_menu)

    sub = parser.add_subparsers(title="commands")

    # ---- library ----
    lib = sub.add_parser("library", help="Browse and search the knowledge library.")
    lib.set_defaults(func=lambda args: lib.print_help())
    lib_sub = lib.add_subparsers(title="library commands")

    p_search = lib_sub.add_parser("search", help="Search the library.")
    p_search.add_argument("query")
    p_search.add_argument("--domain", choices=DOMAINS, default=None)
    p_search.add_argument("--limit", type=positive_limit, default=20)
    p_search.add_argument("--min-cs", dest="min_cs", type=int, default=0)
    p_search.set_defaults(func=cmd_library_search)

    p_read = lib_sub.add_parser("read", help="Read an article by ID or title.")
    p_read.add_argument("id_or_title")
    p_read.set_defaults(func=cmd_library_read)

    p_top = lib_sub.add_parser("top", help="List top articles by Civilization Score.")
    p_top.add_argument("--limit", type=positive_limit, default=20)
    p_top.add_argument("--domain", choices=DOMAINS, default=None)
    p_top.set_defaults(func=cmd_library_top)

    p_add = lib_sub.add_parser("add", help="Add a custom article from a YAML file.")
    p_add.add_argument("--file", required=True, metavar="PATH")
    p_add.set_defaults(func=cmd_library_add)

    p_export = lib_sub.add_parser("export", help="Export an article to txt or md.")
    p_export.add_argument("id")
    p_export.add_argument("--format", dest="format", choices=["txt", "md"], default="txt")
    p_export.add_argument("--output", default=None, metavar="PATH")
    p_export.set_defaults(func=cmd_library_export)

    # ---- tree ----
    tr = sub.add_parser("tree", help="Explore the civilization skill tree.")
    tr.set_defaults(func=lambda args: tr.print_help())
    tr_sub = tr.add_subparsers(title="tree commands")

    p_show = tr_sub.add_parser("show", help="Display the full skill tree.")
    p_show.add_argument("--community", default=None)
    p_show.add_argument("--domain", choices=DOMAINS, default=None)
    p_show.set_defaults(func=cmd_tree_show)

    p_next = tr_sub.add_parser("next", help="Show unlockable skills for a community.")
    p_next.add_argument("--community", required=True)
    p_next.add_argument("--limit", type=positive_limit, default=10)
    p_next.set_defaults(func=cmd_tree_next)

    p_path = tr_sub.add_parser("path", help="Show learning path to a skill.")
    p_path.add_argument("--skill", required=True)
    p_path.add_argument("--community", default=None)
    p_path.set_defaults(func=cmd_tree_path)

    p_learn = tr_sub.add_parser("learn", help="Mark a skill as known for a community.")
    p_learn.add_argument("--community", required=True)
    p_learn.add_argument("--skill", required=True)
    p_learn.set_defaults(func=cmd_tree_learn)

    p_unlearn = tr_sub.add_parser("unlearn", help="Remove a skill from a community's known set.")
    p_unlearn.add_argument("--community", required=True)
    p_unlearn.add_argument("--skill", required=True)
    p_unlearn.set_defaults(func=cmd_tree_unlearn)

    # ---- community ----
    com = sub.add_parser("community", help="Manage community profiles.")
    com.set_defaults(func=lambda args: com.print_help())
    com_sub = com.add_subparsers(title="community commands")

    p_cnew = com_sub.add_parser("new", help="Create a new community.")
    p_cnew.add_argument("name")
    p_cnew.set_defaults(func=cmd_community_new)

    p_clist = com_sub.add_parser("list", help="List all communities.")
    p_clist.set_defaults(func=cmd_community_list)

    # ---- sync ----
    sy = sub.add_parser("sync", help="Sync databases between communities (USB).")
    sy.set_defaults(func=lambda args: sy.print_help())
    sy_sub = sy.add_subparsers(title="sync commands")

    p_merge = sy_sub.add_parser("merge", help="Merge a remote database into local.")
    p_merge.add_argument("--source", required=True, metavar="PATH")
    p_merge.set_defaults(func=cmd_sync_merge)

    p_sexp = sy_sub.add_parser("export", help="Export local database for transport.")
    p_sexp.add_argument("--output", required=True, metavar="PATH")
    p_sexp.set_defaults(func=cmd_sync_export)

    return parser


# ------------------------------------------------------------------ #
#  Entry point                                                         #
# ------------------------------------------------------------------ #

def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="backslashreplace")
    parser = build_parser()
    args = parser.parse_args()

    # If a group command is called with no subcommand, print its help
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(EXIT_USER_ERROR)

    try:
        args.func(args)
    except (ValueError, RuntimeError, OSError) as error:
        print("Error: {}".format(error), file=sys.stderr)
        sys.exit(EXIT_USER_ERROR)
    except KeyboardInterrupt:
        print("\nCancelled.", file=sys.stderr)
        sys.exit(EXIT_USER_ERROR)


if __name__ == "__main__":
    main()
