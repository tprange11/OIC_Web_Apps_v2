// sq-card-pay.js

async function CardPay(fieldEl, buttonEl) {
  const appId = window.applicationId;
  const locationId = window.locationId;

  if (!appId || !locationId) {
    console.error("Square configuration missing.");
    return;
  }

  // Initialize Square Payments
  let payments;
  try {
    payments = Square.payments(appId, locationId);
  } catch (err) {
    console.error("Failed to initialize Square Payments:", err);
    return;
  }

  // Create card instance
  const card = await payments.card({
    style: {
      '.input-container.is-focus': { borderColor: '#006AFF' },
      '.message-text.is-error': { color: '#BF0020' }
    }
  });

  await card.attach(fieldEl);

  // Message element for displaying errors
  const messageEl = document.getElementById("payment-flow-message");

  async function eventHandler(event) {
    // Clear old messages
    if (messageEl) messageEl.innerText = "";

    try {
      const result = await card.tokenize();

      if (result.status === "OK") {
        // Put the token into the hidden input
        document.getElementById("payment-token").value = result.token;

        // Disable button to prevent double-click
        buttonEl.disabled = true;

        // Submit the Django form
        document.getElementById("fast-checkout").submit();
        return;
      }

      // If result wasn't OK, show error
      if (messageEl) {
        messageEl.innerText = result.errors?.[0]?.message || "Payment failed.";
      }

    } catch (e) {
      console.error("Tokenization Error:", e);

      if (messageEl) {
        messageEl.innerText = e.message || "Something went wrong.";
      }

      buttonEl.disabled = false;
    }
  }

  // Bind click event
  buttonEl.addEventListener("click", eventHandler);
}
