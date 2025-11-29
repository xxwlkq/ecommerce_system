//商品管理页面 JS
document.addEventListener('DOMContentLoaded', function() {
    // 1. 商品图片上传（添加/编辑商品时）
    const uploadInput = document.querySelector('#product-image-upload');
    const previewImg = document.querySelector('#image-preview');
    if (uploadInput && previewImg) {
        uploadInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (!file) return;

            // 验证文件类型和大小
            const allowedTypes = ['image/jpeg', 'image/png', 'image/jpg'];
            if (!allowedTypes.includes(file.type)) {
                adminToast('仅支持 JPG/PNG 格式图片', false);
                return;
            }

            if (file.size > 5 * 1024 * 1024) { // 5MB 限制
                adminToast('图片大小不能超过 5MB', false);
                return;
            }

            // 预览图片
            const reader = new FileReader();
            reader.onload = function(e) {
                previewImg.src = e.target.result;
                previewImg.style.display = 'block';
            };
            reader.readAsDataURL(file);
        });
    }

    // 2. 提交商品表单（添加/编辑）
    const productForm = document.querySelector('#product-form');
    if (productForm) {
        productForm.addEventListener('submit', function(e) {
            e.preventDefault();

            // 表单验证
            const productName = document.querySelector('#product-name').value.trim();
            const price = document.querySelector('#product-price').value.trim();
            const stock = document.querySelector('#product-stock').value.trim();

            if (!productName) {
                adminToast('请填写商品名称', false);
                return;
            }

            if (!/^\d+(\.\d{1,2})?$/.test(price)) {
                adminToast('请填写正确的价格（最多2位小数）', false);
                return;
            }

            if (!/^\d+$/.test(stock) || parseInt(stock) < 0) {
                adminToast('请填写正确的库存（非负整数）', false);
                return;
            }

            // 构建表单数据（包含图片）
            const formData = new FormData(productForm);

            // 提交到后端（添加/编辑接口）
            const action = productForm.dataset.action || 'add'; // add/edit
            const url = action === 'add' ? '/admin/api/product/add' : '/admin/api/product/edit';

            fetch(url, {
                method: 'POST',
                body: formData
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    adminToast(action === 'add' ? '商品添加成功' : '商品编辑成功');
                    setTimeout(() => window.location.href = '/admin/product_manage', 1500);
                } else {
                    adminToast(data.msg, false);
                }
            })
            .catch(err => {
                console.error('提交失败：', err);
                adminToast('网络错误，操作失败', false);
            });
        });
    }

    // 3. 删除商品
    const deleteBtns = document.querySelectorAll('.product-delete');
    deleteBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const productId = this.dataset.productId;
            const productName = this.dataset.productName;

            if (confirm(`确定要删除商品《${productName}》吗？删除后不可恢复！`)) {
                fetch('/admin/api/product/delete', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ product_id: productId })
                })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        adminToast('商品删除成功');
                        // 移除当前行
                        this.closest('tr').remove();
                    } else {
                        adminToast('删除失败：' + data.msg, false);
                    }
                });
            }
        });
    });

    // 4. 商品筛选（按类型/价格）
    const filterForm = document.querySelector('#product-filter-form');
    if (filterForm) {
        filterForm.addEventListener('submit', function(e) {
            e.preventDefault();

            // 获取筛选参数
            const productType = document.querySelector('#product-type').value;
            const minPrice = document.querySelector('#min-price').value;
            const maxPrice = document.querySelector('#max-price').value;

            // 构建查询参数
            const params = new URLSearchParams();
            if (productType) params.append('type', productType);
            if (minPrice) params.append('min_price', minPrice);
            if (maxPrice) params.append('max_price', maxPrice);

            // 跳转到筛选后的页面（后端需要处理筛选参数）
            window.location.href = `/admin/product_manage?${params.toString()}`;
        });
    }
});