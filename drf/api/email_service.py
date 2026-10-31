"""Uygulamanın tüm e-posta bildirimleri için ortak gönderim katmanı."""
import logging
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def send_notification(subject, recipient, text, html_template=None, context=None):
    """E-posta gönderir. SMTP arızası başarılı API işlemini geri almaz."""
    if not recipient:
        logger.warning("E-posta alıcısı bulunamadığı için bildirim atlandı: %s", subject)
        return False
    try:
        message = EmailMultiAlternatives(
            subject=subject,
            body=text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient],
        )
        if html_template:
            message.attach_alternative(
                render_to_string(html_template, context or {}),
                "text/html",
            )
        sent = message.send(fail_silently=False)
        return sent == 1
    except Exception:
        logger.exception("E-posta gönderilemedi. Konu: %s, alıcı: %s", subject, recipient)
        return False


def send_product_notification(user, product, action):
    labels = {"created": "oluşturuldu", "updated": "güncellendi", "deleted": "silindi"}
    label = labels[action]
    subject = f"Ürün işlemi: {product.title} {label}"
    text = (
        f"Merhaba {user.username},\n\n"
        f'"{product.title}" adlı ürününüz {label}.\n'
        f"İşlem zamanı: {product.updated_at:%d.%m.%Y %H:%M}\n\n"
        "Bu işlemi siz yapmadıysanız hesabınızın güvenliğini kontrol edin."
    )
    return send_notification(subject, user.email, text, "api/email/product_notification.html", {
        "username": user.username, "product_title": product.title,
        "action_label": label,
    })


def send_account_notification(user, action, old_value=None, new_value=None, recipient=None):
    labels = {
        "email_changed": "E-posta adresiniz değiştirildi",
        "username_changed": "Kullanıcı adınız değiştirildi",
        "password_changed": "Şifreniz değiştirildi",
        "account_deleted": "Hesabınız silindi",
        "profile_updated": "Profil bilgileriniz güncellendi",
    }
    subject = labels[action]
    detail = ""
    if action == "email_changed":
        detail = f"Yeni e-posta adresi: {new_value}\n"
    elif action == "username_changed":
        detail = f"Yeni kullanıcı adı: {new_value}\n"
    elif action == "password_changed":
        detail = "Güvenliğiniz için yeni şifreniz e-posta ile paylaşılmamıştır.\n"
    elif action == "account_deleted":
        detail = "Hesabınız ve hesabınıza bağlı kullanıcı verileri silinmiştir.\n"
    text = (
        f"Merhaba {user.username},\n\n{subject}.\n{detail}\n"
        "Bu işlemi siz yapmadıysanız derhal destek ekibiyle iletişime geçin "
        "ve hesabınızın güvenliğini kontrol edin."
    )
    return send_notification(subject, recipient or user.email, text)


def send_verification_email(user, verification_url):
    text = (
        f"Merhaba {user.username},\n\nHesabınızı doğrulamak için bağlantıyı açın:\n"
        f"{verification_url}\n\nBağlantı 24 saat geçerlidir."
    )
    return send_notification(
        "E-posta adresinizi doğrulayın", user.email, text,
        "api/email/verification.html",
        {"username": user.username, "verification_url": verification_url},
    )
