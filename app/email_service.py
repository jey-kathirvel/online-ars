import html, logging, smtplib
from dataclasses import dataclass
from datetime import datetime
from email.message import EmailMessage
from email.utils import formataddr
from pathlib import Path
from .config import get_settings

log=logging.getLogger(__name__)
LOGO=Path(__file__).resolve().parent.parent/'static'/'images'/'peacock-logo-mark.png'
@dataclass(frozen=True)
class BookingEmail:
    recipient:str; guest_name:str; booking_no:str; room_type:str; check_in_at:datetime; check_out_at:datetime
    number_of_rooms:int; number_of_days:int; subtotal_amount:object; gst_amount:object; total_amount:object; paid_amount:object
    payment_mode:str; payment_id:str|None=None; balance_amount:object=0

def money(v): return f'₹{float(v):,.2f}'
def dt(v): return v.strftime('%d %b %Y, %I:%M %p')
def send_booking_confirmation(d:BookingEmail)->bool:
    s=get_settings()
    if not d.recipient or not s.smtp_password:
        log.warning('Email skipped for %s: recipient or SMTP password missing',d.booking_no); return False
    esc=html.escape
    rows=[('Room',f'{esc(d.room_type)} × {d.number_of_rooms}'),('Check-in',dt(d.check_in_at)),('Check-out',dt(d.check_out_at)),('Stay',f'{d.number_of_days} day(s)'),('Subtotal',money(d.subtotal_amount)),('GST',money(d.gst_amount)),('Total',money(d.total_amount)),(f'Paid via {esc(d.payment_mode)}',money(d.paid_amount)),('Balance',money(d.balance_amount)),('Payment reference',esc(d.payment_id or 'Recorded by the property'))]
    table=''.join(f'<tr><td style="padding:8px"><b>{a}</b></td><td align="right" style="padding:8px">{b}</td></tr>' for a,b in rows)
    body=f'''<html><body style="margin:0;background:#f2f8f6;font-family:Arial;color:#143d3d"><div style="max-width:620px;margin:auto;background:white"><div style="padding:28px;text-align:center;background:#07545a;color:white"><img src="cid:ars-logo" width="90"><h1>Akshat Royal Stay</h1><p style="color:#e6c56e">Booking confirmed</p></div><div style="padding:28px"><p>Dear {esc(d.guest_name)},</p><p>Your booking and payment are confirmed.</p><h2>{esc(d.booking_no)}</h2><table width="100%">{table}</table><h3>Terms & refund policy</h3><ul style="line-height:1.6"><li>Valid government photo ID is required. Occupancy must match the booking; extra guests incur applicable charges.</li><li>Date changes depend on availability and rate difference.</li><li>48+ hours before check-in: full room-charge refund; gateway charges, if any, are non-refundable.</li><li>24–48 hours: 50% refund. Within 24 hours, no-show or early departure: no refund.</li><li>Approved refunds return to the original method in 7–10 business days. Property cancellation: full refund.</li></ul><p>Help: +91 90929 77055 · ars.familystay@gmail.com</p></div></div></body></html>'''
    msg=EmailMessage(); msg['Subject']=f'Booking confirmed — {d.booking_no} | Akshat Royal Stay'; msg['From']=formataddr((s.smtp_from_name,s.smtp_from_email)); msg['To']=d.recipient; msg['Reply-To']=s.smtp_reply_to
    msg.set_content(f'Booking {d.booking_no} confirmed. Total {money(d.total_amount)}; paid {money(d.paid_amount)}. Details: https://online.akshatroyalstay.in/refund-policy')
    msg.add_alternative(body,subtype='html'); part=msg.get_payload()[-1]
    if LOGO.exists(): part.add_related(LOGO.read_bytes(),maintype='image',subtype='png',cid='<ars-logo>')
    try:
        client=smtplib.SMTP_SSL(s.smtp_host,s.smtp_port,timeout=s.smtp_timeout_seconds) if s.smtp_use_ssl else smtplib.SMTP(s.smtp_host,s.smtp_port,timeout=s.smtp_timeout_seconds)
        with client:
            if s.smtp_use_starttls: client.starttls()
            client.login(s.smtp_username,s.smtp_password); client.send_message(msg)
        return True
    except Exception: log.exception('Email failed for %s',d.booking_no); return False
