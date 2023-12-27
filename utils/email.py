import re


def check_email_format(email_address):
    """
    Verify that the email address has the good format xxx@yyy.zzz
    :param email_address:
    :return:
    """
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    if re.fullmatch(regex, email_address):
        return True
    else:
        return False
