(() => {
    const box = document.getElementById('daily-message');
    if (!box) return;
    let busy = false;
    box.querySelector('button').onclick = () => {box.hidden = true;};
    async function check() {
        if (busy || document.hidden || !box.hidden) return;
        busy = true;
        try {
            const response = await fetch('/notificaciones/siguiente/', {method:'POST', credentials:'same-origin', headers:{'X-CSRFToken':document.querySelector('#message-token input').value,'Content-Type':'application/x-www-form-urlencoded'}, body:'entrenando=' + (location.pathname.includes('/entrenamiento/sesion/') ? '1' : '0')});
            if (response.ok) {
                const data = await response.json();
                if (data.mensaje) {box.querySelector('p').textContent = data.mensaje.mensaje; box.hidden = false;}
            }
        } catch (_) { /* No interrumpir el entrenamiento por una desconexión. */ }
        finally {busy = false;}
    }
    setTimeout(check, 1800); setInterval(check, 60000);
    document.addEventListener('visibilitychange', check);
})();
