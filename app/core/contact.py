import aiosmtplib
from email.header import Header
from email.mime.text import MIMEText
from app.models.base import ContactMe
from app.core.config import settings
from app.schemas.contact import EmailResponse


async def send_email(mail:ContactMe) ->EmailResponse:
    try:
        sendAddress=settings.SEND_ADDRESS
        password=settings.EMAIL_AUTH_PASSWORD
        receivers=settings.RECEIVE_ADDRESS
        message=MIMEText(f'sender: {mail.sender_name},contact information:{mail.sender_email}, {mail.mail_text}','plain','utf-8')
        message["From"]=Header(sendAddress)
        message["To"]=Header(','.join(receivers))

        async with aiosmtplib.SMTP(hostname=settings.SMTP_HOST,port=settings.SMTP_PORT,use_tls=True) as smtp:

            await smtp.login(sendAddress, password)
            await smtp.sendmail(sendAddress, receivers, message.as_string())
        return EmailResponse(success=True)
    except aiosmtplib.SMTPConnectError as e:
        return EmailResponse(success=False, message=f"连接邮件服务器失败: {str(e)}")
    except aiosmtplib.SMTPAuthenticationError as e:
        return EmailResponse(success=False, message=f"邮件服务器认证失败: 请检查用户名和密码")
    except aiosmtplib.SMTPRecipientsRefused as e:
        return EmailResponse(success=False, message=f"收件人被拒绝")
    except aiosmtplib.SMTPServerDisconnected as e:
        return EmailResponse(success=False, message=f"邮件服务器连接断开: {str(e)}")
    except aiosmtplib.SMTPException as e:
        return EmailResponse( success=False, message=f"邮件发送失败: {str(e)}")
    except Exception as e:
        return EmailResponse(success=False, message=f"未知错误: {str(e)}")








