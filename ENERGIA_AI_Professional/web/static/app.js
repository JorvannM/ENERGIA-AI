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
'cooling_eer_proposed',
'ventilation_investment_eur',
'heating_investment_eur',
'cooling_investment_eur',
'gas_price_eur_kwh',
'district_price_eur_kwh',
'heating_energy_price_eur_kwh'
];
ledFields.forEach(k=>{
    o[k]=o[k]!==undefined && o[k]!=='' ? Number(o[k]) : null;
});
o.meter_separation=f.has('meter_separation');return o}
async function post(url,body){const response=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});if(!response.ok){let err=await response.json().catch(()=>({}));throw Error(typeof err.detail==='string'?err.detail:JSON.stringify(err.detail||'Erreur du serveur'))}return response}
const number=(n,d=0)=>Number(n||0).toLocaleString('fr-FR',{maximumFractionDigits:d,minimumFractionDigits:d});

function actions(id, items, empty) {
    const root = $(id);
    root.replaceChildren();

    if (!items.length) {
        const p = document.createElement('p');
        p.className = 'muted';
        p.textContent = empty;
        root.append(p);
        return;
    }

    const priorityOrder = {
        verification: 0,
        optimization: 1,
        investigation: 2
    };

    const sorted = id === 'recommendations'
        ? [...items].sort((a, b) =>
            (priorityOrder[a.action_type] ?? 3) -
            (priorityOrder[b.action_type] ?? 3)
        )
        : items;

    sorted.forEach(item => {
        const el = document.createElement('div');
        el.className = 'action';

        const title = item.title || item.category || 'Recommandation';
        const detail = item.detail || item.basis || '';

        const strong = document.createElement('strong');
        strong.textContent = title;
        el.append(strong);

        const normalize = value =>
            String(value || '').trim().replace(/\\s+/g, ' ').toLowerCase();

        const sameText = normalize(title) === normalize(detail);

        if (detail && !sameText && !(item.simulation?.available)) {
            const p = document.createElement('div');
            p.textContent = detail;
            el.append(p);
        }

        if (item.action_type) {
            const priority = document.createElement('div');
            priority.className = 'muted';
            priority.style.marginTop = '8px';
            priority.style.fontWeight = '600';

            const labels = {
                verification: '\u26a0 V\u00e9rification prioritaire',
                optimization: '\u2713 Am\u00e9lioration \u00e0 \u00e9tudier',
                investigation: '\u2139 Analyse compl\u00e9mentaire'
            };

            priority.textContent =
                labels[item.action_type] || item.priority || '';

            el.append(priority);
        }

        if (Array.isArray(item.checks) && item.checks.length) {
            const checks = document.createElement('div');
            checks.className = 'muted';
            checks.style.marginTop = '6px';
            checks.textContent =
                '\u00c0 v\u00e9rifier : ' + item.checks.join(' \u2022 ');
            el.append(checks);
        }

        if (item.simulation?.available) {
            const sim = document.createElement('div');
            sim.className = 'muted';

            sim.textContent =
                'Economies estimees : ' +
                number(item.simulation.savings_kwh_year) +
                ' kWh/an (' +
                number(item.simulation.savings_pct, 1) +
                ' %)';

            el.append(sim);

            if (item.economics?.available) {
                const eco = document.createElement('div');
                eco.className = 'muted';

                eco.textContent =
                    'Gain financier estime : ' +
                    number(item.economics.annual_savings_eur, 2) +
                    ' EUR/an' +
                    (item.economics.payback_years != null
                        ? ' | Retour simple : ' +
                          number(item.economics.payback_years, 2) +
                          ' ans'
                        : '');

                el.append(eco);
            }
        }

        root.append(el);
    });
}


