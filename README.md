# Deep-Dork

---

## Description

Deep Dork is a Python-based tool designed to automate Google Dork searches, validate proxies, bypass CAPTCHAs, and export results for further analysis.

---

## Requirements

Before running the tool, ensure you have the following libraries installed:

- `requests`
- `beautifulsoup4`
- `selenium`
- `fake-useragent`
- `colorama`

You can install these libraries using pip:

```bash
pip install requests beautifulsoup4 selenium fake-useragent colorama
```

Additionally, you need to have [ChromeDriver](https://sites.google.com/a/chromium.org/chromedriver/) installed and available in your system's PATH for Selenium to work correctly.

---

## Features

- **Advanced Google Dork Search**: Perform targeted searches using predefined or custom Google Dorks.
- **Proxy Management**: Load, validate, and test proxies from files or manual input to ensure anonymity and avoid IP bans.
- **CAPTCHA Bypass**: Use Selenium or third-party CAPTCHA-solving services (e.g., 2Captcha) to handle CAPTCHA challenges.
- **Multi-threaded Proxy Validation**: Efficiently validate proxies in parallel to improve performance.
- **Search History**: Automatically save and manage search history for future reference.
- **Export Results**: Export search results in JSON or CSV formats for further analysis.
- **User-friendly Menu Interface**: Navigate through options effortlessly via an interactive CLI menu.
- **Customizable User-Agent**: Randomize user-agent headers to mimic different browsers and devices.
- **Error Handling**: Built-in mechanisms to handle timeouts, proxy errors, and other exceptions gracefully.

---

## Usage

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/Diogo-Lages/Deep-Dork.git
   cd Deep-Dork
   ```

2. **Install Dependencies**:
   ```bash
   pip install requests beautifulsoup4 selenium fake-useragent colorama
   ```

3. **Run the Tool**:
   ```bash
   python deepdork.py
   ```

4. **Follow the On-Screen Menu**:
   - **Advanced Search**: Perform targeted searches using predefined or custom Google Dorks.
   - **Run All Dorks Automatically**: Execute all predefined Dorks sequentially.
   - **Configure Proxies**: Load and validate proxies manually or from a file.
   - **View History**: Display past search queries and their results.
   - **Export Results**: Save search results in JSON or CSV format.
   - **Test Proxies**: Validate the functionality of configured proxies.
   - **Solve CAPTCHA with Third-Party Service**: Use external services like 2Captcha to solve CAPTCHAs.
   - **Exit**: Save history and exit the program.

---

## Ethical Considerations

This tool is intended for **ethical use only**. Unauthorized use of Google Dorks or any form of web scraping may violate terms of service and legal regulations. Always ensure you have explicit permission before conducting reconnaissance or testing on any system.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.
