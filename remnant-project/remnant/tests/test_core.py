import contextlib
import dataclasses
import io
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from core.db import Database
from core.models import Article, Skill, Community
from core.search import search_library
from core.sync import merge_databases
from core.yaml_loader import load
from skilltree.graph import SkillGraph
from skilltree.community import create_community, learn_skill, unlearn_skill
from library.scorer import compute_skill_cs
from scripts.seed_db import seed

def article(id='water', **kwargs):
    values=dict(id=id,title='Water collection',domain='other',tags=['water'],civilization_score=80,difficulty=1,requires_skills=[],summary='Collect rainwater.',content='Water collection example.',sources=['Example source'])
    values.update(kwargs)
    return Article(**values)

def skill(id='base',requires=None,**kwargs):
    values=dict(id=id,title=id,domain='other',civilization_score=70,requires=requires or [],unlocks=[],summary='Example skill.',difficulty=1,time_to_learn_days=1)
    values.update(kwargs)
    return Skill(**values)

class CoreTests(unittest.TestCase):
    def setUp(self):
        self.db=Database(':memory:')
        self.temp=tempfile.TemporaryDirectory()
    def tearDown(self):
        self.db.close()
        self.temp.cleanup()
    def remote(self):
        path=Path(self.temp.name)/'remote.db'
        return path,Database(str(path))

    def test_validation_blocks_bad_fields_and_terminal_sequences(self):
        for changes in [{'id':'../bad'},{'civilization_score':101},{'difficulty':0},{'tags':'water'},{'title':'\x1b[31mred'},{'title':'\x9b31mred'},{'content':''},{'custom':1}]:
            with self.assertRaises((ValueError,TypeError)):
                article(**changes)
        with self.assertRaises(ValueError):
            Community('', 'name')

    def test_fts_insert_update_delete_remains_consistent(self):
        self.db.insert_article(article(content='uniquewater token'))
        self.assertEqual(len(search_library(self.db,'uniquewater')),1)
        self.db.insert_article(article(content='replacementtoken text'),replace=True)
        self.assertEqual(search_library(self.db,'uniquewater'),[])
        self.assertEqual(len(search_library(self.db,'replacementtoken')),1)
        self.db.connection.execute('DELETE FROM articles WHERE id=?',('water',))
        self.db.connection.commit()
        self.assertEqual(search_library(self.db,'replacementtoken'),[])

    def test_search_literals_filters_and_fallback(self):
        self.db.insert_article(article('first',civilization_score=20))
        self.db.insert_article(article('second',domain='food',civilization_score=90))
        self.assertEqual([a.id for a in search_library(self.db,'water',limit=1,min_cs=80)],['second'])
        self.assertEqual([a.id for a in search_library(self.db,'wat',domain='food')],['second'])
        self.assertEqual(search_library(self.db,'   '),[])
        search_library(self.db,'" OR title: *')
        self.db.fts_available=False
        self.assertEqual(search_library(self.db,'%'),[])
        self.assertEqual(len(search_library(self.db,'Water')),2)

    def test_graph_paths_are_deterministic_and_include_all_prerequisites(self):
        for s in [skill('a'),skill('b',['a']),skill('c',['a']),skill('d',['b','c'])]:self.db.insert_skill(s)
        graph=SkillGraph(self.db)
        self.assertEqual([s.id for s in graph.shortest_path(set(),'d')],['a','b','c','d'])
        self.assertEqual([s.id for s in graph.get_unlockable({'a'})],['b','c'])
        self.assertEqual(compute_skill_cs('a',graph),74)
        self.assertEqual(graph.shortest_path({'a','b','c','d'},'d'),[])
        with self.assertRaises(ValueError):graph.shortest_path(set(),'missing')

    def test_graph_rejects_missing_prerequisites_and_cycles(self):
        self.db.insert_skill(skill('a',['missing']))
        with self.assertRaisesRegex(ValueError,'Unknown prerequisite'):SkillGraph(self.db)
        self.db.insert_skill(skill('missing',['a']))
        with self.assertRaisesRegex(ValueError,'cycle'):SkillGraph(self.db)

    def test_learning_and_unlearning_preserve_dependencies(self):
        self.db.insert_skill(skill('base'));self.db.insert_skill(skill('advanced',['base']))
        community=create_community(self.db,'Test Community')
        with self.assertRaisesRegex(ValueError,'prerequisites'):learn_skill(self.db,community.id,'advanced')
        with self.assertRaises(ValueError):learn_skill(self.db,community.id,'unknown')
        self.assertTrue(learn_skill(self.db,community.id,'base'))
        self.assertFalse(learn_skill(self.db,community.id,'base'))
        learn_skill(self.db,community.id,'advanced')
        with self.assertRaisesRegex(ValueError,'dependent'):unlearn_skill(self.db,community.id,'base')
        self.assertTrue(unlearn_skill(self.db,community.id,'advanced'))
        self.assertTrue(unlearn_skill(self.db,community.id,'base'))

    def test_seed_update_preserves_custom_entries(self):
        custom=article('water-purification-boiling',custom=True,content='Custom reviewed local content.')
        self.db.insert_article(custom)
        with contextlib.redirect_stdout(io.StringIO()):seed(self.db,update=True)
        self.assertEqual(self.db.get_article(custom.id).content,custom.content)
        self.assertEqual(len(self.db.all_skills()),6)

    def test_missing_source_is_not_created(self):
        path=Path(self.temp.name)/'missing.db'
        with self.assertRaises(RuntimeError):merge_databases(self.db,str(path))
        self.assertFalse(path.exists())

    def test_sync_is_additive_preserves_local_and_deduplicates_conflicts(self):
        self.db.insert_article(article(content='Local article.'))
        path,remote=self.remote()
        remote.insert_article(article(content='Remote article.'))
        remote.insert_article(article('new-article'))
        remote.insert_skill(skill())
        remote.insert_community(Community('town','Town',['base']))
        remote.close()
        first=merge_databases(self.db,str(path))
        self.assertEqual(first,dict(articles_added=1,skills_added=1,conflicts=1,communities_merged=1))
        self.assertEqual(self.db.get_article('water').content,'Local article.')
        self.assertEqual(merge_databases(self.db,str(path))['conflicts'],0)
        self.assertEqual(len(self.db.list_conflicts()),1)

    def test_late_merge_failure_rolls_back_every_write(self):
        path,remote=self.remote()
        remote.insert_article(article())
        remote.insert_community(Community('town','Town',['unknown']))
        remote.close()
        with self.assertRaisesRegex(RuntimeError,'local data was not changed'):merge_databases(self.db,str(path))
        self.assertIsNone(self.db.get_article('water'))
        self.assertEqual(self.db.list_communities(),[])

    def test_community_union_preserves_local_notes(self):
        self.db.insert_skill(skill('a'));self.db.insert_skill(skill('b'))
        self.db.insert_community(Community('town','Local Town',['a'],notes='Keep this.'))
        path,remote=self.remote()
        remote.insert_skill(skill('a'));remote.insert_skill(skill('b'))
        remote.insert_community(Community('town','Remote Town',['b']))
        remote.close()
        merge_databases(self.db,str(path))
        merged=self.db.get_community('town')
        self.assertEqual(merged.known_skills,['a','b'])
        self.assertEqual(merged.notes,'Keep this.')

    def test_malformed_and_cyclic_sources_are_rejected(self):
        path,remote=self.remote()
        remote.insert_skill(skill('a',['b']));remote.insert_skill(skill('b',['a']));remote.close()
        with self.assertRaisesRegex(RuntimeError,'cycle'):merge_databases(self.db,str(path))
        self.assertEqual(self.db.all_skills(),[])
        connection=sqlite3.connect(str(path));connection.execute("UPDATE skills SET civilization_score=999");connection.commit();connection.close()
        with self.assertRaises(RuntimeError):merge_databases(self.db,str(path))

    def test_backup_restores_wal_data_and_refuses_overwrite(self):
        path,live=self.remote();live.insert_article(article())
        target=Path(self.temp.name)/'backup.db'
        live.backup(str(target));restored=Database(str(target))
        self.assertEqual(restored.get_article('water').title,'Water collection')
        self.assertEqual(restored.connection.execute('PRAGMA integrity_check').fetchone()[0],'ok')
        if os.name=='posix':self.assertEqual(target.stat().st_mode & 0o777,0o600)
        with self.assertRaises(ValueError):live.backup(str(target))
        with self.assertRaises(ValueError):live.backup(str(path))
        restored.close();live.close()

    def test_transaction_rolls_back_helpers_that_used_to_commit_early(self):
        with self.assertRaises(ValueError):
            with self.db.transaction():
                self.db.insert_article(article())
                self.db.set_meta('test','value')
                self.db.insert_conflict('article','water','old','new')
                raise ValueError('cancel')
        self.assertIsNone(self.db.get_article('water'))
        self.assertIsNone(self.db.get_meta('test'))
        self.assertEqual(len(self.db.list_conflicts()),0)

    def test_yaml_subset_is_predictable(self):
        self.assertEqual(load('id: "true"\nscore: 5\ntags: [water, fire]')['id'],'true')
        with self.assertRaises(ValueError):load('id: a\nid: b')
        with self.assertRaises(ValueError):load('a'*250001)

    def test_cli_works_without_site_packages_and_incomplete_groups_do_not_hang(self):
        path=Path(self.temp.name)/'cli.db'
        cmd=[sys.executable,'-S',str(ROOT/'scripts'/'seed_db.py'),'--db',str(path)]
        self.assertEqual(subprocess.run(cmd,capture_output=True,timeout=15).returncode,0)
        for args in [['library','search','water'],['tree','show'],['library']]:
            result=subprocess.run([sys.executable,'-S',str(ROOT/'main.py'),'--db',str(path),'--ui','plain']+args,capture_output=True,timeout=5)
            self.assertEqual(result.returncode,0,result.stderr)
        result=subprocess.run([sys.executable,'-S',str(ROOT/'main.py'),'--db',str(path),'library','top','--limit','-5'],capture_output=True,timeout=5)
        self.assertNotEqual(result.returncode,0)

if __name__=='__main__':unittest.main()
