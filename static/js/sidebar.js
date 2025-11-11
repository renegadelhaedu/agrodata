const menuBtn = document.getElementById('menu-btn');
const sidebar = document.getElementById('sidebar');
const closeBtn = document.getElementById('close-btn');

menuBtn.addEventListener('click', () => {
    sidebar.style.width = "250px";
});

closeBtn.addEventListener('click', () => {
    sidebar.style.width = "0";
});
