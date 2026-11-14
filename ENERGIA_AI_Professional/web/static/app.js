const $=id=>document.getElementById(id);let lastAudit=null,lastResult=null,chart=null;
const names={dashboard:"Vue d'ensemble",portfolio:"Mes bâtiments",building:'Bâtiment',audit:'Audit énergétique',advisor:'AI Advisor',reports:'Rapports & méthode'};
function go(page){document.querySelectorAll('.page').forEach(e=>e.classList.toggle('active',e.id==='page-'+page));document.querySelectorAll('.nav-item').forEach(e=>e.classList.toggle('active',e.dataset.page===page));$('crumb').textContent=names[page];document.querySelector('.sidebar').classList.remove('open');window.scrollTo({top:0,behavior:'smooth'});}
document.querySelectorAll('[data-page]').forEach(e=>e.addEventListener('click',()=>go(e.dataset.page)));document.querySelectorAll('[data-go]').forEach(e=>e.addEventListener('click',()=>go(e.dataset.go)));$('menuToggle').addEventListener('click',()=>document.querySelector('.sidebar').classList.toggle('open'));
function notice(message,error=false){const el=$('notice');el.textContent=message;el.className='notice show'+(error?' error':'');setTimeout(()=>el.classList.remove('show'),6500)}
function payload(){const f=new FormData($('auditForm'));const o=Object.fromEntries(f.entries());['surface','electricity','gas','district','annual_cost','occupancy_hours_week'].forEach(k=>o[k]=Number(o[k]||0));o.construction_year=o.construction_year?Number(o.construction_year):null;const ledFields=[
'lighting_fixture_count',
'lighting_power_existing_w',
'lighting_power_proposed_w',
'lighting_schedule_hours_day',
'electricity_price_eur_kwh',
'lighting_investment_eur',
'ventilation_fan_power_w',
'ventilation_schedule_hours_day',
'ventilation_proposed_hours_day',
'heating_energy_kwh_year',
'heating_reduction_pct',
'cooling_capacity_kw',
'cooling_hours_year',
'cooling_eer_existing',
'cooling_eer_proposed'
];
ledFields.forEach(k=>{
    o[k]=o[k]!==undefined && o[k]!=='' ? Number(o[k]) : null;
});
o.meter_separation=f.has('meter_separation');return o}
async function post(url,body){const response=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});if(!response.ok){let err=await response.json().catch(()=>({}));throw Error(typeof err.detail==='string'?err.detail:JSON.stringify(err.detail||'Erreur du serveur'))}return response}
const number=(n,d=0)=>Number(n||0).toLocaleString('fr-FR',{maximumFractionDigits:d,minimumFractionDigits:d});
function actions(id,items,empty){const root=$(id);root.replaceChildren();if(!items.length){const p=document.createElement('p');p.className='muted';p.textContent=empty;root.append(p);return}items.forEach(item=>{const el=document.createElement('div');el.className='action';const strong=document.createElement('strong');strong.textContent=item.title||item.category||'Recommandation';const p=document.createElement('div');p.textContent=item.detail||item.basis||'';el.append(strong,p);
if(item.simulation && item.simulation.available){
    const sim=document.createElement('div');
    sim.className='muted';
    sim.textContent=({
    'Ventilation': 'Economies ventilation estimees : ',
    'Chauffage': 'Economies chauffage estimees : ',
    'Climatisation': 'Economies climatisation estimees : ',
    'Eclairage': 'Economies LED estimees : '
}[item.category] || 'Economies energetiques estimees : ')
        +number(item.simulation.savings_kwh_year)
        +' kWh/an ('+number(item.simulation.savings_pct,1)+' %)';
    el.append(sim);

    if(item.economics && item.economics.available){
        const eco=document.createElement('div');
        eco.className='muted';
        eco.textContent='Gain financier estime : '
            +number(item.economics.annual_savings_eur,2)
            +' EUR/an'
            +(item.economics.payback_years!==null
                ? ' | Retour simple : '+number(item.economics.payback_years,2)+' ans'
                : '');
        el.append(eco);
    }
}
root.append(el)})}


