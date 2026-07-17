const form = document.getElementById('onlineBookingForm');
const availabilityPanel = document.getElementById('availabilityPanel');
const priceSummary = document.getElementById('priceSummary');
const payButton = document.getElementById('payButton');
const errorBox = document.getElementById('bookingError');
let latestAvailability = null;

function time24(hour, minute, period) {
  let value = Number(hour);
  if (period === 'AM' && value === 12) value = 0;
  if (period === 'PM' && value !== 12) value += 12;
  return `${String(value).padStart(2, '0')}:${minute}:00`;
}

function payload() {
  const data = new FormData(form);
  const checkInDate = data.get('check_in_date');
  const checkOutDate = data.get('check_out_date');
  const checkInTime = time24(data.get('check_in_hour'), data.get('check_in_minute'), data.get('check_in_period'));
  const checkOutTime = time24(data.get('check_out_hour'), data.get('check_out_minute'), data.get('check_out_period'));
  return {
    guest_name: String(data.get('guest_name') || '').trim(),
    mobile: String(data.get('mobile') || '').trim(),
    email: String(data.get('email') || '').trim(),
    room_type_id: Number(data.get('room_type_id')),
    check_in_at: checkInDate ? `${checkInDate}T${checkInTime}` : '',
    check_out_at: checkOutDate ? `${checkOutDate}T${checkOutTime}` : '',
    number_of_rooms: Number(data.get('number_of_rooms')),
    occupants_per_room: Number(data.get('occupants_per_room')),
  };
}

function money(value) { return new Intl.NumberFormat('en-IN', {style:'currency', currency:'INR'}).format(value); }
function showError(message) { errorBox.textContent = message; errorBox.hidden = !message; }
function formatDateTime(value) { return new Date(value).toLocaleString('en-IN', {dateStyle:'medium', timeStyle:'short', hour12:true}); }

async function checkAvailability() {
  const p = payload();
  latestAvailability = null;
  payButton.disabled = true;
  if (!p.room_type_id || !p.check_in_at || !p.check_out_at || !p.number_of_rooms || !p.occupants_per_room) return;
  availabilityPanel.textContent = 'Checking live room availability…';
  const params = new URLSearchParams({room_type_id:p.room_type_id, check_in_at:p.check_in_at, check_out_at:p.check_out_at, number_of_rooms:p.number_of_rooms, occupants_per_room:p.occupants_per_room});
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
    availabilityPanel.innerHTML = `<strong>Available</strong><span>${result.available_count} room(s) available · ${result.number_of_days} billed 24-hour day(s) · Checkout ${formatDateTime(result.check_out_at)}</span>`;
    const extraLine = result.extra_occupant_charge > 0 ? `<div><span>Extra occupant charge</span><strong>${money(result.extra_occupant_charge)}</strong></div>` : '';
    const roomBase = result.subtotal - result.extra_occupant_charge;
    priceSummary.innerHTML = `<div><span>Room charge</span><strong>${money(roomBase)}</strong></div>${extraLine}<div><span>Subtotal</span><strong>${money(result.subtotal)}</strong></div><div><span>GST (${result.gst_percent}%)</span><strong>${money(result.gst_amount)}</strong></div><div class="price-total"><span>Total payable</span><strong>${money(result.total)}</strong></div>`;
    payButton.disabled = false;
  } catch (error) { availabilityPanel.textContent = error.message; }
}

['room_type_id','check_in_date','check_in_hour','check_in_minute','check_in_period','check_out_date','check_out_hour','check_out_minute','check_out_period','number_of_rooms','occupants_per_room'].forEach(name => form.elements[name]?.addEventListener('change', checkAvailability));

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
      theme: {color:'#07565b'},
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
