// ============================================
// URL SHORTENER - JAVASCRIPT
// API Integration | Analytics | QR Codes
// ============================================

// Global state
let currentShortCode = null;
let currentShortUrl = null;

// ============================================
// INITIALIZATION
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    console.log('LinkSnap initialized');
    console.log('API Endpoint:', CONFIG.API_ENDPOINT);
    console.log('Short URL Base:', CONFIG.SHORT_URL_BASE);
    
    // Add enter key listener to URL input
    document.getElementById('urlInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            shortenURL();
        }
    });
    
    // Add enter key listener to custom code input
    document.getElementById('customCodeInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            shortenURL();
        }
    });
});

// ============================================
// TOGGLE CUSTOM CODE INPUT
// ============================================

function toggleCustomCode() {
    const checkbox = document.getElementById('useCustomCode');
    const input = document.getElementById('customCodeInput');
    
    if (checkbox.checked) {
        input.style.display = 'block';
        input.focus();
    } else {
        input.style.display = 'none';
        input.value = '';
    }
}

// ============================================
// SHORTEN URL - MAIN FUNCTION
// ============================================

async function shortenURL() {
    const urlInput = document.getElementById('urlInput');
    const customCodeInput = document.getElementById('customCodeInput');
    const loading = document.getElementById('loading');
    const result = document.getElementById('result');
    const error = document.getElementById('error');
    const btn = document.getElementById('shortenBtn');
    
    // Get values
    const url = urlInput.value.trim();
    const customCode = customCodeInput.value.trim();
    
    // Hide previous results/errors
    result.style.display = 'none';
    error.style.display = 'none';
    
    // Validate URL
    if (!url) {
        showError('Please enter a URL');
        return;
    }
    
    if (!isValidUrl(url)) {
        showError('Please enter a valid URL starting with http:// or https://');
        return;
    }
    
    // Validate custom code if provided
    if (customCode) {
        if (customCode.length < 3) {
            showError('Custom code must be at least 3 characters');
            return;
        }
        if (!/^[a-zA-Z0-9]+$/.test(customCode)) {
            showError('Custom code can only contain letters and numbers');
            return;
        }
    }
    
    // Show loading
    loading.style.display = 'block';
    btn.disabled = true;
    
    try {
        // Call API
        const response = await fetch(`${CONFIG.API_ENDPOINT}/shorten`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                url: url,
                custom_code: customCode || undefined
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to shorten URL');
        }
        
        // Success!
        currentShortCode = data.short_code;
        currentShortUrl = `${CONFIG.SHORT_URL_BASE}/${data.short_code}`;
        
        showResult(currentShortUrl);
        
    } catch (err) {
        console.error('Error:', err);
        showError(err.message || 'Failed to shorten URL. Please try again.');
    } finally {
        loading.style.display = 'none';
        btn.disabled = false;
    }
}

// ============================================
// VALIDATE URL
// ============================================

function isValidUrl(string) {
    try {
        const url = new URL(string);
        return url.protocol === 'http:' || url.protocol === 'https:';
    } catch {
        return false;
    }
}

// ============================================
// SHOW RESULT
// ============================================

function showResult(shortUrl) {
    const result = document.getElementById('result');
    const shortUrlInput = document.getElementById('shortUrlInput');
    
    shortUrlInput.value = shortUrl;
    result.style.display = 'block';
    
    // Smooth scroll to result
    result.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// ============================================
// SHOW ERROR
// ============================================

function showError(message) {
    const error = document.getElementById('error');
    error.textContent = message;
    error.style.display = 'block';
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        error.style.display = 'none';
    }, 5000);
}

// ============================================
// COPY TO CLIPBOARD
// ============================================

async function copyURL() {
    const shortUrlInput = document.getElementById('shortUrlInput');
    const copyBtn = document.querySelector('.btn-copy');
    const copyText = document.getElementById('copyText');
    
    try {
        await navigator.clipboard.writeText(shortUrlInput.value);
        
        // Visual feedback
        copyText.textContent = 'Copied!';
        copyBtn.classList.add('copied');
        
        setTimeout(() => {
            copyText.textContent = 'Copy';
            copyBtn.classList.remove('copied');
        }, 2000);
        
    } catch (err) {
        console.error('Failed to copy:', err);
        
        // Fallback: select text
        shortUrlInput.select();
        document.execCommand('copy');
        
        copyText.textContent = 'Copied!';
        setTimeout(() => {
            copyText.textContent = 'Copy';
        }, 2000);
    }
}

// ============================================
// SHOW ANALYTICS MODAL
// ============================================