function renderEnergyBreakdown(bilan) {
    const root = $('energyBreakdownContent');
    if (!root) return;
    root.replaceChildren();

    if (!bilan) {
        const p = document.createElement('p');
        p.className = 'muted';
        p.textContent = 'Bilan \u00e9nerg\u00e9tique indisponible.';
        root.append(p);
        return;
    }

    function element(tag, className, content) {
        const node = document.createElement(tag);
        if (className) node.className = className;
        if (content !== undefined) node.textContent = content;
        return node;
    }

    const summary = element('div', 'energy-summary');
    summary.append(
        element('div', 'energy-summary-label',
            'CONSOMMATION \u00c9NERG\u00c9TIQUE ANNUALIS\u00c9E'),
        element('div', 'energy-summary-value',
            number(bilan.total_kwh_year) + ' kWh/an')
    );
    root.append(summary);

    root.append(element('h4', 'energy-section-title',
        'Consommations par \u00e9nergie'));

    const colors = {
        electricity: '#078ca6',
        gas: '#49b9a8',
        district: '#9cb3df',
        other: '#9062d0'
    };

    Object.entries(bilan.by_energy || {}).forEach(([key, item]) => {
        const value = Number(item.kwh_year || 0);
        const total = Number(bilan.total_kwh_year || 0);
        const percent = total > 0 ? 100 * value / total : 0;

        const row = element('div', 'energy-row');
        const label = element('div', 'energy-row-label', item.label);
        const bar = element('div', 'energy-bar');
        const fill = element('div', 'energy-bar-fill');

        fill.style.width = Math.max(0, Math.min(100, percent)) + '%';
        fill.style.background = colors[key] || '#078ca6';
        bar.append(fill);

        const valueBox = element('div', 'energy-row-value',
            number(value) + ' kWh/an');

        row.append(label, bar, valueBox);
        root.append(row);
    });

    root.append(element('h4', 'energy-section-title',
        'Consommations par poste'));

    Object.entries(bilan.by_use || {}).forEach(([key, item]) => {
        const row = element('div', 'energy-row');
        const labelBox = element('div', '');

        labelBox.append(
            element('div', 'energy-row-label', item.label)
        );

        const sources = {
            declared: 'Donn\u00e9e d\u00e9clar\u00e9e',
            declared_annualized: 'Donn\u00e9e d\u00e9clar\u00e9e / annualis?e',
            theoretical: 'Calcul th\u00e9orique',
            not_quantified: 'Non quantifi\u00e9'
        };

        labelBox.append(
            element('div', 'energy-source',
                sources[item.source] || 'Origine non pr\u00e9cis\u00e9e')
        );

        const value = item.kwh_year === null
            ? '?'
            : number(item.kwh_year) + ' kWh/an';

        const valueBox = element('div', 'energy-row-value', value);

        row.append(labelBox, element('div', ''), valueBox);
        root.append(row);
    });

    root.append(
        element('p', 'muted',
            'Les consommations par poste sont d\u00e9clar\u00e9es ou th\u00e9oriques. ' +
            'Elles ne sont pas additionn\u00e9es au total par \u00e9nergie.')
    );
}


