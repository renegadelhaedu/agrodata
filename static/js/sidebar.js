const menuBtn = document.getElementById('menu-btn');
const sidebar = document.getElementById('sidebar');
const closeBtn = document.getElementById('close-btn');

menuBtn.addEventListener('click', () => {
    sidebar.style.width = "250px";
});

closeBtn.addEventListener('click', () => {
    sidebar.style.width = "0";
});

document.addEventListener("DOMContentLoaded", () => {
    const toggles = document.querySelectorAll(".submenu-toggle");
    toggles.forEach(toggle => {
        toggle.addEventListener("click", (e) => {
            e.preventDefault();
            const parent = toggle.parentElement;
            parent.classList.toggle("open");
        });
    });
});