function renderEconomicComparison(recommendations) {
    const root = document.getElementById('economicComparison');
    if (!root) return;

    root.replaceChildren();

    const items = (recommendations || [])
        .filter(item =>
            item.simulation?.available &&
            item.economics?.available
        )
        .sort((a, b) => {
            const x = a.economics.payback_years;
            const y = b.economics.payback_years;
            return (x == null ? Infinity : x) -
                   (y == null ? Infinity : y);
        });

    if (!items.length) {
        const empty = document.createElement('p');
        empty.className = 'muted';
        empty.textContent =
            'Aucune comparaison financiere disponible. Renseignez les tarifs energetiques.';
        root.append(empty);
        return;
    }

    items.forEach((item, index) => {
        const card = document.createElement('div');
        card.className = 'action-item';

        const title = document.createElement('strong');
        title.textContent = (index + 1) + '. ' + item.title;

        const details = document.createElement('p');
        details.className = 'muted';

        const eco = item.economics;
        const sim = item.simulation;

        details.textContent =
            'Economies : ' + number(sim.savings_kwh_year, 0) + ' kWh/an' +
            ' | Gains : ' + number(eco.annual_savings_eur, 2) + ' EUR/an' +
            ' | Investissement : ' +
            (eco.investment_eur == null
                ? 'non renseigne'
                : number(eco.investment_eur, 2) + ' EUR') +
            ' | Retour simple : ' +
            (eco.payback_years == null
                ? 'non calculable'
                : number(eco.payback_years, 2) + ' ans');

        card.append(title, details);
        root.append(card);
    });
}

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
renderEconomicComparison(result.recommendations);
renderEnergyBreakdown(result.energy_breakdown);
renderEnergyIntelligence(result.energy_intelligence);
const d=result.data,c=result.carbon,s=result.savings;$('m-consumption').textContent=number(d.total_kwh);$('m-intensity').textContent=number(d.intensity,1);$('m-cost').textContent=number(d.annual_cost);$('m-carbon').textContent=number(c.total_tonnes,2);$('savings').textContent=number(s.low_kwh)+' – '+number(s.high_kwh);actions('topActions',result.recommendations.slice(0,3),'Aucune action proposée');actions('alerts',result.diagnosis.alerts,'Aucune alerte détectée avec les données renseignées.');actions('recommendations',result.recommendations,'Aucune recommandation disponible.');const ctx=$('energyChart');if(chart)chart.destroy();if(window.Chart){chart=new Chart(ctx,{type:'doughnut',data:{labels:['Électricité','Gaz','Réseau de chaleur'],datasets:[{data:[d.electricity,d.gas,d.district],backgroundColor:['#078eaa','#49b9a8','#9cb3df'],borderWidth:0,hoverOffset:5}]},options:{responsive:true,maintainAspectRatio:false,cutout:'70%',plugins:{legend:{position:'bottom',labels:{usePointStyle:true,padding:20}}}}})}else{ctx.replaceWith(document.createTextNode('Électricité : '+number(d.electricity)+' kWh · Gaz : '+number(d.gas)+' kWh · Réseau : '+number(d.district)+' kWh'))}}
$('auditForm').addEventListener('submit',async e=>{e.preventDefault();const btn=$('analyzeBtn');btn.disabled=true;btn.textContent='Analyse en cours…';try{const p=payload(),r=await (await post('/api/analyze',p)).json();lastAudit=p;lastResult=r;render(r);if(selectedBuildingId){try{await post('/api/v8/buildings/'+encodeURIComponent(selectedBuildingId)+'/audits',p)}catch(saveError){notice('Diagnostic calculé mais historique non enregistré : '+saveError.message,true)}}notice('Diagnostic effectué avec le moteur V5.');go('dashboard')}catch(err){notice(err.message,true)}finally{btn.disabled=false;btn.textContent='Lancer le diagnostic →'}});
function bubble(text,who){const el=document.createElement('div');el.className='chat-message '+who;el.textContent=text;$('chat').append(el);$('chat').scrollTop=$('chat').scrollHeight}

