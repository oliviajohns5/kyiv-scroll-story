const response = await fetch('/content/story.json');
const story = await response.json();
const chapters = story.chapters;

const root = document.documentElement;
const storyScroll = document.getElementById('storyScroll');
const sceneStack = document.getElementById('sceneStack');
const storyCard = document.getElementById('storyCard');
const chapterDots = document.getElementById('chapterDots');
const chapterCounter = document.getElementById('chapterCounter');
const chapterNav = document.getElementById('chapterNav');
const chapterMenu = document.getElementById('chapterMenu');
const chaptersButton = document.getElementById('chaptersButton');
const staticStory = document.getElementById('staticStory');

storyScroll.style.height = `${chapters.length * 110}svh`;

const fallbackSvg = (chapter) => {
  const [a,b,c] = chapter.palette;
  return `<svg viewBox="0 0 1200 800" role="img" aria-label="${chapter.image_alt}">
    <defs>
      <linearGradient id="sky-${chapter.id}" x1="0" y1="0" x2="1" y2="1"><stop stop-color="${a}"/><stop offset=".7" stop-color="${b}"/><stop offset="1" stop-color="${c}"/></linearGradient>
      <filter id="paper-${chapter.id}"><feTurbulence baseFrequency=".02 .18" numOctaves="3"/><feColorMatrix values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 .16 0"/></filter>
    </defs>
    <rect width="1200" height="800" fill="url(#sky-${chapter.id})"/>
    <path d="M0 600 C180 520 330 650 500 560 C700 450 850 590 1200 430 V800 H0Z" fill="${a}" opacity=".85"/>
    <path d="M0 660 C260 600 420 700 680 625 C860 575 980 610 1200 550" fill="none" stroke="${c}" stroke-width="7" opacity=".5"/>
    <rect width="1200" height="800" filter="url(#paper-${chapter.id})" opacity=".8"/>
  </svg>`;
};

// Story data is repository-owned static JSON, not user input. The templates below intentionally
// use innerHTML only for this trusted, version-controlled content.
const layers = chapters.map((chapter, index) => {
  const layer = document.createElement('div');
  layer.className = `scene-layer ${chapter.side === 'right' ? 'side-right' : ''}`;
  layer.dataset.index = String(index);
  layer.innerHTML = `
    <div class="scene-fallback" style="--scene-a:${chapter.palette[0]};--scene-b:${chapter.palette[1]}">${fallbackSvg(chapter)}</div>
    <picture class="scene-media">
      <source media="(max-width: 760px)" srcset="${chapter.mobile_image}">
      <img src="${chapter.image}" alt="${chapter.image_alt}" ${index < 2 ? 'loading="eager"' : 'loading="lazy"'} decoding="async">
    </picture>`;
  layer.querySelector('img').addEventListener('error', () => layer.querySelector('.scene-media')?.remove());
  sceneStack.appendChild(layer);
  return layer;
});

chapters.forEach((chapter, index) => {
  const navLink = document.createElement('a');
  navLink.href = `#${chapter.id}`;
  navLink.dataset.index = String(index);
  navLink.innerHTML = `<span>${chapter.number}</span><b>${chapter.title}</b>`;
  chapterNav.appendChild(navLink);

  const dot = document.createElement('button');
  dot.type = 'button';
  dot.dataset.index = String(index);
  dot.setAttribute('aria-label', `Go to ${chapter.title}`);
  chapterDots.appendChild(dot);

  const staticCard = document.createElement('article');
  staticCard.id = chapter.id;
  staticCard.className = 'static-card';
  staticCard.innerHTML = `<picture><source media="(max-width:760px)" srcset="${chapter.mobile_image}"><img src="${chapter.image}" alt="${chapter.image_alt}" loading="lazy"></picture><div class="static-copy"><p class="overline">${chapter.eyebrow} · ${chapter.period}</p><h2>${chapter.title}</h2><p>${chapter.text}</p></div>`;
  staticStory.appendChild(staticCard);
});

function openMenu(open) {
  chapterMenu.classList.toggle('open', open);
  chapterMenu.setAttribute('aria-hidden', String(!open));
  chaptersButton.setAttribute('aria-expanded', String(open));
}
chaptersButton.addEventListener('click', () => openMenu(!chapterMenu.classList.contains('open')));
chapterMenu.querySelector('.menu-close').addEventListener('click', () => openMenu(false));
document.addEventListener('keydown', (event) => event.key === 'Escape' && openMenu(false));

