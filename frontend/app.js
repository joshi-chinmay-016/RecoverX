// Revenue Intelligence Dashboard JavaScript

const API_BASE_URL = 'http://localhost:8000/api/v1';

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    loadOverview();
    loadOpportunities();
    setupEventListeners();
});

// Setup event listeners
function setupEventListeners() {
    document.getElementById('priorityFilter').addEventListener('change', loadOpportunities);
    document.getElementById('categoryFilter').addEventListener('change', loadOpportunities);
    document.getElementById('refreshBtn').addEventListener('click', () => {
        loadOverview();
        loadOpportunities();
    });
}

// Load overview data
async function loadOverview() {
    try {
        const response = await fetch(`${API_BASE_URL}/intelligence/overview`);
        if (!response.ok) throw new Error('Failed to load overview');
        
        const data = await response.json();
        updateOverviewCards(data);
        updateRiskOverview(data);
        updateFailureAnalysis(data);
    } catch (error) {
        console.error('Error loading overview:', error);
        showError('Failed to load overview data');
    }
}

// Update overview cards
function updateOverviewCards(data) {
    document.getElementById('revenueAtRisk').textContent = formatCurrency(data.revenue_at_risk);
    document.getElementById('estimatedRecoverable').textContent = formatCurrency(data.estimated_recoverable_revenue);
    document.getElementById('failedRevenue').textContent = formatCurrency(data.failed_revenue);
    document.getElementById('highPriorityCount').textContent = data.high_priority_opportunities;
}

// Update risk overview
function updateRiskOverview(data) {
    const totalRevenue = data.total_revenue || 1;
    const riskPercentage = (data.revenue_at_risk / totalRevenue) * 100;
    
    document.getElementById('riskBarFill').style.width = `${Math.min(riskPercentage, 100)}%`;
    document.getElementById('riskAtRisk').textContent = formatCurrency(data.revenue_at_risk);
    document.getElementById('riskRecoverable').textContent = formatCurrency(data.estimated_recoverable_revenue);
    document.getElementById('riskRecovered').textContent = formatCurrency(data.recovered_revenue);
}

// Update failure analysis
function updateFailureAnalysis(data) {
    updateFailureDistribution(data.failure_distribution);
    updateTopFailureReasons(data.top_failure_reasons);
    updatePriorityDistribution(data.priority_distribution);
}

// Update failure distribution chart
function updateFailureDistribution(distribution) {
    const container = document.getElementById('failureDistributionChart');
    
    if (!distribution || Object.keys(distribution).length === 0) {
        container.innerHTML = '<div class="chart-placeholder">No data available</div>';
        return;
    }
    
    const categories = Object.keys(distribution);
    const counts = Object.values(distribution);
    const maxCount = Math.max(...counts);
    
    let html = '<div style="width: 100%; display: flex; flex-direction: column; gap: 8px;">';
    
    categories.forEach(category => {
        const count = distribution[category];
        const percentage = (count / maxCount) * 100;
        const displayName = category.replace(/_/g, ' ').toLowerCase();
        
        html += `
            <div style="display: flex; align-items: center; gap: 10px;">
                <div style="width: 120px; font-size: 0.8rem; color: #555;">${displayName}</div>
                <div style="flex: 1; height: 20px; background: #e9ecef; border-radius: 10px; overflow: hidden;">
                    <div style="width: ${percentage}%; height: 100%; background: #667eea; border-radius: 10px;"></div>
                </div>
                <div style="width: 30px; text-align: right; font-size: 0.8rem; font-weight: 600;">${count}</div>
            </div>
        `;
    });
    
    html += '</div>';
    container.innerHTML = html;
}