/* ENERGIA_ADVISOR_DUAL_MODE_V8 */
(function () {
  const form = document.getElementById('askForm');
  const input = document.getElementById('question');
  const status = document.getElementById(
    'energiaAdvisorModeStatus'
  );

  if (!form || !input) return;

  function currentMode() {
    const selected = document.querySelector(
      'input[name="energiaAdvisorMode"]:checked'
    );

    return selected ? selected.value : 'building';
  }

  function updateStatus() {
    if (!status) return;

    const labels = {
      building: 'diagnostic batiment',
      consumption: 'consommations importees',
      combined: 'analyse combinee'
    };

    status.textContent =
      'Mode actuel : ' +
      (labels[currentMode()] || labels.building) + '.';
  }

  document.querySelectorAll(
    'input[name="energiaAdvisorMode"]'
  ).forEach(radio => {
    radio.addEventListener('change', updateStatus);
  });

  updateStatus();


  /* ENERGIA_ADVISOR_COMBINED_HANDLER_V8 */
  form.addEventListener('submit', async function (event) {
    if (currentMode() !== 'combined') return;

    event.preventDefault();
    event.stopImmediatePropagation();

    const question = input.value.trim();
    if (!question) return;

    if (!lastResult) {
      bubble(
        'Realisez d abord un diagnostic dans la page Batiment.',
        'assistant'
      );
      return;
    }

    input.value = '';
    bubble(question, 'user');

    try {
      const response = await post(
        '/api/consumption/combined',
        { building_result: lastResult, question: question }
      );

      if (!response.ok) {
        let detail = 'Analyse combinee indisponible.';

        try {
          const error = await response.json();
          detail = error.detail || detail;
        } catch (_) {}

        throw new Error(detail);
      }

      const data = await response.json();
      const combined = data.combined || {};
      const messages = ['Analyse energetique combinee'];

      if (combined.estimated_annual_kwh != null) {
        messages.push(
          'Estimation annuelle : ' +
          Number(combined.estimated_annual_kwh)
            .toLocaleString('fr-FR') + ' kWh'
        );
      }

      if (combined.measured_annual_kwh != null) {
        messages.push(
          'Consommation mesuree (' +
          combined.measured_year + ') : ' +
          Number(combined.measured_annual_kwh)
            .toLocaleString('fr-FR') + ' kWh'
        );
      }

      if (combined.gap_pct != null) {
        messages.push(
          'Ecart indicatif : ' +
          Number(combined.gap_pct).toFixed(1) + ' %'
        );
      }

      for (const item of combined.observations || []) {
        messages.push(
          item.title + ' : ' + item.message
        );
      }

      for (const limitation of combined.limitations || []) {
        messages.push('Limite : ' + limitation);
      }

      /* ENERGIA_COMBINED_CONTEXTUAL_ANSWERS_V8 */
      if (typeof data.answer === 'string' && data.answer.trim()) {
        bubble(data.answer, 'assistant');
      } else {
        bubble(messages.join('\\n\\n'), 'assistant');
      }

    } catch (error) {
      bubble('Erreur : ' + error.message, 'assistant');
    }
  }, true);

  form.addEventListener('submit', async function (event) {
    if (currentMode() !== 'consumption') {
      return;
    }

    event.preventDefault();
    event.stopImmediatePropagation();

    const question = input.value.trim();

    if (!question) return;

    input.value = '';

    bubble(question, 'user');

    try {
      const response = await post(
        '/api/consumption/ask',
        { question }
      );

      if (!response.ok) {
        let detail = 'Erreur du conseiller energetique.';

        try {
          const error = await response.json();
          detail = error.detail || detail;
        } catch (_) {}

        throw new Error(detail);
      }

      const data = await response.json();

      bubble(
        data.answer || 'Aucune reponse disponible.',
        'assistant'
      );

    } catch (error) {
      bubble(
        'Erreur : ' + error.message,
        'assistant'
      );
    }
  }, true);
})();

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