function chapterScrollY(index) {
  const scrollable = Math.max(1, storyScroll.offsetHeight - innerHeight);
  return Math.round(storyScroll.offsetTop + scrollable * ((index + .08) / chapters.length));
}
function goToChapter(index, behavior = 'smooth') {
  const safe = Math.max(0, Math.min(chapters.length - 1, Number(index) || 0));
  history.replaceState(null, '', `#${chapters[safe].id}`);
  scrollTo({top: chapterScrollY(safe), behavior});
  openMenu(false);
}
function goToIntro(event) {
  event?.preventDefault();
  history.replaceState(null, '', '#intro');
  scrollTo({top: 0, behavior: 'smooth'});
}

chapterNav.addEventListener('click', (event) => {
  const link = event.target.closest('a[data-index]');
  if (!link) return;
  event.preventDefault();
  goToChapter(link.dataset.index);
});
chapterDots.addEventListener('click', (event) => {
  const dot = event.target.closest('button[data-index]');
  if (dot) goToChapter(dot.dataset.index);
});
document.querySelector('.brand').addEventListener('click', goToIntro);
document.querySelector('.outro a[href="#intro"]').addEventListener('click', goToIntro);
document.querySelector('.intro .enter').addEventListener('click', (event) => {event.preventDefault(); goToChapter(0);});

let activeIndex = -1;
function renderCard(index) {
  const chapter = chapters[index];
  storyCard.className = `story-card ${chapter.side === 'right' ? 'right' : 'left'}`;
  storyCard.innerHTML = `
    <div class="card-top"><span>${chapter.number} · ${chapter.eyebrow}</span><i class="card-rule"></i><span>${chapter.period}</span></div>
    <h2>${chapter.title}</h2>
    <p class="card-place">${chapter.place}</p>
    <p class="card-text">${chapter.text}</p>`;
  chapterCounter.textContent = `${chapter.number} / ${String(chapters.length).padStart(2,'0')}`;
  [...chapterDots.children].forEach((dot, i) => dot.classList.toggle('active', i === index));
  [...chapterNav.children].forEach((link, i) => link.classList.toggle('active', i === index));
  root.style.setProperty('--scene-a', chapter.palette[0]);
  root.style.setProperty('--scene-b', chapter.palette[1]);
}

function update() {
  const pageMax = Math.max(1, document.documentElement.scrollHeight - innerHeight);
  root.style.setProperty('--global-progress', Math.min(1, Math.max(0, scrollY / pageMax)).toFixed(4));

  const rect = storyScroll.getBoundingClientRect();
  const scrollable = Math.max(1, storyScroll.offsetHeight - innerHeight);
  const local = Math.min(1, Math.max(0, -rect.top / scrollable));
  const raw = Math.min(chapters.length - .0001, local * chapters.length);
  const index = Math.floor(raw);
  const progress = raw - index;
  root.style.setProperty('--chapter-progress', progress.toFixed(4));

  layers.forEach((layer, i) => {
    const distance = i - raw;
    const visible = Math.abs(distance) < 1.08;
    layer.classList.toggle('active', i === index || i === index + 1);
    let opacity = 0;
    if (i === index) opacity = 1 - Math.max(0, (progress - .68) / .32);
    if (i === index + 1) opacity = Math.max(0, (progress - .68) / .32);
    if (index === chapters.length - 1 && i === index) opacity = 1;
    layer.style.opacity = visible ? String(Math.max(0, Math.min(1, opacity))) : '0';
    const direction = chapters[i].side === 'right' ? -1 : 1;
    const scale = 1.035 + Math.max(-.2, Math.min(1.2, -distance)) * .055;
    const shift = direction * distance * 2.2;
    layer.style.transform = `scale(${scale}) translate3d(${shift}%, ${distance * .45}%, 0)`;
  });

  if (index !== activeIndex) {
    activeIndex = index;
    renderCard(index);
    const next = chapters[index + 1];
    if (next) {
      const preloadDesktop = new Image(); preloadDesktop.src = next.image;
      const preloadMobile = new Image(); preloadMobile.src = next.mobile_image;
    }
  }
}

let ticking = false;
addEventListener('scroll', () => {
  if (ticking) return;
  ticking = true;
  requestAnimationFrame(() => {update(); ticking = false;});
}, {passive:true});
addEventListener('resize', update);

renderCard(0);
update();
const initial = chapters.findIndex(chapter => `#${chapter.id}` === location.hash);
if (initial >= 0) requestAnimationFrame(() => goToChapter(initial, 'auto'));
