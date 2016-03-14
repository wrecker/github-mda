# Github Mail Delivery Agent
This directory contains a python script that acts like a Mail Delivery Agent (MDA) that can be used in fetchmail. 

## Motivation
Github Enterprise (GHE) supports replying by email to post comments on pull requests, issues, commit comments etc. But it requires that port 25 (SMTP) is directly exposed to the internet so external mail servers can relay messages to it. Depending on the security policies of your environment this might not be possible to do.  

### Solution
Github Enterprise sends out notification emails with the reply-to address set to ```reply+NN..NN@reply.[hostname]```. Here [hostname] is the FQDN of the GHE instance. E.g: ```github.priv.mycompany.net```.

* Create DNS records for ```reply.github.priv.mycompany.net``` with your DNS provider.
  * You will at the minimum need MX records for this sub-domain.
* Set up email delivery to ```reply.github.priv.mycompany.net``` with an external email provider ([Google Apps](https://apps.google.com/), [Zoho](https://www.zoho.com/mail/), [Exchange Online](https://products.office.com/en-us/exchange/exchange-online) or [roll your own](https://samhobbs.co.uk/raspberry-pi-email-server))
* Use fetchmail to retrieve messages
* When fetchmail downloads new emails it forwards them to a custom MDA. The MDA then filters messages that have a TO address of the form ```reply+NN..NN@reply.[hostname]``` and delivers them to the SMTP server on the GHE instance.

## Setup
In a separate VM

* Install fetchmail
* Copy the ```etc/fetchmailrc``` to ```/etc``` on the target machine.
  * Replace _imap.gmail.com_ to point to the right mail server
  * Replace _reply@reply.github.priv.mycompany.net_ with the right username & domain for your mail server. 
  * Replace _INSERT PASSWORD_ with the password for the account
  * Replace the protocol _IMAP_ with whatever mail download protocol you enable for this account. 
* Copy the script ```github_mda.py``` to some location on the target machine. e.g. ```/home/joe/github-fetchmail``` and update the mda line in ```/etc/fetchmailrc```
  * Update the constants _REPLY_SUBDOMAIN_ to the right reply subdomain for your GHE instance
  * Update _SMTP_HOST_ to the hostname for your GHE instance 
* Create directory ```/var/github-fetchmail``` and change its owner to ```fetchmail```
* Edit ```/etc/default/fetchmail``` and set ```START_DAEMON``` to 'yes'
* Enable fetchmail to start on boot
  
  ```
  # Ubuntu
  sudo updated-rc.d fetchmail enable
  
  # debian 8 / Arch
  sudo systemctl enable fetchmail
  ```
* Start fetchmail

  ```
  # Ubuntu
  sudo /etc/init.d/fetchmail start
  
  # debian 8 / Arch
  sudo systemctl start fetchmail
  ```

## Licensing
* See [LICENSE](LICENSE)

