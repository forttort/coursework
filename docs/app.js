const PAGE_SIZE = 48;
const CATEGORY_LABELS = {
  all: 'Все',
  wear: 'Одежда',
  shoes: 'Обувь',
  bags: 'Сумки',
  accessories: 'Аксессуары',
  jewelry: 'Украшения',
};
const CATEGORY_ORDER = ['all', 'wear', 'shoes', 'bags', 'accessories', 'jewelry'];

const productsNode = document.getElementById('products');
const categoriesNode = document.getElementById('categories');
const messageNode = document.getElementById('message');
const paginationNode = document.getElementById('pagination');
const pageStatusNode = document.getElementById('pageStatus');
const previousButton = document.getElementById('previousPage');
const nextButton = document.getElementById('nextPage');

const initialParams = new URLSearchParams(window.location.search);
let products = [];
let category = initialParams.get('category') || 'all';
let page = Math.max(1, Number.parseInt(initialParams.get('page') || '1', 10) || 1);

function formatPrice(value) {
  if (value === null || value === undefined) return '-';
  return `${Math.round(Number(value)).toLocaleString('ru-RU')} ₽`;
}

function createText(tag, className, value) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  node.textContent = value;
  return node;
}

function createCard(product) {
  const card = document.createElement('article');
  card.className = 'product-card';

  const content = document.createElement('div');
  content.className = 'product-card-link';

  const strip = createText('div', 'showcase-card-strip', '');
  strip.appendChild(createText('span', '', 'HELLA.RESALE HELLA.RESALE HELLA.RESALE'));
  content.appendChild(strip);

  const frame = document.createElement('div');
  frame.className = 'product-image-frame is-loading';
  if (product.image) {
    const image = document.createElement('img');
    image.className = 'product-image';
    image.alt = `${product.brand || ''} ${product.title || ''}`.trim();
    image.loading = 'lazy';
    image.referrerPolicy = 'no-referrer';
    image.addEventListener('load', () => frame.classList.remove('is-loading'), { once: true });
    image.addEventListener('error', () => {
      frame.classList.remove('is-loading');
      frame.classList.add('is-missing');
      image.remove();
    }, { once: true });
    image.src = product.image;
    frame.appendChild(image);
  } else {
    frame.classList.remove('is-loading');
    frame.classList.add('is-missing');
  }
  content.appendChild(frame);

  const info = document.createElement('div');
  info.className = 'showcase-card-info';
  info.appendChild(createText('p', 'product-condition', product.condition || 'состояние не указано'));
  info.appendChild(createText('h2', 'product-brand', product.brand || 'Без бренда'));
  info.appendChild(createText('p', 'product-size', `Размер ${product.size || '-'}`));
  info.appendChild(createText('p', 'product-price', formatPrice(product.price)));
  content.appendChild(info);

  card.appendChild(content);
  return card;
}

function syncUrl() {
  const params = new URLSearchParams();
  if (category !== 'all') params.set('category', category);
  if (page > 1) params.set('page', String(page));
  window.history.replaceState({}, '', `${window.location.pathname}${params.size ? `?${params}` : ''}`);
}

function renderCategories() {
  const present = new Set(products.map((product) => product.category));
  categoriesNode.replaceChildren();
  for (const value of CATEGORY_ORDER) {
    if (value !== 'all' && !present.has(value)) continue;
    const button = document.createElement('button');
    button.type = 'button';
    button.className = `quick-category-button${category === value ? ' is-active' : ''}`;
    button.textContent = CATEGORY_LABELS[value];
    button.setAttribute('aria-pressed', String(category === value));
    button.addEventListener('click', () => {
      category = value;
      page = 1;
      render();
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
    categoriesNode.appendChild(button);
  }
}

function render() {
  const filtered = category === 'all'
    ? products
    : products.filter((product) => product.category === category);
  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  page = Math.min(page, pageCount);
  const start = (page - 1) * PAGE_SIZE;

  productsNode.replaceChildren(...filtered.slice(start, start + PAGE_SIZE).map(createCard));
  messageNode.hidden = filtered.length > 0;
  messageNode.textContent = filtered.length ? '' : 'В этой категории пока нет товаров';
  paginationNode.hidden = pageCount <= 1;
  pageStatusNode.textContent = `Страница ${page} из ${pageCount}`;
  previousButton.disabled = page <= 1;
  nextButton.disabled = page >= pageCount;
  renderCategories();
  syncUrl();
}

previousButton.addEventListener('click', () => {
  if (page <= 1) return;
  page -= 1;
  render();
  window.scrollTo({ top: 0, behavior: 'smooth' });
});

nextButton.addEventListener('click', () => {
  page += 1;
  render();
  window.scrollTo({ top: 0, behavior: 'smooth' });
});

fetch('catalog.json')
  .then((response) => {
    if (!response.ok) throw new Error('Не удалось загрузить каталог');
    return response.json();
  })
  .then((payload) => {
    products = Array.isArray(payload) ? payload : [];
    render();
  })
  .catch(() => {
    messageNode.hidden = false;
    messageNode.textContent = 'Каталог временно недоступен';
  });
