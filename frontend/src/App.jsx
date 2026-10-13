import React, { useEffect, useMemo, useState } from 'react'
import { Link, Navigate, Route, Routes, useLocation, useNavigate } from 'react-router-dom'
import {
  BarChart3, Boxes, Building2, ChevronRight, ClipboardList, LogOut,
  Menu, Package, Settings, ShoppingCart, Sparkles, Truck, UserRound, Users, X
} from 'lucide-react'
import api from './api'

const resources = {
  clientes: { title: 'Clientes', endpoint: '/clientes', icon: Users, fields: [
    ['nome','Nome','text'], ['documento','CPF/CNPJ','text'], ['telefone','Telefone','text'], ['email','E-mail','email']
  ]},
  propriedades: { title: 'Propriedades', endpoint: '/propriedades', icon: Building2, fields: [
    ['nome','Nome da propriedade','text'], ['localizacao','Localização','text'], ['id_cliente','ID do cliente','number']
  ]},
  produtos: { title: 'Produtos', endpoint: '/produtos', icon: Package, fields: [
    ['nome','Nome','text'], ['tipo','Tipo','text'], ['peso_unidade','Peso por unidade','number']
  ]},
  usuarios: { title: 'Usuários', endpoint: '/usuarios', icon: UserRound, fields: [
    ['nome','Nome','text'], ['email','E-mail','email'], ['senha','Senha','password'], ['tipo_usuario','Perfil (ADMIN/VENDEDOR)','text']
  ]},
  predicoes: { title: 'Predições', endpoint: '/predicoes', icon: Sparkles, fields: [
    ['cliente','Cliente','text'],
    ['animal','Animal','text'],
    ['quantidade_kg','Qtd (Kg)','number'],
    ['data_compra','Data Compra','date'],
    ['dias_previstos','Prev. Dias','number'],
    ['data_previsao','Data Prevista','date'],
    ['data_real','Data Real','date']
  ]}
}

function getUser() {
  try { return JSON.parse(localStorage.getItem('cotriflow_user') || 'null') } catch { return null }
}

function Protected({ children }) {
  return localStorage.getItem('cotriflow_token') ? children : <Navigate to="/login" replace />
}

function Login() {
  const nav = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function submit(e) {
    e.preventDefault()
    setLoading(true); setError('')
    try {
      const body = new URLSearchParams()
      body.append('username', email); body.append('password', password)
      const { data } = await api.post('/auth/login', body, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      })
      localStorage.setItem('cotriflow_token', data.access_token)
      const me = data.usuario || (await api.get('/auth/me')).data
      localStorage.setItem('cotriflow_user', JSON.stringify(me))
      nav('/')
    } catch (err) {
      setError(err.response?.data?.detail || 'Não foi possível entrar.')
    } finally { setLoading(false) }
  }

  return <div className="login-page">
    <div className="login-card">
      <div className="brand brand-center"><div className="brand-mark">C</div><div><b>CotriFlow</b><span>Gestão agropecuária</span></div></div>
      <h1>Bem-vindo</h1>
      <p className="muted">Entre para acessar o sistema.</p>
      <form onSubmit={submit}>
        <label>E-mail<input value={email} onChange={e=>setEmail(e.target.value)} type="email" required autoFocus /></label>
        <label>Senha<input value={password} onChange={e=>setPassword(e.target.value)} type="password" required /></label>
        {error && <div className="error">{error}</div>}
        <button className="primary full" disabled={loading}>{loading ? 'Entrando...' : 'Entrar'}</button>
      </form>
    </div>
  </div>
}

function Layout({ children }) {
  const loc = useLocation()
  const nav = useNavigate()
  const user = getUser()
  const [open, setOpen] = useState(false)
  const links = [
    ['/', 'Dashboard', BarChart3],
    ['/clientes', 'Clientes', Users],
    ['/propriedades', 'Propriedades', Building2],
    ['/produtos', 'Produtos', Package],
    ['/pedidos', 'Pedidos', ShoppingCart],
    ['/predicoes', 'Predições', Sparkles],
  ]
  if (user?.tipo_usuario === 'ADMIN' || user?.tipo === 'ADMIN') links.push(['/usuarios','Usuários',UserRound])

  function logout() {
    api.post('/auth/logout').catch(()=>{})
    localStorage.clear(); nav('/login')
  }

  return <div className="app-shell">
    <aside className={open ? 'sidebar open' : 'sidebar'}>
      <div className="brand"><div className="brand-mark">C</div><div><b>CotriFlow</b><span>Gestão agropecuária</span></div><button className="icon mobile-close" onClick={()=>setOpen(false)}><X size={20}/></button></div>
      <nav>{links.map(([to,label,Icon])=><Link key={to} to={to} onClick={()=>setOpen(false)} className={loc.pathname===to?'active':''}><Icon size={19}/><span>{label}</span>{loc.pathname===to&&<ChevronRight size={16} className="nav-arrow"/>}</Link>)}</nav>
      <div className="sidebar-bottom">
        <div className="user-mini"><div className="avatar">{(user?.nome||'U').slice(0,1).toUpperCase()}</div><div><b>{user?.nome||'Usuário'}</b><span>{user?.tipo_usuario||user?.tipo||''}</span></div></div>
        <button className="logout" onClick={logout}><LogOut size={18}/> Sair</button>
      </div>
    </aside>
    <main className="main">
      <header className="topbar"><button className="icon mobile-menu" onClick={()=>setOpen(true)}><Menu/></button><div><span className="eyebrow">COTRIFLOW</span><h2>{links.find(x=>x[0]===loc.pathname)?.[1] || 'CotriFlow'}</h2></div><div className="top-user">{user?.nome||'Usuário'}</div></header>
      <div className="content">{children}</div>
    </main>
  </div>
}

