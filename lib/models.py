from flask_login import UserMixin
import datetime

class User(UserMixin):
    def __init__(self, id, username, email, downloads_remaining, sub_date, sub_level):
        self.id = id
        self.username = username
        self.email = email
        self.downloads_remaining = downloads_remaining
        self.sub_date = sub_date
        self.sub_level = sub_level

    @property
    def days_left(self):
        try:
            if self.sub_date:
                expiration_date = datetime.datetime.strptime(self.sub_date, '%d-%m-%Y')
                today = datetime.datetime.now()
                delta = expiration_date - today
                days_remaining = max(0, delta.days+1)
                return days_remaining
        except ValueError as e:
            print("Error parsing the date:", str(e))
        except Exception as e:
            print("An error occurred:", str(e))
        return 0
