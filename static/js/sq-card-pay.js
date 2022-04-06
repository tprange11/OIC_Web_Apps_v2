async function CardPay(fieldEl, buttonEl) {
  // Create a card payment object and attach to page, payment/templates/sq-payment-form.html
  const card = await window.payments.card({
    style: {
      '.input-container.is-focus': {
        borderColor: '#006AFF'
      },
      '.message-text.is-error': {
        color: '#BF0020'
      }
    }
  });
  await card.attach(fieldEl);

  async function eventHandler(event) {
    // Clear any existing messages
    window.paymentFlowMessageEl.innerText = '';

    try {
      const result = await card.tokenize();
      if (result.status === 'OK') {
        // Use global method from sq-payment-flow.js
        // window.createPayment(result.token);
        // Changed by Brian Christensen, instead submit the form and process the payment in the view.
        document.getElementById('payment-token').value = result.token;
        document.getElementById('fast-checkout').submit();
        document.getElementById('card-button').disabled = true;
      }
    } catch (e) {
      if (e.message) {
        window.showError(`Error: ${e.message}`);
        document.getElementById('card-button').disabled = false;
      } else {
        window.showError('Something went wrong');
        document.getElementById('card-button').disabled = false;
      }
    }
  }

  buttonEl.addEventListener('click', eventHandler);
}
