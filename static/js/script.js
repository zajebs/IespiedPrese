let page = 1;
let query = '';
let order = 'dt';
let isLoading = false;
let allProducts = [];
let lastRequestUrl = '';
let secondLastRequestUrl = '';

function resetAndLoadProducts() {
	page = 1;
	allProducts = [];
	lastRequestUrl = '';
	secondLastRequestUrl = '';
	loadProducts(true);
}

function redirectToGoogle(productName) {
	const url = `https://google.com/search?q=${productName}&btnI`;
	const a = document.createElement('a');
	a.href = url;
	a.target = '_blank';
	a.rel = 'noopener noreferrer';
	document.body.appendChild(a);
	a.click();
	document.body.removeChild(a);
}

function loadProducts(reset = false) {
	if (isLoading) return;
	isLoading = true;

	query = document.getElementById('search').value;
	order = document.getElementById('order').checked ? 'dl' : 'dt';
	const requestUrl = `/products?q=${query}&p=${page}&o=${order}`;

	if (requestUrl === lastRequestUrl && requestUrl === secondLastRequestUrl) {
		isLoading = false;
		return;
	}

	fetch(requestUrl)
		.then(response => response.json())
		.then(data => {
			secondLastRequestUrl = lastRequestUrl;
			lastRequestUrl = requestUrl;

			document.getElementById('total').textContent = data.total;
			const container = document.getElementById('product-container');
			const noProductsMsg = document.getElementById('no-products');
			const user = data.user_info;

			if (reset) {
				container.innerHTML = '';
				page = 1;
				allProducts = [];
			}

			if (data.products.length === 0 && allProducts.length === 0 && query) {
				noProductsMsg.innerHTML = `Ooops, <b>${query}</b> mums diemžēl vēl nav... 🥺`;
				noProductsMsg.classList.remove('hidden');
			} else {
				noProductsMsg.classList.add('hidden');
				data.products.forEach(product => {
					allProducts.push(product);

					let category = product.category;
					if (category.includes('/')) {
						let parts = category.split('/');
						if (parts[0].includes('WooCommerce')) {
							parts[0] = parts[0].replace('WooCommerce', '').trim();
						} else if (parts[0].includes('Wordpress')) {
							parts[0] = parts[0].replace('Wordpress', '').trim();
						}

						switch (parts[0]) {
							case 'Brands':
								parts[0] = 'Zīmoli';
								break;
							case 'Themes':
								parts[0] = 'Tēmas';
								break;
							case 'Plugins':
								parts[0] = 'Spraudņi';
								break;
						}

						category = parts.join('→').trim();
					}

					let downloads = product.downloads;
					let downloads_text = '';
					if (downloads === 0) {
						downloads_text = 'Vēl nav lejuplādēts';
					} else if (downloads % 10 === 1 && downloads % 100 !== 11) {
						downloads_text = `Lejuplādēts ${downloads} reizi`;
					} else {
						downloads_text = `Lejuplādēts ${downloads} reizes`;
					}

					const productDiv = document.createElement('div');
					productDiv.className = 'h-full bg-white p-4 shadow rounded-lg flex flex-col justify-between';
					productDiv.innerHTML = `
                    <div class="bg-gray-100 rounded-lg shadow-md overflow-hidden transform transition-transform hover:scale-105 flex flex-col h-full">
                    <img src="${product.image_url}" alt="" class="w-full h-64 object-cover" onclick="redirectToGoogle('${encodeURIComponent(product.name)}');" style="cursor: pointer;">
                    <div class="p-4 flex flex-col justify-between flex-grow">
                        <div>
                        <h3 class="text-lg font-bold my-2 flex items-center mb-4" onclick="redirectToGoogle('${encodeURIComponent(product.name)}');" style="cursor: pointer;">${product.name}</h3>
                        </div>
                        <div class="mt-auto">
                            <p class="text-gray-600 flex items-center"><i class="fas fa-tags text-blue-500 mr-2"></i><span>${category}</span></p>
                            <p class="text-gray-600 flex items-center"><i class="fas fa-code-branch text-blue-500 mr-2"></i><span>v${product.version}</span></p>
                            <p class="text-gray-600 flex items-center"><i class="fas fa-calendar-alt text-blue-500 mr-2"></i><span>${product.last_updated}</span></p>
                            <p class="text-gray-600 flex items-center pb-2"><i class="fas fa-download text-blue-500 mr-2"></i><span>${downloads_text}</span></p>
                        </div>
                    </div>
                </div>
                    `;

					function generateButtons(user, productId) {
						if (!user.is_authenticated) {
							return `
                                <div class="text-center mt-6">
                                    <div class="flex justify-center space-x-4">
                                        <a href="login" class="flex-1 bg-blue-800 text-white py-2 px-4 rounded hover:bg-blue-900 text-center whitespace-nowrap">Pieslēgties</a>
                                        <a href="register" class="flex-1 bg-green-700 text-white py-2 px-4 rounded hover:bg-green-900 text-center whitespace-nowrap">Reģistrēties</a>
                                    </div>
                                </div>
                            `;
						} else if (user.sub_level == 0) {
							return `
                                <div class="text-center mt-6">
                                    <div class="flex justify-center space-x-4">
                                        <a href="/plans" class="flex-1 bg-blue-800 text-white font-bold py-2 px-4 rounded hover:bg-blue-900 text-center whitespace-nowrap">Pirkt</a>
                                        <span class="flex-1 bg-green-700 text-white py-2 px-4 rounded hover:bg-green-900 cursor-pointer promo-code-link text-center whitespace-nowrap" data-id="${productId}">Ir kods?</span>
                                    </div>
                                </div>
                            `;
						} else if (user.sub_level == 1) {
							if (user.downloads_remaining > 0) {
								return `
                                    <button class="download-btn w-full text-center py-2 px-4 bg-blue-800 text-white rounded cursor-pointer mt-6 hover:bg-blue-900" data-id="${productId}">Lejuplādēt</button>
                                `;
							} else {
								return `
                                    <button class="w-full text-center py-2 px-4 bg-blue-800 text-white rounded cursor-pointer mt-6 hover:bg-blue-900 promo-code-link" data-id="${productId}">
                                        Ievadīt promo kodu
                                    </button>
                                `;
							}
						} else if (user.sub_level == 2) {
							return `
                                <button class="download-btn w-full text-center py-2 px-4 bg-blue-800 text-white rounded cursor-pointer mt-6 hover:bg-blue-900" data-id="${productId}">Lejuplādēt</button>
                            `;
						}
					}

					productDiv.innerHTML += generateButtons(user, product.id);

					container.appendChild(productDiv);
				});

				document.querySelectorAll('.promo-code-link').forEach(link => {
					link.addEventListener('click', function() {
						const productId = this.getAttribute('data-id');
						openPromoModal(productId);
					});
				});
			}

			if (data.products.length > 0) {
				page++;
			}

			isLoading = false;
		}).catch(error => {
			console.error('Error loading products:', error);
			isLoading = false;
		});
}

