import csv
import json
import os
import random
import threading
import time
import webbrowser
from typing import List, Dict
import requests
from bs4 import BeautifulSoup
from colorama import Fore, Style, init
from fake_useragent import UserAgent
from requests.exceptions import ProxyError, Timeout, RequestException
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService

# Initialize colorama for colored terminal output
init(autoreset=True)

class GoogleDorkSearch:
    def __init__(self):
        self.ua = UserAgent()
        self.base_url = 'https://www.google.com/search'
        self.results = []
        self.proxies = []
        self.session = requests.Session()
        self.session.headers.update({
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br'
        })
        self.proxy_lock = threading.Lock()
        self.current_proxy_index = 0

    def test_proxy(self, proxy: dict) -> bool:
        test_urls = [
            {"url": "http://httpbin.org/ip", "method": "GET"},
            {"url": "https://httpbin.org/ip", "method": "GET"}  # Add HTTPS test
        ]

        for test_url in test_urls:
            try:
                url = test_url["url"]
                method = test_url["method"]

                response = requests.request(method, url, proxies=proxy, timeout=5)

                if response.status_code == 200:
                    print(f"{Fore.GREEN}✓ Proxy {proxy} is working with {url}.")
                    return True
                else:
                    print(f"{Fore.RED}✗ Proxy {proxy} returned status code {response.status_code} with {url}.")
            except (ProxyError, Timeout, RequestException) as e:
                print(f"{Fore.YELLOW}⚠ Proxy {proxy} failed with {url}: {str(e)}")
                continue

        print(f"{Fore.RED}✗ Proxy {proxy} failed all tests.")
        return False

    def load_proxies_from_file_menu(self):
        """Menu option to load proxies from a file."""
        filename = input(f"{Fore.GREEN}Enter the filename containing proxies (e.g., proxies.txt): ").strip()
        self.dork_search.load_proxies_from_file(filename)
        self.show_menu()


    def load_proxies_from_file(self, filename: str):
        """Load proxies from a text file and validate them."""
        try:
            with open(filename, "r", encoding="utf-8") as f:
                proxy_list = [line.strip() for line in f if line.strip()]
            print(f"{Fore.YELLOW}Loaded {len(proxy_list)} proxies from file.")
            self.validate_and_test_proxies(proxy_list)
        except FileNotFoundError:
            print(f"{Fore.RED}⚠ Proxy file '{filename}' not found.")

    def validate_and_test_proxies(self, proxy_list: List[str]):
        """Validate proxies, check their type, and measure response time."""
        valid_proxies = []
        threads = []

        print(f"{Fore.YELLOW}Validating and testing proxies...")
        for proxy in proxy_list:
            thread = threading.Thread(target=self._validate_and_test_proxy_thread, args=(proxy, valid_proxies))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        if valid_proxies:
            self.proxies = valid_proxies
            print(f"{Fore.GREEN}✓ {len(valid_proxies)} proxies configured successfully!")
        else:
            print(f"{Fore.RED}⚠ No valid proxies found.")

    def _validate_and_test_proxy_thread(self, proxy: str, valid_proxies: list):
        """Thread worker to validate and test a single proxy."""
        proxy_type = self.detect_proxy_type(proxy)
        if not proxy_type:
            print(f"{Fore.RED}⚠ Skipping malformed proxy: {proxy}")
            return

        proxy_dict = {proxy_type: proxy}
        start_time = time.time()
        if self.test_proxy(proxy_dict):
            response_time = int((time.time() - start_time) * 1000)
            with self.proxy_lock:
                valid_proxies.append({"proxy": proxy, "type": proxy_type, "response_time": response_time})
            print(f"{Fore.GREEN}✓ Proxy {proxy} ({proxy_type}) is working with response time {response_time} ms.")
        else:
            print(f"{Fore.RED}✗ Proxy {proxy} failed validation.")

    def detect_proxy_type(self, proxy: str) -> str:
        """Detect the type of proxy (SOCKS5, SOCKS4, HTTP)."""
        if "socks5" in proxy.lower():
            return "socks5"
        elif "socks4" in proxy.lower():
            return "socks4"
        else:
            return "http"



    def set_proxies(self, proxy_list: List[str]):
        valid_proxies = []
        print(f"{Fore.YELLOW}Testing proxies...")
        threads = []
        for proxy in proxy_list:
            proxy = proxy.strip()
            if not proxy:
                continue

            proxy_dict = self.parse_proxy(proxy)
            if not proxy_dict:
                print(f"{Fore.RED}⚠ Skipping malformed proxy: {proxy}")
                continue

            thread = threading.Thread(target=self._test_proxy_thread, args=(proxy_dict, valid_proxies))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        if valid_proxies:
            self.proxies = valid_proxies
            print(f"{Fore.GREEN}✓ {len(valid_proxies)} proxies configured successfully!")
        else:
            print(f"{Fore.RED}⚠ No valid proxies found.")

    def _test_proxy_thread(self, proxy: dict, valid_proxies: list):
        if self.test_proxy(proxy):
            with self.proxy_lock:
                valid_proxies.append(proxy)

    def parse_proxy(self, proxy: str) -> dict:
        proxy = proxy.strip()
        if not proxy:
            return {}

        if proxy.startswith("http://http://"):
            proxy = proxy.replace("http://http://", "http://")
        elif proxy.startswith("https://https://"):
            proxy = proxy.replace("https://https://", "https://")

        if "socks5" in proxy.lower():
            return {'http': f'socks5://{proxy}', 'https': f'socks5://{proxy}'}
        elif "socks4" in proxy.lower():
            return {'http': f'socks4://{proxy}', 'https': f'socks4://{proxy}'}
        else:
            # Use only HTTP for proxies that don't explicitly support HTTPS
            return {'http': f'http://{proxy}'}  # Remove the 'https' key

    def get_next_proxy(self):
        with self.proxy_lock:
            if not self.proxies:
                print(f"{Fore.RED}No proxies available.")
                return None
            proxy = self.proxies[self.current_proxy_index]
            self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxies)
            print(f"{Fore.YELLOW}Using proxy: {proxy}")
            return proxy

    def bypass_captcha_with_selenium(self, query: str):
        print(f"{Fore.CYAN}Attempting to bypass CAPTCHA with Selenium...")

        # Path to ChromeDriver
        driver_path = "C:/selenium/drivers/chromedriver.exe"  # Update this path if necessary

        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument(f"user-agent={self.ua.random}")

        # Use the Service class to specify the driver path
        service = ChromeService(executable_path=driver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)

        try:
            driver.get("https://www.google.com/search?q=" + query.replace(' ', '+'))
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.g")))
            html = driver.page_source
            self._parse_results(html)
            print(f"{Fore.GREEN}✓ CAPTCHA bypassed and results parsed.")
        except Exception as e:
            print(f"{Fore.RED}✗ Error during CAPTCHA bypass: {str(e)}")
        finally:
            driver.quit()

    def solve_captcha_with_third_party(self, site_key: str, page_url: str, api_key: str):
        print(f"{Fore.CYAN}Solving CAPTCHA with third-party service...")
        captcha_service_url = "https://2captcha.com/in.php"
        params = {
            'key': api_key,
            'method': 'userrecaptcha',
            'googlekey': site_key,
            'pageurl': page_url,
            'json': 1
        }
        response = requests.post(captcha_service_url, data=params)
        if response.status_code == 200:
            result = response.json()
            if result['status'] == 1:
                captcha_id = result['request']
                print(f"{Fore.GREEN}✓ CAPTCHA submitted. Waiting for solution...")
                solution_url = f"https://2captcha.com/res.php?key={api_key}&action=get&id={captcha_id}&json=1"
                while True:
                    solution_response = requests.get(solution_url)
                    solution_data = solution_response.json()
                    if solution_data['status'] == 1:
                        captcha_solution = solution_data['request']
                        print(f"{Fore.GREEN}✓ CAPTCHA solved: {captcha_solution}")
                        return captcha_solution
                    time.sleep(5)
            else:
                print(f"{Fore.RED}✗ CAPTCHA submission failed: {result['request']}")
        else:
            print(f"{Fore.RED}✗ Failed to submit CAPTCHA: {response.status_code}")

    def search(self, query: str, num_pages: int = 1):
        self.results.clear()
        print(f"\n{Fore.YELLOW}=== STARTING SEARCH ===")
        print(f"{Fore.CYAN}Dork: {query}")
        print(f"{Fore.CYAN}Pages: {num_pages}")

        max_retries = 3  # Maximum number of retries for CAPTCHA
        retries = 0

        for page in range(num_pages):
            while retries < max_retries:
                try:
                    params = {
                        'q': query,
                        'start': page * 10,
                        'hl': 'en'
                    }

                    headers = {
                        'User-Agent': self.ua.random,
                        'Referer': self.base_url,
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'Connection': 'keep-alive'
                    }

                    proxy = self.get_next_proxy()

                    response = self.session.get(
                        self.base_url,
                        params=params,
                        headers=headers,
                        proxies=proxy,
                        timeout=15,
                        allow_redirects=True
                    )

                    if "captcha" in response.text.lower() or "sorry" in response.text.lower():
                        print(f"{Fore.RED}⚠ CAPTCHA detected! Retrying... ({retries + 1}/{max_retries})")
                        retries += 1
                        time.sleep(5)  # Wait before retrying
                        continue

                    if response.status_code != 200:
                        print(f"{Fore.RED}✗ Status code: {response.status_code}")
                        break

                    self._parse_results(response.text)
                    print(f"{Fore.GREEN}✓ Page {page + 1}/{num_pages} completed.")

                    wait_time = random.uniform(5, 15)
                    print(f"{Fore.MAGENTA}... Waiting {wait_time:.1f} s for the next page ...")
                    time.sleep(wait_time)
                    break  # Exit retry loop if successful

                except Exception as e:
                    print(f"{Fore.RED}✗ Error on page {page + 1}: {str(e)}")
                    retries += 1
                    time.sleep(5)  # Wait before retrying
                    continue

            if retries >= max_retries:
                print(f"{Fore.RED}✗ Max retries reached for page {page + 1}. Skipping...")
                continue

    def _parse_results(self, html: str):
        soup = BeautifulSoup(html, 'html.parser')
        for result in soup.select('div.g'):
            try:
                title_element = result.select_one('h3.LC20lb')
                if not title_element:
                    continue
                title = title_element.get_text().strip()

                link_element = result.select_one('a')
                if not link_element or 'href' not in link_element.attrs:
                    continue
                url = link_element['href']

                snippet_element = result.select_one('div.VwiC3b')
                snippet_text = snippet_element.get_text().strip() if snippet_element else 'N/A'

                self.results.append({
                    'title': title,
                    'url': url,
                    'snippet': snippet_text
                })
            except Exception as e:
                print(f"{Fore.RED}⚠ Error processing result: {str(e)}")
                continue

