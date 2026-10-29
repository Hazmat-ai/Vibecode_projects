"""Deterministic dependency graph; no optional library changes its semantics."""

def validate_dependencies(skills):
    # Iterative topological validation avoids recursive overflow on imported graphs.
    indegree = {key: len(skill.requires) for key, skill in skills.items()}
    children = {key: [] for key in skills}
    for key, skill in skills.items():
        for required in skill.requires:
            if required not in skills:
                raise ValueError("Unknown prerequisite '{}' for '{}'".format(required, key))
            children[required].append(key)
    ready = sorted(key for key, count in indegree.items() if count == 0)
    visited = 0
    while ready:
        key = ready.pop()
        visited += 1
        for child in children[key]:
            indegree[child] -= 1
            if indegree[child] == 0:
                ready.append(child)
    if visited != len(skills):
        raise ValueError("Skill dependencies contain a cycle.")

class SkillGraph:
    def __init__(self, db):
        self._db = db
        self.reload()

    def reload(self):
        self._skills = {s.id: s for s in self._db.all_skills()}
        validate_dependencies(self._skills)
        self._forward = {key: [] for key in self._skills}
        self._reverse = {key: list(s.requires) for key, s in self._skills.items()}
        for key, requirements in self._reverse.items():
            for required in requirements:
                self._forward[required].append(key)
        for children in self._forward.values():
            children.sort()

    def get_skill(self, skill_id):
        return self._skills.get(skill_id)

    def get_dependents(self, skill_id):
        return list(self._forward.get(skill_id, []))

    def get_unlockable(self, known):
        return sorted((s for s in self._skills.values() if s.id not in known and set(s.requires) <= set(known)), key=lambda s: (-s.civilization_score, s.id))

    def get_blocking(self, target_id, known):
        target = self.get_skill(target_id)
        if target is None:
            raise ValueError("Unknown skill: " + target_id)
        return [self._skills[key] for key in target.requires if key not in known]

    def shortest_path(self, known, target_id):
        if target_id not in self._skills:
            raise ValueError("Unknown skill: " + target_id)
        needed, pending = set(), [target_id]
        while pending:
            key = pending.pop()
            if key in known or key in needed:
                continue
            needed.add(key)
            pending.extend(self._reverse[key])
        import heapq
        indegree = {key: sum(req in needed for req in self._reverse[key]) for key in needed}
        ready = [key for key, count in indegree.items() if count == 0]
        heapq.heapify(ready)
        ordered = []
        while ready:
            key = heapq.heappop(ready)
            ordered.append(self._skills[key])
            for child in self._forward[key]:
                if child in indegree:
                    indegree[child] -= 1
                    if indegree[child] == 0:
                        heapq.heappush(ready, child)
        if len(ordered) != len(needed):
            raise ValueError("Unresolvable dependency graph.")
        return ordered

    def all_skills(self):
        return sorted(self._skills.values(), key=lambda s: s.id)
