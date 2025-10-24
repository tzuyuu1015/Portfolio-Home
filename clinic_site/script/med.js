const tabLinks = document.querySelectorAll('.tab-link');
const tabPanels = document.querySelectorAll('.tab-panel');

tabLinks.forEach((tab) => {
  tab.addEventListener('click', () => {
    tabLinks.forEach((link) => link.classList.remove('active'));
    tabPanels.forEach((panel) => panel.classList.remove('active'));
    tab.classList.add('active');
    const targetPanel = document.getElementById(tab.dataset.tab);
    targetPanel.classList.add('active');
  });
});

var marqueeWrapper = document.getElementById('marquee-wrapper');
var marqueeContent = document.querySelector('.marquee-content');
var marqueeHeight = marqueeWrapper.clientHeight;

var marqueeWrapper = document.getElementById('marquee-wrapper');
var marqueeContent = document.querySelector('.marquee-content');
var marqueeHeight = marqueeWrapper.clientHeight;

function scrollMarquee() {
    marqueeContent.style.transform = 'translateY(-' + marqueeHeight + 'px)';

    setTimeout(function () {
        marqueeContent.appendChild(marqueeContent.firstElementChild);
        marqueeContent.style.transition = 'none';
        marqueeContent.style.transform = 'translateY(0)';
        setTimeout(function () {
            marqueeContent.style.transition = 'transform 1.5s ease';
        });
    }, 1500);
}

setInterval(scrollMarquee, 5000);
