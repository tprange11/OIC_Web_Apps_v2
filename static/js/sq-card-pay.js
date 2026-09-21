// sq-card-pay.js
//
// Square card checkout for payment/templates/sq-payment-form.html. Flow:
//   1. Square.payments(appId, locationId) builds a Payments instance from the
//      window.applicationId / window.locationId set by the template.
//   2. A hosted card field is attached to fieldEl.
//   3. On click, card.tokenize() turns the card details into a one-time token; the
//      token is written to the hidden #payment-token input and the #fast-checkout
//      form is POSTed to payment:process_payment, where the server charges it.
// Card data never touches this site: only the token is submitted.
//
// sq-payment-flow.js also creates its own Payments instance (window.payments) before
// calling this, so the page ends up with two; only the one built here is used.

async function CardPay(fieldEl, buttonEl) {
  const appId = window.applicationId;
  const locationId = window.locationId;

  if (!appId || !locationId) {
    console.error("Square configuration missing.");
    return;
  }

  let payments;
  try {
    payments = Square.payments(appId, locationId);
  } catch (err) {
    console.error("Failed to initialize Square Payments:", err);
    return;
  }

  // Hosted card field; errors from attach() are not caught and will surface in the console
  const card = await payments.card({
    style: {
      '.input-container.is-focus': { borderColor: '#006AFF' },
      '.message-text.is-error': { color: '#BF0020' }
    }
  });

  await card.attach(fieldEl);

  const messageEl = document.getElementById("payment-flow-message");

  async function eventHandler(event) {
    // Clear old messages
    if (messageEl) messageEl.innerText = "";

    try {
      const result = await card.tokenize();

      if (result.status === "OK") {
        document.getElementById("payment-token").value = result.token;

        // Disable the button so a second click cannot submit the same token
        buttonEl.disabled = true;

        document.getElementById("fast-checkout").submit();
        return;
      }

      // Tokenization was rejected (bad card number, expired, etc.); the button
      // stays enabled so the user can correct the card and retry
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

  buttonEl.addEventListener("click", eventHandler);
}
