"""Bounded, iterative tree rendering; shared DAG branches are shown once."""
import sys
_UTF8 = bool(sys.stdout.encoding and sys.stdout.encoding.lower() in ('utf-8', 'utf8'))

def render_tree(graph, known, domain=None):
    skills = {s.id: s for s in graph.all_skills() if domain is None or s.domain == domain}
    roots = sorted((s for s in skills.values() if not any(req in skills for req in s.requires)), key=lambda s: (-s.civilization_score,s.id))
    lines = ['SKILL TREE', '=' * 50]
    stack = [(root.id,0) for root in reversed(roots)]
    seen = set()
    while stack and len(lines) < 2002:
        key,depth = stack.pop()
        skill = skills[key]
        prefix = '  ' * min(depth,20) + ('- ' if not _UTF8 else '• ')
        if key in seen:
            lines.append(prefix + skill.title + ' (shared prerequisite path; shown above)')
            continue
        seen.add(key)
        lines.append(prefix + ('[x] ' if key in known else '[ ] ') + skill.title + ' (CS:{})'.format(skill.civilization_score))
        children = sorted((child for child in graph.get_dependents(key) if child in skills), reverse=True)
        stack.extend((child,depth+1) for child in children)
    if stack:
        lines.append('(Output limited to 2,000 rows; narrow the domain.)')
    return '\n'.join(lines)