function openPromoModal(productId) {
	const promoModal = document.getElementById('promo-modal');
	promoModal.style.display = 'flex';
	const promoSubmitButton = document.getElementById('promo-code-submit');

	promoSubmitButton.onclick = function() {
		const promoCode = document.getElementById('promo-code-input').value;
		applyPromoCode(productId, promoCode);
	};

	const promoCancelButton = document.getElementById('promo-code-cancel');
	promoCancelButton.onclick = function() {
		promoModal.style.display = 'none';
	};
}

function generateUUID() {
	var d = new Date().getTime();
	var d2 = ((typeof performance !== 'undefined') && performance.now && (performance.now() * 1000)) || 0;
	return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
		var r = Math.random() * 16;
		if (d > 0) {
			r = (d + r) % 16 | 0;
			d = Math.floor(d / 16);
		} else {
			r = (d2 + r) % 16 | 0;
			d2 = Math.floor(d2 / 16);
		}
		return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);
	});
}

function applyPromoCode(productId, promoCode) {
	const promoSubmitButton = document.getElementById('promo-code-submit');
	promoSubmitButton.disabled = true;

	let loadingTextIndex = 0;
	const loadingTexts = ['Pārbaudām', 'Pārbaudām.', 'Pārbaudām..', 'Pārbaudām...'];
	const loadingInterval = setInterval(() => {
		promoSubmitButton.textContent = loadingTexts[loadingTextIndex];
		loadingTextIndex = (loadingTextIndex + 1) % loadingTexts.length;
	}, 300);

	fetch(`/promo_download/${productId}/${promoCode}`, {
			method: 'GET',
			headers: {
				'Content-Type': 'application/json'
			}
		})
		.then(response => {
			clearInterval(loadingInterval);
			if (response.ok) {
				return response.blob().then(blob => {
					const url = window.URL.createObjectURL(blob);
					const a = document.createElement('a');
					a.style.display = 'none';
					a.href = url;
					a.download = `${generateUUID()}.zip`;
					document.body.appendChild(a);
					a.click();
					window.URL.revokeObjectURL(url);
					window.location.reload();
				});
			} else {
				return response.json().then(data => {
					window.location.reload();
				});
			}
		})
		.catch(error => {
			clearInterval(loadingInterval);
			console.error('Error applying promo code:', error);
			window.location.reload();
		})
		.finally(() => {
			clearInterval(loadingInterval);
			promoSubmitButton.disabled = false;
			promoSubmitButton.textContent = 'Piemērot kodu';
			document.getElementById('promo-modal').style.display = 'none';
		});
}


document.getElementById('product-container').addEventListener('click', function(e) {
	if (e.target.classList.contains('download-btn')) {
		const productId = e.target.getAttribute('data-id');
		window.location.href = `/download/${productId}`;
	}
});

window.onscroll = function() {
	if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 200 && !isLoading) {
		loadProducts();
	}
};

resetAndLoadProducts();