class DorkMenu:
    def __init__(self):
        self.dork_search = GoogleDorkSearch()
        self.search_history = []
        self.load_history()
        self.dork_examples = self.load_dorks_from_file("dorks.json")

    def load_dorks_from_file(self, filename: str) -> List[Dict]:
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"{Fore.RED}⚠ Dorks file '{filename}' not found. Using an empty list.")
            return []

    def load_history(self):
        try:
            with open("search_history.json", "r", encoding="utf-8") as f:
                self.search_history = json.load(f)
        except FileNotFoundError:
            self.search_history = []

    def save_history(self):
        try:
            with open("search_history.json", "w", encoding="utf-8") as f:
                json.dump(self.search_history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"{Fore.RED}✗ Error saving history: {str(e)}")

    def show_menu(self):
        print(f"""
{Fore.BLUE}====================================
{Fore.YELLOW}MAIN MENU - GOOGLE DORK SEARCH
{Fore.BLUE}====================================
{Fore.CYAN}1. {Fore.WHITE}Advanced Search (Dork)
{Fore.CYAN}2. {Fore.WHITE}Run All Dorks Automatically
{Fore.CYAN}3. {Fore.WHITE}Configure Proxies
{Fore.CYAN}4. {Fore.WHITE}View History
{Fore.CYAN}5. {Fore.WHITE}Export Results
{Fore.CYAN}6. {Fore.WHITE}Test Proxies
{Fore.CYAN}7. {Fore.WHITE}Solve CAPTCHA with Third-Party Service
{Fore.CYAN}0. {Fore.WHITE}Exit
{Fore.BLUE}====================================
""")
        choice = input(f"{Fore.GREEN}>> Choose an option: ")
        self.handle_choice(choice.strip())

    def handle_choice(self, choice: str):
        if choice == '1':
            self.advanced_search()
        elif choice == '2':
            self.run_all_dorks()
        elif choice == '3':
            self.configure_proxies()
        elif choice == '4':
            self.show_history()
        elif choice == '5':
            self.export_menu()
        elif choice == '6':
            self.test_proxies()
        elif choice == '7':
            self.solve_captcha_menu()
        elif choice == '0':
            self.exit_program()
        else:
            print(f"{Fore.RED}⚠ Invalid option. Try again.")
            self.show_menu()

    def advanced_search(self):
        print(f"{Fore.YELLOW}\n--- ADVANCED SEARCH ---")
        nome = input(f"{Fore.GREEN}Enter the name or domain you want to search: ").strip()
        opcao = input(f"{Fore.GREEN}Do you want to use a predefined dork? (y/n): ").strip().lower()
        if opcao == 'y':
            print(f"{Fore.CYAN}\nList of available Dorks:")
            for idx, example in enumerate(self.dork_examples, 1):
                print(f"{Fore.WHITE}{idx}. {example['name']} - {example['description']}")
            escolha = int(input(f"{Fore.GREEN}Choose a corresponding number: "))
            dork_template = self.dork_examples[escolha - 1]["dork"]
            query = dork_template.replace("{nome}", nome) if "{nome}" in dork_template else dork_template
            print(f"{Fore.GREEN}You chose: {self.dork_examples[escolha - 1]['name']}")
        else:
            query = input(f"{Fore.GREEN}Enter your custom Dork: ")

        google_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        print(f"{Fore.CYAN}Opening Google search in your browser: {google_url}")
        webbrowser.open(google_url)

        pages = int(input(f"{Fore.GREEN}Number of pages (1-10): "))
        self.dork_search.search(query, pages)
        self.search_history.append({"query": query, "pages": pages, "results": len(self.dork_search.results)})
        self.save_history()
        self.show_results()
        self.show_menu()

    def run_all_dorks(self):
        print(f"{Fore.YELLOW}\n--- RUNNING ALL DORKS ---")
        nome = input(f"{Fore.GREEN}Enter the name or domain you want to search: ").strip()

        for idx, example in enumerate(self.dork_examples, 1):
            dork_template = example["dork"]
            query = dork_template.replace("{nome}", nome) if "{nome}" in dork_template else dork_template
            print(f"{Fore.CYAN}Testing Dork {idx}/{len(self.dork_examples)}: {example['name']}")

            google_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            print(f"{Fore.CYAN}Opening Google search in your browser: {google_url}")
            webbrowser.open(google_url)

            if self.dork_search.search(query):
                print(f"{Fore.GREEN}✓ Results found for Dork: {example['name']}")
                self.search_history.append({"query": query, "results": len(self.dork_search.results)})
                self.save_history()
                self.show_results()
                break

        print(f"{Fore.CYAN}Finished running all dorks.")
        self.show_menu()

    def show_results(self):
        if not self.dork_search.results:
            print(f"{Fore.RED}⚠ No results found.")
            print(f"{Fore.YELLOW}Suggestions:")
            print("1. Check the syntax of your Dork or query.")
            print("2. Use more specific operators.")
            print("3. Reduce the number of pages.")
            print("4. Configure valid proxies.")
            return

        print(f"\n{Fore.CYAN}=== SEARCH RESULTS ===")
        for idx, res in enumerate(self.dork_search.results, 1):
            print(f"{Fore.WHITE}{idx}. {res['title']}")
            print(f"   URL: {res['url']}")
            print(f"   Snippet: {res['snippet']}\n")
        print(f"{Fore.CYAN}===============================")

    def configure_proxies(self):
        print(f"{Fore.YELLOW}--- CONFIGURE PROXIES ---")
        print(f"{Fore.CYAN}1. Enter proxies manually")
        print(f"{Fore.CYAN}2. Upload proxies from a file (e.g., proxy.txt)")
        choice = input(f"{Fore.GREEN}Choose an option (1/2): ").strip()

        if choice == '1':
            # Manual proxy input
            proxy_input = input(
                f"{Fore.GREEN}Enter proxies separated by commas (e.g., http://1.2.3.4:8080, socks5://5.6.7.8:1080): ")
            proxies = [p.strip() for p in proxy_input.split(",") if p.strip()]
        elif choice == '2':
            # File upload
            filename = input(f"{Fore.GREEN}Enter the filename containing proxies (e.g., proxy.txt): ").strip()
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    proxies = [line.strip() for line in f if line.strip()]
                print(f"{Fore.YELLOW}Loaded {len(proxies)} proxies from file.")
            except FileNotFoundError:
                print(f"{Fore.RED}⚠ Proxy file '{filename}' not found.")
                self.show_menu()
                return
        else:
            print(f"{Fore.RED}⚠ Invalid option. Try again.")
            self.show_menu()
            return

        if proxies:
            self.dork_search.set_proxies(proxies)
        else:
            print(f"{Fore.RED}⚠ No proxies provided.")
        self.show_menu()

    def test_proxies(self):
        if not self.dork_search.proxies:
            print(f"{Fore.RED}⚠ No proxies configured.")
            self.show_menu()
        print(f"{Fore.YELLOW}Testing configured proxies...")
        valid_proxies = []
        for proxy in self.dork_search.proxies:
            if self.dork_search.test_proxy(proxy):
                valid_proxies.append(proxy)
        print(f"{Fore.GREEN}✓ {len(valid_proxies)} proxies passed the test.")
        self.show_menu()

    def solve_captcha_menu(self):
        site_key = input(f"{Fore.GREEN}Enter the site key (reCAPTCHA): ").strip()
        page_url = input(f"{Fore.GREEN}Enter the page URL: ").strip()
        api_key = input(f"{Fore.GREEN}Enter your third-party CAPTCHA solver API key: ").strip()
        self.dork_search.solve_captcha_with_third_party(site_key, page_url, api_key)
        self.show_menu()

    def show_history(self):
        if not self.search_history:
            print(f"{Fore.RED}⚠ Search history is empty.")
            return
        print(f"{Fore.YELLOW}--- SEARCH HISTORY ---")
        for i, record in enumerate(self.search_history, 1):
            print(f"{Fore.CYAN}{i}. Query: {record['query']} - Results: {record['results']}")
        print(f"{Fore.YELLOW}===========================")
        self.show_menu()

    def export_menu(self):
        if not self.dork_search.results:
            print(f"{Fore.RED}⚠ No results to export.")
            self.show_menu()
        format_choice = input(f"{Fore.GREEN}Enter the format to export (csv/json): ").strip().lower()
        filename = input(f"{Fore.GREEN}Enter the filename to export (e.g., results.csv): ")
        self.dork_search.export_results(filename, format_choice)
        self.show_menu()

    def exit_program(self):
        self.save_history()
        print(f"{Fore.RED}Exiting the program.")
        exit(0)

if __name__ == '__main__':
    print(f"""
{Fore.GREEN}================================================================================

██████╗ ███████╗███████╗██████╗     ██████╗  ██████╗ ██████╗ ██╗  ██╗
██╔══██╗██╔════╝██╔════╝██╔══██╗    ██╔══██╗██╔═══██╗██╔══██╗██║ ██╔╝
██║  ██║█████╗  █████╗  ██████╔╝    ██║  ██║██║   ██║██████╔╝█████╔╝ 
██║  ██║██╔══╝  ██╔══╝  ██╔═══╝     ██║  ██║██║   ██║██╔══██╗██╔═██╗ 
██████╔╝███████╗███████╗██║         ██████╔╝╚██████╔╝██║  ██║██║  ██╗
╚═════╝ ╚══════╝╚══════╝╚═╝         ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝                                                            

================================================================================
""")
    input("Press Enter to continue...")

    menu = DorkMenu()
    menu.show_menu()