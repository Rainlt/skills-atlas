'use strict';
function createAtlasModel(data) {
  const byId=new Map(data.skills.map(s=>[s.id,s])),groups=new Map(data.groups.map(g=>[g.id,g]));
  const names=Object.fromEntries(data.categories.map(c=>[c.id,c.name_zh]));
  const cmp=(a,b)=>{for(let i=0;i<a.length;i++){if(a[i]===b[i])continue;return a[i]<b[i]?-1:1}return 0};
  const known=s=>Boolean(s.compatibility&&!s.compatibility.startsWith('未验证'));
  const rank=s=>[-s.verification.rank,-Number(s.repository.kind==='standalone'),-Number(s.repository.high_star),-Number(known(s)),-Number(s.file_count>1),s.source_priority,s.id];
  function relevance(s,g,terms){
    const name=s.name.toLowerCase(),id=s.id.toLowerCase(),editorial=[g.title,g.summary,...g.keywords].join(' ').toLowerCase();
    const text=[id,name,s.description,...s.categories,...s.categories.map(c=>names[c]),editorial].join(' ').toLowerCase();let score=0;
    for(const t of terms){if(t===name||t===id)score+=100;else if(name.includes(t))score+=40;else if(g.title.toLowerCase().includes(t))score+=35;else if(editorial.includes(t))score+=25;else if(id.includes(t))score+=20;else if(text.includes(t))score+=8;
      else {const exp=data.categories.filter(c=>c.queries_zh.includes(t)||c.name_zh===t).flatMap(c=>[c.id,...c.keywords]);if(!exp.some(x=>text.includes(x.toLowerCase())))return -1;score++}}
    return score;
  }
  function filter({query='',category='',source='',scope='featured',grouped=true,sort='relevance',include_archived=false}={}){
    const terms=query.toLowerCase().trim().split(/\s+/).filter(Boolean),cards=[];let matchedSkills=0;
    for(const g of groups.values()){
      if(scope==='featured'&&!g.featured)continue;
      const candidates=g.members.map(id=>byId.get(id)).filter(s=>{
        const state=s.lifecycle.state;
        if(scope==='archived'){if(!['watch','archived'].includes(state))return false}else if(!include_archived&&state==='archived')return false;
        if(scope==='research'&&!s.categories.some(c=>['research','data','documents'].includes(c)))return false;
        if(scope==='integrations'&&!s.integration)return false;
        return (!category||s.categories.includes(category))&&(!source||s.sources.some(r=>r.toLowerCase().includes(source.toLowerCase())));
      }).map(s=>({s,score:relevance(s,g,terms)})).filter(x=>x.score>=0);
      const candidateOrder=x=>{const base=[-x.score,Number(x.s.lifecycle.state==='watch'),rank(x.s)[0],-Number(x.s.id===g.preferred),...rank(x.s).slice(1)],r=x.s.repository;return sort==='stars'?[-(r.fresh?(r.stars??-1):-1),...base]:base};
      candidates.sort((a,b)=>cmp(candidateOrder(a),candidateOrder(b)));
      matchedSkills+=candidates.length;
      if(grouped&&candidates.length)cards.push({group:g,representative:candidates[0].s,variants:candidates.map(c=>c.s),score:candidates[0].score});
      if(!grouped)for(const c of candidates)cards.push({group:g,representative:c.s,variants:[c.s],score:c.score});
    }
    const order=c=>{const s=c.representative,g=c.group,r=s.repository;
      if(sort==='stars')return[-(r.fresh?(r.stars??-1):-1),-c.score,...rank(s)];
      if(sort==='name')return[s.name.toLowerCase(),s.id];
      return[-c.score,-Number(g.featured),Number(s.lifecycle.state==='watch'),rank(s)[0],-Number(r.kind==='standalone'),g.position,...rank(s).slice(2)];
    };
    cards.sort((a,b)=>cmp(order(a),order(b)));return {cards,matchedSkills};
  }
  return {filter,byId,groups};
}
if(typeof module!=='undefined')module.exports={createAtlasModel};