function renderEnergyIntelligence(analysis) {
    const root = $('energyIntelligenceContent');
    if (!root) return;
    root.replaceChildren();

    function make(tag, className, value) {
        const el = document.createElement(tag);
        if (className) el.className = className;
        if (value !== undefined) el.textContent = value;
        return el;
    }

    if (!analysis) {
        root.append(make('p', 'muted',
            'Analyse \u00e9nerg\u00e9tique indisponible.'));
        return;
    }

    const quality = analysis.data_quality || {};
    const statuses = {
        incomplete: 'Donn\u00e9es incompl\u00e8tes',
        estimated: 'Donn\u00e9es estim\u00e9es',
        declared: 'Donn\u00e9es d\u00e9clar\u00e9es',
        unavailable: 'Donn\u00e9es indisponibles'
    };

    const summary = make('div', 'energy-summary');
    summary.append(
        make('div', 'energy-summary-label',
            'QUALIT\u00c9 DES DONN\u00c9ES'),
        make('div', 'energy-row-label',
            statuses[quality.status] || 'Non \u00e9valu\u00e9e'),
        make('p', 'muted',
            (quality.quantified_uses || 0) + ' postes quantifi\u00e9s \u00b7 ' +
            (quality.theoretical_uses || 0) + ' estimations th\u00e9oriques \u00b7 ' +
            (quality.missing_uses || 0) + ' postes non quantifi\u00e9s')
    );
    root.append(summary);

    root.append(make('h4', 'energy-section-title',
        'Observations du diagnostic'));

    const observations = analysis.observations || [];

    if (!observations.length) {
        root.append(make('p', 'muted',
            'Aucune observation disponible.'));
    }

    observations.forEach(item => {
        const isWarning =
            item.severity === 'warning' ||
            item.type === 'electricity_inconsistency';

        const card = make(
            'div',
            isWarning ? 'action energy-warning' : 'action'
        );

        card.style.marginBottom = '10px';

        if (isWarning) {
            card.append(
                make('span', 'energy-warning-label',
                    '\u00c0 V\u00c9RIFIER')
            );
        }

        card.append(
            make('strong', '', item.title || 'Observation'),
            make('div', '', item.detail || '')
        );

        root.append(card);
    });

    const uses = analysis.ranked_uses || [];

    if (uses.length) {
        root.append(make('h4', 'energy-section-title',
            'Classement indicatif des postes quantifi\u00e9s'));

        uses.forEach((item, index) => {
            const row = make('div', 'energy-row');
            row.append(
                make('div', 'energy-row-label',
                    (index + 1) + '. ' + item.label),
                make('div', 'energy-source',
                    item.source === 'theoretical'
                        ? 'Estimation th\u00e9orique'
                        : 'Donn\u00e9e d\u00e9clar\u00e9e'),
                make('div', 'energy-row-value',
                    number(item.kwh_year, 0) + ' kWh/an')
            );
            root.append(row);
        });
    }

    root.append(make('p', 'muted',
        'Analyse indicative : les consommations th\u00e9oriques ' +
        'ne constituent pas des mesures et ne sont pas additionn\u00e9es ' +
        'au total par \u00e9nergie.'));
}

function render(result){
renderEnergyBreakdown(result.energy_breakdown);
renderEnergyIntelligence(result.energy_intelligence);
const d=result.data,c=result.carbon,s=result.savings;$('m-consumption').textContent=number(d.total_kwh);$('m-intensity').textContent=number(d.intensity,1);$('m-cost').textContent=number(d.annual_cost);$('m-carbon').textContent=number(c.total_tonnes,2);$('savings').textContent=number(s.low_kwh)+' – '+number(s.high_kwh);actions('topActions',result.recommendations.slice(0,3),'Aucune action proposée');actions('alerts',result.diagnosis.alerts,'Aucune alerte détectée avec les données renseignées.');actions('recommendations',result.recommendations,'Aucune recommandation disponible.');const ctx=$('energyChart');if(chart)chart.destroy();if(window.Chart){chart=new Chart(ctx,{type:'doughnut',data:{labels:['Électricité','Gaz','Réseau de chaleur'],datasets:[{data:[d.electricity,d.gas,d.district],backgroundColor:['#078eaa','#49b9a8','#9cb3df'],borderWidth:0,hoverOffset:5}]},options:{responsive:true,maintainAspectRatio:false,cutout:'70%',plugins:{legend:{position:'bottom',labels:{usePointStyle:true,padding:20}}}}})}else{ctx.replaceWith(document.createTextNode('Électricité : '+number(d.electricity)+' kWh · Gaz : '+number(d.gas)+' kWh · Réseau : '+number(d.district)+' kWh'))}}
$('auditForm').addEventListener('submit',async e=>{e.preventDefault();const btn=$('analyzeBtn');btn.disabled=true;btn.textContent='Analyse en cours…';try{const p=payload(),r=await (await post('/api/analyze',p)).json();lastAudit=p;lastResult=r;render(r);if(selectedBuildingId){try{await post('/api/v8/buildings/'+encodeURIComponent(selectedBuildingId)+'/audits',p)}catch(saveError){notice('Diagnostic calculé mais historique non enregistré : '+saveError.message,true)}}notice('Diagnostic effectué avec le moteur V5.');go('dashboard')}catch(err){notice(err.message,true)}finally{btn.disabled=false;btn.textContent='Lancer le diagnostic →'}});
function bubble(text,who){const el=document.createElement('div');el.className='chat-message '+who;el.textContent=text;$('chat').append(el);$('chat').scrollTop=$('chat').scrollHeight}
$('askForm').addEventListener('submit',async e=>{e.preventDefault();if(!lastAudit){notice('Lancez d’abord un diagnostic dans Bâtiment.',true);go('building');return}const input=$('question'),q=input.value.trim();if(!q)return;input.value='';bubble(q,'user');try{const r=await(await post('/api/ask',{audit:lastAudit,question:q})).json();bubble(r.answer,'bot')}catch(err){bubble('Erreur : '+err.message,'bot')}});
$('downloadReport').addEventListener('click',async()=>{
 const btn=$('downloadReport');
 if(!lastAudit){notice('Lancez d’abord un diagnostic dans Bâtiment pour créer le rapport.',true);go('building');return}
 btn.disabled=true;btn.textContent='Génération du PDF…';
 try{
  const r=await post('/api/report',lastAudit);
  const blob=await r.blob();
  if(!blob.type.includes('pdf'))throw Error('Le serveur n’a pas renvoyé un PDF.');
  const url=URL.createObjectURL(blob),a=document.createElement('a');
  a.href=url;a.download='ENERGIA_AI_Rapport_Energetique.pdf';document.body.appendChild(a);a.click();a.remove();
  setTimeout(()=>URL.revokeObjectURL(url),30000);
  notice('Rapport PDF généré. Vérifiez votre dossier Téléchargements.');
 }catch(err){notice('Rapport PDF : '+err.message,true)}
 finally{btn.disabled=false;btn.textContent='↓ Générer le rapport PDF'}
});

