const form = document.getElementById('onlineBookingForm');
const availabilityPanel = document.getElementById('availabilityPanel');
const priceSummary = document.getElementById('priceSummary');
const payButton = document.getElementById('payButton');
const errorBox = document.getElementById('bookingError');

const bookingCalendar = document.getElementById('bookingCalendar');
const calendarLoading = document.getElementById('calendarLoading');
const calendarMonthLabel = document.getElementById('calendarMonthLabel');
const calendarPreviousButton = document.getElementById('calendarPreviousButton');
const calendarNextButton = document.getElementById('calendarNextButton');
const calendarDescription = document.getElementById('bookingCalendarDescription');
const calendarSuggestion = document.getElementById('calendarSuggestion');
const calendarSuggestionText = document.getElementById('calendarSuggestionText');
const useSuggestedDateButton = document.getElementById('useSuggestedDateButton');

const checkInDateInput = document.getElementById('checkInDate');
const checkOutDateInput = document.getElementById('checkOutDate');

let latestAvailability = null;
let calendarData = null;
let suggestedDate = null;

const today = new Date();
today.setHours(0, 0, 0, 0);

let calendarCursor = new Date(
  today.getFullYear(),
  today.getMonth(),
  1,
);

function pad(value) {
  return String(value).padStart(2, '0');
}

function localDateString(date) {
  return [
    date.getFullYear(),
    pad(date.getMonth() + 1),
    pad(date.getDate()),
  ].join('-');
}

function parseLocalDate(value) {
  if (!value) return null;

  const parts = value.split('-').map(Number);

  if (parts.length !== 3 || parts.some(Number.isNaN)) {
    return null;
  }

  return new Date(parts[0], parts[1] - 1, parts[2]);
}

function addDays(value, days) {
  const date = value instanceof Date
    ? new Date(value)
    : parseLocalDate(value);

  if (!date) return null;

  date.setDate(date.getDate() + days);
  return date;
}

function numberOfStayDays() {
  const checkIn = parseLocalDate(checkInDateInput.value);
  const checkOut = parseLocalDate(checkOutDateInput.value);

  if (!checkIn || !checkOut || checkOut <= checkIn) {
    return 1;
  }

  return Math.max(
    1,
    Math.ceil((checkOut - checkIn) / 86400000),
  );
}

function time24(hour, minute, period) {
  let value = Number(hour);

  if (period === 'AM' && value === 12) {
    value = 0;
  }

  if (period === 'PM' && value !== 12) {
    value += 12;
  }

  return `${pad(value)}:${minute}:00`;
}

function payload() {
  const data = new FormData(form);

  const checkInDate = data.get('check_in_date');
  const checkOutDate = data.get('check_out_date');

  const checkInTime = time24(
    data.get('check_in_hour'),
    data.get('check_in_minute'),
    data.get('check_in_period'),
  );

  const checkOutTime = time24(
    data.get('check_out_hour'),
    data.get('check_out_minute'),
    data.get('check_out_period'),
  );

  return {
    guest_name: String(data.get('guest_name') || '').trim(),
    mobile: String(data.get('mobile') || '').trim(),
    email: String(data.get('email') || '').trim(),
    room_type_id: Number(data.get('room_type_id')),
    check_in_at: checkInDate
      ? `${checkInDate}T${checkInTime}`
      : '',
    check_out_at: checkOutDate
      ? `${checkOutDate}T${checkOutTime}`
      : '',
    number_of_rooms: Number(data.get('number_of_rooms')),
    occupants_per_room: Number(data.get('occupants_per_room')),
  };
}

function money(value) {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
  }).format(value);
}

function formatDate(value) {
  const date = parseLocalDate(value);

  if (!date) return value;

  return date.toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });
}

function formatDateTime(value) {
  return new Date(value).toLocaleString('en-IN', {
    dateStyle: 'medium',
    timeStyle: 'short',
    hour12: true,
  });
}

function showError(message) {
  errorBox.textContent = message;
  errorBox.hidden = !message;
}

function clearCalendarSuggestion() {
  suggestedDate = null;
  calendarSuggestion.hidden = true;
  calendarSuggestionText.textContent = '';
}

