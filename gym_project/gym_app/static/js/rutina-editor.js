document.querySelectorAll('.builder-day').forEach(day => {
    const rows = day.querySelector('.routine-rows');
    const items = [...day.querySelectorAll('.catalog-item')];
    const refresh = () => day.querySelector('.empty-day').hidden = !!rows.children.length;
    function add(item, values = {}) {
        if (rows.querySelector(`[data-exercise="${item.dataset.id}"]`)) return;
        const row = document.createElement('div');
        row.className = 'routine-row'; row.dataset.exercise = item.dataset.id;
        const title = document.createElement('strong'); title.textContent = item.querySelector('span').textContent; row.append(title);
        for (const [name, value] of [['dia', day.dataset.dia], ['ejercicio_id', item.dataset.id]]) {
            const input = document.createElement('input'); input.type = 'hidden'; input.name = name; input.value = value; row.append(input);
        }
        const unit = item.dataset.type === 'tiempo' ? 'Segundos' : item.dataset.type === 'distancia' ? 'Metros' : 'Repeticiones';
        for (const [name, label, initial, max] of [['series','Series',3,20],['cantidad',unit,10,9999],['descanso','Descanso (s)',day.dataset.rest,1800]]) {
            const field = document.createElement('label'); field.textContent = label;
            const input = document.createElement('input'); input.type = 'number'; input.required = true; input.name = name;
            input.min = name === 'descanso' ? 15 : 1; input.max = max; input.value = values[name] || initial; field.append(input); row.append(field);
        }
        const remove = document.createElement('button'); remove.type = 'button'; remove.className = 'remove-row'; remove.textContent = '×'; remove.setAttribute('aria-label','Quitar ' + title.textContent);
        remove.onclick = () => {row.remove(); item.disabled = false; refresh();}; row.append(remove);
        rows.append(row); item.disabled = true; refresh();
    }
    items.forEach(item => item.onclick = () => add(item));
    const search = day.querySelector('.search-exercise'), group = day.querySelector('.group-filter');
    const normalize = s => s.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
    function filter() {items.forEach(item => item.hidden = !(normalize(item.textContent).includes(normalize(search.value)) && (!group.value || item.dataset.group === group.value)));}
    search.oninput = filter; group.onchange = filter;
    JSON.parse(document.getElementById('rutina-inicial').textContent).filter(v => String(v.dia) === day.dataset.dia).forEach(v => {
        const item = items.find(i => i.dataset.id === String(v.ejercicio_id)); if(item) add(item,v);
    });
});
