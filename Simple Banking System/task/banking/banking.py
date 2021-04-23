import random
import sys
from sqlite3 import *


class Database:
    def __init__(self, filename="card.s3db"):
        self.filename = filename
        self.conn = connect(filename)
        self.create_table()

    def create_table(self):
        command = """CREATE TABLE IF NOT EXISTS card(
            id INTEGER,
            number TEXT,
            pin TEXT,
            balance INTEGER DEFAULT 0
            );
            """
        self.conn.cursor().execute(command)
        self.conn.commit()

    def quit(self):
        self.conn.close()

    def save_data(self, data: tuple):
        command = f"INSERT INTO card VALUES (?, ?, ?, ?);"
        self.conn.cursor().execute(command, data)
        self.conn.commit()

    def load_all(self):
        command = """SELECT * FROM card;"""
        return self.conn.cursor().execute(command).fetchall()

    def load_by_id(self, account_id):
        command = """SELECT * FROM card WHERE id=?;"""
        return self.conn.cursor().execute(command, account_id).fetchone()

    def load_attribute(self, attribute="id"):
        command = f"""SELECT {attribute} FROM card;"""
        return self.conn.cursor().execute(command).fetchall()

    def load_with_where(self, attribute="", conditions="TRUE"):
        command = f"""SELECT {attribute} FROM card WHERE {conditions}"""
        return self.conn.cursor().execute(command).fetchone()

    def update(self, value, data):
        command = f"UPDATE card SET {value} WHERE id = ?;"
        self.conn.cursor().execute(command, data)
        self.conn.commit()

    def delete(self, account_id):
        command = "DELETE FROM card WHERE id = ?"
        self.conn.cursor().execute(command, (account_id,))
        self.conn.commit()


class CreditCard:
    def __init__(self):
        self.default_number = "400000"
        self.pin = None
        self.card_number = None
        self._account_id = None

    def new_credit_card(self, account_id: str):
        self._account_id = account_id
        self.pin = "".join([str(random.randint(0, 9)) for _n in range(4)])
        self._make_card_number()

        print("Your card has been created")
        print(f"Your card number:\n{self.card_number}")
        print(f"Your card PIN:\n{self.pin}\n")

    def load_credit_card(self, credit_card_data: tuple):
        self._account_id = credit_card_data[0]
        self.card_number = credit_card_data[1]
        self.pin = credit_card_data[2]

    def _make_card_number(self):
        card_number = self.default_number + self._account_id
        aux = 0
        for pos, number in enumerate(card_number):
            number = int(number)
            if (pos + 1) % 2 != 0:
                number *= 2
                if number > 9:
                    number -= 9
            aux += number
        card_number += str(10 - aux % 10) if aux % 10 != 0 else "0"
        self.card_number = card_number


class Account:
    def __init__(self):
        self.db = None
        self.id = None
        self.credit_card = None
        self.balance = 0

    def new_account(self):
        self.db = Database()
        while True:
            _id = "".join([str(random.randint(0, 9)) for _n in range(9)])
            if _id not in self.db.load_attribute():
                self.id = _id
                break
        self._make_credit_card()
        self.db.quit()

    def load_account(self, account_data: tuple):
        self.id = account_data[0]
        self.balance = account_data[3]

        self.credit_card = CreditCard()
        self.credit_card.load_credit_card((account_data[0], account_data[1], account_data[2]))

    def _make_credit_card(self):
        self.credit_card = CreditCard()
        self.credit_card.new_credit_card(self.id)

    def account_menu(self):
        self.db = Database()
        while True:
            print("1. Balance")
            print("2. Add income")
            print("3. Do transfer")
            print("4. Close account")
            print("5. Log out")
            print("0. Exit")
            op = input()
            print()

            if op == "0":
                self.db.quit()
                sys.exit()
            elif op == "1":
                print(f"balance: {self.balance}\n")
            elif op == "5":
                self.db.quit()
                break
            elif op == "2":
                self.add_income()
            elif op == "3":
                self.do_transfer()
            elif op == "4":
                self.db.delete(self.id)
                self.db.quit()
                break

    def add_income(self):
        print("Enter income:")
        income = input()
        self.balance += float(income)
        self.db.update("balance = ?", (self.balance, self.id))
        print("Income was added!\n")

    def do_transfer(self):
        print("Transfer")
        print("Enter card number:")
        number = input()
        if self.credit_card.card_number == number:
            print("You can't transfer money to the same account!")
        elif not self.check_luhn(number):
            print("Probably you made a mistake in the card number. Please try again!\n")
        elif not self.db.load_with_where("id", f"number = {number}"):
            print("Such a card does not exist.")
        else:
            print("Enter how much money you want to transfer:")
            transfer = float(input())
            if transfer > self.balance:
                print("Not enough money!\n")
            else:
                print("Success!\n")
                self.db.update("balance = ?", (self.balance-transfer, self.id))
                self.balance -= transfer
                trans_id, balance = self.db.load_with_where("id, balance", f"number = {number}")
                self.db.update("balance = ?", (balance+transfer, trans_id))

    @staticmethod
    def check_luhn(card_number):
        aux = 0
        for pos, n in enumerate(card_number[:-1]):
            n = int(n)
            if (pos + 1) % 2 != 0:
                n *= 2
                if n > 9:
                    n -= 9
            aux += n
        aux += int(card_number[-1])
        if aux % 10 == 0:
            return True
        else:
            return False


class Bank:
    def __init__(self):
        self.db = Database()
        while True:
            print("1. Create an account")
            print("2. Log into account")
            print("0. Exit")
            op = input()
            print()
            if op == "0":
                self.db.quit()
                sys.exit()
            elif op == "1":
                self.new_account()
            elif op == "2":
                self.login()

    def new_account(self):
        account = Account()
        account.new_account()
        card_data = (account.id, account.credit_card.card_number, account.credit_card.pin, account.balance)
        self.db.save_data(card_data)

    def login(self):
        print("Enter your card number: ")
        card_number = input()
        print("Enter your PIN:")
        pin = input()
        print()

        acc_id = self.db.load_with_where("id", f"number = '{card_number}' and pin = '{pin}' ")
        if acc_id:
            print("You have successfully logged in!\n")
            account = Account()
            account.load_account(self.db.load_by_id(acc_id))
            account.account_menu()
        else:
            print("Wrong card number or PIN!\n")


if __name__ == '__main__':
    Bank()
