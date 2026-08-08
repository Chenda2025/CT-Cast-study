const slides = Array.from(document.querySelectorAll(".slide"));
const dotsBox = document.getElementById("dots");
const progressBar = document.getElementById("progressBar");
const slideNum = document.getElementById("slideNum");
const slideTotal = document.getElementById("slideTotal");

let current = 0;

slideTotal.textContent = slides.length;

slides.forEach((_, i) => {
  const dot = document.createElement("i");
  dot.addEventListener("click", () => go(i));
  dotsBox.appendChild(dot);
});
const dots = Array.from(dotsBox.children);

function go(index) {
  current = Math.max(0, Math.min(slides.length - 1, index));
  slides.forEach((s, i) => s.classList.toggle("active", i === current));
  dots.forEach((d, i) => d.classList.toggle("on", i === current));
  slideNum.textContent = current + 1;
  progressBar.style.width = `${((current + 1) / slides.length) * 100}%`;
  location.hash = `s${current + 1}`;
}

document.getElementById("prev").addEventListener("click", () => go(current - 1));
document.getElementById("next").addEventListener("click", () => go(current + 1));

document.addEventListener("keydown", (e) => {
  if (e.key === "ArrowRight" || e.key === "PageDown" || e.key === " ") {
    e.preventDefault();
    go(current + 1);
  } else if (e.key === "ArrowLeft" || e.key === "PageUp") {
    e.preventDefault();
    go(current - 1);
  } else if (e.key === "Home") {
    go(0);
  } else if (e.key === "End") {
    go(slides.length - 1);
  }
});

let touchX = null;
document.addEventListener("touchstart", (e) => {
  touchX = e.changedTouches[0].clientX;
});
document.addEventListener("touchend", (e) => {
  if (touchX === null) return;
  const dx = e.changedTouches[0].clientX - touchX;
  if (Math.abs(dx) > 60) go(current + (dx < 0 ? 1 : -1));
  touchX = null;
});

const fromHash = parseInt((location.hash || "").replace("#s", ""), 10);
go(Number.isFinite(fromHash) && fromHash > 0 ? fromHash - 1 : 0);
