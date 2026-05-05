// static/js/bulk_upload.js
document.addEventListener('DOMContentLoaded', function() {
    console.log('Bulk upload page loaded');
    
    // Drag & Drop
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const fileNamesDiv = document.getElementById('fileNames');
    
    if (uploadArea && fileInput) {
        uploadArea.addEventListener('click', () => fileInput.click());
        
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.style.background = '#fff9e6';
            uploadArea.style.borderColor = '#1e3c72';
        });
        
        uploadArea.addEventListener('dragleave', (e) => {
            e.preventDefault();
            uploadArea.style.background = '#fefcf9';
            uploadArea.style.borderColor = '#c9a959';
        });
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.style.background = '#fefcf9';
            fileInput.files = e.dataTransfer.files;
            updateFileNames(fileInput.files);
        });
        
        fileInput.addEventListener('change', () => updateFileNames(fileInput.files));
    }
    
    function updateFileNames(files) {
        if (!fileNamesDiv) return;
        if (files.length === 0) {
            fileNamesDiv.innerHTML = '';
            return;
        }
        
        let names = [];
        let totalSize = 0;
        for (let i = 0; i < files.length; i++) {
            names.push(files[i].name);
            totalSize += files[i].size;
        }
        
        const sizeMB = (totalSize / (1024 * 1024)).toFixed(1);
        fileNamesDiv.innerHTML = `
            <div style="background: #d4edda; padding: 10px 15px; border-radius: 12px; margin-top: 10px;">
                <i class="fas fa-check-circle" style="color: #28a745;"></i>
                <strong>${files.length} file(s):</strong> ${names.join(', ')} (${sizeMB} MB)
            </div>
        `;
    }
    
    // Method tabs
    window.showMethod = function(method) {
        const filePanel = document.getElementById('filePanel');
        const pastePanel = document.getElementById('pastePanel');
        const tabs = document.querySelectorAll('.method-tab');
        
        tabs.forEach(tab => tab.classList.remove('active'));
        event?.target?.closest('.method-tab')?.classList.add('active');
        
        if (method === 'file') {
            filePanel.style.display = 'block';
            pastePanel.style.display = 'none';
            if (fileInput) fileInput.required = true;
            const pastedText = document.querySelector('textarea[name="pasted_text"]');
            if (pastedText) pastedText.required = false;
        } else {
            filePanel.style.display = 'none';
            pastePanel.style.display = 'block';
            if (fileInput) fileInput.required = false;
            const pastedText = document.querySelector('textarea[name="pasted_text"]');
            if (pastedText) pastedText.required = true;
        }
    };
    
    // Load books on poet select
    const poetSelect = document.getElementById('poetSelect');
    const bookSelect = document.getElementById('bookSelect');
    
    if (poetSelect && bookSelect) {
        poetSelect.addEventListener('change', function() {
            const poetId = this.value;
            if (!poetId) {
                bookSelect.innerHTML = '<option value="">-- Select Poet First --</option>';
                return;
            }
            
            bookSelect.innerHTML = '<option value="">📚 Loading...</option>';
            bookSelect.disabled = true;
            
            fetch('/api/books/' + poetId)
                .then(res => res.json())
                .then(books => {
                    let options = '<option value="">-- Auto Select First Book --</option>';
                    books.forEach(book => {
                        options += `<option value="${book.id}">📖 ${book.title}</option>`;
                    });
                    bookSelect.innerHTML = options;
                    bookSelect.disabled = false;
                    if (window.selectedBookId) bookSelect.value = window.selectedBookId;
                })
                .catch(err => {
                    bookSelect.innerHTML = '<option value="">-- Error loading books --</option>';
                    bookSelect.disabled = false;
                });
        });
        
        if (poetSelect.value) poetSelect.dispatchEvent(new Event('change'));
    }
    
    // Clear button
    const clearBtn = document.getElementById('clearAllBtn');
    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            if (confirm('Clear all?')) {
                if (fileInput) fileInput.value = '';
                if (fileNamesDiv) fileNamesDiv.innerHTML = '';
                const pastedText = document.querySelector('textarea[name="pasted_text"]');
                if (pastedText) pastedText.value = '';
            }
        });
    }
    
    // Sample button
    const sampleBtn = document.getElementById('loadSampleBtn');
    if (sampleBtn) {
        sampleBtn.addEventListener('click', () => {
            const sample = `دل ہی تو ہے نہ سنگ و خشت
درد سے بھر نہ آئے کیوں

روئیں گے ہم ہزار بار
کوئی ہمیں ستائے کیوں

###GHZ###
اب کے ہم بچھڑے تو شاید کبھی خوابوں میں ملیں
جس طرح سوکھے ہوئے پھول کتابوں میں ملیں`;
            const pastedText = document.querySelector('textarea[name="pasted_text"]');
            if (pastedText) {
                pastedText.value = sample;
                if (typeof showToast === 'function') showToast('Sample loaded', 'success');
            }
        });
    }
});