function Dashboard() {
  const [stats,setStats] = useState({clientes:0,propriedades:0,produtos:0,pedidos:0})
  useEffect(()=>{ Promise.all([
    api.get('/clientes'), api.get('/propriedades'), api.get('/produtos'), api.get('/pedidos')
  ]).then(([a,b,c,d])=>setStats({clientes:a.data.length,propriedades:b.data.length,produtos:c.data.length,pedidos:d.data.length})).catch(()=>{}) },[])
  return <><div className="hero"><div><span className="eyebrow">VISÃO GERAL</span><h1>Bom trabalho! 👋</h1><p>Acompanhe os principais dados da operação da CotriFlow.</p></div><div className="hero-icon"><Truck size={44}/></div></div>
  <div className="stats">
    <Stat icon={Users} label="Clientes" value={stats.clientes} to="/clientes"/>
    <Stat icon={Building2} label="Propriedades" value={stats.propriedades} to="/propriedades"/>
    <Stat icon={Package} label="Produtos" value={stats.produtos} to="/produtos"/>
    <Stat icon={ShoppingCart} label="Pedidos" value={stats.pedidos} to="/pedidos"/>
  </div>
  <div className="panel"><div className="panel-title"><div><h3>Acesso rápido</h3><p>Cadastre e consulte informações da operação.</p></div></div><div className="quick-grid">
    {linksQuick.map(([to,label,Icon])=><Link to={to} className="quick" key={to}><Icon/><span>{label}</span><ChevronRight/></Link>)}
  </div></div></>
}
const linksQuick=[['/clientes','Clientes',Users],['/propriedades','Propriedades',Building2],['/produtos','Produtos',Package],['/pedidos','Pedidos',ShoppingCart]]

function Stat({icon:Icon,label,value,to}) { return <Link to={to} className="stat"><div className="stat-icon"><Icon size={22}/></div><div><span>{label}</span><strong>{value}</strong></div></Link> }

function formatCell(val, type) {
  if (val === null || val === undefined || val === '') return '—'
  if (type === 'date') {
    if (typeof val === 'string') {
      const first = val.replace('T', ' ').split(' ')[0]
      if (first && first.length === 10) return first
    }
    const d = new Date(val)
    if (!isNaN(d.getTime())) return d.toISOString().slice(0, 10)
  }
  return String(val)
}

