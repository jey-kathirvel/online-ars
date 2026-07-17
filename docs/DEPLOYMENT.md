# VPS deployment

Production path: `/var/www/online-ars`  
Service: `online-ars.service`  
Public URL: `https://online.akshatroyalstay.in`

## Deploy develop for acceptance testing

```bash
ssh root@72.61.245.128
sudo -u online-ars git -C /var/www/online-ars status -sb
sudo -u online-ars git -C /var/www/online-ars pull --ff-only origin develop
systemctl restart online-ars.service
systemctl is-active online-ars.service
```

## Verify

```bash
curl -I https://online.akshatroyalstay.in/
curl -I https://online.akshatroyalstay.in/rooms
curl -I 'https://online.akshatroyalstay.in/book?embed=1'
journalctl -u online-ars.service -n 100 --no-pager
```

Expected result is HTTP `200` and service status `active`.

## Environment changes

Edit `/var/www/online-ars/.env`, then restart the service. Validate only whether values exist and whether the Razorpay key uses `rzp_test_`; never print credentials.

## Rollback

Record the current commit before deployment. If a release fails, switch to the previously tested commit using a normal Git revert or a reviewed rollback commit, restart the service, and verify all URLs. Do not use `git reset --hard` on production.
