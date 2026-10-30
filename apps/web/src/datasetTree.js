const order=new Intl.Collator('en',{numeric:true,sensitivity:'base'})
export function catalogNodes(catalog){
  const root={kind:'folder',label:'NL2VBENCH',path:'NL2VBENCH',count:0,children:[]}
  for(const group of catalog.groups||[]){
    let node=root
    for(const part of group.path.split('/')){
      let child=node.children.find(n=>n.kind==='folder'&&n.label===part)
      if(!child){child={kind:'folder',label:part,path:node.path+'/'+part,count:0,children:[]};node.children.push(child)}
      node=child
    }
    for(const file of group.files)node.children.push({...file,kind:'file',label:file.name,path:node.path+'/'+file.sample_id})
  }
  function sort(node){node.children.sort((a,b)=>(a.kind===b.kind?order.compare(a.label,b.label):a.kind==='folder'?-1:1));node.count=node.children.reduce((n,c)=>n+(c.kind==='folder'?sort(c):1),0);return node.count}
  sort(root);return root
}
export function visibleCatalogRows(root,expanded,query=''){
  const needle=query.trim().toLowerCase(),rows=[]
  function matching(node){return node.label.toLowerCase().includes(needle)||(node.kind==='file'&&String(node.category).toLowerCase().includes(needle))||(node.children||[]).some(matching)}
  function visit(node,depth,parentMatch=false){
    if(needle&&!parentMatch&&!matching(node))return
    rows.push({...node,depth});if(node.kind==='folder'&&(expanded.has(node.path)||needle))for(const child of node.children)visit(child,depth+1,parentMatch||!!needle&&node.label.toLowerCase().includes(needle))
  }
  visit(root,0);return rows
}