function CrudPage({kind}) {
  const cfg=resources[kind], [rows,setRows]=useState([]), [loading,setLoading]=useState(true), [editing,setEditing]=useState(null), [q,setQ]=useState('')
  const [error,setError]=useState('')
  const [page,setPage]=useState(1)
  const pageSize=20
  async function load(){setLoading(true);try{const {data}=await api.get(cfg.endpoint);setRows(Array.isArray(data)?data:[])}catch(e){setError(e.response?.data?.detail||'Erro ao carregar.')}finally{setLoading(false)}}
  useEffect(()=>{load()},[])
  const filtered=useMemo(()=>rows.filter(r=>JSON.stringify(r).toLowerCase().includes(q.toLowerCase())),[rows,q])
  useEffect(()=>{setPage(1)},[q])
  const totalPages=Math.ceil(filtered.length/pageSize)||1
  const paginated=useMemo(()=>filtered.slice((page-1)*pageSize,page*pageSize),[filtered,page])
  async function remove(id){if(!confirm('Excluir este registro?'))return;try{await api.delete(`${cfg.endpoint}/${id}`);load()}catch(e){alert(e.response?.data?.detail||'Não foi possível excluir.')} }
  return <div>
    <div className="page-head"><div><span className="eyebrow">CADASTRO</span><h1>{cfg.title}</h1><p>Gerencie os registros de {cfg.title.toLowerCase()}.</p></div><button className="primary" onClick={()=>setEditing({})}>+ Novo</button></div>
    <div className="toolbar"><input placeholder={`Pesquisar ${cfg.title.toLowerCase()}...`} value={q} onChange={e=>setQ(e.target.value)}/></div>
    {error&&<div className="error">{error}</div>}
    <div className="table-wrap"><table><thead><tr>{cfg.fields.filter(f=>f[0]!=='senha').map(f=><th key={f[0]}>{f[1]}</th>)}<th>Ações</th></tr></thead><tbody>
      {loading?<tr><td colSpan="10" className="empty">Carregando...</td></tr>:filtered.length===0?<tr><td colSpan="10" className="empty">Nenhum registro encontrado.</td></tr>:paginated.map(r=><tr key={r.id||r.id_usuario||r.id_cliente||r.id_propriedade||r.id_produto||r.id_predicao}>
        {cfg.fields.filter(f=>f[0]!=='senha').map(f=><td key={f[0]}>{formatCell(r[f[0]], f[2])}</td>)}<td><button className="link-btn" onClick={()=>setEditing(r)}>Editar</button><button className="danger-btn" onClick={()=>remove(r.id||r.id_usuario||r.id_cliente||r.id_propriedade||r.id_produto||r.id_predicao)}>Excluir</button></td>
      </tr>)}
    </tbody></table></div>
    {filtered.length>pageSize&&<div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginTop:16,flexWrap:'wrap',gap:8}}>
      <span className="muted">Total: {filtered.length} registros (Página {page} de {totalPages})</span>
      <div style={{display:'flex',gap:8}}>
        <button className="secondary" disabled={page<=1} onClick={()=>setPage(p=>p-1)}>Anterior</button>
        <button className="secondary" disabled={page>=totalPages} onClick={()=>setPage(p=>p+1)}>Próxima</button>
      </div>
    </div>}
    {editing!==null&&<FormModal cfg={cfg} value={editing} onClose={()=>setEditing(null)} onSaved={()=>{setEditing(null);load()}}/>}
  </div>
}

function FormModal({cfg,value,onClose,onSaved}) {
  const [form,setForm]=useState({...value}),[saving,setSaving]=useState(false),[error,setError]=useState('')
  function set(k,v){setForm(x=>({...x,[k]:v}))}
  async function submit(e){e.preventDefault();setSaving(true);setError('');try{
    const id=form.id||form.id_usuario||form.id_cliente||form.id_propriedade||form.id_produto||form.id_predicao
    const data={...form}
    for(const k of Object.keys(data)) if(data[k]==='') delete data[k]
    if(!id && data.data_predicao) delete data.data_predicao
    if(id) await api.put(`${cfg.endpoint}/${id}`,data); else await api.post(cfg.endpoint,data)
    onSaved()
  }catch(e){setError(e.response?.data?.detail||'Erro ao salvar.')}finally{setSaving(false)}}
  return <div className="modal-backdrop"><div className="modal"><div className="modal-head"><h3>{(value.id||value.id_usuario||value.id_cliente||value.id_predicao)?'Editar':'Novo'} {cfg.title.slice(0,-1)}</h3><button className="icon" onClick={onClose}><X/></button></div>
  <form onSubmit={submit}>{cfg.fields.map(([key,label,type])=><label key={key}>{label}<input type={type} value={form[key]??''} onChange={e=>set(key,type==='number'?(e.target.value===''?'':Number(e.target.value)):e.target.value)} required={!value[key]&&key!=='senha'&&key!=='observacao'&&key!=='data_real'&&key!=='dias_previstos'&&key!=='data_previsao'}/></label>)}{error&&<div className="error">{error}</div>}<div className="modal-actions"><button type="button" className="secondary" onClick={onClose}>Cancelar</button><button className="primary" disabled={saving}>{saving?'Salvando...':'Salvar'}</button></div></form></div></div>
}

