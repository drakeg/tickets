// Legacy account sections remain usable without jQuery.
document.querySelectorAll('.admin-menu a[data-target-id]').forEach(link => {
    link.addEventListener('click', event => {
        const target = document.getElementById(link.dataset.targetId);
        if (!target) return;
        event.preventDefault();
        document.querySelectorAll('.admin-content').forEach(section => {
            section.hidden = section !== target;
        });
        target.scrollIntoView({block: 'start'});
    });
});
