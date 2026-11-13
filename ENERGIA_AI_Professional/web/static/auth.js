// V8 Lot 2 login gate; session stored only in an HttpOnly cookie.
(()=>{
 let csrf='';
 const originalFetch=window.fetch.bind(window);
 window.fetch=(url,opts={})=>{
  const next={...opts};const method=(next.method||'GET').toUpperCase();
  if(typeof url==='string' && url.startsWith('/api/') && !['GET','HEAD','OPTIONS'].includes(method) && !url.startsWith('/api/auth/login')){
   next.headers={...(next.headers||{}),'X-CSRF-Token':csrf};
  }
  return originalFetch(url,next);
 };
 const overlay=document.createElement('div');overlay.id='energiaLogin';
 overlay.style.cssText='position:fixed;inset:0;z-index:99999;background:#f4f8fb;display:flex;align-items:center;justify-content:center;padding:24px;font-family:system-ui,sans-serif';
 overlay.innerHTML=`<form id="energiaLoginForm" style="background:white;padding:32px;border-radius:18px;box-shadow:0 10px 35px #132d4b22;max-width:420px;width:100%;display:grid;gap:15px"><h2 style="margin:0;color:#10365b">ENERGIA AI · Espace professionnel</h2><p style="margin:0;color:#5b7183">Connectez-vous pour accéder à vos bâtiments.</p><label>Email<input id="energiaEmail" type="email" required autocomplete="username" style="display:block;width:100%;box-sizing:border-box;padding:12px;margin-top:5px"></label><label>Mot de passe<input id="energiaPassword" type="password" required autocomplete="current-password" style="display:block;width:100%;box-sizing:border-box;padding:12px;margin-top:5px"></label><button type="submit" style="padding:13px;background:#087fa0;color:white;border:0;border-radius:8px;cursor:pointer">Se connecter</button><p id="energiaLoginError" role="alert" style="color:#b3261e;margin:0"></p></form>`;
 document.addEventListener('DOMContentLoaded',async()=>{
  document.body.appendChild(overlay);
  const userBar=document.createElement('div');
  userBar.id='energiaUserBar';
  userBar.style.cssText='display:none;align-items:center;gap:10px;flex-wrap:wrap;margin-left:12px';
  userBar.innerHTML='<span id="energiaUserLabel" style="font-size:12px;color:#36546a;max-width:190px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap"></span><button id="energiaLogout" type="button" style="background:#fff;border:1px solid #c6d8e3;border-radius:8px;padding:9px 12px;color:#10365b;cursor:pointer;font-weight:600">Se déconnecter</button>';
  const adminButton=document.createElement('button');
  adminButton.type='button';adminButton.textContent='Collaborateurs';
  adminButton.style.cssText='display:none;background:#eaf4f8;border:1px solid #b5d3e0;border-radius:8px;padding:9px 12px;color:#10365b;cursor:pointer;font-weight:600';
  userBar.insertBefore(adminButton,userBar.querySelector('#energiaLogout'));
  const panel=document.createElement('div');panel.id='energiaAdminPanel';
  panel.style.cssText='display:none;position:fixed;inset:0;z-index:99998;background:#102a4377;align-items:center;justify-content:center;padding:18px;font-family:system-ui,sans-serif';
  panel.innerHTML=`<section role="dialog" aria-modal="true" aria-label="Gestion des collaborateurs" style="background:white;border-radius:16px;padding:24px;width:min(650px,100%);max-height:90vh;overflow:auto;color:#183e5b"><div style="display:flex;justify-content:space-between;gap:12px"><h2 style="margin:0 0 16px">Collaborateurs</h2><button id="energiaCloseAdmin" type="button">Fermer</button></div><p id="energiaAdminError" role="alert" style="color:#b3261e"></p><div id="energiaAdminUsers"></div><h3>Ajouter un collaborateur</h3><form id="energiaAddUser" style="display:grid;gap:10px"><input name="email" type="email" placeholder="Email professionnel" autocomplete="off" required style="padding:10px"><input name="password" type="password" placeholder="Mot de passe provisoire (12 caractères minimum)" minlength="12" required autocomplete="new-password" style="padding:10px"><select name="role" style="padding:10px"><option value="engineer">Ingénieur</option><option value="reader">Lecteur</option><option value="admin">Administrateur</option></select><button type="submit" style="background:#087fa0;color:white;border:0;border-radius:8px;padding:12px">Créer le compte</button></form><p style="font-size:12px;color:#526f82">Transmets le mot de passe provisoire par un canal sécurisé. La réinitialisation autonome du mot de passe sera ajoutée ultérieurement.</p></section>`;
  document.body.appendChild(panel);
  const adminError=panel.querySelector('#energiaAdminError');
  async function loadUsers(){
    const r=await window.fetch('/api/v8/admin/users');if(!r.ok)throw Error('Accès à la liste impossible');
    const data=await r.json();const target=panel.querySelector('#energiaAdminUsers');target.replaceChildren();
    for(const u of data.users){
      const line=document.createElement('div');line.style.cssText='display:flex;align-items:center;gap:10px;flex-wrap:wrap;padding:9px 0;border-bottom:1px solid #e1ebf0';
      const name=document.createElement('span');name.textContent=u.email;name.style.flex='1';line.appendChild(name);
      const select=document.createElement('select');select.setAttribute('aria-label','Rôle de '+u.email);
      for(const [value,label] of [['admin','Administrateur'],['engineer','Ingénieur'],['reader','Lecteur']]){
        const opt=document.createElement('option');opt.value=value;opt.textContent=label;select.appendChild(opt);
      }
      select.value=u.role;
      select.addEventListener('change',async()=>{
        adminError.textContent='';select.disabled=true;
        try{
          const r=await window.fetch('/api/v8/admin/users/'+encodeURIComponent(u.id)+'/role',{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({role:select.value})});
          if(!r.ok){const body=await r.json();throw Error(body.detail||'Modification refusée');}
          await loadUsers();
        }catch(e){adminError.textContent=e.message;select.value=u.role;select.disabled=false;}
      });
      line.appendChild(select);target.appendChild(line);
    }
  }
  adminButton.addEventListener('click',async()=>{panel.style.display='flex';adminError.textContent='';try{await loadUsers()}catch(e){adminError.textContent=e.message}});
  panel.querySelector('#energiaCloseAdmin').addEventListener('click',()=>panel.style.display='none');
  panel.querySelector('#energiaAddUser').addEventListener('submit',async e=>{
    e.preventDefault();adminError.textContent='';const form=e.currentTarget;const button=form.querySelector('button');button.disabled=true;
    try{
      const r=await window.fetch('/api/v8/admin/users',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:form.elements.email.value,password:form.elements.password.value,role:form.elements.role.value})});
      if(!r.ok){const body=await r.json();throw Error(typeof body.detail==='string'?body.detail:'Création impossible');}
      form.reset();await loadUsers();
    }catch(ex){adminError.textContent=ex.message}finally{button.disabled=false}
  });
  (document.querySelector('.top-right')||document.querySelector('.topbar')||document.body).appendChild(userBar);
  async function session(){
   const r=await originalFetch('/api/auth/me',{credentials:'same-origin'});
   if(!r.ok){csrf='';userBar.style.display='none';overlay.style.display='flex';return false;}
   const data=await r.json();csrf=data.csrf;
   const u=data.user||{};
   document.getElementById('energiaUserLabel').textContent=[u.email,u.role].filter(Boolean).join(' · ');
   adminButton.style.display=u.role==='admin'?'inline-block':'none';
   userBar.style.display='flex';overlay.style.display='none';return true;
  }
  document.getElementById('energiaLogout').addEventListener('click',async()=>{
   const btn=document.getElementById('energiaLogout');btn.disabled=true;
   try{
    const r=await window.fetch('/api/auth/logout',{method:'POST',credentials:'same-origin'});
    if(!r.ok)throw Error('La déconnexion a échoué. Réessaie.');
    csrf='';window.location.reload();
   }catch(ex){alert(ex.message);btn.disabled=false;}
  });
  try{await session()}catch{}
  document.getElementById('energiaLoginForm').addEventListener('submit',async(e)=>{
   e.preventDefault();const err=document.getElementById('energiaLoginError');err.textContent='';
   try{
    const r=await originalFetch('/api/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:document.getElementById('energiaEmail').value,password:document.getElementById('energiaPassword').value})});
    if(!r.ok)throw Error('Identifiants invalides');
    if(!await session())throw Error('Session non disponible');
    document.getElementById('energiaPassword').value='';
   }catch(ex){err.textContent=ex.message}
  });
 });
})();