function Pedidos() {
  const [rows,setRows]=useState([]),[clientes,setClientes]=useState([]),[loading,setLoading]=useState(true),[modal,setModal]=useState(false)
  async function load(){setLoading(true);try{const [p,c]=await Promise.all([api.get('/pedidos'),api.get('/clientes')]);setRows(p.data);setClientes(c.data)}catch{}finally{setLoading(false)}}
  useEffect(()=>{load()},[])
  async function status(id,status){try{await api.patch(`/pedidos/${id}/status`,{status});load()}catch(e){alert(e.response?.data?.detail||'Erro ao atualizar status.')}}
  return <><div className="page-head"><div><span className="eyebrow">OPERAÇÃO</span><h1>Pedidos</h1><p>Acompanhe pedidos e entregas.</p></div><button className="primary" onClick={()=>setModal(true)}>+ Novo pedido</button></div>
  <div className="table-wrap"><table><thead><tr><th>ID</th><th>Cliente</th><th>Data</th><th>Peso total</th><th>Status</th><th>Ações</th></tr></thead><tbody>{loading?<tr><td colSpan="6" className="empty">Carregando...</td></tr>:rows.length===0?<tr><td colSpan="6" className="empty">Nenhum pedido cadastrado.</td></tr>:rows.map(r=><tr key={r.id_pedido||r.id}><td>#{r.id_pedido||r.id}</td><td>{r.cliente?.nome||clientes.find(c=>(c.id_cliente||c.id)===r.cliente_id)?.nome||r.cliente_id||'—'}</td><td>{r.data||r.data_pedido||'—'}</td><td>{r.peso_total??'—'}</td><td><select className="status-select" value={r.status||'PENDENTE'} onChange={e=>status(r.id_pedido||r.id,e.target.value)}>{['PENDENTE','SEPARANDO','EM_ENTREGA','ENTREGUE','CANCELADO'].map(s=><option key={s}>{s}</option>)}</select></td><td><Link className="link-btn" to={`/pedidos/${r.id_pedido||r.id}`}>Detalhes</Link></td></tr>)}</tbody></table></div>
  {modal&&<PedidoModal clientes={clientes} onClose={()=>setModal(false)} onSaved={()=>{setModal(false);load()}}/>}</>
}

function PedidoModal({clientes,onClose,onSaved}) {
  const [form,setForm]=useState({cliente_id:'',endereco_entrega:'',observacoes:''}),[items,setItems]=useState([{produto_id:'',quantidade:1}]),[products,setProducts]=useState([]),[saving,setSaving]=useState(false),[error,setError]=useState('')
  useEffect(()=>{api.get('/produtos').then(r=>setProducts(r.data)).catch(()=>{})},[])
  function upd(i,k,v){setItems(a=>a.map((x,n)=>n===i?{...x,[k]:v}:x))}
  async function submit(e){e.preventDefault();setSaving(true);try{await api.post('/pedidos',{...form,cliente_id:Number(form.cliente_id),itens:items.map(x=>({produto_id:Number(x.produto_id),quantidade:Number(x.quantidade)}))});onSaved()}catch(e){setError(e.response?.data?.detail||'Erro ao criar pedido.')}finally{setSaving(false)}}
  return <div className="modal-backdrop"><div className="modal wide"><div className="modal-head"><h3>Novo pedido</h3><button className="icon" onClick={onClose}><X/></button></div><form onSubmit={submit}>
    <label>Cliente<select value={form.cliente_id} onChange={e=>setForm({...form,cliente_id:e.target.value})} required><option value="">Selecione...</option>{clientes.map(c=><option key={c.id_cliente||c.id} value={c.id_cliente||c.id}>{c.nome}</option>)}</select></label>
    <label>Endereço de entrega<input value={form.endereco_entrega} onChange={e=>setForm({...form,endereco_entrega:e.target.value})}/></label>
    <h4>Produtos</h4>{items.map((it,i)=><div className="item-row" key={i}><select value={it.produto_id} onChange={e=>upd(i,'produto_id',e.target.value)} required><option value="">Produto...</option>{products.map(p=><option key={p.id_produto||p.id} value={p.id_produto||p.id}>{p.nome}</option>)}</select><input type="number" min="1" value={it.quantidade} onChange={e=>upd(i,'quantidade',e.target.value)} /><button type="button" className="danger-btn" onClick={()=>setItems(a=>a.filter((_,n)=>n!==i))}>Remover</button></div>)}<button type="button" className="secondary" onClick={()=>setItems(a=>[...a,{produto_id:'',quantidade:1}])}>+ Produto</button>
    {error&&<div className="error">{error}</div>}<div className="modal-actions"><button type="button" className="secondary" onClick={onClose}>Cancelar</button><button className="primary" disabled={saving}>{saving?'Criando...':'Criar pedido'}</button></div>
  </form></div></div>
}

function App() {
  return <Routes>
    <Route path="/login" element={<Login/>}/>
    <Route path="*" element={<Protected><Layout><Routes>
      <Route path="/" element={<Dashboard/>}/>
      <Route path="/clientes" element={<CrudPage kind="clientes"/>}/>
      <Route path="/propriedades" element={<CrudPage kind="propriedades"/>}/>
      <Route path="/produtos" element={<CrudPage kind="produtos"/>}/>
      <Route path="/usuarios" element={<CrudPage kind="usuarios"/>}/>
      <Route path="/predicoes" element={<CrudPage kind="predicoes"/>}/>
      <Route path="/pedidos" element={<Pedidos/>}/>
      <Route path="*" element={<Dashboard/>}/>
    </Routes></Layout></Protected>}/>
  </Routes>
}
export default App