import { useEffect, useState } from "react";
import { api } from "../api.js";
import { can } from "../permissions.js";
import DataTable from "./DataTable.jsx";
import Modal from "./Modal.jsx";

const EMPTY={department_id:0,name:"",enabled:true};
export default function DepartmentsPage({permissions,showToast}){
  const[rows,setRows]=useState([]),[form,setForm]=useState(EMPTY);
  const mayView=can.departmentsView(permissions), mayOperate=can.departmentsOperate(permissions);
  async function load(){if(!mayView)return;try{const x=await api.getDepartments();setRows(Array.isArray(x)?x:[])}catch(e){showToast(e.message,"error")}}
  useEffect(()=>{load()},[mayView]);
  const columns=[{key:"department_id",label:"ID",className:"num"},{key:"name",label:"Название"},{key:"enabled",label:"Активен",render:r=><span className={r.enabled?"badge badge-ok":"badge badge-muted"}>{r.enabled?"Да":"Нет"}</span>},{key:"date_created",label:"Создан"}];
  async function save(){try{if(form.department_id)await api.updateDepartment(form.department_id,{name:form.name});else await api.createDepartment({name:form.name,enabled:true});setForm(EMPTY);await load();showToast("Отдел сохранён","success")}catch(e){showToast(e.message,"error")}}
  async function toggle(){try{await(form.enabled?api.disableDepartment(form.department_id):api.enableDepartment(form.department_id));setForm(EMPTY);await load()}catch(e){showToast(e.message,"error")}}
  async function remove(){if(!confirm("Удалить отдел?"))return;try{await api.deleteDepartment(form.department_id);setForm(EMPTY);await load();showToast("Отдел удалён","success")}catch(e){showToast(e.message,"error")}}
  if(!mayView)return <div className="empty-permission">Нет права управления отделами.</div>;
  return <div><div className="view-header"><div><h1>Отделы</h1><p>Справочник Department.</p></div><div className="view-actions"><button className="btn" onClick={load}>Обновить</button><button className="btn btn-primary" onClick={()=>setForm({...EMPTY})}>Создать</button></div></div>
    <DataTable storageKey="departments" title="Отделы" rows={rows} columns={columns} getRowId={r=>r.department_id} onRowClick={r=>setForm({...r})}/>
    {form!==EMPTY&&<Modal title={form.department_id?`Отдел #${form.department_id}`:"Новый отдел"} onClose={()=>setForm(EMPTY)}><div className="form-grid compact"><label><span>Название</span><input value={form.name} onChange={e=>setForm({...form,name:e.target.value})}/></label></div><div className="card-actions"><button className="btn btn-primary" disabled={!form.name.trim()} onClick={save}>Сохранить</button>{form.department_id>0&&<><button className="btn" onClick={toggle}>{form.enabled?"Отключить":"Включить"}</button><button className="btn btn-danger" onClick={remove}>Удалить</button></>}</div></Modal>}
  </div>
}