// Update top failure reasons
function updateTopFailureReasons(topReasons) {
    const container = document.getElementById('topFailureReasons');
    
    if (!topReasons || topReasons.length === 0) {
        container.innerHTML = '<div class="chart-placeholder">No data available</div>';
        return;
    }
    
    let html = '';
    topReasons.forEach(item => {
        html += `
            <div class="reason-item">
                <span class="reason-text">${item.reason}</span>
                <span class="reason-count">${item.count}</span>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

// Update priority distribution
function updatePriorityDistribution(distribution) {
    const container = document.getElementById('priorityDistribution');
    
    if (!distribution || Object.keys(distribution).length === 0) {
        container.innerHTML = '<div class="chart-placeholder">No data available</div>';
        return;
    }
    
    const priorities = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'];
    const maxCount = Math.max(...Object.values(distribution), 1);
    
    let html = '';
    
    priorities.forEach(priority => {
        const count = distribution[priority] || 0;
        const percentage = (count / maxCount) * 100;
        
        html += `
            <div class="priority-item">
                <div class="priority-label">${priority}</div>
                <div class="priority-bar">
                    <div class="priority-bar-fill ${priority.toLowerCase()}" style="width: ${percentage}%"></div>
                </div>
                <div class="priority-count">${count}</div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

// Load opportunities
async function loadOpportunities() {
    const priorityFilter = document.getElementById('priorityFilter').value;
    const categoryFilter = document.getElementById('categoryFilter').value;
    
    let url = `${API_BASE_URL}/intelligence/opportunities?page=1&page_size=50`;
    
    if (priorityFilter) {
        url += `&priority=${priorityFilter}`;
    }
    
    if (categoryFilter) {
        url += `&failure_category=${categoryFilter}`;
    }
    
    try {
        const response = await fetch(url);
        if (!response.ok) throw new Error('Failed to load opportunities');
        
        const data = await response.json();
        updateOpportunitiesTable(data.opportunities);
    } catch (error) {
        console.error('Error loading opportunities:', error);
        showError('Failed to load opportunities');
    }
}

// Update opportunities table
function updateOpportunitiesTable(opportunities) {
    const tbody = document.getElementById('opportunitiesTableBody');
    
    if (!opportunities || opportunities.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="loading">No opportunities found</td></tr>';
        return;
    }
    
    let html = '';
    
    opportunities.forEach(opp => {
        html += `
            <tr>
                <td><code>${opp.payment_id.substring(0, 8)}...</code></td>
                <td>${formatCurrency(opp.revenue_at_risk)}</td>
                <td>${opp.failure_reason}</td>
                <td>${(opp.recovery_probability * 100).toFixed(0)}%</td>
                <td>${opp.opportunity_score.toFixed(1)}</td>
                <td><span class="priority-badge ${opp.priority}">${opp.priority}</span></td>
                <td>${opp.recommended_intervention}</td>
                <td>
                    <button class="action-btn view" onclick="viewOpportunity('${opp.id}')">View</button>
                </td>
            </tr>
        `;
    });
    
    tbody.innerHTML = html;
}

// View opportunity details
async function viewOpportunity(resultId) {
    const modal = document.getElementById('opportunityModal');
    const modalBody = document.getElementById('modalBody');
    
    modalBody.innerHTML = '<div class="loading">Loading...</div>';
    modal.classList.add('active');
    
    try {
        const response = await fetch(`${API_BASE_URL}/intelligence/opportunities/${resultId}`);
        if (!response.ok) throw new Error('Failed to load opportunity details');
        
        const data = await response.json();
        updateModalContent(data);
    } catch (error) {
        console.error('Error loading opportunity details:', error);
        modalBody.innerHTML = '<div class="loading">Failed to load details</div>';
    }
}

// Update modal content
function updateModalContent(data) {
    const modalBody = document.getElementById('modalBody');
    
    const factorsHtml = data.factors && data.factors.length > 0 
        ? data.factors.map(factor => `
            <div class="factor-item">
                <span class="factor-direction ${factor.direction || (factor.impact >= 0 ? 'positive' : 'negative')}">
                    ${factor.impact >= 0 ? '↑' : '↓'}
                </span>
                <span class="factor-text">${formatFactorName(factor.factor)}</span>
                <span class="factor-impact">${factor.impact >= 0 ? '+' : ''}${(factor.impact * 100).toFixed(0)}%</span>
            </div>
        `).join('')
        : '<div class="loading">No factors available</div>';
    
    modalBody.innerHTML = `
        <div class="detail-section">
            <h3>Payment Information</h3>
            <div class="detail-row">
                <span class="detail-label">Payment ID:</span>
                <span class="detail-value"><code>${data.payment_id}</code></span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Amount:</span>
                <span class="detail-value highlight">${formatCurrency(data.revenue_at_risk)}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Status:</span>
                <span class="detail-value">Failed</span>
            </div>
        </div>
        
        <div class="detail-section">
            <h3>Failure Analysis</h3>
            <div class="detail-row">
                <span class="detail-label">Why it failed:</span>
                <span class="detail-value">${data.failure_reason}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Category:</span>
                <span class="detail-value">${data.failure_category.replace(/_/g, ' ')}</span>
            </div>
        </div>
        
        <div class="detail-section">
            <h3>Revenue Intelligence</h3>
            <div class="detail-row">
                <span class="detail-label">Revenue at risk:</span>
                <span class="detail-value highlight">${formatCurrency(data.revenue_at_risk)}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Recovery probability:</span>
                <span class="detail-value highlight">${(data.recovery_probability * 100).toFixed(0)}%</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Estimated recoverable:</span>
                <span class="detail-value">${formatCurrency(data.estimated_recoverable_revenue)}</span>
            </div>
        </div>
        
        <div class="detail-section">
            <h3>Opportunity Scoring</h3>
            <div class="detail-row">
                <span class="detail-label">Opportunity score:</span>
                <span class="detail-value highlight">${data.opportunity_score.toFixed(1)}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Priority:</span>
                <span class="detail-value"><span class="priority-badge ${data.priority}">${data.priority}</span></span>
            </div>
        </div>
        
        <div class="detail-section">
            <h3>Recommended Intervention</h3>
            <div class="detail-row">
                <span class="detail-label">Action:</span>
                <span class="detail-value highlight">${data.recommended_intervention}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Reason:</span>
                <span class="detail-value">${data.intervention_reason}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Confidence:</span>
                <span class="detail-value">${(data.confidence * 100).toFixed(0)}%</span>
            </div>
        </div>
        
        <div class="detail-section">
            <h3>Why? (Deterministic Reasoning)</h3>
            <p style="color: #555; font-size: 0.9rem; margin-bottom: 15px;">${data.explanation}</p>
            <div class="factors-list">
                ${factorsHtml}
            </div>
        </div>
        
        <div class="detail-section">
            <h3>Analysis Metadata</h3>
            <div class="detail-row">
                <span class="detail-label">Model version:</span>
                <span class="detail-value">${data.model_version}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Analyzed at:</span>
                <span class="detail-value">${new Date(data.updated_at).toLocaleString()}</span>
            </div>
        </div>
    `;
}

// Close modal
function closeModal() {
    const modal = document.getElementById('opportunityModal');
    modal.classList.remove('active');
}

// Close modal on outside click
document.getElementById('opportunityModal').addEventListener('click', (e) => {
    if (e.target.id === 'opportunityModal') {
        closeModal();
    }
});

// Format currency (paise to rupees)
function formatCurrency(paise) {
    const rupees = paise / 100;
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(rupees);
}

// Format factor name for display
function formatFactorName(factorName) {
    return factorName
        .replace(/_/g, ' ')
        .replace(/\b\w/g, l => l.toUpperCase());
}

// Show error message
function showError(message) {
    console.error(message);
    // Could add a toast notification here
}
