// Copies Page JavaScript - Vanilla JS version

let allCopies = [];

// Load all copies on page load
document.addEventListener('DOMContentLoaded', function() {
    loadCopies();
    
    // Add copy button click
    document.getElementById('add-copy-btn').addEventListener('click', function() {
        document.getElementById('add-copy-modal').style.display = 'block';
    });
    
    // Close modal buttons
    document.querySelectorAll('.close-btn, .cancel-btn').forEach(function(btn) {
        btn.addEventListener('click', function() {
            document.getElementById('add-copy-modal').style.display = 'none';
            document.getElementById('add-copy-form').reset();
        });
    });
    
    // Close modal when clicking outside
    window.addEventListener('click', function(event) {
        if (event.target.id === 'add-copy-modal') {
            document.getElementById('add-copy-modal').style.display = 'none';
            document.getElementById('add-copy-form').reset();
        }
    });
    
    // Add copy form submission
    document.getElementById('add-copy-form').addEventListener('submit', function(e) {
        e.preventDefault();
        
        const formData = {
            title: document.getElementById('copy-title').value,
            copy_text: document.getElementById('copy-text').value,
            category: document.getElementById('copy-category').value
        };
        
        fetch('/api/copies', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('add-copy-modal').style.display = 'none';
                document.getElementById('add-copy-form').reset();
                loadCopies();
                showMessage('コピーを追加しました！', 'success');
            } else {
                showMessage(data.message || 'エラーが発生しました', 'error');
            }
        })
        .catch(error => {
            showMessage('コピーの追加に失敗しました', 'error');
        });
    });
    
    // Category filter
    document.getElementById('category-filter').addEventListener('change', function() {
        const selectedCategory = this.value;
        filterCopies(selectedCategory);
    });
});

function loadCopies() {
    fetch('/api/copies')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                allCopies = data.copies;
                displayCopies(allCopies);
            } else {
                showMessage('コピーの読み込みに失敗しました', 'error');
            }
        })
        .catch(error => {
            showMessage('コピーの読み込みに失敗しました', 'error');
        });
}

function displayCopies(copies) {
    const grid = document.getElementById('copies-grid');
    grid.innerHTML = '';
    
    if (copies.length === 0) {
        grid.innerHTML = `
            <div class="empty-state">
                <h3>まだコピーがありません</h3>
                <p>「新しいコピーを追加」ボタンから最初のコピーを作成してください。</p>
            </div>
        `;
        return;
    }
    
    copies.forEach(function(copy) {
        const date = new Date(copy.created_at * 1000);
        const formattedDate = formatDate(date);
        
        const card = document.createElement('div');
        card.className = 'copy-card';
        card.setAttribute('data-category', copy.category);
        card.innerHTML = `
            <div class="copy-card-header">
                <h3 class="copy-card-title">${escapeHtml(copy.title)}</h3>
                <div class="copy-card-meta">
                    <span class="copy-category">${escapeHtml(copy.category)}</span>
                    <span class="copy-date">${formattedDate}</span>
                </div>
            </div>
            <div class="copy-card-body">
                <p class="copy-text">${escapeHtml(copy.copy_text)}</p>
            </div>
            <div class="copy-card-footer">
                <span class="copy-author">著者: ${escapeHtml(copy.author)}</span>
            </div>
        `;
        
        grid.appendChild(card);
    });
}

function filterCopies(category) {
    if (category === 'all') {
        displayCopies(allCopies);
    } else {
        const filtered = allCopies.filter(copy => copy.category === category);
        displayCopies(filtered);
    }
}

function formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${year}/${month}/${day} ${hours}:${minutes}`;
}

function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, function(m) { return map[m]; });
}

function showMessage(message, type) {
    // Simple alert for now - could be improved with a toast notification
    alert(message);
}
