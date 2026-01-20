import json
from pathlib import Path
from typing import Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class CurrencyConverter:
    """Convert amounts to USD using exchange rates."""

    def __init__(self, rates_file: Optional[Path] = None):
        """
        Initialize the currency converter.

        Args:
            rates_file: Path to JSON file with exchange rates
        """
        self.rates = {}
        self.rates_date = None

        if rates_file and rates_file.exists():
            self.load_rates(rates_file)

    def load_rates(self, rates_file: Path) -> bool:
        """
        Load exchange rates from a JSON file.

        Expected format:
        {
            "date": "2026-01-20",
            "base": "USD",
            "rates": {
                "EUR": 1.08,
                "GBP": 1.27,
                "ILS": 0.27
            }
        }

        Args:
            rates_file: Path to the rates JSON file

        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            with open(rates_file, 'r') as f:
                data = json.load(f)

            self.rates = data.get('rates', {})
            self.rates_date = data.get('date')

            # Ensure USD is in the rates (rate of 1.0)
            self.rates['USD'] = 1.0

            logger.info(f"Loaded {len(self.rates)} exchange rates for {self.rates_date}")
            return True

        except Exception as e:
            logger.error(f"Error loading exchange rates: {str(e)}")
            return False

    def set_rates(self, rates: dict, date: Optional[str] = None):
        """
        Set exchange rates programmatically.

        Args:
            rates: Dictionary of currency code to USD rate
            date: Date of the rates (optional)
        """
        self.rates = rates
        self.rates['USD'] = 1.0  # Ensure USD is included
        self.rates_date = date or datetime.now().strftime('%Y-%m-%d')
        logger.info(f"Set {len(self.rates)} exchange rates")

    def convert_to_usd(self, amount: float, currency: str) -> Optional[float]:
        """
        Convert an amount to USD.

        Args:
            amount: The amount to convert
            currency: The source currency code (e.g., 'EUR', 'GBP')

        Returns:
            Amount in USD, or None if currency not found
        """
        if not currency:
            logger.warning("No currency provided, assuming USD")
            return amount

        currency = currency.upper().strip()

        if currency == 'USD':
            return amount

        rate = self.rates.get(currency)

        if rate is None:
            logger.warning(f"No exchange rate found for {currency}")
            return None

        # Rate is "how many USD per 1 unit of currency"
        usd_amount = amount * rate
        return round(usd_amount, 2)

    def get_rate(self, currency: str) -> Optional[float]:
        """
        Get the exchange rate for a currency.

        Args:
            currency: The currency code

        Returns:
            Exchange rate to USD, or None if not found
        """
        return self.rates.get(currency.upper().strip())

    def has_rate(self, currency: str) -> bool:
        """
        Check if a rate exists for the given currency.

        Args:
            currency: The currency code

        Returns:
            True if rate exists, False otherwise
        """
        return currency.upper().strip() in self.rates

    def get_supported_currencies(self) -> list:
        """
        Get list of currencies with available rates.

        Returns:
            List of currency codes
        """
        return list(self.rates.keys())
