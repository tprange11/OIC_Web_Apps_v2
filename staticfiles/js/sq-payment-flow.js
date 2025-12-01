// sq-payment-flow.js

document.addEventListener("DOMContentLoaded", async () => {

  // Ensure required DOM elements exist before calling any Square methods
  window.paymentFlowMessageEl = document.getElementById('payment-flow-message');

  // Build Square payments instance AFTER template variables exist
  const appId = window.applicationId;
  const locationId = window.locationId;

  if (!appId || !locationId) {
    console.error("Square app or location ID missing.");
    return;
  }

  try {
    window.payments = Square.payments(appId, locationId);
  } catch (err) {
    console.error("Failed initializing Square Payments:", err);
    return;
  }

  // Initialize card payment UI
  await CardPay(
    document.getElementById('card-container'),
    document.getElementById('card-button')
  );
});

// Simple helpers for error/success messages
window.showSuccess = function(message) {
  if (!window.paymentFlowMessageEl) return;
  paymentFlowMessageEl.classList.add('success');
  paymentFlowMessageEl.classList.remove('error');
  paymentFlowMessageEl.innerText = message;
}

window.showError = function(message) {
  if (!window.paymentFlowMessageEl) return;
  paymentFlowMessageEl.classList.add('error');
  paymentFlowMessageEl.classList.remove('success');
  paymentFlowMessageEl.innerText = message;
}
