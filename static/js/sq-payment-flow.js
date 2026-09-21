// sq-payment-flow.js
//
// Page bootstrap for sq-payment-form.html: waits for the DOM (and the inline
// window.applicationId / window.locationId assignments), checks that Square.js
// loaded, then hands the card container and pay button to CardPay() in
// sq-card-pay.js, which does the actual tokenize-and-submit.

document.addEventListener("DOMContentLoaded", async () => {

  window.paymentFlowMessageEl = document.getElementById('payment-flow-message');

  const appId = window.applicationId;
  const locationId = window.locationId;

  if (!appId || !locationId) {
    console.error("Square app or location ID missing.");
    return;
  }

  // This instance is only a sanity check that the SDK and IDs work; CardPay()
  // builds the instance it actually uses
  try {
    window.payments = Square.payments(appId, locationId);
  } catch (err) {
    console.error("Failed initializing Square Payments:", err);
    return;
  }

  await CardPay(
    document.getElementById('card-container'),
    document.getElementById('card-button')
  );
});

// Message helpers. Nothing calls these at the moment; CardPay() writes to the
// message element directly.
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
