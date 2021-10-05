# wits-reminder
Tells me when I get new WITSmail, when grades are uploaded, and possibly even when teacher pages get changed.

To get this to work, you need to enable 2FA in your Google Account and go to Configure Account -> Security -> App Passwords. Use a name like "My SMS", and copy the app password into your .env file. Your config file should have these keys:

SCHOOL_EMAIL, SCHOOL_PASS, EMAIL_FROM, EMAIL_APP_PASS, and EMAIL_SMS_TOi

According to https://www.digitaltrends.com/mobile/how-to-send-a-text-from-your-email-account/, you can find your sms email gateway to send messages. 
