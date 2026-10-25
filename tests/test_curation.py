import copy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from scripts.curate import build
from catalog_model import filter_catalog, compact, recommend


class CurationTests(unittest.TestCase):
    def fixture(self):
        def skill(repo, name, digest, priority):
            return {'id':repo+'/skills/'+name, 'name':name, 'description':'PDF document processing',
                    'instruction_sha256':digest, 'categories':['documents'], 'aliases':[],
                    'locations':[{'repo':repo,'commit':'a'*40,'bundle_sha':repo,'priority':priority,'url':'https://github.com/'+repo,'license':{}}],
                    'has_external_refs':False,'declared_risk':None,'compatibility':'未验证；请阅读上游要求','format_issues':[]}
        a=skill('publisher/pdf','pdf','one',10);b=skill('collection/skills','pdf','two',30);c=skill('publisher/more','unusual','three',10)
        data={'snapshot':'fixture','generated_at':'2026-10-25T00:00:00Z','sources':[{'repo':'publisher/pdf','kind':'publisher','skills_scanned':1},{'repo':'collection/skills','kind':'collection','skills_scanned':500}], 'skills':[a,b,c]}
        sel={'featured':[{'id':a['id'],'title':'PDF 处理','summary':'读取和检查文档','reason':'有当前核对','keywords':['文档']}],
             'reviews':{a['id']:{'commit':'a'*40,'bundle_sha':'publisher/pdf','level':'metadata_reviewed','date':'2026-10-25','note':'用途核对'}},'lifecycle':{}}
        signals={'repositories':{'publisher/pdf':{'stars':12000,'captured_at':'2026-10-25T00:00:00Z'},'collection/skills':{'stars':200000,'captured_at':'2026-10-25T00:00:00Z'}}}
        categories=[{'id':'documents','name_zh':'文档','queries_zh':['文档'],'keywords':['pdf']}]
        return data,sel,signals,categories
    def make(self,as_of='2026-10-25'):
        d,s,r,c=self.fixture();return build(d,s,{},r,as_of),c
    def test_grouping_preserves_each_original_id(self):
        d,c=self.make();self.assertEqual(len(d['skills']),3);self.assertEqual(len(d['groups']),2)
        self.assertEqual(len(filter_catalog(d,c)['cards'][0]['variants']),2)
    def test_exact_query_overrides_editorial_representative(self):
        d,c=self.make();r=filter_catalog(d,c,query='collection/skills/skills/pdf')
        self.assertEqual(r['cards'][0]['representative']['sources'],['collection/skills'])
        self.assertNotEqual(compact(r['cards'][0])['summary'],'读取和检查文档')
    def test_repository_star_does_not_override_relevance_or_review(self):
        d,c=self.make();r=filter_catalog(d,c,query='pdf')
        self.assertEqual(r['cards'][0]['representative']['repository']['repo'],'publisher/pdf')
        self.assertEqual(r['cards'][0]['representative']['repository']['kind'],'standalone')
        explicit=filter_catalog(d,c,query='pdf',sort='stars')
        self.assertEqual(explicit['cards'][0]['representative']['repository']['repo'],'collection/skills')
    def test_source_filter_keeps_the_requested_implementation(self):
        d,c=self.make();r=filter_catalog(d,c,source='collection')
        self.assertEqual(len(r['cards'][0]['variants']),1)
        self.assertEqual(r['cards'][0]['representative']['sources'],['collection/skills'])
    def test_changed_commit_or_bundle_exits_featured(self):
        for field in ['commit','bundle_sha']:
            d,s,r,c=self.fixture();d['skills'][0]['locations'][0][field]='changed'
            out=build(d,s,{},r,'2026-10-25');self.assertEqual(out['curation']['featured_groups'],0)
            self.assertEqual(next(x for x in out['skills'] if x['id']==d['skills'][0]['id'])['verification']['level'],'stale')
    def test_due_review_moves_to_watch_not_deletes(self):
        d,c=self.make('2026-11-24');self.assertEqual(d['curation']['featured_groups'],0)
        self.assertEqual(len(d['skills']),3);self.assertTrue(filter_catalog(d,c,scope='archived')['cards'])
    def test_candidate_expiry_and_manual_archive_keep_reasons(self):
        d,s,r,c=self.fixture();identifier=d['skills'][1]['id']
        s['lifecycle'][identifier]={'state':'candidate','entered_on':'2026-09-01'}
        out=build(d,s,{},r,'2026-10-25');item=next(x for x in out['skills'] if x['id']==identifier)
        self.assertEqual(item['lifecycle']['state'],'watch')
        s['lifecycle'][identifier]={'state':'archived','reason':'同用途保留发布者入口','changed_on':'2026-10-25','replaced_by':d['skills'][0]['id']}
        out=build(d,s,{},r,'2026-10-25')
        self.assertEqual(len(filter_catalog(out,c)['cards'][0]['variants']),1)
        self.assertEqual(len(filter_catalog(out,c,include_archived=True)['cards'][0]['variants']),2)
        self.assertEqual(compact(filter_catalog(out,c,scope='archived')['cards'][0])['replacement'],d['skills'][0]['id'])
    def test_restoring_archive_requires_fresh_review(self):
        d,s,r,c=self.fixture();s['lifecycle'][d['skills'][0]['id']]={'state':'featured','reviewed_on':'2026-12-01'}
        s['reviews'][d['skills'][0]['id']]['date']='2026-12-01'
        self.assertEqual(build(d,s,{},r,'2026-12-01')['curation']['featured_groups'],1)
    def test_archived_repository_is_signal_not_automatic_removal(self):
        d,s,r,c=self.fixture();r['repositories']['publisher/pdf']['archived']=True
        out=build(d,s,{},r,'2026-10-25');self.assertEqual(out['curation']['featured_groups'],1)
    def test_stale_signals_never_mark_high_star(self):
        d,c=self.make('2026-12-01');self.assertFalse(any(x['repository']['high_star'] for x in d['skills']))
    def test_capacity_and_archive_validation(self):
        d,s,r,c=self.fixture();s['policy']={'featured_limit':0}
        with self.assertRaises(ValueError):build(d,s,{},r)
        s.pop('policy');s['lifecycle'][d['skills'][0]['id']]={'state':'archived'}
        with self.assertRaises(ValueError):build(d,s,{},r)
    def test_semantic_group_requires_explicit_reason(self):
        d,s,r,c=self.fixture();s['groups']=[{'members':[d['skills'][0]['id'],d['skills'][2]['id']]}]
        with self.assertRaises(ValueError):build(d,s,{},r)
    def test_explicit_task_group_keeps_distinct_names_and_ids(self):
        d,s,r,c=self.fixture();s['groups']=[{'members':[d['skills'][0]['id'],d['skills'][2]['id']],'reason':'相同任务的两种实现'}]
        out=build(d,s,{},r,'2026-10-25')
        self.assertEqual(len(out['groups']),1);self.assertEqual(len(out['skills']),3)
        self.assertEqual(out['groups'][0]['grouping_notes'],['相同任务的两种实现'])
    def test_compact_search_expands_only_when_shortlist_misses(self):
        d,c=self.make()
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'data').mkdir()
            (root/'taxonomy.json').write_text(json.dumps({'categories':c}))
            (root/'data/curated.json').write_text(json.dumps(d))
            short=copy.deepcopy(d);short['groups']=[g for g in d['groups'] if g['featured']]
            (root/'data/shortlist.json').write_text(json.dumps(short))
            self.assertFalse(recommend(root,'pdf')['expanded_to_all'])
            result=recommend(root,'unusual')
            self.assertTrue(result['expanded_to_all']);self.assertEqual(result['results'][0]['id'],'publisher/more/skills/unusual')
            self.assertNotIn('locations',result['results'][0]);self.assertNotIn('manifest',result['results'][0])
    def test_models_rank_and_filter_identically(self):
        d,c=self.make();d['categories']=c
        script="const {createAtlasModel}=require('./web/catalog-model.js');const fs=require('fs');let x=JSON.parse(fs.readFileSync(0,'utf8'));console.log(JSON.stringify(createAtlasModel(x.data).filter(x.options).cards.map(c=>[c.representative.id,c.variants.map(s=>s.id)])));"
        for options in [{},{'scope':'all'},{'query':'pdf'},{'source':'collection'},{'sort':'stars','scope':'all'},{'query':'publisher/more/skills/unusual','scope':'all'},{'grouped':False,'scope':'all'}]:
            result=filter_catalog(d,c,**options)
            expected=[[x['representative']['id'],[s['id'] for s in x['variants']]] for x in result['cards']]
            actual=json.loads(subprocess.check_output(['node','-e',script],input=json.dumps({'data':d,'options':options}),text=True,cwd=Path(__file__).resolve().parents[1]))
            self.assertEqual(expected,actual)


if __name__=='__main__':unittest.main()
