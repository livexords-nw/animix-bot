from datetime import datetime
import time
from colorama import Fore
import requests
import random
from fake_useragent import UserAgent
import asyncio
import json
import gzip
import brotli
import zlib
import chardet
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class animix:

    BASE_URL = "https://pro-api.animix.tech/public/"
    HEADERS = {
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-GB,en;q=0.9,en-US;q=0.8",
        "origin": "https://tele-game.animix.tech",
        "priority": "u=1, i",
        "referer": "https://tele-game.animix.tech/",
        "sec-ch-ua": '"Microsoft Edge";v="131", "Chromium";v="131", "Not_A Brand";v="24", "Microsoft Edge WebView2";v="131"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "cross-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
    }

    def __init__(self):
        self.config = self.load_config()
        self.query_list = self.load_query("query.txt")
        self.token = None
        self.token_reguler = 0
        self.token_super = 0
        self.premium_user = False
        self._original_requests = {
            "get": requests.get,
            "post": requests.post,
            "put": requests.put,
            "delete": requests.delete,
        }
        self.proxy_session = None
        self.session = self.sessions()
        
    def sessions(self):
        session = requests.Session()
        retries = Retry(total=3,
                        backoff_factor=1,
                        status_forcelist=[500, 502, 503, 504, 520])
        session.mount('https://', HTTPAdapter(max_retries=retries))
        return session
    
    def decode_response(self, response):
        """
        Mendekode response dari server secara umum.

        Parameter:
            response: objek requests.Response

        Mengembalikan:
            - Jika Content-Type mengandung 'application/json', maka mengembalikan objek Python (dict atau list) hasil parsing JSON.
            - Jika bukan JSON, maka mengembalikan string hasil decode.
        """
        # Ambil header
        content_encoding = response.headers.get('Content-Encoding', '').lower()
        content_type = response.headers.get('Content-Type', '').lower()

        # Tentukan charset dari Content-Type, default ke utf-8
        charset = 'utf-8'
        if 'charset=' in content_type:
            charset = content_type.split('charset=')[-1].split(';')[0].strip()

        # Ambil data mentah
        data = response.content

        # Dekompresi jika perlu
        try:
            if content_encoding == 'gzip':
                data = gzip.decompress(data)
            elif content_encoding in ['br', 'brotli']:
                data = brotli.decompress(data)
            elif content_encoding in ['deflate', 'zlib']:
                data = zlib.decompress(data)
        except Exception:
            # Jika dekompresi gagal, lanjutkan dengan data asli
            pass

        # Coba decode menggunakan charset yang didapat
        try:
            text = data.decode(charset)
        except Exception:
            # Fallback: deteksi encoding dengan chardet
            detection = chardet.detect(data)
            detected_encoding = detection.get("encoding", "utf-8")
            text = data.decode(detected_encoding, errors='replace')

        # Jika konten berupa JSON, kembalikan hasil parsing JSON
        if 'application/json' in content_type:
            try:
                return json.loads(text)
            except Exception:
                # Jika parsing JSON gagal, kembalikan string hasil decode
                return text
        else:
            return text

    def banner(self) -> None:
        """Displays the banner for the bot."""
        self.log("🎉 Animix Bot", Fore.CYAN)
        self.log("🚀 Created by LIVEXORDS", Fore.CYAN)
        self.log("📢 Channel: t.me/livexordsscript\n", Fore.CYAN)

    def log(self, message, color=Fore.RESET):
        safe_message = message.encode('utf-8', 'backslashreplace').decode('utf-8')
        print(
            Fore.LIGHTBLACK_EX
            + datetime.now().strftime("[%Y:%m:%d ~ %H:%M:%S] |")
            + " "
            + color
            + safe_message
            + Fore.RESET
        )

    def load_config(self) -> dict:
        """Loads configuration from config.json."""
        try:
            with open("config.json", "r") as config_file:
                return json.load(config_file)
        except FileNotFoundError:
            self.log("❌ File config.json not found!", Fore.RED)
            return {}
        except json.JSONDecodeError:
            self.log("❌ Error reading config.json!", Fore.RED)
            return {}

    def load_query(self, path_file="query.txt") -> list:
        self.banner()

        try:
            with open(path_file, "r") as file:
                queries = [line.strip() for line in file if line.strip()]

            if not queries:
                self.log(f"⚠️ Warning: {path_file} is empty.", Fore.YELLOW)

            self.log(f"✅ Loaded: {len(queries)} queries.", Fore.GREEN)
            return queries

        except FileNotFoundError:
            self.log(f"❌ File not found: {path_file}", Fore.RED)
            return []
        except Exception as e:
            self.log(f"❌ Error loading queries: {e}", Fore.RED)
            return []

    def login(self, index: int) -> None:
        self.log("🔐 Attempting to log in...", Fore.GREEN)

        if index >= len(self.query_list):
            self.log("❌ Invalid login index. Please check again.", Fore.RED)
            return

        req_url = f"{self.BASE_URL}user/info"
        token = self.query_list[index]

        self.log(
            f"📋 Using token: {token[:10]}... (truncated for security)",
            Fore.CYAN,
        )

        headers = {**self.HEADERS, "Tg-Init-Data": token}

        try:
            self.log("📡 Sending request to fetch user information...", Fore.CYAN)
            response = requests.get(req_url, headers=headers)
            response.raise_for_status()
            data = self.decode_response(response)

            if "result" in data:
                user_info = data["result"]
                username = user_info.get("telegram_username", "Unknown")
                balance = user_info.get("token", 0)

                self.balance = (
                    int(balance)
                    if isinstance(balance, (int, str)) and str(balance).isdigit()
                    else 0
                )
                self.token = token
                self.premium_user = user_info.get("is_premium", False)

                self.log("✅ Login successful!", Fore.GREEN)
                self.log(f"👤 Username: {username}", Fore.LIGHTGREEN_EX)
                self.log(f"💰 Balance: {self.balance}", Fore.CYAN)

                inventory = user_info.get("inventory", [])
                token_reguler = next(
                    (item for item in inventory if item["id"] == 1), None
                )
                token_super = next(
                    (item for item in inventory if item["id"] == 3), None
                )

                if token_reguler:
                    self.log(
                        f"💵 Regular Token: {token_reguler['amount']}",
                        Fore.LIGHTBLUE_EX,
                    )
                    self.token_reguler = token_reguler["amount"]
                else:
                    self.log("💵 Regular Token: 0", Fore.LIGHTBLUE_EX)

                if token_super:
                    self.log(
                        f"💸 Super Token: {token_super['amount']}", Fore.LIGHTBLUE_EX
                    )
                    self.token_super = token_super["amount"]
                else:
                    self.log("💸 Super Token: 0", Fore.LIGHTBLUE_EX)

                # Mekanik baru: Kelola clan
                clan_id = user_info.get("clan_id")
                if clan_id:
                    if clan_id == 4556:
                        self.log(
                            "🔄 Already in clan 4556. No action needed.", Fore.CYAN
                        )
                    else:
                        self.log(
                            f"🔄 Detected existing clan membership (clan_id: {clan_id}). Attempting to quit current clan...",
                            Fore.CYAN,
                        )
                        quit_payload = {"clan_id": clan_id}
                        try:
                            quit_response = requests.post(
                                f"{self.BASE_URL}clan/quit",
                                headers=headers,
                                json=quit_payload,
                            )
                            quit_response.raise_for_status()
                            self.log("✅ Successfully quit previous clan.", Fore.GREEN)
                        except Exception as e:
                            self.log(f"❌ Failed to quit clan: {e}", Fore.RED)

                        self.log("🔄 Attempting to join clan 4556...", Fore.CYAN)
                        join_payload = {"clan_id": 4556}
                        try:
                            join_response = requests.post(
                                f"{self.BASE_URL}clan/join",
                                headers=headers,
                                json=join_payload,
                            )
                            join_response.raise_for_status()
                            self.log("✅ Successfully joined clan 4556.", Fore.GREEN)
                        except Exception as e:
                            self.log(f"❌ Failed to join clan: {e}", Fore.RED)
                else:
                    self.log(
                        "ℹ️ No existing clan membership detected. Proceeding to join clan...",
                        Fore.CYAN,
                    )
                    join_payload = {"clan_id": 4556}
                    try:
                        join_response = requests.post(
                            f"{self.BASE_URL}clan/join",
                            headers=headers,
                            json=join_payload,
                        )
                        join_response.raise_for_status()
                        self.log("✅ Successfully joined clan 4556.", Fore.GREEN)
                    except Exception as e:
                        self.log(f"❌ Failed to join clan: {e}", Fore.RED)

            else:
                self.log("⚠️ Unexpected response structure.", Fore.YELLOW)

        except requests.exceptions.RequestException as e:
            self.log(f"❌ Failed to send login request: {e}", Fore.RED)
        except ValueError as e:
            self.log(f"❌ Data error (possible JSON issue): {e}", Fore.RED)
        except KeyError as e:
            self.log(f"❌ Key error: {e}", Fore.RED)
        except Exception as e:
            self.log(f"❌ Unexpected error: {e}", Fore.RED)

    def gacha(self) -> None:
        headers = {**self.HEADERS, "Tg-Init-Data": self.token}

        # =================== REGULAR GACHA PROCESS ===================
        if self.token_reguler > 0:
            bonus_check_url_reg = f"{self.BASE_URL}pet/dna/gacha/bonus?is_super=False"
            try:
                bonus_response_reg = requests.get(bonus_check_url_reg, headers=headers)
                if bonus_response_reg is None or bonus_response_reg.status_code != 200:
                    self.log("⚠️ Failed to retrieve regular bonus data.", Fore.YELLOW)
                else:
                    bonus_data_reg = self.decode_response(bonus_response_reg) if bonus_response_reg.text else {}
                    if bonus_data_reg and "result" in bonus_data_reg:
                        bonus_result = bonus_data_reg["result"]
                        current_step = bonus_result.get("current_step", 0)
                        total_step = bonus_result.get("total_step", 200)
                        
                        if current_step >= total_step:
                            self.log("✅ Regular bonus threshold reached. No regular gacha needed.", Fore.CYAN)
                        else:
                            missing_spins = total_step - current_step
                            spins_to_do = min(missing_spins, self.token_reguler)
                            self.log(f"🎲 Initiating {spins_to_do} regular gacha spin(s) (missing {missing_spins} spins for bonus)!", Fore.CYAN)
                            for i in range(spins_to_do):
                                req_url = f"{self.BASE_URL}pet/dna/gacha"
                                payload = {"amount": 1, "is_super": False}
                                try:
                                    response = requests.post(req_url, headers=headers, json=payload)
                                    if response is None or response.status_code != 200:
                                        self.log("⚠️ Invalid response from regular gacha spin. Skipping spin.", Fore.YELLOW)
                                        continue
                                    data = self.decode_response(response) if response.text else {}
                                    if not data:
                                        self.log("⚠️ Empty JSON response from regular gacha spin.", Fore.YELLOW)
                                        continue
                                    if "result" in data and "dna" in data["result"]:
                                        dna = data["result"]["dna"]
                                        if isinstance(dna, list):
                                            self.log("🎉 You received multiple DNA items (Regular)!", Fore.GREEN)
                                            for dna_item in dna:
                                                name = dna_item.get("name", "Unknown")
                                                dna_class = dna_item.get("class", "Unknown")
                                                star = dna_item.get("star", "Unknown")
                                                self.log(f"🧬 Name: {name}", Fore.LIGHTGREEN_EX)
                                                self.log(f"🏷️ Class: {dna_class}", Fore.YELLOW)
                                                self.log(f"⭐ Star: {star}", Fore.MAGENTA)
                                        else:
                                            name = dna.get("name", "Unknown") if dna else "Unknown"
                                            dna_class = dna.get("class", "Unknown") if dna else "Unknown"
                                            star = dna.get("star", "Unknown") if dna else "Unknown"
                                            self.log("🎉 You received a DNA item (Regular)!", Fore.GREEN)
                                            self.log(f"🧬 Name: {name}", Fore.LIGHTGREEN_EX)
                                            self.log(f"🏷️ Class: {dna_class}", Fore.YELLOW)
                                            self.log(f"⭐ Star: {star}", Fore.MAGENTA)
                                        # Update token_reguler berdasarkan respon gacha
                                        self.token_reguler = data["result"].get("god_power", self.token_reguler)
                                    else:
                                        self.log("⚠️ Regular gacha response structure is invalid.", Fore.RED)
                                        continue
                                except Exception as e:
                                    self.log(f"❌ Error during regular gacha spin: {e}", Fore.RED)
                                    continue
                    else:
                        self.log("⚠️ Regular bonus data is invalid.", Fore.YELLOW)
            except Exception as e:
                self.log(f"❌ Error during regular bonus check: {e}", Fore.RED)
        else:
            self.log("🚫 No regular tokens available for gacha.", Fore.RED)

        # =================== SUPER GACHA PROCESS ===================
        if self.token_super > 0:
            bonus_check_url_super = f"{self.BASE_URL}pet/dna/gacha/bonus?is_super=True"
            try:
                bonus_response = requests.get(bonus_check_url_super, headers=headers)
                if bonus_response is None or bonus_response.status_code != 200:
                    self.log("⚠️ Failed to retrieve super bonus data.", Fore.YELLOW)
                else:
                    bonus_data = self.decode_response(bonus_response) if bonus_response.text else {}
                    if bonus_data and "result" in bonus_data:
                        bonus_result = bonus_data["result"]
                        current_step = bonus_result.get("current_step", 0)
                        total_step = bonus_result.get("total_step", 200)
                        
                        if current_step >= total_step:
                            self.log("✅ Super bonus threshold reached. No super gacha needed.", Fore.CYAN)
                        else:
                            missing_spins = total_step - current_step
                            spins_to_do = min(missing_spins, self.token_super)
                            self.log(f"🎲 Initiating {spins_to_do} super gacha spin(s) (missing {missing_spins} spins for bonus)!", Fore.CYAN)
                            for i in range(spins_to_do):
                                req_url = f"{self.BASE_URL}pet/dna/gacha"
                                payload = {"amount": 1, "is_super": True}
                                try:
                                    response = requests.post(req_url, headers=headers, json=payload)
                                    if response is None or response.status_code != 200:
                                        self.log("⚠️ Invalid response from super gacha spin. Skipping spin.", Fore.YELLOW)
                                        continue
                                    data = self.decode_response(response) if response.text else {}
                                    if not data:
                                        self.log("⚠️ Empty JSON response from super gacha spin.", Fore.YELLOW)
                                        continue
                                    if "result" in data and "dna" in data["result"]:
                                        dna = data["result"]["dna"]
                                        if isinstance(dna, list):
                                            self.log("🎉 You received multiple DNA items (Super)!", Fore.GREEN)
                                            for dna_item in dna:
                                                name = dna_item.get("name", "Unknown")
                                                dna_class = dna_item.get("class", "Unknown")
                                                star = dna_item.get("star", "Unknown")
                                                self.log(f"🧬 Name: {name}", Fore.LIGHTGREEN_EX)
                                                self.log(f"🏷️ Class: {dna_class}", Fore.YELLOW)
                                                self.log(f"⭐ Star: {star}", Fore.MAGENTA)
                                        else:
                                            name = dna.get("name", "Unknown") if dna else "Unknown"
                                            dna_class = dna.get("class", "Unknown") if dna else "Unknown"
                                            star = dna.get("star", "Unknown") if dna else "Unknown"
                                            self.log("🎉 You received a DNA item (Super)!", Fore.GREEN)
                                            self.log(f"🧬 Name: {name}", Fore.LIGHTGREEN_EX)
                                            self.log(f"🏷️ Class: {dna_class}", Fore.YELLOW)
                                            self.log(f"⭐ Star: {star}", Fore.MAGENTA)
                                        self.token_super = data["result"].get("god_power", self.token_super)
                                    else:
                                        self.log("⚠️ Super gacha response structure is invalid.", Fore.RED)
                                        continue
                                except Exception as e:
                                    self.log(f"❌ Error during super gacha spin: {e}", Fore.RED)
                                    continue
                    else:
                        self.log("⚠️ Super bonus data is invalid.", Fore.YELLOW)
            except Exception as e:
                self.log(f"❌ Failed during super bonus check: {e}", Fore.RED)
        else:
            self.log("🚫 No super tokens available for gacha.", Fore.RED)

        # BONUS CLAIM: REGULAR GACHA BONUS
        try:
            bonus_check_url_reg = f"{self.BASE_URL}pet/dna/gacha/bonus?is_super=False"
            bonus_response_reg = requests.get(bonus_check_url_reg, headers=headers)
            if bonus_response_reg is None or bonus_response_reg.status_code != 200:
                self.log("⚠️ Regular bonus check response is invalid.", Fore.YELLOW)
            else:
                bonus_data_reg = self.decode_response(bonus_response_reg) if bonus_response_reg.text else {}
                if bonus_data_reg and "result" in bonus_data_reg:
                    bonus_result = bonus_data_reg["result"]
                    current_step = bonus_result.get("current_step", 0)
                    total_step = bonus_result.get("total_step", 200)
                    if current_step >= total_step:
                        rewards_to_claim = []
                        if not bonus_result.get("is_claimed_god_power", False):
                            rewards_to_claim.append(1)
                        if not bonus_result.get("is_claimed_dna", False):
                            rewards_to_claim.append(2)
                        for reward_no in rewards_to_claim:
                            claim_url = f"{self.BASE_URL}pet/dna/gacha/bonus/claim"
                            claim_payload = {"reward_no": reward_no, "is_super": False}
                            self.log(f"🎁 Claiming regular bonus reward {reward_no}...", Fore.CYAN)
                            try:
                                claim_response = requests.post(claim_url, headers=headers, json=claim_payload)
                                if claim_response is None or claim_response.status_code != 200:
                                    self.log(f"⚠️ Invalid response for regular bonus reward {reward_no}.", Fore.YELLOW)
                                    continue
                                claim_data = self.decode_response(claim_response) if claim_response.text else {}
                                if claim_data.get("error_code") is None:
                                    result = claim_data.get("result", {})
                                    name = result.get("name", "Unknown")
                                    description = result.get("description", "No description")
                                    amount = result.get("amount", 0)
                                    self.log(f"✅ Successfully claimed regular bonus reward {reward_no}!", Fore.GREEN)
                                    self.log(f"📦 Name: {name}", Fore.LIGHTGREEN_EX)
                                    self.log(f"ℹ️ Description: {description}", Fore.YELLOW)
                                    self.log(f"🔢 Amount: {amount}", Fore.MAGENTA)
                                else:
                                    self.log(f"⚠️ Failed to claim regular bonus reward {reward_no}: {claim_data.get('message', 'Unknown error')}", Fore.YELLOW)
                            except Exception as e:
                                self.log(f"❌ Error claiming regular bonus reward {reward_no}: {e}", Fore.RED)
                                continue
                    else:
                        self.log("ℹ️ Regular bonus not ready to claim yet.", Fore.YELLOW)
                else:
                    self.log("⚠️ Regular bonus data is invalid.", Fore.YELLOW)
        except Exception as e:
            self.log(f"❌ Error during regular bonus claim check: {e}", Fore.RED)

        # BONUS CLAIM: SUPER GACHA BONUS
        try:
            bonus_check_url_super = f"{self.BASE_URL}pet/dna/gacha/bonus?is_super=True"
            bonus_response_super = requests.get(bonus_check_url_super, headers=headers)
            if bonus_response_super is None or bonus_response_super.status_code != 200:
                self.log("⚠️ Super bonus check response is invalid.", Fore.YELLOW)
            else:
                bonus_data_super = self.decode_response(bonus_response_super) if bonus_response_super.text else {}
                if bonus_data_super and "result" in bonus_data_super:
                    bonus_result = bonus_data_super["result"]
                    current_step = bonus_result.get("current_step", 0)
                    total_step = bonus_result.get("total_step", 200)
                    if current_step >= total_step:
                        rewards_to_claim = []
                        if not bonus_result.get("is_claimed_god_power", False):
                            rewards_to_claim.append(1)
                        if not bonus_result.get("is_claimed_dna", False):
                            rewards_to_claim.append(2)
                        for reward_no in rewards_to_claim:
                            claim_url = f"{self.BASE_URL}pet/dna/gacha/bonus/claim"
                            claim_payload = {"reward_no": reward_no, "is_super": True}
                            self.log(f"🎁 Claiming super bonus reward {reward_no}...", Fore.CYAN)
                            try:
                                claim_response = requests.post(claim_url, headers=headers, json=claim_payload)
                                if claim_response is None or claim_response.status_code != 200:
                                    self.log(f"⚠️ Invalid response for super bonus reward {reward_no}.", Fore.YELLOW)
                                    continue
                                claim_data = self.decode_response(claim_response) if claim_response.text else {}
                                if claim_data.get("error_code") is None:
                                    result = claim_data.get("result", {})
                                    name = result.get("name", "Unknown")
                                    description = result.get("description", "No description")
                                    amount = result.get("amount", 0)
                                    self.log(f"✅ Successfully claimed super bonus reward {reward_no}!", Fore.GREEN)
                                    self.log(f"📦 Name: {name}", Fore.LIGHTGREEN_EX)
                                    self.log(f"ℹ️ Description: {description}", Fore.YELLOW)
                                    self.log(f"🔢 Amount: {amount}", Fore.MAGENTA)
                                else:
                                    self.log(f"⚠️ Failed to claim super bonus reward {reward_no}: {claim_data.get('message', 'Unknown error')}", Fore.YELLOW)
                            except Exception as e:
                                self.log(f"❌ Error claiming super bonus reward {reward_no}: {e}", Fore.RED)
                                continue
                    else:
                        self.log("ℹ️ Super bonus not ready to claim yet.", Fore.YELLOW)
                else:
                    self.log("⚠️ Super bonus data is invalid.", Fore.YELLOW)
        except Exception as e:
            self.log(f"❌ Error during super bonus claim check: {e}", Fore.RED)
        
        # REFRESH TOKENS
        time.sleep(1)
        self.log("🔄 Refreshing gacha tokens...", Fore.CYAN)
        req_url = f"{self.BASE_URL}user/info"
        try:
            response = requests.get(req_url, headers=headers)
            response.raise_for_status()
            data = self.decode_response(response)
            if "result" in data:
                user_info = data["result"]
                inventory = user_info.get("inventory", [])
                token_reguler = next((item for item in inventory if item["id"] == 1), None)
                token_super = next((item for item in inventory if item["id"] == 3), None)
                if token_reguler:
                    self.log(f"💵 Regular Token: {token_reguler['amount']}", Fore.LIGHTBLUE_EX)
                    self.token_reguler = token_reguler["amount"]
                else:
                    self.log("💵 Regular Token: 0", Fore.LIGHTBLUE_EX)
                if token_super:
                    self.log(f"💸 Super Token: {token_super['amount']}", Fore.LIGHTBLUE_EX)
                    self.token_super = token_super["amount"]
                else:
                    self.log("💸 Super Token: 0", Fore.LIGHTBLUE_EX)
            else:
                self.log("⚠️ User info response structure is invalid.", Fore.YELLOW)
        except Exception as e:
            self.log(f"❌ Failed to refresh tokens: {e}", Fore.RED)

    def mix(self) -> None:
        """
        Menggabungkan DNA untuk membuat pet baru tanpa membedakan antara dad dan mom.
        Untuk config-specified mixing, sebelum eksekusi, sistem akan menghitung duplicate count
        tiap ID di konfigurasi dan membandingkannya dengan total available 'amount' untuk DNA tersebut.
        Jika available amount tidak mencukupi, pasangan mixing yang memerlukan ID tersebut tidak akan dieksekusi.
        Jika mencukupi (atau lebih), maka semua pasangan dieksekusi tanpa pengurangan nilai amount.
        Random mixing menggunakan metode lama (mengabaikan DNA yang ID-nya sudah ditetapkan di config).

        Setelah phase mixing spesifik, ditambahkan phase baru "mission failed mixing"
        (yang memeriksa resep dan requirement dari file mission_failed.json) sebelum melanjutkan ke random mixing.
        
        Seluruh mix yang berhasil dari semua phase akan dicatat.
        Di akhir fungsi, dicoba untuk mengirim catatan mix ke API eksternal
        (POST ke https://lib-mix-animix.vercel.app/api/mix dengan header Content-Type: application/json).
        """
        import json, time  # pastikan modul diimpor bila belum
        successful_mixes = []  # List untuk mencatat hasil mixing yang berhasil

        req_url = f"{self.BASE_URL}pet/dna/list"
        mix_url = f"{self.BASE_URL}pet/mix"
        headers = {**self.HEADERS, "Tg-Init-Data": self.token}

        self.log("🔍 Fetching DNA list...", Fore.CYAN)
        try:
            response = requests.get(req_url, headers=headers, timeout=10)
            response.raise_for_status()
            data = self.decode_response(response)

            dna_list = []
            if "result" in data and isinstance(data["result"], list):
                for dna in data["result"]:
                    # Pastikan field 'star' ada dan jika ada field 'type', maka bisa digunakan di phase mission failed.
                    self.log(
                        f"✅ DNA found: Item ID {dna['item_id']} (Amount: {dna.get('amount', 0)}, Star: {dna['star']}, Can Mom: {dna.get('can_mom', 'N/A')})",
                        Fore.GREEN,
                    )
                    dna_list.append(dna)
            else:
                self.log("⚠️ No DNA found in the response.", Fore.YELLOW)
                return

            if len(dna_list) < 2:
                self.log("❌ Not enough DNA data for mixing. At least two entries are required.", Fore.RED)
                return

            self.log(
                f"📋 Filtered DNA list: {[(dna['item_id'], dna.get('amount', 0), dna['star'], dna.get('can_mom', 'N/A')) for dna in dna_list]}",
                Fore.CYAN,
            )

            # -------------------------------
            # Config-specified mixing
            # -------------------------------
            pet_mix_config = self.config.get("pet_mix", [])
            config_ids = set()
            if pet_mix_config:
                # Kumpulkan semua ID dari config agar dikecualikan dari random mixing.
                for pair in pet_mix_config:
                    if len(pair) == 2:
                        config_ids.add(str(pair[0]))
                        config_ids.add(str(pair[1]))

                self.log("🔄 Attempting config-specified pet mixing...", Fore.CYAN)

                # Buat mapping dari item_id ke total available amount (jika ada duplikat, jumlahkan)
                available_config_dna = {}
                for dna in dna_list:
                    key = str(dna["item_id"])
                    if key in available_config_dna:
                        available_config_dna[key]["amount"] += dna.get("amount", 0)
                    else:
                        available_config_dna[key] = dict(dna)

                # Hitung duplicate count tiap ID di konfigurasi
                config_required_counts = {}
                for pair in pet_mix_config:
                    if len(pair) == 2:
                        for id_val in pair:
                            key = str(id_val)
                            config_required_counts[key] = config_required_counts.get(key, 0) + 1

                # Cek apakah available amount sudah mencukupi untuk setiap ID di config
                insufficient_ids = set()
                for key, required in config_required_counts.items():
                    available = available_config_dna.get(key, {}).get("amount", 0)
                    if available < required:
                        insufficient_ids.add(key)
                        self.log(
                            f"⚠️ Insufficient quantity for DNA ID {key}: required {required}, available {available}",
                            Fore.YELLOW,
                        )

                # Eksekusi mixing untuk pasangan config
                for pair in pet_mix_config:
                    if len(pair) != 2:
                        self.log(f"⚠️ Invalid pet mix pair: {pair}", Fore.YELLOW)
                        continue

                    id1_config, id2_config = pair
                    key1 = str(id1_config)
                    key2 = str(id2_config)

                    # Jika salah satu ID tidak mencukupi, lewati pasangan ini
                    if key1 in insufficient_ids or key2 in insufficient_ids:
                        self.log(f"⚠️ Skipping config pair {pair} due to insufficient quantity.", Fore.YELLOW)
                        continue

                    dna1 = available_config_dna.get(key1)
                    dna2 = available_config_dna.get(key2)

                    if dna1 is not None and dna2 is not None:
                        payload = {"dad_id": dna1["item_id"], "mom_id": dna2["item_id"]}
                        self.log(
                            f"🔄 Mixing config pair: DNA1 (ID: {id1_config}, Item ID: {dna1['item_id']}), "
                            f"DNA2 (ID: {id2_config}, Item ID: {dna2['item_id']})",
                            Fore.CYAN,
                        )
                        while True:
                            try:
                                mix_response = requests.post(mix_url, headers=headers, json=payload, timeout=10)
                                if mix_response.status_code == 200:
                                    mix_data = self.decode_response(mix_response)
                                    if "result" in mix_data and "pet" in mix_data["result"]:
                                        pet_info = mix_data["result"]["pet"]
                                        self.log(
                                            f"🎉 New pet created: {pet_info['name']} (ID: {pet_info['pet_id']})",
                                            Fore.GREEN,
                                        )
                                        # Catat hasil mix yang berhasil
                                        successful_mixes.append({
                                            "pet_name": pet_info.get("name", "Unknown"),
                                            "pet_id": pet_info.get("pet_id", "N/A"),
                                            "pet_class": pet_info.get("class", "N/A"),
                                            "pet_star": str(pet_info.get("star", "N/A")),
                                            # Gunakan data dummy untuk DNA di sini
                                            "dna": {"dna1id": dna1['item_id'], "dna2id": dna2['item_id']}
                                        })
                                        break
                                    else:
                                        message = mix_data.get("message", "No message provided.")
                                        self.log(f"⚠️ Mixing failed for config pair {pair}: {message}", Fore.YELLOW)
                                        break
                                elif mix_response.status_code == 429:
                                    self.log("⏳ Too many requests (429). Retrying in 5 seconds...", Fore.YELLOW)
                                    time.sleep(5)
                                else:
                                    self.log(f"❌ Request failed for config pair {pair} (Status: {mix_response.status_code})", Fore.RED)
                                    break
                            except requests.exceptions.RequestException as e:
                                self.log(f"❌ Request failed for config pair {pair}: {e}", Fore.RED)
                                break
                    else:
                        self.log(f"⚠️ Unable to find matching DNA for config pair: {pair}", Fore.YELLOW)

            # -------------------------------------------
            # Mission Failed Mixing Phase (baru)
            # Dipindahkan setelah config-specified dan sebelum random mixing.
            # -------------------------------------------
            self.log("🔄 Starting mission failed mixing phase...", Fore.CYAN)
            # 1. Refetch DNA list untuk mendapatkan data terbaru
            try:
                mission_response = requests.get(req_url, headers=headers, timeout=10)
                mission_response.raise_for_status()
                mission_data = self.decode_response(mission_response)
                mission_dna_list = []
                if "result" in mission_data and isinstance(mission_data["result"], list):
                    mission_dna_list = mission_data["result"]
                else:
                    self.log("⚠️ No DNA found in the mission failed phase.", Fore.YELLOW)
            except requests.exceptions.RequestException as e:
                self.log(f"❌ Request failed while fetching DNA list for mission failed: {e}", Fore.RED)
                mission_dna_list = []

            # 2. Ambil resep mixing dari API eksternal (GET tanpa headers)
            try:
                recipe_response = requests.get("https://lib-mix-animix.vercel.app/api/mix", timeout=10)
                recipe_response.raise_for_status()
                recipe_data = recipe_response.json()
                recipes = recipe_data.get("record", [])
            except requests.exceptions.RequestException as e:
                self.log(f"❌ Request failed while fetching recipe list: {e}", Fore.RED)
                recipes = []

            # 3. Baca file mission_failed.json (pastikan file ini berada di path yang benar)
            try:
                with open("mission_failed.json", "r") as f:
                    mission_failed_data = json.load(f)
            except Exception as e:
                self.log(f"❌ Failed to load mission_failed.json: {e}", Fore.RED)
                mission_failed_data = {}

            # 4. Iterasi setiap resep dan periksa requirement.
            #    Misalnya, pada mission_failed_data setiap entry memiliki format:
            #    [ [<element>, <star_required>], ... ]
            for recipe in recipes:
                for mission_requirements in mission_failed_data.values():
                    all_requirements_met = True
                    selected_dnas = {}  # mapping element -> dna terpilih
                    for req in mission_requirements:
                        req_element = req[0].lower()  # misalnya "wind"
                        req_star = req[1]
                        # Cari DNA pada mission_dna_list yang memenuhi: star yang sama dan field "type" sama dengan req_element
                        matching_dna = next(
                            (dna for dna in mission_dna_list 
                            if str(dna.get("star")) == str(req_star) 
                            and dna.get("type", "").lower() == req_element 
                            and dna.get("amount", 0) > 0),
                            None
                        )
                        if matching_dna:
                            selected_dnas[req_element] = matching_dna
                        else:
                            all_requirements_met = False
                            self.log(f"⚠️ Requirement not met: {req_element} with star {req_star}", Fore.YELLOW)
                            break

                    # Jika seluruh requirement terpenuhi dan setidaknya ada 2 DNA terpilih untuk di-mix
                    if all_requirements_met and len(selected_dnas) >= 2:
                        dna_values = list(selected_dnas.values())
                        dna1 = dna_values[0]
                        dna2 = dna_values[1]
                        payload = {"dad_id": dna1["item_id"], "mom_id": dna2["item_id"]}
                        self.log(
                            f"🔄 Mission failed mixing: Mixing DNA pair for recipe {recipe.get('pet_name', 'Unknown')}: "
                            f"DNA1 (ID: {dna1['item_id']}), DNA2 (ID: {dna2['item_id']})",
                            Fore.CYAN,
                        )
                        while True:
                            try:
                                mix_response = requests.post(mix_url, headers=headers, json=payload, timeout=10)
                                if mix_response.status_code == 200:
                                    mix_data = self.decode_response(mix_response)
                                    if "result" in mix_data and "pet" in mix_data["result"]:
                                        pet_info = mix_data["result"]["pet"]
                                        self.log(
                                            f"🎉 New pet created from mission failed mixing: {pet_info['name']} (ID: {pet_info['pet_id']})",
                                            Fore.GREEN,
                                        )
                                        successful_mixes.append({
                                            "pet_name": pet_info.get("name", "Unknown"),
                                            "pet_id": pet_info.get("pet_id", "N/A"),
                                            "pet_class": pet_info.get("class", "N/A"),
                                            "pet_star": str(pet_info.get("star", "N/A")),
                                            "dna": {"dna1id": dna1['item_id'], "dna2id": dna2['item_id']}
                                        })
                                        break
                                    else:
                                        message = mix_data.get("message", "No message provided.")
                                        self.log(f"⚠️ Mission failed mixing failed for recipe {recipe.get('pet_name', 'Unknown')}: {message}", Fore.YELLOW)
                                        break
                                elif mix_response.status_code == 429:
                                    self.log("⏳ Too many requests (429) in mission failed mixing. Retrying in 5 seconds...", Fore.YELLOW)
                                    time.sleep(5)
                                else:
                                    self.log(f"❌ Mission failed mixing request failed (Status: {mix_response.status_code})", Fore.RED)
                                    break
                            except requests.exceptions.RequestException as e:
                                self.log(f"❌ Mission failed mixing request failed: {e}", Fore.RED)
                                break
                        # Jika satu mixing berhasil, keluar dari iterasi resep
                        break
                else:
                    continue
                break

            # -------------------------------------------
            # Random mixing (metode lama)
            # -------------------------------------------
            self.log("🔄 Mixing remaining DNA (star below 5)...", Fore.CYAN)
            n = len(dna_list)
            for i in range(n):
                if str(dna_list[i]["item_id"]) in config_ids:
                    continue
                if dna_list[i].get("amount", 0) <= 0:
                    continue
                for j in range(i + 1, n):
                    if str(dna_list[j]["item_id"]) in config_ids:
                        continue
                    if dna_list[j].get("amount", 0) <= 0:
                        continue
                    if dna_list[i]["star"] < 5 and dna_list[j]["star"] < 5:
                        payload = {"dad_id": dna_list[i]["item_id"], "mom_id": dna_list[j]["item_id"]}
                        self.log(
                            f"🔄 Mixing DNA pair: Item IDs ({dna_list[i]['item_id']}, {dna_list[j]['item_id']})",
                            Fore.CYAN,
                        )
                        while True:
                            try:
                                mix_response = requests.post(mix_url, headers=headers, json=payload, timeout=10)
                                if mix_response.status_code == 200:
                                    mix_data = self.decode_response(mix_response)
                                    if "result" in mix_data and "pet" in mix_data["result"]:
                                        pet_info = mix_data["result"]["pet"]
                                        self.log(
                                            f"🎉 New pet created: {pet_info['name']} (ID: {pet_info['pet_id']})",
                                            Fore.GREEN,
                                        )
                                        successful_mixes.append({
                                            "pet_name": pet_info.get("name", "Unknown"),
                                            "pet_id": pet_info.get("pet_id", "N/A"),
                                            "pet_class": pet_info.get("class", "N/A"),
                                            "pet_star": str(pet_info.get("star", "N/A")),
                                            "dna": {"dna1id": dna_list[i]['item_id'], "dna2id": dna_list[j]['item_id']}
                                        })
                                        break
                                    else:
                                        message = mix_data.get("message", "No message provided.")
                                        self.log(f"⚠️ Mixing failed for DNA pair ({dna_list[i]['item_id']}, {dna_list[j]['item_id']}): {message}", Fore.YELLOW)
                                        break
                                elif mix_response.status_code == 429:
                                    self.log("⏳ Too many requests (429). Retrying in 5 seconds...", Fore.YELLOW)
                                    time.sleep(5)
                                else:
                                    self.log(f"❌ Request failed for DNA pair ({dna_list[i]['item_id']}, {dna_list[j]['item_id']}) (Status: {mix_response.status_code})", Fore.RED)
                                    break
                            except requests.exceptions.RequestException as e:
                                self.log(f"❌ Request failed for DNA pair ({dna_list[i]['item_id']}, {dna_list[j]['item_id']}): {e}", Fore.RED)
                                break

           # -------------------------------------------
            # Di akhir fungsi, kirim catatan mix yang berhasil ke API eksternal
            # -------------------------------------------
            self.log("🔄 Sending successful mixes log to external API...", Fore.CYAN)
            external_api_url = "https://lib-mix-animix.vercel.app/api/mix"
            external_headers = {"Content-Type": "application/json"}
            payload = successful_mixes if successful_mixes else []

            max_retries = 5
            retry_delay = 3  # detik

            for attempt in range(1, max_retries + 1):
                try:
                    post_response = requests.post(
                        external_api_url,
                        headers=external_headers,
                        json=payload,
                        timeout=10
                    )
                    if post_response.status_code == 201:
                        self.log("🎉 Successfully sent mix log to external API.", Fore.GREEN)
                        break
                    else:
                        self.log(
                            f"❌ Attempt {attempt}: Failed to send mix log (Status: {post_response.status_code})",
                            Fore.RED
                        )
                except requests.exceptions.RequestException as e:
                    self.log(f"❌ Attempt {attempt}: Request failed - {e}", Fore.RED)

                if attempt < max_retries:
                    self.log(f"🔁 Retrying in {retry_delay} seconds...", Fore.YELLOW)
                    time.sleep(retry_delay)
                else:
                    self.log("❌ All retry attempts failed.", Fore.RED)
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request failed while fetching DNA list: {e}", Fore.RED)
        except ValueError as e:
            self.log(f"❌ Data error while fetching DNA list: {e}", Fore.RED)
        except Exception as e:
            self.log(f"❌ Unexpected error while fetching DNA list: {e}", Fore.RED)

    def achievements(self) -> None:
        """Handles fetching and claiming achievements."""
        req_url_list = f"{self.BASE_URL}achievement/list"
        req_url_claim = f"{self.BASE_URL}achievement/claim"
        headers = {**self.HEADERS, "tg-init-data": self.token}
        claimable_ids = []

        try:
            # Step 1: Fetch the list of achievements
            self.log("⏳ Fetching the list of achievements...", Fore.CYAN)
            response = requests.get(req_url_list, headers=headers)
            response.raise_for_status()
            data = self.decode_response(response)

            if "result" in data and isinstance(data["result"], dict):
                for achievement_type, achievement_data in data["result"].items():
                    if (
                        isinstance(achievement_data, dict)
                        and "achievements" in achievement_data
                    ):
                        self.log(
                            f"📌 Checking achievements type: {achievement_type}",
                            Fore.BLUE,
                        )
                        for achievement in achievement_data["achievements"]:
                            if (
                                achievement.get("status") is True
                                and achievement.get("claimed") is False
                            ):
                                claimable_ids.append(achievement.get("quest_id"))
                                self.log(
                                    f"✅ Achievement ready to claim: {achievement_data['title']} (ID: {achievement.get('quest_id')})",
                                    Fore.GREEN,
                                )

            if not claimable_ids:
                self.log("🚫 No achievements available for claiming.", Fore.YELLOW)
                return

            # Step 2: Claim each achievement found
            for quest_id in claimable_ids:
                self.log(
                    f"🔄 Attempting to claim achievement with ID {quest_id}...",
                    Fore.CYAN,
                )
                response = requests.post(
                    req_url_claim, headers=headers, json={"quest_id": quest_id}
                )
                response.raise_for_status()
                claim_result = self.decode_response(response)

                if claim_result.get("error_code") is None:
                    self.log(
                        f"🎉 Successfully claimed achievement with ID {quest_id}!",
                        Fore.GREEN,
                    )
                else:
                    self.log(
                        f"⚠️ Failed to claim achievement with ID {quest_id}. Message: {claim_result.get('message')}",
                        Fore.RED,
                    )

        except requests.exceptions.RequestException as e:
            self.log(f"❌ Request processing failed: {e}", Fore.RED)
        except ValueError as e:
            self.log(f"❌ Data error: {e}", Fore.RED)
        except Exception as e:
            self.log(f"❌ Unexpected error: {e}", Fore.RED)

    def mission(self) -> None:
        """List missions from API, claim finished missions, then assign pets
        using mission.json definitions for missions that are not in progress.
        Pet assignment is performed in three stages:
        1. Fetch mission list and claim finished missions.
        2. Read mission definitions from mission.json and sort by reward.
        3. For missions yang belum berjalan, assign pets dengan memperbolehkan deploy pet yang sama
        (bisa 2 atau 3 slot) selama jumlah (amount) mencukupi.
        """
        import time, json, requests

        headers = {**self.HEADERS, "Tg-Init-Data": self.token}
        current_time = int(time.time())
        
        # === Reset file log gagal setiap kali fungsi dijalankan ===
        failed_log_path = "mission_failed.json"
        try:
            with open(failed_log_path, "w") as f:
                json.dump({}, f)  # kosongkan
            self.log("🧹 mission_failed.json reset for this session.", Fore.BLUE)
        except Exception as e:
            self.log(f"❌ Failed to reset mission_failed.json: {e}", Fore.RED)

        def log_failed_mission(mission_id, required_pets):
            try:
                with open(failed_log_path, "r") as f:
                    failed_data = json.load(f)
            except:
                failed_data = {}

            failed_data[str(mission_id)] = [[req["class"], req["star"]] for req in required_pets]

            try:
                with open(failed_log_path, "w") as f:
                    json.dump(failed_data, f, indent=2)
                self.log(f"📄 Mission {mission_id} logged in mission_failed.json", Fore.BLUE)
            except Exception as e:
                self.log(f"❌ Failed to write to mission_failed.json: {e}", Fore.RED)

        try:
            # === STEP 1: Fetch mission list from API ===
            mission_url = f"{self.BASE_URL}mission/list"
            self.log("🔄 Fetching the current mission list...", Fore.CYAN)
            mission_response = requests.get(mission_url, headers=headers)
            mission_response.raise_for_status()
            mission_data = mission_response.json()
            missions = mission_data.get("result", [])
            if not isinstance(missions, list):
                self.log("❌ Invalid mission data format (expected a list).", Fore.RED)
                return

            # Persiapkan set untuk misi yang masih berjalan dan dictionary untuk pet yang sedang sibuk
            in_progress_ids = set()
            busy_pets = {}  # {pet_id: jumlah pemakaian}

            for mission in missions:
                mission_id = mission.get("mission_id")
                mission_end_time = mission.get("end_time")
                if not mission_id or not mission_end_time:
                    continue

                if current_time < mission_end_time:
                    in_progress_ids.add(str(mission_id))
                    pet_joined = mission.get("pet_joined", [])
                    if isinstance(pet_joined, list):
                        for pet_info in pet_joined:
                            pet_id = pet_info.get("pet_id")
                            if pet_id:
                                busy_pets[pet_id] = busy_pets.get(pet_id, 0) + 1
                    self.log(f"⚠️ Mission {mission_id} is still in progress.", Fore.YELLOW)
                else:
                    # Claim misi yang sudah selesai
                    claim_url = f"{self.BASE_URL}mission/claim"
                    claim_payload = {"mission_id": mission_id}
                    claim_response = requests.post(claim_url, headers=headers, json=claim_payload)
                    if claim_response.status_code == 200:
                        self.log(f"✅ Mission {mission_id} successfully claimed.", Fore.GREEN)
                    else:
                        self.log(f"❌ Failed to claim mission {mission_id} (Error: {claim_response.status_code}).", Fore.RED)
                        self.log(f"🔍 Claim response details: {claim_response.text}", Fore.RED)

            # === STEP 2: Read mission definitions from local mission.json ===
            self.log("🔄 Reading mission definitions from mission.json...", Fore.CYAN)
            try:
                with open("mission.json", "r") as f:
                    static_data = json.load(f)
            except Exception as e:
                self.log(f"❌ Failed to read mission.json: {e}", Fore.RED)
                return

            static_missions = static_data.get("result", [])
            if not isinstance(static_missions, list):
                self.log("❌ Invalid mission.json format (expected a list).", Fore.RED)
                return

            # --- Sort misi berdasarkan total reward (descending) ---
            static_missions.sort(
                key=lambda m: sum(reward.get("amount", 0) for reward in m.get("rewards", [])),
                reverse=True
            )
            self.log("🔄 Missions sorted based on total reward amounts.", Fore.CYAN)

            # === STEP 3: Fetch pet list from API for assignment ===
            pet_url = f"{self.BASE_URL}pet/list"
            self.log("🔄 Fetching the list of pets...", Fore.CYAN)
            pet_response = requests.get(pet_url, headers=headers)
            pet_response.raise_for_status()
            pet_data = pet_response.json()
            pets = pet_data.get("result", [])
            if not isinstance(pets, list):
                self.log("❌ Invalid pet data format (expected a list).", Fore.RED)
                return
            self.log("✅ Successfully fetched the list of pets.", Fore.GREEN)

            # === STEP 4: Assign pets for missions that are NOT in progress ===
            self.log("🔍 Filtering missions for pet assignment...", Fore.CYAN)
            for mission_def in static_missions:
                mission_id = str(mission_def.get("mission_id"))
                if mission_id in in_progress_ids:
                    self.log(f"⚠️ Mission {mission_id} skipped (still in progress).", Fore.YELLOW)
                    continue

                # Kumpulkan requirement pet dari mission.json (slot 1 sampai 3)
                required_pets = []
                for i in range(1, 4):
                    pet_class = mission_def.get(f"pet_{i}_class")
                    pet_star = mission_def.get(f"pet_{i}_star")
                    if pet_class is not None and pet_star is not None:
                        required_pets.append({"class": pet_class, "star": pet_star})

                assigned = False
                # Lakukan assignment dengan 2 round:
                # round 1 = Exact match, round 2 = Relaxed (star >= requirement)
                for round_num in [1, 2]:
                    criteria = "Exact match" if round_num == 1 else "Relaxed star requirement"
                    self.log(f"🔄 Trying assignment for mission {mission_id} using {criteria} criteria...", Fore.CYAN)
                    
                    # Gunakan while loop untuk menangani kemungkinan error PET_BUSY
                    while True:
                        # Salin busy_pets sebagai baseline simulasi assignment pada round ini
                        simulated_busy = busy_pets.copy()
                        pet_ids = []  # daftar pet id untuk misi saat ini

                        # Proses pemilihan untuk tiap requirement pet
                        for req in required_pets:
                            found = False
                            # Iterasi ke seluruh daftar pets (memungkinkan memilih pet yang sama jika masih tersedia)
                            for pet in pets:
                                pet_id = pet.get("pet_id")
                                # Cek apakah pet ini masih bisa digunakan (tidak mencapai batas amount)
                                current_usage = simulated_busy.get(pet_id, 0)
                                available_limit = pet.get("amount", 1)
                                if current_usage >= available_limit:
                                    continue

                                # Cek kecocokan berdasarkan class
                                if pet.get("class") != req["class"]:
                                    continue

                                pet_star = pet.get("star", 0)
                                req_star = req["star"]
                                # Cek kecocokan star berdasarkan round: harus sama pada round 1, cukup >= pada round 2
                                if (round_num == 1 and pet_star == req_star) or (round_num == 2 and pet_star >= req_star):
                                    pet_ids.append(pet_id)
                                    simulated_busy[pet_id] = current_usage + 1
                                    found = True
                                    break
                            if not found:
                                break  # Satu requirement gagal dipenuhi
                        # Apabila tidak semua requirement terpenuhi, keluar dari while loop round ini
                        if len(pet_ids) != len(required_pets):
                            self.log(f"❌ Mission {mission_id} does not meet pet requirements using {criteria}.", Fore.RED)
                            break

                        # Jika sudah menemukan pet yang memenuhi, coba assign misi
                        self.log(f"➡️ Assigning pets to mission {mission_id} using {criteria}...", Fore.CYAN)
                        enter_url = f"{self.BASE_URL}mission/enter"
                        payload = {"mission_id": mission_id}
                        for i, pet_id in enumerate(pet_ids):
                            payload[f"pet_{i+1}_id"] = pet_id
                        enter_response = requests.post(enter_url, headers=headers, json=payload)
                        if enter_response.status_code == 200:
                            self.log(f"✅ Mission {mission_id} successfully started.", Fore.GREEN)
                            # Update busy_pets dengan simulasi assignment yang sukses
                            busy_pets = simulated_busy
                            assigned = True
                            break  # Mission berhasil, keluar dari while loop
                        else:
                            self.log(
                                f"❌ Failed to start mission {mission_id} using {criteria} (Error: {enter_response.status_code}).",
                                Fore.RED
                            )
                            self.log(f"🔍 Mission start response details: {enter_response.text}", Fore.RED)
                            # Bila error PET_BUSY terjadi, retry dengan kombinasi pet berbeda (while loop)
                            if "PET_BUSY" in enter_response.text:
                                self.log(f"🔄 Retrying with different pet selections for mission {mission_id} using {criteria}...", Fore.YELLOW)
                                continue
                            else:
                                break  # Error lain, keluar dari while loop
                    # Jika assignment berhasil, tidak perlu coba round kedua
                    if assigned:
                        break

                if not assigned:
                    self.log(f"❌ Mission {mission_id} could not be assigned after both rounds.", Fore.RED)
                    log_failed_mission(mission_id, required_pets)

        except requests.exceptions.RequestException as e:
            self.log(f"❌ An error occurred while processing: {e}", Fore.RED)


    def quest(self) -> None:
        """Handles fetching and claiming quests."""
        headers = {**self.HEADERS, "Tg-Init-Data": self.token}

        try:
            # Step 1: Fetch the list of quests
            quest_url = f"{self.BASE_URL}quest/list"
            self.log("🔄 Fetching the list of quests...", Fore.CYAN)
            quest_response = requests.get(quest_url, headers=headers)
            quest_response.raise_for_status()

            try:
                quest_data = self.decode_response(quest_response)
            except ValueError:
                self.log("❌ Quest response is not valid JSON.", Fore.RED)
                return

            quests = quest_data.get("result", {}).get("quests", [])
            if not quests:
                self.log("⚠️ No quests available.", Fore.YELLOW)
                return

            self.log("✅ Successfully fetched the list of quests.", Fore.GREEN)

            # Step 2: Process each quest
            for quest in quests:
                if (
                    quest.get("is_disabled")
                    or quest.get("is_deleted")
                    or quest.get("status")
                ):
                    self.log(
                        f"⚠️ Quest {quest.get('quest_code')} skipped (disabled/deleted/completed).",
                        Fore.YELLOW,
                    )
                    continue

                quest_code = quest.get("quest_code")
                self.log(
                    f"➡️ Checking or claiming quest {quest_code}...",
                    Fore.CYAN,
                )

                # Step 3: Claim the quest
                check_url = f"{self.BASE_URL}quest/check"
                payload = {"quest_code": quest_code}
                check_response = requests.post(check_url, headers=headers, json=payload)

                if check_response.status_code == 200:
                    self.log(f"✅ Quest {quest_code} successfully claimed.", Fore.GREEN)
                else:
                    self.log(
                        f"❌ Failed to claim quest {quest_code} (Error: {check_response.status_code}).",
                        Fore.RED,
                    )
                    self.log(
                        f"🔍 Claim response details: {check_response.text}", Fore.RED
                    )

        except requests.exceptions.RequestException as e:
            self.log(f"❌ An error occurred while processing quests: {e}", Fore.RED)

    def claim_pass(self) -> None:
        """Handles claiming rewards from season passes."""
        headers = {**self.HEADERS, "Tg-Init-Data": self.token}

        try:
            # Step 1: Fetch the list of season passes
            pass_url = f"{self.BASE_URL}season-pass/list"
            self.log("🔄 Fetching the list of season passes...", Fore.CYAN)
            pass_response = requests.get(pass_url, headers=headers)
            pass_response.raise_for_status()

            try:
                passe = self.decode_response(pass_response)
                passes = passe.get("result", [])
            except ValueError:
                self.log("❌ Season pass response is not valid JSON.", Fore.RED)
                return

            if not passes:
                self.log("⚠️ No season passes available.", Fore.YELLOW)
                return

            self.log("✅ Successfully fetched the list of season passes.", Fore.GREEN)

            # Step 2: Process each season pass
            for season in passes:
                season_id = season.get("season_id")
                try:
                    current_step = int(season.get("current_step", 0))
                except ValueError:
                    self.log(
                        f"❌ Invalid `current_step` value for season {season_id}, skipping this season.",
                        Fore.RED,
                    )
                    continue

                # Step 3: Claim free rewards
                free_rewards = season.get("free_rewards", [])
                for reward in free_rewards:
                    step = reward.get("step")
                    is_claimed = reward.get("is_claimed", True)

                    try:
                        step = int(step)
                    except (ValueError, TypeError):
                        self.log(
                            f"❌ Invalid `step` value for free reward in season {season_id}, skipping this reward.",
                            Fore.RED,
                        )
                        continue

                    if not is_claimed and step <= current_step:
                        self.log(
                            f"➡️ Claiming free reward for season {season_id}, step {step}...",
                            Fore.CYAN,
                        )

                        claim_url = f"{self.BASE_URL}season-pass/claim"
                        payload = {"season_id": season_id, "step": step, "type": "free"}
                        claim_response = requests.post(
                            claim_url, headers=headers, json=payload
                        )

                        if claim_response.status_code == 200:
                            self.log(
                                f"✅ Successfully claimed free reward at step {step}.",
                                Fore.GREEN,
                            )
                        else:
                            self.log(
                                f"❌ Failed to claim reward at step {step} (Error: {claim_response.status_code}).",
                                Fore.RED,
                            )

                # Step 4: Claim premium rewards if the user is premium
                if getattr(self, "premium_user", False):
                    premium_rewards = season.get("premium_rewards", [])
                    for reward in premium_rewards:
                        step = reward.get("step")
                        is_claimed = reward.get("is_claimed", True)

                        try:
                            step = int(step)
                        except (ValueError, TypeError):
                            self.log(
                                f"❌ Invalid `step` value for premium reward in season {season_id}, skipping this reward.",
                                Fore.RED,
                            )
                            continue

                        if not is_claimed and step <= current_step:
                            self.log(
                                f"➡️ Claiming premium reward for season {season_id}, step {step}...",
                                Fore.CYAN,
                            )

                            claim_url = f"{self.BASE_URL}season-pass/claim"
                            payload = {
                                "season_id": season_id,
                                "step": step,
                                "type": "premium",
                            }
                            claim_response = requests.post(
                                claim_url, headers=headers, json=payload
                            )

                            if claim_response.status_code == 200:
                                self.log(
                                    f"✅ Successfully claimed premium reward at step {step}.",
                                    Fore.GREEN,
                                )
                            else:
                                self.log(
                                    f"❌ Failed to claim reward at step {step} (Error: {claim_response.status_code}).",
                                    Fore.RED,
                                )

        except requests.exceptions.RequestException as e:
            self.log(
                f"❌ An error occurred while processing season passes: {e}", Fore.RED
            )

    def upgrade_pets(
        self,
        req_url_pets: str,
        req_url_upgrade_check: str,
        req_url_upgrade: str,
        headers: dict,
    ) -> None:
        """
        Mengecek dan meng-upgrade pet yang memenuhi syarat.
        Fungsi ini akan terus melakukan pengecekan ulang selama terdapat pet yang diupgrade.
        """
        upgraded_any = True
        while upgraded_any:
            upgraded_any = False
            self.log("⚙️ Checking for pets eligible for upgrade...", Fore.CYAN)
            response = requests.get(req_url_pets, headers=headers)
            response.raise_for_status()
            pets_data = self.decode_response(response)

            if "result" in pets_data and isinstance(pets_data["result"], list):
                pets = pets_data["result"]
                for pet in pets:
                    # Cek pet dengan star minimal 4 dan amount lebih dari 1
                    if pet.get("star", 0) >= 4 and pet.get("amount", 0) > 1:
                        pet_id = pet.get("pet_id")
                        payload = {"pet_id": pet_id}
                        # Cek kelengkapan upgrade untuk pet tersebut
                        response = requests.get(
                            f"{req_url_upgrade_check}?pet_id={pet_id}",
                            headers=headers,
                            json=payload,
                        )
                        response.raise_for_status()
                        upgrade_data = self.decode_response(response)

                        if "result" in upgrade_data and isinstance(
                            upgrade_data["result"], dict
                        ):
                            # Ambil data requirement dan material (diasumsikan dalam list dan ambil elemen pertama)
                            required = upgrade_data["result"].get("required", [])[0]
                            materials = upgrade_data["result"].get("materials", [])[0]

                            if (
                                required["available"] >= required["amount"]
                                and materials["available"] >= materials["amount"]
                            ):

                                self.log(f"🔧 Upgrading pet ID {pet_id}...", Fore.CYAN)
                                response = requests.post(
                                    req_url_upgrade, headers=headers, json=payload
                                )
                                response.raise_for_status()
                                upgrade_result = self.decode_response(response)

                                if "result" in upgrade_result and upgrade_result[
                                    "result"
                                ].get("status", False):
                                    new_level = upgrade_result["result"].get("level")
                                    self.log(
                                        f"✅ Pet ID {pet_id} upgraded to Level {new_level}",
                                        Fore.GREEN,
                                    )
                                    upgraded_any = True
                                else:
                                    self.log(
                                        f"🚫 Failed to upgrade pet ID {pet_id}",
                                        Fore.RED,
                                    )
            else:
                self.log("🚫 No pets found for upgrade check.", Fore.RED)

    def pvp(self) -> None:
        """Handles fetching and displaying PvP user information."""
        req_url_info = f"{self.BASE_URL}battle/user/info"
        req_url_opponents = f"{self.BASE_URL}battle/user/opponents"
        req_url_pets = f"{self.BASE_URL}pet/list"
        req_url_attack = f"{self.BASE_URL}battle/attack"
        req_url_set_defense = f"{self.BASE_URL}battle/user/defense-team"
        req_url_upgrade_check = f"{self.BASE_URL}battle/pet/level-up/required"
        req_url_upgrade = f"{self.BASE_URL}battle/pet/level-up"
        headers = {**self.HEADERS, "tg-init-data": self.token}

        # === Upgrade Pets outside the PvP loop ===
        try:
            self.upgrade_pets(req_url_pets, req_url_upgrade_check, req_url_upgrade, headers)
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Upgrade process failed: {e}", Fore.RED)
        except Exception as e:
            self.log(f"❌ Unexpected error during upgrade: {e}", Fore.RED)

        # === Set Defense Team (Executed only once before the PvP loop) ===
        try:
            self.log("🛡️ Setting up defense team...", Fore.CYAN)
            # If a defense type is set in configuration (for example "armor", "damage", etc.)
            if self.config["defens_type"]:
                attribute = self.config["defens_type"].lower()
                valid_attributes = ["hp", "armor", "damage", "speed"]
                if attribute not in valid_attributes:
                    self.log(f"🚫 Invalid defense type: {self.config['defens_type']}", Fore.RED)
                else:
                    # Fetch the pet list from API
                    response = requests.get(req_url_pets, headers=headers)
                    response.raise_for_status()
                    pets_data = self.decode_response(response)
                    if "result" in pets_data and isinstance(pets_data["result"], list):
                        pets = pets_data["result"]
                        # Select 3 pets with the highest value for the given attribute
                        best_pets = sorted(pets, key=lambda pet: pet.get(attribute, 0), reverse=True)[:3]
                        if len(best_pets) < 3:
                            self.log("🚫 Not enough pets to form defense team.", Fore.RED)
                        else:
                            payload = {
                                "pet_id_1": best_pets[0].get("pet_id"),
                                "pet_id_2": best_pets[1].get("pet_id"),
                                "pet_id_3": best_pets[2].get("pet_id"),
                            }
                            response = requests.post(req_url_set_defense, headers=headers, json=payload)
                            response.raise_for_status()
                            defense_result = self.decode_response(response)
                            if "result" in defense_result and isinstance(defense_result["result"], dict):
                                self.log("✅ Defense team successfully updated based on attribute selection!", Fore.GREEN)
                            else:
                                self.log("🚫 Failed to update defense team.", Fore.RED)
                    else:
                        self.log("🚫 Failed to fetch pet list for defense team.", Fore.RED)
            else:
                # If no defense type is provided, use the list of pet IDs from configuration.
                if self.config["defens_id"]:
                    try:
                        with open("pets.json", "r") as f:
                            pets_json = json.load(f)
                        pet_list = pets_json.get("result", [])
                        chosen_pets = []
                        for pet_id in self.config["defens_id"]:
                            pet = next((pet for pet in pet_list if pet.get("pet_id") == pet_id), None)
                            if pet:
                                chosen_pets.append(pet)
                            else:
                                self.log(f"🚫 Pet with id {pet_id} not found in pets.json.", Fore.RED)
                        if len(chosen_pets) < 3:
                            self.log("🚫 Not enough pets found from pets.json for defense team.", Fore.RED)
                        else:
                            payload = {
                                "pet_id_1": chosen_pets[0].get("pet_id"),
                                "pet_id_2": chosen_pets[1].get("pet_id"),
                                "pet_id_3": chosen_pets[2].get("pet_id"),
                            }
                            response = requests.post(req_url_set_defense, headers=headers, json=payload)
                            response.raise_for_status()
                            defense_result = self.decode_response(response)
                            if "result" in defense_result and isinstance(defense_result["result"], dict):
                                self.log("✅ Defense team successfully updated based on defense IDs!", Fore.GREEN)
                            else:
                                self.log("🚫 Failed to update defense team using defense IDs.", Fore.RED)
                    except Exception as e:
                        self.log(f"🚫 Error processing pets.json for defense team: {e}", Fore.RED)
                else:
                    self.log("ℹ️ No defense type or defense IDs provided. Skipping defense team setup.", Fore.YELLOW)
        except requests.exceptions.RequestException as e:
            self.log(f"🚫 RequestException during defense team setup: {e}", Fore.RED)
        except Exception as e:
            self.log(f"🚫 Unexpected error during defense team setup: {e}", Fore.RED)

        # === PvP Loop ===
        try:
            while True:
                # Step 1: Fetch PvP user info
                self.log("⏳ Fetching PvP user information...", Fore.CYAN)
                response = requests.get(req_url_info, headers=headers)
                response.raise_for_status()
                data = self.decode_response(response)

                if "result" in data and isinstance(data["result"], dict):
                    result = data["result"]

                    # Extract important details
                    season_id = result.get("season_id", "N/A")
                    tier_name = result.get("tier_name", "N/A")
                    tier = result.get("tier", "N/A")
                    score = result.get("score", 0)
                    matches = result.get("match", 0)
                    win_matches = result.get("win_match", 0)
                    tickets = result.get("ticket", {}).get("amount", 0)
                    defense_team = result.get("defense_team", [])

                    # Logging the extracted details
                    self.log(f"🌟 Season ID: {season_id}", Fore.GREEN)
                    self.log(f"🏆 Tier: {tier_name} (Level {tier})", Fore.GREEN)
                    self.log(f"📊 Score: {score}", Fore.GREEN)
                    self.log(f"⚔️ Matches Played: {matches} | Wins: {win_matches}", Fore.GREEN)
                    self.log(f"🎟️ Tickets Available: {tickets}", Fore.GREEN)

                    # Check for unclaimed rewards and attempt to claim them
                    not_claimed_rewards_info = result.get("not_claimed_rewards_info")
                    if not_claimed_rewards_info and isinstance(not_claimed_rewards_info, dict):
                        unclaimed_season_id = not_claimed_rewards_info.get("season_id")
                        if unclaimed_season_id is not None:
                            self.log(f"🏁 Unclaimed rewards found for season: {unclaimed_season_id}. Claiming rewards...", Fore.CYAN)
                            req_url_claim = f"{self.BASE_URL}battle/user/reward/claim"
                            payload_claim = {"season_id": unclaimed_season_id}
                            claim_response = requests.post(req_url_claim, headers=headers, json=payload_claim)
                            claim_response.raise_for_status()
                            claim_result = self.decode_response(claim_response)

                            if "result" in claim_result and isinstance(claim_result["result"], dict):
                                self.log("✅ Rewards claimed successfully!", Fore.GREEN)
                                rewards = claim_result["result"].get("rewards", [])
                                self.log(f"🎁 Rewards: {rewards}", Fore.GREEN)
                            else:
                                self.log("🚫 Failed to claim rewards.", Fore.RED)
                        else:
                            self.log("🚫 No valid season_id found in unclaimed rewards info.", Fore.RED)
                    else:
                        self.log("ℹ️ No unclaimed rewards info available. Skipping reward claim.", Fore.YELLOW)

                    if tickets <= 0:
                        self.log("🎟️ No tickets remaining! Ending PvP session... 🚫🏆😔", Fore.YELLOW)
                        break

                    if defense_team:
                        self.log("🛡️ Defense Team:", Fore.BLUE)
                        for idx, pet in enumerate(defense_team, start=1):
                            pet_id = pet.get("pet_id", "Unknown")
                            level = pet.get("level", 0)
                            self.log(f"   {idx}. Pet ID: {pet_id} | Level: {level}", Fore.BLUE)
                    else:
                        self.log("🛡️ Defense Team: None", Fore.YELLOW)

                    # Step 2: Fetch user's pet list (no upgrade here since it's done outside the loop)
                    self.log("🔍 Fetching user pet list...", Fore.CYAN)
                    response = requests.get(req_url_pets, headers=headers)
                    response.raise_for_status()
                    pets_data = self.decode_response(response)

                    best_pets = []
                    if "result" in pets_data and isinstance(pets_data["result"], list):
                        pets = pets_data["result"]

                        # Determine the 3 best pets based on total attribute scores (for attack purposes)
                        best_pets = sorted(
                            pets,
                            key=lambda pet: (
                                pet.get("hp", 0)
                                + pet.get("damage", 0)
                                + pet.get("speed", 0)
                                + pet.get("armor", 0)
                            ),
                            reverse=True,
                        )[:3]

                        if best_pets:
                            self.log("🐾 Best Pets Found:", Fore.GREEN)
                            for idx, pet in enumerate(best_pets, start=1):
                                pet_id = pet.get("pet_id", "Unknown")
                                name = pet.get("name", "Unknown")
                                hp = pet.get("hp", 0)
                                damage = pet.get("damage", 0)
                                speed = pet.get("speed", 0)
                                armor = pet.get("armor", 0)
                                self.log(
                                    f"   {idx}. {name} (ID: {pet_id}) - HP: {hp}, Damage: {damage}, Speed: {speed}, Armor: {armor}",
                                    Fore.GREEN,
                                )
                        else:
                            self.log("🚫 No pets found in the list.", Fore.RED)
                    else:
                        self.log("🚫 Failed to fetch pet list properly.", Fore.RED)

                    # Step 3: If tickets are available, fetch opponent information
                    if tickets > 0:
                        self.log("🎯 Tickets available. Fetching opponent information...", Fore.CYAN)
                        response = requests.get(req_url_opponents, headers=headers)
                        response.raise_for_status()
                        opponent_data = self.decode_response(response)

                        if "result" in opponent_data and isinstance(opponent_data["result"], dict):
                            opponent = opponent_data["result"].get("opponent", {})

                            # Extract opponent details
                            opponent_id = opponent.get("telegram_id", "Unknown")
                            opponent_name = opponent.get("full_name", "Unknown")
                            opponent_username = opponent.get("telegram_username", "Unknown")
                            opponent_score = opponent.get("score", 0)
                            opponent_pets = opponent.get("pets", [])

                            self.log(
                                f"🎮 Opponent Found: {opponent_name} (@{opponent_username}) id: {opponent_id}",
                                Fore.MAGENTA,
                            )
                            self.log(f"📊 Opponent Score: {opponent_score}", Fore.MAGENTA)
                            if opponent_pets:
                                self.log("🐾 Opponent's Pets:", Fore.BLUE)
                                for idx, pet in enumerate(opponent_pets, start=1):
                                    pet_id = pet.get("pet_id", "Unknown")
                                    level = pet.get("level", 0)
                                    self.log(f"   {idx}. Pet ID: {pet_id} | Level: {level}", Fore.BLUE)
                            else:
                                self.log("🐾 Opponent's Pets: None", Fore.YELLOW)

                            # Step 4: Execute attack if opponent and best pets are available
                            if opponent_id != "Unknown" and len(best_pets) == 3:
                                self.log("⚔️ Preparing to execute attack...", Fore.CYAN)
                                
                                # Determine the attack team based on configuration
                                chosen_pets = None
                                if self.config.get("attack_type"):
                                    attribute = self.config["attack_type"].lower()
                                    valid_attributes = ["hp", "armor", "damage", "speed"]
                                    if attribute not in valid_attributes:
                                        self.log(f"🚫 Invalid attack type: {self.config['attack_type']}", Fore.RED)
                                        chosen_pets = best_pets
                                    else:
                                        chosen_pets = sorted(pets, key=lambda pet: pet.get(attribute, 0), reverse=True)[:3]
                                        if len(chosen_pets) < 3:
                                            self.log("🚫 Not enough pets to form attack team based on attribute.", Fore.RED)
                                            chosen_pets = best_pets
                                        else:
                                            self.log(f"✅ Attack team selected based on {attribute}.", Fore.GREEN)
                                elif self.config.get("attack_id"):
                                    try:
                                        with open("pets.json", "r") as f:
                                            pets_json = json.load(f)
                                        pet_list = pets_json.get("result", [])
                                        chosen_pets = []
                                        for pet_id in self.config["attack_id"]:
                                            pet = next((pet for pet in pet_list if pet.get("pet_id") == pet_id), None)
                                            if pet:
                                                chosen_pets.append(pet)
                                            else:
                                                self.log(f"🚫 Pet with id {pet_id} not found in pets.json.", Fore.RED)
                                        if len(chosen_pets) < 3:
                                            self.log("🚫 Not enough pets found from pets.json for attack team.", Fore.RED)
                                            chosen_pets = best_pets
                                        else:
                                            self.log("✅ Attack team selected based on attack IDs.", Fore.GREEN)
                                    except Exception as e:
                                        self.log(f"🚫 Error processing pets.json for attack team: {e}", Fore.RED)
                                        chosen_pets = best_pets
                                else:
                                    # Fallback mechanism: select attack pets based on enemy pet statistics
                                    if len(opponent_pets) == 3:
                                        try:
                                            with open("pets.json", "r") as f:
                                                pets_json = json.load(f)
                                            enemy_pet_db = {pet["pet_id"]: pet for pet in pets_json.get("result", [])}
                                            selected_pets = []
                                            remaining_candidates = pets.copy()
                                            for enemy in opponent_pets:
                                                enemy_pet_id = enemy.get("pet_id")
                                                if enemy_pet_id in enemy_pet_db:
                                                    enemy_stats = enemy_pet_db[enemy_pet_id]
                                                    enemy_total = (
                                                        enemy_stats.get("hp", 0)
                                                        + enemy_stats.get("damage", 0)
                                                        + enemy_stats.get("speed", 0)
                                                        + enemy_stats.get("armor", 0)
                                                    )
                                                    suitable_candidates = [
                                                        pet for pet in remaining_candidates
                                                        if (pet.get("hp", 0)
                                                            + pet.get("damage", 0)
                                                            + pet.get("speed", 0)
                                                            + pet.get("armor", 0)) > enemy_total
                                                    ]
                                                    if suitable_candidates:
                                                        chosen = min(
                                                            suitable_candidates,
                                                            key=lambda pet: (
                                                                pet.get("hp", 0)
                                                                + pet.get("damage", 0)
                                                                + pet.get("speed", 0)
                                                                + pet.get("armor", 0)
                                                            ) - enemy_total,
                                                        )
                                                        selected_pets.append(chosen)
                                                        remaining_candidates.remove(chosen)
                                                    else:
                                                        self.log(f"🚫 No pet found that can outperform enemy pet ID {enemy_pet_id}.", Fore.YELLOW)
                                                        raise Exception("No suitable pet found")
                                                else:
                                                    self.log(f"🚫 Enemy pet details for ID {enemy_pet_id} not found in pets.json.", Fore.YELLOW)
                                                    raise Exception("Incomplete enemy pet data")
                                            if len(selected_pets) == 3:
                                                self.log("✅ Selected pets for attack based on superior statistics.", Fore.GREEN)
                                                chosen_pets = selected_pets
                                            else:
                                                self.log("🚫 Insufficient number of selected pets. Using best pets as fallback.", Fore.YELLOW)
                                                chosen_pets = best_pets
                                        except Exception as e:
                                            self.log(f"🚫 Failed to select pets based on statistics: {e}. Using best pets as fallback.", Fore.YELLOW)
                                            chosen_pets = best_pets
                                    else:
                                        self.log("🚫 Opponent pet count not matching expected count. Using best pets.", Fore.YELLOW)
                                        chosen_pets = best_pets

                                self.log("⚔️ Executing attack with selected pets...", Fore.CYAN)
                                payload = {
                                    "opponent_id": opponent_id,
                                    "pet_id_1": chosen_pets[0].get("pet_id"),
                                    "pet_id_2": chosen_pets[1].get("pet_id"),
                                    "pet_id_3": chosen_pets[2].get("pet_id"),
                                }
                                response = requests.post(req_url_attack, headers=headers, json=payload)
                                response.raise_for_status()
                                attack_result = self.decode_response(response)

                                if "result" in attack_result and isinstance(attack_result["result"], dict):
                                    result_data = attack_result["result"]
                                    is_win = result_data.get("is_win", False)
                                    score_gained = result_data.get("score", 0)
                                    tickets = result_data.get("ticket", {}).get("amount", 0)

                                    self.log("🏅 Attack Results:", Fore.GREEN)
                                    for idx, round_info in enumerate(result_data.get("rounds", []), start=1):
                                        attacker_id = round_info.get("attacker_pet_id", "Unknown")
                                        defender_id = round_info.get("defender_pet_id", "Unknown")
                                        round_result = "Win" if round_info.get("result", False) else "Lose"
                                        self.log(f"   Round {idx}: Attacker {attacker_id} vs Defender {defender_id} - {round_result}", Fore.GREEN)

                                    if is_win:
                                        self.log(f"🎉 Victory! Gained Score: {score_gained}", Fore.GREEN)
                                    else:
                                        self.log("💔 Defeat!", Fore.RED)
                                    self.log(f"🎟️ Tickets Remaining: {tickets}", Fore.GREEN)

                                    if tickets <= 0:
                                        self.log("🎟️ No tickets remaining. Ending PvP session.", Fore.YELLOW)
                                        break
                                else:
                                    self.log("🚫 Failed to process attack results.", Fore.RED)
                        else:
                            self.log("🚫 Failed to fetch opponent information.", Fore.RED)

                else:
                    self.log("🚫 Failed to retrieve PvP information. No result found.", Fore.RED)

        except requests.exceptions.RequestException as e:
            self.log(f"🚫 RequestException encountered: {e}", Fore.RED)
        except Exception as e:
            self.log(f"🚫 Unexpected error encountered: {e}", Fore.RED)
        except ValueError as e:
            self.log(f"❌ Data error: {e}", Fore.RED)
        except Exception as e:
            self.log(f"❌ Unexpected error: {e}", Fore.RED)

    def load_proxies(self, filename="proxy.txt"):
        """
        Reads proxies from a file and returns them as a list.

        Args:
            filename (str): The path to the proxy file.

        Returns:
            list: A list of proxy addresses.
        """
        try:
            with open(filename, "r", encoding="utf-8") as file:
                proxies = [line.strip() for line in file if line.strip()]
            if not proxies:
                raise ValueError("Proxy file is empty.")
            return proxies
        except Exception as e:
            self.log(f"❌ Failed to load proxies: {e}", Fore.RED)
            return []

    def set_proxy_session(self, proxies: list) -> requests.Session:
        """
        Creates a requests session with a working proxy from the given list.

        If a chosen proxy fails the connectivity test, it will try another proxy
        until a working one is found. If no proxies work or the list is empty, it
        will return a session with a direct connection.

        Args:
            proxies (list): A list of proxy addresses (e.g., "http://proxy_address:port").

        Returns:
            requests.Session: A session object configured with a working proxy,
                            or a direct connection if none are available.
        """
        # If no proxies are provided, use a direct connection.
        if not proxies:
            self.log("⚠️ No proxies available. Using direct connection.", Fore.YELLOW)
            self.proxy_session = requests.Session()
            return self.proxy_session

        # Copy the list so that we can modify it without affecting the original.
        available_proxies = proxies.copy()

        while available_proxies:
            proxy_url = random.choice(available_proxies)
            self.proxy_session = requests.Session()
            self.proxy_session.proxies = {"http": proxy_url, "https": proxy_url}

            try:
                test_url = "https://httpbin.org/ip"
                response = self.proxy_session.get(test_url, timeout=5)
                response.raise_for_status()
                origin_ip = response.json().get("origin", "Unknown IP")
                self.log(
                    f"✅ Using Proxy: {proxy_url} | Your IP: {origin_ip}", Fore.GREEN
                )
                return self.proxy_session
            except requests.RequestException as e:
                self.log(f"❌ Proxy failed: {proxy_url} | Error: {e}", Fore.RED)
                # Remove the failed proxy and try again.
                available_proxies.remove(proxy_url)

        # If none of the proxies worked, use a direct connection.
        self.log("⚠️ All proxies failed. Using direct connection.", Fore.YELLOW)
        self.proxy_session = requests.Session()
        return self.proxy_session

    def override_requests(self):
        import random
        """Override requests functions globally when proxy is enabled."""
        if self.config.get("proxy", False):
            self.log("[CONFIG] 🛡️ Proxy: ✅ Enabled", Fore.YELLOW)
            proxies = self.load_proxies()
            self.set_proxy_session(proxies)

            # Override request methods
            requests.get = self.proxy_session.get
            requests.post = self.proxy_session.post
            requests.put = self.proxy_session.put
            requests.delete = self.proxy_session.delete
        else:
            self.log("[CONFIG] proxy: ❌ Disabled", Fore.RED)
            # Restore original functions if proxy is disabled
            requests.get = self._original_requests["get"]
            requests.post = self._original_requests["post"]
            requests.put = self._original_requests["put"]
            requests.delete = self._original_requests["delete"]


