const form = document.getElementById('onlineBookingForm');
const availabilityPanel = document.getElementById('availabilityPanel');
const priceSummary = document.getElementById('priceSummary');
const payButton = document.getElementById('payButton');
const errorBox = document.getElementById('bookingError');
let latestAvailability = null;

function payload() {
  const data = new FormData(form);
  const date = data.get('check_in_date');
  const time = data.get('check_in_time');
  return {
    guest_name: String(data.get('guest_name') || '').trim(),
    mobile: String(data.get('mobile') || '').trim(),
    email: String(data.get('email') || '').trim(),
    room_type_id: Number(data.get('room_type_id')),
    check_in_at: date && time ? `${date}T${time}:00` : '',
    number_of_days: Number(data.get('number_of_days')),
    number_of_rooms: Number(data.get('number_of_rooms')),
  };
}

function money(value) { return new Intl.NumberFormat('en-IN', {style:'currency', currency:'INR'}).format(value); }
function showError(message) { errorBox.textContent = message; errorBox.hidden = !message; }

async function checkAvailability() {
  const p = payload();
  latestAvailability = null;
  payButton.disabled = true;
  if (!p.room_type_id || !p.check_in_at || !p.number_of_days || !p.number_of_rooms) return;
  availabilityPanel.textContent = 'Checking live room availability…';
  const params = new URLSearchParams({room_type_id:p.room_type_id, check_in_at:p.check_in_at, number_of_days:p.number_of_days, number_of_rooms:p.number_of_rooms});
  try {
    const response = await fetch(`/api/booking/availability?${params}`);
    const result = await response.json();
    if (!response.ok) throw new Error(result.detail || 'Unable to check availability');
    latestAvailability = result;
    if (!result.available) {
      availabilityPanel.innerHTML = `<strong>Not available</strong><span>Only ${result.available_count} room(s) remain for these dates.</span>`;
      priceSummary.innerHTML = '<p>Try another room type, date or number of rooms.</p>';
      return;
    }
    availabilityPanel.innerHTML = `<strong>Available</strong><span>${result.available_count} room(s) currently available · Checkout ${new Date(result.check_out_at).toLocaleString('en-IN')}</span>`;
    priceSummary.innerHTML = `<div><span>Room subtotal</span><strong>${money(result.subtotal)}</strong></div><div><span>GST (${result.gst_percent}%)</span><strong>${money(result.gst_amount)}</strong></div><div class="price-total"><span>Total payable</span><strong>${money(result.total)}</strong></div>`;
    payButton.disabled = false;
  } catch (error) { availabilityPanel.textContent = error.message; }
}

['room_type_id','check_in_date','check_in_time','number_of_days','number_of_rooms'].forEach(name => form.elements[name]?.addEventListener('change', checkAvailability));

form.addEventListener('submit', async event => {
  event.preventDefault(); showError('');
  if (!form.reportValidity() || !latestAvailability) return;
  payButton.disabled = true; payButton.textContent = 'Reserving your room…';
  try {
    const orderResponse = await fetch('/api/booking/order', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload())});
    const order = await orderResponse.json();
    if (!orderResponse.ok) throw new Error(order.detail || 'Unable to reserve the room');
    const options = {
      key: order.key_id, amount: order.amount, currency: order.currency,
      name: 'Akshat Royal Stay', description: `Full payment · ${order.booking_no}`,
      order_id: order.order_id,
      prefill: {name:payload().guest_name, email:payload().email, contact:payload().mobile},
      theme: {color:'#173f31'},
      handler: async response => {
        const confirmResponse = await fetch('/api/booking/confirm', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(response)});
        const result = await confirmResponse.json();
        if (!confirmResponse.ok) { showError(result.detail || 'Payment received, but confirmation needs assistance. Please contact us with your payment ID.'); return; }
        window.location.assign(`/booking/confirmed?booking_no=${encodeURIComponent(result.booking_no)}`);
      },
      modal: {ondismiss: () => { payButton.disabled = false; payButton.textContent = 'Pay full amount & confirm'; }},
    };
    new Razorpay(options).open();
  } catch (error) { showError(error.message); payButton.disabled = false; }
  finally { payButton.textContent = 'Pay full amount & confirm'; }
});