async function showAnalytics() {
    if (!currentShortCode) {
        showError('No short URL to show analytics for');
        return;
    }
    
    const modal = document.getElementById('analyticsModal');
    const content = document.getElementById('analyticsContent');
    
    // Show modal with loading
    modal.style.display = 'flex';
    content.innerHTML = `
        <div class="modal-loading">
            <div class="spinner"></div>
            <p>Loading analytics...</p>
        </div>
    `;
    
    try {
        const response = await fetch(`${CONFIG.API_ENDPOINT}/analytics/${currentShortCode}`);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to load analytics');
        }
        
        // Display analytics
        content.innerHTML = `
            <div class="analytics-stats">
                <div class="analytics-stat">
                    <span class="analytics-stat-label">Short Code</span>
                    <span class="analytics-stat-value">${data.short_code}</span>
                </div>
                <div class="analytics-stat">
                    <span class="analytics-stat-label">Total Clicks</span>
                    <span class="analytics-stat-value">${data.total_clicks}</span>
                </div>
                <div class="analytics-stat">
                    <span class="analytics-stat-label">Unique Visitors</span>
                    <span class="analytics-stat-value">${data.unique_visitors}</span>
                </div>
                <div class="analytics-stat">
                    <span class="analytics-stat-label">Created</span>
                    <span class="analytics-stat-value">${formatDate(data.created_at)}</span>
                </div>
            </div>
            
            ${data.total_clicks > 0 ? `
                <div style="margin-top: 24px;">
                    <h4 style="margin-bottom: 12px; color: var(--dark);">Top Referrers</h4>
                    ${formatReferrers(data.referrers)}
                </div>
                
                <div style="margin-top: 24px;">
                    <h4 style="margin-bottom: 12px; color: var(--dark);">Recent Clicks</h4>
                    ${formatRecentClicks(data.recent_clicks)}
                </div>
            ` : `
                <div style="margin-top: 24px; text-align: center; padding: 20px; background: rgba(102, 126, 234, 0.05); border-radius: 10px;">
                    <p style="color: #64748b;">No clicks yet. Share your link to start tracking!</p>
                </div>
            `}
        `;
        
    } catch (err) {
        console.error('Error loading analytics:', err);
        content.innerHTML = `
            <div style="text-align: center; padding: 40px;">
                <p style="color: var(--error);">Failed to load analytics</p>
                <p style="color: #64748b; margin-top: 8px; font-size: 14px;">${err.message}</p>
            </div>
        `;
    }
}

// ============================================
// FORMAT HELPERS
// ============================================

function formatDate(isoString) {
    const date = new Date(isoString);
    return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatReferrers(referrers) {
    if (!referrers || Object.keys(referrers).length === 0) {
        return '<p style="color: #64748b; font-size: 14px;">No referrer data yet</p>';
    }
    
    return Object.entries(referrers)
        .map(([ref, count]) => `
            <div class="analytics-stat">
                <span class="analytics-stat-label" style="font-size: 14px;">${ref}</span>
                <span class="analytics-stat-value">${count}</span>
            </div>
        `).join('');
}

function formatRecentClicks(clicks) {
    if (!clicks || clicks.length === 0) {
        return '<p style="color: #64748b; font-size: 14px;">No clicks yet</p>';
    }
    
    return clicks.map(click => `
        <div style="padding: 12px; background: rgba(102, 126, 234, 0.05); border-radius: 8px; margin-bottom: 8px;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                <span style="font-size: 13px; color: var(--dark); font-weight: 600;">${click.referer}</span>
                <span style="font-size: 12px; color: #64748b;">${formatDate(click.timestamp)}</span>
            </div>
            <div style="font-size: 12px; color: #64748b;">${click.user_agent}</div>
        </div>
    `).join('');
}

// ============================================
// SHOW QR CODE MODAL
// ============================================

function showQR() {
    if (!currentShortUrl) {
        showError('No short URL to generate QR code for');
        return;
    }
    
    const modal = document.getElementById('qrModal');
    const qrContainer = document.getElementById('qrcode');
    
    // Clear previous QR code
    qrContainer.innerHTML = '';
    
    // Generate QR code
    new QRCode(qrContainer, {
        text: currentShortUrl,
        width: 256,
        height: 256,
        colorDark: '#667eea',
        colorLight: '#ffffff',
        correctLevel: QRCode.CorrectLevel.H
    });
    
    // Show modal
    modal.style.display = 'flex';
}

// ============================================
// CLOSE MODAL
// ============================================

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

// ============================================
// RESET FORM
// ============================================

function reset() {
    document.getElementById('urlInput').value = '';
    document.getElementById('customCodeInput').value = '';
    document.getElementById('useCustomCode').checked = false;
    document.getElementById('customCodeInput').style.display = 'none';
    document.getElementById('result').style.display = 'none';
    document.getElementById('error').style.display = 'none';
    
    currentShortCode = null;
    currentShortUrl = null;
    
    document.getElementById('urlInput').focus();
}

// ============================================
// SMOOTH SCROLL FOR NAVIGATION
// ============================================

document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// ============================================
// CLOSE MODALS ON ESCAPE KEY
// ============================================

document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        document.querySelectorAll('.modal').forEach(modal => {
            modal.style.display = 'none';
        });
    }
});

// ============================================
// INITIALIZATION COMPLETE
// ============================================

console.log('✅ LinkSnap ready!');