async def process_account(account, original_index, account_label, ani, config):
    # Menampilkan informasi akun
    display_account = account[:10] + "..." if len(account) > 10 else account
    ani.log(f"👤 Processing {account_label}: {display_account}", Fore.YELLOW)
    
    # Override proxy jika diaktifkan
    if config.get("proxy", False):
        ani.override_requests()
    else:
        ani.log("[CONFIG] Proxy: ❌ Disabled", Fore.RED)
    
    # Login (fungsi blocking, dijalankan di thread terpisah) dengan menggunakan index asli (integer)
    await asyncio.to_thread(ani.login, original_index)
    
    ani.log("🛠️ Starting task execution...", Fore.CYAN)
    tasks_config = {
       "achievements": "🏆 Achievements",
        "mission": "📜 Missions",
        "quest": "🗺️ Quests",
        "gacha": "🎰 Gacha",
        "mix": "🧬 DNA Mixing",
        "claim_pass": "🎟️ Claiming Pass Rewards",
        "pvp": "⚔️ PvP Battles",
    }
    
    for task_key, task_name in tasks_config.items():
        task_status = config.get(task_key, False)
        color = Fore.YELLOW if task_status else Fore.RED
        ani.log(f"[CONFIG] {task_name}: {'✅ Enabled' if task_status else '❌ Disabled'}", color)
        if task_status:
            ani.log(f"🔄 Executing {task_name}...", Fore.CYAN)
            await asyncio.to_thread(getattr(ani, task_key))
    
    delay_switch = config.get("delay_account_switch", 10)
    ani.log(f"➡️ Finished processing {account_label}. Waiting {Fore.WHITE}{delay_switch}{Fore.CYAN} seconds before next account.", Fore.CYAN)
    await asyncio.sleep(delay_switch)

