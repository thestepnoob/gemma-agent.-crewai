import os
import datetime
from typing import Optional
from crewai.tools import BaseTool
from .core import log_created_file

class DeepWebSearchTool(BaseTool):
    name: str = "Tiefgruendige Websuche"
    description: str = (
        "Führt eine tiefe Websuche im Internet für eine Suchanfrage durch. "
        "Das Tool sucht nach aktuellen Links und lädt die Inhalte der Top-3 Webseiten direkt herunter."
    )

    def _run(self, query: str) -> str:
        import urllib3
        from duckduckgo_search import DDGS
        from bs4 import BeautifulSoup
        import requests
        
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        results_summary = []
        try:
            with DDGS() as ddgs:
                search_results = [r for r in ddgs.text(query, max_results=3)]
                
            if not search_results:
                return f"Keine Suchergebnisse im Web für die Anfrage '{query}' gefunden."
            
            for idx, res in enumerate(search_results, 1):
                title = res.get("title", "Kein Titel")
                url = res.get("href", "")
                snippet = res.get("body", "")
                
                if not url: continue
                
                results_summary.append(f"=== Quelle {idx}: {title} ===\nURL: {url}\nSnippet: {snippet}")
                try:
                    response = requests.get(url, headers=headers, timeout=10, verify=False)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        for element in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
                            element.decompose()
                            
                        page_text = soup.get_text(separator='\n')
                        lines = (line.strip() for line in page_text.splitlines())
                        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                        clean_text = '\n'.join(chunk for chunk in chunks if chunk)
                        
                        scraped_content = clean_text[:3000]
                        results_summary.append(f"Ausgelesener Inhalt (Auszug):\n{scraped_content}\n")
                    else:
                        results_summary.append(f"Ausgelesener Inhalt: Fehlgeschlagen (HTTP-Code {response.status_code})\n")
                except Exception as scrape_err:
                    results_summary.append(f"Ausgelesener Inhalt: Fehlgeschlagen ({str(scrape_err)})\n")
            
            return "\n\n".join(results_summary)
        except Exception as e:
            return f"Fehler bei der Websuche: {str(e)}"

class InteractiveBrowserTool(BaseTool):
    name: str = "Interaktiver Browser"
    description: str = (
        "Öffnet einen Browser im Hintergrund, lädt eine Webseite, "
        "klickt optional auf Cookie-Banner, füllt Formulare aus oder klickt auf Elemente. "
        "Kann einen Screenshot im Ordner attachments/ speichern und den Inhalt der Seite zurückgeben."
    )

    def _run(self, url: str, action: str = "scrape", selector: Optional[str] = None, text_to_type: Optional[str] = None, take_screenshot: bool = True) -> str:
        from playwright.sync_api import sync_playwright
        from bs4 import BeautifulSoup
        
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ATTACHMENT_DIR = os.path.join(project_dir, "attachments")
        os.makedirs(ATTACHMENT_DIR, exist_ok=True)
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    viewport={"width": 1280, "height": 800},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                page = context.new_page()
                
                page.goto(url, timeout=30000, wait_until="load")
                page.wait_for_timeout(2000)
                
                log_msg = f"Webseite {url} erfolgreich geladen.\n"
                
                consent_keywords = [
                    "accept", "agree", "allow", "consent", "ok", "yes",
                    "akzeptieren", "zustimmen", "einverstanden", "zulassen", "erlauben", "ja", "schliessen", "schließen",
                    "accept all", "alle akzeptieren", "zustimmen & weiter"
                ]
                
                try:
                    elements = page.locator("button, a, div[role='button']").all()
                    clicked = False
                    for element in elements:
                        if element.is_visible() and element.is_enabled():
                            text = (element.inner_text() or "").strip().lower()
                            for keyword in consent_keywords:
                                if keyword == text or (keyword in text and len(text) < 35):
                                    element.click()
                                    page.wait_for_timeout(1500)
                                    log_msg += f"Cookie-Banner automatisch geklickt ('{text}').\n"
                                    clicked = True
                                    break
                            if clicked: break
                except Exception as e:
                    pass
                
                if action == "click" and selector:
                    try:
                        page.click(selector, timeout=10000)
                        page.wait_for_timeout(1500)
                        log_msg += f"Erfolgreich auf '{selector}' geklickt.\n"
                    except Exception as e:
                        log_msg += f"Fehler beim Klicken auf '{selector}': {str(e)}\n"
                        
                elif action == "type" and selector and text_to_type:
                    try:
                        page.fill(selector, text_to_type, timeout=10000)
                        page.wait_for_timeout(1000)
                        log_msg += f"Erfolgreich '{text_to_type}' eingegeben.\n"
                    except Exception as e:
                        log_msg += f"Fehler beim Schreiben: {str(e)}\n"
                
                if take_screenshot:
                    try:
                        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                        screenshot_name = f"screenshot_{timestamp}.png"
                        screenshot_path = os.path.join(ATTACHMENT_DIR, screenshot_name)
                        page.screenshot(path=screenshot_path, full_page=False)
                        log_msg += f"Screenshot gespeichert unter: {screenshot_path}\n"
                        log_created_file(screenshot_path)
                    except Exception as e:
                        log_msg += f"Fehler beim Screenshot: {str(e)}\n"
                
                html_content = page.content()
                soup = BeautifulSoup(html_content, 'html.parser')
                for element in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
                    element.decompose()
                page_text = soup.get_text(separator='\n')
                lines = (line.strip() for line in page_text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                clean_text = '\n'.join(chunk for chunk in chunks if chunk)
                
                browser.close()
                return f"--- BROWSER LOG ---\n{log_msg}\n--- TEXT CONTENT (Erste 6000 Zeichen) ---\n{clean_text[:6000]}"
                
        except Exception as e:
            return f"Fehler bei Browser-Automatisierung: {str(e)}"
