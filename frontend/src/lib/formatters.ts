/**
 * Financial and display formatters for RecoverX
 */

export function formatCurrency(minorUnits: number = 0, currency: string = 'INR'): string {
  const rupees = (minorUnits || 0) / 100;
  
  if (currency === 'INR') {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(rupees);
  }
  
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
  }).format(rupees);
}

export function formatCompactCurrency(minorUnits: number = 0): string {
  const rupees = (minorUnits || 0) / 100;
  if (rupees >= 10000000) {
    return `₹${(rupees / 10000000).toFixed(2)}Cr`;
  }
  if (rupees >= 100000) {
    return `₹${(rupees / 100000).toFixed(2)}L`;
  }
  if (rupees >= 1000) {
    return `₹${(rupees / 1000).toFixed(1)}k`;
  }
  return `₹${Math.round(rupees)}`;
}

export function formatPercentage(rate: number = 0): string {
  const pct = rate <= 1.0 ? rate * 100 : rate;
  return `${Math.round(pct)}%`;
}

export function formatFactorName(name: string = ''): string {
  if (!name) return 'Factor';
  return name
    .replace(/_/g, ' ')
    .replace(/\b\w/g, l => l.toUpperCase());
}

export function formatEnum(val: string = ''): string {
  if (!val) return '—';
  return val
    .replace(/_/g, ' ')
    .toLowerCase()
    .replace(/\b\w/g, l => l.toUpperCase());
}

export function formatDate(isoString?: string | null): string {
  if (!isoString) return '—';
  try {
    const d = new Date(isoString);
    return d.toLocaleString('en-IN', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return isoString;
  }
}