function showCalendarSuggestion(dateValue) {
  if (!dateValue) {
    clearCalendarSuggestion();
    return;
  }

  suggestedDate = dateValue;
  calendarSuggestionText.textContent =
    `Next available check-in date: ${formatDate(dateValue)}.`;

  calendarSuggestion.hidden = false;
}

function resetAvailability() {
  latestAvailability = null;
  payButton.disabled = true;

  priceSummary.innerHTML =
    '<p>Your GST-inclusive total will appear after availability is confirmed.</p>';
}

function inventoryMap() {
  const map = new Map();

  for (const item of calendarData?.inventory || []) {
    map.set(item.date, item);
  }

  return map;
}

function isDateDisabled(dateValue, item) {
  if (!item) return true;

  if (!item.available) return true;

  const roomCount = Number(
    form.elements.number_of_rooms?.value || 1,
  );

  return Number(item.available_count || 0) < roomCount;
}

function renderCalendar() {
  if (!bookingCalendar) return;

  bookingCalendar.innerHTML = '';

  const year = calendarCursor.getFullYear();
  const month = calendarCursor.getMonth();

  calendarMonthLabel.textContent =
    calendarCursor.toLocaleDateString('en-IN', {
      month: 'long',
      year: 'numeric',
    });

  const weekdayNames = [
    'Sun',
    'Mon',
    'Tue',
    'Wed',
    'Thu',
    'Fri',
    'Sat',
  ];

  const weekdayRow = document.createElement('div');
  weekdayRow.className = 'booking-calendar-weekdays';

  for (const weekday of weekdayNames) {
    const label = document.createElement('span');
    label.textContent = weekday;
    weekdayRow.appendChild(label);
  }

  bookingCalendar.appendChild(weekdayRow);

  const grid = document.createElement('div');
  grid.className = 'booking-calendar-grid';

  const firstDay = new Date(year, month, 1);
  const leadingDays = firstDay.getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const dataByDate = inventoryMap();

  for (let index = 0; index < leadingDays; index += 1) {
    const blank = document.createElement('span');
    blank.className = 'calendar-day calendar-day-empty';
    blank.setAttribute('aria-hidden', 'true');
    grid.appendChild(blank);
  }

  for (let day = 1; day <= daysInMonth; day += 1) {
    const date = new Date(year, month, day);
    const dateValue = localDateString(date);
    const item = dataByDate.get(dateValue);
    const isPast = date < today;
    const disabled = isPast || isDateDisabled(dateValue, item);
    const selected = checkInDateInput.value === dateValue;

    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'calendar-day';
    button.dataset.date = dateValue;

    if (selected) {
      button.classList.add('selected');
    }

    if (disabled) {
      button.classList.add('sold-out');
      button.disabled = true;
    } else {
      button.classList.add('available');
    }

    const dateNumber = document.createElement('strong');
    dateNumber.textContent = String(day);

    const inventoryText = document.createElement('small');

    if (isPast) {
      inventoryText.textContent = 'Past';
    } else if (!item) {
      inventoryText.textContent = 'Unavailable';
    } else if (disabled) {
      inventoryText.textContent = 'Sold out';
    } else {
      inventoryText.textContent =
        `${item.available_count} left`;
    }

    button.appendChild(dateNumber);
    button.appendChild(inventoryText);

    if (!disabled) {
      button.addEventListener('click', () => {
        selectCalendarDate(dateValue);
      });
    }

    grid.appendChild(button);
  }

  bookingCalendar.appendChild(grid);
}

function selectCalendarDate(dateValue) {
  const checkIn = parseLocalDate(dateValue);

  if (!checkIn) return;

  const stayDays = numberOfStayDays();
  const checkOut = addDays(checkIn, stayDays);

  checkInDateInput.value = dateValue;
  checkOutDateInput.value = localDateString(checkOut);

  clearCalendarSuggestion();
  renderCalendar();
  checkAvailability();
}

