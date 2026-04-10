const productContainer = document.getElementById('productContainer');
const params = new URLSearchParams(window.location.search);
const productId = params.get('id');

async function loadProduct() {
  if (!productId) {
    productContainer.innerHTML = '<p>Не передан id товара</p>';
    return;
  }

  const response = await fetch(`/api/products/${productId}`);
  if (!response.ok) {
    productContainer.innerHTML = '<p>Товар не найден</p>';
    return;
  }

  const product = await response.json();
  const gallery = (product.image_urls || [])
    .map((url) => `<img class="detail-image" src="${url}" alt="${product.title}" />`)
    .join('');

  productContainer.innerHTML = `
    <article class="detail-card">
      <h1>${product.title}</h1>
      <p><strong>Бренд:</strong> ${product.brand_name || '-'}</p>
      <p><strong>Категории:</strong> ${product.general_category_name || '-'} / ${product.category_name || '-'} / ${product.subcategory_name || '-'}</p>
      <p><strong>Пол:</strong> ${product.gender_label || '-'}</p>
      <p><strong>Размер:</strong> ${product.size_label || '-'}</p>
      <p><strong>Состояние:</strong> ${product.condition_rank || '-'}</p>
      <p><strong>Замеры:</strong> ${product.measurements_text || '-'}</p>
      <p><strong>Цена:</strong> ${product.price_original || '-'} ${product.currency_code || ''}</p>
      <p><strong>Описание:</strong><br />${(product.description || '-').replaceAll('\n', '<br />')}</p>
      <p><a href="${product.product_url}" target="_blank" rel="noreferrer">Открыть исходный товар</a></p>
      <section class="detail-gallery">${gallery}</section>
    </article>
  `;
}

loadProduct();
