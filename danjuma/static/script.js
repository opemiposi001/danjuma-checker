const baseUrl = window.location.origin;

// Render result with enhanced styling
function renderResult(data, type = 'info') {
    const resultsDiv = document.getElementById('results');
    const resultCard = document.createElement('div');
    
    let htmlContent = '';
    let cardClass = 'info';

    if (type === 'register') {
        cardClass = data.message ? 'success' : 'error';
        htmlContent = `
            <div class="result-title">
                <i class="fas fa-${data.message ? 'check-circle' : 'exclamation-circle'}"></i>
                <span>${data.message || data.error || 'Registration Failed'}</span>
            </div>
        `;
    }

    if (type === 'status') {
        const isActive = data.is_active;
        cardClass = isActive ? 'success' : 'error';
        htmlContent = `
            <div class="result-title">
                <i class="fas fa-${isActive ? 'shield-alt' : 'lock'}"></i>
                <span>Protection Status</span>
            </div>
            <div style="font-size: 16px; color: var(--text-secondary);">
                Status: <strong>${isActive ? '✅ Active' : '❌ Inactive'}</strong>
            </div>
        `;
    }

    if (type === 'scans') {
        cardClass = data.length > 0 ? 'success' : 'info';
        
        if (data.length === 0) {
            htmlContent = `
                <div class="result-title">
                    <i class="fas fa-inbox"></i>
                    <span>No Scans Found</span>
                </div>
                <p style="color: var(--text-secondary);">No recent scans for this email address.</p>
            `;
        } else {
            let scansHtml = `
                <div class="result-title">
                    <i class="fas fa-list"></i>
                    <span>Scan History (${data.length} records)</span>
                </div>
            `;

            data.forEach((scan, index) => {
                const verdictClass = scan.verdict.toLowerCase();
                const verdictIcon = verdictClass === 'clean' ? 'check-circle' : 
                                   verdictClass === 'suspicious' ? 'exclamation-triangle' : 
                                   'times-circle';
                
                const scannedAt = new Date(scan.scanned_at).toLocaleString();
                
                scansHtml += `
                    <div class="scan-item ${verdictClass}">
                        <div style="display: flex; justify-content: space-between; align-items: start;">
                            <div style="flex: 1;">
                                <strong style="font-size: 15px;">File:</strong> ${scan.file_name}<br>
                                <strong style="font-size: 15px;">From:</strong> ${scan.sender_email}<br>
                                <strong style="font-size: 15px;">Scanned:</strong> ${scannedAt}
                                <div class="scan-verdict ${verdictClass}">
                                    <i class="fas fa-${verdictIcon}"></i>
                                    ${scan.verdict}
                                </div>
                                <div class="scan-details">
                                    Malicious Detections: <strong>${scan.malicious_count}</strong><br>
                                    Suspicious Detections: <strong>${scan.suspicious_count}</strong>
                                    ${scan.virustotal_link ? `<br><a href="${scan.virustotal_link}" target="_blank" class="scan-link"><i class="fas fa-external-link-alt"></i> View Full Report</a>` : ''}
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            });
            
            htmlContent = scansHtml;
        }
    }

    if (type === 'unregister') {
        cardClass = data.message ? 'success' : 'error';
        htmlContent = `
            <div class="result-title">
                <i class="fas fa-${data.message ? 'check-circle' : 'exclamation-circle'}"></i>
                <span>${data.message || data.error || 'Unregistration Failed'}</span>
            </div>
        `;
    }

    resultCard.className = `result-card ${cardClass}`;
    resultCard.innerHTML = htmlContent;
    
    resultsDiv.innerHTML = '';
    resultsDiv.appendChild(resultCard);
    
    // Scroll to results
    resultCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// Show loading state
function showLoading(element) {
    const originalContent = element.innerHTML;
    element.innerHTML = '<span class="loading"></span> Processing...';
    element.disabled = true;
    return originalContent;
}

// Restore button state
function restoreButton(element, originalContent) {
    element.innerHTML = originalContent;
    element.disabled = false;
}

// Register Form
document.getElementById('registerForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const button = e.target.querySelector('button');
    const originalContent = showLoading(button);
    
    try {
        const email = document.getElementById('registerEmail').value;
        const response = await fetch(`${baseUrl}/api/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email })
        });
        const data = await response.json();
        renderResult(data, 'register');
        
        if (data.message) {
            document.getElementById('registerEmail').value = '';
        }
    } catch (error) {
        renderResult({ error: error.message }, 'register');
    } finally {
        restoreButton(button, originalContent);
    }
});

// Status Form
document.getElementById('statusForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const button = e.target.querySelector('button');
    const originalContent = showLoading(button);
    
    try {
        const email = document.getElementById('statusEmail').value;
        const response = await fetch(`${baseUrl}/api/status?email=${encodeURIComponent(email)}`);
        const data = await response.json();
        renderResult(data, 'status');
    } catch (error) {
        renderResult({ error: error.message }, 'status');
    } finally {
        restoreButton(button, originalContent);
    }
});

// Scans Form
document.getElementById('scansForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const button = e.target.querySelector('button');
    const originalContent = showLoading(button);
    
    try {
        const email = document.getElementById('scansEmail').value;
        const response = await fetch(`${baseUrl}/api/scans?email=${encodeURIComponent(email)}`);
        const data = await response.json();
        renderResult(data, 'scans');
    } catch (error) {
        renderResult({ error: 'Failed to fetch scan history' }, 'scans');
    } finally {
        restoreButton(button, originalContent);
    }
});

// Unregister Form
document.getElementById('unregisterForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const button = e.target.querySelector('button');
    
    // Confirm action
    if (!confirm('Are you sure you want to disable protection for this email?')) {
        return;
    }
    
    const originalContent = showLoading(button);
    
    try {
        const email = document.getElementById('unregisterEmail').value;
        const response = await fetch(`${baseUrl}/api/unregister`, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email })
        });
        const data = await response.json();
        renderResult(data, 'unregister');
        
        if (data.message) {
            document.getElementById('unregisterEmail').value = '';
        }
    } catch (error) {
        renderResult({ error: error.message }, 'unregister');
    } finally {
        restoreButton(button, originalContent);
    }
});

// Add smooth scroll behavior
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({ behavior: 'smooth' });
        }
    });
});

console.log('Danjuma Email Security Scanner - Ready');