async function loadCalendar() {
  const roomTypeId = Number(
    form.elements.room_type_id?.value || 0,
  );

  if (!roomTypeId) {
    calendarData = null;
    bookingCalendar.innerHTML = '';
    calendarMonthLabel.textContent = 'Calendar';
    calendarDescription.textContent =
      'Choose a room type to view available and sold-out dates.';
    clearCalendarSuggestion();
    return;
  }

  calendarLoading.hidden = false;
  bookingCalendar.setAttribute('aria-busy', 'true');
  clearCalendarSuggestion();

  const startDate = localDateString(
    new Date(
      calendarCursor.getFullYear(),
      calendarCursor.getMonth(),
      1,
    ),
  );

  const lastDate = new Date(
    calendarCursor.getFullYear(),
    calendarCursor.getMonth() + 1,
    0,
  );

  const days = lastDate.getDate();

  const params = new URLSearchParams({
    room_type_id: String(roomTypeId),
    start_date: startDate,
    days: String(days),
    stay_days: String(numberOfStayDays()),
    check_in_time: time24(
      form.elements.check_in_hour.value,
      form.elements.check_in_minute.value,
      form.elements.check_in_period.value,
    ),
    number_of_rooms: String(
      form.elements.number_of_rooms.value || 1,
    ),
  });

  try {
    const response = await fetch(
      `/api/booking/calendar?${params}`,
    );

    const result = await response.json();

    if (!response.ok) {
      throw new Error(
        result.detail || 'Unable to load availability calendar',
      );
    }

    calendarData = result;

    calendarDescription.textContent =
      `${result.room_type} · Select an available check-in date.`;

    renderCalendar();

    if (
      checkInDateInput.value &&
      result.disabled_dates.includes(checkInDateInput.value)
    ) {
      showCalendarSuggestion(result.next_available_date);
    }
  } catch (error) {
    calendarData = null;
    bookingCalendar.innerHTML =
      `<p class="booking-calendar-error">${error.message}</p>`;
  } finally {
    calendarLoading.hidden = true;
    bookingCalendar.removeAttribute('aria-busy');
  }
}

async function checkAvailability() {
  const p = payload();

  resetAvailability();

  if (
    !p.room_type_id ||
    !p.check_in_at ||
    !p.check_out_at ||
    !p.number_of_rooms ||
    !p.occupants_per_room
  ) {
    return;
  }

  availabilityPanel.textContent =
    'Checking live room availability…';

  const params = new URLSearchParams({
    room_type_id: String(p.room_type_id),
    check_in_at: p.check_in_at,
    check_out_at: p.check_out_at,
    number_of_rooms: String(p.number_of_rooms),
    occupants_per_room: String(p.occupants_per_room),
  });

  try {
    const response = await fetch(
      `/api/booking/availability?${params}`,
    );

    const result = await response.json();

    if (!response.ok) {
      throw new Error(
        result.detail || 'Unable to check availability',
      );
    }

    latestAvailability = result;

    if (!result.available) {
      availabilityPanel.innerHTML = `
        <strong>Not available</strong>
        <span>
          Only ${result.available_count} room(s) remain for these dates.
        </span>
      `;

      priceSummary.innerHTML =
        '<p>Try another room type, date or number of rooms.</p>';

      const calendarItem = inventoryMap().get(
        checkInDateInput.value,
      );

      if (
        !calendarItem ||
        Number(calendarItem.available_count || 0) <
          p.number_of_rooms
      ) {
        showCalendarSuggestion(
          calendarData?.next_available_date,
        );
      }

      return;
    }

    clearCalendarSuggestion();

    availabilityPanel.innerHTML = `
      <strong>Available</strong>
      <span>
        ${result.available_count} room(s) available ·
        ${result.number_of_days} billed 24-hour day(s) ·
        Checkout ${formatDateTime(result.check_out_at)}
      </span>
    `;

    const extraLine =
      result.extra_occupant_charge > 0
        ? `
          <div>
            <span>Extra occupant charge</span>
            <strong>
              ${money(result.extra_occupant_charge)}
            </strong>
          </div>
        `
        : '';

    const roomBase =
      result.subtotal - result.extra_occupant_charge;

    priceSummary.innerHTML = `
      <div>
        <span>Room charge</span>
        <strong>${money(roomBase)}</strong>
      </div>

      ${extraLine}

      <div>
        <span>Subtotal</span>
        <strong>${money(result.subtotal)}</strong>
      </div>

      <div>
        <span>GST (${result.gst_percent}%)</span>
        <strong>${money(result.gst_amount)}</strong>
      </div>

      <div class="price-total">
        <span>Total payable</span>
        <strong>${money(result.total)}</strong>
      </div>
    `;

    payButton.disabled = false;
  } catch (error) {
    availabilityPanel.textContent = error.message;
  }
}