// Recherche et sélection explicite du DPE, sans écraser les factures utilisateur.
let addressLocations=[],dpeCandidates=[];
function lookupMessage(target,message){const p=document.createElement('p');p.className='muted';p.textContent=message;$(target).replaceChildren(p)}
$('searchAddress').addEventListener('click',async()=>{
 const q=$('addressQuery').value.trim();if(q.length<5){notice('Saisissez une adresse complète.',true);return}
 lookupMessage('addressMatches','Recherche des adresses…');$('dpeMatches').replaceChildren();
 try{const r=await(await post('/api/address/search',{address:q})).json();addressLocations=r.locations||[];
 const root=$('addressMatches');root.replaceChildren();if(!addressLocations.length){lookupMessage('addressMatches','Aucune adresse trouvée. Saisie manuelle possible.');return}
 addressLocations.forEach((loc,i)=>{const b=document.createElement('button');b.type='button';b.className='lookup-choice';b.textContent=loc.address;b.addEventListener('click',()=>selectAddress(i));root.append(b)});
 }catch(err){lookupMessage('addressMatches',err.message)}
});
async function selectAddress(i){const loc=addressLocations[i];$('auditForm').elements.namedItem('address').value=loc.address;
 lookupMessage('addressMatches','Adresse retenue : '+loc.address);lookupMessage('dpeMatches','Recherche des DPE ADEME en cours…');
 try{const r=await(await post('/api/address/dpe',{location:loc})).json();dpeCandidates=r.dpe||[];
 const root=$('dpeMatches');root.replaceChildren();
 if(!dpeCandidates.length)lookupMessage('dpeMatches','Aucun DPE correspondant trouvé. Complétez les données manuellement.');
 dpeCandidates.forEach((d,j)=>{const b=document.createElement('button');b.type='button';b.className='lookup-choice';b.textContent=`DPE ${d.id||'sans numéro'} · ${d.kind||''} · ${d.address||''} · ${d.surface_m2||'?'} m² · classe ${d.energy_class||'?'}`;b.addEventListener('click',()=>selectDpe(j));root.append(b)});
 $('dpeWarning').textContent=(r.warnings||[]).join(' | ')||'Vérifiez que le DPE correspond bien au bâtiment ou au logement audité.';
 }catch(err){lookupMessage('dpeMatches',err.message)}
}
async function selectDpe(i){try{const d=dpeCandidates[i],r=await(await post('/api/address/prefill',{candidate:d})).json(),f=$('auditForm').elements;
 if(r.surface_m2>0)f.namedItem('surface').value=r.surface_m2;
 const year=Number(r.construction_year);if(Number.isInteger(year)&&year>=1800&&year<=2100)f.namedItem('construction_year').value=year;
 const energy=String(r.heating_energy||r.heating_type||'').toLowerCase();let heat='unknown';if(energy.includes('élec')||energy.includes('elec'))heat='electric';else if(energy.includes('gaz'))heat='gas';else if(energy.includes('réseau')||energy.includes('reseau'))heat='district';else if(energy.includes('pompe')||energy.includes('pac'))heat='heat_pump';if(heat!=='unknown')f.namedItem('heating_type').value=heat;
 $('dpeWarning').textContent=`DPE ${r.dpe_id||''} sélectionné. ${r.scope_warning||''} Vérifiez la surface et le chauffage. Renseignez séparément les consommations réelles et le coût annuel : les valeurs préexistantes sont des exemples, pas des données ADEME.`;
 notice('DPE sélectionné : caractéristiques disponibles préremplies. Vérifiez les données avant le diagnostic.');
 }catch(err){notice(err.message,true)}
}