/* ENERGIA_CONSUMPTION_IMPORT_V8 */
(function () {
  const form = document.getElementById('consumptionImportForm');
  if (!form) return;

  const status = document.getElementById('consumptionImportStatus');
  const results = document.getElementById('consumptionImportResults');

  function addText(parent, tag, value) {
    const element = document.createElement(tag);
    element.textContent = value;
    parent.appendChild(element);
  }

  form.addEventListener('submit', async function (event) {
    event.preventDefault();
    results.replaceChildren();

    const file = document.getElementById('consumptionFile').files[0];

    if (!file) {
      status.textContent = 'Selectionnez un fichier.';
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      status.textContent = 'Fichier trop volumineux (5 Mo maximum).';
      return;
    }

    const button = form.querySelector('button[type="submit"]');
    button.disabled = true;
    status.textContent = 'Analyse en cours...';

    try {
      const data = new FormData();
      data.append('file', file);

      const response = await fetch('/api/consumption/import', {
        method: 'POST',
        body: data
      });

      const payload = await response.json();

      if (!response.ok) {
        throw new Error(
          typeof payload.detail === 'string'
            ? payload.detail
            : 'Importation impossible.'
        );
      }

      /* ENERGIA_IMPORT_TO_AUDIT_V8 */
      (function () {
        const records = Array.isArray(payload.records) ? payload.records : [];

        const years = [...new Set(
          records.map(r => Number(r.year)).filter(Number.isFinite)
        )].sort((a, b) => b - a);

        if (!years.length) return;

        const latestYear = years[0];
        const annual = records.filter(r => Number(r.year) === latestYear);

        const totals = {
          electricity: 0,
          gas: 0,
          district: 0,
          annual_cost: 0
        };

        for (const record of annual) {
          const energy = String(record.energy || '').trim().toLowerCase();
          const kwh = Number(record.kwh);
          const cost = Number(record.cost_eur);

          if (!Number.isFinite(kwh) || kwh < 0) continue;

          if (['electricity', 'electricite', '?lectricit?', 'electric'].includes(energy)) {
            totals.electricity += kwh;
          } else if (['gas', 'gaz'].includes(energy)) {
            totals.gas += kwh;
          } else if (['district', 'reseau', 'r?seau', 'district_heating'].includes(energy)) {
            totals.district += kwh;
          } else {
            continue;
          }

          if (Number.isFinite(cost) && cost >= 0) {
            totals.annual_cost += cost;
          }
        }

        const transferButton = document.createElement('button');
        transferButton.type = 'button';
        transferButton.className = 'primary';
        transferButton.textContent = 'Utiliser ces consommations pour l\u2019audit';

        transferButton.addEventListener('click', function () {
          const auditForm = document.getElementById('auditForm');

          if (!auditForm) {
            status.textContent = 'Formulaire d?audit introuvable.';
            return;
          }

          const fields = auditForm.elements;

          for (const key of ['electricity', 'gas', 'district', 'annual_cost']) {
            const field = fields.namedItem(key);
            if (field) field.value = String(
              Math.round(totals[key] * 100) / 100
            );
          }

          lastAudit = null;
          lastResult = null;

          go('building');

          notice(
            'Consommations ' + latestYear +
            ' import\u00e9es. V\u00e9rifiez la surface, les \u00e9quipements et les co\u00fbts avant le diagnostic.'
          );
        });

        const transferPanel = document.createElement('div');
        transferPanel.className = 'panel';
        transferPanel.style.marginTop = '16px';

        const heading = document.createElement('h3');
        heading.textContent = 'Poursuivre vers l\u2019audit \u00e9nerg\u00e9tique';

        const description = document.createElement('p');
        description.textContent =
          'Les consommations de ' + latestYear +
          ' seront transf\u00e9r\u00e9es dans le formulaire B\u00e2timent. ' +
          'Les caract\u00e9ristiques techniques resteront \u00e0 v\u00e9rifier.';

        transferPanel.append(heading, description, transferButton);
        results.appendChild(transferPanel);
      })();

      const analysis = payload.analysis;

      /* ENERGIA_ANNUAL_COMPARISON_V8 */
      const annualReport = payload.comparison;

      if (annualReport?.available) {
        const panel = document.createElement('section');
        panel.className = 'panel';

        addText(panel, 'h3', 'Comparaison annuelle des consommations');

        const annual = annualReport.annual || [];
        const years = [...new Set(annual.map(x => x.year))].sort();
        const energies = [...new Set(annual.map(x => x.energy))];

        const energyLabels = {
          electricity: 'Electricite',
          electricite: 'Electricite',
          gas: 'Gaz',
          gaz: 'Gaz',
          district: 'Reseau de chaleur',
          reseau: 'Reseau de chaleur'
        };

        const colors = [
          '#2563eb',
          '#16a34a',
          '#f59e0b',
          '#8b5cf6'
        ];

        if (typeof Chart !== 'undefined') {
          const container = document.createElement('div');
          container.style.position = 'relative';
          container.style.height = '340px';

          const canvas = document.createElement('canvas');
          container.appendChild(canvas);
          panel.appendChild(container);

          const datasets = energies.map((energy, index) => ({
            label: energyLabels[energy] || energy,
            data: years.map(year => {
              const item = annual.find(
                x => x.year === year && x.energy === energy
              );
              return item ? item.total_kwh : null;
            }),
            backgroundColor: colors[index % colors.length]
          }));

          if (window.energiaAnnualChart) {
            window.energiaAnnualChart.destroy();
          }

          window.energiaAnnualChart = new Chart(canvas, {
            type: 'bar',
            data: {
              labels: years.map(String),
              datasets
            },
            options: {
              responsive: true,
              maintainAspectRatio: false,
              plugins: {
                legend: { position: 'bottom' }
              },
              scales: {
                y: {
                  beginAtZero: true,
                  title: {
                    display: true,
                    text: 'Consommation annuelle (kWh)'
                  }
                }
              }
            }
          });
        }

        for (const item of annual) {
          addText(
            panel,
            'p',
            (energyLabels[item.energy] || item.energy) +
            ' - ' + item.year +
            ' : ' +
            Number(item.total_kwh).toLocaleString('fr-FR') +
            ' kWh (' + item.months_count + '/12 mois)'
          );
        }

        for (const item of annualReport.comparisons || []) {
          const energy = energyLabels[item.energy] || item.energy;

          if (item.comparable && item.variation_pct !== null) {
            const sign = item.variation_pct > 0 ? '+' : '';

            addText(
              panel,
              'p',
              energy + ' : ' +
              item.previous_year + ' / ' + item.current_year +
              ' : ' + sign + item.variation_pct + ' %'
            );
          } else {
            addText(
              panel,
              'p',
              energy + ' : comparaison ' +
              item.previous_year + ' / ' + item.current_year +
              ' non fiable (annee incomplete ou reference nulle).'
            );
          }
        }

        if (annualReport.limitations) {
          const note = document.createElement('p');
          note.className = 'muted';
          note.textContent = annualReport.limitations;
          panel.appendChild(note);
        }

        results.appendChild(panel);
      }



      /* ENERGIA_ANOMALY_DISPLAY_V8 */
      const anomalyReport = payload.anomalies;

      if (anomalyReport) {
        const anomalyPanel = document.createElement('section');
        anomalyPanel.className = 'panel';

        addText(
          anomalyPanel,
          'h3',
          'Detection des anomalies energetiques'
        );

        const count = anomalyReport.anomaly_count || 0;

        addText(
          anomalyPanel,
          'p',
          count === 0
            ? 'Aucune anomalie detectee avec les regles actuelles.'
            : count + ' signalement(s) a examiner.'
        );

        const energyLabels = {
          electricity: 'Electricite',
          electricite: 'Electricite',
          gas: 'Gaz',
          gaz: 'Gaz',
          district: 'Reseau de chaleur',
          reseau: 'Reseau de chaleur'
        };

        const typeLabels = {
          high_consumption: 'Pic de consommation',
          low_consumption: 'Baisse inhabituelle',
          sudden_change: 'Variation importante',
          missing_data: 'Donnees manquantes'
        };

        const alerts = [...(anomalyReport.anomalies || [])];

        alerts.sort((a, b) => {
          const rank = {warning: 0, info: 1};
          return (rank[a.severity] ?? 2) -
                 (rank[b.severity] ?? 2);
        });

        for (const alert of alerts) {
          const item = document.createElement('article');
          item.className = 'action';

          const title = document.createElement('strong');

          title.textContent =
            (alert.severity === 'warning' ? '\u26a0 ' : '\u2139 ') +
            (typeLabels[alert.type] || alert.type);

          item.appendChild(title);

          const energy =
            energyLabels[alert.energy] || alert.energy;

          addText(
            item,
            'p',
            energy + ' - ' +
            String(alert.month).padStart(2, '0') +
            '/' + alert.year
          );

          addText(item, 'p', alert.message);

          if (alert.variation_pct !== undefined) {
            addText(
              item,
              'p',
              'Variation : ' + alert.variation_pct + ' %'
            );
          }

          anomalyPanel.appendChild(item);
        }

        if (anomalyReport.limitations) {
          const note = document.createElement('p');
          note.className = 'muted';
          note.textContent = anomalyReport.limitations;
          anomalyPanel.appendChild(note);
        }

        results.appendChild(anomalyPanel);
      }



      const number = value =>
        Number(value).toLocaleString('fr-FR', {
          maximumFractionDigits: 2
        });

      status.textContent =
        'Importation reussie : ' + payload.record_count + ' lignes.';



      /* ENERGIA_CONSUMPTION_CHART_V8 */
      if (typeof Chart !== 'undefined' && analysis.monthly?.length) {
        addText(results, 'h3', 'Evolution mensuelle par energie');

        const canvas = document.createElement('canvas');
        const container = document.createElement('div');

        container.style.position = 'relative';
        container.style.height = '340px';
        container.style.width = '100%';

        container.appendChild(canvas);
        results.appendChild(container);

        const periods = analysis.monthly.map(
          p => `${p.year}-${String(p.month).padStart(2, '0')}`
        );

        const labels = analysis.monthly.map(
          p => `${String(p.month).padStart(2, '0')}/${p.year}`
        );

        const energyNames = {
          electricity: 'Electricite',
          electricite: 'Electricite',
          gas: 'Gaz',
          gaz: 'Gaz',
          district: 'Reseau de chaleur',
          reseau: 'Reseau de chaleur'
        };

        const energyColors = {
          'Electricite': '#2563eb',
          'Gaz': '#16a34a',
          'Reseau de chaleur': '#f59e0b'
        };

        const series = {};

        for (const record of payload.records) {
          const key = energyNames[
            String(record.energy).trim().toLowerCase()
          ] || String(record.energy);

          const period =
            `${record.year}-${String(record.month).padStart(2, '0')}`;

          if (!series[key]) series[key] = {};

          series[key][period] =
            (series[key][period] || 0) + Number(record.kwh);
        }

        const datasets = Object.entries(series).map(
          ([energy, values]) => ({
            label: energy,
            data: periods.map(p => values[p] ?? null),
            borderColor: energyColors[energy] || '#64748b',
            backgroundColor: energyColors[energy] || '#64748b',
            tension: 0.3,
            pointRadius: 4,
            spanGaps: false
          })
        );

        if (window.energiaConsumptionChart) {
          window.energiaConsumptionChart.destroy();
        }

        window.energiaConsumptionChart = new Chart(canvas, {
          type: 'line',
          data: { labels, datasets },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
              mode: 'index',
              intersect: false
            },
            plugins: {
              legend: {
                display: true,
                position: 'bottom'
              }
            },
            scales: {
              y: {
                beginAtZero: true,
                title: {
                  display: true,
                  text: 'Consommation (kWh)'
                }
              }
            }
          }
        });
      }

      addText(results, 'h3', 'Synthese des consommations');

      addText(results, 'p',
        'Consommation totale : ' + number(analysis.total_kwh) + ' kWh');

      addText(results, 'p',
        'Cout total : ' + number(analysis.total_cost_eur) + ' EUR');

      addText(results, 'p',
        'Moyenne mensuelle : ' +
        number(analysis.average_monthly_kwh) + ' kWh');

      if (analysis.peak_month) {
        addText(results, 'p',
          'Mois de consommation maximale : ' +
          analysis.peak_month.month + '/' +
          analysis.peak_month.year + ' (' +
          number(analysis.peak_month.kwh) + ' kWh)');
      }

      addText(results, 'p',
        'Periodes analysees : ' + analysis.period_count);

    } catch (error) {
      status.textContent = 'Erreur : ' + error.message;
    } finally {
      button.disabled = false;
    }
  });
})();