function moveCalendar(monthOffset) {
  calendarCursor = new Date(
    calendarCursor.getFullYear(),
    calendarCursor.getMonth() + monthOffset,
    1,
  );

  loadCalendar();
}

calendarPreviousButton?.addEventListener('click', () => {
  const previousMonth = new Date(
    calendarCursor.getFullYear(),
    calendarCursor.getMonth() - 1,
    1,
  );

  const currentMonth = new Date(
    today.getFullYear(),
    today.getMonth(),
    1,
  );

  if (previousMonth < currentMonth) {
    return;
  }

  moveCalendar(-1);
});

calendarNextButton?.addEventListener('click', () => {
  moveCalendar(1);
});

useSuggestedDateButton?.addEventListener('click', () => {
  if (!suggestedDate) return;

  const date = parseLocalDate(suggestedDate);

  if (!date) return;

  calendarCursor = new Date(
    date.getFullYear(),
    date.getMonth(),
    1,
  );

  selectCalendarDate(suggestedDate);
  loadCalendar();
});

form.elements.room_type_id?.addEventListener(
  'change',
  async () => {
    resetAvailability();
    await loadCalendar();
    await checkAvailability();
  },
);

[
  'check_in_date',
  'check_in_hour',
  'check_in_minute',
  'check_in_period',
  'check_out_date',
  'check_out_hour',
  'check_out_minute',
  'check_out_period',
  'number_of_rooms',
  'occupants_per_room',
].forEach((name) => {
  form.elements[name]?.addEventListener(
    'change',
    async () => {
      if (
        name === 'check_in_date' &&
        checkInDateInput.value
      ) {
        const date = parseLocalDate(
          checkInDateInput.value,
        );

        if (date) {
          calendarCursor = new Date(
            date.getFullYear(),
            date.getMonth(),
            1,
          );
        }
      }

      if (
        [
          'check_in_date',
          'check_out_date',
          'check_in_hour',
          'check_in_minute',
          'check_in_period',
          'number_of_rooms',
        ].includes(name)
      ) {
        await loadCalendar();
      }

      await checkAvailability();
    },
  );
});

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  showError('');

  if (!form.reportValidity() || !latestAvailability) {
    return;
  }

  payButton.disabled = true;
  payButton.textContent = 'Reserving your room…';

  try {
    const orderResponse = await fetch(
      '/api/booking/order',
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload()),
      },
    );

    const order = await orderResponse.json();

    if (!orderResponse.ok) {
      throw new Error(
        order.detail || 'Unable to reserve the room',
      );
    }

    const options = {
      key: order.key_id,
      amount: order.amount,
      currency: order.currency,
      name: 'Akshat Royal Stay',
      description: `Full payment · ${order.booking_no}`,
      order_id: order.order_id,

      prefill: {
        name: payload().guest_name,
        email: payload().email,
        contact: payload().mobile,
      },

      theme: {
        color: '#07565b',
      },

      handler: async (response) => {
        const confirmResponse = await fetch(
          '/api/booking/confirm',
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(response),
          },
        );

        const result = await confirmResponse.json();

        if (!confirmResponse.ok) {
          showError(
            result.detail ||
            'Payment received, but confirmation needs assistance. Please contact us with your payment ID.',
          );

          return;
        }

        window.location.assign(
          `/booking/confirmed?booking_no=${encodeURIComponent(
            result.booking_no,
          )}`,
        );
      },

      modal: {
        ondismiss: () => {
          payButton.disabled = false;
          payButton.textContent =
            'Pay full amount & confirm';
        },
      },
    };

    new Razorpay(options).open();
  } catch (error) {
    showError(error.message);
    payButton.disabled = false;
  } finally {
    payButton.textContent =
      'Pay full amount & confirm';
  }
});

checkInDateInput.min = localDateString(today);
checkOutDateInput.min = localDateString(
  addDays(today, 1),
);

renderCalendar();
