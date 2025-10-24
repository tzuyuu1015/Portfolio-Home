// ---------- Tabs 點選切換 ----------
document.addEventListener('DOMContentLoaded', () => {
  const tabs = document.querySelectorAll('.tab');
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
    });
  });
});

// ---------- 感謝卡片資料 ----------
const cards = [
  {
    title: "致謝16病房護理團隊",
    date: "2026年10月5日",
    content: "感謝16病房護理團隊在近期的高峰工作中，依然以專業態度和無微不至的照顧，讓病人和家屬感受到滿滿的溫暖與支持。",
    img: "people1.png",
  },
  {
    title: "致謝兒科醫療團隊",
    date: "2026年10月6日",
    content: "感謝兒科醫療團隊耐心解答病人家屬疑問，提供專業且貼心的照護服務。",
    img: "people2.png",
  },
  {
    title: "致謝社區義診團隊",
    date: "2026年10月7日",
    content: "感謝社區義診團隊提供專業的醫療服務，讓社區居民享受到健康的關懷。",
    img: "people1.png",
  },
  {
    title: "致謝心臟內科醫療團隊",
    date: "2026年10月8日",
    content: "感謝心臟內科醫療團隊提供細心且專業的診療服務。",
    img: "people2.png",
  },
];

// 圖片資料夾的正確路徑
const IMG_BASE = "/clinic_site/images/";

let currentIndex = 0;

// ---------- 渲染卡片 ----------
function renderCards() {
  const cardsWrapper = document.querySelector(".cards-wrapper");
  if (!cardsWrapper) return;
  cardsWrapper.innerHTML = "";

  // 每次顯示兩張卡片
  for (let i = 0; i < 2; i++) {
    const cardIndex = (currentIndex + i) % cards.length;
    const c = cards[cardIndex];
    const card = document.createElement("article");
    card.className = "card";
    card.innerHTML = `
      <div class="card-header">
        <img src="${IMG_BASE}${c.img}" alt="Avatar">
        <div class="title-text4" style="text-decoration:none;margin:0;display:flex;flex-direction:column;gap:2px;">
          <div>${c.title}</div>
          <div class="date">${c.date}</div>
        </div>
      </div>
      <div class="card-content">${c.content}</div>
    `;
    cardsWrapper.appendChild(card);
  }
}

// ---------- 上一張 / 下一張 ----------
window.prevCards = function () {
  currentIndex = (currentIndex - 1 + cards.length) % cards.length;
  renderCards();
};
window.nextCards = function () {
  currentIndex = (currentIndex + 1) % cards.length;
  renderCards();
};

// ---------- 初始渲染 ----------
document.addEventListener("DOMContentLoaded", renderCards);
