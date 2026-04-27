"""Money Forward ME client for fetching personal finance data."""

import os
import re
from typing import Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://moneyforward.com"
_LOGIN_URL = f"{BASE_URL}/sign_in"
_ASSETS_URL = f"{BASE_URL}/accounts"
_CF_URL = f"{BASE_URL}/cf"


class MoneyForwardClient:
    def __init__(self, email: Optional[str] = None, password: Optional[str] = None):
        self.email = email or os.environ.get("MF_EMAIL")
        self.password = password or os.environ.get("MF_PASSWORD")
        if not self.email or not self.password:
            raise ValueError("MF_EMAIL and MF_PASSWORD must be set")
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        })
        self._logged_in = False

    def login(self) -> None:
        """Login to Money Forward ME."""
        resp = self.session.get(_LOGIN_URL)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        token_input = soup.find("input", {"name": "authenticity_token"})
        if not token_input:
            raise RuntimeError("Could not find authenticity_token on login page")
        token = token_input["value"]

        payload = {
            "authenticity_token": token,
            "mf_user[email]": self.email,
            "mf_user[password]": self.password,
            "mf_user[remember_me]": "0",
        }
        resp = self.session.post(_LOGIN_URL, data=payload, allow_redirects=True)
        resp.raise_for_status()

        if "/sign_in" in resp.url or "ログイン" in resp.text[:500]:
            raise RuntimeError("Login failed: check your MF_EMAIL and MF_PASSWORD")

        self._logged_in = True

    def _ensure_login(self) -> None:
        if not self._logged_in:
            self.login()

    def get_assets(self) -> dict:
        """Fetch total assets and account balances."""
        self._ensure_login()
        resp = self.session.get(_ASSETS_URL)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        total_assets = _parse_amount(
            soup.find(class_=re.compile(r"total-assets|total_assets"))
        )

        accounts = []
        for row in soup.select("table.account-list tbody tr, .account-list-item"):
            name_el = row.select_one(".account-name, td.name")
            balance_el = row.select_one(".balance, td.balance")
            if name_el and balance_el:
                accounts.append({
                    "name": name_el.get_text(strip=True),
                    "balance": _parse_amount(balance_el),
                })

        return {
            "total_assets": total_assets,
            "accounts": accounts,
        }

    def get_transactions(self, page: int = 1) -> list[dict]:
        """Fetch recent transactions."""
        self._ensure_login()
        params = {"page": page}
        resp = self.session.get(_CF_URL, params=params)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        transactions = []
        for row in soup.select("table#cf-detail-table tbody tr, .transaction-item"):
            date_el = row.select_one(".date, td.date")
            content_el = row.select_one(".content, td.content")
            amount_el = row.select_one(".amount, td.amount")
            category_el = row.select_one(".category, td.category")

            if date_el and content_el and amount_el:
                transactions.append({
                    "date": date_el.get_text(strip=True),
                    "content": content_el.get_text(strip=True),
                    "amount": amount_el.get_text(strip=True),
                    "category": category_el.get_text(strip=True) if category_el else "",
                })

        return transactions

    def get_summary_text(self) -> str:
        """Return a plain-text summary of assets and recent transactions."""
        assets = self.get_assets()
        transactions = self.get_transactions()

        lines = ["=== マネーフォワードME 資産サマリー ==="]
        if assets["total_assets"] is not None:
            lines.append(f"総資産: {assets['total_assets']:,} 円")
        lines.append("")

        if assets["accounts"]:
            lines.append("【口座残高】")
            for acct in assets["accounts"]:
                balance = f"{acct['balance']:,} 円" if acct["balance"] is not None else "取得不可"
                lines.append(f"  {acct['name']}: {balance}")
            lines.append("")

        if transactions:
            lines.append("【最近の取引】")
            for tx in transactions[:20]:
                lines.append(
                    f"  {tx['date']}  {tx['content']}  {tx['amount']}"
                    + (f"  [{tx['category']}]" if tx["category"] else "")
                )

        return "\n".join(lines)


def _parse_amount(element) -> Optional[int]:
    """Extract integer yen amount from a BeautifulSoup element."""
    if element is None:
        return None
    text = element.get_text(strip=True)
    digits = re.sub(r"[^\d\-]", "", text)
    return int(digits) if digits and digits != "-" else None
