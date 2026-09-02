"""RingGuard AI — Synthetic Entity Generators.

Stage 2: Synthetic Data Engine.
Generates baseline relational entities: Customers, Accounts, Devices,
IP Addresses, Beneficiaries, and Merchants with stable IDs and realistic properties.
Strictly deterministic when seeded.
"""

import hashlib
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
from faker import Faker
import numpy as np


class EntityGenerator:
    """Generates deterministic relational entities for RingGuard synthetic datasets."""

    def __init__(self, seed: int, start_date: datetime, end_date: datetime):
        self.seed = seed
        self.start_date = start_date
        self.end_date = end_date
        self.rng = random.Random(seed)
        self.np_rng = np.random.default_rng(seed)

        # Initialize Faker with seed
        Faker.seed(seed)
        self.fake = Faker("en_IN")

    def _random_date(self, start: datetime, end: datetime) -> datetime:
        """Generate a deterministic random datetime between start and end."""
        delta = end - start
        total_seconds = int(delta.total_seconds())
        if total_seconds <= 0:
            return start
        random_seconds = self.rng.randint(0, total_seconds)
        return start + timedelta(seconds=random_seconds)

    def generate_customers(self, count: int) -> List[Dict[str, Any]]:
        """Generate synthetic customers."""
        customers: List[Dict[str, Any]] = []
        for i in range(1, count + 1):
            customer_id = f"CUST_{i:06d}"
            # Deterministic account creation window (up to 365 days prior to start_date)
            cust_created = self._random_date(
                self.start_date - timedelta(days=365),
                self.start_date - timedelta(days=10),
            )
            phone_seed = f"{self.seed}_{i}_phone"
            phone_hash = hashlib.sha256(phone_seed.encode()).hexdigest()[:12]
            risk_tier = self.rng.choices(
                ["STANDARD", "PREMIUM", "LOW_ACTIVITY"], weights=[0.75, 0.15, 0.10]
            )[0]

            customers.append(
                {
                    "customer_id": customer_id,
                    "customer_name": self.fake.name(),
                    "customer_email": f"user_{i}_{phone_hash[:6]}@example.synth",
                    "customer_phone_hash": f"PH_{phone_hash}",
                    "risk_tier": risk_tier,
                    "created_at": cust_created.isoformat(),
                }
            )
        return customers

    def generate_accounts(
        self, count: int, customers: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate synthetic accounts mapped to customers."""
        accounts: List[Dict[str, Any]] = []
        num_cust = len(customers)

        for i in range(1, count + 1):
            account_id = f"ACC_{i:06d}"
            # Primary 1:1 mapping with small chance of customer having second account
            cust_idx = (i - 1) % num_cust if i <= num_cust else self.rng.randint(0, num_cust - 1)
            customer = customers[cust_idx]
            cust_created = datetime.fromisoformat(customer["created_at"])

            # Account created after customer created
            account_created = self._random_date(
                cust_created + timedelta(days=1),
                self.start_date - timedelta(days=2),
            )

            acc_status = self.rng.choices(
                ["ACTIVE", "ACTIVE", "ACTIVE", "RESTRICTED", "DORMANT"],
                weights=[0.85, 0.05, 0.05, 0.03, 0.02],
            )[0]

            acc_type = self.rng.choices(
                ["SAVINGS", "CURRENT", "WALLET"], weights=[0.70, 0.20, 0.10]
            )[0]

            accounts.append(
                {
                    "account_id": account_id,
                    "customer_id": customer["customer_id"],
                    "account_created_at": account_created.isoformat(),
                    "account_status": acc_status,
                    "account_type": acc_type,
                    # Provenance fields will be filled during scenario assignment
                    "scenario_id": "SCEN_UNASSIGNED",
                    "scenario_type": "LEGITIMATE",
                    "ground_truth_label": "legitimate",
                }
            )
        return accounts

    def generate_devices(self, count: int) -> List[Dict[str, Any]]:
        """Generate synthetic device entities."""
        devices: List[Dict[str, Any]] = []
        device_types = [
            ("MOBILE_ANDROID", "Android 14"),
            ("MOBILE_ANDROID", "Android 13"),
            ("MOBILE_IOS", "iOS 17.4"),
            ("MOBILE_IOS", "iOS 16.6"),
            ("DESKTOP_WINDOWS", "Windows 11"),
            ("DESKTOP_MAC", "macOS Sonoma"),
        ]

        for i in range(1, count + 1):
            device_id = f"DEV_{i:06d}"
            dtype, os_name = self.rng.choice(device_types)
            dev_created = self._random_date(
                self.start_date - timedelta(days=400),
                self.start_date - timedelta(days=30),
            )
            fp_raw = f"{self.seed}_dev_{i}_{dtype}"
            fingerprint = hashlib.sha256(fp_raw.encode()).hexdigest()[:16]

            devices.append(
                {
                    "device_id": device_id,
                    "device_type": dtype,
                    "device_created_at": dev_created.isoformat(),
                    "device_os": os_name,
                    "fingerprint_hash": f"FP_{fingerprint}",
                }
            )
        return devices

    def generate_ips(self, count: int) -> List[Dict[str, Any]]:
        """Generate synthetic IP address records."""
        ips: List[Dict[str, Any]] = []

        isps = {
            "RESIDENTIAL": [
                ("Airtel Broadband", "IN"),
                ("JioFiber Commercial", "IN"),
                ("ACT Fibernet", "IN"),
                ("Tata Play Fiber", "IN"),
            ],
            "CELLULAR": [
                ("Jio 5G Mobile", "IN"),
                ("Airtel 4G/5G", "IN"),
                ("Vodafone Idea Mobile", "IN"),
            ],
            "DATACENTER": [
                ("Amazon AWS Datacenter", "IN"),
                ("DigitalOcean Droplets", "SG"),
                ("Hetzner Online GmbH", "DE"),
                ("Google Cloud Compute", "IN"),
            ],
            "VPN_PROXY": [
                ("Nord Security Relays", "SG"),
                ("Cloudflare WARP Anycast", "US"),
                ("ProtonVPN Transit", "CH"),
            ],
        }

        for i in range(1, count + 1):
            ip_id = f"IP_{i:06d}"
            # Type distribution: mostly residential and cellular, small portion DC/VPN
            ip_type = self.rng.choices(
                ["RESIDENTIAL", "CELLULAR", "DATACENTER", "VPN_PROXY"],
                weights=[0.60, 0.25, 0.10, 0.05],
            )[0]

            isp_name, country = self.rng.choice(isps[ip_type])
            # Deterministic synthetic IP octets (e.g. 103.xxx or 49.xxx for IN, 10.xxx reserved for synth)
            octet1 = self.rng.choice([49, 103, 106, 117, 157, 182]) if country == "IN" else 128
            octet2 = (self.seed + i) % 254 + 1
            octet3 = (self.seed * 3 + i) % 254 + 1
            octet4 = (self.seed * 7 + i) % 254 + 1
            ip_str = f"{octet1}.{octet2}.{octet3}.{octet4}"

            ips.append(
                {
                    "ip_id": ip_id,
                    "ip_address": ip_str,
                    "ip_type": ip_type,
                    "asn_org": isp_name,
                    "country": country,
                }
            )
        return ips

    def generate_beneficiaries(self, count: int) -> List[Dict[str, Any]]:
        """Generate synthetic beneficiary endpoints."""
        beneficiaries: List[Dict[str, Any]] = []
        btypes = [
            ("INDIVIDUAL_ACCOUNT", 0.55),
            ("UPI_VPA", 0.30),
            ("WALLET_MERCHANT", 0.10),
            ("ESCROW_GATEWAY", 0.05),
        ]
        types_list, weights = zip(*btypes)
        ifsc_prefixes = ["HDFC", "SBIN", "ICIC", "UTIB", "KKBK", "BARB", "PUNB"]

        for i in range(1, count + 1):
            ben_id = f"BEN_{i:06d}"
            btype = self.rng.choices(types_list, weights=weights)[0]
            ifsc = f"{self.rng.choice(ifsc_prefixes)}0{self.rng.randint(100000, 999999)}"
            acct_raw = f"BEN_RAW_{self.seed}_{i}_{ifsc}"
            account_hash = hashlib.sha256(acct_raw.encode()).hexdigest()[:16]

            beneficiaries.append(
                {
                    "beneficiary_id": ben_id,
                    "beneficiary_type": btype,
                    "bank_ifsc_prefix": ifsc[:4],
                    "account_hash": f"ACT_{account_hash}",
                }
            )
        return beneficiaries

    def generate_merchants(self, count: int) -> List[Dict[str, Any]]:
        """Generate synthetic merchant destinations."""
        merchants: List[Dict[str, Any]] = []
        categories = [
            ("ECOMMERCE", "LOW", 0.30),
            ("FOOD_GROCERY", "LOW", 0.25),
            ("UTILITIES_BILLS", "LOW", 0.15),
            ("TRAVEL_HOSPITALITY", "MEDIUM", 0.10),
            ("GAMING_ENTERTAINMENT", "ELEVATED", 0.10),
            ("FINANCIAL_SERVICES", "MEDIUM", 0.05),
            ("JEWELRY_LUXURY", "ELEVATED", 0.05),
        ]
        cats, ratings, weights = zip(*categories)

        for i in range(1, count + 1):
            mer_id = f"MER_{i:06d}"
            idx = self.rng.choices(range(len(cats)), weights=weights)[0]
            category = cats[idx]
            risk_rating = ratings[idx]

            merchants.append(
                {
                    "merchant_id": mer_id,
                    "merchant_name": f"{self.fake.company()} {category.split('_')[0].title()}",
                    "merchant_category": category,
                    "merchant_risk_rating": risk_rating,
                }
            )
        return merchants