// V8 local portfolio; the existing V5 audit workflow remains unchanged.
let selectedBuildingId=null;
async function refreshPortfolio(){
 const root=$('portfolioList');root.replaceChildren();
 try{
  const response=await fetch('/api/v8/buildings');if(!response.ok)throw Error('Portefeuille indisponible');
  const data=await response.json();if(!data.buildings.length){lookupMessage('portfolioList','Aucun bâtiment enregistré.');return}
  for(const item of data.buildings){
   const row=document.createElement('div');row.className='action';
   const title=document.createElement('strong');title.textContent=item.name;
   const desc=document.createElement('p');desc.className='muted';desc.textContent=item.address||'Adresse non renseignée';
   const open=document.createElement('button');open.className='secondary';open.textContent='Charger le bâtiment';
   open.addEventListener('click',async()=>{
    try{const r=await fetch('/api/v8/buildings/'+encodeURIComponent(item.id));if(!r.ok)throw Error('Chargement impossible');const data=await r.json();
    const f=$('auditForm').elements;for(const [key,value] of Object.entries(data.input)){const field=f.namedItem(key);if(!field)continue;if(field.type==='checkbox')field.checked=!!value;else field.value=value??''}
    selectedBuildingId=item.id;lastAudit=null;lastResult=null;notice('Bâtiment chargé. Lancez un diagnostic pour actualiser les résultats.');go('building');
    }catch(err){notice(err.message,true)}
   });
   const history=document.createElement('button');history.className='secondary';history.textContent='Historique des audits';
   history.addEventListener('click',async()=>{
    try{const r=await fetch('/api/v8/buildings/'+encodeURIComponent(item.id)+'/audits');if(!r.ok)throw Error('Historique indisponible');const d=await r.json();
    const historyBox=document.createElement('div');historyBox.className='muted';historyBox.textContent=d.audits.length?d.audits.map(a=>new Date(a.created_at).toLocaleString('fr-FR')+' · '+a.id.slice(0,8)).join(' | '):'Aucun audit enregistré';row.append(historyBox);
    }catch(err){notice(err.message,true)}
   });row.append(title,desc,open,history);root.append(row)
  }
 }catch(err){notice(err.message,true)}
}
$('refreshPortfolio').addEventListener('click',refreshPortfolio);
$('saveBuilding').addEventListener('click',async()=>{
 try{const r=await post('/api/v8/buildings',payload());const data=await r.json();selectedBuildingId=data.id;notice('Bâtiment enregistré dans votre espace professionnel.');await refreshPortfolio();}
 catch(err){notice(err.message,true)}
});
// Persist audit results after a successful existing V5 calculation, when a building is selected.
$('auditForm').addEventListener('submit',async()=>{
 // The original handler runs first; wait for its async result without changing it.
 // Explicit saving is available through the portfolio-specific endpoint below.
});
refreshPortfolio();
