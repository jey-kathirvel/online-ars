const button = document.querySelector('.menu-button');
const nav = document.querySelector('.nav');
button?.addEventListener('click', () => {
  const open = button.getAttribute('aria-expanded') === 'true';
  button.setAttribute('aria-expanded', String(!open));
  nav?.classList.toggle('open', !open);
});

const bookingModal = document.getElementById('bookingModal');
const bookingFrame = bookingModal?.querySelector('.booking-modal__frame');
let bookingTrigger = null;

function openBookingModal(trigger) {
  if (!bookingModal || !bookingFrame) return;
  bookingTrigger = trigger;
  if (!bookingFrame.src) bookingFrame.src = bookingFrame.dataset.src;
  bookingModal.hidden = false;
  document.body.classList.add('booking-modal-open');
  bookingModal.querySelector('.booking-modal__close')?.focus();
}

function closeBookingModal() {
  if (!bookingModal) return;
  bookingModal.hidden = true;
  document.body.classList.remove('booking-modal-open');
  bookingTrigger?.focus();
}

document.addEventListener('click', (event) => {
  const bookingLink = event.target.closest('a[href="/book"]');
  if (bookingLink && bookingModal) {
    event.preventDefault();
    openBookingModal(bookingLink);
    return;
  }
  if (event.target.closest('[data-booking-close]')) closeBookingModal();
});

document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape' && bookingModal && !bookingModal.hidden) closeBookingModal();
});