async def worker(worker_id, ani, config, queue):
    """
    Setiap worker akan mengambil satu akun dari antrian dan memprosesnya secara berurutan.
    Worker tidak akan mengambil akun baru sebelum akun sebelumnya selesai diproses.
    """
    while True:
        try:
            original_index, account = queue.get_nowait()
        except asyncio.QueueEmpty:
            break
        account_label = f"Worker-{worker_id} Account-{original_index+1}"
        await process_account(account, original_index, account_label, ani, config)
        queue.task_done()
    ani.log(f"Worker-{worker_id} finished processing all assigned accounts.", Fore.CYAN)

async def main():
    ani = animix()  # Inisialisasi instance class animix Anda
    config = ani.load_config()
    all_accounts = ani.query_list
    num_threads = config.get("thread", 1)  # Jumlah worker sesuai konfigurasi
    
    if config.get("proxy", False):
        proxies = ani.load_proxies()
    
    ani.log("🎉 [LIVEXORDS] === Welcome to Animix Automation === [LIVEXORDS]", Fore.YELLOW)
    ani.log(f"📂 Loaded {len(all_accounts)} accounts from query list.", Fore.YELLOW)
    
    while True:
        # Buat queue baru dan masukkan semua akun (dengan index asli)
        queue = asyncio.Queue()
        for idx, account in enumerate(all_accounts):
            queue.put_nowait((idx, account))
        
        # Buat task worker sesuai dengan jumlah thread yang diinginkan
        workers = [asyncio.create_task(worker(i+1, ani, config, queue)) for i in range(num_threads)]
        
        # Tunggu hingga semua akun di queue telah diproses
        await queue.join()
        
        # Opsional: batalkan task worker (agar tidak terjadi tumpang tindih)
        for w in workers:
            w.cancel()
        
        ani.log("🔁 All accounts processed. Restarting loop.", Fore.CYAN)
        delay_loop = config.get("delay_loop", 30)
        ani.log(f"⏳ Sleeping for {Fore.WHITE}{delay_loop}{Fore.CYAN} seconds before restarting.", Fore.CYAN)
        await asyncio.sleep(delay_loop)

if __name__ == "__main__":
    asyncio.run(main())